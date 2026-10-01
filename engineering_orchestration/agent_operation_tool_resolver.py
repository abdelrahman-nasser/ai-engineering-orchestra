"""Trusted deterministic Agent Operation Tool Binding resolution.

The resolver joins one intrinsically valid authenticated Grant to one exact
permanent historical Registration in an immutable trusted registry snapshot.
It constructs only the existing two-field Agent Operation Tool Binding.  It
performs no discovery, availability probing, resource access, fallback,
persistence, dispatch, or invocation.
"""

from __future__ import annotations

from dataclasses import dataclass

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    validate_agent_operation_tool_binding,
)
from engineering_orchestration.agent_operation_tool_registry import (
    _AgentOperationToolRegistration,
    _AgentOperationToolRegistryAuditMaterial,
    _AgentOperationToolRegistryOutcome,
    _AgentOperationToolRegistryRetryDisposition,
    _AgentOperationToolRoute,
    _ResolvedAgentOperationToolRegistration,
    _TrustedAgentOperationToolRegistrySnapshot,
    _agent_operation_tool_registry_retry_disposition,
    _make_agent_operation_tool_registry_audit_material,
    _resolve_agent_operation_tool_registration,
)


__all__ = ("TrustedAgentOperationToolBindingResolver",)


@dataclass(frozen=True, slots=True)
class _AgentOperationToolResolutionResult:
    """One closed process-local resolution result."""

    outcome: _AgentOperationToolRegistryOutcome
    retry_disposition: _AgentOperationToolRegistryRetryDisposition
    resolved_registration: _ResolvedAgentOperationToolRegistration | None
    binding: AgentOperationToolBinding | None
    audit: _AgentOperationToolRegistryAuditMaterial


def _resolution_result(
    outcome: _AgentOperationToolRegistryOutcome,
    *,
    grant: AgentExecutionAuthorizationGrant | None = None,
    route: _AgentOperationToolRoute | None = None,
    resolved_registration: _ResolvedAgentOperationToolRegistration | None = None,
    binding: AgentOperationToolBinding | None = None,
) -> _AgentOperationToolResolutionResult:
    """Create one coherent rich result without free-form diagnostics."""

    if type(outcome) is not _AgentOperationToolRegistryOutcome:
        outcome = _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
    if outcome is not _AgentOperationToolRegistryOutcome.RESOLVED:
        resolved_registration = None
        binding = None

    run_id = None
    if type(grant) is AgentExecutionAuthorizationGrant:
        candidate_run_id = getattr(grant.run, "run_id", None)
        if type(candidate_run_id) is str and candidate_run_id:
            run_id = candidate_run_id

    tool_id = None
    snapshot_fingerprint = None
    if (
        outcome is _AgentOperationToolRegistryOutcome.RESOLVED
        and type(resolved_registration)
        is _ResolvedAgentOperationToolRegistration
    ):
        candidate_tool_id = resolved_registration.registration.tool_id
        if type(candidate_tool_id) is str and candidate_tool_id:
            tool_id = candidate_tool_id
        candidate_fingerprint = resolved_registration.snapshot_fingerprint
        if type(candidate_fingerprint) is str and candidate_fingerprint:
            snapshot_fingerprint = candidate_fingerprint

    retry = _agent_operation_tool_registry_retry_disposition(outcome)
    return _AgentOperationToolResolutionResult(
        outcome=outcome,
        retry_disposition=retry,
        resolved_registration=resolved_registration,
        binding=binding,
        audit=_make_agent_operation_tool_registry_audit_material(
            outcome,
            run_id=run_id,
            route=route,
            tool_id=tool_id,
            snapshot_fingerprint=snapshot_fingerprint,
        ),
    )


@dataclass(frozen=True, slots=True, init=False, repr=False, eq=False)
class TrustedAgentOperationToolBindingResolver:
    """Resolve exact Grants through one immutable trusted registry snapshot."""

    _snapshot: _TrustedAgentOperationToolRegistrySnapshot

    def __init__(
        self,
        snapshot: _TrustedAgentOperationToolRegistrySnapshot,
    ) -> None:
        if type(snapshot) is not _TrustedAgentOperationToolRegistrySnapshot:
            raise TypeError(
                "snapshot must be an exact trusted Agent Operation Tool "
                "Registry snapshot"
            )
        object.__setattr__(self, "_snapshot", snapshot)

    def resolve(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> _AgentOperationToolResolutionResult:
        """Return one rich private result for an exact authenticated Grant."""

        if type(grant) is not AgentExecutionAuthorizationGrant:
            return _resolution_result(
                _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            )

        try:
            grant_result = validate_agent_execution_authorization_grant(grant)
            if not grant_result.valid or grant_result.grant is not grant:
                return _resolution_result(
                    _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
                )

            contract = grant.run.contract
            route = _AgentOperationToolRoute(
                runtime_option_id=contract.runtime_option_id,
                environment_id=contract.environment_id,
                operation_id=contract.operation_id,
            )
            outcome, resolved = _resolve_agent_operation_tool_registration(
                self._snapshot,
                route,
            )
            if outcome is not _AgentOperationToolRegistryOutcome.RESOLVED:
                return _resolution_result(
                    outcome,
                    grant=grant,
                    route=route,
                )
            if (
                type(resolved) is not _ResolvedAgentOperationToolRegistration
                or resolved.route is not route
                or type(resolved.registration)
                is not _AgentOperationToolRegistration
                or resolved.registration.runtime_option_id
                != route.runtime_option_id
                or resolved.registration.environment_id
                != route.environment_id
                or resolved.registration.operation_id != route.operation_id
                or type(resolved.registration.tool_id) is not str
                or not resolved.registration.tool_id
                or type(resolved.snapshot_fingerprint) is not str
                or not resolved.snapshot_fingerprint
            ):
                return _resolution_result(
                    _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
                    grant=grant,
                    route=route,
                )

            binding = AgentOperationToolBinding(
                run=grant.run,
                tool_id=resolved.registration.tool_id,
            )
            binding_result = validate_agent_operation_tool_binding(binding)
            if (
                not binding_result.valid
                or binding_result.binding is not binding
                or binding.run is not grant.run
                or binding.run != grant.run
            ):
                return _resolution_result(
                    _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
                    grant=grant,
                    route=route,
                )
            return _resolution_result(
                _AgentOperationToolRegistryOutcome.RESOLVED,
                grant=grant,
                route=route,
                resolved_registration=resolved,
                binding=binding,
            )
        except Exception:
            return _resolution_result(
                _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE
            )

    def resolve_tool_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentOperationToolBinding | None:
        """Implement the unchanged AIO-047 resolver port.

        Only the exact successful Binding crosses the port.  Every private
        rejection collapses to ``None``.  Nonordinary process-control
        exceptions are deliberately not intercepted.
        """

        try:
            result = self.resolve(grant)
        except Exception:
            return None
        if (
            type(result) is _AgentOperationToolResolutionResult
            and result.outcome is _AgentOperationToolRegistryOutcome.RESOLVED
            and type(result.binding) is AgentOperationToolBinding
        ):
            return result.binding
        return None
