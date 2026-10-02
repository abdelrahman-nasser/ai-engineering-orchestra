from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import engineering_orchestration.local_operational_trust as local_trust
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_authorization_grant_producer import (
    AgentExecutionAuthorizationGrantLifetimePolicy,
    AgentExecutionAuthorizationGrantProductionOutcome,
    AgentExecutionAuthorizationGrantProductionResult,
    AgentExecutionAuthorizationGrantRetryDisposition,
    _AgentExecutionAuthorizationGrantAuthenticationPort,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import AgentExecutionContract
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentActionPrerequisiteParentInputs,
    AgentExecutionDispatchAdmissionStoreOutcome,
    AgentExecutionDispatchAdmissionStoreResult,
    AgentExecutionDispatchAdmissionStoreRetryDisposition,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
from engineering_orchestration.agent_operation_tool_registry import (
    _AgentOperationToolRegistryOutcome,
    _AgentOperationToolRegistryRetryDisposition,
    _AgentOperationToolRoute,
    _build_trusted_agent_operation_tool_registry_snapshot,
    _make_aeo_native_repository_file_read_registration,
    _select_agent_operation_tool_route,
)
from engineering_orchestration.agent_operation_tool_resolver import (
    TrustedAgentOperationToolBindingResolver,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.local_operational_trust import (
    LocalOperationalTrustCoordinator,
    _cleanup_components,
    _compose_local_operational_trust_coordinator,
    _new_grant_authentication_latch,
)
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
)
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    SqliteAdmissionStoreIntegrityError,
    SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
)
from engineering_orchestration import windows_local_authorization_domain_owner as windows_owner


TASK_ID = "AIO-053"
TASK_TYPE = "architecture-change"
ACTION = "implement"
ROLE_ID = "software-engineer"
ACTOR_ID = "actor::synthetic"
RUNTIME_ID = "runtime::synthetic"
INFERENCE_ID = "inference::synthetic"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
RESOURCE = "synthetic/input.txt"
EXECUTION_MODE = "critical"
DOMAIN_ID = "authorization-domain::aio-053-synthetic"
LEDGER_ID = "ledger-instance::aio-053-synthetic"
TOOL_ID = "tool::aeo-native-repository-file-read::v1"


# This is deliberately a closed, reviewable map.  A scenario may not disappear
# merely because a test is renamed or regrouped.
SCENARIO_TEST_MAP = {
    1: "LocalOperationalTrustWindowsTests.test_01_exact_human_approval",
    2: "LocalOperationalTrustWindowsTests.test_02_exact_policy_allow",
    3: "LocalOperationalTrustWindowsTests.test_03_policy_deny",
    4: "LocalOperationalTrustWindowsTests.test_04_expired_authority",
    5: "LocalOperationalTrustWindowsTests.test_05_run_changed_after_proof",
    6: "LocalOperationalTrustWindowsTests.test_06_fabricated_grant",
    7: "LocalOperationalTrustWindowsTests.test_07_foreign_presentation",
    8: "LocalOperationalTrustWindowsTests.test_08_wrong_domain",
    9: "LocalOperationalTrustWindowsTests.test_09_wrong_generation",
    10: "LocalOperationalTrustWindowsTests.test_10_ownership_lost",
    11: "LocalOperationalTrustWindowsTests.test_11_fenced_or_closed_session",
    12: "LocalOperationalTrustWindowsTests.test_12_unknown_tool_route",
    13: "LocalOperationalTrustContractTests.test_13_retired_route",
    14: "LocalOperationalTrustContractTests.test_14_tool_id_rebind",
    15: "LocalOperationalTrustWindowsTests.test_15_runtime_mismatch",
    16: "LocalOperationalTrustWindowsTests.test_16_environment_mismatch",
    17: "LocalOperationalTrustWindowsTests.test_17_operation_mismatch",
    18: "LocalOperationalTrustWindowsTests.test_18_resource_widening",
    19: "LocalOperationalTrustWindowsTests.test_19_contradictory_binding_run",
    20: "LocalOperationalTrustWindowsTests.test_20_expected_run_mismatch",
    21: "LocalOperationalTrustWindowsTests.test_21_fresh_source_rejections",
    22: "LocalOperationalTrustWindowsTests.test_22_invalid_execution_mode",
    23: "LocalOperationalTrustWindowsTests.test_23_original_issuer_revocation",
    24: "LocalOperationalTrustWindowsTests.test_24_expired_grant",
    25: "LocalOperationalTrustWindowsTests.test_25_exact_admission_retry",
    26: "LocalOperationalTrustWindowsTests.test_26_restart_boundary",
    27: "LocalOperationalTrustContractTests.test_27_registry_reconstruction",
    28: "LocalOperationalTrustWindowsTests.test_28_corrupt_ledger",
    29: "LocalOperationalTrustWindowsTests.test_29_no_tool_fallback",
    30: "LocalOperationalTrustWindowsTests.test_30_option_substitution",
    31: "LocalOperationalTrustContractTests.test_31_latch_before_binding",
    32: "LocalOperationalTrustContractTests.test_32_latch_is_install_once",
    33: "LocalOperationalTrustContractTests.test_33_cleanup_is_exhaustive",
    34: "LocalOperationalTrustWindowsTests.test_34_pre_admission_retry",
    35: "LocalOperationalTrustWindowsTests.test_35_binding_has_no_behavior",
    36: "LocalOperationalTrustWindowsTests.test_36_inter_lease_fence",
    37: "LocalOperationalTrustWindowsTests.test_37_close_race",
    38: "LocalOperationalTrustWindowsTests.test_38_operation_after_close",
    39: "LocalOperationalTrustWindowsTests.test_39_foreign_adapter_epoch",
    40: "LocalOperationalTrustWindowsTests.test_40_issuer_disabled_between_leases",
    41: "LocalOperationalTrustWindowsTests.test_41_stale_revocation_proof",
    42: "LocalOperationalTrustWindowsTests.test_42_foreign_authority_subjects",
}


class _ExecutionProbe:
    """Record real identity-only Bindings and inspect executable surfaces."""

    def __init__(self) -> None:
        self.bindings: list[AgentOperationToolBinding] = []

    def observe_binding(self, binding: AgentOperationToolBinding) -> None:
        self.bindings.append(binding)

    def assert_no_execution_surfaces(self, case: unittest.TestCase) -> None:
        registration = _make_aeo_native_repository_file_read_registration(
            RUNTIME_ID,
            ENVIRONMENT_ID,
        )
        selector = registration.implementation_selector
        case.assertFalse(callable(selector))
        for name in ("dispatch", "invoke", "open", "read", "read_resource"):
            case.assertFalse(hasattr(selector, name))
            case.assertFalse(hasattr(LocalOperationalTrustCoordinator, name))
        for binding in self.bindings:
            case.assertIs(type(binding), AgentOperationToolBinding)
            case.assertFalse(callable(binding))
            for name in ("dispatch", "invoke", "open", "read", "read_resource"):
                case.assertFalse(hasattr(binding, name))
            case.assertIs(type(binding.run.contract.resource), str)


class _Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

    def now_utc(self) -> datetime:
        return self.value

    def advance(self, amount: timedelta) -> None:
        self.value += amount


