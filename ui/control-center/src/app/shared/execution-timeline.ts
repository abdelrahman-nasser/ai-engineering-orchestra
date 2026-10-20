import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  Injector,
  input,
  model,
  output,
  signal,
} from '@angular/core';
import { TimelineEntry, TimelineKind } from '../data/models';
import { EvidencePanel } from './evidence-panel';
import { Icon, IconName } from './icon';
import { ResultShell } from './result-shell';
import { StatePanel } from './state-panel';
import { StatusBadge } from './status-badge';

const KIND_ICON: Readonly<Record<TimelineKind, IconName>> = {
  stage: 'branch',
  agent: 'agents',
  'quality-gate': 'check',
  approval: 'shield',
  tool: 'tool',
  note: 'file',
};

export type TimelineFilter = 'all' | 'result' | 'evidence' | 'attention';

/**
 * Execution Timeline component.
 *
 * Renders UI-local {@link TimelineEntry} values in data-source supplied order.
 * It is not a Journal view: Core defines no Journal yet, so no canonical
 * ordering or authoritative timestamps are asserted.
 *
 * Features:
 * - Chronological display with clear timestamps and markers.
 * - Operator filtering (all, with result, with evidence, attention, actor, tool).
 * - Interactive item selection with expanded detail inspector.
 * - Result and Evidence linkage and inspection.
 * - Explicit data-source display order disclaimer.
 */
