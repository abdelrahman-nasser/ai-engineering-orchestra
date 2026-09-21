"""Pure validation for Run-bound Agent Execution Authorization Grants.

The values in this module are intrinsic, declarative data.  Core neither
issues nor authenticates a Grant and does not evaluate current time, consume
authority, provide replay protection, persist state, admit dispatch, or invoke
an Agent.  Operational trust requires a separate authenticated and
integrity-protected authority-producer boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable

from engineering_orchestration.agent_execution_run import (
    AgentExecutionRun,
    AgentExecutionRunFinding,
    validate_agent_execution_run,
)


_CANONICAL_UTC_TIMESTAMP = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-"
    r"(?P<day>[0-9]{2})T(?P<hour>[0-9]{2}):"
    r"(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,6}))?Z$"
)
_ISSUER_KINDS = ("human", "policy")


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrant:
    """One positive authority artifact bound to one exact execution Run."""

    grant_id: str
    run: AgentExecutionRun
    authorization_domain_id: str
    issuer_kind: str
    issuer_id: str
    provenance_reference: str
    issued_at: str
    expires_at: str


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantFinding:
    """Stable intrinsic or collection-validation finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantValidationResult:
    """Atomic result containing either one exact Grant or findings."""

    valid: bool
    findings: tuple[AgentExecutionAuthorizationGrantFinding, ...]
    grant: AgentExecutionAuthorizationGrant | None


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantCollectionValidationResult:
    """Atomic result containing canonical Grants or findings for one domain."""

    valid: bool
    findings: tuple[AgentExecutionAuthorizationGrantFinding, ...]
    normalized_grants: tuple[AgentExecutionAuthorizationGrant, ...]


def _finding(
    code: str,
    message: str,
) -> AgentExecutionAuthorizationGrantFinding:
    return AgentExecutionAuthorizationGrantFinding(code=code, message=message)


def _invalid(
    findings: Iterable[AgentExecutionAuthorizationGrantFinding],
) -> AgentExecutionAuthorizationGrantValidationResult:
    return AgentExecutionAuthorizationGrantValidationResult(
        valid=False,
        findings=tuple(findings),
        grant=None,
    )


def _invalid_collection(
    findings: Iterable[AgentExecutionAuthorizationGrantFinding],
) -> AgentExecutionAuthorizationGrantCollectionValidationResult:
    return AgentExecutionAuthorizationGrantCollectionValidationResult(
        valid=False,
        findings=tuple(findings),
        normalized_grants=(),
    )


def _converted_run_findings(
    findings: Iterable[AgentExecutionRunFinding],
) -> tuple[AgentExecutionAuthorizationGrantFinding, ...]:
    return tuple(_finding(item.code, item.message) for item in findings)


def _identifier_finding(
    value: object,
    *,
    field_name: str,
) -> AgentExecutionAuthorizationGrantFinding | None:
    if type(value) is str and bool(value):
        return None
    return _finding(
        f"agent_execution_authorization_grant_{field_name}_invalid",
        "Agent Execution Authorization Grant "
        f"{field_name} must be an exact nonempty string.",
    )


def _parse_canonical_utc_timestamp(value: object) -> datetime | None:
    """Parse locked UTC syntax without consulting any clock."""

    if type(value) is not str:
        return None
    match = _CANONICAL_UTC_TIMESTAMP.fullmatch(value)
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


def _timestamp_finding(
    value: object,
    *,
    field_name: str,
) -> tuple[
    datetime | None,
    AgentExecutionAuthorizationGrantFinding | None,
]:
    parsed = _parse_canonical_utc_timestamp(value)
    if parsed is not None:
        return parsed, None
    return None, _finding(
        f"agent_execution_authorization_grant_{field_name}_invalid",
        "Agent Execution Authorization Grant "
        f"{field_name} must be a valid canonical UTC timestamp matching "
        "YYYY-MM-DDTHH:MM:SS[.fraction]Z with one to six fractional "
        "digits when present.",
    )


