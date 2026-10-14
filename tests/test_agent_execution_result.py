"""Twelve explicit pure ITRU-060 cases; no fixtures, discovery or target I/O."""
from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, fields
import pickle
import unittest

from itru import agent_execution_result as result
from itru._execution_entry_and_controlled_invocation import _ExecutionEntry, _InvocationOutcome
from itru.authorization_domain_ownership import AuthorizationDomainIdentity


def _raw_invocation(status="completed", reason="effect_completed", data=b"", byte_count=0):
    value = object.__new__(_InvocationOutcome)
    for key, item in (("status", status), ("reason", reason), ("data", data), ("byte_count", byte_count)):
        object.__setattr__(value, key, item)
    return value


def _lookalike():
    """Untrusted structural specimen: deliberately no producer membership."""
    value = object.__new__(result.AgentExecutionResult)
    for key, item in (
        ("ledger_identity", AuthorizationDomainIdentity("domain", "ledger", 1)),
        ("execution_entry", _ExecutionEntry(("domain", "human", "issuer", "grant"),
                                           "1" * 64, "2" * 64, 1, "", 0)),
        ("tool_binding", None), ("outcome", "succeeded"),
        ("payload", result.RepositoryFileReadResultPayload(b"", 0)), ("diagnostic", None),
    ):
        object.__setattr__(value, key, item)
    return value


