"""Access the tool's canonical schemas in installations and uninstalled sources."""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


def schema_resource(name: str) -> Traversable | None:
    """Return a bundled schema, never a schema from the active project.

    Setuptools maps canonical schemas/ into the private resource package.
    Uninstalled source wrappers also work: only this module's own checkout
    (identified by its packaging metadata) may supply that resource directory.
    """
    if name not in {
        "actor.schema.json",
        "actor-availability.schema.json",
        "assignment.schema.json",
        "inference-option.schema.json",
        "inference-option-availability.schema.json",
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

    resource = schema_resource(name)
    if resource is None:
        raise FileNotFoundError(f"Required tool schema missing: {name}")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_errors(validator, document):
    """Deterministic structural errors, retaining jsonschema evidence objects."""
    return sorted(validator.iter_errors(document),
                  key=lambda error: (str(list(error.absolute_path)), str(error.validator)))
