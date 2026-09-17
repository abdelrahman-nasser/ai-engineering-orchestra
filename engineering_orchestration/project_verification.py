"""Programmatic planning and execution of Project Verification Checks.

This module consumes only the Manifest's ``verification.checks`` declaration.
It does not run Tasks, Workflow stages, Agents, Providers, or Quality Gates, and
it is intentionally not wired to the CLI or the legacy repository preflight.

Declared commands run sequentially with the caller's effective authority and
inherited environment. They may access files, networks, credentials, and spawn
descendants; no sandbox, purity, or process-tree confinement is provided. The
outer subprocess call uses ``shell=False`` and never builds a command string,
although Windows may still route a declared ``.cmd`` or ``.bat`` executable
through the command interpreter. On timeout or interruption, only the directly
launched child is terminated and reaped on a best-effort basis.

Diagnostic excerpts are bounded but unsanitized and may contain sensitive
command output. Project Verification Checks must not deliberately invoke the
aggregate AIO verifier recursively; recursion detection is deferred until the
aggregate verifier is migrated.
"""

from __future__ import annotations

import locale
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Literal

import yaml

from engineering_orchestration.schema_resources import load_validator, schema_errors
from engineering_orchestration.validation import Finding, manifest_semantic_errors


DEFAULT_TIMEOUT_SECONDS = 600
DIAGNOSTIC_EXCERPT_LIMIT = 64 * 1024
_DIRECT_CHILD_STOP_GRACE_SECONDS = 0.2
_DEFAULT_WINDOWS_PATHEXT = ".COM;.EXE;.BAT;.CMD"

CheckStatus = Literal["PASS", "FAIL", "ERROR"]
_FileIdentity = tuple[int, int]


@dataclass(frozen=True)
class PlannedCheck:
    """One fully materialized, immutable Verification Check."""

    id: str
    command: tuple[str, ...]
    declared_cwd: str | None
    cwd: Path
    timeout_seconds: int
    _cwd_identity: _FileIdentity = field(repr=False)


@dataclass(frozen=True)
class VerificationPlan:
    """Complete immutable plan that must exist before any command executes."""

    project_root: Path
    checks: tuple[PlannedCheck, ...]
    _project_root_identity: _FileIdentity = field(repr=False)


@dataclass(frozen=True)
class VerificationPlanResult:
    """Planning-specific result, separate from structural validation state."""

    plan: VerificationPlan | None = None
    findings: tuple[Finding, ...] = ()

    @property
    def is_ready(self) -> bool:
        return self.plan is not None and not self.findings

    @property
    def status(self) -> Literal["PASS", "FAIL", "ERROR"]:
        if any(item.status == "ERROR" for item in self.findings):
            return "ERROR"
        return "FAIL" if self.findings else "PASS"


@dataclass(frozen=True)
class VerificationCheckResult:
    """Ephemeral mechanical evidence from one declared command."""

    id: str
    command: tuple[str, ...]
    cwd: Path
    status: CheckStatus
    return_code: int | None
    duration_seconds: float
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    error: str | None = None


@dataclass(frozen=True)
class VerificationRunResult:
    """Aggregate mechanical evidence; it is not a Quality Gate result."""

    plan: VerificationPlan
    results: tuple[VerificationCheckResult, ...] = ()
    fatal_error: str | None = None

    @property
    def passed_count(self) -> int:
        return sum(item.status == "PASS" for item in self.results)

    @property
    def failed_count(self) -> int:
        return sum(item.status == "FAIL" for item in self.results)

    @property
    def error_count(self) -> int:
        return sum(item.status == "ERROR" for item in self.results)

    @property
    def status(self) -> CheckStatus:
        if self.fatal_error is not None or self.error_count:
            return "ERROR"
        return "FAIL" if self.failed_count else "PASS"

    @property
    def exit_code(self) -> int:
        if self.status == "ERROR":
            return 2
        return 1 if self.status == "FAIL" else 0


class _FatalRunnerError(RuntimeError):
    """Internal marker for failures that invalidate the remaining session."""


