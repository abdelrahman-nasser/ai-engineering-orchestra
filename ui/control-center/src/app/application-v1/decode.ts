import {
  errorShape,
  inspectRequestShape,
  inspectShape,
  journalRequestShape,
  journalShape,
  type InspectRunRequest,
  type ReadRunJournalRequest,
  type InspectRun,
  type RunJournal,
  type ReadError,
  type JournalRecord,
} from './contracts';
import { parseProjection, requireValid, timeKey } from './validation';

export function decodeInspectRunRequest(input: unknown): InspectRunRequest {
  return inspectRequestShape(typeof input === 'string' ? parseProjection(input) : input);
}
export function decodeRunJournalRequest(input: unknown): ReadRunJournalRequest {
  return journalRequestShape(typeof input === 'string' ? parseProjection(input) : input);
}

export const publicErrors: Record<ReadError['error']['code'], string> = {
  invalid_request: 'Invalid request.',
  unsupported_version: 'Unsupported application version.',
  access_denied: 'Access denied; prior subject references cleared.',
  source_unavailable: 'Source unavailable.',
  source_revision_changed: 'Source revision changed; restart inspection.',
  run_not_found: 'Run not found in the authorized source.',
  source_busy: 'Source busy.',
  owner_unavailable: 'Lifecycle owner unavailable.',
  identity_mismatch: 'Observation identity mismatch.',
  incompatible_source_version: 'Incompatible source version.',
  integrity_failure: 'Snapshot integrity validation failed; observation withheld.',
  metadata_limit: 'Metadata limit exceeded.',
  work_budget_exceeded: 'Read work budget exhausted; coverage unproven.',
  deadline_exceeded: 'Read deadline exceeded.',
  inspection_expired: 'Inspection expired.',
  invalid_cursor: 'Invalid cursor; traversal not restarted.',
  cursor_expired: 'Cursor expired.',
  context_limit: 'Retained context limit exceeded.',
  internal_error: 'Read failed.',
};
export function equal(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
function unique(values: readonly string[]): void {
  requireValid(new Set(values).size === values.length);
}
function sorted(values: readonly string[]): void {
  unique(values);
  // Opaque IDs use Unicode scalar ordering, with no normalization.
  for (let i = 1; i < values.length; i++) {
    const a = Array.from(values[i - 1], (c) => c.codePointAt(0)!);
    const b = Array.from(values[i], (c) => c.codePointAt(0)!);
    let j = 0;
    while (j < a.length && j < b.length && a[j] === b[j]) j++;
    requireValid(j === a.length || (j < b.length && a[j] < b[j]));
  }
}
function receipt(v: { received_at: string; completed_at: string }): void {
  requireValid(timeKey(v.received_at) <= timeKey(v.completed_at));
}
function acceptedResultState(
  state: InspectRun['lifecycle']['run_state'],
  identity: InspectRun['lifecycle']['accepted_result_identity'],
): void {
  requireValid(
    ['succeeded', 'failed_before_effect', 'effect_ambiguous'].includes(state) ===
      (identity !== null),
  );
}
function subjectResult(
  identity: InspectRun['lifecycle']['accepted_result_identity'],
  ledger: InspectRun['lifecycle']['ledger_identity'],
): void {
  if (identity)
    requireValid(
      identity[0] === ledger.ledger_instance_id && identity[1] === ledger.authorization_domain_id,
    );
}

export function decodeInspectRun(input: unknown): InspectRun | ReadError {
  const value = typeof input === 'string' ? parseProjection(input) : input;
  if (value && typeof value === 'object' && 'outcome' in value && value.outcome === 'error')
    return decodeError(value);
  const v = inspectShape(value);
  receipt(v);
  requireValid(timeKey(v.completed_at) < timeKey(v.expires_at));
  requireValid(timeKey(v.source_observation.observed_at) <= timeKey(v.completed_at));
  const life = v.lifecycle;
  requireValid(life.task_id === life.binding.run.contract.task_id);
  requireValid(equal(life.ledger_identity, v.source_observation.expected_ledger_identity));
  acceptedResultState(life.run_state, life.accepted_result_identity);
  subjectResult(life.accepted_result_identity, life.ledger_identity);
  const history = v.task_run_history;
  history.entries.forEach((entry) =>
    acceptedResultState(entry.state, entry.accepted_result_identity),
  );
  unique(history.entries.map((entry) => entry.run_id));
  requireValid(
    history.entries.length > 0 && history.entries.at(-1)!.run_id === history.latest_run_id,
  );
  const target = history.entries.find((entry) => entry.run_id === life.binding.run.run_id);
  requireValid(
    target &&
      target.state === life.run_state &&
      target.revision === life.run_revision &&
      equal(target.accepted_result_identity, life.accepted_result_identity),
  );
  // Historical summaries carry their own physical identity. They are not rebound
  // to the selected Run's ledger; no per-history-entry ledger observation exists.
  const nodes = v.graph.nodes.map((node) => node.task_id);
  unique(nodes);
  unique(v.graph.topological_order);
  requireValid(
    v.graph.topological_order.length === nodes.length &&
      nodes.every((id) => v.graph.topological_order.includes(id)),
  );
  const node = v.graph.nodes.find((item) => item.task_id === life.task_id);
  requireValid(node?.definition_reference === life.definition_reference);
  unique(
    v.graph.dependencies.map((edge) => JSON.stringify([edge.task_id, edge.prerequisite_task_id])),
  );
  for (const edge of v.graph.dependencies)
    requireValid(
      nodes.includes(edge.task_id) &&
        nodes.includes(edge.prerequisite_task_id) &&
        v.graph.topological_order.indexOf(edge.prerequisite_task_id) <
          v.graph.topological_order.indexOf(edge.task_id),
    );
  const schedule = v.scheduling;
  const coverage = schedule.snapshot_coverage;
  sorted(coverage.expected_task_ids);
  sorted(coverage.missing_task_ids);
  requireValid(
    nodes.length === coverage.expected_task_ids.length &&
      nodes.every((id) => coverage.expected_task_ids.includes(id)),
  );
  unique(coverage.observed_tasks.map((task) => task.task_id));
  requireValid(coverage.observed_tasks.length + coverage.missing_task_ids.length === nodes.length);
  for (const observed of coverage.observed_tasks) {
    requireValid(
      v.graph.nodes.some(
        (item) =>
          item.task_id === observed.task_id &&
          item.definition_reference === observed.definition_reference,
      ),
    );
    requireValid(!coverage.missing_task_ids.includes(observed.task_id));
    if (observed.task_id === life.task_id)
      requireValid(observed.state === life.task_state && observed.revision === life.task_revision);
  }
  requireValid(coverage.missing_task_ids.every((id) => nodes.includes(id)));
  requireValid(coverage.observed_tasks.some((task) => task.task_id === life.task_id));
  unique(schedule.evaluations.map((evaluation) => evaluation.task_id));
  requireValid(schedule.evaluations.length === nodes.length);
  for (const evaluation of schedule.evaluations) {
    requireValid(
      nodes.includes(evaluation.task_id) && evaluation.dependencies.task_id === evaluation.task_id,
    );
    sorted(evaluation.dependencies.unsatisfied_task_ids);
    requireValid(evaluation.dependencies.unsatisfied_task_ids.every((id) => nodes.includes(id)));
  }
  unique(schedule.selected_task_ids);
  unique(schedule.occupied_run_ids);
  requireValid(schedule.selected_task_ids.every((id) => nodes.includes(id)));
  requireValid(schedule.state === 'evaluated' || schedule.selected_task_ids.length === 0);
  requireValid(coverage.missing_task_ids.length > 0 === (schedule.state === 'incomplete_snapshot'));
  // No readiness, capacity, selection, Task completion or authority is computed here.
  return v;
}

export function recordIdentity(record: JournalRecord) {
  return Object.freeze([
    record.ledger_identity.ledger_instance_id,
    ...record.execution_entry.identity,
  ]);
}
function validateRecord(v: JournalRecord): void {
  const entry = v.execution_entry,
    admission = v.admission,
    grant = admission.grant;
  requireValid(equal(grant.run, admission.tool_binding.run));
  requireValid(
    equal(entry.identity, [
      grant.authorization_domain_id,
      grant.issuer_kind,
      grant.issuer_id,
      grant.grant_id,
    ]),
  );
  requireValid(v.ledger_identity.authorization_domain_id === entry.identity[0]);
  requireValid(
    timeKey(grant.issued_at) <= timeKey(admission.decision_time) &&
      timeKey(admission.decision_time) < timeKey(grant.expires_at),
  );
  requireValid(timeKey(admission.decision_time) <= timeKey(entry.entry_time));
  requireValid(timeKey(entry.entry_time) === BigInt(entry.entry_time_key));
  if (v.event_kind === 'entry_observed') requireValid(v.result_summary === null);
  else {
    const summary = v.result_summary;
    requireValid(summary && v.provenance === 'original_controlled_invocation');
    if (summary.outcome === 'succeeded')
      requireValid(summary.diagnostic_code === null && summary.byte_count !== null);
    else {
      requireValid(summary.byte_count === null && summary.diagnostic_code !== null);
      if (summary.outcome === 'failed_before_effect')
        requireValid(summary.diagnostic_code !== 'effect_ambiguous');
      if (summary.outcome === 'effect_ambiguous')
        requireValid(
          summary.diagnostic_code !== 'guard_lost' && summary.diagnostic_code !== 'ownership_lost',
        );
    }
  }
}

/** Match to the dated inspection. This validates descriptive consistency only;
 * whole-Journal validation and cross-page reconciliation remain Core responsibilities. */
export function decodeRunJournal(input: unknown, inspection: InspectRun): RunJournal | ReadError {
  const value = typeof input === 'string' ? parseProjection(input) : input;
  if (value && typeof value === 'object' && 'outcome' in value && value.outcome === 'error')
    return decodeError(value);
  const v = journalShape(value);
  receipt(v);
  requireValid(
    v.source_id === inspection.source_id &&
      v.source_revision === inspection.source_revision &&
      v.inspection_ref === inspection.inspection_ref,
  );
  requireValid(
    equal(v.subject, {
      binding: inspection.lifecycle.binding,
      ledger_identity: inspection.lifecycle.ledger_identity,
      accepted_result_identity: inspection.lifecycle.accepted_result_identity,
    }),
  );
  const observation = v.journal_observation,
    traversal = v.traversal,
    comparison = v.comparison;
  requireValid(
    observation.journal_id === inspection.source_observation.expected_journal_id &&
      equal(observation.ledger_identity, v.subject.ledger_identity),
  );
  requireValid(
    timeKey(observation.started_at) <= timeKey(observation.completed_at) &&
      timeKey(observation.completed_at) <= timeKey(v.completed_at),
  );
  requireValid(traversal.expires_at === inspection.expires_at);
  requireValid(BigInt(traversal.high_water) <= BigInt(observation.current_high_water));
  requireValid(BigInt(traversal.last_scanned_sequence) <= BigInt(traversal.high_water));
  requireValid(traversal.scanned_count === traversal.last_scanned_sequence);
  requireValid(
    BigInt(traversal.matched_count) <= BigInt(traversal.scanned_count) &&
      BigInt(traversal.matched_count) >= BigInt(v.records.length),
  );
  requireValid(traversal.complete === (traversal.high_water === traversal.last_scanned_sequence));
  requireValid(
    traversal.complete
      ? traversal.next_cursor === null && traversal.stop_reason === 'high_water_reached'
      : traversal.next_cursor !== null && traversal.stop_reason !== 'high_water_reached',
  );
  requireValid(
    comparison.lifecycle_state_at_inspection === inspection.lifecycle.run_state &&
      comparison.lifecycle_revision_at_inspection === inspection.lifecycle.run_revision,
  );
  sorted(comparison.discrepancies);
  requireValid(comparison.coverage === (traversal.complete ? 'complete' : 'partial'));
  requireValid(
    traversal.complete
      ? comparison.core_reconciliation !== null
      : comparison.core_reconciliation === null,
  );
  if (comparison.core_reconciliation)
    requireValid(comparison.core_reconciliation.lifecycle_state === inspection.lifecycle.run_state);
  if (!traversal.complete)
    requireValid(
      comparison.discrepancies.every(
        (code) => code === 'multiple_physical_subjects' || code === 'different_outcomes',
      ),
    );
  let sequence = 0n;
  const subjects = new Map<string, JournalRecord>();
  requireValid(v.records.length <= 100);
  for (const record of v.records) {
    validateRecord(record);
    requireValid(
      record.journal_id === observation.journal_id &&
        equal(record.ledger_identity, observation.ledger_identity),
    );
    requireValid(equal(record.admission.tool_binding, v.subject.binding));
    requireValid(
      BigInt(record.sequence) > sequence &&
        BigInt(record.sequence) <= BigInt(traversal.last_scanned_sequence),
    );
    sequence = BigInt(record.sequence);
    const key = JSON.stringify(recordIdentity(record)),
      previous = subjects.get(key);
    if (previous) {
      requireValid(
        equal(previous.execution_entry, record.execution_entry) &&
          equal(previous.admission, record.admission),
      );
      requireValid(
        previous.event_kind === 'entry_observed' && record.event_kind === 'result_observed',
      );
    }
    subjects.set(key, record);
  }
  return v;
}

export function decodeError(input: unknown): ReadError {
  const v = errorShape(typeof input === 'string' ? parseProjection(input) : input);
  receipt(v);
  const advice = ['source_busy', 'owner_unavailable', 'deadline_exceeded'].includes(v.error.code)
    ? 'retry_query_later'
    : ['inspection_expired', 'cursor_expired', 'source_revision_changed'].includes(v.error.code)
      ? 'restart_inspection'
      : 'do_not_retry';
  requireValid(v.error.retry_advice === advice);
  // The design does not specify literal server messages. Never retain/display
  // supplied prose; use fixed UI text rather than risk exposing an exception.
  return Object.freeze({
    ...v,
    error: Object.freeze({ ...v.error, safe_message: publicErrors[v.error.code] }),
  });
}
