import {
  decimal,
  grantTime,
  list,
  nullable,
  object,
  oneOf,
  scalarText,
  utcTime,
  requireValid,
  type Value,
} from './validation';

// Closed application 1.0 projections from approved boundary v2 §§6, 8–10, 12.
// These descriptive UI values are never persisted Core records or capabilities.
export const taskState = oneOf('planned', 'in_progress', 'blocked', 'completed', 'cancelled');
export const runState = oneOf(
  'pending',
  'running',
  'succeeded',
  'failed_before_effect',
  'effect_ambiguous',
  'interrupted',
  'cancelled',
);
export const resultOutcome = oneOf('succeeded', 'failed_before_effect', 'effect_ambiguous');
export const issuerKind = oneOf('human', 'policy');
const requestFields = {
  application_version: oneOf('1.0'),
  source_id: scalarText,
  source_revision: scalarText,
};
// Inert semantic request values only. No dispatcher, client or transport is connected.
export const inspectRequestShape = object({ ...requestFields, run_id: scalarText });
export const journalRequestShape = object(
  { ...requestFields, inspection_ref: scalarText },
  {
    limit: (value: unknown) => {
      requireValid(typeof value === 'number' && Number.isInteger(value) && value >= 1 && value <= 100);
      return value;
    },
    cursor: scalarText,
  },
);
export type InspectRunRequest = Value<typeof inspectRequestShape>;
export type ReadRunJournalRequest = Value<typeof journalRequestShape>;
const count = decimal();
const positive = decimal(1n);
const int64 = decimal(1n, 9223372036854775807n);
export const ledgerIdentity = object({
  authorization_domain_id: scalarText,
  ledger_instance_id: scalarText,
  domain_generation: positive,
});
export const physicalIdentity = (
  value: unknown,
): readonly [string, string, 'human' | 'policy', string, string] => {
  // Tuple order: ledger, domain, issuer kind, issuer, grant.
  if (!Array.isArray(value) || value.length !== 5)
    throw new Error('Invalid application v1.0 identity.');
  return Object.freeze([
    scalarText(value[0]),
    scalarText(value[1]),
    issuerKind(value[2]),
    scalarText(value[3]),
    scalarText(value[4]),
  ]);
};
export const contract = object({
  task_id: scalarText,
  workflow_id: scalarText,
  stage_id: scalarText,
  role_id: scalarText,
  actor_id: scalarText,
  runtime_option_id: scalarText,
  option_id: scalarText,
  environment_id: scalarText,
  operation_id: oneOf('repository_file_read'),
  resource: (value: unknown) => {
    const text = scalarText(value);
    requireValid(
      !/[\x00-\x1f\x7f-\x9f\\*?\[\]{}]/.test(text) &&
        !/^(\/|~|[A-Za-z][A-Za-z0-9+.-]*:)/.test(text),
    );
    requireValid(text.split('/').every((part) => part !== '' && part !== '.' && part !== '..'));
    return text;
  },
  execution_mode: oneOf('lite', 'standard', 'deep', 'critical'),
});
export const run = object({ run_id: scalarText, contract });
export const binding = object({ run, tool_id: scalarText });
const accepted = nullable(physicalIdentity);
const payload = object({ status: oneOf('unavailable_not_retained') });
const envelope = {
  outcome: oneOf('ok'),
  application_version: oneOf('1.0'),
  source_id: scalarText,
  source_revision: scalarText,
  request_id: scalarText,
  received_at: utcTime,
  completed_at: utcTime,
};
export const inspectShape = object({
  ...envelope,
  inspection_ref: scalarText,
  expires_at: utcTime,
  source_observation: object({
    project_id: scalarText,
    store_id: scalarText,
    definition_set_reference: scalarText,
    graph_reference: scalarText,
    metadata_policy_reference: scalarText,
    budget_profile_reference: scalarText,
    observed_at: utcTime,
    expected_journal_id: scalarText,
    expected_ledger_identity: ledgerIdentity,
  }),
  lifecycle: object({
    task_id: scalarText,
    definition_reference: scalarText,
    task_state: taskState,
    task_revision: int64,
    run_state: runState,
    run_revision: int64,
    binding,
    ledger_identity: ledgerIdentity,
    accepted_result_identity: accepted,
  }),
  task_run_history: object({
    entries: list(
      object({
        run_id: scalarText,
        state: runState,
        revision: int64,
        accepted_result_identity: accepted,
      }),
    ),
    order: oneOf('registration_order'),
    latest_run_id: scalarText,
    complete: oneOf(true),
  }),
  definition_metadata: object({
    status: oneOf('unavailable'),
    reason: oneOf('not_in_first_slice'),
  }),
  graph: object({
    nodes: list(object({ task_id: scalarText, definition_reference: scalarText })),
    dependencies: list(object({ task_id: scalarText, prerequisite_task_id: scalarText })),
    topological_order: list(scalarText),
  }),
  scheduling: object({
    state: oneOf('evaluated', 'incomplete_snapshot', 'over_capacity'),
    max_concurrency: oneOf(1, 2),
    occupied_run_ids: list(scalarText),
    evaluations: list(
      object({
        task_id: scalarText,
        state: oneOf('unresolved', 'unsafe', 'terminal', 'active', 'manual', 'blocked', 'ready'),
        dependencies: object({
          task_id: scalarText,
          state: oneOf('ready', 'blocked', 'unresolved'),
          unsatisfied_task_ids: list(scalarText),
        }),
      }),
    ),
    selected_task_ids: list(scalarText),
    snapshot_coverage: object({
      expected_task_ids: list(scalarText),
      observed_tasks: list(
        object({
          task_id: scalarText,
          definition_reference: scalarText,
          state: taskState,
          revision: int64,
        }),
      ),
      missing_task_ids: list(scalarText),
    }),
  }),
  continuation: object({ eligibility: oneOf('unassessed'), action_available: oneOf(false) }),
  payload,
});
export type InspectRun = Value<typeof inspectShape>;
export type Binding = Value<typeof binding>;
export type PhysicalIdentity = Value<typeof physicalIdentity>;