def _identity(path: Path) -> _FileIdentity:
    stat = path.stat()
    return stat.st_dev, stat.st_ino


def _schema_findings(manifest_path: Path, manifest: object) -> tuple[Finding, ...]:
    try:
        validator = load_validator("project-manifest.schema.json")
        errors = schema_errors(validator, manifest)
    except Exception as exc:
        return (Finding(
            "ERROR", manifest_path,
            f"Project Manifest contract validation could not run: {exc}",
        ),)

    findings = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        findings.append(Finding("FAIL", manifest_path, f"{location}: {error.message}"))
    if findings:
        return tuple(findings)

    try:
        semantic_errors = manifest_semantic_errors(manifest)  # type: ignore[arg-type]
    except Exception as exc:
        return (Finding(
            "ERROR", manifest_path,
            f"Project Manifest semantic validation could not run: {exc}",
        ),)
    return tuple(Finding("FAIL", manifest_path, message) for message in semantic_errors)


def _load_validated_manifest(manifest_path: Path) -> tuple[dict | None, tuple[Finding, ...]]:
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, (Finding("ERROR", manifest_path, "Project Manifest not found"),)
    except (yaml.YAMLError, UnicodeError) as exc:
        return None, (Finding("FAIL", manifest_path, f"Invalid Project Manifest: {exc}"),)
    except OSError as exc:
        return None, (Finding(
            "ERROR", manifest_path, f"Project Manifest could not be read: {exc}",
        ),)

    findings = _schema_findings(manifest_path, manifest)
    if findings:
        return None, findings
    return manifest, ()  # type: ignore[return-value]


def plan_project_checks(project_root: Path) -> VerificationPlanResult:
    """Load, validate, and completely plan the active project's Checks.

    All effective working directories are resolved, checked as directories,
    checked for containment after link resolution, and identified before a plan
    is returned. Executable availability is intentionally deferred per Check.
    """

    supplied_root = Path(project_root)
    try:
        try:
            root = supplied_root.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            return VerificationPlanResult(findings=(Finding(
                "ERROR", supplied_root, f"Project root could not be resolved: {exc}",
            ),))
        if not root.is_dir():
            return VerificationPlanResult(findings=(Finding(
                "ERROR", root, "Project root is not a directory",
            ),))
        try:
            root_identity = _identity(root)
        except OSError as exc:
            return VerificationPlanResult(findings=(Finding(
                "ERROR", root, f"Project root could not be inspected: {exc}",
            ),))

        manifest_path = root / ".ai" / "project.yaml"
        manifest, contract_findings = _load_validated_manifest(manifest_path)
        if contract_findings:
            return VerificationPlanResult(findings=contract_findings)
        assert manifest is not None

        checks = manifest.get("verification", {}).get("checks", [])
        planned: list[PlannedCheck] = []
        findings: list[Finding] = []
        for check in checks:
            declared_cwd = check.get("cwd")
            candidate = root if declared_cwd is None else root / declared_cwd
            try:
                resolved_cwd = candidate.resolve(strict=True)
            except (OSError, RuntimeError) as exc:
                findings.append(Finding(
                    "ERROR", candidate,
                    f"Verification Check '{check['id']}' cwd could not be resolved: {exc}",
                ))
                continue
            if not resolved_cwd.is_dir():
                findings.append(Finding(
                    "ERROR", resolved_cwd,
                    f"Verification Check '{check['id']}' cwd is not a directory",
                ))
                continue
            if resolved_cwd != root and not resolved_cwd.is_relative_to(root):
                findings.append(Finding(
                    "ERROR", resolved_cwd,
                    f"Verification Check '{check['id']}' cwd resolves outside project root",
                ))
                continue
            try:
                cwd_identity = _identity(resolved_cwd)
            except OSError as exc:
                findings.append(Finding(
                    "ERROR", resolved_cwd,
                    f"Verification Check '{check['id']}' cwd could not be inspected: {exc}",
                ))
                continue
            planned.append(PlannedCheck(
                id=check["id"],
                command=tuple(check["command"]),
                declared_cwd=declared_cwd,
                cwd=resolved_cwd,
                timeout_seconds=check.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
                _cwd_identity=cwd_identity,
            ))

        if findings:
            return VerificationPlanResult(findings=tuple(findings))
        return VerificationPlanResult(plan=VerificationPlan(
            project_root=root,
            checks=tuple(planned),
            _project_root_identity=root_identity,
        ))
    except Exception as exc:
        return VerificationPlanResult(findings=(Finding(
            "ERROR", supplied_root, f"Verification planning could not finish: {exc}",
        ),))