def validate_agent_execution_authorization_grant(
    grant: AgentExecutionAuthorizationGrant,
) -> AgentExecutionAuthorizationGrantValidationResult:
    """Validate intrinsic Grant semantics without establishing trust."""

    if type(grant) is not AgentExecutionAuthorizationGrant:
        return _invalid(
            (
                _finding(
                    "agent_execution_authorization_grant_invalid_type",
                    "Agent Execution Authorization Grant must be an exact "
                    "AgentExecutionAuthorizationGrant value.",
                ),
            )
        )

    findings: list[AgentExecutionAuthorizationGrantFinding] = []

    grant_id_finding = _identifier_finding(
        grant.grant_id,
        field_name="grant_id",
    )
    if grant_id_finding is not None:
        findings.append(grant_id_finding)

    run_result = validate_agent_execution_run(grant.run)
    findings.extend(_converted_run_findings(run_result.findings))

    domain_finding = _identifier_finding(
        grant.authorization_domain_id,
        field_name="authorization_domain_id",
    )
    if domain_finding is not None:
        findings.append(domain_finding)

    if type(grant.issuer_kind) is not str or grant.issuer_kind not in _ISSUER_KINDS:
        findings.append(
            _finding(
                "agent_execution_authorization_grant_issuer_kind_invalid",
                "Agent Execution Authorization Grant issuer_kind must be "
                "exactly 'human' or 'policy'.",
            )
        )

    issuer_id_finding = _identifier_finding(
        grant.issuer_id,
        field_name="issuer_id",
    )
    if issuer_id_finding is not None:
        findings.append(issuer_id_finding)

    provenance_finding = _identifier_finding(
        grant.provenance_reference,
        field_name="provenance_reference",
    )
    if provenance_finding is not None:
        findings.append(provenance_finding)

    issued_at, issued_at_finding = _timestamp_finding(
        grant.issued_at,
        field_name="issued_at",
    )
    if issued_at_finding is not None:
        findings.append(issued_at_finding)

    expires_at, expires_at_finding = _timestamp_finding(
        grant.expires_at,
        field_name="expires_at",
    )
    if expires_at_finding is not None:
        findings.append(expires_at_finding)

    if (
        issued_at is not None
        and expires_at is not None
        and issued_at >= expires_at
    ):
        findings.append(
            _finding(
                "agent_execution_authorization_grant_time_order_invalid",
                "Agent Execution Authorization Grant issued_at must be "
                "earlier than expires_at.",
            )
        )

    if findings:
        return _invalid(findings)
    return AgentExecutionAuthorizationGrantValidationResult(
        valid=True,
        findings=(),
        grant=grant,
    )


def _grant_identity(
    grant: AgentExecutionAuthorizationGrant,
) -> tuple[str, str, str, str]:
    return (
        grant.authorization_domain_id,
        grant.issuer_kind,
        grant.issuer_id,
        grant.grant_id,
    )


def _grant_identity_text(identity: tuple[str, str, str, str]) -> str:
    domain, kind, issuer, grant_id = identity
    return (
        "(authorization_domain_id="
        f"{domain!r}, issuer_kind={kind!r}, issuer_id={issuer!r}, "
        f"grant_id={grant_id!r})"
    )


