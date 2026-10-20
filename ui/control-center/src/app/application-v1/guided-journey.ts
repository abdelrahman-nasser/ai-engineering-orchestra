import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  Injector,
  signal,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import type { InspectRun } from './contracts';
import { runLabels, taskLabels } from './presentation';
import { GuidedExplorerState } from './guided-explorer-state';

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
  protected readonly explorer = inject(GuidedExplorerState);
  protected readonly session = this.explorer.session;
  protected readonly scenario = this.explorer.selected;
  protected readonly scenarios = this.explorer.scenarios;
  private readonly element = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly locateStatus = signal('');
  protected readonly steps = this.explorer.steps;
  protected readonly step = this.explorer.step;
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
    this.explorer.go(index);
    this.locateStatus.set('');
  }

  protected selectStep(event: Event): void {
    this.go(Number((event.target as HTMLSelectElement).value));
  }

  protected choose(event: Event): void {
    this.explorer.choose((event.target as HTMLSelectElement).value);
    this.locateStatus.set('');
  }

  protected minimize(): void {
    this.explorer.minimize();
    this.focusControl('.explorer-expand');
  }

  protected exit(): void {
    this.element.nativeElement.ownerDocument
      .querySelector<HTMLElement>('.explorer-launch')
      ?.focus({ preventScroll: true });
    this.explorer.exit();
  }

  private focusControl(selector: string): void {
    const document = this.element.nativeElement.ownerDocument;
    afterNextRender(
      () => document.querySelector<HTMLElement>(selector)?.focus({ preventScroll: true }),
      { injector: this.injector },
    );
  }

  protected async locate(): Promise<void> {
    const targets = [
      'lifecycle-evidence',
      'contract-evidence',
      'run-history-evidence',
      'result-evidence',
      'journal-evidence',
    ];
    const step = this.step();
    const id = targets[step];
    const document = this.element.nativeElement.ownerDocument;
    await this.router.navigateByUrl('/application-v1-preview');
    if (this.destroyRef.destroyed || !this.explorer.active()) return;
    afterNextRender(
      () => {
        const exact = document.getElementById(id);
        const target =
          exact ?? document.getElementById(step < 3 ? 'lifecycle-evidence' : 'journal-evidence');
        this.locateStatus.set(
          exact
            ? 'Selected synthetic section located.'
            : 'Selected section unavailable. Showing its observation status.',
        );
        if (target instanceof HTMLDetailsElement) target.open = true;
        target?.focus({ preventScroll: true });
        // Explicit Locate is the only guide action that scrolls application content.
        target?.scrollIntoView?.({ block: 'start', behavior: 'instant' });
      },
      { injector: this.injector },
    );
  }
}
