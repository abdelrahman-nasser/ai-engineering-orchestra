"""Pure Assignment responsibility-binding validation over supplied data.

Assignment records which concrete Actor was selected for one required Role at
one Workflow Stage for one Task. It does not select Actors, inspect availability,
grant authority, execute work, persist state, or evaluate Quality Gates.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias, cast

from engineering_orchestration._responsibility import (
    _require_valid_role_catalog,
    _resolve_task_responsibility,
    _resolve_task_workflow,
    _task_workflow_id,
)
from engineering_orchestration.actor_coverage import (
    ActorRoleCoverage,
    evaluate_actor_role_coverage,
)
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowDefinition,
)


AssignmentKey: TypeAlias = tuple[str, str, str, str]


@dataclass(frozen=True)
class Assignment:
    """One immutable Actor-to-responsibility binding."""

    task_id: str
    workflow_id: str
    stage_id: str
    role_id: str
    actor_id: str

    @property
    def key(self) -> AssignmentKey:
        """Return the responsibility identity, excluding the selected Actor."""
        return (self.task_id, self.workflow_id, self.stage_id, self.role_id)


@dataclass(frozen=True)
class AssignmentFinding:
    """Stable semantic finding produced by Assignment validation."""

    code: str
    message: str


@dataclass(frozen=True)
class AssignmentValidationResult:
    """Validation result for one Assignment."""

    valid: bool
    findings: tuple[AssignmentFinding, ...]
    coverage: ActorRoleCoverage | None


@dataclass(frozen=True)
class AssignmentSetValidationResult:
    """Validation and completeness result for a supplied Assignment sequence."""

    valid: bool
    complete: bool | None
    findings: tuple[AssignmentFinding, ...]
    unassigned_requirements: tuple[AssignmentKey, ...]
    separation_findings: tuple[AssignmentFinding, ...]


def _invalid(
    code: str,
    message: str,
    *,
    coverage: ActorRoleCoverage | None = None,
) -> AssignmentValidationResult:
    return AssignmentValidationResult(
        valid=False,
        findings=(AssignmentFinding(code=code, message=message),),
        coverage=coverage,
    )


def _duplicate_actor_ids(
    actors: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    actor_ids = [cast(str, actor["id"]) for actor in actors]
    return tuple(sorted(actor_id for actor_id, count in Counter(actor_ids).items()
                        if count > 1))


def _duplicate_actor_finding(
    actors: Sequence[Mapping[str, object]],
) -> AssignmentFinding | None:
    duplicates = _duplicate_actor_ids(actors)
    if not duplicates:
        return None
    return AssignmentFinding(
        code="duplicate_actor_id",
        message="Actor IDs must be unique in the supplied context; duplicates: "
        + ", ".join(duplicates),
    )


def validate_assignment(
    assignment: Assignment,
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Sequence[Mapping[str, object]],
) -> AssignmentValidationResult:
    """Validate one responsibility binding in dependency-aware order.

    Inputs are expected to have passed their structural schemas. Ordinary
    consumer-data problems return findings. A corrupt or unusable framework
    catalog remains an infrastructure failure and raises its catalog error.
    """

    duplicate_actor = _duplicate_actor_finding(actors)
    if duplicate_actor is not None:
        return AssignmentValidationResult(False, (duplicate_actor,), None)

    task_id = cast(str, task["id"])
    if assignment.task_id != task_id:
        return _invalid(
            "task_id_mismatch",
            f"Assignment Task ID '{assignment.task_id}' does not match supplied "
            f"Task ID '{task_id}'.",
        )

    task_workflow_id, workflow_failure = _task_workflow_id(task)
    if workflow_failure is not None:
        return _invalid(*workflow_failure)
    task_workflow_id = cast(str, task_workflow_id)

    if assignment.workflow_id != task_workflow_id:
        return _invalid(
            "workflow_id_mismatch",
            f"Assignment Workflow ID '{assignment.workflow_id}' does not match "
            f"Task Workflow '{task_workflow_id}'.",
        )

    _, role, resolution_failure = _resolve_task_responsibility(
        task,
        assignment.stage_id,
        assignment.role_id,
        workflow_catalog,
        role_catalog,
        catalog_consumer="Assignment validation",
    )
    if resolution_failure is not None:
        return _invalid(*resolution_failure)
    assert role is not None

    actors_by_id = {cast(str, actor["id"]): actor for actor in actors}
    actor = actors_by_id.get(assignment.actor_id)
    if actor is None:
        return _invalid(
            "actor_not_found",
            f"Actor '{assignment.actor_id}' was not found in the supplied Actor context.",
        )

    coverage = evaluate_actor_role_coverage(actor, role)
    if not coverage.compatible:
        evidence = (
            f" diagnostic={coverage.diagnostic}"
            if coverage.diagnostic is not None
            else " missing=" + ", ".join(coverage.missing_competencies)
        )
        return _invalid(
            "actor_role_incompatible",
            f"Actor '{assignment.actor_id}' does not cover Role "
            f"'{assignment.role_id}';{evidence}",
            coverage=coverage,
        )

    return AssignmentValidationResult(valid=True, findings=(), coverage=coverage)


def _requirement_keys(
    task_id: str,
    workflow: WorkflowDefinition,
) -> tuple[AssignmentKey, ...]:
    requirements: list[AssignmentKey] = []
    for stage in workflow.stages:
        seen_roles: set[str] = set()
        for role_id in stage.required_roles:
            if role_id in seen_roles:
                continue
            seen_roles.add(role_id)
            requirements.append((task_id, workflow.id, stage.id, role_id))
    return tuple(requirements)


def _duplicate_binding_findings(
    assignments: tuple[Assignment, ...],
    key_counts: Counter[AssignmentKey],
) -> tuple[AssignmentFinding, ...]:
    findings: list[AssignmentFinding] = []
    seen: set[AssignmentKey] = set()
    for assignment in assignments:
        key = assignment.key
        if key_counts[key] < 2 or key in seen:
            continue
        seen.add(key)
        findings.append(AssignmentFinding(
            code="duplicate_assignment_binding",
            message="Responsibility binding appears more than once: "
            + "/".join(key),
        ))
    return tuple(findings)


def _separation_findings(
    valid_unique: tuple[Assignment, ...],
) -> tuple[AssignmentFinding, ...]:
    implementers = [item for item in valid_unique
                    if item.role_id == "software-engineer"]
    reviewers = [item for item in valid_unique if item.role_id == "reviewer"]
    conflicts: list[AssignmentFinding] = []
    seen: set[tuple[str, str, str]] = set()
    for reviewer in reviewers:
        for implementer in implementers:
            conflict = (
                reviewer.task_id,
                reviewer.workflow_id,
                reviewer.actor_id,
            )
            if (
                reviewer.task_id == implementer.task_id
                and reviewer.workflow_id == implementer.workflow_id
                and reviewer.actor_id == implementer.actor_id
                and conflict not in seen
            ):
                seen.add(conflict)
                conflicts.append(AssignmentFinding(
                    code="reviewer_actor_matches_implementer",
                    message=f"Actor '{reviewer.actor_id}' is bound to both "
                    "software-engineer and reviewer responsibilities for Task "
                    f"'{reviewer.task_id}' in Workflow '{reviewer.workflow_id}'.",
                ))
    return tuple(conflicts)


def validate_assignment_set(
    assignments: Sequence[Assignment],
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Sequence[Mapping[str, object]],
) -> AssignmentSetValidationResult:
    """Validate supplied bindings and report Workflow responsibility coverage.

    This function accepts an ordinary sequence; it does not define or persist an
    AssignmentSet domain object. Separation findings are evidence only and do
    not change validity, completeness, Workflow state, or Quality Gate state.
    """

    supplied = tuple(assignments)
    task_id = cast(str, task["id"])
    duplicate_actor = _duplicate_actor_finding(actors)

    workflow, workflow_failure = _resolve_task_workflow(
        task,
        workflow_catalog,
        catalog_consumer="Assignment validation",
    )
    if workflow is None:
        findings = (duplicate_actor,) if duplicate_actor is not None else ()
        workflow_finding = (
            AssignmentFinding(*workflow_failure)
            if workflow_failure is not None
            else None
        )
        if workflow_finding is not None and workflow_finding not in findings:
            findings += (workflow_finding,)
        return AssignmentSetValidationResult(
            valid=False,
            complete=None,
            findings=findings,
            unassigned_requirements=(),
            separation_findings=(),
        )

    _require_valid_role_catalog(
        role_catalog,
        catalog_consumer="Assignment validation",
    )
    requirements = _requirement_keys(task_id, workflow)

    if duplicate_actor is not None:
        return AssignmentSetValidationResult(
            valid=False,
            complete=not requirements,
            findings=(duplicate_actor,),
            unassigned_requirements=requirements,
            separation_findings=(),
        )

    key_counts: Counter[AssignmentKey] = Counter(
        assignment.key for assignment in supplied
    )
    findings = list(_duplicate_binding_findings(supplied, key_counts))
    valid_unique: list[Assignment] = []

    for assignment in supplied:
        result = validate_assignment(
            assignment,
            task,
            workflow_catalog,
            role_catalog,
            actors,
        )
        findings.extend(result.findings)
        if result.valid and key_counts[assignment.key] == 1:
            valid_unique.append(assignment)

    covered = {assignment.key for assignment in valid_unique}
    unassigned = tuple(key for key in requirements if key not in covered)
    valid_unique_tuple = tuple(valid_unique)
    return AssignmentSetValidationResult(
        valid=not findings,
        complete=not unassigned,
        findings=tuple(findings),
        unassigned_requirements=unassigned,
        separation_findings=_separation_findings(valid_unique_tuple),
    )
