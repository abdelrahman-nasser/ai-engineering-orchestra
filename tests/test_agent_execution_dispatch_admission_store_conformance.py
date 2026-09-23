"""Focused backend-neutral AIO-047 store/coordinator conformance tests."""

from __future__ import annotations

from dataclasses import replace
from inspect import signature
import unittest
from unittest.mock import patch

import engineering_orchestration.agent_execution_dispatch_admission_store as subject
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
)
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentActionPrerequisiteParentInputs,
    AgentExecutionDispatchAdmissionCoordinator,
    AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    AgentExecutionDispatchAdmissionStoreOutcome,
    AgentExecutionDispatchAdmissionStoreResult,
    AgentExecutionDispatchAdmissionStoreRetryDisposition,
    make_agent_execution_dispatch_admission_store_administration_result,
    make_agent_execution_dispatch_admission_store_result,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
)


DOMAIN_ID = "authorization-domain::synthetic"
RESPONSIBILITY_KEY = (
    "AIO-047",
    "architecture-change",
    "implement",
    "software-engineer",
)
ACTOR_ID = "actor::synthetic"
RUNTIME_OPTION_ID = "runtime::synthetic"
OPTION_ID = "inference::synthetic"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
RESOURCE = "synthetic/input.txt"
DECISION_TIME = "2026-01-01T00:00:00.000000Z"


def make_run(
    *,
    run_id: str = "run::synthetic",
    resource: str = RESOURCE,
) -> AgentExecutionRun:
    return AgentExecutionRun(
        run_id=run_id,
        contract=AgentExecutionContract(
            task_id=RESPONSIBILITY_KEY[0],
            workflow_id=RESPONSIBILITY_KEY[1],
            stage_id=RESPONSIBILITY_KEY[2],
            role_id=RESPONSIBILITY_KEY[3],
            actor_id=ACTOR_ID,
            runtime_option_id=RUNTIME_OPTION_ID,
            option_id=OPTION_ID,
            environment_id=ENVIRONMENT_ID,
            operation_id=OPERATION_ID,
            resource=resource,
            execution_mode="critical",
        ),
    )


def make_grant(
    *,
    grant_id: str = "grant::synthetic",
    run: AgentExecutionRun | None = None,
    domain_id: str = DOMAIN_ID,
    issued_at: str = "2025-01-01T00:00:00Z",
    expires_at: str = "2027-01-01T00:00:00Z",
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id=grant_id,
        run=run or make_run(),
        authorization_domain_id=domain_id,
        issuer_kind="policy",
        issuer_id="issuer::synthetic",
        provenance_reference="provenance::synthetic",
        issued_at=issued_at,
        expires_at=expires_at,
    )


def make_parents(
    *,
    permission_state: EnvironmentOperationPermissionState = (
        EnvironmentOperationPermissionState.ALLOWED
    ),
) -> AgentActionPrerequisiteParentInputs:
    candidate = AgentExecutionCandidatePrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=RESPONSIBILITY_KEY,
        actor_id=ACTOR_ID,
        runtime_option_id=RUNTIME_OPTION_ID,
        option_id=OPTION_ID,
        outcome=AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
        reasons=(
            AgentExecutionCandidatePrerequisiteReason.
            ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
        ),
    )
    capability = RuntimeOperationCapabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=(
            RuntimeOperationCapabilityObservation(
                RUNTIME_OPTION_ID,
                OPERATION_ID,
                RuntimeOperationCapabilityState.PRESENT,
            ),
        ),
    )
    permission = EnvironmentOperationPermissionValidationResult(
        valid=True,
        findings=(),
        normalized_observations=(
            EnvironmentOperationPermissionObservation(
                RUNTIME_OPTION_ID,
                ENVIRONMENT_ID,
                OPERATION_ID,
                RESOURCE,
                permission_state,
            ),
        ),
    )
    evidence = AgentExecutionAuthorizationEvidence(
        *RESPONSIBILITY_KEY,
        ACTOR_ID,
        RUNTIME_OPTION_ID,
        OPTION_ID,
        ENVIRONMENT_ID,
        OPERATION_ID,
        RESOURCE,
        AgentExecutionAuthorizationAuthorityKind.HUMAN,
        "human::synthetic",
        "authorization-evidence::synthetic",
        AgentExecutionAuthorizationState.GRANTED,
    )
    authorization = AgentExecutionAuthorizationValidationResult(
        valid=True,
        findings=(),
        normalized_evidence=(evidence,),
    )
    return AgentActionPrerequisiteParentInputs(
        candidate_result=candidate,
        requirement=OperationRequirement(OPERATION_ID, RESOURCE),
        capability_result=capability,
        permission_result=permission,
        authorization_result=authorization,
        environment_id=ENVIRONMENT_ID,
    )