class ResultContractTests(unittest.TestCase):
    def test_closed_shape(self):
        self.assertEqual(tuple(field.name for field in fields(result.AgentExecutionResult)),
            ("ledger_identity", "execution_entry", "tool_binding", "outcome", "payload", "diagnostic"))
        self.assertEqual(tuple(field.name for field in fields(result.RepositoryFileReadResultPayload)),
                         ("data", "byte_count"))
        self.assertEqual(tuple(field.name for field in fields(result.AgentExecutionResultDiagnostic)), ("code",))
        self.assertEqual(set(result.__all__), {"AgentExecutionResult", "AgentExecutionResultDiagnostic",
                                              "RepositoryFileReadResultPayload"})

    def test_R16_unsupported_private_taxonomy(self):
        for value in (_raw_invocation("future"), _raw_invocation("failed_before_content", "future", None),
                      _raw_invocation("failed_before_content", "entry_rejected", None)):
            with self.subTest(value=value.status), self.assertRaises(result._ResultIntegrityError):
                result._map_invocation(value)

    def test_R17_malformed_success_is_sanitized(self):
        for value in (_raw_invocation(reason="read_failure"), _raw_invocation(data=b"secret", byte_count=5),
                      _raw_invocation(data=None), _raw_invocation(data=b"a" * 65537, byte_count=65537)):
            with self.subTest(count=value.byte_count):
                try:
                    result._map_invocation(value)
                except result._ResultIntegrityError as error:
                    self.assertEqual(error.args, ("canonical Result integrity failure",))
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                else:
                    self.fail("malformed success accepted")

    def test_R28_construction_copy_and_subclass_are_rejected(self):
        value = _lookalike()
        for operation in (lambda: result.AgentExecutionResult(), lambda: copy.copy(value),
                          lambda: copy.deepcopy(value), lambda: pickle.dumps(value),
                          lambda: type("ForgedResult", (result.AgentExecutionResult,), {})):
            with self.assertRaises(TypeError):
                operation()
        self.assertFalse(result._is_authoritative_result(value))
        original = tuple(getattr(value, field.name) for field in fields(value))
        for state in (original, [None] * 6, {"outcome": "effect_ambiguous"}, None):
            with self.subTest(state=type(state).__name__), self.assertRaises(TypeError):
                value.__setstate__(state)
            self.assertTrue(all(getattr(value, field.name) is item
                                for field, item in zip(fields(value), original)))
            self.assertFalse(result._is_authoritative_result(value))
        with self.assertRaises(TypeError):
            value.__getstate__()

    def test_R29_closed_diagnostics_only(self):
        for code in ("secret-content", "C:/protected/file", {"code": "read_failure"}, Exception("secret"), None):
            with self.subTest(code=type(code).__name__), self.assertRaises(ValueError):
                result.AgentExecutionResultDiagnostic(code)
        with self.assertRaises(TypeError):
            result.AgentExecutionResultDiagnostic("read_failure", message="secret")
        diagnostic = result.AgentExecutionResultDiagnostic("read_failure")
        for operation in (lambda: diagnostic.__setstate__(["effect_ambiguous"]),
                          diagnostic.__getstate__, lambda: pickle.dumps(diagnostic)):
            with self.assertRaises(TypeError):
                operation()
            self.assertEqual(diagnostic.code, "read_failure")

    def test_R30_unsuccessful_content_is_rejected(self):
        for status in ("failed_before_content", "failed_after_content", "ambiguous"):
            with self.subTest(status=status), self.assertRaises(result._ResultIntegrityError):
                result._map_invocation(_raw_invocation(status, "read_failure", b"partial", 7))
        with self.assertRaises(result._ResultIntegrityError):
            result._validate_terminal_values("effect_ambiguous", result.RepositoryFileReadResultPayload(b"", 0),
                                            result.AgentExecutionResultDiagnostic("read_failure"))

    def test_R31_exact_payload_types(self):
        class BytesSubclass(bytes):
            pass
        for data, count in ((bytearray(b"x"), 1), (memoryview(b"x"), 1), (BytesSubclass(b"x"), 1),
                            (b"x", True), (b"", -1), (b"", 1)):
            with self.subTest(data=type(data).__name__, count=count), self.assertRaises(ValueError):
                result.RepositoryFileReadResultPayload(data, count)
        payload = result.RepositoryFileReadResultPayload(b"x", 1)
        for operation in (lambda: payload.__setstate__([b"replacement", 11]),
                          payload.__getstate__, lambda: pickle.dumps(payload)):
            with self.assertRaises(TypeError):
                operation()
            self.assertEqual((payload.data, payload.byte_count), (b"x", 1))

    def test_R36_reports_have_no_trust_or_deserializer(self):
        for value in ({"trusted": True, "outcome": "succeeded"}, '{"outcome":"succeeded"}',
                      b"serialized", _lookalike()):
            self.assertFalse(result._is_authoritative_result(value))
            with self.assertRaises(TypeError):
                result.AgentExecutionResult(value)
        for name in ("deserialize", "from_json", "from_mapping", "load_result", "serialize"):
            self.assertFalse(hasattr(result, name))

    def test_R37_physical_identity_does_not_replace_evidence(self):
        first, second = _lookalike(), _lookalike()
        object.__setattr__(second, "outcome", "effect_ambiguous")
        object.__setattr__(second, "ledger_identity", AuthorizationDomainIdentity("domain", "ledger", 2))
        self.assertEqual(first.identity, second.identity)
        self.assertNotEqual(first, second)
        self.assertFalse(result._is_authoritative_result(first))
        self.assertFalse(result._is_authoritative_result(second))

    def test_R38_empty_success_is_not_absent(self):
        outcome, payload, diagnostic = result._map_invocation(_InvocationOutcome("completed", "effect_completed", b"", 0))
        self.assertEqual(outcome, "succeeded")
        self.assertEqual(payload, result.RepositoryFileReadResultPayload(b"", 0))
        self.assertIsNone(diagnostic)
        with self.assertRaises(result._ResultIntegrityError):
            result._validate_terminal_values("succeeded", None, None)

    def test_R39_code_outcome_coherence(self):
        for outcome, code in (("failed_before_effect", "effect_ambiguous"),
                              ("effect_ambiguous", "guard_lost"), ("effect_ambiguous", "ownership_lost")):
            with self.subTest(outcome=outcome, code=code), self.assertRaises(result._ResultIntegrityError):
                result._validate_terminal_values(outcome, None, result.AgentExecutionResultDiagnostic(code))
        self.assertEqual(result._map_invocation(_InvocationOutcome("failed_after_content", "adapter_unavailable"))[0],
                         "effect_ambiguous")

    def test_R40_immutable_evidence_has_no_execution_api(self):
        value = _lookalike()
        for name, item in (("outcome", "failed_before_effect"), ("payload", None), ("ledger_identity", None)):
            with self.subTest(name=name), self.assertRaises(FrozenInstanceError):
                setattr(value, name, item)
        with self.assertRaises(FrozenInstanceError):
            value.payload.data = b"replacement"
        for name in ("invoke", "dispatch", "retry", "grant", "continuation", "trusted", "persist"):
            self.assertFalse(hasattr(value, name))
