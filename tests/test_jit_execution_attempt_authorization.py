"""72 explicit F identities; synthetic authority, disposable ledger, no effects.

Imports reuse reviewed predecessor fixture builders. No test discovery,
operational owner registry, target file access or invocation is performed.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
from datetime import timedelta
from pathlib import Path
import pickle
from threading import Barrier, Event, Thread
from unittest import TestCase, mock

from engineering_orchestration import _jit_execution_attempt_authorization as jit
from engineering_orchestration import agent_execution_authorization_grant_producer as prod
from engineering_orchestration import agent_operation_tool_registry as registry
from engineering_orchestration.agent_operation_tool_resolver import TrustedAgentOperationToolBindingResolver
from tests import test_dispatch_claim_lease_foundation as claims
from tests import test_agent_execution_authorization_grant_producer as proofs
from tests import test_agent_action_prerequisite as prereqs


class _Cooperative:
    def _jit_mutable_partitions(self):
        return (self,)

    def _bind_jit_authority_guard(self, guard):
        if getattr(self, "_jit_guard", None) is not None:
            raise RuntimeError("partition already bound")
        self._jit_guard = guard

    def change(self, kind, **values):
        with self._jit_guard.mutation_scope(self, kind):
            for name, value in values.items():
                setattr(self, name, value)


class _Identity(_Cooperative, proofs._IdentityAdapter):
    pass


class _Human(_Cooperative, proofs._HumanApprovalAdapter):
    pass


class _Policy(_Cooperative, proofs._PolicyDecisionAdapter):
    pass


class _Issuer(_Cooperative, proofs._IssuerStateAuthority):
    def disable(self):
        with self._jit_guard.mutation_scope(self, "issuer_disable"):
            super().disable()

    def enable(self):
        with self._jit_guard.mutation_scope(self, "issuer_enable"):
            super().enable()


class _Entitlement(_Cooperative, proofs._EntitlementPolicy):
    pass


class _Facts(_Cooperative):
    def __init__(self, run):
        c = run.contract
        responsibility = (c.task_id, c.workflow_id, c.stage_id, c.role_id)
        self.inputs = dict(
            candidate_result=replace(prereqs.candidate(
                actor_id=c.actor_id, runtime_option_id=c.runtime_option_id,
                option_id=c.option_id), responsibility_key=responsibility),
            requirement=prereqs.OperationRequirement(c.operation_id, c.resource),
            capability_result=prereqs.capability(runtime_option_id=c.runtime_option_id),
            permission_result=prereqs.permission(runtime_option_id=c.runtime_option_id,
                environment_id=c.environment_id, resource=c.resource),
            authorization_result=prereqs.authorization(
                responsibility_key=responsibility, actor_id=c.actor_id,
                runtime_option_id=c.runtime_option_id, option_id=c.option_id,
                environment_id=c.environment_id, resource=c.resource),
            environment_id=c.environment_id)
        self.actual_mode = c.execution_mode
        self.required_mode = c.execution_mode

    def _jit_current_inputs(self):
        return dict(self.inputs), self.actual_mode, self.required_mode


class _Rig:
    def __init__(self, test, *, retired=False, missing=False, issuer_kind=None, short_grant=False):
        f = claims.DispatchClaimLeaseTests("runTest")
        f.setUp()
        test.addCleanup(f.doCleanups)
        self.fixture = f
        if issuer_kind is not None or short_grant:
            def admit(index, store):
                run = claims.fixture.make_run(f"run::{index}")
                grant = claims.fixture.make_grant(bound_run=run, grant_id=f"grant::{index}",
                    domain_id=store.configuration.authorization_domain_id)
                if issuer_kind is not None:
                    grant = replace(grant, issuer_kind=issuer_kind)
                if short_grant:
                    grant = replace(grant, expires_at=claims.subject._canonical_decision_time(
                        claims.T+timedelta(seconds=1))[1])
                binding = claims.fixture.make_binding(bound_run=run)
                result = store.admit_or_return_existing(claims.outbox._request(
                    store.configuration, grant, binding))
                test.assertEqual(result.outcome.value, "newly_admitted", result.detail)
                return grant
            f._admit = admit
        self.facade = f._setup()
        self.claim = f._claim()
        self.session = self.facade._session
        self.store = f.store
        self.clock = f.clock
        self.grant = f.grants[0]
        self.run = self.grant.run
        self.binding_value = claims.fixture.make_binding(bound_run=self.run)
        self.identity = _Identity()
        self.human = _Human()
        self.policy = _Policy()
        self.issuer = _Issuer()
        self.entitlement = _Entitlement()
        self.producer_binding = prod._compose_agent_execution_authorization_grant_producer(
            owned_session=self.session, identity_adapter=self.identity,
            human_approval_adapter=self.human, policy_decision_adapter=self.policy,
            issuer_state_authority=self.issuer, issuer_entitlement_policy=self.entitlement,
            lifetime_policy=proofs.AgentExecutionAuthorizationGrantLifetimePolicy(
                timedelta(minutes=2), timedelta(minutes=10), "jit-fixture"),
            utc_clock=self.clock, grant_id_source=proofs._GrantIdSource())
        c = self.run.contract
        route = registry._AgentOperationToolRoute(c.runtime_option_id, c.environment_id, c.operation_id)
        registration = registry._AgentOperationToolRegistration(
            c.runtime_option_id, c.environment_id, c.operation_id,
            self.binding_value.tool_id,
            registry._AgentOperationToolImplementationSelector.AEO_NATIVE_REPOSITORY_FILE_READ_V1)
        built = registry._build_trusted_agent_operation_tool_registry_snapshot(
            (replace(registration, runtime_option_id=c.runtime_option_id+"-other"),)
                if missing else (registration,),
            retired_routes=(route,) if retired else ())
        if built.snapshot is None:
            raise AssertionError(built.outcome)
        self.resolver = TrustedAgentOperationToolBindingResolver(built.snapshot)
        self.facts = _Facts(self.run)
        self.a = jit._compose_jit_execution_attempt_authorizer(
            session=self.session, producer_binding=self.producer_binding,
            resolver=self.resolver, current_source=self.facts)
        self.subject = self.a.subject(self.claim, self.facade._executor, self.run, self.binding_value)
        self.principal = self.identity.mint(
            issuer_kind=self.grant.issuer_kind, issuer_id=self.grant.issuer_id,
            authentication_session_id="jit-test", valid_from=claims.T-timedelta(seconds=1),
            valid_until=claims.T+timedelta(minutes=5))
        self.decision = self.new_decision()
        test.addCleanup(self.a.close)

    def new_decision(self):
        args = dict(provenance_reference="jit-test", valid_from=claims.T-timedelta(seconds=1),
                    valid_until=claims.T+timedelta(minutes=5))
        if self.grant.issuer_kind == "human":
            args["approval_session_id"] = "jit-test"
        else:
            args.update(decision="allow", policy_revision="jit-test")
        return self.a.mint_entry_decision(self.subject, self.principal, **args)

    def prepare(self, subject=None, decision=None):
        return self.a.prepare(subject or self.subject, self.principal, decision or self.decision)

    def cap(self, test):
        result = self.prepare()
        test.assertEqual(result.outcome, "prepared", result)
        return result.capability

    def consume(self, cap):
        return self.a._consume_assessment(cap, self.principal, self.decision)


class FoundationTests(TestCase):
    def _assert_sec_057_3(self, r, cap):
        """F04: reject alternate keys and keep reconstructed Claim facts shared."""
        subject, a = r.subject, r.a
        key = subject.physical_key
        components = {f.name: getattr(subject, f.name) for f in fields(subject)}
        self.assertNotIn("key", components)
        self.assertNotIn("physical_key", components)
        malformed_keys = (
            (*key, "extra"), key[:-1], (key[1], key[0], *key[2:]),
            (*key, key[-1]), (*key[:-1], str(key[-1])), key[:2],
        )
        for malformed in malformed_keys:
            with self.subTest(attack="independent key", representation=malformed):
                # Exact former exploit, plus direct construction and derived-key substitution.
                for name in ("key", "physical_key"):
                    with self.assertRaises(TypeError):
                        replace(subject, **{name: malformed})
                    with self.assertRaises(TypeError):
                        jit._Subject(**components, **{name: malformed})
                self.assertEqual(len(a.cells), 1)
                self.assertIs(a.cells[key].capability, cap)

        malformed_components = (
            ("ledger_identity", (subject.ledger_identity,)),
            ("store", id(subject.store)),
            ("dispatch_identity", subject.dispatch_identity[:-1]),
            ("dispatch_identity", (*subject.dispatch_identity, "extra")),
            ("dispatch_identity", list(subject.dispatch_identity)),
            ("dispatch_identity", (subject.dispatch_identity[1], subject.dispatch_identity[0],
                                   *subject.dispatch_identity[2:])),
            ("claim_id", subject.claim_id.encode("ascii")),
            ("lease_generation", True), ("lease_generation", str(subject.lease_generation)),
        )
        for name, value in malformed_components:
            with self.subTest(attack="component type/shape", component=name):
                with self.assertRaises((TypeError, ValueError)):
                    replace(subject, **{name: value})
                with self.assertRaises((TypeError, ValueError)):
                    jit._Subject(**{**components, name: value})

        copied = copy.copy(subject)
        for name in ("key", "physical_key"):
            with self.assertRaises((AttributeError, TypeError)):
                setattr(copied, name, (*key, "extra"))
            with self.assertRaises(AttributeError):
                object.__setattr__(copied, name, (*key, "extra"))

        # A malformed manually allocated subject cannot enter the Producer seam.
        incomplete = object.__new__(jit._Subject)
        before = len(a.state.jit_entry_proofs)
        with self.assertRaises((AttributeError, TypeError, jit._JitFailure)):
            prod._mint_jit_entry_decision(a.state, a.guard, incomplete, r.principal)
        self.assertEqual(len(a.state.jit_entry_proofs), before)
        self.assertEqual(a.prepare(incomplete, r.principal, r.decision).outcome, "integrity_failure")
        self.assertEqual(len(a.cells), 1)

        for equivalent in (jit._Subject(**components), replace(subject), copied):
            self.assertEqual(equivalent.physical_key, key)
            retry = r.prepare(equivalent)
            self.assertEqual(retry.outcome, "exact_retry")
            self.assertIs(retry.capability, cap)
            self.assertIs(a.cells[equivalent.physical_key], cap._cell)

        changed_proof = r.new_decision()
        second = r.prepare(jit._Subject(**components), changed_proof)
        self.assertEqual(second.outcome, "already_prepared")
        self.assertIsNone(second.capability)
        self.assertEqual(len(a.cells), 1)
        attempts = (r.consume(cap), r.consume(retry.capability))
        self.assertEqual(sum(result.outcome == "assessed" for result in attempts), 1)
        self.assertEqual(attempts[1].outcome, "terminal_capability")
        self.assertEqual(cap._cell.state, "UNCERTAIN")
        self.assertEqual(r.prepare().outcome, "terminal_capability")
        self.assertEqual(len(a.cells), 1)

    def run_scenario(self, n):
        identity = n
        n = {57: 59, 58: 60, 59: 58, 60: 61, 61: 62, 62: 63,
             63: 64, 64: 65, 65: 66, 66: 67, 67: 68, 68: 69,
             69: 70, 70: 71, 71: 72, 72: 73}.get(n, n)
        r = _Rig(self, retired=identity == 58, missing=identity == 57,
                 issuer_kind="human" if identity in (37,44) else "policy" if identity in (38,45) else None,
                 short_grant=identity == 31)
        a = r.a
        if n in (1, 4, 37, 38, 49, 55):
            cap = r.cap(self)
            self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
            self.assertEqual(r.producer_binding.producer._state.issuances, {})
            self.assertIs(cap._cell.subject.binding, r.binding_value)
            self.assertIs(cap._cell.subject.run, r.run)
            if n == 4:
                self._assert_sec_057_3(r, cap)
        elif n in (2, 36):
            cap = r.cap(self)
            r.clock.value = claims.T+timedelta(seconds=5)
            self.assertEqual(r.fixture._renew(r.claim).outcome, "newly_renewed")
            self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
        elif n in (3, 27, 28):
            cap = r.cap(self)
            r.clock.value = claims.T+timedelta(seconds=30)
            other = r.fixture._other()
            newer = r.fixture._claim(3, other)
            self.assertEqual(newer.lease_generation, 2)
            self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, "stale_generation")
            if n == 3:
                subject = a.subject(newer, other._executor, r.run, r.binding_value)
                decision_args = dict(provenance_reference="new-claim", valid_from=claims.T,
                                     valid_until=claims.T+timedelta(minutes=5))
                if r.grant.issuer_kind == "human":
                    decision_args["approval_session_id"] = "new-claim"
                else:
                    decision_args.update(decision="allow", policy_revision="new-claim")
                new_decision = a.mint_entry_decision(subject, r.principal, **decision_args)
                self.assertEqual(a.prepare(subject, r.principal, new_decision).outcome, "prepared")
        elif n in (5, 6, 7):
            cap = r.cap(self)
            if n == 5:
                s = replace(r.subject, run=replace(r.run, run_id="different"))
            elif n == 6:
                s = replace(r.subject, binding=replace(r.binding_value, tool_id="different"))
            else:
                s = replace(r.subject, executor=r.fixture._other()._executor)
            self.assertEqual(r.prepare(s).outcome, "subject_conflict")
            self.assertEqual(len(a.cells), 1)
            self.assertIs(a.cells[r.subject.physical_key].capability, cap)
            if n == 7:
                other = _Rig(self)
                substituted = replace(other.subject, executor=other.fixture._other()._executor)
                args = dict(provenance_reference="substituted", valid_from=claims.T,
                    valid_until=claims.T+timedelta(minutes=5))
                if other.grant.issuer_kind == "human":
                    args["approval_session_id"] = "substituted"
                else:
                    args.update(decision="allow", policy_revision="substituted")
                proof = other.a.mint_entry_decision(substituted, other.principal, **args)
                self.assertEqual(other.prepare(substituted, proof).outcome, "wrong_executor")
        elif n == 8:
            s = replace(r.subject, dispatch_identity=("wrong-domain", *r.subject.dispatch_identity[1:]))
            self.assertNotEqual(r.prepare(s).outcome, "prepared")
        elif n == 9:
            for name, value in (("ledger_identity", replace(r.session.identity, domain_generation=99)),
                                ("store", r.store)):
                other = _Rig(self)
                subject = replace(other.subject, **{name: value})
                # Entry-purpose membership is exact too: no foreign ledger binds.
                self.assertNotEqual(other.prepare(subject).outcome, "prepared")
        elif n == 10:
            counterfeit = copy.copy(r.facade._executor._executor_id)
            with self.assertRaises((ValueError, TypeError)):
                a.subject(r.claim, counterfeit, r.run, r.binding_value)
        elif n in (11, 20):
            entered, release = Event(), Event()
            results = []
            original = r.store._fault
            def hold(point):
                if point == "jit.after_begin":
                    entered.set()
                    if not release.wait(5):
                        raise AssertionError("bounded synchronization timed out")
                original(point)
            with mock.patch.object(r.store, "_fault", side_effect=hold):
                worker = Thread(target=lambda: results.append(r.prepare()))
                worker.start()
                self.assertTrue(entered.wait(5))
                try:
                    self.assertEqual(r.prepare().outcome, "preparation_in_progress")
                finally:
                    release.set()
                    worker.join(5)
                self.assertFalse(worker.is_alive())
            self.assertEqual(results[0].outcome, "prepared")
            self.assertEqual(len(a.cells), 1)
            if n == 20:
                for cut in ("jit.before_commit", "jit.after_commit_before_response"):
                    other = _Rig(self)
                    def interrupt(point):
                        if point == cut:
                            raise OSError("publication interrupted")
                    with mock.patch.object(other.store, "_fault", side_effect=interrupt):
                        result = other.prepare()
                    self.assertIsNone(result.capability)
                    self.assertNotEqual(other.a.cells[other.subject.physical_key].state, "PREPARED")
                    self.assertEqual(other.prepare().outcome, "terminal_capability")
        elif n in (12, 16, 17):
            cap = r.cap(self)
            result = r.prepare()
            self.assertEqual(result.outcome, "exact_retry")
            self.assertIs(result.capability, cap)
        elif n in (13, 14):
            cap = r.cap(self)
            alias = cap
            barrier = Barrier(3)
            results = []
            def consume(value):
                barrier.wait(5)
                results.append(r.consume(value))
            workers = [Thread(target=consume, args=(value,)) for value in (cap, alias)]
            for t in workers:
                t.start()
            barrier.wait(5)
            for t in workers:
                t.join(5)
                self.assertFalse(t.is_alive())
            self.assertEqual(sum(x.outcome == "assessed" for x in results), 1)
            self.assertEqual(cap._cell.state, "UNCERTAIN")
            self.assertEqual(a.verify(alias, r.principal, r.decision).outcome, "terminal_capability")
        elif n in (15, 18):
            cap = r.cap(self)
            changed = r.new_decision()
            self.assertEqual(r.prepare(decision=changed).outcome, "already_prepared")
            self.assertIs(a.cells[r.subject.physical_key].capability, cap)
            self.assertIsNone(r.prepare(decision=object()).capability)
        elif n == 19:
            self.assertEqual(a.prepare(None, r.principal, r.decision).outcome, "invalid_input")
            self.assertEqual(a.cells, {})
            r.cap(self)
        elif n == 21:
            cap = r.cap(self)
            a.abandon(cap)
            self.assertEqual(cap._cell.state, "ABANDONED")
            self.assertEqual(r.prepare().outcome, "terminal_capability")
        elif n == 22:
            cap = r.cap(self)
            r.issuer.disable()
            self.assertEqual(r.consume(cap).outcome, "issuer_disabled")
            self.assertEqual(cap._cell.state, "REJECTED")
            self.assertIsNone(r.prepare().capability)
        elif n == 23:
            cap = r.cap(self)
            r.consume(cap)
            self.assertEqual(r.consume(cap).outcome, "terminal_capability")
            self.assertEqual(r.prepare().outcome, "terminal_capability")
            with cap._cell.lock:
                with self.assertRaises(jit._JitFailure):
                    cap._cell._transition("PREPARED")
            # CONSUMED is an implemented terminal state, not Entry success.
            mechanics = jit._Cell(r.subject, ())
            with mechanics.lock:
                for target in ("PREPARED", "CONSUMING", "CONSUMED"):
                    mechanics._transition(target)
                with self.assertRaises(jit._JitFailure):
                    mechanics._transition("PREPARED")
        elif n in (24, 65):
            cap = r.cap(self)
            with mock.patch.object(jit.os, "getpid", return_value=a.pid+1):
                self.assertNotEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
            foreign = claims.adapter._create_owned_dispatch_claim_lease(r.session)._executor
            with self.assertRaises((ValueError, jit._JitFailure)):
                a.subject(r.claim, foreign, r.run, r.binding_value)
            if n == 65:
                other = _Rig(self)
                self.assertEqual(other.a.verify(cap, r.principal, r.decision).outcome, "invalid_capability")
        elif n in (25, 26, 32):
            cap = r.cap(self) if n == 32 else None
            r.clock.value = claims.T+timedelta(seconds=30 if n != 25 else 31)
            result = a.verify(cap, r.principal, r.decision) if cap else r.prepare()
            self.assertEqual(result.outcome, "expired_claim")
        elif n == 29:
            s = replace(r.subject, claim_id=claims.token(999))
            self.assertEqual(r.prepare(s).outcome, "claim_not_found")
        elif n == 30:
            historical = r.facade.query(r.claim.claim_id)
            self.assertEqual(a.verify(historical, r.principal, r.decision).outcome, "invalid_capability")
        elif n == 31:
            # Consumed Grant expiry does not become a continuing entry window.
            cap = r.cap(self)
            r.clock.value = claims.T+timedelta(seconds=2)
            self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
            with mock.patch.object(prod, "_prepare_attempt", side_effect=AssertionError("no issuance")):
                self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
        elif n == 33:
            r.cap(self)
            self.assertEqual(r.prepare().outcome, "exact_retry")
        elif n in (34, 35):
            cap = r.cap(self)
            if n == 34:
                r.clock.value = claims.T-timedelta(microseconds=1)
                expected = "clock_regression"
            else:
                r.clock.exception = RuntimeError("clock unavailable")
                expected = "clock_failure"
            self.assertEqual(a.verify(cap, r.principal, r.decision).outcome, expected)
            if n == 35:
                for value in (claims.T.replace(tzinfo=None), object()):
                    other = _Rig(self)
                    other.clock.value = value
                    self.assertEqual(other.prepare().outcome, "clock_failure")
        elif n == 39:
            public_producer = r.producer_binding.producer
            offered = public_producer.produce(run=r.run,
                authenticated_principal=r.principal, authority_proof=r.decision)
            self.assertEqual(offered.outcome.value, "authority_proof_invalid")
            args = dict(principal=r.principal, run=r.run,
                provenance_reference="issuance", valid_from=claims.T,
                valid_until=claims.T+timedelta(minutes=5))
            if r.grant.issuer_kind == "human":
                issuance = r.human.mint(approval_session_id="issuance", **args)
            else:
                issuance = r.policy.mint(decision="allow", policy_revision="issuance", **args)
            self.assertEqual(r.prepare(decision=issuance).outcome, "invalid_entry_proof")
            # Guard attachment preserves ordinary public issuance and close.
            issued = public_producer.produce(run=r.run,
                authenticated_principal=r.principal, authority_proof=issuance)
            self.assertEqual(issued.outcome.value, "issued")
            public_producer.close()
            self.assertEqual(public_producer.produce(run=r.run,
                authenticated_principal=r.principal,
                authority_proof=issuance).outcome.value, "producer_closed")
        elif n == 40:
            registered = a.state.jit_entry_proofs[id(r.decision)]
            a.state.jit_entry_proofs[id(r.decision)] = (registered[0], replace(r.subject,
                run=replace(r.run, run_id="foreign")), registered[2], registered[3])
            self.assertEqual(r.prepare().outcome, "invalid_entry_proof")
        elif n == 41:
            r.issuer.disable()
            self.assertEqual(r.prepare().outcome, "issuer_disabled")
        elif n == 42:
            r.issuer.disable()
            r.issuer.enable()
            self.assertEqual(r.prepare().outcome, "issuer_disabled")
        elif n in (43, 44, 45):
            source = r.identity if n == 43 else r.human if r.grant.issuer_kind == "human" else r.policy
            source.change("principal_invalidate" if n == 43 else "decision_invalidate", valid=False)
            self.assertNotEqual(r.prepare().outcome, "prepared")
            other = _Rig(self, issuer_kind="human" if n == 44 else "policy")
            source = other.identity if n == 43 else other.human if n == 44 else other.policy
            source.change("epoch_revision", epoch=object())
            self.assertNotEqual(other.prepare().outcome, "prepared")
            if n == 45:
                third = _Rig(self, issuer_kind="policy")
                deny = third.a.mint_entry_decision(third.subject, third.principal,
                    decision="deny", policy_revision="denied", provenance_reference="denied",
                    valid_from=claims.T, valid_until=claims.T+timedelta(minutes=5))
                self.assertEqual(third.prepare(decision=deny).outcome, "policy_denied")
        elif n == 46:
            cap = r.cap(self)
            entered, release, mutated = Event(), Event(), Event()
            results = []
            def hold(point):
                if point == "jit.before_commit":
                    entered.set()
                    if not release.wait(5):
                        raise AssertionError("bounded synchronization timed out")
            with mock.patch.object(r.store, "_fault", side_effect=hold):
                worker = Thread(target=lambda: results.append(r.consume(cap)))
                worker.start()
                self.assertTrue(entered.wait(5))
                mutation = Thread(target=lambda: (r.issuer.disable(), mutated.set()))
                mutation.start()
                try:
                    self.assertFalse(mutated.wait(.05))
                finally:
                    release.set()
                    worker.join(5)
                    mutation.join(5)
                self.assertFalse(worker.is_alive())
                self.assertFalse(mutation.is_alive())
            self.assertEqual(results[0].outcome, "assessed")
            self.assertTrue(mutated.is_set())
            self.assertEqual(cap._cell.state, "UNCERTAIN")
            # Every declared mutable partition uses the same guard revision.
            for source, kind in ((r.identity, "logout"), (r.human, "withdrawal"),
                    (r.policy, "policy_revision"), (r.issuer, "reenable"),
                    (r.facts, "availability"), (r.facts, "applicability"),
                    (r.facts, "compatibility"), (r.facts, "runtime_capability"),
                    (r.facts, "resource_permission"), (r.facts, "effective_mode")):
                before = a.guard.revision
                with a.guard.mutation_scope(source, kind):
                    pass
                self.assertEqual(a.guard.revision, before+1)
        elif n == 47:
            foreign = _Rig(self)
            foreign.facts._jit_mutable_partitions = None
            with self.assertRaises(jit._JitFailure) as error:
                jit._compose_jit_execution_attempt_authorizer(
                    session=foreign.session, producer_binding=foreign.producer_binding,
                    resolver=foreign.resolver, current_source=foreign.facts)
            self.assertEqual(error.exception.outcome, "unsupported_source")
        elif n == 48:
            cap = r.cap(self)
            with self.assertRaises(RuntimeError):
                with a.guard.mutation_scope(r.facts, "permission"):
                    raise RuntimeError("ambiguous source write")
            self.assertNotEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
        elif n in (50, 51, 52, 53, 54):
            if n == 50:
                r.facts.inputs["candidate_result"] = replace(prereqs.candidate(
                    prereqs.AgentExecutionCandidatePrerequisiteOutcome.BLOCKED),
                    responsibility_key=r.facts.inputs["candidate_result"].responsibility_key)
            elif n == 51:
                r.facts.inputs["capability_result"] = prereqs.capability(
                    prereqs.RuntimeOperationCapabilityState.UNKNOWN,
                    runtime_option_id=r.run.contract.runtime_option_id)
            elif n == 52:
                r.facts.inputs["permission_result"] = prereqs.permission(
                    prereqs.EnvironmentOperationPermissionState.DENIED,
                    runtime_option_id=r.run.contract.runtime_option_id,
                    environment_id=r.run.contract.environment_id, resource=r.run.contract.resource)
            elif n == 53:
                r.facts.actual_mode = "lite"
            else:
                r.facts.inputs["candidate_result"] = object()
            self.assertNotEqual(r.prepare().outcome, "prepared")
            if n in (50, 51, 52):
                other = _Rig(self)
                if n == 50:
                    other.facts.inputs["candidate_result"] = replace(prereqs.candidate(
                        prereqs.AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED),
                        responsibility_key=other.facts.inputs["candidate_result"].responsibility_key)
                elif n == 51:
                    other.facts.inputs["capability_result"] = prereqs.capability(
                        prereqs.RuntimeOperationCapabilityState.ABSENT,
                        runtime_option_id=other.run.contract.runtime_option_id)
                else:
                    other.facts.inputs["permission_result"] = prereqs.permission(
                        prereqs.EnvironmentOperationPermissionState.UNKNOWN,
                        runtime_option_id=other.run.contract.runtime_option_id,
                        environment_id=other.run.contract.environment_id,
                        resource=other.run.contract.resource)
                self.assertNotEqual(other.prepare().outcome, "prepared")
        elif n in (56, 57):
            changed = replace(r.binding_value, tool_id="wrong") if n == 56 else replace(
                r.binding_value, run=replace(r.run, contract=replace(r.run.contract, resource="other.txt")))
            if n == 56:
                changed_subject = a.subject(r.claim, r.facade._executor, r.run, changed)
                self.assertEqual(r.prepare(changed_subject).outcome, "wrong_binding")
                other = _Rig(self)
                changed_run = replace(other.run, contract=replace(
                    other.run.contract, resource="other.txt"))
                with self.assertRaises(jit._JitFailure):
                    other.a.subject(other.claim, other.facade._executor, other.run,
                        replace(other.binding_value, run=changed_run))
            else:
                with self.assertRaises(jit._JitFailure):
                    a.subject(r.claim, r.facade._executor, r.run, changed)
        elif n in (58, 59, 60):
            if n == 58:
                s = replace(r.subject, binding=replace(r.binding_value, tool_id="wrong"))
                self.assertEqual(r.prepare(s).outcome, "wrong_binding")
                c = r.run.contract
                route = registry._AgentOperationToolRoute(
                    c.runtime_option_id, c.environment_id, c.operation_id)
                for field in ("runtime_option_id", "environment_id", "operation_id"):
                    changed = replace(route, **{field: getattr(route, field)+"-foreign"})
                    selected = registry._select_agent_operation_tool_route(a.snapshot, route=changed)
                    self.assertIsNone(selected.selected_route)
            else:
                self.assertNotEqual(r.prepare().outcome, "prepared")
                if n == 60:
                    self.assertEqual(r.resolver.resolve(r.grant).binding, r.binding_value)
        elif n == 61:
            object.__setattr__(r.resolver, "_snapshot", object())
            self.assertEqual(r.prepare().outcome, "corrupt_snapshot")
            c = r.run.contract
            invalid = registry._AgentOperationToolRegistration(
                c.runtime_option_id, c.environment_id, c.operation_id,
                r.binding_value.tool_id, "unknown-selector")
            self.assertIsNone(registry._build_trusted_agent_operation_tool_registry_snapshot(
                (invalid,)).snapshot)
        elif n == 62:
            with self.assertRaises(TypeError):
                jit._ExecutionAttemptAuthorization()
            forged = object.__new__(jit._ExecutionAttemptAuthorization)
            self.assertEqual(a.verify(forged, r.principal, r.decision).outcome, "invalid_capability")
        elif n in (63, 64):
            cap = r.cap(self)
            for operation in ((copy.copy, copy.deepcopy) if n == 63 else (pickle.dumps,)):
                with self.assertRaises(TypeError):
                    operation(cap)
        elif n == 66:
            with self.assertRaises(jit._JitFailure):
                jit._compose_jit_execution_attempt_authorizer(
                    session=r.session, producer_binding=r.producer_binding,
                    resolver=r.resolver, current_source=r.facts)
            with self.assertRaises(TypeError):
                jit._JitAuthorizer(a.guard, r.resolver, r.facts)
        elif n == 67:
            cap = r.cap(self)
            a.close()
            self.assertNotEqual(a.verify(cap, r.principal, r.decision).outcome, "assessed")
            self.assertEqual(r.prepare().capability, None)
        elif n == 68:
            with mock.patch.object(r.store, "_verify_authoritative_connection",
                    side_effect=claims.subject.SqliteAdmissionStoreIntegrityError("synthetic corruption")):
                self.assertEqual(r.prepare().outcome, "integrity_failure")
        elif n == 69:
            for error, expected in ((claims.subject.SqliteAdmissionStoreIncompatibleSchemaError("v2"),
                                    "incompatible_schema"), (OSError("unavailable"), "storage_unavailable")):
                other = _Rig(self)
                with mock.patch.object(other.store, "_open_existing", side_effect=error):
                    self.assertEqual(other.prepare().outcome, expected)
        elif n == 70:
            with r.session.operation():
                with a.guard.read_scope():
                    with self.assertRaises(jit._JitFailure):
                        with a.guard.leaf():
                            r.identity.mint(issuer_kind="policy", issuer_id="x",
                                authentication_session_id="x", valid_from=claims.T,
                                valid_until=claims.T+timedelta(seconds=5))
                    with self.assertRaises(jit._JitFailure):
                        with a.guard.mutation_scope(r.facts, "permission"):
                            pass
        elif n == 71:
            original = claims.adapter._WindowsOwnedAuthorizationDomainSession._revalidate
            committed = [False]
            # Fault after a committed preparation but before owned disclosure.
            def fail(session):
                if committed[0]:
                    raise claims.integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError("post-check")
                original(session)
            def after_commit(point):
                if point == "jit.after_commit_before_response":
                    committed[0] = True
            with mock.patch.object(claims.adapter._WindowsOwnedAuthorizationDomainSession,
                                   "_revalidate", new=fail):
                with mock.patch.object(r.store, "_fault", side_effect=after_commit):
                    self.assertIsNone(r.prepare().capability)
            self.assertNotEqual(a.cells[r.subject.physical_key].state, "PREPARED")
        elif n == 72:
            cap = r.cap(self)
            before = r.fixture._counts()
            for result in (a.verify(cap, r.principal, r.decision), r.consume(cap)):
                self.assertIsNone(result.capability)
                self.assertFalse(hasattr(result, "entry_committed"))
            self.assertEqual(before, r.fixture._counts())
            tree = ast.parse(Path(jit.__file__).read_text(encoding="utf-8"))
            calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
            self.assertFalse(any(isinstance(x, ast.Attribute) and x.attr in (
                "execute", "connect", "read_bytes", "read_text", "open", "Popen", "run") for x in calls))
            self.assertEqual(jit.__all__, ())
        elif n == 73:
            before = r.fixture._snapshot(r.fixture.configuration.database_path) if hasattr(
                r.fixture, "_snapshot") else claims._snapshot(r.fixture.configuration.database_path)
            cap = r.cap(self)
            a.verify(cap, r.principal, r.decision)
            after = claims._snapshot(r.fixture.configuration.database_path)
            self.assertEqual(before[1], after[1])  # Claim/Renewal rows unchanged.
            self.assertEqual(jit.__all__, ())
            self.assertIsNone(r.consume(cap).capability)
        else:
            raise AssertionError("unmapped foundation identity")


def _scenario(number):
    def test(self):
        self.run_scenario(number)
    test.__name__ = f"test_F{number:02d}"
    return test


SCENARIO_TEST_MAP = {f"F{n:02d}": f"FoundationTests.test_F{n:02d}" for n in range(1, 73)}
for _number in range(1, 73):
    setattr(FoundationTests, f"test_F{_number:02d}", _scenario(_number))
