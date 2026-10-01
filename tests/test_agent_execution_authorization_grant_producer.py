"""Focused synthetic trust-boundary tests for AIO-050.

The fixtures in this module are deliberately process-local and in-memory.
They do not authenticate a real Human or policy principal, persist a Grant,
create an Admission, resolve a Tool, dispatch, or invoke anything.
"""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from inspect import Parameter, signature
import pickle
from threading import Barrier, Lock, Thread
import unittest
from unittest.mock import patch

import engineering_orchestration.agent_execution_authorization_grant_producer as subject
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_authorization_grant_producer import (
    AgentExecutionAuthorizationGrantAuditMaterial,
    AgentExecutionAuthorizationGrantLifetimePolicy,
    AgentExecutionAuthorizationGrantProducer,
    AgentExecutionAuthorizationGrantProductionOutcome,
    AgentExecutionAuthorizationGrantProductionResult,
    AgentExecutionAuthorizationGrantRetryDisposition,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainIdentity,
    AuthorizationDomainOperationLease,
    OwnedAuthorizationDomainSession,
    OwnedAuthorizationDomainSessionClosedError,
    OwnedAuthorizationDomainSessionLostError,
)


UTC = timezone.utc
NOW = datetime(2026, 9, 26, 10, 0, 0, tzinfo=UTC)
VALID_FROM = NOW - timedelta(minutes=5)
VALID_UNTIL = NOW + timedelta(minutes=5)
IDENTITY = AuthorizationDomainIdentity(
    authorization_domain_id="authorization-domain::synthetic",
    ledger_instance_id="ledger-instance::synthetic",
    domain_generation=7,
)
FIRST_ID_MATERIAL = bytes(range(32))
SECOND_ID_MATERIAL = bytes(reversed(range(32)))


EXPECTED_RETRY = {
    "issued": "no_retry_needed",
    "existing_exact_issuance": "no_retry_needed",
    "unauthenticated_principal": "retry_with_fresh_principal_and_authority",
    "identity_unavailable": "retry_after_identity_remediation",
    "issuer_disabled": "retry_after_issuer_reenable_with_fresh_authority",
    "not_entitled": "do_not_retry_same_request",
    "approval_missing": "retry_with_fresh_human_approval",
    "approval_subject_mismatch": "retry_with_fresh_human_approval",
    "policy_denied": "retry_with_fresh_policy_decision",
    "authority_proof_invalid": "retry_with_fresh_authority_decision",
    "invalid_run": "do_not_retry_same_request",
    "domain_not_owned": "retry_with_fresh_session_authority",
    "domain_mismatch": "retry_with_fresh_session_authority",
    "generation_mismatch": "retry_with_fresh_session_authority",
    "ownership_lost": "retry_with_fresh_session_authority",
    "producer_closed": "retry_with_new_run_and_fresh_session_authority",
    "run_already_issued": "do_not_retry_same_request",
    "run_identity_conflict": "retry_with_new_run_and_fresh_authority",
    "run_issuance_conflict": "retry_with_new_run_and_fresh_authority",
    "clock_failure": "retry_after_clock_remediation",
    "lifetime_invalid": "retry_with_fresh_authority_decision",
    "grant_id_generation_failure": "retry_after_internal_remediation",
    "grant_id_collision": "retry_after_internal_remediation",
    "integrity_failure": "retry_after_internal_remediation",
}


EXPECTED_RETRY_VALUES = {
    "no_retry_needed",
    "retry_with_fresh_principal_and_authority",
    "retry_after_identity_remediation",
    "retry_after_issuer_reenable_with_fresh_authority",
    "retry_with_fresh_human_approval",
    "retry_with_fresh_policy_decision",
    "retry_with_fresh_authority_decision",
    "retry_with_fresh_session_authority",
    "retry_with_new_run_and_fresh_authority",
    "retry_with_new_run_and_fresh_session_authority",
    "retry_after_clock_remediation",
    "retry_after_internal_remediation",
    "do_not_retry_same_request",
}


SCENARIO_TEST_MAP = {
    1: "ProducerSuccessTests.test_human_success_is_exact_and_published_after_clean_lease",
    2: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    3: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    4: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    5: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    6: "ProducerFailureTests.test_domain_ownership_generation_and_close_failures",
    7: "ProducerFailureTests.test_domain_ownership_generation_and_close_failures",
    8: "ProducerFailureTests.test_domain_ownership_generation_and_close_failures",
    9: "ProducerSuccessTests.test_policy_success_uses_policy_identity_and_provenance",
    10: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    11: "ProducerFailureTests.test_clock_windows_and_lifetime_fail_closed",
    12: "ProducerFailureTests.test_clock_windows_and_lifetime_fail_closed",
    13: "ProducerFailureTests.test_grant_id_entropy_collision_and_source_failures",
    14: "ProducerPresentationTests.test_close_and_restart_invalidate_presentations",
    15: "ProducerPresentationTests.test_port_rejects_raw_foreign_copied_and_integrity_conflicts",
    16: "ProducerPresentationTests.test_port_rejects_raw_foreign_copied_and_integrity_conflicts",
    17: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    18: "ProducerContractTests.test_locked_api_and_capabilities_are_guarded",
    19: "ProducerPresentationTests.test_disable_reenable_and_port_linearization",
    20: "ProducerPresentationTests.test_outer_gate_rejects_closed_or_fenced_before_port",
    21: "ProducerRegistryTests.test_concurrent_identical_requests_share_one_presentation",
    22: "ProducerRegistryTests.test_sequential_retry_and_run_conflicts",
    23: "ProducerRegistryTests.test_sequential_retry_and_run_conflicts",
    24: "ProducerRegistryTests.test_sequential_retry_and_run_conflicts",
    25: "ProducerRegistryTests.test_composition_rejects_second_producer",
    26: "ProducerPresentationTests.test_close_and_restart_invalidate_presentations",
    27: "ProducerFailureTests.test_principal_identity_entitlement_and_authority_failures",
    28: "ProducerPresentationTests.test_disable_reenable_and_port_linearization",
    29: "ProducerFailureTests.test_grant_id_entropy_collision_and_source_failures",
    30: "ProducerFailureTests.test_audit_construction_failure_is_unambiguous",
}


def contract(
    *,
    task_id: str = "AIO-050",
    resource: str = "synthetic/input.txt",
) -> AgentExecutionContract:
    """Build one synthetic declarative Contract without execution authority."""

    return AgentExecutionContract(
        task_id,
        "architecture-change",
        "implement",
        "software-engineer",
        "actor::synthetic",
        "runtime::synthetic",
        "option::synthetic",
        "environment::synthetic",
        "repository_file_read",
        resource,
        "critical",
    )


def run(
    run_id: str = "run::synthetic-one",
    *,
    resource: str = "synthetic/input.txt",
) -> AgentExecutionRun:
    """Build one synthetic Run without dispatch or invocation."""

    return AgentExecutionRun(run_id, contract(resource=resource))


class _NonCanonicalRunId(str):
    """String value whose nonexact type makes an otherwise equal Run invalid."""


class _NonCanonicalPolicyDecision(str):
    """Equal-looking string subclass that is not a canonical decision."""


class _EqualitySpoofingRunSubject:
    def __init__(self) -> None:
        self.comparison_calls = 0

    def __eq__(self, other: object) -> bool:
        del other
        self.comparison_calls += 1
        return True

    def __ne__(self, other: object) -> bool:
        del other
        self.comparison_calls += 1
        return False


class _SpoofingPolicyDecision:
    def __init__(self) -> None:
        self.comparison_calls = 0
        self.truth_calls = 0
        self.lower_calls = 0

    def __eq__(self, other: object) -> bool:
        del other
        self.comparison_calls += 1
        return True

    def __ne__(self, other: object) -> bool:
        del other
        self.comparison_calls += 1
        return False

    def __bool__(self) -> bool:
        self.truth_calls += 1
        return True

    def lower(self) -> str:
        self.lower_calls += 1
        return "allow"


