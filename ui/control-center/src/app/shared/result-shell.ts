import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { ProvisionalResult } from '../data/models';
import { Icon } from './icon';
import { StatePanel } from './state-panel';

/**
 * Provisional Result presentation shell.
 *
 * Core defines no Result contract, so this shell only lays out the regions a
 * Result is likely to need (headline, summary, changed areas, open items) and
 * says so on screen. Its input is a UI-local {@link ProvisionalResult}.
 */
@Component({
  selector: 'cc-result-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatePanel],
  styles: `
    :host {
      display: block;
    }
    .banner {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
      margin-bottom: var(--space-4);
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-soft);
      border: 1px dashed color-mix(in srgb, var(--gold) 50%, transparent);
      border-radius: 999px;
      width: fit-content;
    }
    h3 {
      font-size: 17px;
      line-height: var(--leading-snug);
      margin-bottom: var(--space-2);
    }
    .summary {
      color: var(--text-muted);
      line-height: var(--leading-normal);
    }
    .regions {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--space-4);
      margin-top: var(--space-4);
    }
    .region {
      padding: var(--space-4);
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
    }
    .region ul {
      margin: var(--space-2) 0 0;
      padding-left: 18px;
      color: var(--text-muted);
      font-size: 13px;
      line-height: 1.6;
    }
    @media (max-width: 760px) {
      .regions {
        grid-template-columns: minmax(0, 1fr);
      }
    }
  `,
  template: `
    <div class="banner"><cc-icon name="alert" [size]="14" /> Provisional presentation — not a Core Result record</div>
    @if (result(); as r) {
      <h3>{{ r.headline }}</h3>
      <p class="summary">{{ r.summary }}</p>
      <div class="regions">
        <section class="region" aria-labelledby="changed-heading">
          <div class="eyebrow" id="changed-heading">Changed areas</div>
          <ul>
            @for (area of r.changedAreas; track area) {
              <li class="mono">{{ area }}</li>
            }
          </ul>
        </section>
        <section class="region" aria-labelledby="open-heading">
          <div class="eyebrow" id="open-heading">Open items</div>
          <ul>
            @for (item of r.openItems; track item) {
              <li>{{ item }}</li>
            } @empty {
              <li>None reported.</li>
            }
          </ul>
        </section>
      </div>
    } @else {
      <cc-state-panel
        kind="empty"
        [compact]="true"
        title="No result has been presented for this item yet"
        message="Results are presented provisionally once assigned work finishes validation."
      />
    }
  `,
})
export class ResultShell {
  readonly result = input.required<ProvisionalResult | null>();
}
