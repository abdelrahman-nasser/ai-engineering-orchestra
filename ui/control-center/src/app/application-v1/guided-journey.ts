import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  input,
  signal,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import type { InspectRun } from './contracts';
import { PreviewSession, runLabels, taskLabels } from './presentation';

/** Educational copy only. These are not simulated transitions or new observations. */
const lifecycleNotes: Record<InspectRun['lifecycle']['run_state'], string> = {
  pending: 'Registered and waiting. This does not establish eligibility or authority to start.',
  running: 'Reported in progress. A completion or effect outcome is not yet established.',
  succeeded: 'This Run succeeded. Task completion is a separate observation.',
  failed_before_effect:
    'No operation content-data request began; that operation had no content effect. This is not a promise about all possible effects. No automatic retry, replay or continuation is authorized.',
  effect_ambiguous:
    'The effect outcome is uncertain and this attempt is terminal. It blocks continuation and automatic retry or replay. Human assessment does not provide an uncertainty override.',
  interrupted:
    'No original Result was durably accepted after start. Invocation or effects may have occurred, and separate Journal evidence may exist.',
  cancelled:
    'Cancellation is a lifecycle observation. It does not prove that no invocation or effects occurred.',
};

const scenarioNotes: Readonly<Record<string, string>> = {
  'interrupted-success':
    'Start here: compare an interrupted lifecycle with a recorded success. Neither observation overwrites the other.',
  'partial-empty':
    'An empty page is not an empty Journal. Check the partial traversal and next-page reference.',
  'success-task-active':
    'A successful historical Run can belong to an unfinished Task. Latest means registration order.',
  'over-capacity':
    'Inspect the supplied over-capacity decision and disconnected capacity consumer; the UI does not reschedule anything.',
  'complete-empty':
    'Complete coverage has a bounded absence claim: this Journal, this subject and this high water only.',
  'entry-only': 'Entry evidence does not establish completion or an effect outcome.',
  conflict: 'Explore both physical subjects and their different outcomes. No winner is selected.',
  incomplete:
    'A missing Task observation leaves scheduler evidence incomplete; it is not a negative observation.',
  unavailable:
    'Journal evidence is unavailable while the independent lifecycle observation remains visible.',
  stale:
    'Historical Journal evidence survives this busy refresh under continuing entitlement. Original times remain visible.',
  denied:
    'Revoked entitlement clears both observations and all previously displayed subject references.',
  incompatible: 'An incompatible Journal response supplies no usable Journal evidence.',
  invalid:
    'An invalid projection supplies no usable Journal prefix. The lifecycle panel remains independent.',
  expired:
    'The inspection context for the Journal request has expired; do not interpret missing records as absence of effects.',
  exhausted: 'The read budget was exhausted. No absence or continuation eligibility is inferred.',
  'not-found': 'The selected Run was not found. No subject metadata is displayed.',
  loading: 'No observations have arrived. Loading is not a Run lifecycle state.',
  'long-text':
    'Inspect the exact long identities and lexical resource. Text wraps without shortening the subject.',
};

@Component({
  selector: 'cc-guided-journey',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './guided-journey.html',
  styleUrl: './guided-journey.css',
})
export class GuidedJourney {
  readonly session = input.required<PreviewSession>();
  readonly scenario = input.required<string>();
  private readonly element = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  protected readonly steps = ['Task', 'Approval preview', 'Run', 'Result', 'Journal'] as const;
  protected readonly step = signal(0);
  protected readonly inspection = computed(() => this.session().inspection.value);
  protected readonly journal = computed(() => this.session().journal.value);
  protected readonly summaries = computed(
    () => this.journal()?.records.filter((record) => record.result_summary !== null) ?? [],
  );
  protected readonly scenarioNote = computed(
    () => scenarioNotes[this.scenario()] ?? 'Explore the supplied synthetic observations.',
  );
  protected readonly runLabels = runLabels;
  protected readonly taskLabels = taskLabels;
  protected readonly lifecycleNotes = lifecycleNotes;
  protected readonly lifecycleExamples = Object.entries(lifecycleNotes);

  protected go(index: number): void {
    this.step.set(index);
    afterNextRender(
      () => {
        const heading = this.element.nativeElement.querySelector<HTMLElement>('#guided-step-title');
        heading?.focus({ preventScroll: true });
        heading?.scrollIntoView?.({ block: 'start' });
      },
      { injector: this.injector },
    );
  }

  protected evidence(event: Event, id: string): void {
    // A native # link would resolve against the app's base href and lose this route.
    event.preventDefault();
    const target = this.element.nativeElement.ownerDocument.getElementById(id);
    target?.focus({ preventScroll: true });
    target?.scrollIntoView?.({ block: 'start' });
  }
}