class _IdentityAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid: object = True
        self.unavailable = False
        self.validation_calls = 0
        self._minter = None

    def current_epoch(self) -> object:
        if self.unavailable:
            raise RuntimeError("synthetic identity unavailable")
        return self.epoch

    def validate_authenticated_principal(self, principal: object) -> bool:
        del principal
        self.validation_calls += 1
        if self.unavailable:
            raise RuntimeError("synthetic identity unavailable")
        return self.valid  # type: ignore[return-value]

    def _bind_authenticated_issuer_principal_minter(
        self,
        minter: object,
    ) -> None:
        if self._minter is not None:
            raise RuntimeError("synthetic principal minter already bound")
        self._minter = minter

    def mint(
        self,
        *,
        issuer_kind: str,
        issuer_id: str,
        authentication_session_id: str,
        valid_from: datetime,
        valid_until: datetime,
    ) -> object:
        if self._minter is None:
            raise RuntimeError("synthetic principal minter is not bound")
        return self._minter.mint(
            issuer_kind=issuer_kind,
            issuer_id=issuer_id,
            authentication_session_id=authentication_session_id,
            valid_from=valid_from,
            valid_until=valid_until,
        )


class _HumanApprovalAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid: object = True
        self.validation_calls = 0
        self._minter = None

    def current_epoch(self) -> object:
        return self.epoch

    def validate_authenticated_human_approval(self, approval: object) -> bool:
        del approval
        self.validation_calls += 1
        return self.valid  # type: ignore[return-value]

    def _bind_authenticated_human_approval_minter(self, minter: object) -> None:
        if self._minter is not None:
            raise RuntimeError("synthetic Human approval minter already bound")
        self._minter = minter

    def mint(
        self,
        *,
        principal: object,
        run: AgentExecutionRun,
        approval_session_id: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None = None,
    ) -> object:
        if self._minter is None:
            raise RuntimeError("synthetic Human approval minter is not bound")
        return self._minter.mint(
            principal=principal,
            run=run,
            approval_session_id=approval_session_id,
            provenance_reference=provenance_reference,
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )


class _FatalBindingHumanApprovalAdapter(_HumanApprovalAdapter):
    def __init__(self, failure: BaseException) -> None:
        super().__init__()
        self.failure = failure

    def _bind_authenticated_human_approval_minter(self, minter: object) -> None:
        super()._bind_authenticated_human_approval_minter(minter)
        raise self.failure


class _PolicyDecisionAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid: object = True
        self.validation_calls = 0
        self._minter = None

    def current_epoch(self) -> object:
        return self.epoch

    def validate_authenticated_policy_decision(self, decision: object) -> bool:
        del decision
        self.validation_calls += 1
        return self.valid  # type: ignore[return-value]

    def _bind_authenticated_policy_decision_minter(self, minter: object) -> None:
        if self._minter is not None:
            raise RuntimeError("synthetic policy decision minter already bound")
        self._minter = minter

    def mint(
        self,
        *,
        principal: object,
        run: AgentExecutionRun,
        decision: str,
        policy_revision: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None = None,
    ) -> object:
        if self._minter is None:
            raise RuntimeError("synthetic policy decision minter is not bound")
        return self._minter.mint(
            principal=principal,
            run=run,
            decision=decision,
            policy_revision=policy_revision,
            provenance_reference=provenance_reference,
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )


class _IssuerStateAuthority:
    def __init__(self) -> None:
        self.enabled = True
        self.epoch = object()
        self.unavailable = False
        self.observations = 0
        self._lock = Lock()

    def observe_issuer_state(
        self,
        *,
        issuer_kind: str,
        issuer_id: str,
    ) -> tuple[bool, object]:
        del issuer_kind, issuer_id
        with self._lock:
            self.observations += 1
            if self.unavailable:
                raise RuntimeError("synthetic issuer state unavailable")
            return self.enabled, self.epoch

    def disable(self) -> None:
        with self._lock:
            self.enabled = False
            self.epoch = object()

    def enable(self) -> None:
        with self._lock:
            self.enabled = True
            self.epoch = object()


class _EntitlementPolicy:
    def __init__(self) -> None:
        self.allowed: object = True
        self.error: BaseException | None = None
        self.calls = 0

    def is_entitled(
        self,
        *,
        run: AgentExecutionRun,
        domain_identity: AuthorizationDomainIdentity,
        issuer_kind: str,
        issuer_id: str,
    ) -> bool:
        del run, domain_identity, issuer_kind, issuer_id
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.allowed  # type: ignore[return-value]


class _Clock:
    def __init__(self, value: object = NOW) -> None:
        self.value = value
        self.error: BaseException | None = None
        self.calls = 0
        self._lock = Lock()

    def now_utc(self) -> datetime:
        with self._lock:
            self.calls += 1
            if self.error is not None:
                raise self.error
            return self.value  # type: ignore[return-value]


class _GrantIdSource:
    def __init__(self, values: list[object] | None = None) -> None:
        self.values = list(values or [FIRST_ID_MATERIAL])
        self.requested_lengths: list[int] = []
        self._lock = Lock()

    def random_bytes(self, length: int) -> bytes:
        with self._lock:
            self.requested_lengths.append(length)
            if self.values:
                value = self.values.pop(0)
            else:
                call = len(self.requested_lengths)
                value = bytes((call + offset) % 256 for offset in range(length))
            if isinstance(value, BaseException):
                raise value
            return value  # type: ignore[return-value]


class _SyntheticOperationLease:
    def __init__(self, session: _SyntheticOwnedSession) -> None:
        self._session = session
        self._entered = False

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        value = self._session.lease_identity
        if value is None:
            value = self._session.identity
        return value  # type: ignore[return-value]

    def __enter__(self) -> _SyntheticOperationLease:
        session = self._session
        session._operation_lock.acquire()
        try:
            if session.closed:
                raise OwnedAuthorizationDomainSessionClosedError(
                    "synthetic session closed"
                )
            if session.lost:
                raise OwnedAuthorizationDomainSessionLostError(
                    "synthetic session lost"
                )
            self._entered = True
            session.active_operations += 1
            session.entered_operations += 1
            return self
        except BaseException:
            session._operation_lock.release()
            raise

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object | None,
    ) -> None:
        del exception_type, exception, traceback
        if not self._entered:
            return
        session = self._session
        post_error: BaseException | None = None
        try:
            if session.on_exit is not None:
                session.on_exit()
            post_error = session.exit_error
            if post_error is None:
                session.clean_exits += 1
        finally:
            session.active_operations -= 1
            session.exited_operations += 1
            self._entered = False
            session._operation_lock.release()
        if post_error is not None:
            raise post_error


