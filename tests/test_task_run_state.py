"""Pure lifecycle, reconciliation and offline schema scenarios; no fixture writes."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
import json
from pathlib import Path
import tomllib
import unittest

import jsonschema
from referencing import Registry, Resource
import yaml

from itru import task_run_state as state
from itru.agent_execution_contract import AgentExecutionContract
from itru.agent_execution_run import AgentExecutionRun
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from itru import agent_execution_journal as journal
from tests.test_agent_execution_journal import _body, _record

ROOT = Path(__file__).resolve().parents[1]
LEDGER = AuthorizationDomainIdentity('domain::journal-fixture', 'ledger::journal-fixture', 1)


def binding(run_id='run::1', task_id='ITRU-062'):
    contract = AgentExecutionContract(task_id, 'standard-change', 'implement',
        'software-engineer', 'actor::fixture', 'runtime::fixture', 'option::fixture',
        'environment::fixture', 'repository_file_read', 'fixtures/journal.bin', 'deep')
    return AgentOperationToolBinding(AgentExecutionRun(run_id, contract),
                                   'tool::itru-native-repository-file-read::v1')


def event(sequence, operation, data, *, task_id='ITRU-062', revision=None):
    return dict(format_version=1, sequence=sequence, task_id=task_id,
                revision=sequence if revision is None else revision, operation=operation, data=data)


def prefix():
    return [event(1, 'enroll', dict(definition_reference='definition::fixture')),
            event(2, 'register', dict(subject=state.subject_document(binding(), LEDGER))),
            event(3, 'start', dict(run_id='run::1'))]


def terminal(outcome='succeeded'):
    return event(4, 'result', dict(run_id='run::1', outcome=outcome,
        result_identity=['ledger::journal-fixture', 'domain::journal-fixture', 'human', 'issuer', 'grant']))


def records(outcome='succeeded'):
    result = []
    for index, kind in enumerate(('entry_observed', 'result_observed'), 1):
        body = _body(kind, outcome, 0 if outcome == 'succeeded' else None,
                     None if outcome == 'succeeded' else 'read_failure')
        body['admission']['grant']['run'] = asdict(binding().run)
        body['admission']['tool_binding'] = asdict(binding())
        result.append(journal.JournalRecord(journal._encode(_record(body, index))))
    return tuple(result)


class TaskRunDomainTests(unittest.TestCase):
    def test_01_legal_states_and_explicit_completion(self):
        events = prefix() + [terminal(), event(5, 'complete', dict(reference='governance::closed'))]
        task = state.reconstruct(events)['ITRU-062']
        self.assertEqual((task.state, task.runs[0].state), ('completed', 'succeeded'))
        with self.assertRaises(FrozenInstanceError):
            task.state = 'planned'

    def test_02_terminal_task_and_run_never_reopen(self):
        for outcome in state.RESULT_OUTCOMES:
            events = prefix() + [terminal(outcome)]
            with self.subTest(outcome=outcome), self.assertRaises(state.StateIntegrityError):
                state.reconstruct(events + [event(5, 'start', dict(run_id='run::1'))])
        events = prefix() + [terminal(), event(5, 'complete', dict(reference='closed'))]
        with self.assertRaises(state.StateIntegrityError):
            state.reconstruct(events + [event(6, 'cancel', dict(reference='reopen'))])

    def test_03_interrupted_never_success_or_eligible(self):
        task = state.reconstruct(prefix() + [event(4, 'recover', {})])['ITRU-062']
        self.assertEqual((task.state, task.runs[0].state), ('blocked', 'interrupted'))
        self.assertFalse(state.continuation_eligible(task))
        view = state.reconcile_run(task.runs[0], records())
        self.assertEqual((view.state, view.lifecycle_state, view.recorded_outcome),
                         ('recorded_result', 'interrupted', 'succeeded'))

    def test_04_before_start_cancel_differs_from_interruption(self):
        for operation, data in (('recover', {}), ('stop', dict(reference='human::stop'))):
            task = state.reconstruct(prefix()[:2] + [event(3, operation, data)])['ITRU-062']
            self.assertEqual(task.runs[0].state, 'cancelled')
            self.assertTrue(state.continuation_eligible(task))

    def test_05_ambiguous_never_continuation(self):
        task = state.reconstruct(prefix() + [terminal('effect_ambiguous')])['ITRU-062']
        self.assertEqual(task.state, 'blocked')
        self.assertFalse(state.continuation_eligible(task))
        self.assertIsNotNone(task.runs[0].result_identity)

    def test_06_ownership_collision_and_illegal_prefix(self):
        bad = prefix()
        bad[1]['data']['subject']['binding']['run']['contract']['task_id'] = 'other'
        variants = [bad, prefix()[1:], prefix() + [event(4, 'recover', {}, revision=9)],
                    prefix() + [event(4, 'complete', dict(reference='missing-result'))]]
        for events in variants:
            with self.subTest(events=events), self.assertRaises(state.StateIntegrityError):
                state.reconstruct(events)

    def test_07_closed_json_and_versions(self):
        for text in ('{"a":1,"a":2}', '{"a":1.0}', '{"a":true}', '{"a":NaN}', ' {"a":1}'):
            with self.subTest(text=text), self.assertRaises(state.StateIntegrityError):
                state.decode(text)
        for field, value in (('format_version', 2), ('sequence', True), ('revision', 0), ('extra', 'authority')):
            changed = deepcopy(prefix()[0]); changed[field] = value
            with self.subTest(field=field), self.assertRaises(state.StateIntegrityError):
                state.validate_event(changed)

    def test_08_reconciliation_gaps_conflicts_and_order(self):
        run = state.reconstruct(prefix())['ITRU-062'].runs[0]
        self.assertEqual(state.reconcile_run(run, ()).state, 'missing')
        self.assertEqual(state.reconcile_run(run, records()[:1]).state, 'entry_only')
        self.assertEqual(state.reconcile_run(run, records()[1:]).state, 'inconsistent')
        self.assertEqual(state.reconcile_run(run, records()[::-1]).state, 'inconsistent')
        self.assertEqual(state.reconcile_run(run, records()[:1]*2).state, 'inconsistent')
        other = replace(run, binding=binding('run::other'))
        self.assertEqual(state.reconcile_run(other, records()).state, 'conflict')
        self.assertEqual(state.reconcile_run(run, ({'outcome': 'succeeded'},)).state, 'inconsistent')
        pending = state.reconstruct(prefix()[:2])['ITRU-062'].runs[0]
        cancelled = state.reconstruct(prefix()[:2] + [event(3, 'recover', {})])['ITRU-062'].runs[0]
        for before_start in (pending, cancelled):
            for evidence in (records()[:1], records()):
                diagnostic = state.reconcile_run(before_start, evidence)
                self.assertEqual(diagnostic.state, 'conflict')
                self.assertEqual(diagnostic.lifecycle_state, before_start.state)
                self.assertEqual(diagnostic.recorded_outcome, 'succeeded' if len(evidence) == 2 else None)
                self.assertIsNone(before_start.result_identity)

    def test_09_reconciliation_matches_all_subject_coordinates(self):
        run = state.reconstruct(prefix())['ITRU-062'].runs[0]
        first, second = records()
        doc = second.document; doc['execution_entry']['claim_id'] = '3'*64
        changed = journal.JournalRecord(journal._encode(doc))
        self.assertEqual(state.reconcile_run(run, (first, changed)).state, 'inconsistent')
        complete = state.reconstruct(prefix() + [terminal()])['ITRU-062'].runs[0]
        self.assertEqual(state.reconcile_run(complete, records('effect_ambiguous')).state, 'conflict')

    def test_10_schema_offline_and_exact_task(self):
        names = ('task-run-state-event', 'agent-operation-tool-binding',
                 'agent-execution-run', 'agent-execution-contract')
        schemas = [json.loads((ROOT/'schemas'/f'{name}.schema.json').read_text(encoding='utf-8')) for name in names]
        registry = Registry(retrieve=lambda uri: (_ for _ in ()).throw(AssertionError('no remote schema')))
        for schema in schemas:
            jsonschema.Draft202012Validator.check_schema(schema)
            registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
        validator = jsonschema.Draft202012Validator(schemas[0], registry=registry)
        examples = prefix() + [terminal(), event(5, 'recover', {}),
            event(6, 'block', dict(reference='ref')), event(7, 'cancel', dict(reference='ref')),
            event(8, 'stop', dict(reference='ref')), event(9, 'complete', dict(reference='ref')),
            event(10, 'continue', dict(subject=state.subject_document(binding('run::2'), LEDGER),
                approval=asdict(state.ContinuationApproval('session', 'request', 'human', 'issuer', 'ref')), reason='next'))]
        for example in examples:
            validator.validate(example); state.validate_event(example)
            for mutate in ('extra', 'missing', 'version', 'data'):
                changed = deepcopy(example)
                if mutate == 'extra': changed['authority'] = True
                elif mutate == 'missing': del changed['task_id']
                elif mutate == 'version': changed['format_version'] = 2
                else: changed['data']['unexpected'] = 'value'
                self.assertTrue(list(validator.iter_errors(changed)))
                with self.assertRaises(state.StateIntegrityError): state.validate_event(changed)
        task = yaml.safe_load((ROOT/'.ai/tasks/ITRU-062-persistent-task-run-state/task.yaml').read_text(encoding='utf-8'))
        task_schema = json.loads((ROOT/'schemas/task.schema.json').read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator(task_schema).validate(task)
        project = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
        self.assertIn('task-run-state-event.schema.json', project['tool']['setuptools']['package-data']['itru._schemas'])
