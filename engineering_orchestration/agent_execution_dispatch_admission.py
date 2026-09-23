"""Pure validation for Agent Execution Dispatch Admissions.

An Admission is an immutable historical value.  Direct construction,
serialization, schema validity, and intrinsic validation do not establish
authoritative-store provenance, issuer authentication, trusted Tool
resolution, currentness at validation time, non-revocation, consumption,
dispatch, invocation, or success.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    AgentExecutionAuthorizationGrantFinding,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    AgentOperationToolBindingFinding,
    validate_agent_operation_tool_binding,
)


__all__ = (
    "AgentExecutionDispatchAdmission",
    "AgentExecutionDispatchAdmissionFinding",
    "AgentExecutionDispatchAdmissionValidationResult",
    "validate_agent_execution_dispatch_admission",
)


_DECISION_TIME = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-"
    r"(?P<day>[0-9]{2})T(?P<hour>[0-9]{2}):"
    r"(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})\."
    r"(?P<fraction>[0-9]{6})Z$"
)
_GRANT_TIME = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-"
    r"(?P<day>[0-9]{2})T(?P<hour>[0-9]{2}):"
    r"(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,6}))?Z$"
)


@dataclass(frozen=True)
class AgentExecutionDispatchAdmission:
    """Exact value shape of one authoritative-store consumption record."""

    grant: AgentExecutionAuthorizationGrant
    tool_binding: AgentOperationToolBinding
    decision_time: str


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionFinding:
    """Stable intrinsic-validation finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionValidationResult:
    """Atomic result containing either one exact Admission or findings."""

    valid: bool
    findings: tuple[AgentExecutionDispatchAdmissionFinding, ...]
    admission: AgentExecutionDispatchAdmission | None


def _finding(
    code: str,
    message: str,
) -> AgentExecutionDispatchAdmissionFinding:
    return AgentExecutionDispatchAdmissionFinding(code=code, message=message)


def _invalid(
    findings: Iterable[AgentExecutionDispatchAdmissionFinding],
) -> AgentExecutionDispatchAdmissionValidationResult:
    return AgentExecutionDispatchAdmissionValidationResult(
        valid=False,
        findings=tuple(findings),
        admission=None,
    )


def _converted_grant_findings(
    findings: Iterable[AgentExecutionAuthorizationGrantFinding],
) -> tuple[AgentExecutionDispatchAdmissionFinding, ...]:
    return tuple(_finding(item.code, item.message) for item in findings)


def _converted_binding_findings(
    findings: Iterable[AgentOperationToolBindingFinding],
) -> tuple[AgentExecutionDispatchAdmissionFinding, ...]:
    return tuple(_finding(item.code, item.message) for item in findings)


def _parse_timestamp(value: object, pattern: re.Pattern[str]) -> datetime | None:
    """Parse one locked UTC representation without obtaining current time."""

    if type(value) is not str:
        return None
    match = pattern.fullmatch(value)
    if match is None:
        return None
    parts = match.groupdict()
    fraction = parts["fraction"] or ""
    try:
        return datetime(
            int(parts["year"]),
            int(parts["month"]),
            int(parts["day"]),
            int(parts["hour"]),
            int(parts["minute"]),
            int(parts["second"]),
            int(fraction.ljust(6, "0")) if fraction else 0,
        )
    except ValueError:
        return None


def validate_agent_execution_dispatch_admission(
    admission: AgentExecutionDispatchAdmission,
) -> AgentExecutionDispatchAdmissionValidationResult:
    """Validate intrinsic Admission coherence without establishing authority."""

    if type(admission) is not AgentExecutionDispatchAdmission:
        return _invalid(
            (
                _finding(
                    "agent_execution_dispatch_admission_invalid_type",
                    "Agent Execution Dispatch Admission must be an exact "
                    "AgentExecutionDispatchAdmission value.",
                ),
            )
        )

    grant_result = validate_agent_execution_authorization_grant(
        admission.grant
    )
    binding_result = validate_agent_operation_tool_binding(
        admission.tool_binding
    )
    findings = list(_converted_grant_findings(grant_result.findings))
    findings.extend(_converted_binding_findings(binding_result.findings))

    if (
        grant_result.valid
        and binding_result.valid
        and admission.grant.run != admission.tool_binding.run
    ):
        findings.append(
            _finding(
                "agent_execution_dispatch_admission_run_mismatch",
                "Agent Execution Dispatch Admission grant.run and "
                "tool_binding.run must be exactly equal complete Agent "
                "Execution Run values.",
            )
        )

    decision_time = _parse_timestamp(admission.decision_time, _DECISION_TIME)
    if decision_time is None:
        findings.append(
            _finding(
                "agent_execution_dispatch_admission_decision_time_invalid",
                "Agent Execution Dispatch Admission decision_time must be a "
                "valid canonical UTC timestamp matching "
                "YYYY-MM-DDTHH:MM:SS.ffffffZ with exactly six fractional "
                "digits.",
            )
        )

    if grant_result.valid and decision_time is not None:
        issued_at = _parse_timestamp(admission.grant.issued_at, _GRANT_TIME)
        expires_at = _parse_timestamp(admission.grant.expires_at, _GRANT_TIME)
        if (
            issued_at is not None
            and expires_at is not None
            and not (issued_at <= decision_time < expires_at)
        ):
            findings.append(
                _finding(
                    "agent_execution_dispatch_admission_currentness_invalid",
                    "Agent Execution Dispatch Admission must satisfy "
                    "grant.issued_at <= decision_time < grant.expires_at "
                    "using parsed UTC instants.",
                )
            )

    if findings:
        return _invalid(findings)
    return AgentExecutionDispatchAdmissionValidationResult(
        valid=True,
        findings=(),
        admission=admission,
    )
