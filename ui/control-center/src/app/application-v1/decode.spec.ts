import { describe, expect, it } from 'vitest';
import {
  decodeError,
  decodeInspectRun,
  decodeInspectRunRequest,
  decodeRunJournal,
  decodeRunJournalRequest,
} from './decode';
import {
  decodedInspection,
  errorFixture,
  inspectionFixture,
  journalFixture,
  recordFixture,
} from './fixtures';
import { grantTime, utcTime } from './validation';

type Mutable = Record<string, unknown>;
function change(value: unknown, path: string, next: unknown, remove = false): unknown {
  const copy = structuredClone(value) as Mutable;
  const keys = path.split('.');
  let target = copy;
  for (const key of keys.slice(0, -1)) target = target[key] as Mutable;
  if (remove) delete target[keys.at(-1)!];
  else target[keys.at(-1)!] = next;
  return copy;
}
const inspect = () => decodedInspection();
const read = (input: unknown) => decodeRunJournal(input, inspect());

describe('application v1.0 closed request decoding', () => {
  const common = { application_version: '1.0', source_id: 'synthetic source', source_revision: '01' };
  const inspection = { ...common, run_id: ' Run-😀 ' };
  const journal = { ...common, inspection_ref: ' synthetic inspection ' };
  const requests = [
    ['InspectRun', inspection, decodeInspectRunRequest, 'run_id'],
    ['ReadRunJournal', journal, decodeRunJournalRequest, 'inspection_ref'],
  ] as const;

  it('preserves exact opaque request text and freezes the decoded value', () => {
    const value = decodeInspectRunRequest(JSON.stringify(inspection));
    expect(value).toEqual(inspection);
    expect(Object.isFrozen(value)).toBe(true);
  });

  for (const optional of [
    {},
    { limit: 1 },
    { cursor: 'opaque cursor' },
    { limit: 100, cursor: 'next' },
  ]) {
    it(`preserves optional Journal request fields ${JSON.stringify(optional)}`, () => {
      const input = { ...journal, ...optional };
      const value = decodeRunJournalRequest(JSON.stringify(input));
      expect(value).toEqual(input);
      expect(Object.isFrozen(value)).toBe(true);
      // Omission preserves the producer's default limit of 50 and new-traversal semantics.
      expect(Object.hasOwn(value, 'limit')).toBe(Object.hasOwn(optional, 'limit'));
      expect(Object.hasOwn(value, 'cursor')).toBe(Object.hasOwn(optional, 'cursor'));
    });
  }

  for (const [name, fixture, decode, subject] of requests) {
    for (const field of ['application_version', 'source_id', 'source_revision', subject]) {
      it(`requires ${name} ${field}`, () =>
        expect(() => decode(change(fixture, field, undefined, true))).toThrow());
    }
    for (const field of ['operation', 'binding', 'payload']) {
      it(`rejects unsupported ${name} ${field}`, () =>
        expect(() => decode({ ...fixture, [field]: 'unsupported' })).toThrow());
    }
    it(`rejects unsupported ${name} versions`, () =>
      expect(() => decode({ ...fixture, application_version: '2.0' })).toThrow());
    it(`rejects duplicate logical ${name} fields`, () => {
      const duplicate = JSON.stringify(fixture).replace('{', '{"source_id":"other",');
      expect(() => decode(duplicate)).toThrow();
    });
    it(`rejects malformed ${name} identity text`, () => {
      for (const value of ['', null, true, 42, '\ud800'])
        expect(() => decode({ ...fixture, [subject]: value })).toThrow();
    });
  }

  for (const limit of [
    -1, 0, 101, 1.5, NaN, Infinity, true, '50', null, undefined, 9007199254740992,
  ]) {
    it(`rejects invalid Journal request limit ${String(limit)}`, () =>
      expect(() => decodeRunJournalRequest({ ...journal, limit })).toThrow());
  }
  for (const cursor of ['', null, undefined, 42]) {
    it(`rejects invalid Journal request cursor ${String(cursor)}`, () =>
      expect(() => decodeRunJournalRequest({ ...journal, cursor })).toThrow());
  }
  for (const token of ['1.0', '1e1', '9007199254740993']) {
    it(`rejects noncanonical numeric JSON limit ${token}`, () => {
      const input = JSON.stringify(journal).replace(/}$/, `,"limit":${token}}`);
      expect(() => decodeRunJournalRequest(input)).toThrow();
    });
  }
});