def _normalized_search_path(cwd: Path) -> str:
    raw_path = os.environ.get("PATH", os.defpath)
    entries = []
    for item in raw_path.split(os.pathsep):
        if len(item) >= 2 and item[0] == item[-1] == '"':
            item = item[1:-1]
        entry = cwd if not item else Path(item)
        if not entry.is_absolute():
            entry = cwd / entry
        entries.append(str(entry))
    return os.pathsep.join(entries)


def _resolve_windows_bare_executable(executable: str, cwd: Path) -> Path | None:
    search_path = _normalized_search_path(cwd)
    raw_extensions = os.environ.get("PATHEXT", _DEFAULT_WINDOWS_PATHEXT)
    extensions = tuple(
        item if item.startswith(".") else f".{item}"
        for item in raw_extensions.split(os.pathsep)
        if item
    )
    suffix = Path(executable).suffix.casefold()
    if suffix and any(suffix == item.casefold() for item in extensions):
        names = (executable,)
    else:
        names = tuple(f"{executable}{item}" for item in extensions)

    for directory in search_path.split(os.pathsep):
        for name in names:
            candidate = Path(directory) / name
            try:
                if candidate.is_file():
                    return candidate.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
    return None


def resolve_executable(executable: str, cwd: Path) -> Path | None:
    """Resolve one executable according to Check cwd and platform semantics."""

    path = Path(executable)
    if os.name == "nt" and (
        (path.drive and not path.root)
        or (path.root and not path.drive)
    ):
        # Drive-relative paths consult per-drive process state, while rooted
        # paths without a drive discard the effective cwd's directory portion.
        # Neither is a deterministic absolute or cwd-relative declaration.
        return None
    has_directory_component = (
        path.parent != Path(".")
        or os.sep in executable
        or (os.altsep is not None and os.altsep in executable)
    )
    if path.is_absolute():
        candidate = path
    elif has_directory_component:
        candidate = Path(cwd) / path
    else:
        if os.name == "nt":
            return _resolve_windows_bare_executable(executable, Path(cwd))
        found = shutil.which(
            executable,
            path=_normalized_search_path(Path(cwd)),
        )
        if found is None:
            return None
        try:
            return Path(found).resolve(strict=True)
        except (OSError, RuntimeError):
            return None

    try:
        resolved = candidate.resolve(strict=True)
        return resolved if resolved.is_file() else None
    except (OSError, RuntimeError):
        return None


def _validate_plan_invariants(plan: VerificationPlan) -> None:
    if not isinstance(plan, VerificationPlan):
        raise _FatalRunnerError("Runner received an invalid VerificationPlan object")
    if not plan.project_root.is_absolute():
        raise _FatalRunnerError("VerificationPlan project root is not absolute")
    seen = set()
    for check in plan.checks:
        if check.id in seen:
            raise _FatalRunnerError(f"VerificationPlan contains duplicate ID: {check.id}")
        seen.add(check.id)
        if not check.command or not isinstance(check.command, tuple):
            raise _FatalRunnerError(f"VerificationPlan command is invalid for: {check.id}")
        if (not isinstance(check.timeout_seconds, int)
                or isinstance(check.timeout_seconds, bool)
                or check.timeout_seconds < 1):
            raise _FatalRunnerError(f"VerificationPlan timeout is invalid for: {check.id}")
        if not check.cwd.is_absolute():
            raise _FatalRunnerError(f"VerificationPlan cwd is not absolute for: {check.id}")
        if (check.cwd != plan.project_root
                and not check.cwd.is_relative_to(plan.project_root)):
            raise _FatalRunnerError(
                f"VerificationPlan cwd is outside project root for: {check.id}")


