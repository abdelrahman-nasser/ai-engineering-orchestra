"""29 exact ITRU-060 scenarios on genuine owned, disposable native fixtures.

No discovery, external/hostile fixtures, privileged links or child executors.
Fault injection observes the original chain; no replacement pathname reader.
"""
from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import os
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest import mock
from uuid import uuid4

from itru import agent_execution_result as result
from itru import _execution_entry_and_controlled_invocation as entry
from itru import _native_repository_file_read as native
from itru import _jit_execution_attempt_authorization as jit
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from itru.authorization_domain_ownership import OwnedAuthorizationDomainSessionLostError
from tests import test_durable_execution_entry_and_controlled_invocation as original
from tests import test_local_operational_trust as integrated

RESOURCE = "fixtures/itru-060-read.bin"
DATA = b"ITRU-060 disposable synthetic nonsecret\n"


@unittest.skipUnless(os.name == "nt", "genuine owned native fixture requires Windows")
class ControlledResultScenarios(unittest.TestCase):
    def rig(self, data=DATA):
        harness = integrated._WindowsHarness
        ledger_id = "ledger::itru-060::" + uuid4().hex
        def fresh_harness(case):
            return harness(case, ledger_id=ledger_id)
        with mock.patch.object(integrated, "_WindowsHarness", side_effect=fresh_harness):
            rig = original._NativeRig(self, resource=RESOURCE, data=data)
        parent = Path(rig.h._temporary_directory.name).resolve()
        self.assertEqual(parent.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(parent.name.startswith("aio-053-local-trust-"))
        self.assertTrue(rig.repo.resolve().is_relative_to(parent))
        self.assertTrue(rig.h.root.resolve().is_relative_to(parent))
        self.assertEqual(integrated.windows_owner._local_appdata_path(), rig.h.root)
        print(f"ITRU060_FIXTURE {self._testMethodName} parent={parent} registry={rig.h.root} ledger={ledger_id}", flush=True)
        return rig

    def terminal(self, rig, expected, code=None):
        outcome = rig.invoke(self)
        self.assertEqual(outcome.entry_result.outcome, "entered")
        self.assertIs(outcome.result.execution_entry, outcome.entry_result.entry)
        self.assertIs(outcome.result.tool_binding, rig.binding_value)
        self.assertEqual(outcome.result.ledger_identity, rig.subject.ledger_identity)
        self.assertEqual(outcome.result.outcome, expected)
        self.assertTrue(result._is_authoritative_result(outcome.result))
        self.assertEqual(outcome.result.identity, (rig.subject.ledger_identity.ledger_instance_id,
                                                  *outcome.entry_result.entry.identity))
        self.assertEqual(original._count(rig), 1)
        self.assertIsNone(rig.coordinator._original)
        if code is None:
            self.assertIsNone(outcome.result.diagnostic)
            self.assertEqual(outcome.result.payload.data, outcome.invocation.data)
        else:
            self.assertIsNone(outcome.result.payload)
            self.assertIsNone(outcome.invocation.data)
            self.assertEqual(outcome.invocation.byte_count, 0)
            self.assertEqual(outcome.result.diagnostic.code, code)
        self.assertTrue(outcome.result._production.closed)
        self.assertIsNone(outcome.result._production.frame)
        self.assertIsNone(outcome.result._production.coordinator)
        canonical = tuple(getattr(outcome.result, name) for name in
                          ("ledger_identity", "execution_entry", "tool_binding",
                           "outcome", "payload", "diagnostic"))
        for state in (canonical, [None] * 6, {"outcome": "succeeded"}, None):
            with self.subTest(restoration=type(state).__name__), self.assertRaises(TypeError):
                outcome.result.__setstate__(state)
            self.assertTrue(all(getattr(outcome.result, name) is item for name, item in zip(
                ("ledger_identity", "execution_entry", "tool_binding", "outcome", "payload", "diagnostic"),
                canonical)))
            self.assertTrue(result._is_authoritative_result(outcome.result))
        with self.assertRaises(TypeError):
            outcome.result.__getstate__()
        component = outcome.result.payload or outcome.result.diagnostic
        state = [b"replacement", 11] if outcome.result.payload is not None else ["read_failure"]
        with self.assertRaises(TypeError):
            component.__setstate__(state)
        self.assertTrue(result._is_authoritative_result(outcome.result))
        return outcome

    def before(self, code):
        rig = self.rig()
        with mock.patch.object(rig.root._native, "open_component", side_effect=native._NativeFailure(code)), \
                mock.patch.object(rig.root._native, "read_data", side_effect=AssertionError("no data request")) as reads:
            self.terminal(rig, "failed_before_effect", code)
            reads.assert_not_called()

    def tamper_after_read(self, transform):
        rig = self.rig()
        cap = rig.cap(self)
        saved = cap._cell.subject
        reader = rig.root._native.read_data
        def changed(*args):
            data = reader(*args)
            cap._cell.subject = transform(saved)
            return data
        try:
            with mock.patch.object(rig.root._native, "read_data", side_effect=changed):
                with self.assertRaises(result._ResultIntegrityError) as caught:
                    rig.coordinator.invoke(cap, rig.principal, rig.decision)
            self.assertEqual(caught.exception.args, ("canonical Result integrity failure",))
            self.assertIsNone(caught.exception.__context__)
            self.assertEqual(original._count(rig), 1)
            self.assertEqual(cap._cell.state, "CONSUMED")
            self.assertIsNone(rig.coordinator._original)
        finally:
            cap._cell.subject = saved

    def test_R01_success(self):
        outcome = self.terminal(self.rig(), "succeeded")
        self.assertEqual(outcome.result.payload, result.RepositoryFileReadResultPayload(DATA, len(DATA)))
        for operation in (copy.copy, copy.deepcopy, pickle.dumps):
            with self.assertRaises(TypeError):
                operation(outcome.result)
        with self.assertRaises(FrozenInstanceError):
            outcome.result.outcome = "effect_ambiguous"
        reconstructed = object.__new__(result.AgentExecutionResult)
        for name in ("ledger_identity", "execution_entry", "tool_binding", "outcome",
                     "payload", "diagnostic", "_production"):
            object.__setattr__(reconstructed, name, getattr(outcome.result, name))
        self.assertFalse(result._is_authoritative_result(reconstructed))
        self.assertTrue(result._is_authoritative_result(outcome.result))
        object.__setattr__(outcome.result, "outcome", "effect_ambiguous")
        self.assertFalse(result._is_authoritative_result(outcome.result))
        object.__setattr__(outcome.result, "outcome", "succeeded")
        self.assertFalse(result._is_authoritative_result(outcome.result))

    def test_R02_empty_success(self):
        rig = self.rig(b"")
        reader = rig.root._native.read_data
        with mock.patch.object(rig.root._native, "read_data", wraps=reader) as reads:
            outcome = self.terminal(rig, "succeeded")
        self.assertEqual(outcome.result.payload, result.RepositoryFileReadResultPayload(b"", 0))
        self.assertEqual(reads.call_count, 1)
        self.assertEqual(reads.call_args.args[1:3], (0, 1))
        object.__setattr__(outcome.result.payload, "byte_count", False)
        self.assertFalse(result._is_authoritative_result(outcome.result))
        object.__setattr__(outcome.result.payload, "byte_count", 0)
        self.assertFalse(result._is_authoritative_result(outcome.result))

    def test_R03_maximum_success(self):
        data = b"x" * 65536
        rig = self.rig(data)
        reader = rig.root._native.read_data
        with mock.patch.object(rig.root._native, "read_data", wraps=reader) as reads:
            outcome = self.terminal(rig, "succeeded")
        self.assertEqual(outcome.result.payload.data, data)
        self.assertEqual(reads.call_count, 17)
        self.assertLessEqual(sum(call.args[2] for call in reads.call_args_list), 65537)

    def test_R04_pre_read_size_limit(self):
        rig = self.rig(b"x" * 65537)
        with mock.patch.object(rig.root._native, "read_data", side_effect=AssertionError("no data request")) as reads:
            self.terminal(rig, "failed_before_effect", "size_limit_exceeded")
            reads.assert_not_called()

    def test_R05_missing_resource(self):
        self.terminal(self.rig(None), "failed_before_effect", "resource_missing")

    def test_R06_containment_rejection(self):
        self.before("containment_rejected")

    def test_R07_adapter_unavailable(self):
        rig = self.rig()
        with mock.patch.object(rig.coordinator, "_availability", return_value=False):
            self.terminal(rig, "failed_before_effect", "adapter_unavailable")

    def test_R08_proven_pre_content_read_failure(self):
        self.before("read_failure")

    def test_R09_proven_pre_content_resource_changed(self):
        self.before("resource_changed")

    def test_R10_guard_lost_before_start(self):
        rig = self.rig()
        with mock.patch.object(rig.coordinator, "_availability", side_effect=jit._JitFailure("guard_lost")):
            self.terminal(rig, "failed_before_effect", "guard_lost")

    def test_R11_ownership_lost_before_start(self):
        rig = self.rig()
        with mock.patch.object(rig.coordinator, "_availability", side_effect=jit._JitFailure("ownership_lost")):
            self.terminal(rig, "failed_before_effect", "ownership_lost")

    def test_R12_post_request_failure_codes(self):
        for code in ("read_failure", "adapter_unavailable"):
            with self.subTest(code=code):
                rig = self.rig()
                with mock.patch.object(rig.root._native, "read_data", side_effect=native._NativeFailure(code)):
                    outcome = self.terminal(rig, "effect_ambiguous", code)
                object.__setattr__(outcome.result.diagnostic, "code", "resource_changed")
                self.assertFalse(result._is_authoritative_result(outcome.result))
                object.__setattr__(outcome.result.diagnostic, "code", code)
                self.assertFalse(result._is_authoritative_result(outcome.result))

    def test_R13_final_metadata_changed(self):
        rig = self.rig()
        metadata = rig.root._native.metadata
        final_calls = []
        def changed(handle, directory=False):
            item = metadata(handle, directory)
            if not directory:
                final_calls.append(True)
                if len(final_calls) == 2:
                    return replace(item, write_time=item.write_time + 1)
            return item
        with mock.patch.object(rig.root._native, "metadata", side_effect=changed):
            self.terminal(rig, "effect_ambiguous", "resource_changed")

    def test_R14_outer_ownership_postcheck(self):
        rig = self.rig()
        reader, revalidate = rig.root._native.read_data, type(rig.session)._revalidate
        read = []
        def original_read(*args):
            data = reader(*args)
            read.append(True)
            return data
        def lost(session):
            if session is rig.session and read:
                raise OwnedAuthorizationDomainSessionLostError("synthetic postcheck loss")
            return revalidate(session)
        with mock.patch.object(rig.root._native, "read_data", side_effect=original_read), \
                mock.patch.object(type(rig.session), "_revalidate", new=lost):
            self.terminal(rig, "effect_ambiguous", "effect_ambiguous")

    def test_R15_cleanup_dominates_no_content(self):
        rig = self.rig()
        close = native._Handle.close
        def uncertain(handle):
            close(handle)
            raise OSError("synthetic cleanup uncertainty")
        with mock.patch.object(rig.root._native, "metadata", side_effect=native._NativeFailure("containment_rejected")), \
                mock.patch.object(native._Handle, "close", new=uncertain), \
                mock.patch.object(rig.root._native, "read_data", side_effect=AssertionError("no content")) as reads:
            self.terminal(rig, "effect_ambiguous", "effect_ambiguous")
            reads.assert_not_called()

    def test_R18_reconstructed_entry_is_not_acknowledgement(self):
        rig = self.rig()
        fake = entry._ExecutionEntry(rig.claim.identity, rig.claim.claim_id,
            rig.claim.executor_instance_id, rig.claim.lease_generation, "2026-09-23T10:30:00.000000Z", 0)
        cap = rig.cap(self)
        with mock.patch.object(rig.store, "_enter_execution", return_value=entry._EntryResult("entered", fake, False)), \
                mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            with self.assertRaises(result._ResultIntegrityError):
                rig.coordinator.invoke(cap, rig.principal, rig.decision)
            opens.assert_not_called()
        self.assertEqual(original._count(rig), 0)
        with self.assertRaises((result._ResultIntegrityError, AttributeError)):
            result._begin_result_production(rig.coordinator, cap._cell)

    def test_R19_same_run_id_changed_contract(self):
        for field, value in (("resource", "fixtures/other.bin"), ("execution_mode", "standard")):
            with self.subTest(field=field):
                self.tamper_after_read(lambda s: replace(s, run=replace(s.run, contract=replace(s.run.contract, **{field: value}))))
        rig = self.rig()
        binding_run = replace(rig.run, contract=replace(rig.run.contract))
        self.assertEqual(binding_run, rig.run)
        self.assertIsNot(binding_run, rig.run)
        self.assertIsNot(binding_run.contract, rig.run.contract)
        rig.binding_value = replace(rig.binding_value, run=binding_run)
        rig.subject = replace(rig.subject, binding=rig.binding_value)
        outcome = self.terminal(rig, "succeeded")
        self.assertIs(outcome.result.tool_binding.run, binding_run)
        object.__setattr__(rig.binding_value, "run", rig.run)
        self.assertFalse(result._is_authoritative_result(outcome.result))
        object.__setattr__(rig.binding_value, "run", binding_run)
        self.assertFalse(result._is_authoritative_result(outcome.result))

    def test_R20_tool_substitution(self):
        self.tamper_after_read(lambda s: replace(s, binding=AgentOperationToolBinding(s.run, "tool::other::v1")))

    def test_R21_ledger_scoping_and_foreign_subject(self):
        first, second = self.rig(), self.rig()
        a, b = self.terminal(first, "succeeded").result, self.terminal(second, "succeeded").result
        self.assertEqual(a.execution_entry.identity, b.execution_entry.identity)
        self.assertNotEqual(a.identity, b.identity)
        self.tamper_after_read(lambda s: replace(s, ledger_identity=second.subject.ledger_identity, store=second.store))
        contract = a.tool_binding.run.contract
        environment = contract.environment_id
        try:
            object.__setattr__(contract, "environment_id", "synthetic altered environment")
            self.assertFalse(result._is_authoritative_result(a))
        finally:
            object.__setattr__(contract, "environment_id", environment)
        self.assertFalse(result._is_authoritative_result(a))
        self.assertTrue(result._is_authoritative_result(b))

    def test_R22_exact_claim_executor_generation(self):
        for field, value in (("claim_id", "a" * 64), ("executor_id", "b" * 64), ("lease_generation", 2)):
            with self.subTest(field=field):
                self.tamper_after_read(lambda s: replace(s, **{field: value}))

    def test_R23_rejected_entry_preserves_diagnostic(self):
        rig = self.rig()
        cap = rig.cap(self)
        rig.clock.value += timedelta(seconds=31)
        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        self.assertEqual(outcome.entry_result.outcome, "expired_claim")
        self.assertIsNone(outcome.invocation)
        self.assertIsNone(outcome.result)
        self.assertEqual(original._count(rig), 0)
        for fatal in (False, True):
            with self.subTest(fatal=fatal):
                other = self.rig()
                cap = other.cap(self)
                other.clock.value += timedelta(seconds=31)
                revalidate = type(other.session)._revalidate
                checked = []
                failure = (KeyboardInterrupt("synthetic rejected-entry fatal unwind") if fatal else
                           OwnedAuthorizationDomainSessionLostError("synthetic rejected-entry postcheck loss"))
                def failing_exit(session):
                    if session is other.session:
                        checked.append(True)
                        if len(checked) == 2 and not fatal:
                            raise failure
                    return revalidate(session)
                retain = type(other.root)._retain
                class FatalRootExit:
                    def __init__(self, scope):
                        self.scope = scope
                    def __enter__(self):
                        return self.scope.__enter__()
                    def __exit__(self, *error):
                        self.scope.__exit__(*error)
                        raise failure
                def retained(root):
                    scope = retain(root)
                    return FatalRootExit(scope) if fatal and root is other.root else scope
                with mock.patch.object(type(other.session), "_revalidate", new=failing_exit), \
                        mock.patch.object(type(other.root), "_retain", new=retained), \
                        mock.patch.object(other.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
                    if not fatal:
                        rejected = other.coordinator.invoke(cap, other.principal, other.decision)
                        self.assertEqual(rejected.entry_result.outcome, "ownership_lost")
                        self.assertIsNone(rejected.invocation)
                        self.assertIsNone(rejected.result)
                    else:
                        with self.assertRaises(KeyboardInterrupt) as caught:
                            other.coordinator.invoke(cap, other.principal, other.decision)
                        self.assertIs(caught.exception, failure)
                    opens.assert_not_called()
                self.assertEqual(len(checked), 2)
                self.assertEqual(original._count(other), 0)

    def test_R24_commit_unknown_no_result_or_effect(self):
        rig = self.rig()
        def lost(point):
            if point == "entry.after_commit_before_response":
                raise OSError("synthetic lost acknowledgement")
        with mock.patch.object(rig.store, "_fault", side_effect=lost), \
                mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            outcome = rig.invoke(self)
            opens.assert_not_called()
        self.assertEqual(outcome.entry_result.outcome, "commit_unknown")
        self.assertIsNone(outcome.invocation)
        self.assertIsNone(outcome.result)
        self.assertEqual(original._count(rig), 1)

    def test_R25_history_has_no_result_factory(self):
        rig = self.rig()
        cap = rig.cap(self)
        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        with mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            history = rig.coordinator.history(cap)
            opens.assert_not_called()
        self.assertEqual(history.outcome, "historical_entry")
        self.assertTrue(history.history_only)
        self.assertEqual(history.entry, outcome.result.execution_entry)
        self.assertFalse(hasattr(history, "result"))
        with self.assertRaises(TypeError):
            result.AgentExecutionResult(history.entry)

    def test_R26_component_restart_never_recovers_invocation(self):
        rig = self.rig()
        cap = rig.cap(self)
        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        rig.root.close()
        rig.a.close()
        rig.h.restart()  # Genuine owner/producer reconstruction; no child executor.
        with mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            restarted = rig.coordinator.invoke(cap, rig.principal, rig.decision)
            opens.assert_not_called()
        self.assertIsNone(restarted.result)
        self.assertNotEqual(restarted.entry_result.outcome, "entered")
        self.assertEqual(original._count(rig), 1)
        self.assertTrue(result._is_authoritative_result(outcome.result))
        with mock.patch.object(result.os, "getpid", return_value=-1):
            self.assertFalse(result._is_authoritative_result(outcome.result))

    def test_R27_repeated_invocation_cannot_publish_again(self):
        rig = self.rig()
        cap = rig.cap(self)
        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        with mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            repeated = rig.coordinator.invoke(cap, rig.principal, rig.decision)
            opens.assert_not_called()
        self.assertEqual(repeated.entry_result.outcome, "terminal_capability")
        self.assertIsNone(repeated.result)
        self.assertEqual(original._count(rig), 1)
        self.assertTrue(result._is_authoritative_result(outcome.result))
        with self.assertRaises(result._ResultIntegrityError):
            outcome.result._production.publish(outcome.entry_result, outcome.invocation)

    def test_R32_historical_and_noncanonical_work_rejected(self):
        rig = self.rig()
        boundary = rig.h.coordinator._historical_boundary
        reference = boundary._authority._reference(rig.grant, None, "live")
        with mock.patch.object(rig.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
            historical = rig.coordinator.invoke(reference, rig.principal, rig.decision)
            self.assertIsNone(historical.result)
            cap = rig.cap(self)
            saved = cap._cell.subject
            cap._cell.subject = replace(saved, binding=AgentOperationToolBinding(rig.run,
                "tool::aeo-native-repository-file-read::v1"))
            try:
                legacy = rig.coordinator.invoke(cap, rig.principal, rig.decision)
                self.assertIsNone(legacy.result)
                self.assertNotEqual(legacy.entry_result.outcome, "entered")
            finally:
                cap._cell.subject = saved
            opens.assert_not_called()
        self.assertEqual(original._count(rig), 0)
        boundary._authority._references.pop(id(reference), None)
        other = self.rig()
        cap = other.cap(self)
        saved = cap._cell.subject
        changed_run = replace(other.run, contract=replace(other.run.contract, operation_id="unsupported_operation"))
        cap._cell.subject = replace(saved, run=changed_run,
            binding=AgentOperationToolBinding(changed_run, other.binding_value.tool_id))
        try:
            with mock.patch.object(other.root._native, "open_component", side_effect=AssertionError("no target")) as opens:
                rejected = other.coordinator.invoke(cap, other.principal, other.decision)
                self.assertIsNone(rejected.result)
                self.assertNotEqual(rejected.entry_result.outcome, "entered")
                opens.assert_not_called()
            self.assertEqual(original._count(other), 0)
        finally:
            cap._cell.subject = saved

    def test_R33_fatal_interruption_preserved(self):
        rig = self.rig()
        cap = rig.cap(self)
        with mock.patch.object(rig.root._native, "read_data", side_effect=native._UnverifiedCompletion("synthetic fatal")):
            with self.assertRaises(native._UnverifiedCompletion):
                rig.coordinator.invoke(cap, rig.principal, rig.decision)
        self.assertEqual(cap._cell.state, "CONSUMED")
        self.assertEqual(original._count(rig), 1)
        self.assertIsNone(rig.coordinator._original)

    def test_R34_success_suppressed_by_cleanup_or_construction(self):
        rig = self.rig()
        close = native._Handle.close
        def uncertain(handle):
            close(handle)
            raise OSError("synthetic cleanup uncertainty")
        with mock.patch.object(native._Handle, "close", new=uncertain):
            self.terminal(rig, "effect_ambiguous", "effect_ambiguous")
        second = self.rig()
        cap = second.cap(self)
        with mock.patch.object(result, "_map_invocation", side_effect=ValueError("raw secret exception")):
            with self.assertRaises(result._ResultIntegrityError) as caught:
                second.coordinator.invoke(cap, second.principal, second.decision)
        self.assertEqual(caught.exception.args, ("canonical Result integrity failure",))
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)
        self.assertEqual(cap._cell.state, "CONSUMED")
        self.assertEqual(original._count(second), 1)
        self.assertIsNone(second.coordinator._original)

    def test_R35_first_request_and_empty_probe_failure(self):
        for data in (DATA, b""):
            with self.subTest(empty=not data):
                rig = self.rig(data)
                with mock.patch.object(rig.root._native, "read_data", side_effect=native._NativeFailure("read_failure")):
                    self.terminal(rig, "effect_ambiguous", "read_failure")
