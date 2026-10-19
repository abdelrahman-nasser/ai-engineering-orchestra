import type { InspectRun, ReadError } from './contracts';
import { decodeInspectRun } from './decode';
import { PreviewSession, type PreviewContext } from './presentation';
import { timeKey } from './validation';

/** Entirely fabricated metadata, independent of existing mock adapters. */
export const previewContext: PreviewContext = Object.freeze({
  principal: 'SYNTHETIC-reader',
  policy: 'SYNTHETIC-policy-v1',
  source: 'SYNTHETIC-source',
  revision: 'SYNTHETIC-revision',
  entitled: true,
});
const t = '2026-10-17T10:00:00.000000Z';
const end = '2026-10-17T10:00:01.000000Z';
const expiry = '2026-10-17T10:15:00.000000Z';
const ledger = {
  authorization_domain_id: 'SYNTHETIC-domain',
  ledger_instance_id: 'SYNTHETIC-ledger',
  domain_generation: '184467440737095516161844674407370955161',
};
const run = {
  run_id: 'SYNTHETIC-run-z',
  contract: {
    task_id: 'SYNTHETIC-task-a',
    workflow_id: 'standard-change',
    stage_id: 'implement',
    role_id: 'software-engineer',
    actor_id: 'SYNTHETIC-actor',
    runtime_option_id: 'SYNTHETIC-runtime',
    option_id: 'SYNTHETIC-inference',
    environment_id: 'SYNTHETIC-environment',
    operation_id: 'repository_file_read',
    resource: 'synthetic/example.txt',
    execution_mode: 'standard',
  },
};
const binding = { run, tool_id: 'SYNTHETIC-tool-v1' };
const envelope = {
  outcome: 'ok',
  application_version: '1.0',
  source_id: previewContext.source,
  source_revision: previewContext.revision,
  request_id: 'SYNTHETIC-request',
  received_at: t,
  completed_at: end,
};
const revision = '9007199254740993';

