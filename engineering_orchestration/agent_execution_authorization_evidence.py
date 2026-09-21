"""Pure validation of Agent Execution Authorization Evidence snapshots.

Evidence values are caller-supplied assertions that a Human or policy
authority granted or denied one exact assigned external-inference Agent action.
They are not authenticated authority, Permission Decisions, Task approval,
environment permission, durable grants, enforcement, or execution. This module
performs no discovery, I/O, approval parsing, persistence, or invocation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping, cast

from engineering_orchestration._operation_vocabulary import (
    validate_core_operation_id,
)
from engineering_orchestration._repository_resource import (
    RepositoryResourceValidationIssue,
    _repository_resource_issue_sort_key,
    validate_repository_resource,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)
from engineering_orchestration.assignment import (
    Assignment,
    validate_assignment_set,
)
from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    validate_inference_option_inventory,
)
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.workflow_catalog import WorkflowCatalog


class AgentExecutionAuthorizationAuthorityKind(StrEnum):
    """Declared authorization origin category, not authenticated identity."""

    HUMAN = "human"
    POLICY = "policy"


class AgentExecutionAuthorizationState(StrEnum):
    """Closed caller-attested authorization states."""

    GRANTED = "granted"
    DENIED = "denied"


@dataclass(frozen=True)
class AgentExecutionAuthorizationEvidence:
    """Evidence about one exact assigned external-inference Agent action."""

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
    authority_kind: AgentExecutionAuthorizationAuthorityKind
    authority_id: str
    provenance_reference: str
    state: AgentExecutionAuthorizationState


@dataclass(frozen=True)
class AgentExecutionAuthorizationFinding:
    """Stable semantic finding from authorization-evidence validation."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionAuthorizationValidationResult:
    """Atomic result with canonically ordered supplied evidence."""

    valid: bool
    findings: tuple[AgentExecutionAuthorizationFinding, ...]
    normalized_evidence: tuple[AgentExecutionAuthorizationEvidence, ...]


_AuthorizationSubject = tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
]
_AssignmentValue = tuple[str, str, str, str, str]
_AuthorityProvenance = tuple[
    AgentExecutionAuthorizationAuthorityKind,
    str,
    str,
]


def _finding(
    code: str,
    message: str,
) -> AgentExecutionAuthorizationFinding:
    return AgentExecutionAuthorizationFinding(code=code, message=message)


def _invalid(
    findings: Iterable[AgentExecutionAuthorizationFinding],
) -> AgentExecutionAuthorizationValidationResult:
    return AgentExecutionAuthorizationValidationResult(
        valid=False,
        findings=tuple(findings),
        normalized_evidence=(),
    )


def _subject(
    evidence: AgentExecutionAuthorizationEvidence,
) -> _AuthorizationSubject:
    return (
        evidence.task_id,
        evidence.workflow_id,
        evidence.stage_id,
        evidence.role_id,
        evidence.actor_id,
        evidence.runtime_option_id,
        evidence.option_id,
        evidence.environment_id,
        evidence.operation_id,
        evidence.resource,
    )


def _assignment_value(
    evidence: AgentExecutionAuthorizationEvidence,
) -> _AssignmentValue:
    return (
        evidence.task_id,
        evidence.workflow_id,
        evidence.stage_id,
        evidence.role_id,
        evidence.actor_id,
    )


def _authority_provenance(
    evidence: AgentExecutionAuthorizationEvidence,
) -> _AuthorityProvenance:
    return (
        evidence.authority_kind,
        evidence.authority_id,
        evidence.provenance_reference,
    )


def _subject_message(subject: _AuthorizationSubject) -> str:
    (
        task_id,
        workflow_id,
        stage_id,
        role_id,
        actor_id,
        runtime_option_id,
        option_id,
        environment_id,
        operation_id,
        resource,
    ) = subject
    return (
        "Agent Execution Authorization Evidence subject "
        f"(task_id={task_id!r}, workflow_id={workflow_id!r}, "
        f"stage_id={stage_id!r}, role_id={role_id!r}, "
        f"actor_id={actor_id!r}, runtime_option_id={runtime_option_id!r}, "
        f"option_id={option_id!r}, environment_id={environment_id!r}, "
        f"operation_id={operation_id!r}, resource={resource!r})"
    )


def _assignment_message(assignment: _AssignmentValue) -> str:
    task_id, workflow_id, stage_id, role_id, actor_id = assignment
    return (
        f"Assignment (task_id={task_id!r}, workflow_id={workflow_id!r}, "
        f"stage_id={stage_id!r}, role_id={role_id!r}, "
        f"actor_id={actor_id!r})"
    )


