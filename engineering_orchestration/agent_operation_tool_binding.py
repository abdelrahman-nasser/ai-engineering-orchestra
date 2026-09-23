"""Pure intrinsic validation for Agent Operation Tool Bindings.

An Agent Operation Tool Binding immutably binds one exact complete Agent
Execution Run to one exact configured Tool implementation identity supplied by
an external trusted resolver. It is not authority, permission, Grant
consumption, dispatch admission, dispatch, or invocation. This module performs
no I/O, discovery, probing, selection, fallback, persistence, clock access,
randomness, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engineering_orchestration.agent_execution_run import (
    AgentExecutionRun,
    AgentExecutionRunFinding,
    validate_agent_execution_run,
)


__all__ = (
    "AgentOperationToolBinding",
    "AgentOperationToolBindingFinding",
    "AgentOperationToolBindingValidationResult",
    "validate_agent_operation_tool_binding",
)


@dataclass(frozen=True)
class AgentOperationToolBinding:
    """One exact Run bound to one immutable configured Tool identity."""

    run: AgentExecutionRun
    tool_id: str


@dataclass(frozen=True)
class AgentOperationToolBindingFinding:
    """Stable intrinsic-validation finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentOperationToolBindingValidationResult:
    """Atomic result containing either one exact binding or findings."""

    valid: bool
    findings: tuple[AgentOperationToolBindingFinding, ...]
    binding: AgentOperationToolBinding | None


def _finding(code: str, message: str) -> AgentOperationToolBindingFinding:
    return AgentOperationToolBindingFinding(code=code, message=message)


def _converted_run_findings(
    findings: Iterable[AgentExecutionRunFinding],
) -> tuple[AgentOperationToolBindingFinding, ...]:
    return tuple(_finding(item.code, item.message) for item in findings)


def _invalid(
    findings: Iterable[AgentOperationToolBindingFinding],
) -> AgentOperationToolBindingValidationResult:
    return AgentOperationToolBindingValidationResult(
        valid=False,
        findings=tuple(findings),
        binding=None,
    )


def validate_agent_operation_tool_binding(
    binding: AgentOperationToolBinding,
) -> AgentOperationToolBindingValidationResult:
    """Validate intrinsic binding semantics without resolving any Tool."""

    if type(binding) is not AgentOperationToolBinding:
        return _invalid(
            (
                _finding(
                    "agent_operation_tool_binding_invalid_type",
                    "Agent Operation Tool Binding must be an exact "
                    "AgentOperationToolBinding value.",
                ),
            )
        )

    run_result = validate_agent_execution_run(binding.run)
    findings = list(_converted_run_findings(run_result.findings))
    if type(binding.tool_id) is not str or not binding.tool_id:
        findings.append(
            _finding(
                "agent_operation_tool_binding_tool_id_invalid",
                "Agent Operation Tool Binding tool_id must be an exact "
                "nonempty string.",
            )
        )

    if findings:
        return _invalid(findings)
    return AgentOperationToolBindingValidationResult(
        valid=True,
        findings=(),
        binding=binding,
    )
