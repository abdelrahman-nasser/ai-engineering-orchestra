import {
  ApprovalLevel,
  ApprovalPresentationState,
  AvailabilityState,
  ContinuationStatus,
  EvidenceOutcome,
  Level,
  PresentationState,
  TaskStatus,
  Tone,
} from '../data/models';

/** Display metadata for a value: label text plus visual tone. */
export interface Descriptor {
  readonly label: string;
  readonly tone: Tone;
}

export const CONTINUATION_STATUS: Readonly<Record<ContinuationStatus, Descriptor>> = {
  available: { label: 'Continuation available', tone: 'success' },
  unavailable: { label: 'Not resumable', tone: 'muted' },
  blocked: { label: 'Continuation blocked', tone: 'warning' },
  interrupted: { label: 'Interrupted', tone: 'danger' },
  completed: { label: 'Completed run', tone: 'neutral' },
  missing: { label: 'No continuation info', tone: 'muted' },
  stale: { label: 'Stale observation', tone: 'warning' },
};

export const TASK_STATUS: Readonly<Record<TaskStatus, Descriptor>> = {
  planned: { label: 'Planned', tone: 'neutral' },
  in_progress: { label: 'In progress', tone: 'info' },
  blocked: { label: 'Blocked', tone: 'warning' },
  completed: { label: 'Completed', tone: 'success' },
  cancelled: { label: 'Cancelled', tone: 'muted' },
};

/** UI-local. Not a Core lifecycle. */
export const PRESENTATION_STATE: Readonly<Record<PresentationState, Descriptor>> = {
  'not-started': { label: 'Not started', tone: 'neutral' },
  'in-progress': { label: 'In progress', tone: 'info' },
  'needs-attention': { label: 'Needs attention', tone: 'warning' },
  finished: { label: 'Finished', tone: 'success' },
  unknown: { label: 'No observation', tone: 'muted' },
};

export const APPROVAL_LEVEL: Readonly<Record<ApprovalLevel, Descriptor>> = {
  none: { label: 'No approval', tone: 'muted' },
  review: { label: 'Review', tone: 'info' },
  explicit: { label: 'Explicit', tone: 'warning' },
  protected: { label: 'Protected', tone: 'danger' },
};

export const APPROVAL_STATE: Readonly<Record<ApprovalPresentationState, Descriptor>> = {
  awaiting: { label: 'No evidence yet', tone: 'warning' },
  granted: { label: 'Granted', tone: 'success' },
  denied: { label: 'Denied', tone: 'danger' },
};

export const AVAILABILITY: Readonly<Record<AvailabilityState, Descriptor>> = {
  available: { label: 'Available', tone: 'success' },
  unavailable: { label: 'Unavailable', tone: 'danger' },
  unknown: { label: 'Unknown', tone: 'muted' },
};

export const EVIDENCE_OUTCOME: Readonly<Record<EvidenceOutcome, Descriptor>> = {
  passed: { label: 'Passed', tone: 'success' },
  failed: { label: 'Failed', tone: 'danger' },
  skipped: { label: 'Skipped', tone: 'warning' },
  unverified: { label: 'Unverified', tone: 'muted' },
};

export const LEVEL: Readonly<Record<Level, Descriptor>> = {
  low: { label: 'Low', tone: 'success' },
  medium: { label: 'Medium', tone: 'info' },
  high: { label: 'High', tone: 'warning' },
  critical: { label: 'Critical', tone: 'danger' },
};

/** Turns `security-sensitive-change` into `Security sensitive change`. */
export function humanize(identifier: string): string {
  const spaced = identifier.replace(/[-_]+/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