def validate_agent_execution_authorization_evidence(
    evidence: Iterable[AgentExecutionAuthorizationEvidence],
    assignments: Iterable[Assignment],
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Iterable[Mapping[str, object]],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
    inference_options: Iterable[InferenceOptionDefinition],
    environment_id: str,
) -> AgentExecutionAuthorizationValidationResult:
    """Validate one caller-supplied authorization-evidence snapshot.

    Inputs are captured exactly once in the locked order. Existing Assignment,
    Runtime Option, and Inference Option validation is foundational. Repeated
    subjects are classified without resolution. Any finding atomically
    invalidates the snapshot; valid output preserves only supplied values and
    sorts them by the exact ten-part action subject.
    """

    captured_assignments = tuple(assignments)
    captured_actors = tuple(actors)
    captured_runtime_options = tuple(runtime_options)
    captured_inference_options = tuple(inference_options)
    captured_evidence = tuple(evidence)

    assignment_result = validate_assignment_set(
        captured_assignments,
        task,
        workflow_catalog,
        role_catalog,
        captured_actors,
    )
    if not assignment_result.valid:
        return _invalid(
            AgentExecutionAuthorizationFinding(finding.code, finding.message)
            for finding in assignment_result.findings
        )

    runtime_result = validate_agent_runtime_option_inventory(
        captured_runtime_options
    )
    if not runtime_result.valid:
        return _invalid(
            AgentExecutionAuthorizationFinding(finding.code, finding.message)
            for finding in runtime_result.findings
        )

    inference_result = validate_inference_option_inventory(
        captured_inference_options
    )
    if not inference_result.valid:
        return _invalid(
            AgentExecutionAuthorizationFinding(finding.code, finding.message)
            for finding in inference_result.findings
        )

    if type(environment_id) is not str or not environment_id:
        return _invalid(
            (
                _finding(
                    "agent_execution_authorization_environment_id_invalid",
                    "Agent Execution Authorization Evidence snapshot "
                    "environment_id must be an exact nonempty string.",
                ),
            )
        )

    has_invalid_type = any(
        type(item) is not AgentExecutionAuthorizationEvidence
        for item in captured_evidence
    )
    has_invalid_fields = any(
        type(item) is AgentExecutionAuthorizationEvidence
        and (
            type(item.task_id) is not str
            or not item.task_id
            or type(item.workflow_id) is not str
            or not item.workflow_id
            or type(item.stage_id) is not str
            or not item.stage_id
            or type(item.role_id) is not str
            or not item.role_id
            or type(item.actor_id) is not str
            or not item.actor_id
            or type(item.runtime_option_id) is not str
            or not item.runtime_option_id
            or type(item.option_id) is not str
            or not item.option_id
            or type(item.environment_id) is not str
            or not item.environment_id
            or type(item.operation_id) is not str
            or type(item.resource) is not str
            or type(item.authority_kind)
            is not AgentExecutionAuthorizationAuthorityKind
            or type(item.authority_id) is not str
            or not item.authority_id
            or type(item.provenance_reference) is not str
            or not item.provenance_reference
            or type(item.state) is not AgentExecutionAuthorizationState
        )
        for item in captured_evidence
    )
    type_findings: list[AgentExecutionAuthorizationFinding] = []
    if has_invalid_type:
        type_findings.append(
            _finding(
                "agent_execution_authorization_evidence_invalid_type",
                "Each supplied Agent Execution Authorization Evidence item "
                "must be an exact AgentExecutionAuthorizationEvidence value.",
            )
        )
    if has_invalid_fields:
        type_findings.append(
            _finding(
                "agent_execution_authorization_evidence_invalid",
                "A supplied Agent Execution Authorization Evidence value "
                "contains malformed subject, authority, provenance, or state "
                "fields.",
            )
        )
    if type_findings:
        return _invalid(type_findings)

    typed_evidence = tuple(
        item
        for item in captured_evidence
        if type(item) is AgentExecutionAuthorizationEvidence
    )
    by_subject: dict[
        _AuthorizationSubject,
        list[AgentExecutionAuthorizationEvidence],
    ] = defaultdict(list)
    for item in typed_evidence:
        by_subject[_subject(item)].append(item)

    duplicate_subjects: list[_AuthorizationSubject] = []
    conflicting_subjects: list[_AuthorizationSubject] = []
    multi_authority_subjects: list[_AuthorizationSubject] = []
    for subject, matching in by_subject.items():
        if len(matching) <= 1:
            continue
        states = {item.state for item in matching}
        authorities = {_authority_provenance(item) for item in matching}
        if len(states) > 1:
            conflicting_subjects.append(subject)
        elif len(authorities) > 1:
            multi_authority_subjects.append(subject)
        else:
            duplicate_subjects.append(subject)

    findings: list[AgentExecutionAuthorizationFinding] = []
    for subject in sorted(duplicate_subjects):
        findings.append(
            _finding(
                "duplicate_agent_execution_authorization_evidence",
                _subject_message(subject)
                + " has more than one identical supplied evidence value.",
            )
        )
    for subject in sorted(conflicting_subjects):
        findings.append(
            _finding(
                "conflicting_agent_execution_authorization_evidence",
                _subject_message(subject) + " has conflicting supplied states.",
            )
        )
    for subject in sorted(multi_authority_subjects):
        findings.append(
            _finding(
                "unsupported_multi_authority_agent_execution_authorization_evidence",
                _subject_message(subject)
                + " has same-state evidence with differing authority or "
                "provenance; multi-authority composition is not supported.",
            )
        )

    supplied_assignment_values = {
        (
            assignment.task_id,
            assignment.workflow_id,
            assignment.stage_id,
            assignment.role_id,
            assignment.actor_id,
        )
        for assignment in captured_assignments
    }
    evidence_assignment_values = {
        _assignment_value(item) for item in typed_evidence
    }
    unmatched_assignments = sorted(
        evidence_assignment_values - supplied_assignment_values
    )
    for assignment in unmatched_assignments:
        findings.append(
            _finding(
                "agent_execution_authorization_assignment_not_found",
                _assignment_message(assignment)
                + " was not found in the supplied valid Assignment context.",
            )
        )

    actors_by_id = {
        cast(str, actor["id"]): actor for actor in captured_actors
    }
    human_assignments = sorted(
        assignment
        for assignment in evidence_assignment_values & supplied_assignment_values
        if actors_by_id[assignment[4]]["kind"] == "human"
    )
    for assignment in human_assignments:
        actor_id = assignment[4]
        findings.append(
            _finding(
                "agent_execution_authorization_not_applicable_to_human_actor",
                "Agent Execution Authorization Evidence does not apply to "
                f"Human Actor {actor_id!r} for {_assignment_message(assignment)}.",
            )
        )

    known_runtime_option_ids = {
        option.runtime_option_id
        for option in runtime_result.normalized_options
    }
    for runtime_option_id in sorted(
        {item.runtime_option_id for item in typed_evidence}
        - known_runtime_option_ids
    ):
        findings.append(
            _finding(
                "agent_runtime_option_not_found",
                f"Agent Runtime Option '{runtime_option_id}' was not found "
                "in the supplied inventory.",
            )
        )

    known_inference_option_ids = {
        option.option_id for option in inference_result.normalized_options
    }
    for option_id in sorted(
        {item.option_id for item in typed_evidence}
        - known_inference_option_ids
    ):
        findings.append(
            _finding(
                "inference_option_not_found",
                f"Inference Option '{option_id}' was not found in the supplied "
                "inventory.",
            )
        )

    for observed_environment_id in sorted(
        {
            item.environment_id
            for item in typed_evidence
            if item.environment_id != environment_id
        }
    ):
        findings.append(
            _finding(
                "agent_execution_authorization_environment_mismatch",
                "Agent Execution Authorization Evidence environment_id "
                f"{observed_environment_id!r} does not match snapshot "
                f"environment_id {environment_id!r}.",
            )
        )

    operation_issues = {
        operation_id: validate_core_operation_id(operation_id)
        for operation_id in {item.operation_id for item in typed_evidence}
    }
    for operation_id in sorted(
        operation_id
        for operation_id, issue in operation_issues.items()
        if issue == "operation_id_invalid_syntax"
    ):
        findings.append(
            _finding(
                "operation_id_invalid_syntax",
                "Agent Execution Authorization Evidence operation_id must use "
                "ASCII lower_snake_case syntax.",
            )
        )
    for operation_id in sorted(
        operation_id
        for operation_id, issue in operation_issues.items()
        if issue == "operation_id_not_supported"
    ):
        findings.append(
            _finding(
                "operation_id_not_supported",
                f"Operation ID '{operation_id}' is not supported by Core.",
            )
        )

    resource_issues: list[
        tuple[str, RepositoryResourceValidationIssue]
    ] = []
    for resource in {item.resource for item in typed_evidence}:
        issue = validate_repository_resource(resource)
        if issue is not None:
            resource_issues.append((resource, issue))
    for resource, issue in sorted(
        resource_issues,
        key=lambda item: _repository_resource_issue_sort_key(
            item[1], item[0]
        ),
    ):
        findings.append(
            _finding(
                issue.code,
                "Agent Execution Authorization Evidence resource "
                f"{resource!r} {issue.message_suffix}",
            )
        )

    if findings:
        return _invalid(findings)

    return AgentExecutionAuthorizationValidationResult(
        valid=True,
        findings=(),
        normalized_evidence=tuple(sorted(typed_evidence, key=_subject)),
    )