def grant_identity(
    grant: AgentExecutionAuthorizationGrant,
) -> tuple[str, str, str, str]:
    return (
        grant.authorization_domain_id,
        grant.issuer_kind,
        grant.issuer_id,
        grant.grant_id,
    )


class SyntheticGrantAuthentication:
    def __init__(self, log: list[str], *, allow: bool = True) -> None:
        self.log = log
        self.allow = allow

    def authenticate_grant(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        self.log.append("authenticate_grant")
        if self.allow and type(presented_grant) is AgentExecutionAuthorizationGrant:
            return presented_grant
        return None


class SyntheticBindingResolver:
    def __init__(
        self,
        log: list[str],
        *,
        tool_id: str = "tool::synthetic::v1",
    ) -> None:
        self.log = log
        self.tool_id = tool_id
        self.allow = True

    def resolve_tool_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentOperationToolBinding | None:
        self.log.append("resolve_tool_binding")
        if not self.allow:
            return None
        return AgentOperationToolBinding(grant.run, self.tool_id)


class SyntheticFreshSource:
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.parents = make_parents()

    def collect_fresh_parent_results(
        self,
        grant: AgentExecutionAuthorizationGrant,
        tool_binding: AgentOperationToolBinding,
    ) -> AgentActionPrerequisiteParentInputs | None:
        del grant, tool_binding
        self.log.append("collect_fresh_parent_results")
        return self.parents


class SyntheticModeResolver:
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.mode: str | None = "critical"

    def resolve_effective_execution_mode(
        self,
        grant: AgentExecutionAuthorizationGrant,
        tool_binding: AgentOperationToolBinding,
    ) -> str | None:
        del grant, tool_binding
        self.log.append("resolve_effective_execution_mode")
        return self.mode


class SyntheticRevocationAuthentication:
    def __init__(self, log: list[str], *, allow: bool = True) -> None:
        self.log = log
        self.allow = allow

    def authenticate_original_issuer_revocation(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        self.log.append("authenticate_original_issuer_revocation")
        if self.allow and type(presented_grant) is AgentExecutionAuthorizationGrant:
            return presented_grant
        return None


class SyntheticConformanceStore:
    """Test-only model; deliberately not a production fallback backend."""

    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.admissions: dict[
            tuple[str, str, str, str],
            AgentExecutionDispatchAdmission,
        ] = {}
        self.revocations: dict[
            tuple[str, str, str, str],
            AgentExecutionAuthorizationGrant,
        ] = {}

    @staticmethod
    def _result(
        outcome: AgentExecutionDispatchAdmissionStoreOutcome,
        *,
        admission: AgentExecutionDispatchAdmission | None = None,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        return make_agent_execution_dispatch_admission_store_result(
            outcome,
            admission=admission,
        )

    def _classify(
        self,
        domain_id: str,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        if domain_id != DOMAIN_ID or grant.authorization_domain_id != DOMAIN_ID:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH
            )
        identity = grant_identity(grant)
        existing = self.admissions.get(identity)
        if existing is not None:
            if existing.grant != grant:
                return self._result(
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    GRANT_IDENTITY_CONFLICT
                )
            if existing.tool_binding != binding:
                return self._result(
                    AgentExecutionDispatchAdmissionStoreOutcome.BINDING_CONFLICT
                )
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                EXISTING_EXACT_ADMISSION,
                admission=existing,
            )
        run_key = (grant.authorization_domain_id, grant.run.run_id)
        if any(
            (item.grant.authorization_domain_id, item.grant.run.run_id)
            == run_key
            for item in self.admissions.values()
        ):
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.RUN_CONFLICT
            )
        return self._result(
            AgentExecutionDispatchAdmissionStoreOutcome.NO_EXISTING_ADMISSION
        )

    def classify_guarded_history(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        self.log.append("classify_guarded_history")
        opened = subject._open_guarded_history_request(request)
        if opened is None:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT
            )
        return self._classify(*opened)

    def admit_or_return_existing(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        self.log.append("admit_or_return_existing")
        opened = subject._open_admission_request(request)
        if opened is None:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT
            )
        domain_id, grant, binding, expected_run = opened
        history = self._classify(domain_id, grant, binding)
        if (
            history.outcome
            is not AgentExecutionDispatchAdmissionStoreOutcome.
            NO_EXISTING_ADMISSION
        ):
            return history
        if not grant.run == binding.run == expected_run:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT
            )
        if grant_identity(grant) in self.revocations:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.REVOKED
            )
        admission = AgentExecutionDispatchAdmission(
            grant,
            binding,
            DECISION_TIME,
        )
        self.admissions[grant_identity(grant)] = admission
        return self._result(
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
            admission=admission,
        )

    def load_authoritative_admission(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        self.log.append("load_authoritative_admission")
        opened = subject._open_authoritative_lookup_request(request)
        if opened is None:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT
            )
        domain_id, grant, binding = opened
        if domain_id != DOMAIN_ID or grant.authorization_domain_id != DOMAIN_ID:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH
            )
        existing = self.admissions.get(grant_identity(grant))
        if existing is None:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                NO_EXISTING_ADMISSION
            )
        if existing.grant != grant:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                GRANT_IDENTITY_CONFLICT
            )
        if existing.tool_binding != binding:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.BINDING_CONFLICT
            )
        return self._result(
            AgentExecutionDispatchAdmissionStoreOutcome.
            EXISTING_EXACT_ADMISSION,
            admission=existing,
        )

    def revoke_or_return_existing(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        self.log.append("revoke_or_return_existing")
        opened = subject._open_revocation_request(request)
        if opened is None:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT
            )
        domain_id, grant = opened
        if domain_id != DOMAIN_ID or grant.authorization_domain_id != DOMAIN_ID:
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH
            )
        identity = grant_identity(grant)
        existing = self.revocations.get(identity)
        if existing is not None:
            if existing != grant:
                return self._result(
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    GRANT_IDENTITY_CONFLICT
                )
            return self._result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                EXISTING_EXACT_REVOCATION
            )
        self.revocations[identity] = grant
        return self._result(
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED
        )


class CoordinatorFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.log: list[str] = []
        self.grant_auth = SyntheticGrantAuthentication(self.log)
        self.binding_resolver = SyntheticBindingResolver(self.log)
        self.fresh_source = SyntheticFreshSource(self.log)
        self.mode_resolver = SyntheticModeResolver(self.log)
        self.revocation_auth = SyntheticRevocationAuthentication(self.log)
        self.store = SyntheticConformanceStore(self.log)
        self.coordinator = AgentExecutionDispatchAdmissionCoordinator(
            authorization_domain_id=DOMAIN_ID,
            store=self.store,
            grant_authentication=self.grant_auth,
            tool_binding_resolver=self.binding_resolver,
            fresh_prerequisite_source=self.fresh_source,
            execution_mode_resolver=self.mode_resolver,
            revocation_authentication=self.revocation_auth,
        )


class ResultTaxonomyTests(unittest.TestCase):
    def test_operational_outcomes_cover_locked_taxonomy(self) -> None:
        values = {item.value for item in AgentExecutionDispatchAdmissionStoreOutcome}
        self.assertEqual(
            values,
            {
                "newly_admitted",
                "existing_exact_admission",
                "newly_revoked",
                "existing_exact_revocation",
                "no_existing_admission",
                "not_yet_current",
                "expired",
                "revoked",
                "domain_mismatch",
                "grant_identity_conflict",
                "binding_conflict",
                "run_conflict",
                "invalid_input",
                "unauthenticated_grant",
                "untrusted_tool_binding",
                "unsatisfied_prerequisites",
                "storage_busy",
                "storage_unavailable",
                "incompatible_schema",
                "integrity_failure",
                "clock_failure",
                "clock_regression",
                "commit_unknown",
            },
        )

    def test_retry_dispositions_are_typed_and_outcome_specific(self) -> None:
        expected = {
            AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY:
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RETRY_EXACT_REQUEST,
            AgentExecutionDispatchAdmissionStoreOutcome.NOT_YET_CURRENT:
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RETRY_AT_OR_AFTER_ISSUANCE,
            AgentExecutionDispatchAdmissionStoreOutcome.
            UNSATISFIED_PREREQUISITES:
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RECOLLECT_FRESH_STATE,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE:
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RETRY_AFTER_REMEDIATION,
            AgentExecutionDispatchAdmissionStoreOutcome.EXPIRED:
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST,
        }
        for outcome, retry in expected.items():
            with self.subTest(outcome=outcome):
                result = make_agent_execution_dispatch_admission_store_result(
                    outcome
                )
                self.assertIs(result.retry_disposition, retry)
                self.assertNotIsInstance(result.retry_disposition, bool)

    def test_migration_and_fencing_are_separate_administrative_results(self) -> None:
        migration = (
            make_agent_execution_dispatch_admission_store_administration_result(
                AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                MIGRATION_FAILURE
            )
        )
        backup = (
            make_agent_execution_dispatch_admission_store_administration_result(
                AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                FENCED_BACKUP_CREATED
            )
        )
        commit_unknown = (
            make_agent_execution_dispatch_admission_store_administration_result(
                AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                COMMIT_UNKNOWN
            )
        )
        unavailable = (
            make_agent_execution_dispatch_admission_store_administration_result(
                AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                STORAGE_UNAVAILABLE
            )
        )
        self.assertIs(
            migration.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_AFTER_REMEDIATION,
        )
        self.assertIs(
            backup.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.NO_RETRY_NEEDED,
        )
        self.assertIs(
            commit_unknown.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RECONCILE_ADMINISTRATIVE_STATE,
        )
        self.assertIs(
            unavailable.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_AFTER_REMEDIATION,
        )