class _SyntheticOwnedSession(OwnedAuthorizationDomainSession):
    __slots__ = (
        "_initial_identity",
        "observed_identity",
        "lease_identity",
        "closed",
        "lost",
        "return_nonlease",
        "operation_error",
        "exit_error",
        "on_exit",
        "entered_operations",
        "exited_operations",
        "clean_exits",
        "active_operations",
        "port_calls",
        "load_calls",
        "revoke_calls",
        "_port",
        "_operation_lock",
    )

    def __init__(self, identity: AuthorizationDomainIdentity = IDENTITY) -> None:
        self._initial_identity = identity
        self.observed_identity: object = identity
        self.lease_identity: object | None = None
        self.closed = False
        self.lost = False
        self.return_nonlease = False
        self.operation_error: BaseException | None = None
        self.exit_error: BaseException | None = None
        self.on_exit = None
        self.entered_operations = 0
        self.exited_operations = 0
        self.clean_exits = 0
        self.active_operations = 0
        self.port_calls = 0
        self.load_calls = 0
        self.revoke_calls = 0
        self._port = None
        self._operation_lock = Lock()

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return self.observed_identity  # type: ignore[return-value]

    def operation(self) -> AuthorizationDomainOperationLease:
        if self.operation_error is not None:
            raise self.operation_error
        if self.return_nonlease:
            return object()  # type: ignore[return-value]
        return _SyntheticOperationLease(self)

    def install_synthetic_port(self, port: object) -> None:
        self._port = port

    def authenticate_under_outer_gate(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        """Mimic only the owned coordinator's outer gate and port call."""

        with self.operation():
            self.port_calls += 1
            if self._port is None:
                raise AssertionError("synthetic authentication port not installed")
            return self._port.authenticate_grant(presented_grant)

    def admit(self, presented_grant: object) -> object:
        return self.authenticate_under_outer_gate(presented_grant)

    def load_authoritative_admission(self, presented_grant: object) -> object:
        del presented_grant
        self.load_calls += 1
        raise AssertionError("AIO-050 tests must not load an Admission")

    def revoke(self, presented_grant: object) -> object:
        del presented_grant
        self.revoke_calls += 1
        raise AssertionError("AIO-050 tests must not revoke a Grant")

    def close(self) -> None:
        self.closed = True

    def fence(self) -> None:
        self.lost = True


class _Harness:
    def __init__(
        self,
        *,
        identity: AuthorizationDomainIdentity = IDENTITY,
        lifetime_policy: AgentExecutionAuthorizationGrantLifetimePolicy | None = None,
        clock: _Clock | None = None,
        grant_id_source: _GrantIdSource | None = None,
        configure_human: bool = True,
        configure_policy: bool = True,
    ) -> None:
        self.session = _SyntheticOwnedSession(identity)
        self.identity_adapter = _IdentityAdapter()
        self.human_adapter = _HumanApprovalAdapter()
        self.policy_adapter = _PolicyDecisionAdapter()
        self.issuer_state = _IssuerStateAuthority()
        self.entitlement = _EntitlementPolicy()
        self.lifetime_policy = lifetime_policy or (
            AgentExecutionAuthorizationGrantLifetimePolicy(
                default_lifetime=timedelta(minutes=2),
                maximum_lifetime=timedelta(minutes=10),
                revision="lifetime-policy::synthetic-v1",
            )
        )
        self.clock = clock or _Clock()
        self.grant_id_source = grant_id_source or _GrantIdSource()
        self.binding = subject._compose_agent_execution_authorization_grant_producer(
            owned_session=self.session,
            identity_adapter=self.identity_adapter,
            human_approval_adapter=(
                self.human_adapter if configure_human else None
            ),
            policy_decision_adapter=(
                self.policy_adapter if configure_policy else None
            ),
            issuer_state_authority=self.issuer_state,
            issuer_entitlement_policy=self.entitlement,
            lifetime_policy=self.lifetime_policy,
            utc_clock=self.clock,
            grant_id_source=self.grant_id_source,
        )
        self.session.install_synthetic_port(self.binding.grant_authentication)

    @property
    def producer(self) -> AgentExecutionAuthorizationGrantProducer:
        return self.binding.producer

    def principal(
        self,
        issuer_kind: str = "human",
        *,
        valid_from: datetime = VALID_FROM,
        valid_until: datetime = VALID_UNTIL,
    ) -> object:
        issuer_id = (
            "human::synthetic-reviewer"
            if issuer_kind == "human"
            else "policy::synthetic-release"
        )
        return self.identity_adapter.mint(
            issuer_kind=issuer_kind,
            issuer_id=issuer_id,
            authentication_session_id="authentication-session::synthetic",
            valid_from=valid_from,
            valid_until=valid_until,
        )

    def human_proof(
        self,
        bound_run: AgentExecutionRun,
        principal: object,
        *,
        valid_from: datetime = VALID_FROM,
        valid_until: datetime = VALID_UNTIL,
        requested_lifetime: timedelta | None = None,
    ) -> object:
        return self.human_adapter.mint(
            principal=principal,
            run=bound_run,
            approval_session_id="approval-session::synthetic",
            provenance_reference="approval::synthetic",
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )

    def policy_proof(
        self,
        bound_run: AgentExecutionRun,
        principal: object,
        *,
        decision: str = "allow",
        valid_from: datetime = VALID_FROM,
        valid_until: datetime = VALID_UNTIL,
        requested_lifetime: timedelta | None = None,
    ) -> object:
        return self.policy_adapter.mint(
            principal=principal,
            run=bound_run,
            decision=decision,
            policy_revision="policy::synthetic-v1",
            provenance_reference="policy-decision::synthetic",
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )

    def produce(
        self,
        bound_run: object,
        principal: object,
        proof: object,
    ) -> AgentExecutionAuthorizationGrantProductionResult:
        return self.producer.produce(
            run=bound_run,  # type: ignore[arg-type]
            authenticated_principal=principal,  # type: ignore[arg-type]
            authority_proof=proof,  # type: ignore[arg-type]
        )

    def compose_again(self) -> object:
        return subject._compose_agent_execution_authorization_grant_producer(
            owned_session=self.session,
            identity_adapter=self.identity_adapter,
            human_approval_adapter=self.human_adapter,
            policy_decision_adapter=self.policy_adapter,
            issuer_state_authority=self.issuer_state,
            issuer_entitlement_policy=self.entitlement,
            lifetime_policy=self.lifetime_policy,
            utc_clock=self.clock,
            grant_id_source=self.grant_id_source,
        )


class _ProducerAssertions(unittest.TestCase):
    def assert_outcome(
        self,
        result: AgentExecutionAuthorizationGrantProductionResult,
        outcome: str,
    ) -> None:
        self.assertIs(type(result), AgentExecutionAuthorizationGrantProductionResult)
        self.assertEqual(result.outcome.value, outcome)
        self.assertEqual(result.retry_disposition.value, EXPECTED_RETRY[outcome])
        self.assertEqual(result.audit_material.outcome, result.outcome)
        self.assertEqual(
            result.audit_material.retry_disposition,
            result.retry_disposition,
        )
        if outcome in {"issued", "existing_exact_issuance"}:
            self.assertIs(
                type(result.presentation),
                subject.IssuedAgentExecutionAuthorizationGrant,
            )
        else:
            self.assertIsNone(result.presentation)

    def exact_human_request(
        self,
        harness: _Harness,
        bound_run: AgentExecutionRun | None = None,
        *,
        requested_lifetime: timedelta | None = None,
    ) -> tuple[AgentExecutionRun, object, object]:
        exact_run = bound_run or run()
        principal = harness.principal("human")
        proof = harness.human_proof(
            exact_run,
            principal,
            requested_lifetime=requested_lifetime,
        )
        return exact_run, principal, proof


class ProducerContractTests(_ProducerAssertions):
    def test_closed_vocabulary_mapping_and_result_shapes(self) -> None:
        outcomes = {
            value.value for value in AgentExecutionAuthorizationGrantProductionOutcome
        }
        retries = {
            value.value for value in AgentExecutionAuthorizationGrantRetryDisposition
        }
        self.assertEqual(outcomes, set(EXPECTED_RETRY))
        self.assertEqual(len(outcomes), 24)
        self.assertEqual(retries, EXPECTED_RETRY_VALUES)
        self.assertEqual(len(retries), 13)
        self.assertEqual(
            {
                outcome.value: retry.value
                for outcome, retry in subject._RETRY_FOR_OUTCOME.items()
            },
            EXPECTED_RETRY,
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionAuthorizationGrantProductionResult)],
            ["outcome", "retry_disposition", "presentation", "audit_material"],
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionAuthorizationGrantAuditMaterial)],
            [
                "outcome",
                "retry_disposition",
                "issuer_kind",
                "issuer_id",
                "authorization_domain_id",
                "ledger_instance_id",
                "domain_generation",
                "run_id",
                "run_subject_correlation",
                "grant_id",
                "provenance_reference",
                "issued_at",
                "expires_at",
                "lifetime_policy_revision",
            ],
        )

        harness = _Harness()
        port_parameters = signature(
            type(harness.binding.grant_authentication).authenticate_grant
        ).parameters
        self.assertEqual(tuple(port_parameters), ("self", "presented_grant"))
        for legacy_binding_minter in (
            "_mint_authenticated_issuer_principal",
            "_mint_authenticated_human_approval",
            "_mint_authenticated_policy_decision",
        ):
            self.assertFalse(hasattr(harness.binding, legacy_binding_minter))
        adapter_minters = (
            harness.identity_adapter._minter,
            harness.human_adapter._minter,
            harness.policy_adapter._minter,
        )
        self.assertTrue(all(minter is not None for minter in adapter_minters))
        for minter in adapter_minters:
            with self.subTest(minter=type(minter).__name__):
                with self.assertRaises(TypeError):
                    copy.copy(minter)
                with self.assertRaises(TypeError):
                    pickle.dumps(minter)

        exact_run, principal, proof = self.exact_human_request(harness)
        result = harness.produce(exact_run, principal, proof)
        with self.assertRaises(FrozenInstanceError):
            result.outcome = (  # type: ignore[misc]
                AgentExecutionAuthorizationGrantProductionOutcome.INTEGRITY_FAILURE
            )
        with self.assertRaises(FrozenInstanceError):
            result.audit_material.run_id = "run::changed"  # type: ignore[misc]
        self.assertFalse(hasattr(result, "grant"))
        self.assertFalse(hasattr(result, "diagnostic"))
        self.assertFalse(hasattr(result, "retry"))

    def test_locked_api_and_capabilities_are_guarded(self) -> None:
        produce_parameters = signature(
            AgentExecutionAuthorizationGrantProducer.produce
        ).parameters
        self.assertEqual(
            tuple(produce_parameters),
            ("self", "run", "authenticated_principal", "authority_proof"),
        )
        self.assertTrue(
            all(
                produce_parameters[name].kind is Parameter.KEYWORD_ONLY
                for name in ("run", "authenticated_principal", "authority_proof")
            )
        )
        self.assertEqual(
            tuple(signature(AgentExecutionAuthorizationGrantProducer.close).parameters),
            ("self",),
        )
        compose_parameters = signature(
            subject._compose_agent_execution_authorization_grant_producer
        ).parameters
        self.assertEqual(
            tuple(compose_parameters),
            (
                "owned_session",
                "identity_adapter",
                "human_approval_adapter",
                "policy_decision_adapter",
                "issuer_state_authority",
                "issuer_entitlement_policy",
                "lifetime_policy",
                "utc_clock",
                "grant_id_source",
            ),
        )
        self.assertTrue(
            all(value.kind is Parameter.KEYWORD_ONLY for value in compose_parameters.values())
        )

        for capability_type in (
            subject.AuthenticatedIssuerPrincipal,
            subject.AuthenticatedHumanApproval,
            subject.AuthenticatedPolicyDecision,
            subject.IssuedAgentExecutionAuthorizationGrant,
            AgentExecutionAuthorizationGrantProducer,
            subject._AgentExecutionAuthorizationGrantProducerBinding,
        ):
            with self.subTest(capability=capability_type.__name__):
                with self.assertRaises(TypeError):
                    capability_type()

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        result = harness.produce(exact_run, principal, proof)
        capabilities = (principal, proof, result.presentation)
        for capability in capabilities:
            with self.subTest(capability=type(capability).__name__):
                with self.assertRaises(TypeError):
                    copy.copy(capability)
                with self.assertRaises(TypeError):
                    copy.deepcopy(capability)
                with self.assertRaises(TypeError):
                    pickle.dumps(capability)
                with self.assertRaises(AttributeError):
                    capability.synthetic = "changed"  # type: ignore[attr-defined]

        for private_name in (
            "AuthenticatedIssuerPrincipal",
            "AuthenticatedHumanApproval",
            "AuthenticatedPolicyDecision",
            "IssuedAgentExecutionAuthorizationGrant",
            "_compose_agent_execution_authorization_grant_producer",
        ):
            self.assertNotIn(private_name, subject.__all__)

    def test_scenario_map_covers_exactly_thirty_without_dispatch(self) -> None:
        self.assertEqual(tuple(SCENARIO_TEST_MAP), tuple(range(1, 31)))
        for scenario, reference in SCENARIO_TEST_MAP.items():
            with self.subTest(scenario=scenario):
                class_name, method_name = reference.split(".", 1)
                test_class = globals()[class_name]
                self.assertTrue(callable(getattr(test_class, method_name, None)))
        public_names = {name.lower() for name in subject.__all__}
        self.assertTrue(
            all(
                fragment not in name
                for name in public_names
                for fragment in ("admission", "dispatch", "invoke", "tool")
            )
        )


