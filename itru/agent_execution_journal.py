"""Content-free execution observations, not Result or execution authority.

Importing this module performs no storage, clock, native or discovery operation.
Only original Result membership or the fixed audited ledger reader can supply
positive observation provenance. Deserialized records are descriptive only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import re
import sys
from weakref import ref

MAX_RECORD_BYTES = 1048576
MAX_SEQUENCE = 9223372036854775807
MAX_TIME_KEY = 315537897599999999
_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")
_BEFORE = frozenset(('adapter_unavailable', 'containment_rejected', 'resource_missing',
    'resource_changed', 'size_limit_exceeded', 'read_failure', 'guard_lost', 'ownership_lost'))
_AMBIGUOUS = (_BEFORE - {'guard_lost', 'ownership_lost'}) | {'effect_ambiguous'}
_BODY_KEYS = frozenset(('format_version', 'ledger_identity', 'execution_entry',
    'admission', 'event_kind', 'provenance', 'result_summary'))
_RECORD_KEYS = _BODY_KEYS | {'journal_id', 'sequence', 'recorded_at'}
_FACT_MEMBERS = {}
_HISTORY_MEMBERS = {}
_RECORDER_MEMBERS = {}


class JournalIntegrityError(ValueError):
    def __init__(self):
        super().__init__('Execution Journal integrity failure')


class JournalMetadataLimit(ValueError):
    def __init__(self):
        super().__init__('Execution Journal metadata limit')


def _object(value, keys):
    if type(value) is not dict or frozenset(value) != frozenset(keys):
        raise JournalIntegrityError()
    return value


def _text(value):
    if type(value) is not str or not value:
        raise JournalIntegrityError()
    value.encode('utf-8', 'strict')
    return value


def _integer(value, minimum=1, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise JournalIntegrityError()
    return value


def _time(value):
    if type(value) is not str or _TIME.fullmatch(value) is None:
        raise JournalIntegrityError()
    try:
        instant = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        raise JournalIntegrityError() from None
    delta = instant - datetime(1, 1, 1)
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def _clock_text(value):
    if (type(value) is not datetime or value.tzinfo is None
            or value.utcoffset() is None or value.utcoffset().total_seconds() != 0):
        raise JournalIntegrityError()
    value = value.astimezone(timezone.utc)
    text = (f'{value.year:04}-{value.month:02}-{value.day:02}T{value.hour:02}:'
            f'{value.minute:02}:{value.second:02}.{value.microsecond:06}Z')
    _time(text)
    return text


def _json_tree(value):
    if value is None or type(value) is int:
        return
    if type(value) is str:
        value.encode('utf-8', 'strict')
        return
    if type(value) is list:
        for item in value:
            _json_tree(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for key, item in value.items():
            _json_tree(key)
            _json_tree(item)
        return
    raise JournalIntegrityError()


def _encode(value):
    _json_tree(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)
    if len(text.encode('utf-8')) > MAX_RECORD_BYTES:
        raise JournalMetadataLimit()
    return text


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise JournalIntegrityError()
        value[key] = item
    return value


def _no_number(value):
    raise JournalIntegrityError()


def _decode(text):
    if type(text) is not str or len(text.encode('utf-8')) > MAX_RECORD_BYTES:
        raise JournalIntegrityError()
    try:
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_float=_no_number, parse_constant=_no_number)
        if _encode(value) != text:
            raise JournalIntegrityError()
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise JournalIntegrityError() from None


def _ledger_document(identity):
    from itru.authorization_domain_ownership import AuthorizationDomainIdentity
    if type(identity) is not AuthorizationDomainIdentity:
        raise JournalIntegrityError()
    return dict(authorization_domain_id=identity.authorization_domain_id,
                ledger_instance_id=identity.ledger_instance_id,
                domain_generation=identity.domain_generation)


def _entry_document(entry):
    from itru._execution_entry_and_controlled_invocation import _ExecutionEntry
    if type(entry) is not _ExecutionEntry:
        raise JournalIntegrityError()
    return dict(identity=list(entry.identity), claim_id=entry.claim_id,
        executor_instance_id=entry.executor_instance_id, lease_generation=entry.lease_generation,
        entry_time=entry.entry_time, entry_time_key=entry.entry_time_key)


def _subject_document(identity, entry, admission):
    from itru.sqlite_agent_execution_dispatch_admission_store import _admission_document
    return dict(ledger_identity=_ledger_document(identity), execution_entry=_entry_document(entry),
                admission=_admission_document(admission))


def _subject_key(document):
    return (document['ledger_identity']['ledger_instance_id'],
            *document['execution_entry']['identity'])


def _subject_only(document):
    return {key: document[key] for key in ('ledger_identity', 'execution_entry', 'admission')}


def _require_same_subject(expected, actual):
    if expected != actual:
        raise JournalIntegrityError()


def _validate_body(body):
    from itru.sqlite_agent_execution_dispatch_admission_store import _decode_admission, _canonical_json
    _object(body, _BODY_KEYS)
    _integer(body['format_version'], 1, 1)
    ledger = _object(body['ledger_identity'], ('authorization_domain_id', 'ledger_instance_id', 'domain_generation'))
    _text(ledger['authorization_domain_id']); _text(ledger['ledger_instance_id'])
    _integer(ledger['domain_generation'])
    entry = _object(body['execution_entry'], ('identity', 'claim_id', 'executor_instance_id',
                   'lease_generation', 'entry_time', 'entry_time_key'))
    dispatch = entry['identity']
    if type(dispatch) is not list or len(dispatch) != 4 or dispatch[1] not in ('human', 'policy'):
        raise JournalIntegrityError()
    for item in dispatch:
        _text(item)
    _text(entry['claim_id']); _text(entry['executor_instance_id'])
    if any(re.fullmatch(r'[0-9a-f]{64}', entry[key]) is None for key in ('claim_id', 'executor_instance_id')):
        raise JournalIntegrityError()
    _integer(entry['lease_generation'], 1, MAX_SEQUENCE)
    _integer(entry['entry_time_key'], 0, MAX_TIME_KEY)
    if _time(entry['entry_time']) != entry['entry_time_key']:
        raise JournalIntegrityError()
    admission = _decode_admission(_canonical_json(body['admission']))
    grant = admission.grant
    if tuple(dispatch) != (grant.authorization_domain_id, grant.issuer_kind, grant.issuer_id, grant.grant_id):
        raise JournalIntegrityError()
    if ledger['authorization_domain_id'] != dispatch[0] or admission.grant.run != admission.tool_binding.run:
        raise JournalIntegrityError()
    if _time(admission.decision_time) > entry['entry_time_key']:
        raise JournalIntegrityError()
    if body['event_kind'] not in ('entry_observed', 'result_observed'):
        raise JournalIntegrityError()
    if body['provenance'] not in ('original_controlled_invocation', 'authoritative_entry_history'):
        raise JournalIntegrityError()
    summary = body['result_summary']
    if body['event_kind'] == 'entry_observed':
        if summary is not None:
            raise JournalIntegrityError()
    else:
        if body['provenance'] != 'original_controlled_invocation':
            raise JournalIntegrityError()
        _object(summary, ('outcome', 'diagnostic_code', 'byte_count'))
        outcome, code, count = summary['outcome'], summary['diagnostic_code'], summary['byte_count']
        if outcome == 'succeeded':
            if code is not None:
                raise JournalIntegrityError()
            _integer(count, 0, 65536)
        elif outcome in ('failed_before_effect', 'effect_ambiguous'):
            if count is not None or type(code) is not str or code not in (_BEFORE if outcome == 'failed_before_effect' else _AMBIGUOUS):
                raise JournalIntegrityError()
        else:
            raise JournalIntegrityError()
    _encode(body)
    return body


def _validate_record(document):
    _object(document, _RECORD_KEYS)
    _text(document['journal_id']); _integer(document['sequence'], 1, MAX_SEQUENCE)
    _time(document['recorded_at'])
    _validate_body({key: document[key] for key in _BODY_KEYS})
    _encode(document)
    return document


class _NoRestore:
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise TypeError('trusted observation source required')

    def __copy__(self):
        raise TypeError('observation cannot be copied')

    def __deepcopy__(self, memo):
        raise TypeError('observation cannot be copied')

    def __reduce_ex__(self, protocol):
        raise TypeError('observation has no trusted serialized format')

    def __getstate__(self):
        raise TypeError('observation has no trusted serialized format')

    def __setstate__(self, state):
        raise TypeError('observation cannot be restored')


@dataclass(frozen=True, slots=True, init=False, weakref_slot=True)
class _Fact(_NoRestore):
    body_json: str

    def __getstate__(self):
        raise TypeError('observation has no trusted serialized format')

    def __setstate__(self, state):
        raise TypeError('observation cannot be restored')


@dataclass(frozen=True, slots=True, init=False, weakref_slot=True)
class _LedgerHistory(_NoRestore):
    ledger_json: str
    dispatch: tuple
    subject_json: str | None

    def __getstate__(self):
        raise TypeError('history provenance cannot be serialized')

    def __setstate__(self, state):
        raise TypeError('history provenance cannot be restored')


def _register(value, table, state):
    key = id(value)
    table[key] = (ref(value, lambda ignored: table.pop(key, None)), os.getpid(), state)
    return value


def _recognized(value, cls, table, state):
    member = table.get(id(value))
    if (type(value) is cls and member is not None and member[0]() is value
            and member[1] == os.getpid() and member[2] == state):
        return True
    table.pop(id(value), None)
    return False


def _trusted_fact(value):
    if type(value) is not _Fact or type(getattr(value, 'body_json', None)) is not str:
        _FACT_MEMBERS.pop(id(value), None)
        return False
    return _recognized(value, _Fact, _FACT_MEMBERS, getattr(value, 'body_json', None))


def _trusted_history(value):
    if type(value) is not _LedgerHistory:
        return False
    state = tuple(getattr(value, key, None) for key in ('ledger_json', 'dispatch', 'subject_json'))
    if (type(state[0]) is not str or type(state[1]) is not tuple
            or any(type(item) is not str for item in state[1])
            or (state[2] is not None and type(state[2]) is not str)):
        _HISTORY_MEMBERS.pop(id(value), None)
        return False
    return _recognized(value, _LedgerHistory, _HISTORY_MEMBERS, state)


def _mint_history(store, identity, dispatch, entry, admission):
    from itru.sqlite_agent_execution_dispatch_admission_store import (
        SqliteAgentExecutionDispatchAdmissionStore, _JOURNAL_HISTORY_READER,
    )
    caller = sys._getframe(1)
    if (type(store) is not SqliteAgentExecutionDispatchAdmissionStore
            or caller.f_code is not _JOURNAL_HISTORY_READER
            or caller.f_locals.get('self') is not store):
        raise JournalIntegrityError()
    ledger_json = _encode(_ledger_document(identity))
    subject_json = None
    if entry is not None:
        subject = _subject_document(identity, entry, admission)
        _validate_body(dict(format_version=1, **subject, event_kind='entry_observed',
            provenance='authoritative_entry_history', result_summary=None))
        subject_json = _encode(subject)
    history = object.__new__(_LedgerHistory)
    for key, value in dict(ledger_json=ledger_json, dispatch=tuple(dispatch), subject_json=subject_json).items():
        object.__setattr__(history, key, value)
    return _register(history, _HISTORY_MEMBERS, (ledger_json, tuple(dispatch), subject_json))


def _mint_fact(body):
    caller = sys._getframe(1)
    owner = caller.f_locals.get('self')
    history = caller.f_locals.get('history')
    if (caller.f_code not in _FACT_SOURCE_CODES or not _trusted_recorder(owner)
            or not _trusted_history(history) or history.subject_json is None
            or _subject_only(body) != _decode(history.subject_json)
            or _decode(history.ledger_json) != _ledger_document(owner._store.configuration.ledger_identity)):
        raise JournalIntegrityError()
    if caller.f_code is ExecutionJournalRecorder.observe_result.__code__:
        from itru.agent_execution_result import _is_authoritative_result
        result = caller.f_locals.get('result')
        if not _is_authoritative_result(result):
            raise JournalIntegrityError()
        expected = dict(outcome=result.outcome,
            diagnostic_code=None if result.diagnostic is None else result.diagnostic.code,
            byte_count=None if result.payload is None else result.payload.byte_count)
        if (body['provenance'] != 'original_controlled_invocation'
                or body['result_summary'] != (expected if body['event_kind'] == 'result_observed' else None)):
            raise JournalIntegrityError()
    elif caller.f_code is ExecutionJournalRecorder.reconcile.__code__:
        if (body['provenance'] != 'authoritative_entry_history' or body['event_kind'] != 'entry_observed'
                or history.dispatch != caller.f_locals['subject_identity'][1:]):
            raise JournalIntegrityError()
    elif body['provenance'] != 'original_controlled_invocation' or body['event_kind'] != 'entry_observed':
        raise JournalIntegrityError()
    text = _encode(_validate_body(body))
    fact = object.__new__(_Fact)
    object.__setattr__(fact, 'body_json', text)
    return _register(fact, _FACT_MEMBERS, text)


def _trusted_recorder(value):
    if type(value) is not ExecutionJournalRecorder:
        return False
    return _recognized(value, ExecutionJournalRecorder, _RECORDER_MEMBERS,
        (getattr(value, '_store', None), getattr(value, '_ledger', None)))


@dataclass(frozen=True, slots=True, repr=False)
class JournalRecord:
    """Descriptive immutable canonical bytes; never a live Result or capability."""
    canonical_json: str

    @property
    def document(self):
        return _validate_record(_decode(self.canonical_json))

    def __repr__(self):
        return 'JournalRecord(descriptive_history)'

    def __setstate__(self, state):
        raise TypeError('JournalRecord cannot be mutated by restoration')


@dataclass(frozen=True, slots=True)
class JournalReceipt:
    outcome: str
    subject_identity: tuple
    event_kinds: tuple
    records: tuple = ()

    def __setstate__(self, state):
        raise TypeError('JournalReceipt cannot be mutated by restoration')


@dataclass(frozen=True, slots=True)
class JournalReconciliation:
    state: str
    records: tuple = ()
    receipt: JournalReceipt | None = None

    def __setstate__(self, state):
        raise TypeError('JournalReconciliation cannot be mutated by restoration')


class ExecutionJournalRecorder:
    """Configured metadata audience boundary; no tool, retry or lifecycle API."""
    __slots__ = ('_store', '_ledger', '__weakref__')

    def __init_subclass__(cls, **kwargs):
        raise TypeError('Journal recorder subclassing is unsupported')

    def __getstate__(self):
        raise TypeError('Journal recorder is not serialized authority')

    def __setstate__(self, state):
        raise TypeError('Journal recorder cannot be restored')

    def __reduce_ex__(self, protocol):
        raise TypeError('Journal recorder cannot be copied or serialized')

    def __init__(self, store, ledger_store, *, metadata_authorized=False):
        from itru.sqlite_agent_execution_journal_store import SqliteExecutionJournalStore
        from itru.sqlite_agent_execution_dispatch_admission_store import SqliteAgentExecutionDispatchAdmissionStore
        if (metadata_authorized is not True or type(store) is not SqliteExecutionJournalStore
                or type(ledger_store) is not SqliteAgentExecutionDispatchAdmissionStore):
            raise JournalIntegrityError()
        identity = _ledger_document(store.configuration.ledger_identity)
        configuration = ledger_store.configuration
        if identity != dict(authorization_domain_id=configuration.authorization_domain_id,
                ledger_instance_id=configuration.ledger_instance_id, domain_generation=configuration.domain_generation):
            raise JournalIntegrityError()
        self._store, self._ledger = store, ledger_store
        _register(self, _RECORDER_MEMBERS, (store, ledger_store))

    def _history(self, dispatch):
        if not _trusted_recorder(self):
            raise JournalIntegrityError()
        history = self._ledger._read_execution_journal_history(dispatch)
        if (not _trusted_history(history) or history.dispatch != tuple(dispatch)
                or _decode(history.ledger_json) != _ledger_document(self._store.configuration.ledger_identity)):
            raise JournalIntegrityError()
        return history

    def _append(self, subject, facts):
        return self._store.append(tuple(facts))

    def observe_result(self, result):
        from itru.agent_execution_result import _is_authoritative_result
        from itru.agent_operation_tool_registry import _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID
        if (not _trusted_recorder(self) or not _is_authoritative_result(result)
                or result.tool_binding.tool_id != _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID):
            raise JournalIntegrityError()
        history = self._history(result.execution_entry.identity)
        if history.subject_json is None:
            raise JournalIntegrityError()
        subject = _decode(history.subject_json)
        from itru.sqlite_agent_execution_dispatch_admission_store import _binding_document
        if (subject['ledger_identity'] != _ledger_document(result.ledger_identity)
                or subject['execution_entry'] != _entry_document(result.execution_entry)
                or subject['admission']['tool_binding'] != _binding_document(result.tool_binding)):
            raise JournalIntegrityError()
        summary = dict(outcome=result.outcome,
            diagnostic_code=None if result.diagnostic is None else result.diagnostic.code,
            byte_count=None if result.payload is None else result.payload.byte_count)
        existing = self._store.lookup(_subject_key(subject), subject=subject)
        facts = []
        if not existing:
            facts.append(_mint_fact(dict(format_version=1, **subject, event_kind='entry_observed',
                provenance='original_controlled_invocation', result_summary=None)))
        facts.append(_mint_fact(dict(format_version=1, **subject, event_kind='result_observed',
            provenance='original_controlled_invocation', result_summary=summary)))
        if not _is_authoritative_result(result):
            raise JournalIntegrityError()
        return self._append(subject, facts)

    def _observe_original_entry(self, coordinator, entry, admission):
        from itru._execution_entry_and_controlled_invocation import _JOURNAL_RECORD_CODE
        caller = sys._getframe(1)
        if (not _trusted_recorder(self) or caller.f_code is not _JOURNAL_RECORD_CODE or caller.f_locals.get('self') is not coordinator
                or coordinator._a.store is not self._ledger):
            raise JournalIntegrityError()
        history = self._history(entry.identity)
        if history.subject_json is None:
            raise JournalIntegrityError()
        subject = _decode(history.subject_json)
        expected = _subject_document(self._store.configuration.ledger_identity, entry, admission)
        _require_same_subject(expected, subject)
        existing = self._store.lookup(_subject_key(subject), subject=subject)
        if existing:
            return JournalReceipt('existing', _subject_key(subject), ('entry_observed',), existing)
        fact = _mint_fact(dict(format_version=1, **subject, event_kind='entry_observed',
            provenance='original_controlled_invocation', result_summary=None))
        return self._append(subject, (fact,))

    def reconcile(self, subject_identity, *, append_missing=False):
        from itru.sqlite_agent_execution_dispatch_admission_store import SqliteAdmissionStoreIntegrityError
        try:
            if not _trusted_recorder(self) or type(subject_identity) is not tuple or len(subject_identity) != 5:
                raise JournalIntegrityError()
            if subject_identity[0] != self._store.configuration.ledger_identity.ledger_instance_id:
                raise JournalIntegrityError()
            history = self._history(subject_identity[1:])
            records = self._store.lookup(subject_identity)
            if history.subject_json is None:
                if records:
                    raise JournalIntegrityError()
                return JournalReconciliation('no_entry_evidence')
            subject = _decode(history.subject_json)
            if any(_subject_only(item.document) != subject for item in records):
                raise JournalIntegrityError()
            receipt = None
            if not records and append_missing:
                fact = _mint_fact(dict(format_version=1, **subject, event_kind='entry_observed',
                    provenance='authoritative_entry_history', result_summary=None))
                receipt = self._append(subject, (fact,))
                if receipt.outcome == 'integrity_failure':
                    return JournalReconciliation('integrity_failure', (), receipt)
                if receipt.outcome not in ('appended', 'existing'):
                    return JournalReconciliation('evidence_unavailable', (), receipt)
                records = receipt.records
            state = 'recorded_result' if any(item.document['event_kind'] == 'result_observed' for item in records) else 'unresolved_result'
            return JournalReconciliation(state, records, receipt)
        except (JournalIntegrityError, SqliteAdmissionStoreIntegrityError):
            return JournalReconciliation('integrity_failure')
        except Exception:
            return JournalReconciliation('evidence_unavailable')


_FACT_SOURCE_CODES = frozenset((ExecutionJournalRecorder.observe_result.__code__,
    ExecutionJournalRecorder._observe_original_entry.__code__, ExecutionJournalRecorder.reconcile.__code__))