class AuthorityInternalRequestTests(unittest.TestCase):
    def test_request_types_cannot_be_directly_constructed(self) -> None:
        request_types = (
            subject._AgentExecutionDispatchAdmissionHistoryRequest,
            subject._AgentExecutionDispatchAdmissionRequest,
            subject._AgentExecutionDispatchAdmissionLookupRequest,
            subject._AgentExecutionAuthorizationRevocationRequest,
        )
        for request_type in request_types:
            with self.subTest(request_type=request_type):
                with self.assertRaises(TypeError):
                    request_type()

    def test_arbitrary_objects_do_not_open_as_authority_internal_requests(
        self,
    ) -> None:
        self.assertIsNone(subject._open_guarded_history_request(object()))
        self.assertIsNone(subject._open_admission_request(object()))
        self.assertIsNone(subject._open_authoritative_lookup_request(object()))
        self.assertIsNone(subject._open_revocation_request(object()))

    def test_public_coordinator_request_accepts_no_trust_time_or_parent_flags(
        self,
    ) -> None:
        parameters = tuple(
            signature(AgentExecutionDispatchAdmissionCoordinator.admit).
            parameters
        )
        self.assertEqual(parameters, ("self", "presented_grant"))
        module_text = subject.__doc__ or ""
        self.assertNotIn("trusted: bool", module_text)


