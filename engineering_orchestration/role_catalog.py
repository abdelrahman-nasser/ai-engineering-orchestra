"""Framework-owned Role catalog backed only by packaged canonical YAML."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from engineering_orchestration import schema_resources


CANONICAL_ROLE_IDS = (
    "architect",
    "documentation-specialist",
    "reviewer",
    "security-reviewer",
    "software-engineer",
)


class RoleCatalogError(Exception):
    """Raised when the framework Role catalog cannot be safely loaded."""


@dataclass
class RoleCatalog:
    """Canonical Role mappings indexed strictly by their declared IDs."""

    roles_source: Traversable | None
    definitions: dict[str, dict[str, Any]] = field(default_factory=dict)
    source_names: dict[str, str] = field(default_factory=dict)
    load_errors: list[str] = field(default_factory=list)
    infrastructure_errors: list[str] = field(default_factory=list)

    def get(self, role_id: str) -> dict[str, Any] | None:
        """Resolve a Role by declared ID; unknown consumer queries return None."""
        return self.definitions.get(role_id)

    def __contains__(self, role_id: str) -> bool:
        return role_id in self.definitions

    @property
    def role_ids(self) -> list[str]:
        """Case-sensitive ascending declared Role IDs."""
        return sorted(self.definitions)

    @property
    def is_valid(self) -> bool:
        """True when at least one Role loaded and no catalog error occurred."""
        return bool(self.definitions) and not self.load_errors


def find_default_roles_resource() -> Traversable | None:
    """Locate tool-owned Roles in source mode or from installed package data.

    Source execution reads the canonical directory beside this implementation.
    Installed execution uses only the private resource package and never falls
    back to a checkout, CWD, or active-project directory.
    """
    source_root = Path(__file__).resolve().parent.parent
    if (source_root / "pyproject.toml").is_file():
        source_roles = source_root / "roles"
        return source_roles if source_roles.is_dir() else None

    package = "engineering_orchestration._roles"
    try:
        resource = files(package)
    except ModuleNotFoundError as exc:
        if exc.name != package:
            raise
        return None
    return resource if resource.is_dir() else None


def find_default_role_schema_path() -> Traversable | None:
    """Locate the packaged Role schema owned by the framework."""
    return schema_resources.schema_resource("role.schema.json")


def _record_error(catalog: RoleCatalog, message: str) -> None:
    """Record corrupt framework-owned data as both load and infrastructure failure."""
    catalog.load_errors.append(message)
    catalog.infrastructure_errors.append(message)


def load_role_catalog(*, raise_on_error: bool = False) -> RoleCatalog:
    """Load canonical framework Roles from package-safe resources.

    The public loader intentionally has no project path or override argument.
    Role identity comes only from each schema-valid document's declared ``id``.
    """
    try:
        roles_source = find_default_roles_resource()
    except Exception as exc:
        roles_source = None
        resource_error = f"Unable to access packaged Role resources: {exc}"
    else:
        resource_error = "Packaged Role resources not found"

    catalog = RoleCatalog(roles_source=roles_source)
    if roles_source is None:
        _record_error(catalog, resource_error)
        if raise_on_error:
            raise RoleCatalogError(resource_error)
        return catalog

    try:
        schema_path = find_default_role_schema_path()
        schema_available = schema_path is not None and schema_path.is_file()
    except Exception as exc:
        schema_path = None
        schema_available = False
        schema_error = f"Unable to access packaged Role schema: {exc}"
    else:
        schema_error = "Required tool schema missing: role.schema.json"

    if not schema_available:
        _record_error(catalog, schema_error)
        if raise_on_error:
            raise RoleCatalogError(schema_error)
        return catalog

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as exc:
        message = f"Failed to load packaged Role schema: {exc}"
        _record_error(catalog, message)
        if raise_on_error:
            raise RoleCatalogError(message) from exc
        return catalog

    try:
        yaml_resources = sorted(
            (
                resource
                for resource in roles_source.iterdir()
                if resource.is_file()
                and Path(resource.name).suffix.lower() in {".yaml", ".yml"}
            ),
            key=lambda resource: resource.name,
        )
    except Exception as exc:
        message = f"Unable to enumerate packaged Role resources: {exc}"
        _record_error(catalog, message)
        if raise_on_error:
            raise RoleCatalogError(message) from exc
        return catalog

    if not yaml_resources:
        message = "No packaged canonical Role YAML resources found"
        _record_error(catalog, message)
        if raise_on_error:
            raise RoleCatalogError(message)
        return catalog

    for resource in yaml_resources:
        try:
            data = yaml.safe_load(resource.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            _record_error(catalog, f"{resource.name}: YAML parse error: {exc}")
            continue
        except (OSError, UnicodeError) as exc:
            _record_error(catalog, f"{resource.name}: unable to read Role: {exc}")
            continue

        if not isinstance(data, dict):
            _record_error(catalog, f"{resource.name}: root content is not a mapping/object")
            continue

        errors = schema_resources.schema_errors(validator, data)
        if errors:
            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path) or "<root>"
                _record_error(
                    catalog,
                    f"{resource.name} [{location}]: {error.message}",
                )
            continue

        role_id = data["id"]
        if role_id in catalog.definitions:
            _record_error(
                catalog,
                f"Duplicate declared Role ID '{role_id}' in {resource.name} "
                f"(already defined in {catalog.source_names[role_id]})",
            )
            continue

        catalog.definitions[role_id] = data
        catalog.source_names[role_id] = resource.name

    actual_ids = set(catalog.definitions)
    expected_ids = set(CANONICAL_ROLE_IDS)
    missing_ids = sorted(expected_ids - actual_ids)
    unexpected_ids = sorted(actual_ids - expected_ids)
    if missing_ids or unexpected_ids:
        parts = []
        if missing_ids:
            parts.append("missing declared IDs: " + ", ".join(missing_ids))
        if unexpected_ids:
            parts.append("unexpected declared IDs: " + ", ".join(unexpected_ids))
        _record_error(
            catalog,
            "Packaged canonical Role ID set mismatch (" + "; ".join(parts) + ")",
        )

    if raise_on_error and catalog.load_errors:
        raise RoleCatalogError("; ".join(catalog.load_errors))
    return catalog