class ProducerSuccessTests(_ProducerAssertions):
    def test_human_success_is_exact_and_published_after_clean_lease(self) -> None:
        source = _GrantIdSource([FIRST_ID_MATERIAL])
        harness = _Harness(grant_id_source=source)
        exact_run = run()
        principal = harness.principal(
            "human",
            valid_from=NOW,
            valid_until=NOW + timedelta(minutes=3),
        )
        proof = harness.human_proof(
            exact_run,
            principal,
            valid_from=NOW,
            valid_until=NOW + timedelta(minutes=1),
            requested_lifetime=timedelta(minutes=2),
        )
        observed_during_exit: list[tuple[int, int]] = []

        def observe_prepublication() -> None:
            observed_during_exit.append(
                (
                    len(harness.binding._state.presentations),
                    harness.session.active_operations,
                )
            )

        harness.session.on_exit = observe_prepublication
        result = harness.produce(exact_run, principal, proof)
        harness.session.on_exit = None

        self.assert_outcome(result, "issued")
        self.assertEqual(observed_during_exit, [(0, 1)])
        self.assertEqual(harness.session.active_operations, 0)
        self.assertEqual(harness.session.clean_exits, 2)
        self.assertEqual(harness.clock.calls, 1)
        self.assertEqual(source.requested_lengths, [32])

        presentation = result.presentation
        assert presentation is not None
        grant = harness.session.authenticate_under_outer_gate(presentation)
        self.assertIs(type(grant), AgentExecutionAuthorizationGrant)
        assert grant is not None
        self.assertIs(grant.run, exact_run)
        self.assertEqual(
            [field.name for field in fields(grant)],
            [
                "grant_id",
                "run",
                "authorization_domain_id",
                "issuer_kind",
                "issuer_id",
                "provenance_reference",
                "issued_at",
                "expires_at",
            ],
        )
        self.assertEqual(grant.grant_id, FIRST_ID_MATERIAL.hex())
        self.assertEqual(len(grant.grant_id), 64)
        self.assertNotIn("-", grant.grant_id)
        self.assertEqual(grant.authorization_domain_id, IDENTITY.authorization_domain_id)
        self.assertEqual(grant.issuer_kind, "human")
        self.assertEqual(grant.issuer_id, "human::synthetic-reviewer")
        self.assertEqual(grant.provenance_reference, "approval::synthetic")
        self.assertEqual(grant.issued_at, "2026-09-26T10:00:00Z")
        self.assertEqual(grant.expires_at, "2026-09-26T10:02:00Z")

        audit = result.audit_material
        self.assertEqual(audit.authorization_domain_id, IDENTITY.authorization_domain_id)
        self.assertEqual(audit.ledger_instance_id, IDENTITY.ledger_instance_id)
        self.assertEqual(audit.domain_generation, IDENTITY.domain_generation)
        self.assertEqual(audit.run_id, exact_run.run_id)
        self.assertTrue((audit.run_subject_correlation or "").startswith("sha256:"))
        self.assertEqual(audit.grant_id, grant.grant_id)
        self.assertEqual(audit.provenance_reference, grant.provenance_reference)
        self.assertEqual(audit.issued_at, grant.issued_at)
        self.assertEqual(audit.expires_at, grant.expires_at)
        self.assertEqual(
            audit.lifetime_policy_revision,
            "lifetime-policy::synthetic-v1",
        )
        rendered = repr(result)
        self.assertNotIn("authentication-session::synthetic", rendered)
        self.assertNotIn("approval-session::synthetic", rendered)
        self.assertEqual(harness.session.load_calls, 0)
        self.assertEqual(harness.session.revoke_calls, 0)

    def test_policy_success_uses_policy_identity_and_provenance(self) -> None:
        harness = _Harness()
        exact_run = run("run::policy")
        principal = harness.principal("policy")
        proof = harness.policy_proof(exact_run, principal, decision="allow")

        result = harness.produce(exact_run, principal, proof)

        self.assert_outcome(result, "issued")
        assert result.presentation is not None
        grant = harness.session.authenticate_under_outer_gate(result.presentation)
        assert grant is not None
        self.assertEqual(grant.issuer_kind, "policy")
        self.assertEqual(grant.issuer_id, "policy::synthetic-release")
        self.assertEqual(grant.provenance_reference, "policy-decision::synthetic")
        self.assertEqual(harness.human_adapter.validation_calls, 0)
        self.assertEqual(harness.policy_adapter.validation_calls, 1)

    def test_policy_decision_minting_requires_exact_canonical_values(self) -> None:
        for decision, expected_outcome in (
            ("allow", "issued"),
            ("deny", "policy_denied"),
        ):
            with self.subTest(decision=decision):
                harness = _Harness()
                exact_run = run(f"run::policy-decision-{decision}")
                principal = harness.principal("policy")
                proof = harness.policy_proof(
                    exact_run,
                    principal,
                    decision=decision,
                )
                self.assert_outcome(
                    harness.produce(exact_run, principal, proof),
                    expected_outcome,
                )

        spoofing_decision = _SpoofingPolicyDecision()
        harness = _Harness()
        principal = harness.principal("policy")
        malformed_decisions = (
            "ALLOW",
            "Allow",
            "yes",
            "",
            None,
            _NonCanonicalPolicyDecision("allow"),
            spoofing_decision,
        )
        for index, decision in enumerate(malformed_decisions):
            with self.subTest(malformed_decision=repr(decision)):
                with self.assertRaises(ValueError):
                    harness.policy_proof(
                        run(f"run::policy-decision-malformed-{index}"),
                        principal,
                        decision=decision,  # type: ignore[arg-type]
                    )
        self.assertEqual(harness.binding._state.authority_proofs, {})
        self.assertEqual(spoofing_decision.comparison_calls, 0)
        self.assertEqual(spoofing_decision.truth_calls, 0)
        self.assertEqual(spoofing_decision.lower_calls, 0)

    def test_policy_decision_verification_requires_exact_allow(self) -> None:
        spoofing_decision = _SpoofingPolicyDecision()
        malformed_decisions = (
            "ALLOW",
            "Allow",
            "yes",
            "",
            None,
            _NonCanonicalPolicyDecision("allow"),
            spoofing_decision,
        )
        for index, decision in enumerate(malformed_decisions):
            with self.subTest(malformed_decision=repr(decision)):
                harness = _Harness()
                exact_run = run(f"run::policy-decision-tampered-{index}")
                principal = harness.principal("policy")
                proof = harness.policy_proof(exact_run, principal)
                object.__setattr__(proof, "_decision", decision)
                self.assert_outcome(
                    harness.produce(exact_run, principal, proof),
                    "authority_proof_invalid",
                )
                self.assertEqual(harness.clock.calls, 0)
                self.assertEqual(harness.policy_adapter.validation_calls, 0)
                self.assertEqual(harness.grant_id_source.requested_lengths, [])
        self.assertEqual(spoofing_decision.comparison_calls, 0)
        self.assertEqual(spoofing_decision.truth_calls, 0)
        self.assertEqual(spoofing_decision.lower_calls, 0)