def validate_agent_execution_authorization_grant_collection(
    grants: Iterable[AgentExecutionAuthorizationGrant],
    *,
    authorization_domain_id: str,
) -> AgentExecutionAuthorizationGrantCollectionValidationResult:
    """Validate and order one supplied authorization-domain snapshot.

    The iterable is captured exactly once.  This is not an authoritative
    registry, consumption ledger, currentness check, or replay-protection API.
    """

    try:
        captured = tuple(grants)
    except TypeError:
        return _invalid_collection(
            (
                _finding(
                    "agent_execution_authorization_grant_collection_invalid",
                    "Agent Execution Authorization Grant collection must be "
                    "an iterable captured exactly once.",
                ),
            )
        )

    if type(authorization_domain_id) is not str or not authorization_domain_id:
        return _invalid_collection(
            (
                _finding(
                    "agent_execution_authorization_grant_collection_"
                    "authorization_domain_id_invalid",
                    "Agent Execution Authorization Grant collection "
                    "authorization_domain_id must be an exact nonempty string.",
                ),
            )
        )

    intrinsic_findings: list[AgentExecutionAuthorizationGrantFinding] = []
    for grant in captured:
        intrinsic_findings.extend(
            validate_agent_execution_authorization_grant(grant).findings
        )
    if intrinsic_findings:
        return _invalid_collection(
            sorted(
                intrinsic_findings,
                key=lambda item: (item.code, item.message),
            )
        )

    exact_grants = captured
    domain_findings = tuple(
        _finding(
            "agent_execution_authorization_grant_domain_mismatch",
            "Agent Execution Authorization Grant authorization_domain_id "
            f"{observed!r} does not match collection authorization_domain_id "
            f"{authorization_domain_id!r}.",
        )
        for observed in sorted(
            {
                grant.authorization_domain_id
                for grant in exact_grants
                if grant.authorization_domain_id != authorization_domain_id
            }
        )
    )
    if domain_findings:
        return _invalid_collection(domain_findings)

    by_identity: dict[
        tuple[str, str, str, str],
        list[AgentExecutionAuthorizationGrant],
    ] = {}
    by_run_id: dict[tuple[str, str], list[AgentExecutionAuthorizationGrant]] = {}
    by_run: dict[
        tuple[str, AgentExecutionRun],
        list[AgentExecutionAuthorizationGrant],
    ] = {}
    for grant in exact_grants:
        by_identity.setdefault(_grant_identity(grant), []).append(grant)
        by_run_id.setdefault(
            (grant.authorization_domain_id, grant.run.run_id),
            [],
        ).append(grant)
        by_run.setdefault(
            (grant.authorization_domain_id, grant.run),
            [],
        ).append(grant)

    duplicate_findings: list[AgentExecutionAuthorizationGrantFinding] = []
    identity_findings: list[AgentExecutionAuthorizationGrantFinding] = []
    for identity in sorted(by_identity):
        members = by_identity[identity]
        if len(members) < 2:
            continue
        first = members[0]
        if any(member != first for member in members[1:]):
            identity_findings.append(
                _finding(
                    "agent_execution_authorization_grant_identity_binding_"
                    "conflict",
                    "Agent Execution Authorization Grant identity "
                    f"{_grant_identity_text(identity)} is bound to differing "
                    "Grant values.",
                )
            )
        else:
            duplicate_findings.append(
                _finding(
                    "duplicate_agent_execution_authorization_grant",
                    "Agent Execution Authorization Grant identity "
                    f"{_grant_identity_text(identity)} has more than one "
                    "identical supplied Grant value.",
                )
            )

    run_binding_findings: list[AgentExecutionAuthorizationGrantFinding] = []
    for (domain, run_id), members in sorted(by_run_id.items()):
        first_contract = members[0].run.contract
        if any(grant.run.contract != first_contract for grant in members[1:]):
            run_binding_findings.append(
                _finding(
                    "agent_execution_authorization_grant_run_identity_"
                    "binding_conflict",
                    "Agent Execution Run identity "
                    f"(authorization_domain_id={domain!r}, run_id={run_id!r}) "
                    "is bound to differing nested Agent Execution Contracts.",
                )
            )

    multiple_findings: list[AgentExecutionAuthorizationGrantFinding] = []
    multi_authority_findings: list[
        AgentExecutionAuthorizationGrantFinding
    ] = []
    ordered_run_groups = sorted(
        by_run.items(),
        key=lambda item: (
            item[0][0],
            item[0][1].run_id,
            repr(item[0][1].contract),
        ),
    )
    for (domain, bound_run), members in ordered_run_groups:
        identities = {_grant_identity(grant) for grant in members}
        if len(identities) < 2:
            continue
        issuers = {(grant.issuer_kind, grant.issuer_id) for grant in members}
        if len(issuers) > 1:
            multi_authority_findings.append(
                _finding(
                    "unsupported_multi_authority_agent_execution_"
                    "authorization_grant",
                    "Agent Execution Run "
                    f"(authorization_domain_id={domain!r}, "
                    f"run_id={bound_run.run_id!r}) has Grants from differing "
                    "issuers; multi-authority composition is not supported.",
                )
            )
        else:
            multiple_findings.append(
                _finding(
                    "unsupported_multiple_agent_execution_authorization_"
                    "grants_for_run",
                    "Agent Execution Run "
                    f"(authorization_domain_id={domain!r}, "
                    f"run_id={bound_run.run_id!r}) has more than one distinct "
                    "Grant identity; replacement or reissue is not supported.",
                )
            )

    findings = (
        *duplicate_findings,
        *identity_findings,
        *run_binding_findings,
        *multiple_findings,
        *multi_authority_findings,
    )
    if findings:
        return _invalid_collection(findings)

    return AgentExecutionAuthorizationGrantCollectionValidationResult(
        valid=True,
        findings=(),
        normalized_grants=tuple(sorted(exact_grants, key=_grant_identity)),
    )
