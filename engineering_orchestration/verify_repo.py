#!/usr/bin/env python3
"""AI Engineering Orchestra — Repository Preflight Verification Utility.

Consolidates the repository's mechanical verification battery into a single
deterministic execution producing a concise summary.

Fundamental Semantic Boundary:
    Repository verification != Quality Gate satisfaction.
    Mechanical check results (e.g. Unit Tests PASS, Markdown Lint PASS) provide
    supporting evidence toward repository health and documentation quality.
    They do NOT automatically satisfy semantic Quality Gates such as
    documentation_consistency or independent_review.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

PYTHON_EXE = sys.executable or "python"


@dataclass(frozen=True)
class CheckDefinition:
    """Immutable definition of a mechanical repository check."""

    name: str
    command: list[str]


@dataclass
class CheckResult:
    """Outcome of an individual mechanical repository check."""

    name: str
    command: list[str]
    status: str  # "PASS", "FAIL", "ERROR"
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error_message: str | None = None


@dataclass
class PreflightResult:
    """Consolidated preflight verification result."""

    repo_root: Path
    results: list[CheckResult] = field(default_factory=list)
    infrastructure_error: str | None = None

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == "ERROR")

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def exit_code(self) -> int:
        """Preflight exit code:

        0 = every repository check passed
        1 = utility executed correctly, but one or more repository checks returned failure
        2 = preflight infrastructure/utility failure (e.g. executable launch failure)
        """
        if self.infrastructure_error is not None or self.error_count > 0:
            return 2
        if self.failed_count > 0:
            return 1
        return 0


DEFAULT_CHECKS: list[CheckDefinition] = [
    CheckDefinition(
        name="Unit Tests",
        command=[PYTHON_EXE, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
    ),
    CheckDefinition(
        name="Task Validation",
        command=[PYTHON_EXE, "-B", "schemas/tests/validate_task.py"],
    ),
    CheckDefinition(
        name="Workflow Validation",
        command=[PYTHON_EXE, "-B", "schemas/tests/validate_workflow.py"],
    ),
    CheckDefinition(
        name="Role Validation",
        command=[PYTHON_EXE, "-B", "schemas/tests/validate_role.py"],
    ),
    CheckDefinition(
        name="Project Manifest Validation",
        command=[PYTHON_EXE, "-B", "schemas/tests/validate_project_manifest.py"],
    ),
    CheckDefinition(
        name="Markdown Lint",
        command=["npx", "--yes", "markdownlint-cli2", "**/*.md"],
    ),
    CheckDefinition(
        name="Git Diff Check",
        command=["git", "diff", "--check"],
    ),
]


def find_repo_root(start_path: Path | None = None) -> Path:
    """Deterministically locate the repository root.

    Resolves from this script's directory hierarchy and validates against
    repository markers (.ai/project.yaml or .git).
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent.parent

    candidate = start_path.resolve()
    if (candidate / ".ai" / "project.yaml").is_file() or (candidate / ".git").exists():
        return candidate

    for parent in candidate.parents:
        if (parent / ".ai" / "project.yaml").is_file() or (parent / ".git").exists():
            return parent

    raise RuntimeError(f"Could not determine repository root from {start_path}")


def resolve_executable(name: str) -> str | None:
    """Resolve an executable command name to a runnable executable path."""
    p = Path(name)
    if p.is_file():
        return str(p.resolve())
    return shutil.which(name)


def default_runner(
    cmd: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess command with shell=False, capturing output."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
    )


def run_check(
    check: CheckDefinition,
    repo_root: Path,
    runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> CheckResult:
    """Execute an individual repository check and classify the outcome."""
    if runner is None:
        runner = default_runner

    executable = check.command[0]
    resolved_exe = resolve_executable(executable)
    if resolved_exe is None:
        return CheckResult(
            name=check.name,
            command=check.command,
            status="ERROR",
            error_message=f"Unable to launch {executable}: executable not found on PATH",
        )

    full_cmd = [resolved_exe] + check.command[1:]
    try:
        proc = runner(full_cmd, repo_root)
        if proc.returncode == 0:
            return CheckResult(
                name=check.name,
                command=check.command,
                status="PASS",
                exit_code=0,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        else:
            return CheckResult(
                name=check.name,
                command=check.command,
                status="FAIL",
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
    except OSError as exc:
        return CheckResult(
            name=check.name,
            command=check.command,
            status="ERROR",
            error_message=f"Unable to launch {executable}: {exc}",
        )
    except Exception as exc:
        return CheckResult(
            name=check.name,
            command=check.command,
            status="ERROR",
            error_message=f"Unexpected runner error executing {executable}: {exc}",
        )


def run_preflight(
    repo_root: Path | None = None,
    checks: list[CheckDefinition] | None = None,
    runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> PreflightResult:
    """Run all configured repository checks sequentially to completion."""
    if repo_root is None:
        repo_root = find_repo_root()

    if checks is None:
        checks = DEFAULT_CHECKS

    result = PreflightResult(repo_root=repo_root)

    for check in checks:
        check_result = run_check(check, repo_root, runner=runner)
        result.results.append(check_result)

    return result


def format_preflight_output(result: PreflightResult) -> str:
    """Format preflight results into a concise deterministic summary."""
    lines: list[str] = [
        "AI Engineering Orchestra - Repository Preflight",
        "=" * 50,
    ]

    for check_res in result.results:
        status_str = check_res.status
        lines.append(f"{check_res.name:<30} {status_str}")
        if check_res.status == "ERROR" and check_res.error_message:
            lines.append(f"  {check_res.error_message}")

    lines.append("")

    if result.infrastructure_error is not None:
        lines.append(f"Infrastructure Error: {result.infrastructure_error}")
        lines.append("")

    if result.failed_count == 0 and result.error_count == 0:
        lines.append(f"Summary: {result.passed_count}/{result.total_count} checks passed")
    else:
        lines.append(f"Summary: {result.passed_count}/{result.total_count} checks passed")
        lines.append(f"  {result.passed_count} PASS")
        lines.append(f"  {result.failed_count} FAIL")
        lines.append(f"  {result.error_count} ERROR")

    # Diagnostics for failed checks or checks with error details
    failed_or_errored = [
        r for r in result.results
        if r.status in ("FAIL", "ERROR") and (r.stdout.strip() or r.stderr.strip() or r.status == "FAIL")
    ]
    if failed_or_errored:
        lines.append("")
        lines.append("--- Failure Diagnostics ---")
        for r in failed_or_errored:
            exit_str = f"exit code {r.exit_code}" if r.exit_code is not None else "launch failure"
            lines.append(f"[{r.name}] ({exit_str}):")
            output_parts = []
            if r.stdout and r.stdout.strip():
                output_parts.append(r.stdout.strip())
            if r.stderr and r.stderr.strip():
                output_parts.append(r.stderr.strip())
            if output_parts:
                for part in output_parts:
                    for line in part.splitlines():
                        lines.append(f"  {line}")
            else:
                lines.append("  (no output captured)")
            lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for repository preflight utility."""
    parser = argparse.ArgumentParser(
        description="AI Engineering Orchestra — Repository Preflight Verification Utility"
    )
    # No --task, --quiet, or --verbose flags per specification
    parser.parse_args(argv)

    try:
        repo_root = find_repo_root()
    except Exception as exc:
        print(f"Preflight Infrastructure Error: {exc}", file=sys.stderr)
        return 2

    preflight_result = run_preflight(repo_root=repo_root)
    output = format_preflight_output(preflight_result)
    print(output)
    return preflight_result.exit_code


if __name__ == "__main__":
    sys.exit(main())