class ProducerFailureTests(_ProducerAssertions):
    def test_principal_identity_entitlement_and_authority_failures(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        result = harness.produce(exact_run, object(), proof)
        self.assert_outcome(result, "unauthenticated_principal")
        self.assertEqual(harness.clock.calls, 0)

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.identity_adapter.unavailable = True
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "identity_unavailable",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.identity_adapter.epoch = object()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "unauthenticated_principal",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.issuer_state.disable()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "issuer_disabled",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.issuer_state.unavailable = True
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "identity_unavailable",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.entitlement.allowed = False
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "not_entitled",
        )

        harness = _Harness()
        exact_run = run("run::approval-missing")
        principal = harness.principal("human")
        result = harness.produce(exact_run, principal, None)
        self.assert_outcome(result, "approval_missing")
        self.assertEqual(harness.clock.calls, 0)

        harness = _Harness()
        approved_run = run("run::approved")
        changed_run = run("run::changed")
        principal = harness.principal("human")
        proof = harness.human_proof(approved_run, principal)
        self.assert_outcome(
            harness.produce(changed_run, principal, proof),
            "approval_subject_mismatch",
        )

        harness = _Harness()
        exact_run = run("run::policy-denied")
        principal = harness.principal("policy")
        proof = harness.policy_proof(exact_run, principal, decision="deny")
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "policy_denied",
        )

        harness = _Harness()
        exact_run = run("run::invalid-authority")
        principal = harness.principal("human")
        for invalid_proof in (object(), "approved", True):
            with self.subTest(invalid_proof=invalid_proof):
                self.assert_outcome(
                    harness.produce(exact_run, principal, invalid_proof),
                    "authority_proof_invalid",
                )

        harness = _Harness()
        exact_run = run("run::stale-authority")
        principal = harness.principal("human")
        proof = harness.human_proof(exact_run, principal)
        harness.human_adapter.epoch = object()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "authority_proof_invalid",
        )

        harness = _Harness()
        exact_run = run("run::policy-missing")
        principal = harness.principal("policy")
        self.assert_outcome(
            harness.produce(exact_run, principal, None),
            "authority_proof_invalid",
        )

        first = _Harness()
        second = _Harness()
        exact_run = run("run::foreign-proof")
        first_principal = first.principal("human")
        second_principal = second.principal("human")
        foreign_proof = second.human_proof(exact_run, second_principal)
        self.assert_outcome(
            first.produce(exact_run, first_principal, foreign_proof),
            "authority_proof_invalid",
        )

        harness = _Harness()
        principal = harness.principal("human")
        proof = harness.human_proof(run("run::valid"), principal)
        self.assert_outcome(
            harness.produce(object(), principal, proof),
            "invalid_run",
        )

    def test_human_authority_subject_requires_exact_intrinsic_run(self) -> None:
        harness = _Harness()
        exact_run = run("run::human-subject-validation")
        principal = harness.principal("human")
        spoofing_subject = _EqualitySpoofingRunSubject()
        invalid_subject = AgentExecutionRun(
            _NonCanonicalRunId(exact_run.run_id),
            exact_run.contract,
        )
        self.assertEqual(invalid_subject, exact_run)

        with self.assertRaises(TypeError):
            harness.human_proof(object(), principal)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            harness.human_proof(  # type: ignore[arg-type]
                spoofing_subject,
                principal,
            )
        with self.assertRaises(ValueError):
            harness.human_proof(invalid_subject, principal)
        self.assertEqual(harness.binding._state.authority_proofs, {})
        self.assertEqual(spoofing_subject.comparison_calls, 0)

        proof = harness.human_proof(exact_run, principal)
        for malformed_subject in (spoofing_subject, invalid_subject):
            with self.subTest(malformed_subject=type(malformed_subject).__name__):
                object.__setattr__(proof, "_run", malformed_subject)
                self.assert_outcome(
                    harness.produce(exact_run, principal, proof),
                    "authority_proof_invalid",
                )
                self.assertEqual(harness.clock.calls, 0)
                self.assertEqual(harness.grant_id_source.requested_lengths, [])
        self.assertEqual(spoofing_subject.comparison_calls, 0)

        object.__setattr__(proof, "_run", exact_run)
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "issued",
        )

    def test_policy_authority_subject_requires_exact_intrinsic_run(self) -> None:
        harness = _Harness()
        exact_run = run("run::policy-subject-validation")
        principal = harness.principal("policy")
        spoofing_subject = _EqualitySpoofingRunSubject()
        invalid_subject = AgentExecutionRun(
            _NonCanonicalRunId(exact_run.run_id),
            exact_run.contract,
        )
        self.assertEqual(invalid_subject, exact_run)

        with self.assertRaises(TypeError):
            harness.policy_proof(object(), principal)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            harness.policy_proof(  # type: ignore[arg-type]
                spoofing_subject,
                principal,
            )
        with self.assertRaises(ValueError):
            harness.policy_proof(invalid_subject, principal)
        self.assertEqual(harness.binding._state.authority_proofs, {})
        self.assertEqual(spoofing_subject.comparison_calls, 0)

        proof = harness.policy_proof(exact_run, principal)
        for malformed_subject in (spoofing_subject, invalid_subject):
            with self.subTest(malformed_subject=type(malformed_subject).__name__):
                object.__setattr__(proof, "_run", malformed_subject)
                self.assert_outcome(
                    harness.produce(exact_run, principal, proof),
                    "authority_proof_invalid",
                )
                self.assertEqual(harness.clock.calls, 0)
                self.assertEqual(harness.grant_id_source.requested_lengths, [])
        self.assertEqual(spoofing_subject.comparison_calls, 0)

        object.__setattr__(proof, "_run", exact_run)
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "issued",
        )

    def test_domain_ownership_generation_and_close_failures(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.observed_identity = AuthorizationDomainIdentity(
            "authorization-domain::other",
            IDENTITY.ledger_instance_id,
            IDENTITY.domain_generation,
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "domain_mismatch",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.observed_identity = AuthorizationDomainIdentity(
            IDENTITY.authorization_domain_id,
            IDENTITY.ledger_instance_id,
            IDENTITY.domain_generation + 1,
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "generation_mismatch",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.return_nonlease = True
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "domain_not_owned",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.close()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "domain_not_owned",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.fence()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "ownership_lost",
        )

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.producer.close()
        harness.producer.close()
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "producer_closed",
        )

    def test_clock_windows_and_lifetime_fail_closed(self) -> None:
        harness = _Harness()
        exact_run = run("run::invalid-principal-window")
        principal = harness.principal(
            "human",
            valid_from=NOW,
            valid_until=NOW,
        )
        proof = harness.human_proof(exact_run, principal)
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "unauthenticated_principal",
        )
        self.assertEqual(harness.clock.calls, 0)

        harness = _Harness()
        exact_run = run("run::invalid-proof-window")
        principal = harness.principal("human")
        proof = harness.human_proof(
            exact_run,
            principal,
            valid_from=NOW,
            valid_until=NOW,
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "authority_proof_invalid",
        )
        self.assertEqual(harness.clock.calls, 0)

        harness = _Harness()
        exact_run = run("run::inclusive-window")
        principal = harness.principal(
            "human",
            valid_from=NOW,
            valid_until=NOW + timedelta(seconds=1),
        )
        proof = harness.human_proof(
            exact_run,
            principal,
            valid_from=NOW,
            valid_until=NOW + timedelta(seconds=1),
        )
        self.assert_outcome(harness.produce(exact_run, principal, proof), "issued")
        self.assertEqual(harness.clock.calls, 1)

        equivalent_utc = timezone(timedelta(0), name="Synthetic UTC")
        harness = _Harness(clock=_Clock(NOW.astimezone(equivalent_utc)))
        exact_run, principal, proof = self.exact_human_request(
            harness,
            run("run::equivalent-utc"),
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "issued",
        )

        harness = _Harness()
        exact_run = run("run::principal-expired")
        principal = harness.principal(
            "human",
            valid_from=NOW - timedelta(minutes=1),
            valid_until=NOW,
        )
        proof = harness.human_proof(exact_run, principal)
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "unauthenticated_principal",
        )
        self.assertEqual(harness.clock.calls, 1)

        harness = _Harness()
        exact_run = run("run::proof-expired")
        principal = harness.principal("human")
        proof = harness.human_proof(
            exact_run,
            principal,
            valid_from=NOW - timedelta(minutes=1),
            valid_until=NOW,
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "authority_proof_invalid",
        )
        self.assertEqual(harness.clock.calls, 1)

        for clock_value in (
            datetime(2026, 9, 26, 10, 0, 0),
            datetime(
                2026,
                9,
                26,
                12,
                0,
                0,
                tzinfo=timezone(timedelta(hours=2)),
            ),
            object(),
        ):
            harness = _Harness(clock=_Clock(clock_value))
            exact_run, principal, proof = self.exact_human_request(harness)
            self.assert_outcome(
                harness.produce(exact_run, principal, proof),
                "clock_failure",
            )
            self.assertEqual(harness.clock.calls, 1)

        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.clock.error = RuntimeError("synthetic clock failure")
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "clock_failure",
        )

        for requested in (timedelta(0), timedelta(seconds=-1), timedelta(hours=1)):
            harness = _Harness()
            exact_run, principal, proof = self.exact_human_request(
                harness,
                requested_lifetime=requested,
            )
            with self.subTest(requested=requested):
                self.assert_outcome(
                    harness.produce(exact_run, principal, proof),
                    "lifetime_invalid",
                )

        invalid_policy = AgentExecutionAuthorizationGrantLifetimePolicy(
            default_lifetime=timedelta(minutes=11),
            maximum_lifetime=timedelta(minutes=10),
            revision="lifetime-policy::invalid",
        )
        harness = _Harness(lifetime_policy=invalid_policy)
        exact_run, principal, proof = self.exact_human_request(harness)
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "lifetime_invalid",
        )

        overflow_policy = AgentExecutionAuthorizationGrantLifetimePolicy(
            default_lifetime=timedelta(minutes=2),
            maximum_lifetime=timedelta(minutes=10),
            revision="lifetime-policy::overflow",
        )
        overflow_clock = _Clock(datetime(9999, 12, 31, 23, 59, 59, tzinfo=UTC))
        harness = _Harness(
            lifetime_policy=overflow_policy,
            clock=overflow_clock,
        )
        exact_run = run("run::overflow")
        principal = harness.principal(
            "human",
            valid_from=datetime(9999, 12, 31, 23, 59, 58, tzinfo=UTC),
            valid_until=datetime.max.replace(tzinfo=UTC),
        )
        proof = harness.human_proof(
            exact_run,
            principal,
            valid_from=datetime(9999, 12, 31, 23, 59, 58, tzinfo=UTC),
            valid_until=datetime.max.replace(tzinfo=UTC),
        )
        self.assert_outcome(
            harness.produce(exact_run, principal, proof),
            "lifetime_invalid",
        )

    def test_grant_id_entropy_collision_and_source_failures(self) -> None:
        repeated = b"A" * 32
        source = _GrantIdSource(
            [repeated, repeated, repeated, repeated, repeated, SECOND_ID_MATERIAL]
        )
        harness = _Harness(grant_id_source=source)

        first_run, first_principal, first_proof = self.exact_human_request(
            harness,
            run("run::id-first"),
        )
        first = harness.produce(first_run, first_principal, first_proof)
        self.assert_outcome(first, "issued")

        second_run, second_principal, second_proof = self.exact_human_request(
            harness,
            run("run::id-second"),
        )
        collision = harness.produce(second_run, second_principal, second_proof)
        self.assert_outcome(collision, "grant_id_collision")
        self.assertEqual(source.requested_lengths, [32, 32, 32, 32, 32])

        recovered = harness.produce(second_run, second_principal, second_proof)
        self.assert_outcome(recovered, "issued")
        self.assertEqual(source.requested_lengths, [32, 32, 32, 32, 32, 32])
        assert first.presentation is not None
        assert recovered.presentation is not None
        first_grant = harness.session.authenticate_under_outer_gate(first.presentation)
        second_grant = harness.session.authenticate_under_outer_gate(
            recovered.presentation
        )
        assert first_grant is not None and second_grant is not None
        self.assertNotEqual(first_grant.grant_id, second_grant.grant_id)

        for invalid_material in (
            b"short",
            bytearray(32),
            RuntimeError("synthetic CSPRNG failure"),
        ):
            harness = _Harness(
                grant_id_source=_GrantIdSource([invalid_material])
            )
            exact_run, principal, proof = self.exact_human_request(harness)
            with self.subTest(material=type(invalid_material).__name__):
                result = harness.produce(exact_run, principal, proof)
                self.assert_outcome(result, "grant_id_generation_failure")
                self.assertEqual(harness.grant_id_source.requested_lengths, [32])

    def test_audit_construction_failure_is_unambiguous(self) -> None:
        source = _GrantIdSource([FIRST_ID_MATERIAL, SECOND_ID_MATERIAL])
        harness = _Harness(grant_id_source=source)
        exact_run, principal, proof = self.exact_human_request(harness)

        with patch.object(
            subject,
            "_build_audit_material",
            side_effect=RuntimeError("synthetic audit construction failure"),
        ):
            failed = harness.produce(exact_run, principal, proof)

        self.assert_outcome(failed, "integrity_failure")
        self.assertEqual(harness.binding._state.presentations, {})
        retried = harness.produce(exact_run, principal, proof)
        self.assert_outcome(retried, "issued")
        self.assertEqual(source.requested_lengths, [32, 32])