@Component({
  selector: 'cc-execution-timeline',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatePanel, StatusBadge, ResultShell, EvidencePanel],
  styleUrl: './execution-timeline.css',
  template: `
    <div class="timeline-wrapper" role="region" aria-label="Execution timeline" tabindex="-1">
      <!-- Data source ordering disclaimer -->
      <div class="timeline-disclaimer" role="note">
        <cc-icon name="info" [size]="15" class="info-icon" />
        <span
          >Mock display order only · This timeline does not establish canonical Journal
          ordering.</span
        >
      </div>

      @if (entries().length === 0) {
        <cc-state-panel
          kind="empty"
          [compact]="true"
          title="No timeline entries to show"
          message="Recorded actions and event milestones will appear here as work progresses."
        />
      } @else {
        <!-- Filter toolbar -->
        <div class="filter-toolbar" role="toolbar" aria-label="Timeline filters">
          <div class="filter-group">
            <button
              type="button"
              class="filter-btn"
              [class.active]="filter() === 'all' && !actorFilter() && !toolFilter()"
              [attr.aria-pressed]="filter() === 'all' && !actorFilter() && !toolFilter()"
              (click)="resetFilters()"
            >
              All ({{ entries().length }})
            </button>
            @if (hasAnyResult()) {
              <button
                type="button"
                class="filter-btn"
                [class.active]="filter() === 'result'"
                [attr.aria-pressed]="filter() === 'result'"
                (click)="setFilter('result')"
              >
                With Result ({{ resultCount() }})
              </button>
            }
            @if (hasAnyEvidence()) {
              <button
                type="button"
                class="filter-btn"
                [class.active]="filter() === 'evidence'"
                [attr.aria-pressed]="filter() === 'evidence'"
                (click)="setFilter('evidence')"
              >
                With Evidence ({{ evidenceCount() }})
              </button>
            }
            @if (hasAnyAttention()) {
              <button
                type="button"
                class="filter-btn filter-attention"
                [class.active]="filter() === 'attention'"
                [attr.aria-pressed]="filter() === 'attention'"
                (click)="setFilter('attention')"
              >
                Attention ({{ attentionCount() }})
              </button>
            }
          </div>

          <!-- Secondary filter chips for actors and tools -->
          @if (availableActors().length > 1 || availableTools().length > 0) {
            <div class="filter-group secondary-filters">
              @for (actor of availableActors(); track actor) {
                <button
                  type="button"
                  class="filter-chip mono"
                  [class.active]="actorFilter() === actor"
                  [attr.aria-pressed]="actorFilter() === actor"
                  (click)="toggleActor(actor)"
                  title="Filter by actor"
                >
                  <cc-icon name="agents" [size]="12" /> {{ actor }}
                </button>
              }
              @for (tool of availableTools(); track tool) {
                <button
                  type="button"
                  class="filter-chip mono"
                  [class.active]="toolFilter() === tool"
                  [attr.aria-pressed]="toolFilter() === tool"
                  (click)="toggleTool(tool)"
                  title="Filter by tool"
                >
                  <cc-icon name="tool" [size]="12" /> {{ formatTool(tool) }}
                </button>
              }
            </div>
          }
        </div>

        @if (filteredEntries().length === 0) {
          <cc-state-panel
            kind="empty"
            [compact]="true"
            title="No matching timeline entries"
            message="No events match the selected filter criteria."
          >
            <button type="button" class="btn btn-ghost" (click)="resetFilters()">
              Clear filters
            </button>
          </cc-state-panel>
        } @else {
          <div class="timeline-layout" [class.has-selection]="selectedEntry()">
            <div class="timeline-list-pane">
              <ol class="timeline" aria-label="Execution timeline">
                @for (entry of filteredEntries(); track entry.id) {
                  <li
                    class="entry"
                    [attr.data-state]="entry.state"
                    [class.is-selected]="selectedId() === entry.id"
                  >
                    <button
                      type="button"
                      class="entry-trigger"
                      [attr.data-entry-id]="entry.id"
                      [attr.aria-pressed]="selectedId() === entry.id"
                      (click)="selectEntry(entry)"
                    >
                      <span class="marker" aria-hidden="true">
                        <cc-icon [name]="icon(entry)" [size]="14" />
                      </span>

                      <span class="body">
                        <span class="head">
                          <span class="title-wrap">
                            <span class="kind-tag">{{ entry.kind }}</span>
                            <strong class="entry-title">{{ entry.title }}</strong>
                          </span>
                          <span class="badge-cluster">
                            @if (entry.hasResult) {
                              <span
                                class="result-pill chip"
                                [attr.data-outcome]="entry.result?.outcome"
                              >
                                <cc-icon name="check" [size]="11" />
                                {{ entry.result?.outcomeLabel }}
                              </span>
                            }
                            <cc-status-badge [label]="entry.stateLabel" [tone]="entry.stateTone" />
                          </span>
                        </span>

                        @if (entry.detail) {
                          <span class="detail">{{ entry.detail }}</span>
                        }

                        <span class="meta">
                          <span class="timestamp" title="Display timestamp">
                            <cc-icon name="clock" [size]="12" /> {{ entry.atLabel }}
                          </span>
                          @if (entry.stageId) {
                            <span class="chip" title="Workflow Stage">{{ entry.stageId }}</span>
                          }
                          @if (entry.actorId) {
                            <span class="chip mono" title="Actor">
                              <cc-icon name="agents" [size]="12" /> {{ entry.actorId }}
                            </span>
                          }
                          @if (entry.toolId) {
                            <span class="chip mono" title="Tool">
                              <cc-icon name="tool" [size]="12" /> {{ formatTool(entry.toolId) }}
                            </span>
                          }
                          @if (entry.executionEntryRef) {
                            <span class="chip mono" title="Execution Entry Claim">
                              <cc-icon name="lock" [size]="12" /> {{ entry.executionEntryRef }}
                            </span>
                          }
                          @if (entry.hasEvidence) {
                            <span
                              class="chip chip-evidence"
                              [class.chip-warn]="entry.hasUnavailableEvidence"
                              title="Evidence records"
                            >
                              <cc-icon name="file" [size]="12" /> {{ entry.evidenceCount }} evidence
                            </span>
                          }
                        </span>

                        <span class="action-bar">
                          <span class="action-hint">
                            {{
                              selectedId() === entry.id
                                ? 'Viewing details'
                                : 'Click to inspect event'
                            }}
                          </span>
                        </span>
                      </span>
                    </button>
                  </li>
                }
              </ol>
            </div>

            <!-- Detail inspector panel -->
            @if (selectedEntry(); as selected) {
              <div class="timeline-detail-pane" role="region" aria-label="Event detail inspector">
                <div class="detail-card">
                  <div class="card-head">
                    <div>
                      <div class="eyebrow">
                        <span>{{ selected.kind }}</span>
                        <span> · {{ selected.atLabel }}</span>
                      </div>
                      <h3>{{ selected.title }}</h3>
                    </div>
                    <button
                      type="button"
                      class="btn btn-ghost close-btn"
                      (click)="clearSelection()"
                      aria-label="Close detail inspector"
                    >
                      <cc-icon name="close" [size]="16" />
                    </button>
                  </div>

                  @if (selected.detail) {
                    <p class="detail-desc">{{ selected.detail }}</p>
                  }

                  <!-- Identifiers and provenance -->
                  <div class="detail-section">
                    <h4 class="section-title">Supplied Metadata & Provenance</h4>
                    <dl class="kv" aria-label="Event metadata">
                      <dt>Event ID</dt>
                      <dd class="mono">{{ selected.id }}</dd>
                      <dt>State</dt>
                      <dd>
                        <cc-status-badge
                          [label]="selected.stateLabel"
                          [tone]="selected.stateTone"
                        />
                      </dd>
                      <dt>Timestamp</dt>
                      <dd>{{ selected.atLabel }}</dd>
                      @if (selected.stageId) {
                        <dt>Stage</dt>
                        <dd>{{ selected.stageId }}</dd>
                      }
                      @if (selected.actorId) {
                        <dt>Actor</dt>
                        <dd class="mono">{{ selected.actorId }}</dd>
                      }
                      @if (selected.toolId) {
                        <dt>Tool</dt>
                        <dd class="mono">{{ selected.toolId }}</dd>
                      }
                      @if (selected.executionEntryRef) {
                        <dt>Entry Claim</dt>
                        <dd class="mono">{{ selected.executionEntryRef }}</dd>
                      }
                      @if (selected.runIdRef) {
                        <dt>Run Ref</dt>
                        <dd class="mono">{{ selected.runIdRef }}</dd>
                      }
                    </dl>
                  </div>

                  <!-- Linked Result section -->
                  @if (selected.hasResult) {
                    <div class="detail-section">
                      <h4 class="section-title">Linked Result</h4>
                      <cc-result-shell [result]="selected.result" />
                    </div>
                  }

                  <!-- Associated Evidence section -->
                  <div class="detail-section">
                    <h4 class="section-title">
                      Associated Evidence ({{ selected.evidenceCount }})
                    </h4>
                    <cc-evidence-panel [items]="selected.evidence" />
                  </div>
                </div>
              </div>
            }
          </div>
        }
      }
    </div>
  `,
})
export class ExecutionTimeline {
  private readonly element = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  private readonly destroyRef = inject(DestroyRef);
  readonly entries = input.required<readonly TimelineEntry[]>();
  readonly selectedId = model<string | null>(null);
  readonly entrySelect = output<TimelineEntry | null>();

