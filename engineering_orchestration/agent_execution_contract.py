"""Pure Agent Execution Contract preparation and intrinsic validation.

An Agent Execution Contract is immutable declarative intent for one exact
assigned external-inference Agent action.  It is not authorization, durable
prerequisite satisfaction, an Execution Run, tool binding, dispatch, or
invocation.  This module performs no I/O, discovery, persistence, policy
evaluation, authorization consumption, dispatch, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engineering_orchestration._operation_vocabulary import (
    validate_core_operation_id,
)
from engineering_orchestration._repository_resource import (
    validate_repository_resource,
)
from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteFinding,
    AgentActionPrerequisiteOutcome,
    AgentActionPrerequisiteReason,
    AgentActionPrerequisiteResult,
)
from engineering_orchestration.execution_mode import EXECUTION_MODE_ORDER
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    validate_operation_requirement,
)


@dataclass(frozen=True)
class AgentExecutionContract:
    """One exact intended external-inference Agent action and bound mode."""

    task_id: str
    workflow_id: str
    stage_id: str
    role_id: str
    actor_id: str
    runtime_option_id: str
    option_id: str
    environment_id: str
    operation_id: str
    resource: str
    execution_mode: str


@dataclass(frozen=True)
class AgentExecutionContractFinding:
    """Stable intrinsic-validation or preparation finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionContractValidationResult:
    """Atomic result containing either one exact contract or findings."""

    valid: bool
    findings: tuple[AgentExecutionContractFinding, ...]
    contract: AgentExecutionContract | None


_IDENTITY_FIELDS = (
    "task_id",
    "workflow_id",
    "stage_id",
    "role_id",
    "actor_id",
    "runtime_option_id",
    "option_id",
    "environment_id",
)
_REASON_ORDER = {
    reason: index for index, reason in enumerate(AgentActionPrerequisiteReason)
}
_BLOCKING_REASONS = frozenset(
    (
        AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
        AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,
        AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_DENIED,
        AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_DENIED,
    )
)
_MUTUALLY_EXCLUSIVE_REASON_PAIRS = (
    (
        AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
        AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,
    ),
    (
        AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,
        AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN,
    ),
    (
        AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_DENIED,
        AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
    ),
    (
        AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_DENIED,
        AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,
    ),
)


def _finding(code: str, message: str) -> AgentExecutionContractFinding:
    return AgentExecutionContractFinding(code=code, message=message)


def _invalid(
    findings: Iterable[AgentExecutionContractFinding],
) -> AgentExecutionContractValidationResult:
    return AgentExecutionContractValidationResult(
        valid=False,
        findings=tuple(findings),
        contract=None,
    )


def _is_exact_nonempty_string(value: object) -> bool:
    return type(value) is str and bool(value)


def _mode_findings(execution_mode: object) -> list[AgentExecutionContractFinding]:
    if type(execution_mode) is not str:
        return [
            _finding(
                "agent_execution_contract_execution_mode_invalid_type",
                "Agent Execution Contract execution_mode must be an exact string.",
            )
        ]
    if execution_mode not in EXECUTION_MODE_ORDER:
        return [
            _finding(
                "agent_execution_contract_execution_mode_not_supported",
                "Agent Execution Contract execution_mode must be one of: "
                "lite, standard, deep, critical.",
            )
        ]
    return []


def _findings_are_canonical(findings: object) -> bool:
    return (
        type(findings) is tuple
        and bool(findings)
        and all(
            type(finding) is AgentActionPrerequisiteFinding
            and _is_exact_nonempty_string(finding.code)
            and _is_exact_nonempty_string(finding.message)
            for finding in findings
        )
    )


def _prerequisite_result_is_coherent(
    result: AgentActionPrerequisiteResult,
) -> bool:
    """Check all observable canonical AIO-040 result invariants."""

    if type(result.valid) is not bool or type(result.findings) is not tuple:
        return False
    if type(result.reasons) is not tuple:
        return False

    if not result.valid:
        return (
            _findings_are_canonical(result.findings)
            and result.responsibility_key is None
            and result.actor_id is None
            and result.runtime_option_id is None
            and result.option_id is None
            and result.environment_id is None
            and result.operation_id is None
            and result.resource is None
            and result.outcome is None
            and result.reasons == ()
        )

    if result.findings != ():
        return False
    if (
        type(result.responsibility_key) is not tuple
        or len(result.responsibility_key) != 4
        or not all(
            _is_exact_nonempty_string(value)
            for value in result.responsibility_key
        )
        or not _is_exact_nonempty_string(result.actor_id)
        or not _is_exact_nonempty_string(result.runtime_option_id)
        or not _is_exact_nonempty_string(result.option_id)
        or not _is_exact_nonempty_string(result.environment_id)
        or type(result.operation_id) is not str
        or validate_core_operation_id(result.operation_id) is not None
        or type(result.resource) is not str
        or validate_repository_resource(result.resource) is not None
        or type(result.outcome) is not AgentActionPrerequisiteOutcome
        or not result.reasons
        or any(
            type(reason) is not AgentActionPrerequisiteReason
            for reason in result.reasons
        )
    ):
        return False

    reasons = result.reasons
    reason_set = set(reasons)
    satisfied_reason = (
        AgentActionPrerequisiteReason.
        ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED
    )
    if result.outcome is AgentActionPrerequisiteOutcome.SATISFIED:
        return reasons == (satisfied_reason,)
    if satisfied_reason in reason_set or len(reason_set) != len(reasons):
        return False
    if tuple(sorted(reasons, key=_REASON_ORDER.__getitem__)) != reasons:
        return False
    if any(
        first in reason_set and second in reason_set
        for first, second in _MUTUALLY_EXCLUSIVE_REASON_PAIRS
    ):
        return False

    has_blocker = bool(reason_set.intersection(_BLOCKING_REASONS))
    if result.outcome is AgentActionPrerequisiteOutcome.BLOCKED:
        return has_blocker
    if result.outcome is AgentActionPrerequisiteOutcome.UNRESOLVED:
        return not has_blocker
    return False


