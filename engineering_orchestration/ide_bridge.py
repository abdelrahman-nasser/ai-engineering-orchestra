"""Bounded, read-only JSON bridge for the experimental VS Code integration.

The bridge deliberately exposes a very small wire contract.  It is not a
general RPC surface and it never executes project-declared commands.  Each
process accepts exactly one request on standard input and writes exactly one
response on standard output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from types import MappingProxyType
from typing import Any, Mapping, NoReturn

import yaml

from engineering_orchestration.inspect_task import CANONICAL_ARTIFACTS, inspect_task
from engineering_orchestration.list_tasks import discover_tasks, filter_tasks
from engineering_orchestration.project import task_directory
from engineering_orchestration.role_catalog import load_role_catalog
from engineering_orchestration.schema_resources import load_validator, schema_errors, schema_resource
from engineering_orchestration.validation import manifest_semantic_errors, validate_project
from engineering_orchestration.workflow_catalog import load_workflow_catalog


PROTOCOL = "aio.ide/1"
PACKAGE_NAME = "ai-engineering-orchestra"
PACKAGE_VERSION_FALLBACK = "0.1.0"

MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_YAML_BYTES = 1024 * 1024
MAX_TASK_DIRECTORIES = 1000
MAX_WORKFLOW_FILES = 256
MAX_DIAGNOSTICS = 100
MAX_DIAGNOSTIC_CHARS = 512
MAX_PROJECT_ROOT_CHARS = 4096
MAX_TASK_ID_CHARS = 256
MAX_FILTER_CHARS = 256

REQUEST_KEYS = frozenset(
    {"protocol", "request_id", "operation", "project_root", "payload"}
)
OPERATIONS = frozenset({"project_snapshot", "task_detail"})
ERROR_CODES = frozenset(
    {
        "invalid_json",
        "invalid_request",
        "unsupported_protocol",
        "unmanaged_project",
        "invalid_project",
        "out_of_scope_resource",
        "task_not_found",
        "task_id_ambiguous",
        "invalid_catalog",
        "resource_limit",
        "internal_error",
    }
)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class BridgeError(Exception):
    """Expected request or project failure represented on the wire."""

    def __init__(
        self,
        code: str,
        message: str,
        diagnostics: list[dict[str, Any]] | None = None,
    ) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"Unknown bridge error code: {code}")
        super().__init__(message)
        self.code = code
        self.message = _bounded_text(message)
        self.diagnostics = _bounded_diagnostics(diagnostics or [])


@dataclass(frozen=True)
class ProjectContext:
    """A request-local filesystem snapshot and its source-root identity map."""

    root: Path
    snapshot_root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    tasks_dir: Path
    workflows_dir: Path
    task_schema: Path
    workflow_schema: Path
    role_catalog: Any
    source_relatives: Mapping[str, str]


def _bounded_text(value: object, limit: int = MAX_DIAGNOSTIC_CHARS) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _bounded_diagnostics(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(items) > MAX_DIAGNOSTICS:
        raise BridgeError(
            "resource_limit",
            f"Diagnostic count exceeds the limit of {MAX_DIAGNOSTICS}.",
        )
    bounded: list[dict[str, Any]] = []
    for item in items:
        diagnostic: dict[str, Any] = {
            "code": _bounded_text(item.get("code", "diagnostic")),
            "message": _bounded_text(item.get("message", "")),
        }
        if "status" in item:
            diagnostic["status"] = _bounded_text(item["status"])
        if "resource_id" in item and item["resource_id"] is not None:
            diagnostic["resource_id"] = _bounded_text(item["resource_id"])
        bounded.append(diagnostic)
    return bounded


def _package_meta() -> dict[str, str]:
    try:
        version = metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        # Source-tree execution remains useful for development; installed use
        # obtains the same value from wheel metadata.
        version = PACKAGE_VERSION_FALLBACK
    return {
        "package_version": version,
        "package_origin": str(Path(__file__).resolve().parent),
    }


def _response(
    request_id: str | None,
    *,
    result: dict[str, Any] | None = None,
    error: BridgeError | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "protocol": PROTOCOL,
        "request_id": request_id,
        "ok": error is None,
        "meta": _package_meta(),
    }
    if error is None:
        base["result"] = result if result is not None else {}
        base["diagnostics"] = _bounded_diagnostics(diagnostics or [])
    else:
        base["error"] = {"code": error.code, "message": error.message}
        base["diagnostics"] = error.diagnostics
    return base


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f"Non-finite JSON number is not permitted: {value}")


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def _parse_json(data: bytes) -> Any:
    if len(data) > MAX_REQUEST_BYTES:
        raise BridgeError(
            "resource_limit",
            f"Request input exceeds the {MAX_REQUEST_BYTES}-byte limit.",
        )
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_closed_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BridgeError("invalid_json", f"Request is not one valid JSON value: {exc}") from exc


def _valid_request_id(value: Any) -> bool:
    return isinstance(value, str) and REQUEST_ID_PATTERN.fullmatch(value) is not None


def _candidate_request_id(document: Any) -> str | None:
    if isinstance(document, dict) and _valid_request_id(document.get("request_id")):
        return document["request_id"]
    return None


def _has_only_keys(value: dict[str, Any], expected: frozenset[str]) -> bool:
    return set(value) == set(expected)


def _is_scalar_text(value: Any, *, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and minimum <= len(value) <= maximum
        and "\x00" not in value
        and all(not 0xD800 <= ord(character) <= 0xDFFF for character in value)
    )


def _validate_filter(value: Any, name: str) -> str | None:
    if value is None:
        return None
    if not _is_scalar_text(value, minimum=1, maximum=MAX_FILTER_CHARS):
        raise BridgeError(
            "invalid_request",
            f"payload.{name} must be null or 1-{MAX_FILTER_CHARS} Unicode scalar values.",
        )
    return value


def _validate_request(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise BridgeError("invalid_request", "Request must be a JSON object.")
    if not _has_only_keys(document, REQUEST_KEYS):
        raise BridgeError(
            "invalid_request",
            "Request must contain exactly protocol, request_id, operation, project_root, and payload.",
        )
    if not _valid_request_id(document["request_id"]):
        raise BridgeError(
            "invalid_request",
            "request_id must be 1-64 ASCII letters, digits, dots, underscores, or hyphens.",
        )
    if not isinstance(document["protocol"], str):
        raise BridgeError("invalid_request", "protocol must be a string.")
    if document["protocol"] != PROTOCOL:
        raise BridgeError(
            "unsupported_protocol",
            f"Unsupported protocol; expected {PROTOCOL}.",
        )
    if not isinstance(document["operation"], str) or document["operation"] not in OPERATIONS:
        raise BridgeError(
            "invalid_request",
            "operation must be one of: project_snapshot, task_detail.",
        )
    project_root = document["project_root"]
    if not _is_scalar_text(
        project_root,
        minimum=1,
        maximum=MAX_PROJECT_ROOT_CHARS,
    ):
        raise BridgeError(
            "invalid_request",
            f"project_root must be 1-{MAX_PROJECT_ROOT_CHARS} Unicode scalar values.",
        )
    try:
        root_path = Path(project_root)
    except (OSError, ValueError) as exc:
        raise BridgeError("invalid_request", "project_root is not a valid local path.") from exc
    if not root_path.is_absolute():
        raise BridgeError("invalid_request", "project_root must be an absolute local path.")
    if os.name == "nt" and root_path.anchor.startswith("\\\\"):
        raise BridgeError("invalid_request", "UNC project roots are not supported.")

    payload = document["payload"]
    if not isinstance(payload, dict):
        raise BridgeError("invalid_request", "payload must be an object.")
    if document["operation"] == "project_snapshot":
        expected = frozenset({"status", "workflow"})
        if not _has_only_keys(payload, expected):
            raise BridgeError(
                "invalid_request",
                "project_snapshot payload must contain exactly status and workflow.",
            )
        _validate_filter(payload["status"], "status")
        _validate_filter(payload["workflow"], "workflow")
    else:
        expected = frozenset({"task_id"})
        if not _has_only_keys(payload, expected):
            raise BridgeError(
                "invalid_request",
                "task_detail payload must contain exactly task_id.",
            )
        if not _is_scalar_text(
            payload["task_id"],
            minimum=1,
            maximum=MAX_TASK_ID_CHARS,
        ):
            raise BridgeError(
                "invalid_request",
                f"payload.task_id must be 1-{MAX_TASK_ID_CHARS} Unicode scalar values.",
            )
    return document


def _resource_id_from_relative(relative: str, kind: str) -> str:
    digest = hashlib.sha256(f"{kind}\0{relative}".encode("utf-8")).hexdigest()[:24]
    return f"{kind}-{digest}"


def _contained_path(
    root: Path,
    candidate: Path,
    label: str,
    *,
    strict: bool,
) -> Path:
    try:
        resolved = candidate.resolve(strict=strict)
    except (OSError, RuntimeError) as exc:
        raise BridgeError(
            "invalid_project",
            f"Unable to resolve the configured {label}.",
        ) from exc
    if resolved != root and not resolved.is_relative_to(root):
        identifier = _resource_id_for_untrusted(label, candidate)
        raise BridgeError(
            "out_of_scope_resource",
            f"Configured {label} resolves outside the selected project.",
            [{
                "code": "out_of_scope_resource",
                "status": "ERROR",
                "resource_id": identifier,
                "message": f"Configured {label} is outside the selected project boundary.",
            }],
        )
    return resolved


def _resource_id_for_untrusted(label: str, path: Path) -> str:
    # Do not expose the path.  This identifier is correlation evidence only.
    digest = hashlib.sha256(f"{label}\0{os.fspath(path)}".encode("utf-8")).hexdigest()[:24]
    return f"blocked-{digest}"


def _read_bounded_file(path: Path, label: str, root: Path) -> bytes:
    """Read one regular file through a bounded handle, not a later path lookup."""
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise BridgeError("invalid_project", f"Unable to read {label}.") from exc
    try:
        with os.fdopen(descriptor, "rb") as stream:
            try:
                file_stat = os.fstat(stream.fileno())
            except OSError as exc:
                raise BridgeError(
                    "invalid_project", f"Unable to inspect {label}."
                ) from exc
            if not stat.S_ISREG(file_stat.st_mode):
                raise BridgeError("invalid_project", f"{label} is not a regular file.")
            confirmed_path = _contained_path(
                root, path, label, strict=True
            )
            try:
                confirmed_stat = confirmed_path.stat()
            except OSError as exc:
                raise BridgeError(
                    "invalid_project", f"Unable to verify {label}."
                ) from exc
            if not os.path.samestat(file_stat, confirmed_stat):
                raise BridgeError(
                    "invalid_project",
                    f"{label} changed while the project snapshot was captured.",
                )
            if file_stat.st_size > MAX_YAML_BYTES:
                raise BridgeError(
                    "resource_limit",
                    f"{label} exceeds the {MAX_YAML_BYTES}-byte YAML limit.",
                )
            data = stream.read(MAX_YAML_BYTES + 1)
    except BridgeError:
        raise
    except OSError as exc:
        raise BridgeError("invalid_project", f"Unable to read {label}.") from exc
    if len(data) > MAX_YAML_BYTES:
        raise BridgeError(
            "resource_limit",
            f"{label} exceeds the {MAX_YAML_BYTES}-byte YAML limit.",
        )
    return data


def _read_manifest(data: bytes) -> dict[str, Any]:
    try:
        document = yaml.safe_load(data.decode("utf-8", errors="strict"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise BridgeError(
            "invalid_project",
            f"Project Manifest is unreadable or invalid YAML: {exc}",
        ) from exc
    if not isinstance(document, dict):
        raise BridgeError("invalid_project", "Project Manifest must be a mapping/object.")
    try:
        validator = load_validator("project-manifest.schema.json")
        errors = schema_errors(validator, document)
    except Exception as exc:
        raise BridgeError(
            "invalid_catalog",
            "The packaged Project Manifest schema could not be loaded.",
        ) from exc
    messages = [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]
    messages.extend(manifest_semantic_errors(document))
    if messages:
        diagnostics = [
            {
                "code": "manifest_validation",
                "status": "FAIL",
                "resource_id": "project-manifest",
                "message": message,
            }
            for message in messages
        ]
        raise BridgeError(
            "invalid_project",
            "Project Manifest does not satisfy the supported contract.",
            diagnostics,
        )
    return document


def _schema_path(name: str) -> Path:
    try:
        resource = schema_resource(name)
        if resource is None or not resource.is_file():
            raise FileNotFoundError(name)
        return Path(resource).resolve(strict=True)
    except Exception as exc:
        raise BridgeError(
            "invalid_catalog",
            f"Required packaged schema is unavailable: {name}.",
        ) from exc


def _preflight_project(project_root: str, snapshot_root: Path) -> ProjectContext:
    """Capture every project-owned input once into a request-local snapshot."""
    requested_root = Path(project_root)
    try:
        root = requested_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BridgeError("invalid_project", "Selected project root does not exist.") from exc
    if not root.is_dir():
        raise BridgeError("invalid_project", "Selected project root is not a directory.")

    try:
        snapshot_root = snapshot_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BridgeError(
            "internal_error", "Bridge could not create its project snapshot."
        ) from exc
    source_relatives: dict[str, str] = {".": "."}

    def register(snapshot_path: Path, source_path: Path) -> None:
        try:
            snapshot_relative = snapshot_path.relative_to(snapshot_root).as_posix()
            source_relative = source_path.relative_to(root).as_posix()
        except ValueError as exc:
            raise BridgeError(
                "internal_error", "Bridge could not map its project snapshot."
            ) from exc
        source_relatives[snapshot_relative] = source_relative

    manifest_candidate = root / ".ai" / "project.yaml"
    manifest_probe = _contained_path(
        root,
        manifest_candidate,
        "Project Manifest",
        strict=False,
    )
    if not manifest_probe.exists():
        raise BridgeError(
            "unmanaged_project",
            "The selected root does not contain .ai/project.yaml.",
        )
    manifest_path = _contained_path(
        root,
        manifest_candidate,
        "Project Manifest",
        strict=True,
    )
    if not manifest_path.is_file():
        raise BridgeError("invalid_project", "The exact Project Manifest marker is not a file.")
    manifest_bytes = _read_bounded_file(manifest_path, "Project Manifest", root)
    manifest = _read_manifest(manifest_bytes)

    snapshot_manifest = snapshot_root / ".ai" / "project.yaml"
    snapshot_manifest.parent.mkdir(parents=True)
    snapshot_manifest.write_bytes(manifest_bytes)
    register(snapshot_manifest, manifest_path)

    try:
        configured_tasks = task_directory(root, manifest)
    except (OSError, ValueError) as exc:
        raise BridgeError("invalid_project", f"Invalid Manifest Task directory: {exc}") from exc
    tasks_dir = _contained_path(
        root,
        configured_tasks,
        "Task directory",
        strict=False,
    )
    if not tasks_dir.is_dir():
        raise BridgeError("invalid_project", "Configured Task directory was not found.")

    try:
        snapshot_tasks_dir = task_directory(snapshot_root, manifest)
    except (OSError, ValueError) as exc:
        raise BridgeError("invalid_project", f"Invalid Manifest Task directory: {exc}") from exc
    snapshot_tasks_dir = _contained_path(
        snapshot_root,
        snapshot_tasks_dir,
        "snapshot Task directory",
        strict=False,
    )
    snapshot_tasks_dir.mkdir(parents=True, exist_ok=True)
    register(snapshot_tasks_dir, tasks_dir)

    try:
        entries = sorted(tasks_dir.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise BridgeError("invalid_project", "Configured Task directory is unreadable.") from exc
    task_directories: list[tuple[Path, Path]] = []
    for entry in entries:
        resolved_entry = _contained_path(
            root,
            entry,
            "Task directory entry",
            strict=False,
        )
        try:
            is_directory = resolved_entry.is_dir()
        except OSError as exc:
            raise BridgeError("invalid_project", "A Task directory entry is unreadable.") from exc
        if not is_directory:
            continue
        task_directories.append((entry, resolved_entry))
    if len(task_directories) > MAX_TASK_DIRECTORIES:
        raise BridgeError(
            "resource_limit",
            f"Immediate Task directory count exceeds the limit of {MAX_TASK_DIRECTORIES}.",
        )
    for entry, directory in task_directories:
        snapshot_directory = snapshot_tasks_dir / entry.name
        snapshot_directory.mkdir(exist_ok=True)
        register(snapshot_directory, directory)
        for artifact_name in CANONICAL_ARTIFACTS:
            artifact = directory / artifact_name
            resolved_artifact = _contained_path(
                root,
                artifact,
                f"Task artifact {artifact_name}",
                strict=False,
            )
            snapshot_artifact = snapshot_directory / artifact_name
            register(snapshot_artifact, resolved_artifact)
            if not resolved_artifact.is_file():
                continue
            if artifact_name == "task.yaml":
                snapshot_artifact.write_bytes(
                    _read_bounded_file(resolved_artifact, "Task YAML", root)
                )
            else:
                # The public contract exposes canonical Markdown presence only.
                snapshot_artifact.touch()

    workflows_candidate = root / "workflows"
    workflows_dir = _contained_path(
        root,
        workflows_candidate,
        "Workflow directory",
        strict=False,
    )
    snapshot_workflows_dir = snapshot_root / "workflows"
    register(snapshot_workflows_dir, workflows_dir)
    workflow_files: list[tuple[Path, Path]] = []
    if workflows_dir.is_dir():
        snapshot_workflows_dir.mkdir(exist_ok=True)
        try:
            candidates = sorted(workflows_dir.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise BridgeError("invalid_project", "Workflow directory is unreadable.") from exc
        for candidate in candidates:
            if candidate.suffix.lower() not in {".yaml", ".yml"}:
                continue
            resolved_workflow = _contained_path(
                root,
                candidate,
                "Workflow YAML",
                strict=False,
            )
            if resolved_workflow.is_file():
                workflow_files.append((candidate, resolved_workflow))
    if len(workflow_files) > MAX_WORKFLOW_FILES:
        raise BridgeError(
            "resource_limit",
            f"Workflow YAML count exceeds the limit of {MAX_WORKFLOW_FILES}.",
        )
    for candidate, resolved_workflow in workflow_files:
        snapshot_workflow = snapshot_workflows_dir / candidate.name
        snapshot_workflow.write_bytes(
            _read_bounded_file(resolved_workflow, "Workflow YAML", root)
        )
        register(snapshot_workflow, resolved_workflow)

    roles = load_role_catalog()
    if not roles.is_valid:
        raise BridgeError(
            "invalid_catalog",
            "The packaged canonical Role catalog could not be loaded.",
        )

    return ProjectContext(
        root=root,
        snapshot_root=snapshot_root,
        manifest_path=snapshot_manifest,
        manifest=manifest,
        tasks_dir=snapshot_tasks_dir,
        workflows_dir=snapshot_workflows_dir,
        task_schema=_schema_path("task.schema.json"),
        workflow_schema=_schema_path("workflow.schema.json"),
        role_catalog=roles,
        source_relatives=MappingProxyType(source_relatives),
    )


def _source_relative(context: ProjectContext, snapshot_path: Path) -> str:
    """Return the preflight-time source identity for a snapshot resource."""
    try:
        relative = snapshot_path.resolve(strict=False).relative_to(
            context.snapshot_root
        ).as_posix()
    except (OSError, RuntimeError, ValueError) as exc:
        raise BridgeError(
            "out_of_scope_resource",
            "A snapshot resource is outside the request boundary.",
        ) from exc
    return context.source_relatives.get(relative, relative)


def _snapshot_resource_id(
    context: ProjectContext, snapshot_path: Path, kind: str
) -> str:
    return _resource_id_from_relative(_source_relative(context, snapshot_path), kind)


def _artifact_descriptors(context: ProjectContext, task_dir: Path) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for name in CANONICAL_ARTIFACTS:
        path = task_dir / name
        source_relative = _source_relative(context, path)
        state = "present" if path.is_file() else "missing"
        descriptors.append(
            {
                "artifact_id": _resource_id_from_relative(
                    source_relative, "artifact"
                ),
                "label": name,
                "state": state,
                "relative_path": source_relative,
            }
        )
    return descriptors


def _task_summary(context: ProjectContext, summary: Any) -> dict[str, Any]:
    artifacts = _artifact_descriptors(context, summary.task_dir)
    artifact_states = {item["label"]: item["state"] for item in artifacts}
    return {
        "resource_id": _snapshot_resource_id(context, summary.task_dir, "task"),
        "id": summary.task_id,
        "title": summary.title,
        "type": summary.task_type,
        "status": summary.status,
        "workflow": summary.workflow,
        "workflow_resolution": summary.resolution,
        "schema_status": "VALID",
        "artifact_health": {
            "task_yaml": artifact_states["task.yaml"] == "present",
            "context_md": artifact_states["context.md"] == "present",
            "acceptance_criteria_md": (
                artifact_states["acceptance-criteria.md"] == "present"
            ),
            "review_md": artifact_states["review.md"] == "present",
        },
    }


def _load_inventory(context: ProjectContext):
    return discover_tasks(
        tasks_dir=context.tasks_dir,
        project_manifest_path=context.manifest_path,
        schema_path=context.task_schema,
        workflows_dir=context.workflows_dir,
    )


def _path_resource_id(context: ProjectContext, path: Path, kind: str) -> str:
    return _snapshot_resource_id(context, path, kind)


def _safe_project_message(context: ProjectContext, value: object) -> str:
    """Remove the selected root from diagnostics intended for UI display."""
    message = str(value)
    for root_text in {
        str(context.root),
        context.root.as_posix(),
        str(context.snapshot_root),
        context.snapshot_root.as_posix(),
    }:
        message = message.replace(root_text, "<selected-project>")
    return _bounded_text(message)


def _inventory_anomalies(context: ProjectContext, inventory: Any) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for anomaly in inventory.anomalies:
        message = anomaly.reason
        if anomaly.details:
            message += ": " + "; ".join(str(item) for item in anomaly.details)
        diagnostics.append(
            {
                "code": "task_inventory_anomaly",
                "status": "FAIL",
                "resource_id": _path_resource_id(context, anomaly.dir_path, "task"),
                "message": _safe_project_message(context, message),
            }
        )
    seen_ids: set[str] = set()
    for summary in inventory.valid_tasks:
        if summary.task_id in seen_ids:
            diagnostics.append(
                {
                    "code": "duplicate_task_id",
                    "status": "FAIL",
                    "resource_id": _path_resource_id(
                        context, summary.task_dir, "task"
                    ),
                    "message": _bounded_text(
                        f"Duplicate declared Task ID: {summary.task_id}"
                    ),
                }
            )
        seen_ids.add(summary.task_id)
    return _bounded_diagnostics(diagnostics)


def _validation_evidence(context: ProjectContext) -> dict[str, Any]:
    evidence = validate_project(context.snapshot_root)
    findings: list[dict[str, Any]] = []
    for finding in evidence.findings:
        findings.append(
            {
                "code": "structural_validation",
                "status": finding.status,
                "resource_id": _path_resource_id(context, finding.path, "validation"),
                "message": _safe_project_message(context, finding.message),
            }
        )
    return {"status": evidence.status, "findings": _bounded_diagnostics(findings)}


def _snapshot(context: ProjectContext, payload: dict[str, Any]) -> dict[str, Any]:
    inventory = _load_inventory(context)
    anomalies = _inventory_anomalies(context, inventory)
    validation = _validation_evidence(context)
    if len(anomalies) + len(validation["findings"]) > MAX_DIAGNOSTICS:
        raise BridgeError(
            "resource_limit",
            f"Combined diagnostic count exceeds the limit of {MAX_DIAGNOSTICS}.",
        )
    status_filter = _validate_filter(payload["status"], "status")
    workflow_filter = _validate_filter(payload["workflow"], "workflow")
    selected = filter_tasks(
        inventory.valid_tasks,
        status=status_filter,
        workflow=workflow_filter,
    )
    state = {"PASS": "managed", "FAIL": "invalid", "ERROR": "error"}[validation["status"]]
    project = context.manifest["project"]
    return {
        "project": {
            "state": state,
            "id": project["id"],
            "name": project["name"],
        },
        "snapshot_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tasks": [_task_summary(context, item) for item in selected],
        "anomalies": anomalies,
        "filters": {
            "statuses": sorted({item.status for item in inventory.valid_tasks}),
            "workflows": sorted(
                {item.workflow for item in inventory.valid_tasks if item.workflow is not None}
            ),
        },
        "validation": validation,
    }


def _effective_metadata(inspection: Any) -> dict[str, Any]:
    return {
        "risk": {"value": inspection.risk, "source": inspection.risk_source},
        "complexity": {
            "value": inspection.complexity,
            "source": inspection.complexity_source,
        },
        "execution_mode": {
            "value": inspection.execution_mode,
            "source": inspection.execution_mode_source,
        },
        "quality_gates": list(inspection.effective_quality_gates),
        "human_control": {
            key: {"value": value, "source": source}
            for key, (value, source) in sorted(inspection.effective_human_control.items())
        },
    }


def _workflow_detail(context: ProjectContext, inspection: Any) -> dict[str, Any] | None:
    if inspection.workflow is None or inspection.workflow_resolution != "RESOLVED":
        return None
    workflows = load_workflow_catalog(
        workflows_dir=context.workflows_dir,
        schema_path=context.workflow_schema,
    )
    workflow = workflows.get(inspection.workflow)
    if workflow is None:
        raise BridgeError("invalid_catalog", "Declared Workflow could not be resolved.")
    roles = context.role_catalog
    stages: list[dict[str, Any]] = []
    for stage in workflow.stages:
        required_roles: list[dict[str, Any]] = []
        for role_id in stage.required_roles:
            role = roles.get(role_id)
            if role is None:
                raise BridgeError(
                    "invalid_catalog",
                    f"Workflow references an unknown canonical Role: {role_id}.",
                )
            required_roles.append(
                {
                    "id": role["id"],
                    "name": role["name"],
                    "purpose": role["purpose"],
                    "required_capabilities": list(role["required_capabilities"]),
                }
            )
        stages.append(
            {
                "id": stage.id,
                "purpose": stage.purpose,
                "human_control_checkpoint": stage.human_control_checkpoint is True,
                "required_quality_gates": list(stage.required_quality_gates),
                "required_roles": required_roles,
            }
        )
    return {
        "id": workflow.id,
        "name": workflow.name,
        "definition_not_execution": True,
        "stages": stages,
    }


def _detail(context: ProjectContext, payload: dict[str, Any]) -> dict[str, Any]:
    inventory = _load_inventory(context)
    task_id = payload["task_id"]
    matches = [item for item in inventory.valid_tasks if item.task_id == task_id]
    if not matches:
        raise BridgeError(
            "task_not_found",
            f"No schema-valid Task has the exact declared ID '{_bounded_text(task_id)}'.",
        )
    if len(matches) > 1:
        raise BridgeError(
            "task_id_ambiguous",
            f"Multiple schema-valid Tasks have the exact declared ID '{_bounded_text(task_id)}'.",
        )
    summary = matches[0]
    inspection = inspect_task(
        task_dir=summary.task_dir,
        project_manifest_path=context.manifest_path,
        schema_path=context.task_schema,
        workflows_dir=context.workflows_dir,
    )
    return {
        "task": _task_summary(context, summary),
        "effective": _effective_metadata(inspection),
        "artifacts": _artifact_descriptors(context, summary.task_dir),
        "workflow": _workflow_detail(context, inspection),
    }


def process_request_bytes(data: bytes) -> dict[str, Any]:
    """Process one UTF-8 JSON request and return one closed response object."""
    request_id: str | None = None
    try:
        document = _parse_json(data)
        request_id = _candidate_request_id(document)
        request = _validate_request(document)
        request_id = request["request_id"]
        with tempfile.TemporaryDirectory(prefix="aio-ide-snapshot-") as directory:
            context = _preflight_project(request["project_root"], Path(directory))
            if request["operation"] == "project_snapshot":
                result = _snapshot(context, request["payload"])
            else:
                result = _detail(context, request["payload"])
        return _response(request_id, result=result)
    except BridgeError as exc:
        return _response(request_id, error=exc)
    except Exception:
        # Unexpected exception text can contain host paths or project data.  It
        # intentionally stays out of the wire response and stderr.
        return _response(
            request_id,
            error=BridgeError("internal_error", "Bridge could not complete the request."),
        )


def _serialized_response(response: dict[str, Any]) -> bytes:
    try:
        encoded = (
            json.dumps(
                response,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        encoded = b""
    if encoded and len(encoded) <= MAX_RESPONSE_BYTES:
        return encoded
    request_id = response.get("request_id") if isinstance(response, dict) else None
    fallback = _response(
        request_id if _valid_request_id(request_id) else None,
        error=BridgeError(
            "resource_limit",
            f"Response exceeds the {MAX_RESPONSE_BYTES}-byte limit.",
        ),
    )
    return (
        json.dumps(fallback, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def main() -> int:
    """Read one bounded request from stdin and emit one JSON-only response."""
    try:
        data = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        response = process_request_bytes(data)
        sys.stdout.buffer.write(_serialized_response(response))
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        # A nonzero exit is reserved for failure before a response can be
        # serialized or written.  Do not put diagnostic data on stderr.
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
