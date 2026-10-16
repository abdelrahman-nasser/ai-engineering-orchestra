"""Narrow local current-user authority composition for approved Alpha reads.

This trusted adapter binds fresh process-local proofs to exact new Runs. No
configuration, model text, persisted receipt or restored Result is authority.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets

from itru import agent_execution_candidate_prerequisite as candidate
from itru.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationEvidence as Evidence,
    AgentExecutionAuthorizationAuthorityKind as AuthorityKind,
    AgentExecutionAuthorizationState as AuthorizationState,
    AgentExecutionAuthorizationValidationResult as AuthorizationResult,
)
from itru.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation as Capability,
    RuntimeOperationCapabilityState as CapabilityState,
    RuntimeOperationCapabilityValidationResult as CapabilityResult,
)
from itru.environment_operation_permission import (
    EnvironmentOperationPermissionObservation as Permission,
    EnvironmentOperationPermissionState as PermissionState,
    EnvironmentOperationPermissionValidationResult as PermissionResult,
)
from itru.agent_execution_dispatch_admission_store import AgentActionPrerequisiteParentInputs
from itru.agent_execution_authorization_grant_producer import (
    AgentExecutionAuthorizationGrantLifetimePolicy, _new_binding,
)
from itru.local_operational_trust import _compose_local_operational_trust_coordinator, _build_native_resolver
from itru import windows_local_authorization_domain_owner as windows
from itru import _jit_execution_attempt_authorization as jit
from itru import _local_dispatch_claim_lease as lease
from itru import _native_repository_file_read as native
from itru._execution_entry_and_controlled_invocation import _ControlledInvocationCoordinator
from itru.agent_execution_journal import ExecutionJournalRecorder
from itru.sqlite_agent_execution_journal_store import (
    SqliteExecutionJournalStore, SqliteExecutionJournalConfiguration,
)
from itru.operation_requirement import OperationRequirement
from itru.role_catalog import load_role_catalog
from itru.workflow_catalog import WorkflowCatalog, WorkflowDefinition, WorkflowStage
from itru.assignment import Assignment
from itru.authorization_domain_ownership import AuthorizationDomainIdentity


class Clock:
    def now_utc(self):
        return datetime.now(timezone.utc)


class _Cooperative:
    def _jit_mutable_partitions(self):
        return (self,)

    def _bind_jit_authority_guard(self, guard):
        if hasattr(self, 'guard'):
            raise RuntimeError('authority adapter already bound')
        self.guard = guard


class _Identity(_Cooperative):
    def __init__(self, issuer):
        self.issuer, self.epoch, self.members = issuer, object(), {}

    def current_epoch(self):
        return self.epoch

    def _bind_authenticated_issuer_principal_minter(self, minter):
        self.minter = minter

    def validate_authenticated_principal(self, principal):
        return self.members.get(id(principal)) is principal

    def mint(self):
        now = datetime.now(timezone.utc)
        with self.guard.mutation_scope(self, 'principal_mint'):
            value = self.minter.mint(issuer_kind='human', issuer_id=self.issuer,
                authentication_session_id=secrets.token_hex(32),
                valid_from=now - timedelta(seconds=1), valid_until=now + timedelta(minutes=10))
            self.members[id(value)] = value
        return value


class _Human(_Cooperative):
    def __init__(self):
        self.epoch, self.members = object(), {}

    def current_epoch(self):
        return self.epoch

    def _bind_authenticated_human_approval_minter(self, minter):
        self.minter = minter

    def validate_authenticated_human_approval(self, value):
        return self.members.get(id(value)) is value

    def mint(self, principal, run, reference):
        now = datetime.now(timezone.utc)
        with self.guard.mutation_scope(self, 'proof_mint'):
            value = self.minter.mint(principal=principal, run=run,
                approval_session_id=secrets.token_hex(32), provenance_reference=reference,
                valid_from=now - timedelta(seconds=1), valid_until=now + timedelta(minutes=5),
                requested_lifetime=None)
            self.members[id(value)] = value
        return value

    def register_entry(self, value):
        with self.guard.mutation_scope(self, 'proof_mint'):
            self.members[id(value)] = value


class _Issuer(_Cooperative):
    def __init__(self, issuer):
        self.issuer, self.epoch = issuer, object()

    def observe_issuer_state(self, issuer_kind, issuer_id):
        return (issuer_kind == 'human' and issuer_id == self.issuer), self.epoch


class _Entitlement(_Cooperative):
    def __init__(self, cfg, runs, issuer):
        self.cfg, self.runs, self.issuer = cfg, runs, issuer

    def is_entitled(self, run, domain_identity, issuer_kind, issuer_id):
        return (self.runs.get(run.run_id) == run and issuer_kind == 'human'
                and issuer_id == self.issuer
                and domain_identity.authorization_domain_id == self.cfg['domain_id'])


class _Facts(_Cooperative):
    def __init__(self, cfg, runs, issuer, reference):
        self.cfg, self.runs, self.issuer, self.reference = cfg, runs, issuer, reference
        self.current = None
        roles = load_role_catalog(raise_on_error=True)
        self.roles = roles
        self.workflow = WorkflowCatalog(Path('.'), definitions={'standard-change': WorkflowDefinition(
            'standard-change', 'Standard Change', 'Govern explicit Alpha read work', [
                WorkflowStage('understand', 'Understand'),
                WorkflowStage('implement', 'Implement', ['software-engineer']),
                WorkflowStage('validate', 'Validate'),
                WorkflowStage('review', 'Review', ['reviewer'], human_control_checkpoint=True)],
            ['implementation'])})

    def parents(self, run):
        if self.runs.get(run.run_id) != run:
            raise ValueError('run was not approved in this process')
        c = run.contract
        assignment = Assignment(c.task_id, c.workflow_id, c.stage_id, c.role_id, c.actor_id)
        role = self.roles.definitions[c.role_id]
        assessed = candidate.assess_agent_execution_candidate_prerequisites(
            assignment, c.runtime_option_id, c.option_id,
            {'id': c.task_id, 'type': 'implementation', 'workflow': c.workflow_id},
            self.workflow, self.roles,
            [{'id': c.actor_id, 'kind': 'agent', 'competencies': role['required_capabilities']}],
            [candidate.ActorAvailabilityObservation(c.actor_id, candidate.AvailabilityState.AVAILABLE)],
            [candidate.ActorRuntimeApplicabilityEvidence(c.actor_id, c.runtime_option_id)],
            [candidate.AgentRuntimeOptionDefinition(c.runtime_option_id)],
            [candidate.InferenceOptionDefinition(c.option_id, self.cfg['provider']['kind'], self.cfg['provider']['model'])],
            [candidate.RuntimeInferenceCompatibilityEvidence(c.runtime_option_id, c.option_id)],
            [candidate.AgentRuntimeOptionAvailabilityObservation(c.runtime_option_id, candidate.AgentRuntimeOptionAvailabilityState.AVAILABLE)],
            [candidate.InferenceOptionAvailabilityObservation(c.option_id, candidate.InferenceOptionAvailabilityState.AVAILABLE)])
        if not assessed.valid or assessed.outcome.value != 'satisfied':
            raise ValueError('configured Alpha candidate does not satisfy prerequisites: ' + str(assessed.findings))
        evidence = Evidence(*assignment.key, c.actor_id, c.runtime_option_id, c.option_id,
            c.environment_id, c.operation_id, c.resource, AuthorityKind.HUMAN,
            self.issuer, self.reference, AuthorizationState.GRANTED)
        # These are scoped trusted-composition observations, not authority proofs.
        return AgentActionPrerequisiteParentInputs(assessed,
            OperationRequirement(c.operation_id, c.resource),
            CapabilityResult(True, (), (Capability(c.runtime_option_id, c.operation_id, CapabilityState.PRESENT),)),
            PermissionResult(True, (), (Permission(c.runtime_option_id, c.environment_id,
                c.operation_id, c.resource, PermissionState.ALLOWED),)),
            AuthorizationResult(True, (), (evidence,)), c.environment_id)

    def collect_fresh_parent_results(self, grant, binding):
        if grant.run != binding.run:
            raise ValueError('grant binding mismatch')
        return self.parents(grant.run)

    def resolve_effective_execution_mode(self, grant, binding):
        self.parents(grant.run)
        return 'deep'

    def _jit_current_inputs(self):
        p = self.parents(self.current)
        return {key: getattr(p, key) for key in asdict(p)}, 'deep', 'deep'


class _NoRevocation:
    def current_epoch(self):
        return self

    def validate_authenticated_original_issuer_revocation(self, *args, **kwargs):
        return False


class _Ids:
    def random_bytes(self, length):
        return secrets.token_bytes(length)


class AlphaExecution:
    def __init__(self, cfg, reference):
        if __import__('os').name != 'nt':
            raise OSError('controlled Developer Alpha execution requires Windows local NTFS')
        self.cfg, self.runs = cfg, {}
        self.trust = self.authorizer = self.root = None
        issuer = 'windows-user::' + windows._current_user_sid()
        self.identity, self.human = _Identity(issuer), _Human()
        self.facts = _Facts(cfg, self.runs, issuer, reference)
        try:
            self.trust = _compose_local_operational_trust_coordinator(
                authorization_domain_id=cfg['domain_id'], runtime_option_id=cfg['runtime_id'],
                environment_id=cfg['environment_id'], identity_adapter=self.identity,
                human_approval_adapter=self.human, policy_decision_adapter=None,
                issuer_state_authority=_Issuer(issuer),
                issuer_entitlement_policy=_Entitlement(cfg, self.runs, issuer),
                lifetime_policy=AgentExecutionAuthorizationGrantLifetimePolicy(
                    timedelta(minutes=5), timedelta(minutes=5), 'itru-alpha-v1'),
                clock=Clock(), grant_id_source=_Ids(), fresh_prerequisite_source=self.facts,
                execution_mode_resolver=self.facts, revocation_adapter=_NoRevocation())
            self.session = self.trust._session
            if self.session.identity != AuthorizationDomainIdentity(cfg['domain_id'], cfg['ledger_id'], 1):
                raise ValueError('configured authorization ledger identity mismatch')
            self.authorizer = jit._compose_jit_execution_attempt_authorizer(session=self.session,
                producer_binding=_new_binding(self.trust._producer._state),
                resolver=_build_native_resolver(runtime_option_id=cfg['runtime_id'], environment_id=cfg['environment_id']),
                current_source=self.facts)
            self.root = native._provision_trusted_root(session=self.session,
                environment_id=cfg['environment_id'], path=Path(cfg['workspace'])/'repository')
            self.dispatch = lease._create_owned_dispatch_claim_lease(self.session)
            directory = Path(cfg['workspace'])/'journal'
            conf = SqliteExecutionJournalConfiguration(directory/'journal.sqlite3', directory,
                                                       cfg['journal_id'], self.session.identity)
            self.journal = SqliteExecutionJournalStore(conf)
            recorder = ExecutionJournalRecorder(self.journal, self.session._store, metadata_authorized=True)
            self.invoker = _ControlledInvocationCoordinator(self.authorizer, self.root, journal=recorder)
        except BaseException:
            self.close()
            raise

    def approve_run(self, run):
        with self.authorizer.guard.mutation_scope(self.facts, 'approval'):
            self.runs[run.run_id] = run

    def invoke(self, run, reference):
        principal = self.identity.mint()
        proof = self.human.mint(principal, run, reference)
        admitted = self.trust.admit(run=run, authenticated_principal=principal, authority_proof=proof)
        if admitted.outcome.value != 'newly_admitted':
            raise RuntimeError('fresh admission failed: ' + admitted.outcome.value)
        binding = admitted.admission.tool_binding
        claim = self.dispatch.claim(secrets.token_hex(32)).claim
        if claim is None:
            raise RuntimeError('dispatch claim failed')
        subject = self.authorizer.subject(claim, self.dispatch._executor, run, binding)
        now = datetime.now(timezone.utc)
        decision = self.authorizer.mint_entry_decision(subject, principal,
            provenance_reference=reference, approval_session_id=secrets.token_hex(32),
            valid_from=now - timedelta(seconds=1), valid_until=now + timedelta(minutes=4))
        self.human.register_entry(decision)
        with self.authorizer.guard.mutation_scope(self.facts, 'current_inputs'):
            self.facts.current = run
        prepared = self.authorizer.prepare(subject, principal, decision)
        if prepared.outcome != 'prepared':
            raise RuntimeError('fresh JIT preparation failed: ' + prepared.outcome)
        return self.invoker.invoke(prepared.capability, principal, decision)

    def close(self):
        for component in (self.root, self.authorizer, self.trust):
            if component is not None:
                component.close()