class CoordinatorOrderingAndConformanceTests(CoordinatorFixture):
    def test_authentication_and_domain_rejection_precede_resolution_and_history(
        self,
    ) -> None:
        self.grant_auth.allow = False
        unauthenticated = self.coordinator.admit(make_grant())
        self.assertIs(
            unauthenticated.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.UNAUTHENTICATED_GRANT,
        )
        self.assertEqual(self.log, ["authenticate_grant"])

        self.log.clear()
        mismatch = self.coordinator.admit(make_grant(domain_id="other-domain"))
        self.assertIs(
            mismatch.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.UNAUTHENTICATED_GRANT,
        )
        self.assertEqual(self.log, ["authenticate_grant"])

        self.grant_auth.allow = True
        self.log.clear()
        mismatch = self.coordinator.admit(make_grant(domain_id="other-domain"))
        self.assertIs(
            mismatch.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH,
        )
        self.assertEqual(self.log, ["authenticate_grant"])

    def test_new_admission_recomputes_aio_040_041_042_in_locked_order(
        self,
    ) -> None:
        grant = make_grant()
        with (
            patch.object(
                subject,
                "assess_agent_action_prerequisites",
                wraps=subject.assess_agent_action_prerequisites,
            ) as assess,
            patch.object(
                subject,
                "prepare_agent_execution_contract",
                wraps=subject.prepare_agent_execution_contract,
            ) as prepare_contract,
            patch.object(
                subject,
                "prepare_agent_execution_run",
                wraps=subject.prepare_agent_execution_run,
            ) as prepare_run,
        ):
            result = self.coordinator.admit(grant)

        self.assertIs(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
        )
        self.assertEqual(
            self.log,
            [
                "authenticate_grant",
                "resolve_tool_binding",
                "classify_guarded_history",
                "collect_fresh_parent_results",
                "resolve_effective_execution_mode",
                "admit_or_return_existing",
            ],
        )
        self.assertEqual(assess.call_count, 1)
        self.assertEqual(prepare_contract.call_count, 1)
        self.assertEqual(prepare_run.call_count, 1)
        self.assertEqual(result.admission.grant.run.run_id, grant.run.run_id)

    def test_exact_history_returns_original_time_without_fresh_collection(
        self,
    ) -> None:
        grant = make_grant()
        first = self.coordinator.admit(grant)
        self.assertIsNotNone(first.admission)
        self.log.clear()

        with patch.object(
            subject,
            "assess_agent_action_prerequisites",
            side_effect=AssertionError("historical retry recollected prerequisites"),
        ):
            second = self.coordinator.admit(grant)

        self.assertIs(
            second.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            EXISTING_EXACT_ADMISSION,
        )
        self.assertEqual(second.admission, first.admission)
        self.assertEqual(second.admission.decision_time, DECISION_TIME)
        self.assertEqual(
            self.log,
            [
                "authenticate_grant",
                "resolve_tool_binding",
                "classify_guarded_history",
            ],
        )

    def test_changed_binding_and_second_grant_same_run_fail_before_freshness(
        self,
    ) -> None:
        grant = make_grant()
        self.assertIs(
            self.coordinator.admit(grant).outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
        )

        self.log.clear()
        self.binding_resolver.tool_id = "tool::synthetic::v2"
        changed = self.coordinator.admit(grant)
        self.assertIs(
            changed.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.BINDING_CONFLICT,
        )
        self.assertNotIn("collect_fresh_parent_results", self.log)

        self.log.clear()
        second_grant = make_grant(grant_id="grant::second", run=grant.run)
        run_conflict = self.coordinator.admit(second_grant)
        self.assertIs(
            run_conflict.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.RUN_CONFLICT,
        )
        self.assertNotIn("collect_fresh_parent_results", self.log)

    def test_grant_identity_conflict_precedes_binding_and_run_conflicts(self) -> None:
        original = make_grant()
        self.assertIs(
            self.coordinator.admit(original).outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
        )
        rebound = replace(
            original,
            provenance_reference="provenance::changed",
        )
        self.binding_resolver.tool_id = "tool::synthetic::v2"
        self.log.clear()
        result = self.coordinator.admit(rebound)
        self.assertIs(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            GRANT_IDENTITY_CONFLICT,
        )
        self.assertNotIn("collect_fresh_parent_results", self.log)

    def test_unsatisfied_fresh_assessment_never_reaches_admission_transaction(
        self,
    ) -> None:
        self.fresh_source.parents = make_parents(
            permission_state=EnvironmentOperationPermissionState.DENIED
        )
        result = self.coordinator.admit(make_grant())
        self.assertIs(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            UNSATISFIED_PREREQUISITES,
        )
        self.assertNotIn("admit_or_return_existing", self.log)

    def test_authoritative_load_is_guarded_and_arbitrary_value_is_descriptive(
        self,
    ) -> None:
        grant = make_grant()
        created = self.coordinator.admit(grant)
        direct_copy = AgentExecutionDispatchAdmission(
            created.admission.grant,
            created.admission.tool_binding,
            created.admission.decision_time,
        )
        self.assertEqual(direct_copy, created.admission)

        self.log.clear()
        loaded = self.coordinator.load_authoritative_admission(grant)
        self.assertIs(
            loaded.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            EXISTING_EXACT_ADMISSION,
        )
        self.assertEqual(loaded.admission, direct_copy)
        self.assertEqual(
            self.log,
            [
                "authenticate_grant",
                "resolve_tool_binding",
                "load_authoritative_admission",
            ],
        )

    def test_original_issuer_revocation_is_separate_and_does_not_mutate_history(
        self,
    ) -> None:
        grant = make_grant()
        admitted = self.coordinator.admit(grant)
        self.log.clear()
        revoked = self.coordinator.revoke(grant)
        repeated = self.coordinator.revoke(grant)
        loaded = self.coordinator.load_authoritative_admission(grant)

        self.assertIs(
            revoked.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        )
        self.assertIs(
            repeated.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            EXISTING_EXACT_REVOCATION,
        )
        self.assertEqual(loaded.admission, admitted.admission)

    def test_revocation_first_blocks_new_admission(self) -> None:
        grant = make_grant()
        self.assertIs(
            self.coordinator.revoke(grant).outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        )
        self.log.clear()
        result = self.coordinator.admit(grant)
        self.assertIs(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.REVOKED,
        )

    def test_incoherent_backend_result_fails_closed_as_integrity_failure(
        self,
    ) -> None:
        malformed = AgentExecutionDispatchAdmissionStoreResult(
            outcome=AgentExecutionDispatchAdmissionStoreOutcome.
            NO_EXISTING_ADMISSION,
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RETRY_EXACT_REQUEST
            ),
            admission=None,
            detail="malformed",
        )
        with patch.object(
            self.store,
            "classify_guarded_history",
            return_value=malformed,
        ):
            result = self.coordinator.admit(make_grant())
        self.assertIs(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )

    def test_operation_specific_store_outcomes_fail_closed(self) -> None:
        grant = make_grant()
        binding = AgentOperationToolBinding(grant.run, "tool::synthetic::v1")
        admission = AgentExecutionDispatchAdmission(
            grant,
            binding,
            DECISION_TIME,
        )
        impossible_history = make_agent_execution_dispatch_admission_store_result(
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
            admission=admission,
        )
        with patch.object(
            self.store,
            "classify_guarded_history",
            return_value=impossible_history,
        ):
            history_result = self.coordinator.admit(grant)
        self.assertIs(
            history_result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )
        self.assertNotIn("collect_fresh_parent_results", self.log)

        self.log.clear()
        with patch.object(
            self.store,
            "load_authoritative_admission",
            return_value=impossible_history,
        ):
            load_result = self.coordinator.load_authoritative_admission(grant)
        self.assertIs(
            load_result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )

        impossible_admit = make_agent_execution_dispatch_admission_store_result(
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        )
        with patch.object(
            self.store,
            "admit_or_return_existing",
            return_value=impossible_admit,
        ):
            admit_result = self.coordinator.admit(grant)
        self.assertIs(
            admit_result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )

        impossible_revoke = make_agent_execution_dispatch_admission_store_result(
            AgentExecutionDispatchAdmissionStoreOutcome.NOT_YET_CURRENT,
        )
        with patch.object(
            self.store,
            "revoke_or_return_existing",
            return_value=impossible_revoke,
        ):
            revoke_result = self.coordinator.revoke(grant)
        self.assertIs(
            revoke_result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )

    def test_backend_neutral_currentness_and_failure_outcomes_propagate(self) -> None:
        grant = make_grant()
        cases = (
            AgentExecutionDispatchAdmissionStoreOutcome.NOT_YET_CURRENT,
            AgentExecutionDispatchAdmissionStoreOutcome.EXPIRED,
            AgentExecutionDispatchAdmissionStoreOutcome.REVOKED,
            AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY,
            AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
            AgentExecutionDispatchAdmissionStoreOutcome.INCOMPATIBLE_SCHEMA,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
            AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_FAILURE,
            AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_REGRESSION,
            AgentExecutionDispatchAdmissionStoreOutcome.COMMIT_UNKNOWN,
        )
        for outcome in cases:
            with self.subTest(outcome=outcome.value), patch.object(
                self.store,
                "admit_or_return_existing",
                return_value=(
                    make_agent_execution_dispatch_admission_store_result(
                        outcome
                    )
                ),
            ):
                result = self.coordinator.admit(grant)
            self.assertIs(result.outcome, outcome)
            self.assertIs(
                result.retry_disposition,
                make_agent_execution_dispatch_admission_store_result(
                    outcome
                ).retry_disposition,
            )


if __name__ == "__main__":
    unittest.main()
