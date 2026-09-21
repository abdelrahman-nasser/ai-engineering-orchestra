"""Pure Agent Execution Run preparation and intrinsic validation.

An Agent Execution Run is immutable occurrence identity for one concrete
attempt involving one exact Agent Execution Contract.  It is not lifecycle,
authorization, authorization consumption, replay protection, tool binding,
dispatch, invocation, or success.  This module performs no I/O, discovery,
persistence, clock access, randomness, policy evaluation, dispatch, or
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
    AgentExecutionContractFinding,
    prepare_agent_execution_contract,
    validate_agent_execution_contract,
)


@dataclass(frozen=True)
class AgentExecutionRun:
    """One concrete attempt identity bound to one exact execution contract."""

    run_id: str
    contract: AgentExecutionContract


@dataclass(frozen=True)
class AgentExecutionRunFinding:
    """Stable intrinsic-validation or preparation finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionRunValidationResult:
    """Atomic result containing either one exact Run or findings."""

    valid: bool
    findings: tuple[AgentExecutionRunFinding, ...]
    run: AgentExecutionRun | None


def _finding(code: str, message: str) -> AgentExecutionRunFinding:
    return AgentExecutionRunFinding(code=code, message=message)


def _converted_contract_findings(
    findings: Iterable[AgentExecutionContractFinding],
) -> tuple[AgentExecutionRunFinding, ...]:
    return tuple(_finding(item.code, item.message) for item in findings)


def _invalid(
    findings: Iterable[AgentExecutionRunFinding],
) -> AgentExecutionRunValidationResult:
    return AgentExecutionRunValidationResult(
        valid=False,
        findings=tuple(findings),
        run=None,
    )


def _run_id_findings(run_id: object) -> list[AgentExecutionRunFinding]:
    if type(run_id) is str and bool(run_id):
        return []
    return [
        _finding(
            "agent_execution_run_run_id_invalid",
            "Agent Execution Run run_id must be an exact nonempty string.",
        )
    ]


def validate_agent_execution_run(
    run: AgentExecutionRun,
) -> AgentExecutionRunValidationResult:
    """Validate intrinsic Run value semantics without proving provenance."""

    if type(run) is not AgentExecutionRun:
        return _invalid(
            (
                _finding(
                    "agent_execution_run_invalid_type",
                    "Agent Execution Run must be an exact AgentExecutionRun "
                    "value.",
                ),
            )
        )

    findings = _run_id_findings(run.run_id)
    contract_result = validate_agent_execution_contract(run.contract)
    findings.extend(_converted_contract_findings(contract_result.findings))
    if findings:
        return _invalid(findings)
    return AgentExecutionRunValidationResult(
        valid=True,
        findings=(),
        run=run,
    )


def prepare_agent_execution_run(
    intended_contract: AgentExecutionContract,
    prerequisite_result: AgentActionPrerequisiteResult,
    *,
    execution_mode: str,
    run_id: str,
) -> AgentExecutionRunValidationResult:
    """Prepare one Run after fresh Contract preparation and exact equality.

    The caller owns the currency of supplied parent evidence and effective
    Execution Mode.  Observable validation cannot authenticate freshness,
    provenance, authority, or Run-ID uniqueness.  Preparation consumes no
    authorization and establishes no lifecycle or dispatch permission.
    """

    findings = _run_id_findings(run_id)

    intended_result = validate_agent_execution_contract(intended_contract)
    findings.extend(_converted_contract_findings(intended_result.findings))

    fresh_result = prepare_agent_execution_contract(
        prerequisite_result,
        execution_mode=execution_mode,
    )
    findings.extend(_converted_contract_findings(fresh_result.findings))

    if findings:
        return _invalid(findings)

    assert intended_result.contract is intended_contract
    assert fresh_result.contract is not None
    if fresh_result.contract != intended_contract:
        return _invalid(
            (
                _finding(
                    "agent_execution_run_contract_mismatch",
                    "Freshly prepared Agent Execution Contract must exactly "
                    "equal intended_contract.",
                ),
            )
        )

    run = AgentExecutionRun(run_id=run_id, contract=intended_contract)
    return validate_agent_execution_run(run)