def validate_agent_execution_contract(
    contract: AgentExecutionContract,
) -> AgentExecutionContractValidationResult:
    """Validate intrinsic contract semantics without proving provenance."""

    if type(contract) is not AgentExecutionContract:
        return _invalid(
            (
                _finding(
                    "agent_execution_contract_invalid_type",
                    "Agent Execution Contract must be an exact "
                    "AgentExecutionContract value.",
                ),
            )
        )

    findings: list[AgentExecutionContractFinding] = []
    for field_name in _IDENTITY_FIELDS:
        if not _is_exact_nonempty_string(getattr(contract, field_name)):
            findings.append(
                _finding(
                    f"agent_execution_contract_{field_name}_invalid",
                    f"Agent Execution Contract {field_name} must be an exact "
                    "nonempty string.",
                )
            )

    requirement_result = validate_operation_requirement(
        OperationRequirement(contract.operation_id, contract.resource)
    )
    findings.extend(
        _finding(finding.code, finding.message)
        for finding in requirement_result.findings
    )
    findings.extend(_mode_findings(contract.execution_mode))

    if findings:
        return _invalid(findings)
    return AgentExecutionContractValidationResult(
        valid=True,
        findings=(),
        contract=contract,
    )


def prepare_agent_execution_contract(
    prerequisite_result: AgentActionPrerequisiteResult,
    *,
    execution_mode: str,
) -> AgentExecutionContractValidationResult:
    """Prepare intent from one coherent satisfied AIO-040 result and mode.

    Observable coherence cannot authenticate assessor provenance or caller
    truth.  Preparation does not consume authorization and does not establish
    permission, readiness, dispatchability, or invocation authority.
    """

    findings: list[AgentExecutionContractFinding] = []
    prerequisite_is_satisfied = False

    if type(prerequisite_result) is not AgentActionPrerequisiteResult:
        findings.append(
            _finding(
                "agent_execution_contract_prerequisite_result_invalid_type",
                "prerequisite_result must be an exact "
                "AgentActionPrerequisiteResult value.",
            )
        )
    elif not _prerequisite_result_is_coherent(prerequisite_result):
        findings.append(
            _finding(
                "agent_execution_contract_prerequisite_result_incoherent",
                "prerequisite_result does not satisfy canonical "
                "AgentActionPrerequisiteResult invariants.",
            )
        )
    elif not prerequisite_result.valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in prerequisite_result.findings
        )
    elif prerequisite_result.outcome is AgentActionPrerequisiteOutcome.BLOCKED:
        findings.append(
            _finding(
                "agent_execution_contract_prerequisites_blocked",
                "Agent Execution Contract preparation requires "
                "prerequisite_result outcome 'satisfied'; received 'blocked'.",
            )
        )
    elif (
        prerequisite_result.outcome
        is AgentActionPrerequisiteOutcome.UNRESOLVED
    ):
        findings.append(
            _finding(
                "agent_execution_contract_prerequisites_unresolved",
                "Agent Execution Contract preparation requires "
                "prerequisite_result outcome 'satisfied'; received "
                "'unresolved'.",
            )
        )
    else:
        prerequisite_is_satisfied = True

    findings.extend(_mode_findings(execution_mode))
    if findings:
        return _invalid(findings)

    # The coherence gate above proves these exact shapes and types.
    assert prerequisite_is_satisfied
    assert type(prerequisite_result) is AgentActionPrerequisiteResult
    assert prerequisite_result.responsibility_key is not None
    assert prerequisite_result.actor_id is not None
    assert prerequisite_result.runtime_option_id is not None
    assert prerequisite_result.option_id is not None
    assert prerequisite_result.environment_id is not None
    assert prerequisite_result.operation_id is not None
    assert prerequisite_result.resource is not None
    assert type(execution_mode) is str

    task_id, workflow_id, stage_id, role_id = (
        prerequisite_result.responsibility_key
    )
    contract = AgentExecutionContract(
        task_id=task_id,
        workflow_id=workflow_id,
        stage_id=stage_id,
        role_id=role_id,
        actor_id=prerequisite_result.actor_id,
        runtime_option_id=prerequisite_result.runtime_option_id,
        option_id=prerequisite_result.option_id,
        environment_id=prerequisite_result.environment_id,
        operation_id=prerequisite_result.operation_id,
        resource=prerequisite_result.resource,
        execution_mode=execution_mode,
    )
    return validate_agent_execution_contract(contract)
