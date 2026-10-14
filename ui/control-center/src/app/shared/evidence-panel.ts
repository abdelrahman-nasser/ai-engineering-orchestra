import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  signal,
} from '@angular/core';
import { EvidenceCategory, EvidenceItem, EvidenceOutcome } from '../data/models';
import { Icon } from './icon';
import { EVIDENCE_OUTCOME } from './presentation';
import { StatePanel } from './state-panel';
import { StatusBadge } from './status-badge';

export type EvidenceFilter = 'all' | EvidenceOutcome | 'unavailable';

/**
 * Evidence Explorer component.
 *
 * Surfaces execution validation checks, diagnostics, diffs, audit trails,
 * and authorization evidence. Reports failed or skipped validation first-class.
 * Supports bounded text previews, binary hex dumps, unavailable evidence states,
 * and explicit integrity badges without inventing Core authority.
 */
@Component({
  selector: 'cc-evidence-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatePanel, StatusBadge],
  styleUrl: './evidence-panel.css',
  template: `
    <div class="evidence-explorer">
      <!-- Outcome summary tally -->
      <div class="tally" role="group" aria-label="Evidence summary tally">
        @for (entry of tally(); track entry.outcome) {
          <button
            type="button"
            class="count"
            [class.active]="filter() === entry.outcome"
            [attr.data-outcome]="entry.outcome"
            [attr.aria-pressed]="filter() === entry.outcome"
            (click)="setFilter(entry.outcome)"
          >
            <strong>{{ entry.count }}</strong> {{ entry.label }}
          </button>
        }
        @if (unavailableCount() > 0) {
          <button
            type="button"
            class="count count-unavailable"
            [class.active]="filter() === 'unavailable'"
            [attr.aria-pressed]="filter() === 'unavailable'"
            (click)="setFilter('unavailable')"
          >
            <strong>{{ unavailableCount() }}</strong> unavailable
          </button>
        }
      </div>

      <!-- Filter bar when multiple items exist -->
      @if (items().length > 1) {
        <div class="filter-bar" role="toolbar" aria-label="Evidence filters">
          <span class="filter-label">Filter:</span>
          <button
            type="button"
            class="filter-pill"
            [class.active]="filter() === 'all'"
            [attr.aria-pressed]="filter() === 'all'"
            (click)="setFilter('all')"
          >
            All ({{ items().length }})
          </button>
          @for (cat of activeCategories(); track cat) {
            <button
              type="button"
              class="filter-pill"
              [class.active]="categoryFilter() === cat"
              [attr.aria-pressed]="categoryFilter() === cat"
              (click)="toggleCategory(cat)"
            >
              {{ cat }}
            </button>
          }
        </div>
      }

      @if (items().length === 0) {
        <cc-state-panel
          kind="no-evidence"
          [compact]="true"
          title="No evidence has been presented"
          message="Validation checks and execution proof have not yet been recorded for this item."
        />
      } @else if (filteredItems().length === 0) {
        <cc-state-panel
          kind="empty"
          [compact]="true"
          title="No evidence matches this filter"
          message="Try selecting 'All' or clearing active filters to inspect all records."
        >
          <button type="button" class="btn btn-ghost" (click)="resetFilters()">Clear filters</button>
        </cc-state-panel>
      } @else {
        <ul class="items" aria-label="Evidence records">
          @for (item of filteredItems(); track item.id) {
            <li class="evidence-card">
              <details
                [open]="shouldOpen(item)"
                [attr.data-outcome]="item.outcome"
                [class.is-unavailable]="item.isUnavailable"
              >
                <summary>
                  <div class="summary-left">
                    <cc-icon name="chevron-right" [size]="14" class="chevron" />
                    <div class="title-wrap">
                      <div class="category-row">
                        <span class="category-chip">{{ item.categoryLabel || item.kind }}</span>
                        @if (item.referenceId) {
                          <span class="ref-chip mono" title="Supplied Reference ID">
                            <cc-icon name="lock" [size]="11" /> {{ item.referenceId }}
                          </span>
                        }
                      </div>
                      <strong class="item-title">{{ item.title }}</strong>
                    </div>
                  </div>

                  <div class="summary-right">
                    @if (item.integrityBadge) {
                      <cc-status-badge
                        [label]="item.integrityBadge.label"
                        [tone]="item.integrityBadge.tone"
                        title="Integrity assertion supplied by data source"
                      />
                    }
                    @if (item.isUnavailable) {
                      <cc-status-badge label="Unavailable" tone="warning" />
                    } @else {
                      <cc-status-badge
                        [label]="outcome(item.outcome).label"
                        [tone]="outcome(item.outcome).tone"
                      />
                    }
                  </div>
                </summary>

                <div class="content">
                  <p class="summary-text">{{ item.summary }}</p>

                  <div class="provenance-row">
                    <span class="source mono" title="Origin source / evaluator">
                      <cc-icon name="tool" [size]="12" /> {{ item.source }}
                    </span>
                    @if (item.recordedAtLabel) {
                      <span class="chip" title="Recorded timestamp">
                        <cc-icon name="clock" [size]="12" /> {{ item.recordedAtLabel }}
                      </span>
                    }
                    @if (item.formattedByteCount) {
                      <span class="chip mono" title="Observed payload size">
                        {{ item.formattedByteCount }}
                      </span>
                    }
                  </div>

                  @if (item.isUnavailable) {
                    <div class="unavailable-callout" role="alert">
                      <cc-icon name="alert" [size]="16" class="warn-icon" />
                      <div>
                        <strong>Evidence record unavailable in current data source</strong>
                        <p>{{ item.unavailableReason }}</p>
                      </div>
                    </div>
                  }

                  @if (item.truncationNotice) {
                    <div class="truncation-banner" role="note">
                      <cc-icon name="info" [size]="14" />
                      <span>{{ item.truncationNotice }}</span>
                    </div>
                  }

                  @if (item.textPreview) {
                    <div class="preview-block">
                      <div class="preview-header">
                        <span>Bounded text preview</span>
                        @if (item.formattedByteCount) {
                          <span class="faint mono">{{ item.formattedByteCount }}</span>
                        }
                      </div>
                      <pre class="lines mono" tabindex="0" aria-label="Bounded text preview">{{ item.textPreview }}</pre>
                    </div>
                  }

                  @if (item.isBinary && item.binaryHexSample) {
                    <div class="preview-block binary-block">
                      <div class="preview-header">
                        <span class="row-flex">
                          <cc-icon name="code" [size]="13" /> Non-text representation (hex sample)
                        </span>
                        @if (item.formattedByteCount) {
                          <span class="faint mono">{{ item.formattedByteCount }}</span>
                        }
                      </div>
                      <pre class="lines hex-dump mono" tabindex="0" aria-label="Binary hex sample">{{ item.binaryHexSample }}</pre>
                    </div>
                  }

                  @if (item.lines?.length) {
                    <div class="preview-block">
                      <div class="preview-header">
                        <span>Execution output ({{ item.lines!.length }} lines)</span>
                      </div>
                      <pre class="lines mono" tabindex="0" aria-label="Execution output log">{{ item.lines!.join('\n') }}</pre>
                    </div>
                  }
                </div>
              </details>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class EvidencePanel {
  readonly items = input.required<readonly EvidenceItem[]>();

  protected readonly filter = signal<EvidenceFilter>('all');
  protected readonly categoryFilter = signal<string | null>(null);

  protected readonly unavailableCount = computed(
    () => this.items().filter((item) => item.isUnavailable).length,
  );

  protected readonly tally = computed(() =>
    (['passed', 'failed', 'skipped', 'unverified'] as const).map((outcome) => ({
      outcome,
      label: EVIDENCE_OUTCOME[outcome].label.toLowerCase(),
      count: this.items().filter((item) => item.outcome === outcome && !item.isUnavailable).length,
    })),
  );

  protected readonly activeCategories = computed(() => {
    const set = new Set<string>();
    for (const item of this.items()) {
      if (item.categoryLabel) {
        set.add(item.categoryLabel);
      } else if (item.kind) {
        set.add(item.kind);
      }
    }
    return Array.from(set);
  });

  protected readonly filteredItems = computed(() => {
    const all = this.items();
    const outcomeFilter = this.filter();
    const cat = this.categoryFilter();

    return all.filter((item) => {
      // Outcome / availability filter
      if (outcomeFilter === 'unavailable') {
        if (!item.isUnavailable) return false;
      } else if (outcomeFilter !== 'all') {
        if (item.isUnavailable || item.outcome !== outcomeFilter) return false;
      }

      // Category filter
      if (cat) {
        const itemCat = item.categoryLabel || item.kind;
        if (itemCat !== cat) return false;
      }

      return true;
    });
  });

  protected setFilter(target: EvidenceFilter): void {
    if (this.filter() === target) {
      this.filter.set('all');
    } else {
      this.filter.set(target);
    }
  }

  protected toggleCategory(cat: string): void {
    if (this.categoryFilter() === cat) {
      this.categoryFilter.set(null);
    } else {
      this.categoryFilter.set(cat);
    }
  }

  protected resetFilters(): void {
    this.filter.set('all');
    this.categoryFilter.set(null);
  }

  protected shouldOpen(item: EvidenceItem): boolean {
    return (
      item.outcome === 'failed' ||
      item.outcome === 'skipped' ||
      Boolean(item.isUnavailable) ||
      this.items().length === 1
    );
  }

  protected outcome(outcome: EvidenceOutcome) {
    return EVIDENCE_OUTCOME[outcome];
  }
}