class _GrantIdSource:
    def __init__(self) -> None:
        self._counter = 0

    def random_bytes(self, length: int) -> bytes:
        self._counter += 1
        seed = hashlib.sha256(str(self._counter).encode("ascii")).digest()
        return (seed * ((length // len(seed)) + 1))[:length]


class _IdentityAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid = True
        self._minter = None
        self._minted: dict[int, object] = {}

    def current_epoch(self) -> object:
        return self.epoch

    def validate_authenticated_principal(self, principal: object) -> bool:
        return self.valid and self._minted.get(id(principal)) is principal

    def _bind_authenticated_issuer_principal_minter(self, minter: object) -> None:
        if self._minter is not None:
            raise RuntimeError("identity minter already bound")
        self._minter = minter

    def mint(self, *, issuer_kind: str, issuer_id: str, now: datetime) -> object:
        if self._minter is None:
            raise RuntimeError("identity minter is not bound")
        principal = self._minter.mint(
            issuer_kind=issuer_kind,
            issuer_id=issuer_id,
            authentication_session_id="authentication-session::synthetic",
            valid_from=now - timedelta(minutes=5),
            valid_until=now + timedelta(hours=1),
        )
        self._minted[id(principal)] = principal
        return principal

    def rotate_epoch(self) -> None:
        self.epoch = object()


class _HumanApprovalAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid = True
        self._minter = None
        self._minted: dict[int, object] = {}

    def current_epoch(self) -> object:
        return self.epoch

    def validate_authenticated_human_approval(self, approval: object) -> bool:
        return self.valid and self._minted.get(id(approval)) is approval

    def _bind_authenticated_human_approval_minter(self, minter: object) -> None:
        if self._minter is not None:
            raise RuntimeError("Human approval minter already bound")
        self._minter = minter

    def mint(
        self,
        *,
        principal: object,
        run: AgentExecutionRun,
        now: datetime,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        provenance_reference: str = "approval::synthetic",
    ) -> object:
        if self._minter is None:
            raise RuntimeError("Human approval minter is not bound")
        approval = self._minter.mint(
            principal=principal,
            run=run,
            approval_session_id="approval-session::synthetic",
            provenance_reference=provenance_reference,
            valid_from=valid_from or now - timedelta(minutes=1),
            valid_until=valid_until or now + timedelta(minutes=10),
            requested_lifetime=None,
        )
        self._minted[id(approval)] = approval
        return approval


class _PolicyDecisionAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid = True
        self._minter = None
        self._minted: dict[int, object] = {}

    def current_epoch(self) -> object:
        return self.epoch

    def validate_authenticated_policy_decision(self, decision: object) -> bool:
        return self.valid and self._minted.get(id(decision)) is decision

    def _bind_authenticated_policy_decision_minter(self, minter: object) -> None:
        if self._minter is not None:
            raise RuntimeError("policy minter already bound")
        self._minter = minter

    def mint(
        self,
        *,
        principal: object,
        run: AgentExecutionRun,
        now: datetime,
        decision: str,
        provenance_reference: str = "policy-decision::synthetic",
    ) -> object:
        if self._minter is None:
            raise RuntimeError("policy minter is not bound")
        proof = self._minter.mint(
            principal=principal,
            run=run,
            decision=decision,
            policy_revision="policy-revision::1",
            provenance_reference=provenance_reference,
            valid_from=now - timedelta(minutes=1),
            valid_until=now + timedelta(minutes=10),
            requested_lifetime=None,
        )
        self._minted[id(proof)] = proof
        return proof


class _IssuerStateAuthority:
    def __init__(self) -> None:
        self.enabled = True
        self.epoch = object()

    def observe_issuer_state(
        self,
        issuer_kind: str,
        issuer_id: str,
    ) -> tuple[bool, object]:
        del issuer_kind, issuer_id
        return self.enabled, self.epoch


class _EntitlementPolicy:
    def __init__(self) -> None:
        self.entitled = True

    def is_entitled(
        self,
        run: AgentExecutionRun,
        domain_identity: object,
        issuer_kind: str,
        issuer_id: str,
    ) -> bool:
        del run, domain_identity, issuer_kind, issuer_id
        return self.entitled


class _FreshPrerequisiteSource:
    def __init__(self) -> None:
        self.override: object | None = None
        self.use_override = False
        self.failure: BaseException | None = None
        self.calls = 0

    def collect_fresh_parent_results(
        self,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> object:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        if self.use_override:
            return self.override
        if binding.run != grant.run:
            return None
        return _make_parent_inputs(grant.run)


class _ExecutionModeResolver:
    def __init__(self) -> None:
        self.mode = EXECUTION_MODE
        self.calls = 0

    def resolve_effective_execution_mode(
        self,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> str:
        del grant, binding
        self.calls += 1
        return self.mode


class _RevocationProof:
    __slots__ = (
        "domain_identity",
        "epoch",
        "intent",
        "provenance_reference",
        "run",
    )

    def __init__(
        self,
        *,
        run: AgentExecutionRun,
        domain_identity: object,
        epoch: object,
        provenance_reference: str,
    ) -> None:
        self.run = run
        self.domain_identity = domain_identity
        self.epoch = epoch
        self.intent = "revoke"
        self.provenance_reference = provenance_reference


class _RevocationAdapter:
    def __init__(self) -> None:
        self.epoch = object()
        self.valid = True
        self._proofs: dict[int, _RevocationProof] = {}
        self.validation_calls = 0

    def current_epoch(self) -> object:
        return self.epoch

    def issue(
        self,
        *,
        run: AgentExecutionRun,
        domain_identity: object,
        provenance_reference: str,
    ) -> _RevocationProof:
        proof = _RevocationProof(
            run=run,
            domain_identity=domain_identity,
            epoch=self.epoch,
            provenance_reference=provenance_reference,
        )
        self._proofs[id(proof)] = proof
        return proof

    def validate_authenticated_original_issuer_revocation(
        self,
        proof: object,
        *,
        grant: AgentExecutionAuthorizationGrant,
        domain_identity: object,
        intent: str,
        provenance_reference: str,
    ) -> bool:
        self.validation_calls += 1
        return (
            self.valid
            and isinstance(proof, _RevocationProof)
            and self._proofs.get(id(proof)) is proof
            and proof.epoch is self.epoch
            and proof.run == grant.run
            and proof.domain_identity == domain_identity
            and proof.intent == intent == "revoke"
            and proof.provenance_reference == provenance_reference
        )

    def rotate_epoch(self) -> None:
        self.epoch = object()


def _make_run(
    run_id: str = "run::aio-053-synthetic",
    *,
    runtime_option_id: str = RUNTIME_ID,
    option_id: str = INFERENCE_ID,
    environment_id: str = ENVIRONMENT_ID,
    operation_id: str = OPERATION_ID,
    resource: str = RESOURCE,
    execution_mode: str = EXECUTION_MODE,
) -> AgentExecutionRun:
    contract = AgentExecutionContract(
        TASK_ID,
        TASK_TYPE,
        ACTION,
        ROLE_ID,
        ACTOR_ID,
        runtime_option_id,
        option_id,
        environment_id,
        operation_id,
        resource,
        execution_mode,
    )
    return AgentExecutionRun(run_id, contract)


def _make_parent_inputs(run: AgentExecutionRun) -> AgentActionPrerequisiteParentInputs:
    contract = run.contract
    responsibility_key = (TASK_ID, TASK_TYPE, ACTION, ROLE_ID)
    candidate = AgentExecutionCandidatePrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=responsibility_key,
        actor_id=contract.actor_id,
        runtime_option_id=contract.runtime_option_id,
        option_id=contract.option_id,
        outcome=AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
        reasons=(
            AgentExecutionCandidatePrerequisiteReason.ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
        ),
    )
    capability = RuntimeOperationCapabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=(
            RuntimeOperationCapabilityObservation(
                contract.runtime_option_id,
                contract.operation_id,
                RuntimeOperationCapabilityState.PRESENT,
            ),
        ),
    )
    permission = EnvironmentOperationPermissionValidationResult(
        valid=True,
        findings=(),
        normalized_observations=(
            EnvironmentOperationPermissionObservation(
                contract.runtime_option_id,
                contract.environment_id,
                contract.operation_id,
                contract.resource,
                EnvironmentOperationPermissionState.ALLOWED,
            ),
        ),
    )
    evidence = AgentExecutionAuthorizationEvidence(
        *responsibility_key,
        contract.actor_id,
        contract.runtime_option_id,
        contract.option_id,
        contract.environment_id,
        contract.operation_id,
        contract.resource,
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
        requirement=OperationRequirement(
            contract.operation_id,
            contract.resource,
        ),
        capability_result=capability,
        permission_result=permission,
        authorization_result=authorization,
        environment_id=contract.environment_id,
    )


def _make_unsatisfied_parent_inputs(
    run: AgentExecutionRun,
) -> AgentActionPrerequisiteParentInputs:
    parents = _make_parent_inputs(run)
    contract = run.contract
    return AgentActionPrerequisiteParentInputs(
        candidate_result=AgentExecutionCandidatePrerequisiteResult(
            valid=True,
            findings=(),
            responsibility_key=(TASK_ID, TASK_TYPE, ACTION, ROLE_ID),
            actor_id=contract.actor_id,
            runtime_option_id=contract.runtime_option_id,
            option_id=contract.option_id,
            outcome=AgentExecutionCandidatePrerequisiteOutcome.BLOCKED,
            reasons=(AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,),
        ),
        requirement=parents.requirement,
        capability_result=parents.capability_result,
        permission_result=parents.permission_result,
        authorization_result=parents.authorization_result,
        environment_id=parents.environment_id,
    )


class _WindowsHarness:
    def __init__(
        self,
        case: unittest.TestCase,
        *,
        domain_id: str = DOMAIN_ID,
        generation: int = 1,
        ledger_id: str = LEDGER_ID,
    ) -> None:
        self.case = case
        self.domain_id = domain_id
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="aio-053-local-trust-",
            dir=Path(__file__).resolve().parent.parent,
        )
        case.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name) / "local-appdata"
        self.root.mkdir()
        sid = windows_owner._current_user_sid()
        windows_owner._apply_security_profile(self.root, sid, directory=True)
        self.ledger_directory = self.root / "ledger"
        self.ledger_directory.mkdir()
        windows_owner._apply_security_profile(
            self.ledger_directory,
            sid,
            directory=True,
        )
        self.configuration = SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
            database_path=self.ledger_directory / "admission.sqlite3",
            authorization_domain_id=domain_id,
            ledger_instance_id=ledger_id,
            domain_generation=generation,
            busy_timeout_ms=2_000,
        )
        self._local_path_patch = mock.patch.object(
            windows_owner,
            "_local_appdata_path",
            return_value=self.root,
        )
        self._local_path_patch.start()
        self._patch_live = True
        case.addCleanup(self._stop_patch)
        self.clock = _Clock()
        administration = windows_owner.WindowsLocalAuthorizationDomainAdministration(
            clock=self.clock,
            busy_timeout_ms=2_000,
        )
        provisioned = administration.provision(self.configuration)
        case.assertEqual(provisioned.outcome.value, "provisioned")
        registered = administration.register(self.configuration)
        activated = administration.activate(
            self.configuration.authorization_domain_id
        )
        case.assertEqual(activated, registered)
        self.coordinator: LocalOperationalTrustCoordinator | None = None
        self._install_adapters_and_compose()
        case.addCleanup(self.close)

    def _install_adapters_and_compose(self) -> None:
        self.identity = _IdentityAdapter()
        self.human = _HumanApprovalAdapter()
        self.policy = _PolicyDecisionAdapter()
        self.issuer_state = _IssuerStateAuthority()
        self.entitlement = _EntitlementPolicy()
        self.fresh_source = _FreshPrerequisiteSource()
        self.mode_resolver = _ExecutionModeResolver()
        self.revocation = _RevocationAdapter()
        self.grant_ids = _GrantIdSource()
        self.coordinator = _compose_local_operational_trust_coordinator(
            authorization_domain_id=self.domain_id,
            runtime_option_id=RUNTIME_ID,
            environment_id=ENVIRONMENT_ID,
            identity_adapter=self.identity,
            human_approval_adapter=self.human,
            policy_decision_adapter=self.policy,
            issuer_state_authority=self.issuer_state,
            issuer_entitlement_policy=self.entitlement,
            lifetime_policy=AgentExecutionAuthorizationGrantLifetimePolicy(
                timedelta(minutes=5),
                timedelta(minutes=10),
                "grant-lifetime-policy::1",
            ),
            clock=self.clock,
            grant_id_source=self.grant_ids,
            fresh_prerequisite_source=self.fresh_source,
            execution_mode_resolver=self.mode_resolver,
            revocation_adapter=self.revocation,
            busy_timeout_ms=2_000,
        )

    def _stop_patch(self) -> None:
        if self._patch_live:
            self._local_path_patch.stop()
            self._patch_live = False

    def close(self) -> None:
        if self.coordinator is not None:
            coordinator, self.coordinator = self.coordinator, None
            coordinator.close()

    def suspend(self) -> None:
        self.close()
        self._stop_patch()

    def restart(self) -> None:
        self.close()
        self._install_adapters_and_compose()

    def human_authority(
        self,
        run: AgentExecutionRun,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> tuple[object, object]:
        principal = self.identity.mint(
            issuer_kind="human",
            issuer_id="human::synthetic",
            now=self.clock.now_utc(),
        )
        approval = self.human.mint(
            principal=principal,
            run=run,
            now=self.clock.now_utc(),
            valid_from=valid_from,
            valid_until=valid_until,
        )
        return principal, approval

    def policy_authority(
        self,
        run: AgentExecutionRun,
        *,
        decision: str,
    ) -> tuple[object, object]:
        principal = self.identity.mint(
            issuer_kind="policy",
            issuer_id="policy::synthetic",
            now=self.clock.now_utc(),
        )
        proof = self.policy.mint(
            principal=principal,
            run=run,
            now=self.clock.now_utc(),
            decision=decision,
        )
        return principal, proof


class _NoExecutionMixin:
    probe: _ExecutionProbe

    def assert_no_execution(self) -> None:
        self.probe.assert_no_execution_surfaces(self)


class LocalOperationalTrustContractTests(_NoExecutionMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.probe = _ExecutionProbe()

    def tearDown(self) -> None:
        self.assert_no_execution()

    def test_13_retired_route(self) -> None:
        registration = _make_aeo_native_repository_file_read_registration(
            RUNTIME_ID,
            ENVIRONMENT_ID,
        )
        route = _AgentOperationToolRoute(
            RUNTIME_ID,
            ENVIRONMENT_ID,
            OPERATION_ID,
        )
        result = _build_trusted_agent_operation_tool_registry_snapshot(
            (registration,),
            retired_routes=(route,),
        )
        self.assertIs(result.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIsNotNone(result.snapshot)
        snapshot = result.snapshot
        assert snapshot is not None
        selection = _select_agent_operation_tool_route(snapshot, route=route)
        self.assertIs(
            selection.outcome,
            _AgentOperationToolRegistryOutcome.TOOL_RETIRED,
        )
        self.assertIsNone(selection.selected_route)

        resolver = TrustedAgentOperationToolBindingResolver(snapshot)
        run = _make_run("run::retired-route")
        grant = AgentExecutionAuthorizationGrant(
            "grant::retired-route",
            run,
            DOMAIN_ID,
            "human",
            "human::synthetic",
            "grant-provenance::synthetic",
            "2026-01-15T12:00:00Z",
            "2026-01-15T12:05:00Z",
        )
        binding = resolver.resolve_tool_binding(grant)
        self.assertIsNotNone(binding)
        assert binding is not None
        self.probe.observe_binding(binding)
        self.assertEqual(binding.run, run)
        self.assertEqual(binding.tool_id, TOOL_ID)
        reconstructed = _build_trusted_agent_operation_tool_registry_snapshot(
            (registration,),
            retired_routes=(route,),
            prior_snapshot=snapshot,
        )
        self.assertIs(
            reconstructed.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )

    def test_14_tool_id_rebind(self) -> None:
        registration = _make_aeo_native_repository_file_read_registration(
            RUNTIME_ID,
            ENVIRONMENT_ID,
        )
        first = _build_trusted_agent_operation_tool_registry_snapshot((registration,))
        self.assertIs(first.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        changed = object.__new__(type(registration))
        changed_slot = False
        for owner in reversed(type(registration).__mro__):
            slots = getattr(owner, "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for slot in slots:
                if slot in {"__dict__", "__weakref__"}:
                    continue
                value = getattr(registration, slot)
                if slot.endswith("tool_id"):
                    value = "tool::attempted-rebind::v1"
                    changed_slot = True
                object.__setattr__(changed, slot, value)
        self.assertTrue(changed_slot)
        attempted = _build_trusted_agent_operation_tool_registry_snapshot(
            (changed,),
            prior_snapshot=first.snapshot,
        )
        self.assertIs(
            attempted.outcome,
            _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND,
        )
        self.assertIs(
            attempted.retry_disposition,
            _AgentOperationToolRegistryRetryDisposition.
            HISTORICAL_MAPPING_REMEDIATION_REQUIRED,
        )
        self.assertIsNone(attempted.snapshot)
        self.assertIsNotNone(first.snapshot)

    def test_27_registry_reconstruction(self) -> None:
        registration = _make_aeo_native_repository_file_read_registration(
            RUNTIME_ID,
            ENVIRONMENT_ID,
        )
        first = _build_trusted_agent_operation_tool_registry_snapshot((registration,))
        self.assertIs(first.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIsNotNone(first.snapshot)
        first_snapshot = first.snapshot
        assert first_snapshot is not None
        second = _build_trusted_agent_operation_tool_registry_snapshot(
            (
                _make_aeo_native_repository_file_read_registration(
                    RUNTIME_ID,
                    ENVIRONMENT_ID,
                ),
            ),
            prior_snapshot=first_snapshot,
            expected_fingerprint=first_snapshot._registration_fingerprint,
        )
        self.assertIs(second.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIsNotNone(second.snapshot)
        second_snapshot = second.snapshot
        assert second_snapshot is not None
        self.assertEqual(
            first_snapshot._registration_fingerprint,
            second_snapshot._registration_fingerprint,
        )

    def test_31_latch_before_binding(self) -> None:
        latch, _bind = _new_grant_authentication_latch()
        self.assertIsNone(latch.authenticate_grant(object()))
        latch.close()
        self.assertIsNone(latch.authenticate_grant(object()))

    def test_32_latch_is_install_once(self) -> None:
        latch, bind = _new_grant_authentication_latch()
        target = object.__new__(_AgentExecutionAuthorizationGrantAuthenticationPort)
        bind(target)
        with self.assertRaises(RuntimeError):
            bind(target)
        self.assertIs(latch._target, target)

        foreign, bind_foreign = _new_grant_authentication_latch()
        with self.assertRaises(RuntimeError):
            bind_foreign(object())
        self.assertIsNone(foreign.authenticate_grant(object()))

    def test_33_cleanup_is_exhaustive(self) -> None:
        class _ClosingComponent:
            def __init__(self, label: str) -> None:
                self.label = label
                self.calls = 0

            def close(self) -> None:
                self.calls += 1
                raise RuntimeError(self.label)

        producer = _ClosingComponent("producer")
        revocation = _ClosingComponent("revocation")
        latch = _ClosingComponent("latch")
        session = _ClosingComponent("session")
        failures = _cleanup_components(
            producer=producer,
            revocation_port=revocation,
            latch=latch,
            session=session,
        )
        self.assertEqual([item.calls for item in (producer, revocation, latch, session)], [1, 1, 1, 1])
        self.assertEqual(len(failures), 4)
        with self.assertRaises(TypeError):
            LocalOperationalTrustCoordinator()

        captured_cleanup: list[dict[str, object]] = []
        real_cleanup = local_trust._cleanup_components

        def record_cleanup(**components: object) -> list[BaseException]:
            captured_cleanup.append(components)
            return real_cleanup(**components)  # type: ignore[arg-type]

        def attempt_composition(
            *,
            identity_adapter: object | None = None,
            human_approval_adapter: object | None = None,
        ) -> None:
            _compose_local_operational_trust_coordinator(
                authorization_domain_id=DOMAIN_ID,
                runtime_option_id=RUNTIME_ID,
                environment_id=ENVIRONMENT_ID,
                identity_adapter=(identity_adapter or _IdentityAdapter()),
                human_approval_adapter=(
                    human_approval_adapter or _HumanApprovalAdapter()
                ),
                policy_decision_adapter=_PolicyDecisionAdapter(),
                issuer_state_authority=_IssuerStateAuthority(),
                issuer_entitlement_policy=_EntitlementPolicy(),
                lifetime_policy=AgentExecutionAuthorizationGrantLifetimePolicy(
                    timedelta(minutes=5),
                    timedelta(minutes=10),
                    "grant-lifetime-policy::cleanup-cut",
                ),
                clock=_Clock(),
                grant_id_source=_GrantIdSource(),
                fresh_prerequisite_source=_FreshPrerequisiteSource(),
                execution_mode_resolver=_ExecutionModeResolver(),
                revocation_adapter=_RevocationAdapter(),
            )

        with mock.patch.object(
            local_trust,
            "WindowsLocalAuthorizationDomainOwner",
            side_effect=RuntimeError("synthetic acquisition cut"),
        ), mock.patch.object(
            local_trust,
            "_cleanup_components",
            side_effect=record_cleanup,
        ):
            with self.assertRaisesRegex(RuntimeError, "acquisition cut"):
                attempt_composition()
        self.assertEqual(len(captured_cleanup), 1)
        cleaned = captured_cleanup[0]
        self.assertIsNone(cleaned["producer"])
        self.assertIsNone(cleaned["session"])
        self.assertEqual(cleaned["latch"]._state, "closed")
        self.assertTrue(cleaned["revocation_port"]._closed)

        class _CutLease:
            def __init__(self, session: _CutSession) -> None:
                self._session = session

            @property
            def identity(self) -> object:
                return self._session.identity

            def __enter__(self) -> _CutLease:
                return self

            def __exit__(
                self,
                exception_type: object,
                exception: object,
                traceback: object,
            ) -> None:
                del exception_type, exception, traceback

        class _CutSession(local_trust.OwnedAuthorizationDomainSession):
            def __init__(self, suffix: str) -> None:
                self._identity = local_trust.AuthorizationDomainIdentity(
                    authorization_domain_id=DOMAIN_ID,
                    ledger_instance_id=f"ledger-instance::cut-{suffix}",
                    domain_generation=1,
                )
                self.close_calls = 0

            @property
            def identity(self) -> object:
                return self._identity

            def operation(self) -> object:
                return _CutLease(self)

            def admit(self, presented_grant: object) -> object:
                del presented_grant
                raise AssertionError("cut session must not admit")

            def load_authoritative_admission(
                self,
                presented_grant: object,
            ) -> object:
                del presented_grant
                raise AssertionError("cut session must not load")

            def revoke(self, presented_grant: object) -> object:
                del presented_grant
                raise AssertionError("cut session must not revoke")

            def close(self) -> None:
                self.close_calls += 1

            def fence(self) -> None:
                raise AssertionError("cut session must not fence")

        class _CapturingIdentityAdapter(_IdentityAdapter):
            def __init__(self) -> None:
                super().__init__()
                self.captured_state: object | None = None

            def _bind_authenticated_issuer_principal_minter(
                self,
                minter: object,
            ) -> None:
                super()._bind_authenticated_issuer_principal_minter(minter)
                self.captured_state = minter._state

        class _FailingHumanApprovalAdapter(_HumanApprovalAdapter):
            def _bind_authenticated_human_approval_minter(
                self,
                minter: object,
            ) -> None:
                super()._bind_authenticated_human_approval_minter(minter)
                raise RuntimeError("synthetic adapter-bind cut")

        class _CutOwner:
            def __init__(
                self,
                *,
                cut: str,
                session: _CutSession,
            ) -> None:
                self.cut = cut
                self.session = session

            def acquire(self, authorization_domain_id: str) -> _CutSession:
                if authorization_domain_id != DOMAIN_ID:
                    raise AssertionError("unexpected authorization domain")
                if self.cut == "owner-acquire":
                    raise RuntimeError("synthetic owner-acquire cut")
                return self.session

        class _PairedState:
            def __init__(self) -> None:
                self.lock = threading.Lock()
                self.closed = False
                self.producer: object | None = None
                self.authentication_port: object | None = None

        def make_exact_pair() -> tuple[object, object, _PairedState, object]:
            state = _PairedState()
            producer = object.__new__(
                local_trust.AgentExecutionAuthorizationGrantProducer
            )
            object.__setattr__(producer, "_state", state)
            authentication_port = object.__new__(
                _AgentExecutionAuthorizationGrantAuthenticationPort
            )
            object.__setattr__(authentication_port, "_state", state)
            state.producer = producer
            state.authentication_port = authentication_port
            binding = object.__new__(
                local_trust._AgentExecutionAuthorizationGrantProducerBinding
            )
            object.__setattr__(binding, "_state", state)
            return binding, producer, state, authentication_port

        real_latch_factory = local_trust._new_grant_authentication_latch
        real_producer_composer = (
            local_trust._compose_agent_execution_authorization_grant_producer
        )
        real_revocation_bind = local_trust._OriginalIssuerRevocationPort.bind_session
        for cut in (
            "owner-acquire",
            "producer-composition",
            "adapter-bind",
            "latch-bind",
            "revocation-bind",
        ):
            with self.subTest(composition_cut=cut):
                cut_session = _CutSession(cut)
                cut_owner = _CutOwner(cut=cut, session=cut_session)
                binding, producer, pair_state, authentication_port = (
                    make_exact_pair()
                )
                cut_cleanups: list[dict[str, object]] = []
                cut_identity_adapter: object = _IdentityAdapter()
                cut_human_adapter: object = _HumanApprovalAdapter()
                if cut == "adapter-bind":
                    cut_identity_adapter = _CapturingIdentityAdapter()
                    cut_human_adapter = _FailingHumanApprovalAdapter()

                def compose_at_cut(**kwargs: object) -> object:
                    if cut == "producer-composition":
                        raise RuntimeError(f"synthetic {cut} cut")
                    if cut == "adapter-bind":
                        return real_producer_composer(**kwargs)  # type: ignore[arg-type]
                    return binding

                def latch_factory_at_cut() -> tuple[object, object]:
                    latch, bind = real_latch_factory()

                    def bind_at_cut(target: object) -> None:
                        if cut == "latch-bind":
                            raise RuntimeError("synthetic latch-bind cut")
                        bind(target)

                    return latch, bind_at_cut

                def revocation_bind_at_cut(
                    port: object,
                    session: object,
                ) -> object:
                    if cut == "revocation-bind":
                        raise RuntimeError("synthetic revocation-bind cut")
                    return real_revocation_bind(port, session)  # type: ignore[arg-type]

                def record_cut_cleanup(
                    **components: object,
                ) -> list[BaseException]:
                    cut_cleanups.append(components)
                    return real_cleanup(**components)  # type: ignore[arg-type]

                with mock.patch.object(
                    local_trust,
                    "WindowsLocalAuthorizationDomainOwner",
                    return_value=cut_owner,
                ), mock.patch.object(
                    local_trust,
                    "_compose_agent_execution_authorization_grant_producer",
                    side_effect=compose_at_cut,
                ), mock.patch.object(
                    local_trust,
                    "_new_grant_authentication_latch",
                    side_effect=latch_factory_at_cut,
                ), mock.patch.object(
                    local_trust._OriginalIssuerRevocationPort,
                    "bind_session",
                    new=revocation_bind_at_cut,
                ), mock.patch.object(
                    local_trust,
                    "_cleanup_components",
                    side_effect=record_cut_cleanup,
                ):
                    with self.assertRaisesRegex(RuntimeError, cut):
                        attempt_composition(
                            identity_adapter=cut_identity_adapter,
                            human_approval_adapter=cut_human_adapter,
                        )

                self.assertEqual(len(cut_cleanups), 1)
                cut_cleanup = cut_cleanups[0]
                expected_session = (
                    None if cut == "owner-acquire" else cut_session
                )
                self.assertIs(cut_cleanup["session"], expected_session)
                self.assertEqual(
                    cut_session.close_calls,
                    0 if cut == "owner-acquire" else 1,
                )
                acquired_pair = cut in {"latch-bind", "revocation-bind"}
                self.assertIs(
                    cut_cleanup["producer"],
                    producer if acquired_pair else None,
                )
                self.assertEqual(pair_state.closed, acquired_pair)
                if cut == "adapter-bind":
                    captured_state = cut_identity_adapter.captured_state
                    self.assertIsNotNone(captured_state)
                    self.assertTrue(captured_state.closed)
                if acquired_pair:
                    self.assertIsNone(
                        authentication_port.authenticate_grant(object())
                    )
                self.assertEqual(cut_cleanup["latch"]._state, "closed")
                self.assertTrue(cut_cleanup["revocation_port"]._closed)

        primary = RuntimeError("synthetic primary failure")
        cleanup = RuntimeError("synthetic cleanup failure")
        with mock.patch.object(
            local_trust,
            "WindowsLocalAuthorizationDomainOwner",
            side_effect=primary,
        ), mock.patch.object(
            local_trust,
            "_cleanup_components",
            return_value=[cleanup],
        ):
            with self.assertRaises(BaseExceptionGroup) as caught:
                attempt_composition()
        self.assertEqual(caught.exception.exceptions, (primary, cleanup))


@unittest.skipUnless(os.name == "nt", "real AIO-049 owner is Windows-only")
class LocalOperationalTrustWindowsTests(_NoExecutionMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.probe = _ExecutionProbe()
        self.harness = _WindowsHarness(self)

    def tearDown(self) -> None:
        self.assert_no_execution()

    @property
    def coordinator(self) -> LocalOperationalTrustCoordinator:
        assert self.harness.coordinator is not None
        return self.harness.coordinator

    def _assert_admitted(
        self,
        result: object,
        run: AgentExecutionRun,
        *,
        outcome: str = "newly_admitted",
    ) -> object:
        self.assertIs(type(result), AgentExecutionDispatchAdmissionStoreResult)
        self.assertEqual(result.outcome.value, outcome)
        self.assertIsNotNone(result.admission)
        self.assertEqual(result.admission.grant.run, run)
        self.assertEqual(result.admission.tool_binding.run, run)
        self.assertEqual(result.admission.tool_binding.tool_id, TOOL_ID)
        self.assertIs(
            result.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.NO_RETRY_NEEDED,
        )
        self.probe.observe_binding(result.admission.tool_binding)
        return result.admission

    def _assert_rejected(
        self,
        result: object,
        *,
        outcome: object | None = None,
        retry_disposition: object | None = None,
    ) -> None:
        if type(result) is AgentExecutionAuthorizationGrantProductionResult:
            self.assertIsNone(result.presentation)
            self.assertNotIn(
                result.outcome.value,
                {"issued", "existing_exact_issuance"},
            )
            if outcome is not None:
                self.assertIs(result.outcome, outcome)
            if retry_disposition is not None:
                self.assertIs(result.retry_disposition, retry_disposition)
            return
        self.assertIs(type(result), AgentExecutionDispatchAdmissionStoreResult)
        self.assertIsNone(result.admission)
        self.assertNotIn(
            result.outcome,
            {
                AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
                AgentExecutionDispatchAdmissionStoreOutcome.
                EXISTING_EXACT_ADMISSION,
                AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
                AgentExecutionDispatchAdmissionStoreOutcome.
                EXISTING_EXACT_REVOCATION,
                AgentExecutionDispatchAdmissionStoreOutcome.
                NO_EXISTING_ADMISSION,
            },
        )
        if outcome is not None:
            self.assertIs(result.outcome, outcome)
        if retry_disposition is not None:
            self.assertIs(result.retry_disposition, retry_disposition)

    def _assert_pre_run_registry_rejection(
        self,
        *,
        runtime_option_id: str,
        environment_id: str,
        operation_id: str,
        outcome: _AgentOperationToolRegistryOutcome,
    ) -> None:
        built = _build_trusted_agent_operation_tool_registry_snapshot(
            (
                _make_aeo_native_repository_file_read_registration(
                    RUNTIME_ID,
                    ENVIRONMENT_ID,
                ),
            )
        )
        self.assertIs(built.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIsNotNone(built.snapshot)
        selected = _select_agent_operation_tool_route(
            built.snapshot,
            route=_AgentOperationToolRoute(
                runtime_option_id,
                environment_id,
                operation_id,
            ),
        )
        self.assertIs(selected.outcome, outcome)
        self.assertIs(
            selected.retry_disposition,
            _AgentOperationToolRegistryRetryDisposition.NEW_RUN_REQUIRED,
        )
        self.assertIsNone(selected.selected_route)

    def _human_call(
        self,
        run: AgentExecutionRun,
        *,
        principal: object | None = None,
        proof: object | None = None,
    ) -> object:
        if principal is None or proof is None:
            principal, proof = self.harness.human_authority(run)
        return self.coordinator.admit(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )

    def _human_call_with_captured_aio047_result(
        self,
        run: AgentExecutionRun,
        *,
        principal: object | None = None,
        proof: object | None = None,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        session = self.coordinator._session
        session_type = type(session)
        original_admit = session_type.admit
        captured: list[AgentExecutionDispatchAdmissionStoreResult] = []

        def capture_result(instance: object, presentation: object) -> object:
            result = original_admit(instance, presentation)
            captured.append(result)
            return result

        with mock.patch.object(session_type, "admit", new=capture_result):
            result = self._human_call(
                run,
                principal=principal,
                proof=proof,
            )

        self.assertEqual(len(captured), 1)
        self.assertIs(result, captured[0])
        return captured[0]

    def test_focused_fresh_admission_result_is_returned_unchanged(self) -> None:
        run = _make_run("run::focused-fresh-pass-through")
        result = self._human_call_with_captured_aio047_result(run)
        self._assert_admitted(result, run)

    def test_focused_historical_admission_result_is_returned_unchanged(
        self,
    ) -> None:
        run = _make_run("run::focused-historical-pass-through")
        principal, proof = self.harness.human_authority(run)
        self._assert_admitted(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            run,
        )
        result = self._human_call_with_captured_aio047_result(
            run,
            principal=principal,
            proof=proof,
        )
        self._assert_admitted(
            result,
            run,
            outcome="existing_exact_admission",
        )

    def test_focused_aio047_integrity_failure_is_returned_unchanged(
        self,
    ) -> None:
        run = _make_run("run::focused-integrity-pass-through")
        principal, proof = self.harness.human_authority(run)
        session = self.coordinator._session
        session_type = type(session)
        original_produce = LocalOperationalTrustCoordinator._produce
        original_revalidate = session_type._revalidate
        drift_armed = False

        def produce_then_arm_drift(instance: object, **kwargs: object) -> object:
            nonlocal drift_armed
            result = original_produce(instance, **kwargs)
            drift_armed = True
            return result

        def revalidate_with_drift(instance: object) -> object:
            if instance is session and drift_armed:
                raise windows_owner.AuthorizationDomainOwnershipIntegrityError(
                    "synthetic identity/generation drift"
                )
            return original_revalidate(instance)

        with mock.patch.object(
            LocalOperationalTrustCoordinator,
            "_produce",
            new=produce_then_arm_drift,
        ), mock.patch.object(
            session_type,
            "_revalidate",
            new=revalidate_with_drift,
        ):
            result = self._human_call_with_captured_aio047_result(
                run,
                principal=principal,
                proof=proof,
            )

        self._assert_rejected(
            result,
            outcome=AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RETRY_AFTER_REMEDIATION
            ),
        )

    def test_focused_other_aio047_failure_is_returned_unchanged(self) -> None:
        run = _make_run(
            "run::focused-other-failure-pass-through",
            runtime_option_id="runtime::focused-untrusted-route",
        )
        result = self._human_call_with_captured_aio047_result(run)
        self._assert_rejected(
            result,
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )
        self.assertIsNot(
            result.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        )

    def test_01_exact_human_approval(self) -> None:
        run = _make_run()
        self._assert_admitted(self._human_call(run), run)

    def test_02_exact_policy_allow(self) -> None:
        run = _make_run("run::policy-allow")
        principal, proof = self.harness.policy_authority(run, decision="allow")
        result = self.coordinator.admit(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        self._assert_admitted(result, run)

    def test_03_policy_deny(self) -> None:
        run = _make_run("run::policy-deny")
        principal, proof = self.harness.policy_authority(run, decision="deny")
        result = self.coordinator.admit(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        self._assert_rejected(
            result,
            outcome=AgentExecutionAuthorizationGrantProductionOutcome.POLICY_DENIED,
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_POLICY_DECISION
            ),
        )

    def test_04_expired_authority(self) -> None:
        run = _make_run("run::expired-authority")
        now = self.harness.clock.now_utc()
        principal, proof = self.harness.human_authority(
            run,
            valid_from=now - timedelta(minutes=10),
            valid_until=now - timedelta(minutes=1),
        )
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_AUTHORITY_DECISION
            ),
        )

    def test_05_run_changed_after_proof(self) -> None:
        original = _make_run("run::authority-subject")
        changed = _make_run("run::changed-after-authority")
        principal, proof = self.harness.human_authority(original)
        self._assert_rejected(
            self.coordinator.admit(
                run=changed,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                APPROVAL_SUBJECT_MISMATCH
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_HUMAN_APPROVAL
            ),
        )

    def test_06_fabricated_grant(self) -> None:
        run = _make_run("run::fabricated-grant")
        fabricated = AgentExecutionAuthorizationGrant(
            "grant::fabricated",
            run,
            DOMAIN_ID,
            "human",
            "human::synthetic",
            "fabricated::provenance",
            "2026-01-15T12:00:00Z",
            "2026-01-15T12:05:00Z",
        )
        result = self.coordinator._session.admit(fabricated)
        self._assert_rejected(
            result,
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def _foreign_presentation(
        self,
        *,
        domain_id: str,
        generation: int,
        suffix: str,
    ) -> object:
        foreign = _WindowsHarness(
            self,
            domain_id=domain_id,
            generation=generation,
            ledger_id=f"ledger-instance::{suffix}",
        )
        run = _make_run(f"run::{suffix}")
        principal, proof = foreign.human_authority(run)
        assert foreign.coordinator is not None
        production, presentation = foreign.coordinator._produce(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        self.assertIn(
            production.outcome.value,
            {"issued", "existing_exact_issuance"},
        )
        self.assertIsNotNone(presentation)
        foreign.suspend()
        return presentation

    def test_07_foreign_presentation(self) -> None:
        presentation = self._foreign_presentation(
            domain_id=DOMAIN_ID,
            generation=1,
            suffix="foreign-presentation",
        )
        self._assert_rejected(
            self.coordinator._session.admit(presentation),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_08_wrong_domain(self) -> None:
        presentation = self._foreign_presentation(
            domain_id="authorization-domain::foreign",
            generation=1,
            suffix="wrong-domain",
        )
        self._assert_rejected(
            self.coordinator._session.admit(presentation),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_09_wrong_generation(self) -> None:
        presentation = self._foreign_presentation(
            domain_id=DOMAIN_ID,
            generation=2,
            suffix="wrong-generation",
        )
        self._assert_rejected(
            self.coordinator._session.admit(presentation),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_10_ownership_lost(self) -> None:
        run = _make_run("run::ownership-lost")
        principal, proof = self.harness.human_authority(run)
        self.coordinator._session.fence()
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                DOMAIN_NOT_OWNED
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_SESSION_AUTHORITY
            ),
        )

    def test_11_fenced_or_closed_session(self) -> None:
        run = _make_run("run::session-closed")
        principal, proof = self.harness.human_authority(run)
        self.coordinator._session.close()
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                DOMAIN_NOT_OWNED
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_SESSION_AUTHORITY
            ),
        )

    def test_12_unknown_tool_route(self) -> None:
        self._assert_pre_run_registry_rejection(
            runtime_option_id="runtime::unknown",
            environment_id="environment::unknown",
            operation_id=OPERATION_ID,
            outcome=_AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE,
        )
        run = _make_run(
            "run::unknown-route",
            runtime_option_id="runtime::unknown",
            environment_id="environment::unknown",
        )
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_15_runtime_mismatch(self) -> None:
        run = _make_run(
            "run::runtime-mismatch",
            runtime_option_id="runtime::foreign",
        )
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_16_environment_mismatch(self) -> None:
        run = _make_run(
            "run::environment-mismatch",
            environment_id="environment::foreign",
        )
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_17_operation_mismatch(self) -> None:
        self._assert_pre_run_registry_rejection(
            runtime_option_id=RUNTIME_ID,
            environment_id=ENVIRONMENT_ID,
            operation_id="write_file",
            outcome=_AgentOperationToolRegistryOutcome.OPERATION_MISMATCH,
        )
        approved_run = _make_run("run::operation-approved")
        run = _make_run("run::operation-mismatch", operation_id="write_file")
        principal, proof = self.harness.human_authority(approved_run)
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=AgentExecutionAuthorizationGrantProductionOutcome.INVALID_RUN,
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )

    def test_18_resource_widening(self) -> None:
        exact = _make_run("run::exact-resource")
        wider = _make_run(
            "run::wider-resource",
            resource="synthetic",
        )
        principal, proof = self.harness.human_authority(exact)
        self._assert_rejected(
            self.coordinator.admit(
                run=wider,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                APPROVAL_SUBJECT_MISMATCH
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_HUMAN_APPROVAL
            ),
        )

    def test_19_contradictory_binding_run(self) -> None:
        run = _make_run("run::binding-subject")
        contradictory = _make_run("run::contradictory-binding")
        binding = AgentOperationToolBinding(contradictory, TOOL_ID)
        with mock.patch.object(
            TrustedAgentOperationToolBindingResolver,
            "resolve_tool_binding",
            return_value=binding,
        ):
            self._assert_rejected(
                self._human_call(run),
                outcome=AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                retry_disposition=(
                    AgentExecutionDispatchAdmissionStoreRetryDisposition.
                    DO_NOT_RETRY_SAME_REQUEST
                ),
            )

    def test_20_expected_run_mismatch(self) -> None:
        run = _make_run("run::expected")
        other = _make_run(
            "run::not-expected",
            resource="synthetic/other-input.txt",
        )
        self.harness.fresh_source.use_override = True
        self.harness.fresh_source.override = _make_parent_inputs(other)
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RECOLLECT_FRESH_STATE
            ),
        )

    def test_21_fresh_source_rejections(self) -> None:
        cases = (
            ("missing", None, None),
            ("invalid", object(), None),
            ("unavailable", None, RuntimeError("fresh source unavailable")),
            ("unsatisfied", None, None),
        )
        for label, value, failure in cases:
            with self.subTest(case=label):
                run = _make_run(f"run::fresh-rejection-{label}")
                self.harness.fresh_source.use_override = failure is None
                self.harness.fresh_source.override = (
                    _make_unsatisfied_parent_inputs(run)
                    if label == "unsatisfied"
                    else value
                )
                self.harness.fresh_source.failure = failure
                self._assert_rejected(
                    self._human_call(run),
                    outcome=(
                        AgentExecutionDispatchAdmissionStoreOutcome.
                        UNSATISFIED_PREREQUISITES
                    ),
                    retry_disposition=(
                        AgentExecutionDispatchAdmissionStoreRetryDisposition.
                        RECOLLECT_FRESH_STATE
                    ),
                )
                self.harness.fresh_source.failure = None

    def test_22_invalid_execution_mode(self) -> None:
        self.harness.mode_resolver.mode = "invalid-mode"
        run = _make_run("run::invalid-mode")
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                RECOLLECT_FRESH_STATE
            ),
        )

    def test_23_original_issuer_revocation(self) -> None:
        run = _make_run("run::revocation")
        principal, proof = self.harness.human_authority(run)
        provenance = "revocation::synthetic"
        revocation_proof = self.harness.revocation.issue(
            run=run,
            domain_identity=self.coordinator._domain_identity,
            provenance_reference=provenance,
        )
        revoked = self.coordinator.revoke(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
            original_issuer_proof=revocation_proof,
            provenance_reference=provenance,
        )
        self.assertIs(type(revoked), AgentExecutionDispatchAdmissionStoreResult)
        self.assertIs(
            revoked.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        )
        self.assertIs(
            revoked.retry_disposition,
            AgentExecutionDispatchAdmissionStoreRetryDisposition.NO_RETRY_NEEDED,
        )
        self.assertIsNone(revoked.admission)
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=AgentExecutionDispatchAdmissionStoreOutcome.REVOKED,
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )
        self.assertEqual(self.harness.revocation.validation_calls, 1)

    def test_24_expired_grant(self) -> None:
        run = _make_run("run::expired-grant")
        principal, proof = self.harness.human_authority(run)
        original = LocalOperationalTrustCoordinator._produce

        def produce_then_expire(instance: object, **kwargs: object) -> object:
            result = original(instance, **kwargs)
            self.harness.clock.advance(timedelta(hours=1))
            return result

        with mock.patch.object(
            LocalOperationalTrustCoordinator,
            "_produce",
            new=produce_then_expire,
        ):
            self._assert_rejected(
                self.coordinator.admit(
                    run=run,
                    authenticated_principal=principal,
                    authority_proof=proof,
                ),
                outcome=AgentExecutionDispatchAdmissionStoreOutcome.EXPIRED,
                retry_disposition=(
                    AgentExecutionDispatchAdmissionStoreRetryDisposition.
                    DO_NOT_RETRY_SAME_REQUEST
                ),
            )

    def test_25_exact_admission_retry(self) -> None:
        run = _make_run("run::admission-retry")
        principal, proof = self.harness.human_authority(run)
        first = self.coordinator.admit(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        second = self.coordinator.admit(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        admission = self._assert_admitted(first, run)
        retried = self._assert_admitted(
            second,
            run,
            outcome="existing_exact_admission",
        )
        self.assertEqual(retried, admission)
        self.assertEqual(self.harness.fresh_source.calls, 1)

    def test_26_restart_boundary(self) -> None:
        run = _make_run("run::restart-boundary")
        principal, proof = self.harness.human_authority(run)
        production, presentation = self.coordinator._produce(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        self.assertIsNotNone(presentation)
        self._assert_admitted(self.coordinator._session.admit(presentation), run)
        ledger = self.harness.configuration.database_path
        self.assertGreater(ledger.stat().st_size, 0)
        self.harness.restart()
        self.assertTrue(ledger.is_file())
        self._assert_rejected(
            self.coordinator._session.load_authoritative_admission(presentation),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )
        self.assertEqual(self.harness.fresh_source.calls, 0)
        self.assertIn(
            production.outcome.value,
            {"issued", "existing_exact_issuance"},
        )

    def test_28_corrupt_ledger(self) -> None:
        run = _make_run("run::before-corruption")
        self._assert_admitted(self._human_call(run), run)
        self.harness.close()
        self.harness.configuration.database_path.write_bytes(b"not-a-sqlite-ledger")
        with self.assertRaises(SqliteAdmissionStoreIntegrityError):
            self.harness._install_adapters_and_compose()

    def test_29_no_tool_fallback(self) -> None:
        self._assert_pre_run_registry_rejection(
            runtime_option_id="runtime::no-fallback",
            environment_id="environment::no-fallback",
            operation_id=OPERATION_ID,
            outcome=_AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE,
        )
        run = _make_run(
            "run::no-fallback",
            runtime_option_id="runtime::no-fallback",
            environment_id="environment::no-fallback",
        )
        self._assert_rejected(
            self._human_call(run),
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )
        self.assertEqual(self.harness.fresh_source.calls, 0)

    def test_30_option_substitution(self) -> None:
        original = _make_run("run::original-option")
        principal, proof = self.harness.human_authority(original)
        substitutions = (
            _make_run(
                "run::substituted-runtime",
                runtime_option_id="runtime::substituted",
            ),
            _make_run(
                "run::substituted-option",
                option_id="inference::substituted",
            ),
        )
        for changed in substitutions:
            with self.subTest(run_id=changed.run_id):
                self._assert_rejected(
                    self.coordinator.admit(
                        run=changed,
                        authenticated_principal=principal,
                        authority_proof=proof,
                    ),
                    outcome=(
                        AgentExecutionAuthorizationGrantProductionOutcome.
                        APPROVAL_SUBJECT_MISMATCH
                    ),
                    retry_disposition=(
                        AgentExecutionAuthorizationGrantRetryDisposition.
                        RETRY_WITH_FRESH_HUMAN_APPROVAL
                    ),
                )

    def test_34_pre_admission_retry(self) -> None:
        run = _make_run("run::production-retry")
        principal, proof = self.harness.human_authority(run)
        first_result, first_presentation = self.coordinator._produce(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        second_result, second_presentation = self.coordinator._produce(
            run=run,
            authenticated_principal=principal,
            authority_proof=proof,
        )
        self.assertEqual(first_result.outcome.value, "issued")
        self.assertEqual(second_result.outcome.value, "existing_exact_issuance")
        self.assertIs(first_presentation, second_presentation)

    def test_35_binding_has_no_behavior(self) -> None:
        run = _make_run("run::binding-only")
        admission = self._assert_admitted(self._human_call(run), run)
        binding = admission.tool_binding
        self.assertFalse(callable(binding))
        self.assertFalse(hasattr(binding, "invoke"))
        self.assertFalse(hasattr(binding, "open"))
        self.assertEqual(binding.tool_id, TOOL_ID)

    def test_36_inter_lease_fence(self) -> None:
        def exercise_gap(
            harness: _WindowsHarness,
            *,
            label: str,
            transition: str,
        ) -> None:
            coordinator = harness.coordinator
            assert coordinator is not None
            session = coordinator._session
            run = _make_run(f"run::inter-lease-{label}")
            principal, proof = harness.human_authority(run)
            original_produce = LocalOperationalTrustCoordinator._produce
            session_type = type(session)
            original_revalidate = session_type._revalidate
            drift_armed = False

            def revalidate_with_drift(candidate: object) -> object:
                if candidate is session and drift_armed:
                    raise windows_owner.AuthorizationDomainOwnershipIntegrityError(
                        "synthetic identity/generation drift"
                    )
                return original_revalidate(candidate)

            def produce_then_transition(
                instance: object,
                **kwargs: object,
            ) -> object:
                nonlocal drift_armed
                result = original_produce(instance, **kwargs)
                if transition == "fence":
                    session.fence()
                elif transition == "close":
                    session.close()
                else:
                    drift_armed = True
                return result

            production_patch = mock.patch.object(
                LocalOperationalTrustCoordinator,
                "_produce",
                new=produce_then_transition,
            )
            try:
                if transition == "drift":
                    with mock.patch.object(
                        session_type,
                        "_revalidate",
                        new=revalidate_with_drift,
                    ), production_patch:
                        result = coordinator.admit(
                            run=run,
                            authenticated_principal=principal,
                            authority_proof=proof,
                        )
                else:
                    with production_patch:
                        result = coordinator.admit(
                            run=run,
                            authenticated_principal=principal,
                            authority_proof=proof,
                        )
                expected_outcome = (
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    INTEGRITY_FAILURE
                    if transition == "drift"
                    else AgentExecutionDispatchAdmissionStoreOutcome.
                    STORAGE_UNAVAILABLE
                )
                expected_retry = (
                    AgentExecutionDispatchAdmissionStoreRetryDisposition.
                    RETRY_AFTER_REMEDIATION
                    if transition == "drift"
                    else AgentExecutionDispatchAdmissionStoreRetryDisposition.
                    RETRY_EXACT_REQUEST
                )
                self._assert_rejected(
                    result,
                    outcome=expected_outcome,
                    retry_disposition=expected_retry,
                )
                self.assertEqual(harness.fresh_source.calls, 0)
            finally:
                harness.suspend()

        cases = (
            ("fence", "fence", None),
            (
                "close",
                "close",
                (
                    "authorization-domain::aio-053-gap-close",
                    "ledger-instance::aio-053-gap-close",
                ),
            ),
            (
                "identity-generation-drift",
                "drift",
                (
                    "authorization-domain::aio-053-gap-drift",
                    "ledger-instance::aio-053-gap-drift",
                ),
            ),
        )
        for label, transition, identity in cases:
            with self.subTest(case=label):
                harness = self.harness
                if identity is not None:
                    domain_id, ledger_id = identity
                    harness = _WindowsHarness(
                        self,
                        domain_id=domain_id,
                        ledger_id=ledger_id,
                    )
                exercise_gap(
                    harness,
                    label=label,
                    transition=transition,
                )

    def test_37_close_race(self) -> None:
        run = _make_run("run::close-race")
        principal, proof = self.harness.human_authority(run)
        produced = threading.Event()
        release = threading.Event()
        original = LocalOperationalTrustCoordinator._produce
        outcomes: list[object] = []
        failures: list[BaseException] = []

        def blocking_produce(instance: object, **kwargs: object) -> object:
            result = original(instance, **kwargs)
            produced.set()
            if not release.wait(5):
                raise TimeoutError("test did not release the in-flight operation")
            return result

        def admit_worker() -> None:
            try:
                outcomes.append(
                    self.coordinator.admit(
                        run=run,
                        authenticated_principal=principal,
                        authority_proof=proof,
                    )
                )
            except BaseException as error:
                failures.append(error)

        close_started = threading.Event()

        def close_worker() -> None:
            close_started.set()
            try:
                self.coordinator.close()
            except BaseException as error:
                failures.append(error)

        with mock.patch.object(
            LocalOperationalTrustCoordinator,
            "_produce",
            new=blocking_produce,
        ):
            operation_thread = threading.Thread(target=admit_worker)
            operation_thread.start()
            self.assertTrue(produced.wait(5))
            close_thread = threading.Thread(target=close_worker)
            close_thread.start()
            self.assertTrue(close_started.wait(5))
            with self.coordinator._condition:
                for _ in range(200):
                    if self.coordinator._state == "closing":
                        break
                    self.coordinator._condition.wait(0.01)
                self.assertEqual(self.coordinator._state, "closing")
            with self.assertRaises(RuntimeError):
                self.coordinator.admit(
                    run=run,
                    authenticated_principal=principal,
                    authority_proof=proof,
                )
            release.set()
            operation_thread.join(5)
            close_thread.join(5)
        self.assertFalse(operation_thread.is_alive())
        self.assertFalse(close_thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(len(outcomes), 1)
        self._assert_admitted(outcomes[0], run)

    def test_38_operation_after_close(self) -> None:
        run = _make_run("run::after-close")
        principal, proof = self.harness.human_authority(run)
        self.coordinator.close()
        with self.assertRaises(RuntimeError):
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            )

    def test_39_foreign_adapter_epoch(self) -> None:
        run = _make_run("run::foreign-epoch")
        principal, proof = self.harness.human_authority(run)
        self.harness.identity.rotate_epoch()
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=principal,
                authority_proof=proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                UNAUTHENTICATED_PRINCIPAL
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_PRINCIPAL_AND_AUTHORITY
            ),
        )

    def test_40_issuer_disabled_between_leases(self) -> None:
        run = _make_run("run::issuer-disabled")
        principal, proof = self.harness.human_authority(run)
        original = LocalOperationalTrustCoordinator._produce

        def produce_then_disable(instance: object, **kwargs: object) -> object:
            result = original(instance, **kwargs)
            self.harness.issuer_state.enabled = False
            return result

        with mock.patch.object(
            LocalOperationalTrustCoordinator,
            "_produce",
            new=produce_then_disable,
        ):
            self._assert_rejected(
                self.coordinator.admit(
                    run=run,
                    authenticated_principal=principal,
                    authority_proof=proof,
                ),
                outcome=(
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    UNAUTHENTICATED_GRANT
                ),
                retry_disposition=(
                    AgentExecutionDispatchAdmissionStoreRetryDisposition.
                    DO_NOT_RETRY_SAME_REQUEST
                ),
            )

    def test_41_stale_revocation_proof(self) -> None:
        run = _make_run("run::stale-revocation")
        principal, approval = self.harness.human_authority(run)
        provenance = "revocation::stale"
        proof = self.harness.revocation.issue(
            run=run,
            domain_identity=self.coordinator._domain_identity,
            provenance_reference=provenance,
        )
        self.harness.revocation.rotate_epoch()
        result = self.coordinator.revoke(
            run=run,
            authenticated_principal=principal,
            authority_proof=approval,
            original_issuer_proof=proof,
            provenance_reference=provenance,
        )
        self._assert_rejected(
            result,
            outcome=(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT
            ),
            retry_disposition=(
                AgentExecutionDispatchAdmissionStoreRetryDisposition.
                DO_NOT_RETRY_SAME_REQUEST
            ),
        )
        self.assertEqual(self.harness.fresh_source.calls, 0)

    def test_42_foreign_authority_subjects(self) -> None:
        run = _make_run("run::authority-subjects")
        first_principal, human_proof = self.harness.human_authority(run)
        foreign_principal = self.harness.identity.mint(
            issuer_kind="human",
            issuer_id="human::foreign",
            now=self.harness.clock.now_utc(),
        )
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=foreign_principal,
                authority_proof=human_proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                APPROVAL_SUBJECT_MISMATCH
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_HUMAN_APPROVAL
            ),
        )
        policy_principal, policy_proof = self.harness.policy_authority(
            run,
            decision="allow",
        )
        self._assert_rejected(
            self.coordinator.admit(
                run=run,
                authenticated_principal=first_principal,
                authority_proof=policy_proof,
            ),
            outcome=(
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            ),
            retry_disposition=(
                AgentExecutionAuthorizationGrantRetryDisposition.
                RETRY_WITH_FRESH_AUTHORITY_DECISION
            ),
        )
        self.assertIsNot(policy_principal, first_principal)


class LocalOperationalTrustScenarioMapTests(unittest.TestCase):
    def test_locked_scenario_map_is_exact_and_resolvable(self) -> None:
        self.assertEqual(tuple(SCENARIO_TEST_MAP), tuple(range(1, 43)))
        classes = {
            LocalOperationalTrustContractTests.__name__:
                LocalOperationalTrustContractTests,
            LocalOperationalTrustWindowsTests.__name__:
                LocalOperationalTrustWindowsTests,
        }
        self.assertEqual(len(set(SCENARIO_TEST_MAP.values())), 42)
        for scenario, reference in SCENARIO_TEST_MAP.items():
            with self.subTest(scenario=scenario):
                class_name, method_name = reference.split(".", 1)
                self.assertTrue(callable(getattr(classes[class_name], method_name)))


if __name__ == "__main__":
    unittest.main()
