"""Trusted process-local Agent Operation Tool registry primitives.

This private value layer constructs one atomic immutable registry snapshot from
explicit package-owned declarations.  It performs no discovery, I/O,
availability probing, persistence, dispatch, or invocation.  The snapshot is
only useful when a trusted composition root supplies it to the paired binding
resolver; direct construction of any private value does not establish trust.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from types import MappingProxyType


__all__: tuple[str, ...] = ()


_AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID = (
    "tool::aeo-native-repository-file-read::v1"
)
_TRUSTED_AGENT_OPERATION_TOOL_BINDING_RESOLVER_IMPLEMENTATION_ID = (
    "trusted-agent-operation-tool-binding-resolver::v1"
)
_REPOSITORY_FILE_READ_OPERATION_ID = "repository_file_read"
_SNAPSHOT_AUTHORITY = object()
_MAPPING_PROXY_TYPE = type(MappingProxyType({}))


class _AgentOperationToolImplementationSelector(StrEnum):
    """Closed non-callable implementation-family selector."""

    AEO_NATIVE_REPOSITORY_FILE_READ_V1 = (
        "AEO_NATIVE_REPOSITORY_FILE_READ_V1"
    )


class _AgentOperationToolRegistryOutcome(StrEnum):
    """Closed construction, selection, and lookup outcomes."""

    RESOLVED = "resolved"
    REGISTRY_INVALID = "registry_invalid"
    REGISTRY_UNAVAILABLE = "registry_unavailable"
    REGISTRATION_INVALID = "registration_invalid"
    UNKNOWN_ROUTE = "unknown_route"
    UNKNOWN_TOOL = "unknown_tool"
    DUPLICATE_ROUTE = "duplicate_route"
    DUPLICATE_TOOL_ID = "duplicate_tool_id"
    TOOL_ID_REBIND = "tool_id_rebind"
    ALIAS_INVALID = "alias_invalid"
    ALIAS_TARGET_UNKNOWN = "alias_target_unknown"
    RUNTIME_MISMATCH = "runtime_mismatch"
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    OPERATION_MISMATCH = "operation_mismatch"
    RESOURCE_WIDENING = "resource_widening"
    TOOL_RETIRED = "tool_retired"
    HISTORICAL_MAPPING_MISSING = "historical_mapping_missing"
    ADAPTER_KIND_UNKNOWN = "adapter_kind_unknown"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    INTEGRITY_FAILURE = "integrity_failure"


class _AgentOperationToolRegistryRetryDisposition(StrEnum):
    """Closed guidance that never permits same-Run Tool substitution."""

    NO_RETRY_NEEDED = "no_retry_needed"
    NEW_RUN_REQUIRED = "new_run_required"
    REGISTRY_REMEDIATION_REQUIRED = "registry_remediation_required"
    PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED = (
        "package_or_configuration_remediation_required"
    )
    HISTORICAL_MAPPING_REMEDIATION_REQUIRED = (
        "historical_mapping_remediation_required"
    )
    DO_NOT_RETRY_SAME_RUN = "do_not_retry_same_run"


_OUTCOME_RETRY_DISPOSITIONS = MappingProxyType(
    {
        _AgentOperationToolRegistryOutcome.RESOLVED:
            _AgentOperationToolRegistryRetryDisposition.NO_RETRY_NEEDED,
        _AgentOperationToolRegistryOutcome.REGISTRY_INVALID:
            _AgentOperationToolRegistryRetryDisposition.
            REGISTRY_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.REGISTRY_UNAVAILABLE:
            _AgentOperationToolRegistryRetryDisposition.
            REGISTRY_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE:
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        _AgentOperationToolRegistryOutcome.UNKNOWN_TOOL:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.DUPLICATE_ROUTE:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.DUPLICATE_TOOL_ID:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND:
            _AgentOperationToolRegistryRetryDisposition.
            HISTORICAL_MAPPING_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.ALIAS_INVALID:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.ALIAS_TARGET_UNKNOWN:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH:
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH:
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH:
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        _AgentOperationToolRegistryOutcome.RESOURCE_WIDENING:
            _AgentOperationToolRegistryRetryDisposition.DO_NOT_RETRY_SAME_RUN,
        _AgentOperationToolRegistryOutcome.TOOL_RETIRED:
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        _AgentOperationToolRegistryOutcome.HISTORICAL_MAPPING_MISSING:
            _AgentOperationToolRegistryRetryDisposition.
            HISTORICAL_MAPPING_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.ADAPTER_KIND_UNKNOWN:
            _AgentOperationToolRegistryRetryDisposition.
            PACKAGE_OR_CONFIGURATION_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.FINGERPRINT_MISMATCH:
            _AgentOperationToolRegistryRetryDisposition.
            HISTORICAL_MAPPING_REMEDIATION_REQUIRED,
        _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE:
            _AgentOperationToolRegistryRetryDisposition.
            REGISTRY_REMEDIATION_REQUIRED,
    }
)


@dataclass(frozen=True, slots=True)
class _AgentOperationToolRoute:
    """One exact case-sensitive Runtime/environment/operation route."""

    runtime_option_id: str
    environment_id: str
    operation_id: str


@dataclass(frozen=True, slots=True)
class _AgentOperationToolRegistration:
    """One immutable configured Tool identity on one exact route."""

    runtime_option_id: str
    environment_id: str
    operation_id: str
    tool_id: str
    implementation_selector: _AgentOperationToolImplementationSelector


@dataclass(frozen=True, slots=True)
class _SelectedAgentOperationToolRoute:
    """One active route selected strictly before Run construction."""

    route: _AgentOperationToolRoute
    tool_id: str


@dataclass(frozen=True, slots=True)
class _ResolvedAgentOperationToolRegistration:
    """One exact process-local historical Registration lookup."""

    route: _AgentOperationToolRoute
    registration: _AgentOperationToolRegistration
    snapshot_fingerprint: str


@dataclass(frozen=True, slots=True)
class _AgentOperationToolRegistryAuditMaterial:
    """Closed nonsecret audit material; never authority or a catalog."""

    outcome: _AgentOperationToolRegistryOutcome
    retry_disposition: _AgentOperationToolRegistryRetryDisposition
    run_id: str | None
    route: _AgentOperationToolRoute | None
    tool_id: str | None
    implementation_id: str
    snapshot_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class _AgentOperationToolRegistryBuildResult:
    """Atomic snapshot-construction result."""

    outcome: _AgentOperationToolRegistryOutcome
    retry_disposition: _AgentOperationToolRegistryRetryDisposition
    snapshot: _TrustedAgentOperationToolRegistrySnapshot | None
    audit: _AgentOperationToolRegistryAuditMaterial


@dataclass(frozen=True, slots=True)
class _AgentOperationToolRouteSelectionResult:
    """Atomic pre-Run route-selection result."""

    outcome: _AgentOperationToolRegistryOutcome
    retry_disposition: _AgentOperationToolRegistryRetryDisposition
    selected_route: _SelectedAgentOperationToolRoute | None
    audit: _AgentOperationToolRegistryAuditMaterial


@dataclass(frozen=True, slots=True, init=False, repr=False, eq=False)
class _TrustedAgentOperationToolRegistrySnapshot:
    """Deeply immutable process-local snapshot minted only by the builder."""

    _registrations: tuple[_AgentOperationToolRegistration, ...]
    _aliases: tuple[tuple[str, _AgentOperationToolRoute], ...]
    _retired_routes: frozenset[_AgentOperationToolRoute]
    _registrations_by_route: Mapping[
        _AgentOperationToolRoute,
        _AgentOperationToolRegistration,
    ]
    _registrations_by_scoped_tool_id: Mapping[
        tuple[str, str, str],
        _AgentOperationToolRegistration,
    ]
    _aliases_by_name: Mapping[str, _AgentOperationToolRoute]
    _registration_fingerprint: str
    _authority: object

    def __init__(self) -> None:
        raise TypeError(
            "Trusted registry snapshots are created only by the atomic builder"
        )


def _agent_operation_tool_registry_retry_disposition(
    outcome: _AgentOperationToolRegistryOutcome,
) -> _AgentOperationToolRegistryRetryDisposition:
    """Return the one locked retry disposition for an exact outcome."""

    if type(outcome) is not _AgentOperationToolRegistryOutcome:
        return (
            _AgentOperationToolRegistryRetryDisposition.
            REGISTRY_REMEDIATION_REQUIRED
        )
    return _OUTCOME_RETRY_DISPOSITIONS[outcome]


def _make_agent_operation_tool_registry_audit_material(
    outcome: _AgentOperationToolRegistryOutcome,
    *,
    run_id: str | None = None,
    route: _AgentOperationToolRoute | None = None,
    tool_id: str | None = None,
    snapshot_fingerprint: str | None = None,
) -> _AgentOperationToolRegistryAuditMaterial:
    """Create one closed audit value without free-form diagnostics."""

    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    safe_run_id = run_id if type(run_id) is str and bool(run_id) else None
    safe_route = route if type(route) is _AgentOperationToolRoute else None
    safe_tool_id = tool_id if type(tool_id) is str and bool(tool_id) else None
    safe_fingerprint = (
        snapshot_fingerprint
        if type(snapshot_fingerprint) is str and bool(snapshot_fingerprint)
        else None
    )
    return _AgentOperationToolRegistryAuditMaterial(
        outcome=outcome,
        retry_disposition=retry,
        run_id=safe_run_id,
        route=safe_route,
        tool_id=safe_tool_id,
        implementation_id=(
            _TRUSTED_AGENT_OPERATION_TOOL_BINDING_RESOLVER_IMPLEMENTATION_ID
        ),
        snapshot_fingerprint=safe_fingerprint,
    )


def _route_for_registration(
    registration: _AgentOperationToolRegistration,
) -> _AgentOperationToolRoute:
    return _AgentOperationToolRoute(
        runtime_option_id=registration.runtime_option_id,
        environment_id=registration.environment_id,
        operation_id=registration.operation_id,
    )


def _scoped_tool_identity(
    registration: _AgentOperationToolRegistration,
) -> tuple[str, str, str]:
    return (
        registration.runtime_option_id,
        registration.environment_id,
        registration.tool_id,
    )


def _is_exact_nonempty_string(value: object) -> bool:
    return type(value) is str and bool(value)


def _is_exact_nonempty_utf8_identifier(value: object) -> bool:
    """Return whether one exact identifier is strictly UTF-8 encodable."""

    if not _is_exact_nonempty_string(value):
        return False
    assert type(value) is str
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _route_validation_outcome(
    route: object,
) -> _AgentOperationToolRegistryOutcome | None:
    if type(route) is not _AgentOperationToolRoute:
        return _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID
    if not _is_exact_nonempty_utf8_identifier(route.runtime_option_id):
        return _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH
    if not _is_exact_nonempty_utf8_identifier(route.environment_id):
        return _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH
    if (
        not _is_exact_nonempty_utf8_identifier(route.operation_id)
        or route.operation_id != _REPOSITORY_FILE_READ_OPERATION_ID
    ):
        return _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH
    return None


def _registration_validation_outcome(
    registration: object,
) -> _AgentOperationToolRegistryOutcome | None:
    if type(registration) is not _AgentOperationToolRegistration:
        return _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID
    if (
        type(registration.implementation_selector)
        is not _AgentOperationToolImplementationSelector
    ):
        return _AgentOperationToolRegistryOutcome.ADAPTER_KIND_UNKNOWN
    if not all(
        _is_exact_nonempty_utf8_identifier(identifier)
        for identifier in (
            registration.runtime_option_id,
            registration.environment_id,
            registration.operation_id,
            registration.tool_id,
            registration.implementation_selector.value,
        )
    ):
        return _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID
    route_outcome = _route_validation_outcome(
        _route_for_registration(registration)
    )
    if route_outcome is not None:
        if route_outcome is _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH:
            return route_outcome
        return _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID
    return None


def _canonical_registration_key(
    registration: _AgentOperationToolRegistration,
) -> tuple[str, str, str, str, str]:
    return (
        registration.runtime_option_id,
        registration.environment_id,
        registration.operation_id,
        registration.tool_id,
        registration.implementation_selector.value,
    )


def _registration_fingerprint(
    registrations: tuple[_AgentOperationToolRegistration, ...],
) -> str:
    payload = json.dumps(
        [_canonical_registration_key(item) for item in registrations],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def _capture_once(values: object) -> tuple[object, ...] | None:
    try:
        return tuple(values)  # type: ignore[arg-type]
    except Exception:
        return None


def _build_rejection(
    outcome: _AgentOperationToolRegistryOutcome,
    *,
    snapshot_fingerprint: str | None = None,
) -> _AgentOperationToolRegistryBuildResult:
    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    return _AgentOperationToolRegistryBuildResult(
        outcome=outcome,
        retry_disposition=retry,
        snapshot=None,
        audit=_make_agent_operation_tool_registry_audit_material(
            outcome,
            snapshot_fingerprint=snapshot_fingerprint,
        ),
    )


def _mint_snapshot(
    registrations: tuple[_AgentOperationToolRegistration, ...],
    aliases: tuple[tuple[str, _AgentOperationToolRoute], ...],
    retired_routes: frozenset[_AgentOperationToolRoute],
    registrations_by_route: dict[
        _AgentOperationToolRoute,
        _AgentOperationToolRegistration,
    ],
    registrations_by_scoped_tool_id: dict[
        tuple[str, str, str],
        _AgentOperationToolRegistration,
    ],
    aliases_by_name: dict[str, _AgentOperationToolRoute],
    registration_fingerprint: str,
) -> _TrustedAgentOperationToolRegistrySnapshot:
    snapshot = object.__new__(_TrustedAgentOperationToolRegistrySnapshot)
    object.__setattr__(snapshot, "_registrations", registrations)
    object.__setattr__(snapshot, "_aliases", aliases)
    object.__setattr__(snapshot, "_retired_routes", retired_routes)
    object.__setattr__(
        snapshot,
        "_registrations_by_route",
        MappingProxyType(dict(registrations_by_route)),
    )
    object.__setattr__(
        snapshot,
        "_registrations_by_scoped_tool_id",
        MappingProxyType(dict(registrations_by_scoped_tool_id)),
    )
    object.__setattr__(
        snapshot,
        "_aliases_by_name",
        MappingProxyType(dict(aliases_by_name)),
    )
    object.__setattr__(
        snapshot,
        "_registration_fingerprint",
        registration_fingerprint,
    )
    object.__setattr__(snapshot, "_authority", _SNAPSHOT_AUTHORITY)
    return snapshot


def _snapshot_integrity_outcome(
    snapshot: object,
) -> _AgentOperationToolRegistryOutcome | None:
    """Check observable snapshot coherence without treating hash as authority."""

    if type(snapshot) is not _TrustedAgentOperationToolRegistrySnapshot:
        return _AgentOperationToolRegistryOutcome.REGISTRY_UNAVAILABLE
    try:
        if snapshot._authority is not _SNAPSHOT_AUTHORITY:
            return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
        if (
            type(snapshot._registrations) is not tuple
            or type(snapshot._aliases) is not tuple
            or type(snapshot._retired_routes) is not frozenset
            or type(snapshot._registrations_by_route) is not _MAPPING_PROXY_TYPE
            or type(snapshot._registrations_by_scoped_tool_id)
            is not _MAPPING_PROXY_TYPE
            or type(snapshot._aliases_by_name) is not _MAPPING_PROXY_TYPE
            or not _is_exact_nonempty_string(
                snapshot._registration_fingerprint
            )
        ):
            return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE

        if len(snapshot._registrations) != len(
            snapshot._registrations_by_route
        ):
            return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
        if len(snapshot._registrations) != len(
            snapshot._registrations_by_scoped_tool_id
        ):
            return _AgentOperationToolRegistryOutcome.UNKNOWN_TOOL

        for registration in snapshot._registrations:
            if _registration_validation_outcome(registration) is not None:
                return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            route = _route_for_registration(registration)
            scoped_identity = _scoped_tool_identity(registration)
            if snapshot._registrations_by_route.get(route) is not registration:
                return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            scoped_registration = (
                snapshot._registrations_by_scoped_tool_id.get(scoped_identity)
            )
            if scoped_registration is None:
                return _AgentOperationToolRegistryOutcome.UNKNOWN_TOOL
            if scoped_registration is not registration:
                return _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND

        if len(snapshot._aliases) != len(snapshot._aliases_by_name):
            return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
        for alias_entry in snapshot._aliases:
            if (
                type(alias_entry) is not tuple
                or len(alias_entry) != 2
                or not _is_exact_nonempty_utf8_identifier(alias_entry[0])
                or type(alias_entry[1]) is not _AgentOperationToolRoute
                or _route_validation_outcome(alias_entry[1]) is not None
            ):
                return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            alias, target = alias_entry
            if snapshot._aliases_by_name.get(alias) is not target:
                return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            if target not in snapshot._registrations_by_route:
                return _AgentOperationToolRegistryOutcome.ALIAS_TARGET_UNKNOWN

        if any(
            type(route) is not _AgentOperationToolRoute
            or _route_validation_outcome(route) is not None
            or route not in snapshot._registrations_by_route
            for route in snapshot._retired_routes
        ):
            return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE

        expected_fingerprint = _registration_fingerprint(
            snapshot._registrations
        )
        if expected_fingerprint != snapshot._registration_fingerprint:
            return _AgentOperationToolRegistryOutcome.FINGERPRINT_MISMATCH
    except Exception:
        return _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
    return None


def _make_aeo_native_repository_file_read_registration(
    runtime_option_id: str,
    environment_id: str,
) -> _AgentOperationToolRegistration:
    """Make the identity-only native reader declaration for one exact route."""

    registration = _AgentOperationToolRegistration(
        runtime_option_id=runtime_option_id,
        environment_id=environment_id,
        operation_id=_REPOSITORY_FILE_READ_OPERATION_ID,
        tool_id=_AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID,
        implementation_selector=(
            _AgentOperationToolImplementationSelector.
            AEO_NATIVE_REPOSITORY_FILE_READ_V1
        ),
    )
    if _registration_validation_outcome(registration) is not None:
        raise ValueError(
            "runtime_option_id and environment_id must be exact nonempty "
            "strict-UTF-8-encodable strings"
        )
    return registration


def _build_trusted_agent_operation_tool_registry_snapshot(
    registrations: Iterable[_AgentOperationToolRegistration],
    *,
    aliases: Iterable[tuple[str, _AgentOperationToolRoute]] = (),
    retired_routes: Iterable[_AgentOperationToolRoute] = (),
    prior_snapshot: _TrustedAgentOperationToolRegistrySnapshot | None = None,
    expected_fingerprint: str | None = None,
) -> _AgentOperationToolRegistryBuildResult:
    """Atomically validate, own, freeze, and publish one registry snapshot."""

    captured_registrations = _capture_once(registrations)
    if captured_registrations is None:
        return _build_rejection(
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID
        )
    if not captured_registrations:
        return _build_rejection(
            _AgentOperationToolRegistryOutcome.REGISTRY_UNAVAILABLE
        )

    captured_aliases = _capture_once(aliases)
    captured_retired_routes = _capture_once(retired_routes)
    if captured_aliases is None or captured_retired_routes is None:
        return _build_rejection(
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID
        )

    exact_registrations: list[_AgentOperationToolRegistration] = []
    for registration in captured_registrations:
        rejection = _registration_validation_outcome(registration)
        if rejection is not None:
            return _build_rejection(rejection)
        assert type(registration) is _AgentOperationToolRegistration
        exact_registrations.append(registration)

    registrations_by_route: dict[
        _AgentOperationToolRoute,
        _AgentOperationToolRegistration,
    ] = {}
    registrations_by_scoped_tool_id: dict[
        tuple[str, str, str],
        _AgentOperationToolRegistration,
    ] = {}
    for registration in exact_registrations:
        route = _route_for_registration(registration)
        existing_route = registrations_by_route.get(route)
        if existing_route is not None:
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.DUPLICATE_ROUTE
            )

        scoped_identity = _scoped_tool_identity(registration)
        existing_tool = registrations_by_scoped_tool_id.get(scoped_identity)
        if existing_tool is not None:
            if (
                existing_tool.implementation_selector
                is registration.implementation_selector
            ):
                return _build_rejection(
                    _AgentOperationToolRegistryOutcome.DUPLICATE_TOOL_ID
                )
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND
            )

        registrations_by_route[route] = registration
        registrations_by_scoped_tool_id[scoped_identity] = registration

    canonical_registrations = tuple(
        sorted(exact_registrations, key=_canonical_registration_key)
    )
    try:
        registration_fingerprint = _registration_fingerprint(
            canonical_registrations
        )
    except UnicodeEncodeError:
        return _build_rejection(
            _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID
        )

    if expected_fingerprint is not None:
        if (
            type(expected_fingerprint) is not str
            or expected_fingerprint != registration_fingerprint
        ):
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.FINGERPRINT_MISMATCH,
                snapshot_fingerprint=registration_fingerprint,
            )

    tool_ids = {item.tool_id for item in canonical_registrations}
    aliases_by_name: dict[str, _AgentOperationToolRoute] = {}
    exact_aliases: list[tuple[str, _AgentOperationToolRoute]] = []
    for alias_entry in captured_aliases:
        if (
            type(alias_entry) is not tuple
            or len(alias_entry) != 2
            or not _is_exact_nonempty_utf8_identifier(alias_entry[0])
            or type(alias_entry[1]) is not _AgentOperationToolRoute
            or _route_validation_outcome(alias_entry[1]) is not None
        ):
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
                snapshot_fingerprint=registration_fingerprint,
            )
        alias, target = alias_entry
        if alias in aliases_by_name or alias in tool_ids:
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
                snapshot_fingerprint=registration_fingerprint,
            )
        if target not in registrations_by_route:
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.ALIAS_TARGET_UNKNOWN,
                snapshot_fingerprint=registration_fingerprint,
            )
        aliases_by_name[alias] = target
        exact_aliases.append((alias, target))

    exact_retired_routes: set[_AgentOperationToolRoute] = set()
    for retired_route in captured_retired_routes:
        if (
            type(retired_route) is not _AgentOperationToolRoute
            or _route_validation_outcome(retired_route) is not None
        ):
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
                snapshot_fingerprint=registration_fingerprint,
            )
        if retired_route in exact_retired_routes:
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
                snapshot_fingerprint=registration_fingerprint,
            )
        if retired_route not in registrations_by_route:
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE,
                snapshot_fingerprint=registration_fingerprint,
            )
        exact_retired_routes.add(retired_route)

    if prior_snapshot is not None:
        prior_integrity = _snapshot_integrity_outcome(prior_snapshot)
        if prior_integrity is not None:
            return _build_rejection(prior_integrity)
        assert type(prior_snapshot) is _TrustedAgentOperationToolRegistrySnapshot
        for old_route, old_registration in (
            prior_snapshot._registrations_by_route.items()
        ):
            new_registration = registrations_by_route.get(old_route)
            if new_registration is None:
                return _build_rejection(
                    _AgentOperationToolRegistryOutcome.
                    HISTORICAL_MAPPING_MISSING,
                    snapshot_fingerprint=registration_fingerprint,
                )
            if new_registration != old_registration:
                return _build_rejection(
                    _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND,
                    snapshot_fingerprint=registration_fingerprint,
                )
        if not prior_snapshot._retired_routes.issubset(
            exact_retired_routes
        ):
            return _build_rejection(
                _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
                snapshot_fingerprint=registration_fingerprint,
            )

    canonical_aliases = tuple(sorted(exact_aliases, key=lambda item: item[0]))
    frozen_retired_routes = frozenset(exact_retired_routes)
    snapshot = _mint_snapshot(
        canonical_registrations,
        canonical_aliases,
        frozen_retired_routes,
        registrations_by_route,
        registrations_by_scoped_tool_id,
        aliases_by_name,
        registration_fingerprint,
    )
    integrity_outcome = _snapshot_integrity_outcome(snapshot)
    if integrity_outcome is not None:
        return _build_rejection(
            integrity_outcome,
            snapshot_fingerprint=registration_fingerprint,
        )

    outcome = _AgentOperationToolRegistryOutcome.RESOLVED
    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    return _AgentOperationToolRegistryBuildResult(
        outcome=outcome,
        retry_disposition=retry,
        snapshot=snapshot,
        audit=_make_agent_operation_tool_registry_audit_material(
            outcome,
            snapshot_fingerprint=registration_fingerprint,
        ),
    )


def _selection_rejection(
    outcome: _AgentOperationToolRegistryOutcome,
    *,
    route: _AgentOperationToolRoute | None = None,
    snapshot_fingerprint: str | None = None,
) -> _AgentOperationToolRouteSelectionResult:
    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    return _AgentOperationToolRouteSelectionResult(
        outcome=outcome,
        retry_disposition=retry,
        selected_route=None,
        audit=_make_agent_operation_tool_registry_audit_material(
            outcome,
            route=route,
            snapshot_fingerprint=snapshot_fingerprint,
        ),
    )


def _missing_selection_outcome(
    snapshot: _TrustedAgentOperationToolRegistrySnapshot,
    requested_route: _AgentOperationToolRoute,
) -> _AgentOperationToolRegistryOutcome:
    """Classify one absent route without selecting a partial-match fallback."""

    known_routes = snapshot._registrations_by_route
    if any(
        known.environment_id == requested_route.environment_id
        and known.operation_id == requested_route.operation_id
        for known in known_routes
    ):
        return _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH
    if any(
        known.runtime_option_id == requested_route.runtime_option_id
        and known.operation_id == requested_route.operation_id
        for known in known_routes
    ):
        return _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH
    if any(
        known.runtime_option_id == requested_route.runtime_option_id
        and known.environment_id == requested_route.environment_id
        for known in known_routes
    ):
        return _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH
    return _AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE


def _select_agent_operation_tool_route(
    snapshot: _TrustedAgentOperationToolRegistrySnapshot,
    *,
    route: _AgentOperationToolRoute | None = None,
    alias: str | None = None,
) -> _AgentOperationToolRouteSelectionResult:
    """Select one active exact route or exact alias strictly before a Run."""

    integrity_outcome = _snapshot_integrity_outcome(snapshot)
    if integrity_outcome is not None:
        return _selection_rejection(integrity_outcome)
    assert type(snapshot) is _TrustedAgentOperationToolRegistrySnapshot

    fingerprint = snapshot._registration_fingerprint
    if (route is None) == (alias is None):
        return _selection_rejection(
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
            snapshot_fingerprint=fingerprint,
        )

    selected_route: _AgentOperationToolRoute
    if alias is not None:
        if not _is_exact_nonempty_utf8_identifier(alias):
            return _selection_rejection(
                _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
                snapshot_fingerprint=fingerprint,
            )
        alias_target = snapshot._aliases_by_name.get(alias)
        if alias_target is None:
            return _selection_rejection(
                _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
                snapshot_fingerprint=fingerprint,
            )
        selected_route = alias_target
    else:
        route_outcome = _route_validation_outcome(route)
        if route_outcome is not None:
            return _selection_rejection(
                route_outcome,
                route=(
                    route
                    if type(route) is _AgentOperationToolRoute
                    else None
                ),
                snapshot_fingerprint=fingerprint,
            )
        assert type(route) is _AgentOperationToolRoute
        selected_route = route

    registration = snapshot._registrations_by_route.get(selected_route)
    if registration is None:
        return _selection_rejection(
            _missing_selection_outcome(snapshot, selected_route),
            route=selected_route,
            snapshot_fingerprint=fingerprint,
        )
    if selected_route in snapshot._retired_routes:
        return _selection_rejection(
            _AgentOperationToolRegistryOutcome.TOOL_RETIRED,
            route=selected_route,
            snapshot_fingerprint=fingerprint,
        )

    outcome = _AgentOperationToolRegistryOutcome.RESOLVED
    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    selected = _SelectedAgentOperationToolRoute(
        route=selected_route,
        tool_id=registration.tool_id,
    )
    return _AgentOperationToolRouteSelectionResult(
        outcome=outcome,
        retry_disposition=retry,
        selected_route=selected,
        audit=_make_agent_operation_tool_registry_audit_material(
            outcome,
            route=selected_route,
            tool_id=registration.tool_id,
            snapshot_fingerprint=fingerprint,
        ),
    )


def _resolve_agent_operation_tool_registration(
    snapshot: _TrustedAgentOperationToolRegistrySnapshot,
    route: _AgentOperationToolRoute,
) -> tuple[
    _AgentOperationToolRegistryOutcome,
    _ResolvedAgentOperationToolRegistration | None,
]:
    """Resolve one permanent historical Registration without retirement."""

    integrity_outcome = _snapshot_integrity_outcome(snapshot)
    if integrity_outcome is not None:
        return integrity_outcome, None
    assert type(snapshot) is _TrustedAgentOperationToolRegistrySnapshot

    route_outcome = _route_validation_outcome(route)
    if route_outcome is not None:
        return route_outcome, None
    assert type(route) is _AgentOperationToolRoute

    registration = snapshot._registrations_by_route.get(route)
    if registration is None:
        return (
            _AgentOperationToolRegistryOutcome.HISTORICAL_MAPPING_MISSING,
            None,
        )
    if registration.runtime_option_id != route.runtime_option_id:
        return _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH, None
    if registration.environment_id != route.environment_id:
        return _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH, None
    if registration.operation_id != route.operation_id:
        return _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH, None

    scoped_registration = snapshot._registrations_by_scoped_tool_id.get(
        _scoped_tool_identity(registration)
    )
    if scoped_registration is None:
        return _AgentOperationToolRegistryOutcome.UNKNOWN_TOOL, None
    if scoped_registration is not registration:
        return _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND, None

    return (
        _AgentOperationToolRegistryOutcome.RESOLVED,
        _ResolvedAgentOperationToolRegistration(
            route=route,
            registration=registration,
            snapshot_fingerprint=snapshot._registration_fingerprint,
        ),
    )
