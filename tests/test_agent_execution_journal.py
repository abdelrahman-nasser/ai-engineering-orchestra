"""16 pure Journal contract scenarios. No fixture I/O or provisioning."""
from __future__ import annotations

import copy
from dataclasses import replace
import json
import os
import unittest
from weakref import ref

from itru import agent_execution_journal as journal
from itru.agent_execution_contract import AgentExecutionContract
from itru.agent_execution_run import AgentExecutionRun
from itru.agent_execution_authorization_grant import AgentExecutionAuthorizationGrant
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from itru.agent_execution_dispatch_admission import AgentExecutionDispatchAdmission
from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from itru._execution_entry_and_controlled_invocation import _ExecutionEntry


def _body(kind='entry_observed', outcome='succeeded', count=0, code=None):
    contract = AgentExecutionContract('ITRU-061', 'standard-change', 'implement',
        'software-engineer', 'actor::fixture', 'runtime::fixture', 'option::fixture',
        'environment::fixture', 'repository_file_read', 'fixtures/journal.bin', 'deep')
    run = AgentExecutionRun('run::journal-fixture', contract)
    grant = AgentExecutionAuthorizationGrant('grant::journal-fixture', run,
        'domain::journal-fixture', 'human', 'issuer::fixture', 'approval::fixture',
        '2026-10-14T00:00:00Z', '2026-10-15T00:00:00Z')
    binding = AgentOperationToolBinding(run, 'tool::itru-native-repository-file-read::v1')
    admission = AgentExecutionDispatchAdmission(grant, binding, '2026-10-14T00:00:00.000000Z')
    identity = AuthorizationDomainIdentity('domain::journal-fixture', 'ledger::journal-fixture', 1)
    entry = _ExecutionEntry((grant.authorization_domain_id, grant.issuer_kind, grant.issuer_id, grant.grant_id),
        '1' * 64, '2' * 64, 1, '2026-10-14T00:00:01.000000Z', journal._time('2026-10-14T00:00:01.000000Z'))
    subject = journal._subject_document(identity, entry, admission)
    summary = None if kind == 'entry_observed' else dict(outcome=outcome, diagnostic_code=code, byte_count=count)
    return dict(format_version=1, **subject, event_kind=kind,
                provenance='original_controlled_invocation', result_summary=summary)


def _record(body=None, sequence=1):
    return dict(_body() if body is None else body, journal_id='journal::fixture',
                sequence=sequence, recorded_at='2026-10-14T00:00:02.000000Z')


def _storage_fact(body):
    """TEST ONLY cooperative membership for storage mechanics, not origin proof.

    No production factory is exposed. F3 separately tests genuine provenance.
    This white-box fixture mutates only the in-memory private membership table.
    """
    text = journal._encode(journal._validate_body(body))
    fact = object.__new__(journal._Fact)
    object.__setattr__(fact, 'body_json', text)
    key = id(fact)
    journal._FACT_MEMBERS[key] = (ref(fact, lambda ignored: journal._FACT_MEMBERS.pop(key, None)), os.getpid(), text)
    return fact