describe('application v1.0 closed response decoding', () => {
  it('preserves exact large decimal strings and timestamp spelling through JSON', () => {
    const value = decodeInspectRun(JSON.stringify(inspectionFixture()));
    expect(value.outcome).toBe('ok');
    if (value.outcome !== 'ok') throw new Error('Expected success');
    expect(value.lifecycle.run_revision).toBe('9007199254740993');
    expect(value.lifecycle.ledger_identity.domain_generation).toBe(
      '184467440737095516161844674407370955161',
    );
    const journal = read(JSON.stringify(journalFixture()));
    if (journal.outcome !== 'ok') throw new Error('Expected success');
    expect(journal.records[0].execution_entry.lease_generation).toBe('9223372036854775807');
    expect(journal.records[0].admission.grant.issued_at).toBe('2026-10-17T09:59:59.1Z');
    expect(journal.records[0].admission.grant.expires_at).toBe('2026-10-17T10:01:00Z');
    expect(journal.records[1].result_summary?.byte_count).toBe('0');
    expect(Object.isFrozen(journal.records[0].admission.grant.run.contract)).toBe(true);
  });

  for (const path of [
    'application_version',
    'source_observation',
    'lifecycle',
    'lifecycle.binding',
    'lifecycle.binding.run',
    'lifecycle.binding.run.contract',
    'task_run_history',
    'task_run_history.entries.0',
    'graph',
    'graph.nodes.0',
    'graph.dependencies.0',
    'scheduling',
    'scheduling.evaluations.0',
    'scheduling.evaluations.0.dependencies',
    'scheduling.snapshot_coverage',
    'scheduling.snapshot_coverage.observed_tasks.0',
    'continuation',
    'payload',
    'definition_metadata',
  ]) {
    it(`rejects unknown fields at InspectRun ${path}`, () => {
      const raw = inspectionFixture();
      const keys = path.split('.');
      let target: unknown = raw;
      for (const key of keys) target = (target as Mutable)[key];
      const injected =
        target && typeof target === 'object' ? { ...target, extra: 'forbidden' } : '2.0';
      expect(() => decodeInspectRun(change(raw, path, injected))).toThrow();
    });
  }
  for (const path of [
    'subject',
    'subject.binding',
    'journal_observation',
    'records.0',
    'records.0.ledger_identity',
    'records.0.execution_entry',
    'records.0.admission',
    'records.0.admission.grant',
    'records.0.admission.tool_binding',
    'records.0.admission.tool_binding.run.contract',
    'records.1.result_summary',
    'traversal',
    'comparison',
    'comparison.core_reconciliation',
    'payload',
  ]) {
    it(`rejects injected Journal content at ${path}`, () => {
      const raw = journalFixture();
      let target: unknown = raw;
      for (const key of path.split('.')) target = (target as Mutable)[key];
      expect(() =>
        read(change(raw, path, { ...(target as Mutable), payload_hex: 'forbidden-content' })),
      ).toThrow();
    });
  }
  for (const path of [
    'lifecycle.accepted_result_identity',
    'task_run_history.entries.0.accepted_result_identity',
  ]) {
    it(`requires explicit null at ${path}`, () =>
      expect(() => decodeInspectRun(change(inspectionFixture(), path, undefined, true))).toThrow());
  }
  for (const path of [
    'subject.accepted_result_identity',
    'records.0.result_summary',
    'records.1.result_summary.diagnostic_code',
    'traversal.next_cursor',
    'comparison.core_reconciliation',
  ]) {
    it(`requires a present nullable field at ${path}`, () =>
      expect(() => read(change(journalFixture(), path, undefined, true))).toThrow());
  }
  for (const value of [
    9007199254740992,
    true,
    -1,
    '0',
    '9223372036854775808',
    '01',
    '-1',
    '+1',
    '1.0',
    '1e9',
    '',
    ' 1',
    '１',
  ]) {
    it(`rejects noncanonical lossless integer ${String(value)}`, () =>
      expect(() =>
        decodeInspectRun(change(inspectionFixture(), 'lifecycle.run_revision', value)),
      ).toThrow());
  }
  for (const [path, value] of [
    ['lifecycle.task_state', 'succeeded'],
    ['lifecycle.run_state', 'completed'],
    ['scheduling.state', 'ready'],
    ['scheduling.evaluations.0.state', 'selected'],
    ['scheduling.evaluations.0.dependencies.state', 'unsafe'],
    ['continuation.eligibility', 'eligible'],
    ['continuation.action_available', true],
    ['lifecycle.binding.configuredRoute', 'invented-route'],
    ['lifecycle.binding.run.contract.operation_id', 'execute'],
    ['lifecycle.binding.run.contract.execution_mode', 'auto'],
    ['lifecycle.binding.run.contract.resource', '../secret'],
  ] as const) {
    it(`rejects incompatible InspectRun ${path}`, () =>
      expect(() => decodeInspectRun(change(inspectionFixture(), path, value))).toThrow());
  }
  for (const [path, value] of [
    ['records.0.event_kind', 'workflow_stage'],
    ['records.0.provenance', 'signature_verified'],
    ['records.0.format_version', 2],
    ['records.0.sequence', '9223372036854775808'],
    ['records.0.execution_entry.lease_generation', '0'],
    ['records.0.execution_entry.entry_time_key', '315537897600000000'],
    ['records.0.execution_entry.claim_id', 'ABC'],
    ['records.0.execution_entry.entry_time_key', '1'],
    ['records.0.admission.grant.issuer_kind', 'agent'],
    ['traversal.stop_reason', 'timeout'],
    ['comparison.coverage', 'all'],
    ['comparison.discrepancies.0', 'safe_to_resume'],
    ['comparison.core_reconciliation.state', 'repaired'],
    ['payload.status', 'available'],
  ] as const) {
    it(`rejects incompatible Journal ${path}`, () =>
      expect(() => read(change(journalFixture(), path, value))).toThrow());
  }
  it('rejects duplicate and unknown JSON keys without a usable prefix', () => {
    const json = JSON.stringify(journalFixture());
    expect(() => read(json.replace('"outcome":"ok"', '"outcome":"ok","outcome":"ok"'))).toThrow();
    expect(() =>
      read(json.replace('"byte_count":"0"', '"byte_count":"0","byte_\\u0063ount":"0"')),
    ).toThrow();
    expect(() => read(change(journalFixture(), 'exception', 'C:\\private\\store.db'))).toThrow();
    expect(() =>
      read(
        json.replace(
          '"lease_generation":"9223372036854775807"',
          '"lease_generation":9223372036854775807',
        ),
      ),
    ).toThrow();
  });
  it('rejects malformed JSON, nulls, surrogates and wrong tuple lengths', () => {
    for (const value of [
      null,
      [],
      '{}',
      '{',
      '[1,]',
      '{"x":01}',
      '{"x":NaN}',
      '{"x":1.0}',
      '{"x":-1}',
    ])
      expect(() => read(value)).toThrow();
    expect(() => decodeInspectRun(change(inspectionFixture(), 'source_id', '\uD800'))).toThrow();
    expect(() =>
      read(change(journalFixture(), 'records.0.execution_entry.identity', ['domain'])),
    ).toThrow();
  });
  it('rejects wrong source, inspection, Binding, ledger generation and subject identity', () => {
    for (const [path, value] of [
      ['source_revision', 'other'],
      ['inspection_ref', 'other'],
      ['subject.binding.tool_id', 'other'],
      ['subject.ledger_identity.domain_generation', '2'],
      ['records.0.admission.grant.run.contract.actor_id', 'other'],
      ['records.0.ledger_identity.domain_generation', '2'],
      ['records.0.execution_entry.identity.3', 'other'],
    ] as const)
      expect(() => read(change(journalFixture(), path, value))).toThrow();
  });
  it('rejects impossible traversal and comparison combinations', () => {
    for (const [path, value] of [
      ['traversal.complete', false],
      ['traversal.next_cursor', 'unexpected'],
      ['traversal.high_water', '1'],
      ['traversal.scanned_count', '1'],
      ['traversal.matched_count', '3'],
      ['comparison.coverage', 'partial'],
      ['comparison.lifecycle_revision_at_inspection', '1'],
      ['records.1.sequence', '1'],
    ] as const)
      expect(() => read(change(journalFixture(), path, value))).toThrow();
  });
  it('rejects malformed later records atomically', () => {
    expect(() =>
      read(change(journalFixture(), 'records.1.result_summary.byte_count', '65537')),
    ).toThrow();
    expect(() =>
      read(
        change(journalFixture(), 'records.1.admission.grant.expires_at', '2026-10-17T09:00:00Z'),
      ),
    ).toThrow();
  });
  it('rejects malformed graph/history without choosing a scheduler result', () => {
    expect(() =>
      decodeInspectRun(change(inspectionFixture(), 'task_run_history.latest_run_id', 'wrong')),
    ).toThrow();
    expect(() =>
      decodeInspectRun(
        change(inspectionFixture(), 'graph.dependencies.0.prerequisite_task_id', 'foreign'),
      ),
    ).toThrow();
    expect(() =>
      decodeInspectRun(
        change(
          inspectionFixture(),
          'scheduling.snapshot_coverage.observed_tasks.1.definition_reference',
          'wrong',
        ),
      ),
    ).toThrow();
  });
  it('preserves historical physical identities without rebinding them to the selected ledger', () => {
    const raw = inspectionFixture();
    raw.task_run_history.entries.unshift({
      run_id: 'SYNTHETIC-earlier-run',
      state: 'succeeded',
      revision: '9007199254740992',
      accepted_result_identity: [
        'SYNTHETIC-earlier-ledger',
        'SYNTHETIC-earlier-domain',
        'policy',
        'SYNTHETIC-earlier-issuer',
        'SYNTHETIC-earlier-grant',
      ],
    });
    const value = decodeInspectRun(raw);
    if (value.outcome !== 'ok') throw new Error('Expected success');
    expect(value.task_run_history.entries[0].accepted_result_identity?.[0]).toBe(
      'SYNTHETIC-earlier-ledger',
    );
    expect(value.task_run_history.latest_run_id).toBe('SYNTHETIC-run-z');
  });
  for (const [state, missingIdentity] of [
    ['succeeded', true],
    ['failed_before_effect', true],
    ['effect_ambiguous', true],
    ['pending', false],
    ['running', false],
    ['interrupted', false],
    ['cancelled', false],
  ] as const) {
    it(`rejects selected ${state} with a contradictory accepted identity even when history matches`, () => {
      const raw = inspectionFixture(state);
      const identity = missingIdentity
        ? null
        : inspectionFixture('succeeded').lifecycle.accepted_result_identity;
      raw.lifecycle.accepted_result_identity = identity;
      raw.task_run_history.entries[0].accepted_result_identity = identity;
      expect(() => decodeInspectRun(raw)).toThrow();
    });
    it(`rejects historical ${state} with a contradictory accepted identity`, () => {
      const raw = inspectionFixture();
      raw.task_run_history.entries.unshift({
        run_id: 'SYNTHETIC-earlier-run',
        state,
        revision: '9007199254740992',
        accepted_result_identity: missingIdentity
          ? null
          : [
              'SYNTHETIC-earlier-ledger',
              'SYNTHETIC-earlier-domain',
              'policy',
              'SYNTHETIC-earlier-issuer',
              'SYNTHETIC-earlier-grant',
            ],
      });
      expect(() => decodeInspectRun(raw)).toThrow();
    });
  }
});