  protected readonly filter = signal<TimelineFilter>('all');
  protected readonly actorFilter = signal<string | null>(null);
  protected readonly toolFilter = signal<string | null>(null);

  protected readonly availableActors = computed(() => {
    const set = new Set<string>();
    for (const entry of this.entries()) {
      if (entry.actorId) set.add(entry.actorId);
    }
    return Array.from(set);
  });

  protected readonly availableTools = computed(() => {
    const set = new Set<string>();
    for (const entry of this.entries()) {
      if (entry.toolId) set.add(entry.toolId);
    }
    return Array.from(set);
  });

  protected readonly hasAnyResult = computed(() => this.entries().some((e) => e.hasResult));

  protected readonly resultCount = computed(() => this.entries().filter((e) => e.hasResult).length);

  protected readonly hasAnyEvidence = computed(() => this.entries().some((e) => e.hasEvidence));

  protected readonly evidenceCount = computed(
    () => this.entries().filter((e) => e.hasEvidence).length,
  );

  protected readonly hasAnyAttention = computed(() =>
    this.entries().some(
      (e) =>
        e.state === 'needs-attention' ||
        (e.result && e.result.outcome !== 'succeeded') ||
        e.hasUnavailableEvidence,
    ),
  );

  protected readonly attentionCount = computed(
    () =>
      this.entries().filter(
        (e) =>
          e.state === 'needs-attention' ||
          (e.result && e.result.outcome !== 'succeeded') ||
          e.hasUnavailableEvidence,
      ).length,
  );

  protected readonly filteredEntries = computed(() => {
    const all = this.entries();
    const f = this.filter();
    const actor = this.actorFilter();
    const tool = this.toolFilter();

    return all.filter((entry) => {
      if (f === 'result' && !entry.hasResult) return false;
      if (f === 'evidence' && !entry.hasEvidence) return false;
      if (f === 'attention') {
        const isAttention =
          entry.state === 'needs-attention' ||
          (entry.result && entry.result.outcome !== 'succeeded') ||
          entry.hasUnavailableEvidence;
        if (!isAttention) return false;
      }

      if (actor && entry.actorId !== actor) return false;
      if (tool && entry.toolId !== tool) return false;

      return true;
    });
  });

  protected readonly selectedEntry = computed(() => {
    const id = this.selectedId();
    if (!id) return null;
    return this.entries().find((e) => e.id === id) ?? null;
  });

  protected icon(entry: TimelineEntry): IconName {
    return KIND_ICON[entry.kind] ?? 'branch';
  }

  protected selectEntry(entry: TimelineEntry): void {
    if (this.selectedId() === entry.id) {
      this.selectedId.set(null);
      this.entrySelect.emit(null);
    } else {
      this.selectedId.set(entry.id);
      this.entrySelect.emit(entry);
    }
  }

  protected clearSelection(): void {
    const previousId = this.selectedId();
    this.selectedId.set(null);
    this.entrySelect.emit(null);
    afterNextRender(
      () => {
        if (this.destroyRef.destroyed || this.selectedId() !== null) return;
        const element = this.element.nativeElement;
        const triggers = Array.from(element.querySelectorAll<HTMLButtonElement>('.entry-trigger'));
        const target =
          triggers.find((trigger) => trigger.dataset['entryId'] === previousId) ??
          triggers[0] ??
          element.querySelector<HTMLElement>('.filter-btn') ??
          element.querySelector<HTMLElement>('.timeline-wrapper');
        target?.focus({ preventScroll: true });
      },
      { injector: this.injector },
    );
  }

  protected setFilter(f: TimelineFilter): void {
    if (this.filter() === f) {
      this.filter.set('all');
    } else {
      this.filter.set(f);
    }
  }

  protected toggleActor(actor: string): void {
    if (this.actorFilter() === actor) {
      this.actorFilter.set(null);
    } else {
      this.actorFilter.set(actor);
    }
  }

  protected toggleTool(tool: string): void {
    if (this.toolFilter() === tool) {
      this.toolFilter.set(null);
    } else {
      this.toolFilter.set(tool);
    }
  }

  protected resetFilters(): void {
    this.filter.set('all');
    this.actorFilter.set(null);
    this.toolFilter.set(null);
  }

  protected formatTool(toolId: string): string {
    const parts = toolId.split('::');
    return parts.length > 1 ? parts[1] : toolId;
  }
}
