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
    if name not in {"task.schema.json", "workflow.schema.json"}:
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