describe('exact timestamps and Result summaries', () => {
  for (const text of [
    '0001-01-01T00:00:00Z',
    '2024-02-29T23:59:59.1Z',
    '9999-12-31T23:59:59.123456Z',
  ]) {
    it(`preserves valid Grant timestamp ${text}`, () => expect(grantTime(text)).toBe(text));
  }
  for (const text of [
    '0000-01-01T00:00:00Z',
    '2025-02-29T00:00:00Z',
    '2026-04-31T00:00:00Z',
    '2026-01-01T24:00:00Z',
    '2026-01-01T00:00:60Z',
    '2026-01-01T00:00:00.1234567Z',
    '2026-01-01T00:00:00.Z',
    '2026-01-01T00:00:00+00:00',
    '2026-01-01t00:00:00z',
  ]) {
    it(`rejects invalid UTC timestamp ${text}`, () => expect(() => grantTime(text)).toThrow());
  }
  it('requires six fractional digits on non-Grant timestamps', () => {
    expect(() => utcTime('2026-01-01T00:00:00Z')).toThrow();
    expect(() => utcTime('2026-01-01T00:00:00.1Z')).toThrow();
    expect(utcTime('0001-01-01T00:00:00.000000Z')).toBe('0001-01-01T00:00:00.000000Z');
  });
  it('keeps distinct summary diagnostic tables and explicit nulls', () => {
    for (const [outcome, diagnostic, valid] of [
      ['failed_before_effect', 'guard_lost', true],
      ['failed_before_effect', 'effect_ambiguous', false],
      ['effect_ambiguous', 'effect_ambiguous', true],
      ['effect_ambiguous', 'ownership_lost', false],
    ] as const) {
      const raw = journalFixture();
      raw.records[1] = recordFixture('result_observed', '2');
      raw.records[1].result_summary = { outcome, diagnostic_code: diagnostic, byte_count: null };
      if (valid) expect(read(raw).outcome).toBe('ok');
      else expect(() => read(raw)).toThrow();
    }
    expect(() =>
      read(change(journalFixture(), 'records.1.result_summary.diagnostic_code', 'read_failure')),
    ).toThrow();
    expect(() =>
      read(
        change(journalFixture(), 'records.0.result_summary', {
          outcome: 'succeeded',
          diagnostic_code: null,
          byte_count: '0',
        }),
      ),
    ).toThrow();
    expect(() =>
      read(change(journalFixture(), 'records.1.provenance', 'authoritative_entry_history')),
    ).toThrow();
  });
});

describe('closed error envelopes', () => {
  it('uses fixed UI error text without retaining supplied exception prose', () => {
    const raw = errorFixture('source_unavailable');
    raw.error.safe_message = 'private exception /secret/store.db';
    const value = decodeError(JSON.stringify(raw));
    expect(value.error.safe_message).toBe('Source unavailable.');
    expect(JSON.stringify(value)).not.toContain('secret');
    expect(value.error.retry_advice).toBe('do_not_retry');
  });
  it('rejects success prefixes, invented codes/components and incorrect retry advice', () => {
    for (const [path, value] of [
      ['records', []],
      ['error.code', 'recovered'],
      ['error.component', 'runtime'],
      ['error.retry_advice', 'retry_query_later'],
    ] as const)
      expect(() => decodeError(change(errorFixture('source_unavailable'), path, value))).toThrow();
  });
});
