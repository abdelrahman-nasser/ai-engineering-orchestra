"""Immutable lifecycle read models and deterministic reduction; no execution API.

Historical state is descriptive. Only the live Store boundary may accept an
original Result or a fresh continuation decision. Reduction restores neither.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json

from itru.agent_execution_contract import AgentExecutionContract
from itru.agent_execution_run import AgentExecutionRun
from itru.agent_operation_tool_binding import (
    AgentOperationToolBinding, validate_agent_operation_tool_binding,
)
from itru.authorization_domain_ownership import AuthorizationDomainIdentity

TASK_STATES = frozenset(('planned', 'in_progress', 'blocked', 'completed', 'cancelled'))
RUN_STATES = frozenset(('pending', 'running', 'succeeded', 'failed_before_effect',
                        'effect_ambiguous', 'interrupted', 'cancelled'))
UNFINISHED = frozenset(('pending', 'running'))
UNSAFE = frozenset(('interrupted', 'effect_ambiguous'))
RESULT_OUTCOMES = frozenset(('succeeded', 'failed_before_effect', 'effect_ambiguous'))
MAX_RECORD_BYTES = 1048576
MAX_EVENTS = 10000


class StateIntegrityError(ValueError):
    """Invalid input or inconsistent persisted state; no partial state is usable."""


class StateConflictError(RuntimeError):
    """Stale revision, illegal transition or identity collision."""


class ContinuationDeniedError(RuntimeError):
    """No fresh exact decision from the configured trusted authority boundary."""


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    binding: AgentOperationToolBinding
    ledger_identity: AuthorizationDomainIdentity
    state: str
    revision: int
    result_identity: tuple[str, ...] | None = None

    @property
    def run_id(self):
        return self.binding.run.run_id


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    task_id: str
    definition_reference: str
    state: str
    revision: int
    reason: str
    runs: tuple[RunSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class Checkpoint:
    store_id: str
    project_id: str
    task_id: str
    revision: int


@dataclass(frozen=True, slots=True)
class ContinuationRequest:
    checkpoint: Checkpoint
    session_nonce: str
    request_nonce: str
    binding: AgentOperationToolBinding
    ledger_identity: AuthorizationDomainIdentity
    reason: str


@dataclass(frozen=True, slots=True)
class ContinuationApproval:
    session_nonce: str
    request_nonce: str
    authority_kind: str
    authority_id: str
    reference: str


@dataclass(frozen=True, slots=True)
class EvidenceReconciliation:
    state: str
    lifecycle_state: str
    recorded_outcome: str | None


def _text(value):
    if type(value) is not str or not value:
        raise StateIntegrityError('expected nonempty exact string')
    try:
        value.encode('utf-8', 'strict')
    except UnicodeError:
        raise StateIntegrityError('invalid text') from None
    return value


def _integer(value):
    if type(value) is not int or not 1 <= value <= 9223372036854775807:
        raise StateIntegrityError('expected bounded positive integer')
    return value


def _object(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise StateIntegrityError('closed object mismatch')
    return value


def _tree(value):
    if value is None or type(value) is int:
        return
    if type(value) is str:
        value.encode('utf-8', 'strict')
        return
    if type(value) is list:
        for item in value:
            _tree(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for key, item in value.items():
            _tree(key)
            _tree(item)
        return
    raise StateIntegrityError('unsupported JSON value')


def encode(value):
    try:
        _tree(value)
        text = json.dumps(value, ensure_ascii=True, sort_keys=True,
                          separators=(',', ':'), allow_nan=False)
        if len(text.encode('utf-8')) > MAX_RECORD_BYTES:
            raise StateIntegrityError('state record limit')
        return text
    except (TypeError, UnicodeError, RecursionError):
        raise StateIntegrityError('invalid state document') from None


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StateIntegrityError('duplicate JSON key')
        result[key] = value
    return result


def _bad_number(value):
    raise StateIntegrityError('unsupported JSON number')


def decode(text):
    if type(text) is not str or len(text.encode('utf-8')) > MAX_RECORD_BYTES:
        raise StateIntegrityError('state record limit/type')
    try:
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_float=_bad_number, parse_constant=_bad_number)
        if encode(value) != text:
            raise StateIntegrityError('noncanonical state JSON')
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise StateIntegrityError('invalid state JSON') from None


def subject_document(binding, ledger_identity):
    if (type(binding) is not AgentOperationToolBinding
            or not validate_agent_operation_tool_binding(binding).valid
            or type(ledger_identity) is not AuthorizationDomainIdentity):
        raise StateIntegrityError('invalid complete Run subject')
    ledger_identity.__post_init__()
    document = dict(binding=asdict(binding), ledger_identity=asdict(ledger_identity))
    encode(document)
    return document


def _subject(document):
    try:
        _object(document, ('binding', 'ledger_identity'))
        b, ledger = document['binding'], document['ledger_identity']
        _object(b, ('run', 'tool_id'))
        _object(b['run'], ('run_id', 'contract'))
        _object(b['run']['contract'], AgentExecutionContract.__dataclass_fields__)
        _object(ledger, AuthorizationDomainIdentity.__dataclass_fields__)
        binding = AgentOperationToolBinding(AgentExecutionRun(b['run']['run_id'],
            AgentExecutionContract(**b['run']['contract'])), b['tool_id'])
        identity = AuthorizationDomainIdentity(**ledger)
        subject_document(binding, identity)
        return binding, identity
    except (TypeError, ValueError, KeyError):
        raise StateIntegrityError('invalid complete Run subject') from None


def _approval(document):
    _object(document, ContinuationApproval.__dataclass_fields__)
    for value in document.values():
        _text(value)
    if document['authority_kind'] not in ('human', 'policy'):
        raise StateIntegrityError('invalid continuation authority kind')


def validate_event(event):
    _object(event, ('format_version', 'sequence', 'task_id', 'revision', 'operation', 'data'))
    if type(event['format_version']) is not int or event['format_version'] != 1:
        raise StateIntegrityError('unsupported event version')
    _integer(event['sequence']); _integer(event['revision']); _text(event['task_id'])
    operation, data = event['operation'], event['data']
    if type(operation) is not str:
        raise StateIntegrityError('invalid operation')
    if operation == 'enroll':
        _object(data, ('definition_reference',)); _text(data['definition_reference'])
    elif operation in ('register', 'continue'):
        keys = ('subject',) if operation == 'register' else ('subject', 'approval', 'reason')
        _object(data, keys)
        binding, _ = _subject(data['subject'])
        if binding.run.contract.task_id != event['task_id']:
            raise StateIntegrityError('Run/Task ownership mismatch')
        if operation == 'continue':
            _approval(data['approval']); _text(data['reason'])
    elif operation in ('block', 'cancel', 'complete', 'stop'):
        _object(data, ('reference',)); _text(data['reference'])
    elif operation == 'start':
        _object(data, ('run_id',)); _text(data['run_id'])
    elif operation == 'result':
        _object(data, ('run_id', 'outcome', 'result_identity'))
        _text(data['run_id'])
        if type(data['outcome']) is not str or data['outcome'] not in RESULT_OUTCOMES:
            raise StateIntegrityError('invalid Result outcome')
        if type(data['result_identity']) is not list or len(data['result_identity']) != 5:
            raise StateIntegrityError('invalid physical Result identity')
        for item in data['result_identity']:
            _text(item)
    elif operation == 'recover':
        _object(data, ())
    else:
        raise StateIntegrityError('unsupported state operation')
    encode(event)
    return event


def continuation_eligible(task):
    return (task.state in ('in_progress', 'blocked')
        and not any(run.state in UNFINISHED | UNSAFE for run in task.runs)
        and (not task.runs or task.runs[-1].state in
             ('succeeded', 'failed_before_effect', 'cancelled')))


def apply_event(tasks, event):
    """Pure reducer; callers must supply the complete previously validated prefix."""
    validate_event(event)
    task_id, revision, operation, data = (event[key] for key in
        ('task_id', 'revision', 'operation', 'data'))
    task = tasks.get(task_id)
    if operation == 'enroll':
        if task is not None or revision != 1:
            raise StateConflictError('Task enrollment collision')
        tasks[task_id] = TaskSnapshot(task_id, data['definition_reference'], 'planned', 1, 'enrolled')
        return
    if task is None or revision != task.revision + 1:
        raise StateConflictError('stale Task revision')
    if task.state in ('completed', 'cancelled'):
        raise StateConflictError('terminal Task cannot reopen')
    runs = list(task.runs)
    state, reason = task.state, task.reason
    if operation in ('register', 'continue'):
        if operation == 'register':
            if state != 'planned' or runs:
                raise StateConflictError('initial registration already used')
        elif not continuation_eligible(task):
            raise StateConflictError('continuation unsafe')
        binding, ledger = _subject(data['subject'])
        if any(item.run_id == binding.run.run_id for t in tasks.values() for item in t.runs):
            raise StateConflictError('Run ID permanently bound')
        runs.append(RunSnapshot(binding, ledger, 'pending', revision))
        state, reason = 'in_progress', 'registered' if operation == 'register' else data['reason']
    elif operation == 'start':
        if not runs or runs[-1].run_id != data['run_id'] or runs[-1].state != 'pending' or state != 'in_progress':
            raise StateConflictError('Run cannot start')
        runs[-1] = replace(runs[-1], state='running', revision=revision)
        reason = 'started'
    elif operation == 'result':
        if not runs or runs[-1].run_id != data['run_id'] or runs[-1].state != 'running':
            raise StateConflictError('Run cannot accept Result')
        run = runs[-1]
        identity = tuple(data['result_identity'])
        if (identity[0] != run.ledger_identity.ledger_instance_id
                or identity[1] != run.ledger_identity.authorization_domain_id
                or identity[2] not in ('human', 'policy')):
            raise StateIntegrityError('Result identity scope mismatch')
        if any(item.result_identity == identity for t in tasks.values() for item in t.runs):
            raise StateConflictError('physical Result identity already bound')
        runs[-1] = replace(run, state=data['outcome'], revision=revision, result_identity=identity)
        state = 'in_progress' if data['outcome'] == 'succeeded' else 'blocked'
        reason = 'original_result_observed'
    elif operation in ('recover', 'stop', 'cancel'):
        if operation != 'cancel' and not any(run.state in UNFINISHED for run in runs):
            raise StateConflictError('no unfinished Run')
        runs = [replace(run, state='cancelled' if run.state == 'pending' else 'interrupted',
                        revision=revision) if run.state in UNFINISHED else run for run in runs]
        state = 'cancelled' if operation == 'cancel' else 'blocked'
        reason = 'process_recovery' if operation == 'recover' else data['reference']
    elif operation == 'block':
        if state not in ('planned', 'in_progress') or any(run.state in UNFINISHED for run in runs):
            raise StateConflictError('cannot block with unfinished work')
        state, reason = 'blocked', data['reference']
    elif operation == 'complete':
        if (state != 'in_progress' or not runs or not any(run.state == 'succeeded' for run in runs)
                or any(run.state in UNFINISHED | UNSAFE for run in runs)):
            raise StateConflictError('Task cannot complete')
        state, reason = 'completed', data['reference']
    tasks[task_id] = replace(task, state=state, revision=revision, reason=reason, runs=tuple(runs))


def reconstruct(events):
    """Validate the entire committed history or return no usable prefix."""
    tasks = {}
    if len(events) > MAX_EVENTS:
        raise StateIntegrityError('Store history limit')
    try:
        for sequence, event in enumerate(events, 1):
            if event['sequence'] != sequence:
                raise StateIntegrityError('broken event sequence')
            apply_event(tasks, event)
    except (StateConflictError, TypeError, KeyError):
        raise StateIntegrityError('inconsistent Store history') from None
    return tasks


def reconcile_run(run, records):
    """Diagnostic-only Journal comparison; no Store reference or authority output."""
    from itru.agent_execution_journal import JournalRecord
    outcome = None
    try:
        if type(run) is not RunSnapshot or type(records) is not tuple:
            raise StateIntegrityError('invalid reconciliation input')
        subject = subject_document(run.binding, run.ledger_identity)
        previous, journal_id, kinds, identity, prior_subject = 0, None, set(), None, None
        for record in records:
            if type(record) is not JournalRecord:
                raise StateIntegrityError('not a validated Journal record')
            doc = JournalRecord(record.canonical_json).document
            if (doc['admission']['tool_binding'] != subject['binding']
                    or doc['ledger_identity'] != subject['ledger_identity']):
                return EvidenceReconciliation('conflict', run.state, None)
            current_identity = (doc['ledger_identity']['ledger_instance_id'],
                                *doc['execution_entry']['identity'])
            current_subject = (doc['admission'], doc['execution_entry'])
            if (doc['sequence'] <= previous or doc['event_kind'] in kinds
                    or (journal_id is not None and journal_id != doc['journal_id'])
                    or (identity is not None and identity != current_identity)
                    or (prior_subject is not None and prior_subject != current_subject)):
                raise StateIntegrityError('inconsistent Journal subset')
            previous, journal_id, identity = doc['sequence'], doc['journal_id'], current_identity
            prior_subject = current_subject
            if doc['event_kind'] == 'result_observed':
                if 'entry_observed' not in kinds:
                    raise StateIntegrityError('Result summary without Entry')
                outcome = doc['result_summary']['outcome']
            kinds.add(doc['event_kind'])
        if ((run.result_identity is not None and identity is not None and run.result_identity != identity)
                or (outcome is not None and run.state in RESULT_OUTCOMES and outcome != run.state)
                or (records and run.state in ('pending', 'cancelled'))):
            return EvidenceReconciliation('conflict', run.state, outcome)
        state = 'recorded_result' if outcome else 'entry_only' if records else 'missing'
        return EvidenceReconciliation(state, run.state, outcome)
    except (ValueError, TypeError, AttributeError, KeyError):
        return EvidenceReconciliation('inconsistent', getattr(run, 'state', 'unknown'), None)