def _revalidate_project_root(plan: VerificationPlan) -> None:
    try:
        current = plan.project_root.resolve(strict=True)
        if not current.is_dir():
            raise _FatalRunnerError("Project root is no longer a directory")
        if current != plan.project_root or _identity(current) != plan._project_root_identity:
            raise _FatalRunnerError("Project root changed after planning")
    except _FatalRunnerError:
        raise
    except (OSError, RuntimeError) as exc:
        raise _FatalRunnerError(f"Project root is no longer usable: {exc}") from exc


def _revalidate_check_cwd(plan: VerificationPlan, check: PlannedCheck) -> Path:
    candidate = (
        plan.project_root
        if check.declared_cwd is None
        else plan.project_root / check.declared_cwd
    )
    try:
        current = candidate.resolve(strict=True)
        if not current.is_dir():
            raise OSError("cwd is no longer a directory")
        if current != plan.project_root and not current.is_relative_to(plan.project_root):
            raise OSError("cwd now resolves outside project root")
        if current != check.cwd or _identity(current) != check._cwd_identity:
            raise OSError("cwd changed after planning")
        return current
    except (OSError, RuntimeError) as exc:
        raise OSError(f"Verification Check '{check.id}' cwd is not launchable: {exc}") from exc


def _stop_direct_child(process: subprocess.Popen[bytes]) -> None:
    try:
        if process.poll() is not None:
            process.wait()
            return
    except OSError:
        pass
    try:
        process.terminate()
    except OSError:
        pass
    try:
        process.wait(timeout=_DIRECT_CHILD_STOP_GRACE_SECONDS)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass
    killed = False
    try:
        process.kill()
        killed = True
    except OSError:
        pass
    try:
        if killed:
            process.wait()
        else:
            process.wait(timeout=_DIRECT_CHILD_STOP_GRACE_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _read_excerpt(stream: BinaryIO) -> str:
    stream.flush()
    total = stream.seek(0, os.SEEK_END)
    start = max(0, total - DIAGNOSTIC_EXCERPT_LIMIT)
    stream.seek(start)
    data = stream.read(DIAGNOSTIC_EXCERPT_LIMIT)
    encoding = locale.getpreferredencoding(False)
    decoded = data.decode(encoding, errors="replace")
    if start:
        return f"[... {start} earlier bytes truncated ...]\n{decoded}"
    return decoded


def _error_result(
    check: PlannedCheck,
    started: float,
    error: str,
    *,
    stdout_excerpt: str = "",
    stderr_excerpt: str = "",
    return_code: int | None = None,
) -> VerificationCheckResult:
    return VerificationCheckResult(
        id=check.id,
        command=check.command,
        cwd=check.cwd,
        status="ERROR",
        return_code=return_code,
        duration_seconds=max(0.0, time.monotonic() - started),
        stdout_excerpt=stdout_excerpt,
        stderr_excerpt=stderr_excerpt,
        error=error,
    )


def _execute_check(plan: VerificationPlan, check: PlannedCheck) -> VerificationCheckResult:
    started = time.monotonic()
    try:
        _revalidate_project_root(plan)
        current_cwd = _revalidate_check_cwd(plan, check)
    except _FatalRunnerError:
        raise
    except OSError as exc:
        return _error_result(check, started, str(exc))

    resolved_executable = resolve_executable(check.command[0], current_cwd)
    if resolved_executable is None:
        return _error_result(
            check, started,
            f"Unable to launch {check.command[0]}: executable not found",
        )
    command = [str(resolved_executable), *check.command[1:]]

    try:
        stdout_file = tempfile.TemporaryFile(mode="w+b")
    except OSError as exc:
        return _error_result(check, started, f"Output capture could not be created: {exc}")
    try:
        stderr_file = tempfile.TemporaryFile(mode="w+b")
    except OSError as exc:
        stdout_file.close()
        return _error_result(check, started, f"Output capture could not be created: {exc}")

    with stdout_file, stderr_file:
        try:
            _revalidate_project_root(plan)
            launch_cwd = _revalidate_check_cwd(plan, check)
        except _FatalRunnerError:
            raise
        except OSError as exc:
            return _error_result(check, started, str(exc))

        try:
            process = subprocess.Popen(
                command,
                cwd=launch_cwd,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                env=None,
            )
        except OSError as exc:
            return _error_result(
                check, started, f"Unable to launch {check.command[0]}: {exc}",
            )

        timed_out = False
        try:
            process.wait(timeout=check.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            _stop_direct_child(process)
        except BaseException:
            _stop_direct_child(process)
            raise

        try:
            stdout_excerpt = _read_excerpt(stdout_file)
            stderr_excerpt = _read_excerpt(stderr_file)
        except OSError as exc:
            return _error_result(
                check,
                started,
                f"Output capture could not be read: {exc}",
                return_code=process.returncode,
            )

        duration = max(0.0, time.monotonic() - started)
        if timed_out:
            return VerificationCheckResult(
                id=check.id,
                command=check.command,
                cwd=check.cwd,
                status="ERROR",
                return_code=None,
                duration_seconds=duration,
                stdout_excerpt=stdout_excerpt,
                stderr_excerpt=stderr_excerpt,
                error=f"Timed out after {check.timeout_seconds} seconds",
            )
        return VerificationCheckResult(
            id=check.id,
            command=check.command,
            cwd=check.cwd,
            status="PASS" if process.returncode == 0 else "FAIL",
            return_code=process.returncode,
            duration_seconds=duration,
            stdout_excerpt=stdout_excerpt,
            stderr_excerpt=stderr_excerpt,
        )


def run_project_checks(plan: VerificationPlan) -> VerificationRunResult:
    """Execute a complete plan sequentially and return mechanical evidence.

    FAIL and ordinary check-local ERROR results do not stop later independent
    Checks. A fatal root/session/invariant failure stops the remaining plan
    without fabricating SKIP results. ``KeyboardInterrupt`` propagates.
    """

    results: list[VerificationCheckResult] = []
    try:
        _validate_plan_invariants(plan)
        _revalidate_project_root(plan)
        for check in plan.checks:
            _revalidate_project_root(plan)
            results.append(_execute_check(plan, check))
            _revalidate_project_root(plan)
    except _FatalRunnerError as exc:
        return VerificationRunResult(
            plan=plan,
            results=tuple(results),
            fatal_error=str(exc),
        )
    except Exception as exc:
        return VerificationRunResult(
            plan=plan,
            results=tuple(results),
            fatal_error=f"Unexpected runner failure: {exc}",
        )
    return VerificationRunResult(plan=plan, results=tuple(results))


def format_project_verification_output(result: VerificationRunResult) -> str:
    """Format concise evidence while suppressing successful command output."""

    lines = ["Project Verification Checks", "=" * 27]
    if not result.results and result.fatal_error is None:
        lines.append("0 project checks configured")
    for item in result.results:
        lines.append(f"{item.id:<30} {item.status:<5} {item.duration_seconds:.3f}s")
        if item.status == "PASS":
            continue
        if item.error:
            lines.append(f"  Error: {item.error}")
        if item.stdout_excerpt:
            lines.append("  stdout:")
            lines.extend(f"    {line}" for line in item.stdout_excerpt.rstrip().splitlines())
        if item.stderr_excerpt:
            lines.append("  stderr:")
            lines.extend(f"    {line}" for line in item.stderr_excerpt.rstrip().splitlines())
        if not item.error and not item.stdout_excerpt and not item.stderr_excerpt:
            lines.append("  (no output captured)")
    if result.fatal_error is not None:
        lines.append(f"Fatal runner error: {result.fatal_error}")
    lines.append(
        f"Summary: {result.passed_count} PASS, {result.failed_count} FAIL, "
        f"{result.error_count} ERROR"
    )
    return "\n".join(lines)
