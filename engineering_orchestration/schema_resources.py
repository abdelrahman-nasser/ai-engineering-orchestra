"""Access the tool's canonical schemas in installations and uninstalled sources."""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


_AGENT_EXECUTION_CONTRACT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-contract.schema.json"
)
_AGENT_EXECUTION_RUN_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-run.schema.json"
)
_AGENT_EXECUTION_AUTHORIZATION_GRANT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-authorization-grant.schema.json"
)
_AGENT_OPERATION_TOOL_BINDING_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-operation-tool-binding.schema.json"
)
_OFFLINE_SCHEMA_REFERENCES = {
    "agent-execution-dispatch-admission.schema.json": (
        (
            _AGENT_EXECUTION_AUTHORIZATION_GRANT_SCHEMA_ID,
            "agent-execution-authorization-grant.schema.json",
        ),
        (
            _AGENT_OPERATION_TOOL_BINDING_SCHEMA_ID,
            "agent-operation-tool-binding.schema.json",
        ),
        (
            _AGENT_EXECUTION_RUN_SCHEMA_ID,
            "agent-execution-run.schema.json",
        ),
        (
            _AGENT_EXECUTION_CONTRACT_SCHEMA_ID,
            "agent-execution-contract.schema.json",
        ),
    ),
    "agent-operation-tool-binding.schema.json": (
        (
            _AGENT_EXECUTION_RUN_SCHEMA_ID,
            "agent-execution-run.schema.json",
        ),
        (
            _AGENT_EXECUTION_CONTRACT_SCHEMA_ID,
            "agent-execution-contract.schema.json",
        ),
    ),
    "agent-execution-authorization-grant.schema.json": (
        (
            _AGENT_EXECUTION_RUN_SCHEMA_ID,
            "agent-execution-run.schema.json",
        ),
        (
            _AGENT_EXECUTION_CONTRACT_SCHEMA_ID,
            "agent-execution-contract.schema.json",
        ),
    ),
    "agent-execution-run.schema.json": (
        (
            _AGENT_EXECUTION_CONTRACT_SCHEMA_ID,
            "agent-execution-contract.schema.json",
        ),
    ),
}


def schema_resource(name: str) -> Traversable | None:
    """Return a bundled schema, never a schema from the active project.

    Setuptools maps canonical schemas/ into the private resource package.
    Uninstalled source wrappers also work: only this module's own checkout
    (identified by its packaging metadata) may supply that resource directory.
    """
    if name not in {
        "actor.schema.json",
        "actor-availability.schema.json",
        "actor-runtime-applicability.schema.json",
        "agent-operation-tool-binding.schema.json",
        "agent-execution-authorization-grant.schema.json",
        "agent-execution-dispatch-admission.schema.json",
        "agent-execution-authorization-evidence.schema.json",
        "agent-execution-contract.schema.json",
        "agent-execution-run.schema.json",
        "agent-runtime-option.schema.json",
        "agent-runtime-option-availability.schema.json",
        "assignment.schema.json",
        "environment-operation-permission.schema.json",
        "inference-option.schema.json",
        "inference-option-availability.schema.json",
        "operation-requirement.schema.json",
        "runtime-operation-capability.schema.json",
        "runtime-inference-compatibility.schema.json",
        "role.schema.json",
        "task.schema.json",
        "workflow.schema.json",
        "project-manifest.schema.json",
    }:
        raise ValueError(f"Unknown tool schema: {name}")
    try:
        resource = files("engineering_orchestration._schemas").joinpath(name)
    except ModuleNotFoundError as exc:
        if exc.name != "engineering_orchestration._schemas":
            raise
        source_root = Path(__file__).resolve().parent.parent
        if not (source_root / "pyproject.toml").is_file():
            return None
        resource = source_root / "schemas" / name
    return resource if resource.is_file() else None


def load_validator(name: str):
    """Load and self-check a canonical tool schema; resource failures propagate."""
    import json
    from jsonschema import Draft202012Validator

    def load_checked_schema(resource_name: str):
        resource = schema_resource(resource_name)
        if resource is None:
            raise FileNotFoundError(
                f"Required tool schema missing: {resource_name}"
            )
        document = json.loads(resource.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)
        return document

    schema = load_checked_schema(name)
    references = _OFFLINE_SCHEMA_REFERENCES.get(name)
    if references is None:
        return Draft202012Validator(schema)

    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource

    def reject_unregistered_reference(uri: str):
        raise NoSuchResource(ref=uri)

    registry = Registry(retrieve=reject_unregistered_reference)
    for canonical_id, referenced_name in references:
        referenced_schema = load_checked_schema(referenced_name)
        if (
            not isinstance(referenced_schema, dict)
            or referenced_schema.get("$id") != canonical_id
        ):
            raise ValueError(
                "Bundled schema canonical ID mismatch: "
                f"{referenced_name} must declare {canonical_id}"
            )
        registry = registry.with_resource(
            canonical_id,
            Resource.from_contents(referenced_schema),
        )
    return Draft202012Validator(schema, registry=registry)


def schema_errors(validator, document):
    """Deterministic structural errors, retaining jsonschema evidence objects."""
    return sorted(validator.iter_errors(document),
                  key=lambda error: (str(list(error.absolute_path)), str(error.validator)))