export function inspectionFixture(state: InspectRun['lifecycle']['run_state'] = 'interrupted') {
  const taskState = ['interrupted', 'failed_before_effect', 'effect_ambiguous'].includes(state)
    ? 'blocked'
    : state === 'cancelled'
      ? 'cancelled'
      : 'in_progress';
  const accepted = ['succeeded', 'failed_before_effect', 'effect_ambiguous'].includes(state)
    ? [
        ledger.ledger_instance_id,
        ledger.authorization_domain_id,
        'human',
        'SYNTHETIC-issuer',
        'SYNTHETIC-grant',
      ]
    : null;
  const history = [{ run_id: run.run_id, state, revision, accepted_result_identity: accepted }];
  if (state === 'succeeded')
    history.push({
      run_id: 'SYNTHETIC-run-a',
      state: 'pending',
      revision: '9007199254740994',
      accepted_result_identity: null,
    });
  const taskRevision = state === 'succeeded' ? '9007199254740994' : revision;
  return structuredClone({
    ...envelope,
    inspection_ref: 'SYNTHETIC-inspection',
    expires_at: expiry,
    source_observation: {
      project_id: 'SYNTHETIC-project',
      store_id: 'SYNTHETIC-store',
      definition_set_reference: 'SYNTHETIC-definitions-v1',
      graph_reference: 'SYNTHETIC-graph-v1',
      metadata_policy_reference: previewContext.policy,
      budget_profile_reference: 'SYNTHETIC-budget-v1',
      observed_at: t,
      expected_journal_id: 'SYNTHETIC-journal',
      expected_ledger_identity: ledger,
    },
    lifecycle: {
      task_id: run.contract.task_id,
      definition_reference: 'SYNTHETIC-definition-a',
      task_state: taskState,
      task_revision: taskRevision,
      run_state: state,
      run_revision: revision,
      binding,
      ledger_identity: ledger,
      accepted_result_identity: accepted,
    },
    task_run_history: {
      entries: history,
      order: 'registration_order',
      latest_run_id: history.at(-1)!.run_id,
      complete: true,
    },
    definition_metadata: { status: 'unavailable', reason: 'not_in_first_slice' },
    graph: {
      nodes: [
        { task_id: run.contract.task_id, definition_reference: 'SYNTHETIC-definition-a' },
        { task_id: 'SYNTHETIC-task-b', definition_reference: 'SYNTHETIC-definition-b' },
        {
          task_id: 'SYNTHETIC-task-disconnected',
          definition_reference: 'SYNTHETIC-definition-disconnected',
        },
      ],
      dependencies: [{ task_id: 'SYNTHETIC-task-b', prerequisite_task_id: run.contract.task_id }],
      topological_order: [run.contract.task_id, 'SYNTHETIC-task-b', 'SYNTHETIC-task-disconnected'],
    },
    scheduling: {
      state: 'evaluated',
      max_concurrency: 2,
      occupied_run_ids:
        state === 'succeeded'
          ? ['SYNTHETIC-run-a', 'SYNTHETIC-disconnected-pending']
          : ['SYNTHETIC-disconnected-pending'],
      evaluations: [
        {
          task_id: run.contract.task_id,
          state: state === 'succeeded' ? 'active' : 'unsafe',
          dependencies: { task_id: run.contract.task_id, state: 'ready', unsatisfied_task_ids: [] },
        },
        {
          task_id: 'SYNTHETIC-task-b',
          state: 'blocked',
          dependencies: {
            task_id: 'SYNTHETIC-task-b',
            state: 'blocked',
            unsatisfied_task_ids: [run.contract.task_id],
          },
        },
        {
          task_id: 'SYNTHETIC-task-disconnected',
          state: 'active',
          dependencies: {
            task_id: 'SYNTHETIC-task-disconnected',
            state: 'ready',
            unsatisfied_task_ids: [],
          },
        },
      ],
      selected_task_ids: [],
      snapshot_coverage: {
        expected_task_ids: [
          run.contract.task_id,
          'SYNTHETIC-task-b',
          'SYNTHETIC-task-disconnected',
        ],
        observed_tasks: [
          {
            task_id: run.contract.task_id,
            definition_reference: 'SYNTHETIC-definition-a',
            state: taskState,
            revision: taskRevision,
          },
          {
            task_id: 'SYNTHETIC-task-b',
            definition_reference: 'SYNTHETIC-definition-b',
            state: 'planned',
            revision: '1',
          },
          {
            task_id: 'SYNTHETIC-task-disconnected',
            definition_reference: 'SYNTHETIC-definition-disconnected',
            state: 'in_progress',
            revision: '2',
          },
        ],
        missing_task_ids: [] as string[],
      },
    },
    continuation: { eligibility: 'unassessed', action_available: false },
    payload: { status: 'unavailable_not_retained' },
  });
}
export function recordFixture(
  kind: 'entry_observed' | 'result_observed' = 'entry_observed',
  sequence = '1',
  grantId = 'SYNTHETIC-grant',
) {
  return structuredClone({
    format_version: 1,
    journal_id: 'SYNTHETIC-journal',
    sequence,
    recorded_at: end,
    ledger_identity: ledger,
    execution_entry: {
      identity: [ledger.authorization_domain_id, 'human', 'SYNTHETIC-issuer', grantId],
      claim_id: 'a'.repeat(64),
      executor_instance_id: 'b'.repeat(64),
      lease_generation: '9223372036854775807',
      entry_time: t,
      entry_time_key: timeKey(t).toString(),
    },
    admission: {
      grant: {
        grant_id: grantId,
        run,
        authorization_domain_id: ledger.authorization_domain_id,
        issuer_kind: 'human',
        issuer_id: 'SYNTHETIC-issuer',
        provenance_reference: 'SYNTHETIC-provenance',
        issued_at: '2026-10-17T09:59:59.1Z',
        expires_at: '2026-10-17T10:01:00Z',
      },
      tool_binding: binding,
      decision_time: t,
    },
    event_kind: kind,
    provenance: 'original_controlled_invocation',
    result_summary:
      kind === 'entry_observed'
        ? null
        : {
            outcome: 'succeeded',
            diagnostic_code: null as string | null,
            byte_count: '0' as string | null,
          },
  });
}
export function journalFixture() {
  return structuredClone({
    ...envelope,
    inspection_ref: 'SYNTHETIC-inspection',
    subject: {
      binding,
      ledger_identity: ledger,
      accepted_result_identity: null as string[] | null,
    },
    journal_observation: {
      journal_id: 'SYNTHETIC-journal',
      ledger_identity: ledger,
      started_at: t,
      completed_at: end,
      current_high_water: '2',
      validation_scope: 'whole_current_snapshot_semantic_validation',
      ledger_observation: 'not_performed',
    },
    records: [recordFixture(), recordFixture('result_observed', '2')],
    traversal: {
      high_water: '2',
      last_scanned_sequence: '2',
      scanned_count: '2',
      matched_count: '2',
      complete: true,
      stop_reason: 'high_water_reached',
      next_cursor: null as string | null,
      expires_at: expiry,
    },
    comparison: {
      lifecycle_state_at_inspection: 'interrupted',
      lifecycle_revision_at_inspection: revision,
      coverage: 'complete',
      core_reconciliation: {
        state: 'recorded_result',
        lifecycle_state: 'interrupted',
        recorded_outcome: 'succeeded' as string | null,
      } as { state: string; lifecycle_state: string; recorded_outcome: string | null } | null,
      discrepancies: ['journal_result_without_lifecycle_acceptance'],
    },
    payload: { status: 'unavailable_not_retained' },
  });
}
export function errorFixture(code: ReadError['error']['code'] = 'owner_unavailable') {
  const retry_advice = ['source_busy', 'owner_unavailable', 'deadline_exceeded'].includes(code)
    ? 'retry_query_later'
    : ['inspection_expired', 'cursor_expired', 'source_revision_changed'].includes(code)
      ? 'restart_inspection'
      : 'do_not_retry';
  return {
    outcome: 'error',
    application_version: '1.0',
    request_id: 'SYNTHETIC-error',
    received_at: t,
    completed_at: end,
    error: { code, component: 'journal', retry_advice, safe_message: 'Synthetic public error.' },
  };
}
export const scenarios = [
  ['interrupted-success', 'Interrupted lifecycle / recorded success'],
  ['partial-empty', 'Empty partial Journal page'],
  ['success-task-active', 'Successful Run / Task still in progress'],
  ['over-capacity', 'Core over-capacity decision'],
  ['complete-empty', 'Complete traversal / no matching evidence'],
  ['entry-only', 'Entry only'],
  ['conflict', 'Conflicting physical subjects'],
  ['incomplete', 'Missing graph observation'],
  ['unavailable', 'Unavailable Journal'],
  ['stale', 'Stale after busy refresh'],
  ['denied', 'Entitlement revoked'],
  ['incompatible', 'Incompatible source'],
  ['invalid', 'Invalid projection'],
  ['expired', 'Expired inspection'],
  ['exhausted', 'Read budget exhausted'],
  ['not-found', 'Run not found'],
  ['loading', 'Loading'],
  ['long-text', 'Long synthetic identities and resource'],
] as const;