class JournalContractScenarios(unittest.TestCase):
    def test_J01_complete_binding(self):
        body = _body()
        self.assertIs(journal._validate_body(body), body)
        record = journal.JournalRecord(journal._encode(_record(body)))
        self.assertEqual(len(record.document), 10)
        self.assertEqual(record.document['admission']['grant']['run'], record.document['admission']['tool_binding']['run'])

    def test_J02_all_contract_fields(self):
        base = _body()
        for field in base['admission']['tool_binding']['run']['contract']:
            changed = copy.deepcopy(base)
            changed['admission']['tool_binding']['run']['contract'][field] = 'standard' if field == 'execution_mode' else 'different'
            self.assertEqual(changed['admission']['grant']['run']['run_id'], changed['admission']['tool_binding']['run']['run_id'])
            with self.subTest(field=field), self.assertRaises(ValueError):
                journal._validate_body(changed)

    def test_J03_ledger_scoped_identity(self):
        first, second = _body(), _body()
        second['ledger_identity']['ledger_instance_id'] = 'ledger::other'
        self.assertNotEqual(journal._subject_key(first), journal._subject_key(second))
        with self.assertRaises(journal.JournalIntegrityError):
            journal._require_same_subject(journal._subject_only(first), journal._subject_only(second))

    def test_J04_generation_not_occurrence(self):
        first, second = _body(), _body()
        second['ledger_identity']['domain_generation'] = 2 ** 63
        journal._validate_body(second)
        self.assertEqual(journal._subject_key(first), journal._subject_key(second))
        with self.assertRaises(journal.JournalIntegrityError):
            journal._require_same_subject(journal._subject_only(first), journal._subject_only(second))

    def test_J05_tool_is_exact(self):
        first, second = _body(), _body()
        second['admission']['tool_binding']['tool_id'] = 'tool::aeo-native-repository-file-read::v1'
        journal._validate_body(second)  # Historical spelling is descriptive, not active resolution.
        with self.assertRaises(journal.JournalIntegrityError):
            journal._require_same_subject(journal._subject_only(first), journal._subject_only(second))

    def test_J06_lookalike_and_copy(self):
        fake = object.__new__(journal._Fact)
        object.__setattr__(fake, 'body_json', journal._encode(_body()))
        self.assertFalse(journal._trusted_fact(fake))
        for op in (copy.copy, copy.deepcopy):
            with self.assertRaises(TypeError):
                op(fake)
        with self.assertRaises(journal.JournalIntegrityError):
            journal._mint_fact(_body())
        with self.assertRaises(TypeError):
            fake.__setstate__([journal._encode(_body('result_observed'))])
        with self.assertRaises(TypeError):
            fake.__getstate__()

    def test_J07_success_is_content_free(self):
        for count in (0, 65536):
            document = _record(_body('result_observed', count=count), 2)
            text = journal._encode(journal._validate_record(document))
            self.assertEqual(journal._decode(text)['result_summary']['byte_count'], count)
            self.assertEqual(set(document['result_summary']), {'outcome', 'diagnostic_code', 'byte_count'})
            self.assertNotIn('payload', document)

    def test_J08_failed_before_effect(self):
        for code in journal._BEFORE:
            journal._validate_body(_body('result_observed', 'failed_before_effect', None, code))

    def test_J09_ambiguous_result(self):
        for code in journal._AMBIGUOUS:
            journal._validate_body(_body('result_observed', 'effect_ambiguous', None, code))
        self.assertIsNone(_body()['result_summary'])
        self.assertIsNotNone(_body('result_observed', 'effect_ambiguous', None, 'effect_ambiguous')['result_summary'])

    def test_J10_closed_summary(self):
        for summary in ({}, dict(outcome='succeeded', diagnostic_code='read_failure', byte_count=0),
                        dict(outcome='effect_ambiguous', diagnostic_code='guard_lost', byte_count=None)):
            body = _body('result_observed'); body['result_summary'] = summary
            with self.assertRaises(ValueError):
                journal._validate_body(body)

    def test_J11_flags_are_not_provenance(self):
        for fake in ({'trusted': True}, {'pid': os.getpid()}, _body()):
            self.assertFalse(journal._trusted_fact(fake))
            self.assertFalse(journal._trusted_history(fake))
        fact = _storage_fact(_body())
        original = fact.body_json
        object.__setattr__(fact, 'body_json', journal._encode(_body('result_observed')))
        self.assertFalse(journal._trusted_fact(fact))
        object.__setattr__(fact, 'body_json', original)
        self.assertFalse(journal._trusted_fact(fact))

    def test_J12_semantic_encoding(self):
        for bad in ('{"x":1,"x":1}', '{"x":1.0}', '{"x":NaN}', '{ "x":1}', '{"x":true}'):
            with self.assertRaises(journal.JournalIntegrityError):
                journal._decode(bad)
        for field, value in (('entry_time', '2026-02-30T00:00:01.000000Z'), ('entry_time_key', True), ('lease_generation', True)):
            body = _body(); body['execution_entry'][field] = value
            with self.assertRaises(ValueError):
                journal._validate_body(body)
        with self.assertRaises((UnicodeError, ValueError)):
            journal._encode({'value': '\ud800'})

    def test_J13_no_sensitive_extensions(self):
        for field in ('data', 'payload', 'digest', 'exception', 'absolute_path'):
            body = _body(); body[field] = 'synthetic-only'
            with self.assertRaises(journal.JournalIntegrityError):
                journal._validate_body(body)

    def test_J14_metadata_limit(self):
        body = _body(); body['admission']['grant']['provenance_reference'] = 'x' * journal.MAX_RECORD_BYTES
        with self.assertRaises(journal.JournalMetadataLimit):
            journal._encode(body)

    def test_J15_descriptive_only(self):
        record = journal.JournalRecord(journal._encode(_record()))
        document = record.document; document['execution_entry']['claim_id'] = '3' * 64
        self.assertNotEqual(document, record.document)
        for name in ('invoke', 'resume', 'result', 'capability', 'deserialize_result'):
            self.assertFalse(hasattr(record, name))
        self.assertFalse(journal._trusted_fact(record))

    def test_J16_no_future_state(self):
        for field in ('task_state', 'run_state', 'retry', 'budget'):
            body = _body(); body[field] = 'pending'
            with self.assertRaises(ValueError):
                journal._validate_body(body)
        body = _body(); body['format_version'] = 2
        with self.assertRaises(ValueError):
            journal._validate_body(body)