class ProducerRegistryTests(_ProducerAssertions):
    def test_sequential_retry_and_run_conflicts(self) -> None:
        source = _GrantIdSource([FIRST_ID_MATERIAL, SECOND_ID_MATERIAL])
        harness = _Harness(grant_id_source=source)
        exact_run, principal, proof = self.exact_human_request(harness)

        issued = harness.produce(exact_run, principal, proof)
        retried = harness.produce(exact_run, principal, proof)
        self.assert_outcome(issued, "issued")
        self.assert_outcome(retried, "existing_exact_issuance")
        self.assertIs(retried.presentation, issued.presentation)
        self.assertEqual(source.requested_lengths, [32])
        self.assertEqual(harness.clock.calls, 2)

        different_proof = harness.human_proof(
            exact_run,
            principal,
            requested_lifetime=timedelta(minutes=1),
        )
        already_issued = harness.produce(exact_run, principal, different_proof)
        self.assert_outcome(already_issued, "run_already_issued")

        rebound_run = run(exact_run.run_id, resource="synthetic/other.txt")
        rebound_proof = harness.human_proof(rebound_run, principal)
        conflict = harness.produce(rebound_run, principal, rebound_proof)
        self.assert_outcome(conflict, "run_identity_conflict")
        self.assertEqual(source.requested_lengths, [32])

    def test_concurrent_identical_requests_share_one_presentation(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        barrier = Barrier(3)
        results: list[AgentExecutionAuthorizationGrantProductionResult] = []
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                barrier.wait()
                results.append(harness.produce(exact_run, principal, proof))
            except BaseException as error:
                errors.append(error)

        threads = [Thread(target=worker), Thread(target=worker)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)

        self.assertEqual(errors, [])
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 2)
        self.assertEqual(
            sorted(result.outcome.value for result in results),
            ["existing_exact_issuance", "issued"],
        )
        self.assertIs(results[0].presentation, results[1].presentation)
        self.assertEqual(harness.grant_id_source.requested_lengths, [32])

    def test_postcheck_ambiguity_burns_the_run(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        harness.session.exit_error = OwnedAuthorizationDomainSessionLostError(
            "synthetic post-check ambiguity"
        )

        ambiguous = harness.produce(exact_run, principal, proof)
        self.assert_outcome(ambiguous, "run_issuance_conflict")
        self.assertEqual(harness.binding._state.presentations, {})

        harness.session.exit_error = None
        burned = harness.produce(exact_run, principal, proof)
        self.assert_outcome(burned, "run_issuance_conflict")
        self.assertEqual(harness.grant_id_source.requested_lengths, [32])

    def test_composition_rejects_second_producer(self) -> None:
        harness = _Harness()
        with self.assertRaises(RuntimeError):
            harness.compose_again()

        fresh_session = _SyntheticOwnedSession()
        with self.assertRaises(ValueError):
            subject._compose_agent_execution_authorization_grant_producer(
                owned_session=fresh_session,
                identity_adapter=_IdentityAdapter(),
                human_approval_adapter=None,
                policy_decision_adapter=None,
                issuer_state_authority=_IssuerStateAuthority(),
                issuer_entitlement_policy=_EntitlementPolicy(),
                lifetime_policy=AgentExecutionAuthorizationGrantLifetimePolicy(
                    timedelta(minutes=1),
                    timedelta(minutes=2),
                    "lifetime-policy::synthetic",
                ),
                utc_clock=_Clock(),
                grant_id_source=_GrantIdSource(),
            )

    def test_fatal_binding_closes_state_and_retains_session_claim(self) -> None:
        for failure in (
            KeyboardInterrupt("synthetic fatal bind interruption"),
            SystemExit(73),
        ):
            with self.subTest(failure=type(failure).__name__):
                session = _SyntheticOwnedSession()
                identity_adapter = _IdentityAdapter()
                human_adapter = _FatalBindingHumanApprovalAdapter(failure)
                issuer_state = _IssuerStateAuthority()
                entitlement = _EntitlementPolicy()
                clock = _Clock()
                grant_id_source = _GrantIdSource()
                lifetime_policy = AgentExecutionAuthorizationGrantLifetimePolicy(
                    timedelta(minutes=1),
                    timedelta(minutes=2),
                    "lifetime-policy::fatal-bind",
                )

                with self.assertRaises(type(failure)) as raised:
                    subject._compose_agent_execution_authorization_grant_producer(
                        owned_session=session,
                        identity_adapter=identity_adapter,
                        human_approval_adapter=human_adapter,
                        policy_decision_adapter=None,
                        issuer_state_authority=issuer_state,
                        issuer_entitlement_policy=entitlement,
                        lifetime_policy=lifetime_policy,
                        utc_clock=clock,
                        grant_id_source=grant_id_source,
                    )

                self.assertIs(raised.exception, failure)
                self.assertIsNotNone(human_adapter._minter)
                state = human_adapter._minter._state
                self.assertIs(state.closed, True)
                self.assertEqual(state.principal_proofs, {})
                self.assertEqual(state.authority_proofs, {})
                self.assertEqual(state.issuances, {})
                self.assertEqual(state.presentations, {})
                self.assertEqual(state.allocated_grant_ids, set())
                self.assertEqual(grant_id_source.requested_lengths, [])
                self.assertIsNone(state.authentication_port.authenticate_grant(object()))

                with self.assertRaises(RuntimeError):
                    human_adapter.mint(
                        principal=object(),
                        run=run("run::fatal-bind-retained-minter"),
                        approval_session_id="approval-session::fatal-bind",
                        provenance_reference="approval::fatal-bind",
                        valid_from=VALID_FROM,
                        valid_until=VALID_UNTIL,
                    )

                with self.assertRaises(RuntimeError):
                    subject._compose_agent_execution_authorization_grant_producer(
                        owned_session=session,
                        identity_adapter=_IdentityAdapter(),
                        human_approval_adapter=_HumanApprovalAdapter(),
                        policy_decision_adapter=None,
                        issuer_state_authority=_IssuerStateAuthority(),
                        issuer_entitlement_policy=_EntitlementPolicy(),
                        lifetime_policy=lifetime_policy,
                        utc_clock=_Clock(),
                        grant_id_source=_GrantIdSource(),
                    )
                self.assertEqual(session.port_calls, 0)
                self.assertEqual(session.load_calls, 0)
                self.assertEqual(session.revoke_calls, 0)


class ProducerPresentationTests(_ProducerAssertions):
    def test_port_rejects_malformed_authority_run_before_equality(self) -> None:
        for issuer_kind in ("human", "policy"):
            with self.subTest(issuer_kind=issuer_kind):
                harness = _Harness()
                exact_run = run(f"run::port-{issuer_kind}-subject")
                principal = harness.principal(issuer_kind)
                proof = (
                    harness.human_proof(exact_run, principal)
                    if issuer_kind == "human"
                    else harness.policy_proof(exact_run, principal)
                )
                result = harness.produce(exact_run, principal, proof)
                self.assert_outcome(result, "issued")
                assert result.presentation is not None

                spoofing_subject = _EqualitySpoofingRunSubject()
                object.__setattr__(proof, "_run", spoofing_subject)
                self.assertIsNone(
                    harness.session.authenticate_under_outer_gate(
                        result.presentation
                    )
                )
                self.assertEqual(spoofing_subject.comparison_calls, 0)

    def test_port_rejects_raw_foreign_copied_and_integrity_conflicts(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        result = harness.produce(exact_run, principal, proof)
        self.assert_outcome(result, "issued")
        presentation = result.presentation
        assert presentation is not None

        operation_count = harness.session.entered_operations
        grant = harness.session.authenticate_under_outer_gate(presentation)
        self.assertIs(type(grant), AgentExecutionAuthorizationGrant)
        self.assertEqual(harness.session.entered_operations, operation_count + 1)
        assert grant is not None
        self.assertIs(
            harness.session.authenticate_under_outer_gate(presentation),
            grant,
        )
        self.assertIsNone(harness.binding.grant_authentication.authenticate_grant(grant))
        reconstructed = replace(grant)
        self.assertEqual(reconstructed, grant)
        self.assertIsNot(reconstructed, grant)
        self.assertIsNone(
            harness.binding.grant_authentication.authenticate_grant(reconstructed)
        )
        self.assertIsNone(
            harness.binding.grant_authentication.authenticate_grant(object())
        )

        foreign = _Harness()
        self.assertIsNone(
            foreign.binding.grant_authentication.authenticate_grant(presentation)
        )
        with self.assertRaises(TypeError):
            copy.copy(presentation)
        with self.assertRaises(TypeError):
            copy.deepcopy(presentation)
        with self.assertRaises(TypeError):
            pickle.dumps(presentation)

        record = harness.binding._state.presentations[id(presentation)]
        record.sealed_grant = ("tampered",) + record.sealed_grant[1:]
        self.assertIsNone(
            harness.session.authenticate_under_outer_gate(presentation)
        )
        self.assertEqual(harness.session.load_calls, 0)
        self.assertEqual(harness.session.revoke_calls, 0)

    def test_disable_reenable_and_port_linearization(self) -> None:
        harness = _Harness()
        exact_run, principal, proof = self.exact_human_request(harness)
        result = harness.produce(exact_run, principal, proof)
        assert result.presentation is not None
        grant = harness.session.authenticate_under_outer_gate(result.presentation)
        self.assertIsNotNone(grant)

        harness.issuer_state.disable()
        self.assertIsNone(
            harness.session.authenticate_under_outer_gate(result.presentation)
        )
        harness.issuer_state.enable()
        self.assertIsNone(
            harness.session.authenticate_under_outer_gate(result.presentation)
        )

        after_check = _Harness()
        exact_run, principal, proof = self.exact_human_request(
            after_check,
            run("run::disable-after-check"),
        )
        result = after_check.produce(exact_run, principal, proof)
        assert result.presentation is not None
        already_authenticated = after_check.session.authenticate_under_outer_gate(
            result.presentation
        )
        after_check.issuer_state.disable()
        self.assertIs(type(already_authenticated), AgentExecutionAuthorizationGrant)
        self.assertIsNone(
            after_check.session.authenticate_under_outer_gate(result.presentation)
        )

        disabled_before = _Harness()
        exact_run, principal, proof = self.exact_human_request(
            disabled_before,
            run("run::disabled-before-produce"),
        )
        disabled_before.issuer_state.disable()
        self.assert_outcome(
            disabled_before.produce(exact_run, principal, proof),
            "issuer_disabled",
        )

    def test_close_and_restart_invalidate_presentations(self) -> None:
        original = _Harness()
        old_run, old_principal, old_proof = self.exact_human_request(original)
        issued = original.produce(old_run, old_principal, old_proof)
        assert issued.presentation is not None

        original.producer.close()
        original.producer.close()
        self.assertIsNone(
            original.session.authenticate_under_outer_gate(issued.presentation)
        )
        self.assert_outcome(
            original.produce(old_run, old_principal, old_proof),
            "producer_closed",
        )
        with self.assertRaises(RuntimeError):
            original.compose_again()

        restarted = _Harness(identity=IDENTITY)
        self.assertIsNone(
            restarted.binding.grant_authentication.authenticate_grant(
                issued.presentation
            )
        )
        new_run, new_principal, new_proof = self.exact_human_request(
            restarted,
            run("run::after-restart"),
        )
        self.assert_outcome(
            restarted.produce(new_run, new_principal, new_proof),
            "issued",
        )

    def test_outer_gate_rejects_closed_or_fenced_before_port(self) -> None:
        fenced = _Harness()
        exact_run, principal, proof = self.exact_human_request(fenced)
        result = fenced.produce(exact_run, principal, proof)
        assert result.presentation is not None
        calls_before = fenced.session.port_calls
        fenced.session.fence()
        with self.assertRaises(OwnedAuthorizationDomainSessionLostError):
            fenced.session.authenticate_under_outer_gate(result.presentation)
        self.assertEqual(fenced.session.port_calls, calls_before)

        closed = _Harness()
        exact_run, principal, proof = self.exact_human_request(
            closed,
            run("run::closed-outer-gate"),
        )
        result = closed.produce(exact_run, principal, proof)
        assert result.presentation is not None
        calls_before = closed.session.port_calls
        closed.session.close()
        with self.assertRaises(OwnedAuthorizationDomainSessionClosedError):
            closed.session.authenticate_under_outer_gate(result.presentation)
        self.assertEqual(closed.session.port_calls, calls_before)
        self.assertEqual(closed.session.load_calls, 0)
        self.assertEqual(closed.session.revoke_calls, 0)


if __name__ == "__main__":
    unittest.main()
