import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { EvidenceItem, EvidenceOutcome } from '../data/models';
import { EVIDENCE_OUTCOME } from './presentation';
import { StatusBadge } from './status-badge';

/**
 * Evidence panel. Failed or skipped validation is surfaced first-class rather
 * than hidden, matching the framework rule to report failed/skipped checks.
 */
@Component({
  selector: 'cc-evidence-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StatusBadge],
  styleUrl: './evidence-panel.css',
  template: `
    <div class="tally" role="group" aria-label="Evidence summary">
      @for (entry of tally(); track entry.outcome) {
        <span class="count" [attr.data-outcome]="entry.outcome">
          <strong>{{ entry.count }}</strong> {{ entry.label }}
        </span>
      }
    </div>

    @if (items().length === 0) {
      <p class="muted empty">No evidence has been presented.</p>
    } @else {
      <ul class="items">
        @for (item of items(); track item.id) {
          <li>
            <details [open]="item.outcome === 'failed' || item.outcome === 'skipped'">
              <summary>
                <span class="title">
                  <span class="kind">{{ item.kind }}</span>
                  <strong>{{ item.title }}</strong>
                </span>
                <cc-status-badge [label]="outcome(item.outcome).label" [tone]="outcome(item.outcome).tone" />
              </summary>
              <div class="content">
                <p>{{ item.summary }}</p>
                <p class="source faint mono">{{ item.source }}</p>
                @if (item.lines?.length) {
                  <pre class="lines mono">{{ item.lines!.join('\n') }}</pre>
                }
              </div>
            </details>
          </li>
        }
      </ul>
    }
  `,
})
export class EvidencePanel {
  readonly items = input.required<readonly EvidenceItem[]>();

  protected readonly tally = computed(() =>
    (['passed', 'failed', 'skipped', 'unverified'] as const).map((outcome) => ({
      outcome,
      label: EVIDENCE_OUTCOME[outcome].label.toLowerCase(),
      count: this.items().filter((item) => item.outcome === outcome).length,
    })),
  );

  protected outcome(outcome: EvidenceOutcome) {
    return EVIDENCE_OUTCOME[outcome];
  }
}