const entryIdentity = (value: unknown): readonly [string, 'human' | 'policy', string, string] => {
  if (!Array.isArray(value) || value.length !== 4)
    throw new Error('Invalid application v1.0 identity.');
  return Object.freeze([
    scalarText(value[0]),
    issuerKind(value[1]),
    scalarText(value[2]),
    scalarText(value[3]),
  ]);
};
const hexId = (value: unknown) => {
  const text = scalarText(value);
  if (!/^[a-f0-9]{64}$/.test(text)) throw new Error('Invalid application v1.0 identifier.');
  return text;
};
export const summaryShape = object({
  outcome: resultOutcome,
  diagnostic_code: nullable(
    oneOf(
      'adapter_unavailable',
      'containment_rejected',
      'resource_missing',
      'resource_changed',
      'size_limit_exceeded',
      'read_failure',
      'guard_lost',
      'ownership_lost',
      'effect_ambiguous',
    ),
  ),
  byte_count: nullable(decimal(0n, 65536n)),
});
export const recordShape = object({
  format_version: oneOf(1),
  journal_id: scalarText,
  sequence: int64,
  recorded_at: utcTime,
  ledger_identity: ledgerIdentity,
  execution_entry: object({
    identity: entryIdentity,
    claim_id: hexId,
    executor_instance_id: hexId,
    lease_generation: int64,
    entry_time: utcTime,
    entry_time_key: decimal(0n, 315537897599999999n),
  }),
  admission: object({
    grant: object({
      grant_id: scalarText,
      run,
      authorization_domain_id: scalarText,
      issuer_kind: issuerKind,
      issuer_id: scalarText,
      provenance_reference: scalarText,
      issued_at: grantTime,
      expires_at: grantTime,
    }),
    tool_binding: binding,
    decision_time: utcTime,
  }),
  event_kind: oneOf('entry_observed', 'result_observed'),
  provenance: oneOf('original_controlled_invocation', 'authoritative_entry_history'),
  result_summary: nullable(summaryShape),
});
export const discrepancy = oneOf(
  'journal_result_without_lifecycle_acceptance',
  'lifecycle_result_without_journal_result',
  'different_outcomes',
  'different_result_identity',
  'multiple_physical_subjects',
  'state_inconsistent_with_recorded_evidence',
);
export const journalShape = object({
  ...envelope,
  inspection_ref: scalarText,
  subject: object({ binding, ledger_identity: ledgerIdentity, accepted_result_identity: accepted }),
  journal_observation: object({
    journal_id: scalarText,
    ledger_identity: ledgerIdentity,
    started_at: utcTime,
    completed_at: utcTime,
    current_high_water: decimal(0n, 9223372036854775807n),
    validation_scope: oneOf('whole_current_snapshot_semantic_validation'),
    ledger_observation: oneOf('not_performed'),
  }),
  records: list(recordShape),
  traversal: object({
    high_water: decimal(0n, 9223372036854775807n),
    last_scanned_sequence: decimal(0n, 9223372036854775807n),
    scanned_count: count,
    matched_count: count,
    complete: oneOf(true, false),
    stop_reason: oneOf('high_water_reached', 'page_limit', 'scan_limit'),
    next_cursor: nullable(scalarText),
    expires_at: utcTime,
  }),
  comparison: object({
    lifecycle_state_at_inspection: runState,
    lifecycle_revision_at_inspection: int64,
    coverage: oneOf('partial', 'complete'),
    core_reconciliation: nullable(
      object({
        state: oneOf('missing', 'entry_only', 'recorded_result', 'conflict', 'inconsistent'),
        lifecycle_state: runState,
        recorded_outcome: nullable(resultOutcome),
      }),
    ),
    discrepancies: list(discrepancy),
  }),
  payload,
});
export type RunJournal = Value<typeof journalShape>;
export type JournalRecord = Value<typeof recordShape>;

export const errorCode = oneOf(
  'invalid_request',
  'unsupported_version',
  'access_denied',
  'source_unavailable',
  'source_revision_changed',
  'run_not_found',
  'source_busy',
  'owner_unavailable',
  'identity_mismatch',
  'incompatible_source_version',
  'integrity_failure',
  'metadata_limit',
  'work_budget_exceeded',
  'deadline_exceeded',
  'inspection_expired',
  'invalid_cursor',
  'cursor_expired',
  'context_limit',
  'internal_error',
);
export const errorShape = object({
  outcome: oneOf('error'),
  application_version: oneOf('1.0'),
  request_id: scalarText,
  received_at: utcTime,
  completed_at: utcTime,
  error: object({
    code: errorCode,
    component: oneOf('request', 'source', 'lifecycle', 'journal', 'context'),
    retry_advice: oneOf('do_not_retry', 'retry_query_later', 'restart_inspection'),
    safe_message: scalarText,
  }),
});
export type ReadError = Value<typeof errorShape>;