/** Presentation stress only; exact replacements keep every supplied reference coherent. */
const longTextValues: Readonly<Record<string, string>> = {
  'SYNTHETIC-run-z': `SYNTHETIC-run-${'identity'.repeat(24)}`,
  'SYNTHETIC-task-a': `SYNTHETIC-task-a-${'subject'.repeat(24)}`,
  'SYNTHETIC-grant': `SYNTHETIC-grant-${'physical'.repeat(24)}`,
  'synthetic/example.txt': `synthetic/${'resource'.repeat(24)}/example.txt`,
};
function withLongText<T>(value: T): T {
  return JSON.parse(JSON.stringify(value, (_key, item: unknown) =>
    typeof item === 'string' ? longTextValues[item] ?? item : item,
  )) as T;
}
export function scenarioSession(id: string): PreviewSession {
  const session = new PreviewSession(previewContext);
  const delivery = session.deliveryContext;
  if (id === 'loading') return session;
  const successfulHistory = id === 'success-task-active' || id === 'over-capacity';
  const baseInspection = inspectionFixture(successfulHistory ? 'succeeded' : 'interrupted');
  const inspection = id === 'long-text' ? withLongText(baseInspection) : baseInspection;
  if (id === 'over-capacity') {
    inspection.scheduling.max_concurrency = 1;
    inspection.scheduling.state = 'over_capacity';
  }
  if (id === 'incomplete') {
    inspection.scheduling.state = 'incomplete_snapshot';
    inspection.scheduling.snapshot_coverage.observed_tasks.splice(1, 1);
    inspection.scheduling.snapshot_coverage.missing_task_ids.push('SYNTHETIC-task-b');
    inspection.scheduling.evaluations[1].state = 'unresolved';
    inspection.scheduling.evaluations[1].dependencies.state = 'unresolved';
  }
  if (id === 'not-found') {
    session.receiveInspection(errorFixture('run_not_found'), delivery);
    return session;
  }
  session.receiveInspection(inspection, delivery);
  const baseJournal = journalFixture();
  const journal = id === 'long-text' ? withLongText(baseJournal) : baseJournal;
  if (successfulHistory) {
    journal.subject.accepted_result_identity = inspection.lifecycle.accepted_result_identity;
    journal.comparison.lifecycle_state_at_inspection = 'succeeded';
    journal.comparison.core_reconciliation!.lifecycle_state = 'succeeded';
    journal.comparison.discrepancies = [];
  }
  if (id === 'partial-empty') {
    journal.records = [];
    journal.traversal.high_water = '9007199254740994';
    journal.journal_observation.current_high_water = '9007199254740994';
    journal.traversal.last_scanned_sequence = '1000';
    journal.traversal.scanned_count = '1000';
    journal.traversal.matched_count = '0';
    journal.traversal.complete = false;
    journal.traversal.stop_reason = 'scan_limit';
    journal.traversal.next_cursor = 'SYNTHETIC-cursor';
    journal.comparison.coverage = 'partial';
    journal.comparison.core_reconciliation = null;
    journal.comparison.discrepancies = [];
  }
  if (id === 'complete-empty') {
    journal.records = [];
    journal.traversal.matched_count = '0';
    journal.comparison.discrepancies = [];
    journal.comparison.core_reconciliation!.state = 'missing';
    journal.comparison.core_reconciliation!.recorded_outcome = null;
  }
  if (id === 'entry-only') {
    journal.records = [recordFixture()];
    journal.traversal.matched_count = '1';
    journal.comparison.discrepancies = [];
    journal.comparison.core_reconciliation!.state = 'entry_only';
    journal.comparison.core_reconciliation!.recorded_outcome = null;
  }
  if (id === 'conflict') {
    const other = recordFixture('result_observed', '4', 'SYNTHETIC-other-grant');
    other.result_summary!.outcome = 'effect_ambiguous';
    other.result_summary!.diagnostic_code = 'effect_ambiguous';
    other.result_summary!.byte_count = null;
    journal.records.push(recordFixture('entry_observed', '3', 'SYNTHETIC-other-grant'), other);
    journal.journal_observation.current_high_water = '4';
    journal.traversal.high_water = '4';
    journal.traversal.last_scanned_sequence = '4';
    journal.traversal.scanned_count = '4';
    journal.traversal.matched_count = '4';
    journal.comparison.discrepancies = ['different_outcomes', 'multiple_physical_subjects'];
    journal.comparison.core_reconciliation!.state = 'conflict';
    journal.comparison.core_reconciliation!.recorded_outcome = null;
  }
  const failures: Record<string, ReadError['error']['code']> = {
    unavailable: 'source_unavailable',
    incompatible: 'incompatible_source_version',
    expired: 'inspection_expired',
    exhausted: 'work_budget_exceeded',
  };
  if (failures[id]) session.receiveJournal(errorFixture(failures[id]), delivery);
  else if (id === 'invalid')
    session.receiveJournal({ ...journal, preview: 'SYNTHETIC-forbidden-content' }, delivery);
  else {
    session.receiveJournal(journal, delivery);
    if (id === 'stale') session.receiveJournal(errorFixture('source_busy'), delivery);
    if (id === 'denied') session.receiveJournal(errorFixture('access_denied'), delivery);
  }
  return session;
}
export function decodedInspection(): InspectRun {
  const value = decodeInspectRun(inspectionFixture());
  if (value.outcome !== 'ok') throw new Error('Synthetic fixture invalid');
  return value;
}
