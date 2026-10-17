import type { InspectRun, ReadError, RunJournal } from './contracts';
import { decodeInspectRun, decodeRunJournal } from './decode';
import { requireValid } from './validation';

export type DisplayStatus =
  | 'loading'
  | 'ready'
  | 'partial'
  | 'complete-empty'
  | 'stale'
  | 'not-found'
  | 'unavailable'
  | 'denied'
  | 'incompatible'
  | 'invalid'
  | 'expired'
  | 'exhausted';
export interface Observation<T> {
  readonly status: DisplayStatus;
  readonly value: T | null;
  readonly failure: ReadError | null;
}
/** Synthetic caller context only; this is not authentication or entitlement enforcement. */
export interface PreviewContext {
  readonly principal: string;
  readonly policy: string;
  readonly source: string;
  readonly revision: string;
  readonly entitled: boolean;
}
const empty = <T>(status: DisplayStatus, failure: ReadError | null = null): Observation<T> => ({
  status,
  value: null,
  failure,
});
function sameContext(a: PreviewContext, b: PreviewContext): boolean {
  return (
    a.principal === b.principal &&
    a.policy === b.policy &&
    a.source === b.source &&
    a.revision === b.revision &&
    a.entitled === b.entitled
  );
}
function statusFor(error: ReadError): DisplayStatus {
  switch (error.error.code) {
    case 'access_denied':
      return 'denied';
    case 'run_not_found':
      return 'not-found';
    case 'unsupported_version':
    case 'incompatible_source_version':
      return 'incompatible';
    case 'inspection_expired':
    case 'cursor_expired':
    case 'source_revision_changed':
      return 'expired';
    case 'metadata_limit':
    case 'work_budget_exceeded':
    case 'context_limit':
      return 'exhausted';
    case 'invalid_request':
    case 'identity_mismatch':
    case 'integrity_failure':
    case 'invalid_cursor':
      return 'invalid';
    default:
      return 'unavailable';
  }
}
function failed<T>(
  previous: Observation<T>,
  error: ReadError,
  context: PreviewContext,
): Observation<T> {
  const historicalAllowed = [
    'source_busy',
    'source_unavailable',
    'owner_unavailable',
    'deadline_exceeded',
  ].includes(error.error.code);
  if (context.entitled && historicalAllowed && previous.value)
    return { status: 'stale', value: previous.value, failure: error };
  return empty(statusFor(error), error);
}

/** In-memory display state for synthetic demonstrations. No stores, services,
 * persistent cache, polling, commands, or transport are connected. */
export class PreviewSession {
  inspection: Observation<InspectRun> = empty('loading');
  journal: Observation<RunJournal> = empty('loading');
  private context: PreviewContext;
  private invalidated = false;
  constructor(context: PreviewContext) {
    this.context = Object.freeze({ ...context });
  }
  /** Capture before a synthetic delivery. Object identity prevents late publication
   * even after switching away from and back to the same named context. */
  get deliveryContext(): PreviewContext {
    return this.context;
  }

  changeContext(next: PreviewContext): void {
    if (!next.entitled || !sameContext(next, this.context)) {
      this.inspection = empty(next.entitled ? 'loading' : 'denied');
      this.journal = empty(next.entitled ? 'loading' : 'denied');
      this.invalidated = false;
    }
    this.context = Object.freeze({ ...next });
  }
  private clearFor(error: ReadError): boolean {
    if (error.error.code !== 'access_denied' && error.error.code !== 'source_revision_changed')
      return false;
    this.inspection = empty(statusFor(error), error);
    this.journal = empty(statusFor(error), error);
    this.invalidated = true;
    if (error.error.code === 'access_denied')
      this.context = Object.freeze({ ...this.context, entitled: false });
    return true;
  }
  receiveInspection(input: unknown, deliveryContext: PreviewContext): void {
    if (this.invalidated || !this.context.entitled || deliveryContext !== this.context) return;
    try {
      const v = decodeInspectRun(input);
      if (v.outcome === 'error') {
        if (!this.clearFor(v)) {
          this.inspection = failed(this.inspection, v, this.context);
          if (!this.inspection.value) this.journal = empty('unavailable');
        }
        return;
      }
      requireValid(
        v.source_id === this.context.source &&
          v.source_revision === this.context.revision &&
          v.source_observation.metadata_policy_reference === this.context.policy,
      );
      this.inspection = { status: 'ready', value: v, failure: null };
      this.journal = empty('loading');
    } catch {
      this.inspection = empty('invalid');
      this.journal = empty('invalid');
    }
  }
  receiveJournal(input: unknown, deliveryContext: PreviewContext): void {
    if (this.invalidated || !this.context.entitled || deliveryContext !== this.context) return;
    const inspection = this.inspection.value;
    if (!inspection) {
      this.journal = empty('unavailable');
      return;
    }
    try {
      const v = decodeRunJournal(input, inspection);
      if (v.outcome === 'error') {
        if (!this.clearFor(v)) this.journal = failed(this.journal, v, this.context);
        return;
      }
      this.journal = {
        status: !v.traversal.complete
          ? 'partial'
          : v.traversal.matched_count === '0'
            ? 'complete-empty'
            : 'ready',
        value: v,
        failure: null,
      };
    } catch {
      this.journal = empty('invalid');
    }
  }
}

export const unsupported = Object.freeze({
  configuredRoute: 'Unavailable — no approved route mapping',
  approvals: 'Unavailable — no approval queue in application v1.0',
  continuation: 'Unassessed — continuation unavailable',
  payload: 'unavailable_not_retained',
});
/** Explicit maps retain the canonical values; none establishes readiness/authority. */
export const taskLabels: Record<InspectRun['lifecycle']['task_state'], string> = {
  planned: 'Planned',
  in_progress: 'In progress',
  blocked: 'Blocked',
  completed: 'Completed',
  cancelled: 'Cancelled',
};
export const runLabels: Record<InspectRun['lifecycle']['run_state'], string> = {
  pending: 'Pending',
  running: 'Running',
  succeeded: 'Succeeded',
  failed_before_effect: 'Failed before effect',
  effect_ambiguous: 'Effect ambiguous',
  interrupted: 'Interrupted',
  cancelled: 'Cancelled',
};
export const schedulerLabels: Record<InspectRun['scheduling']['state'], string> = {
  evaluated: 'Evaluated',
  incomplete_snapshot: 'Incomplete snapshot',
  over_capacity: 'Over capacity',
};
