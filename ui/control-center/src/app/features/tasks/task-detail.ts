import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { of } from 'rxjs';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { ContinuationShell } from '../../shared/continuation-shell';
import { EvidencePanel } from '../../shared/evidence-panel';
import { ExecutionTimeline } from '../../shared/execution-timeline';
import { toLoadState, toLoadStateFor } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import {
  APPROVAL_LEVEL,
  CONTINUATION_STATUS,
  LEVEL,
  PRESENTATION_STATE,
  TASK_STATUS,
  humanize,
} from '../../shared/presentation';
import { ResultShell } from '../../shared/result-shell';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

@Component({
  selector: 'cc-task-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    PageHeader,
    StatePanel,
    StatusBadge,
    ContinuationShell,
    ResultShell,
    ExecutionTimeline,
    EvidencePanel,
  ],
  styleUrl: './task-detail.css',
  template: `
    <section class="page">
      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load this Task" />
        }
        @default {
          @if (task(); as t) {
            <cc-page-header
              [title]="t.title"
              [crumbs]="[{ label: 'Tasks', link: ['/tasks'] }, { label: t.id }]"
              [lede]="t.objective"
            >
              <cc-status-badge [label]="status[t.status].label" [tone]="status[t.status].tone" />
            </cc-page-header>

            @if (t.blockedReason) {
              <div class="notice" role="note">
                <div><strong>Blocked.</strong> {{ t.blockedReason }}</div>
              </div>
            }

            <div class="grid grid-main-aside">
              <div class="stack column">
                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Workflow stages</h2>
                      <p>{{ humanize(t.workflowId) }} — stages progress sequentially.</p>
                    </div>
                  </div>
                  <ol class="stages">
                    @for (stage of t.stages; track stage.id; let i = $index) {
                      <li>
                        <span class="index" aria-hidden="true">{{ i + 1 }}</span>
                        <div class="stage-body">
                          <div class="row">
                            <strong>{{ humanize(stage.id) }}</strong>
                            @if (stage.humanControlCheckpoint) {
                              <cc-status-badge label="Human checkpoint" tone="accent" />
                            }
                          </div>
                          <p class="muted">{{ stage.purpose }}</p>
                          @if (stage.requiredRoles.length) {
                            <div class="row roles">
                              @for (role of stage.requiredRoles; track role) {
                                <span class="chip">{{ role }}</span>
                              }
                            </div>
                          }
                        </div>
                      </li>
                    }
                  </ol>
                </div>

                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Task Run History</h2>
                      <p>Associated runs for this Task. Select a run to inspect its continuation, result, timeline, and evidence.</p>
                    </div>
                  </div>
                  @if (runs().length === 0) {
                    <cc-state-panel kind="empty" title="No runs yet" message="Nothing has been run for this Task." />
                  } @else {
                    <div class="run-tree-wrapper">
                      <div class="run-tree" role="tree" [attr.aria-label]="'Runs for task ' + t.id">
                        <div class="tree-root">
                          <span class="mono tree-root-id">{{ t.id }}</span>
                          <span class="badge-count">{{ runs().length }} run{{ runs().length === 1 ? '' : 's' }}</span>
                        </div>
                        <div class="tree-children" role="group">
                          @for (run of runs(); track run.runId; let last = $last) {
                            <div
                              class="tree-item"
                              role="treeitem"
                              [class.active]="activeRunId() === run.runId"
                              [attr.aria-selected]="activeRunId() === run.runId"
                              [attr.data-testid]="'run-tree-item-' + run.runId"
                              tabindex="0"
                              (click)="selectRun(run.runId)"
                              (keydown.enter)="selectRun(run.runId)"
                              (keydown.space)="selectRun(run.runId); $event.preventDefault()"
                            >
                              <div class="tree-branch-glyph" aria-hidden="true">{{ last ? '└─' : '├─' }}</div>
                              <div class="tree-node-main">
                                <div class="tree-node-header">
                                  <span class="mono run-id-label">{{ run.runId }}</span>
                                  <cc-status-badge
                                    [label]="presentation[run.presentationState].label"
                                    [tone]="presentation[run.presentationState].tone"
                                  />
                                  @if (run.continuation) {
                                    <cc-status-badge
                                      [label]="continuationStatus[run.continuation.status].label"
                                      [tone]="continuationStatus[run.continuation.status].tone"
                                    />
                                  }
                                  @if (run.hasResult) {
                                    <span
                                      class="chip-sm"
                                      [class.info]="run.resultOutcome === 'succeeded'"
                                      [class.danger]="run.resultOutcome === 'failed_before_effect'"
                                    >
                                      Result: {{ run.resultOutcome || 'published' }}
                                    </span>
                                  }
                                  @if (run.evidenceCount && run.evidenceCount > 0) {
                                    <span class="chip-sm faint">{{ run.evidenceCount }} evidence</span>
                                  }
                                </div>
                                <div class="tree-node-meta muted text-xs">
                                  <span>Stage: <strong>{{ run.contract.stageId }}</strong></span>
                                  <span>Role: <strong>{{ run.contract.roleId }}</strong></span>
                                  <span>Actor: <code class="mono">{{ run.contract.actorId }}</code></span>
                                  @if (run.lastActivityLabel) {
                                    <span>Activity: {{ run.lastActivityLabel }}</span>
                                  }
                                </div>
                              </div>
                              <div class="tree-node-actions">
                                <a
                                  class="btn-subtle"
                                  [routerLink]="['/runs', run.runId]"
                                  (click)="$event.stopPropagation()"
                                  [attr.aria-label]="'Open dedicated Run Detail page for ' + run.runId"
                                >
                                  Detail &rarr;
                                </a>
                              </div>
                            </div>
                          }
                        </div>
                      </div>
                    </div>
                  }
                </div>

                @if (selectedRun(); as sel) {
                  <div class="card run-inspector" [attr.aria-label]="'Inspection for run ' + sel.runId" data-testid="run-inspection-card">
                    <div class="card-head">
                      <div>
                        <div class="inspector-badge-row">
                          <span class="inspector-tag">Selected Run</span>
                          <h2 class="mono">{{ sel.runId }}</h2>
                        </div>
                        <p>
                          Viewing Run in context of Task {{ t.id }}.
                          <a class="row-link" [routerLink]="['/runs', sel.runId]">Open full Run Detail page &rarr;</a>
                        </p>
                      </div>
                      <cc-status-badge
                        [label]="presentation[sel.presentationState].label"
                        [tone]="presentation[sel.presentationState].tone"
                      />
                    </div>

                    <div class="inspector-sections">
                      <section class="inspector-block" aria-labelledby="heading-continuation">
                        <div class="block-header">
                          <h3 id="heading-continuation">Continuation &amp; Recovery</h3>
                          <p class="muted text-xs">Mock continuation metadata; operational continuation is unavailable.</p>
                        </div>
                        <cc-continuation-shell
                          [continuation]="sel.continuation"
                          [runId]="sel.runId"
                          [resultOutcome]="sel.result?.outcome"
                        />
                      </section>

                      @if (sel.result) {
                        <section class="inspector-block" aria-labelledby="heading-result">
                          <div class="block-header">
                            <h3 id="heading-result">Execution Result</h3>
                          </div>
                          <cc-result-shell [result]="sel.result" />
                        </section>
                      }

                      @if (sel.timeline && sel.timeline.length > 0) {
                        <section class="inspector-block" aria-labelledby="heading-timeline">
                          <div class="block-header">
                            <h3 id="heading-timeline">Execution Timeline</h3>
                            <p class="muted text-xs">Mock presentation entries; this is not the canonical Journal.</p>
                          </div>
                          <cc-execution-timeline [entries]="sel.timeline" />
                        </section>
                      }

                      @if (sel.evidence && sel.evidence.length > 0) {
                        <section class="inspector-block" aria-labelledby="heading-evidence">
                          <div class="block-header">
                            <h3 id="heading-evidence">Evidence Explorer</h3>
                          </div>
                          <cc-evidence-panel [items]="sel.evidence" />
                        </section>
                      }
                    </div>
                  </div>
                }
              </div>

              <div class="stack column">
                <div class="card">
                  <div class="card-head"><h2>Classification</h2></div>
                  <dl class="kv" aria-label="Task classification">
                    <dt>Task ID</dt><dd class="mono">{{ t.id }}</dd>
                    <dt>Type</dt><dd>{{ t.type }}</dd>
                    <dt>Risk</dt><dd><cc-status-badge [label]="level[t.risk].label" [tone]="level[t.risk].tone" /></dd>
                    <dt>Complexity</dt><dd><cc-status-badge [label]="level[t.complexity].label" [tone]="level[t.complexity].tone" /></dd>
                    <dt>Execution mode</dt><dd><span class="chip">{{ t.executionMode }}</span></dd>
                    <dt>Human approval</dt><dd><cc-status-badge [label]="approval[t.approvalLevel].label" [tone]="approval[t.approvalLevel].tone" /></dd>
                    <dt>Updated</dt><dd>{{ t.updatedLabel }}</dd>
                  </dl>
                </div>

                <div class="card">
                  <div class="card-head"><h2>Scope</h2></div>
                  <h3 class="sub">Included</h3>
                  <ul class="list">
                    @for (item of t.scopeIncluded; track item) { <li>{{ item }}</li> }
                  </ul>
                  <h3 class="sub">Excluded</h3>
                  <ul class="list">
                    @for (item of t.scopeExcluded; track item) { <li>{{ item }}</li> }
                  </ul>
                </div>

                <div class="card">
                  <div class="card-head"><h2>Dependencies &amp; gates</h2></div>
                  <h3 class="sub">Depends on</h3>
                  <div class="row">
                    @for (dep of t.dependencies; track dep) {
                      <a class="chip" [routerLink]="['/tasks', dep]">{{ dep }}</a>
                    } @empty {
                      <span class="muted">None</span>
                    }
                  </div>
                  <h3 class="sub">Quality Gates</h3>
                  <div class="row">
                    @for (gate of t.qualityGates; track gate) {
                      <span class="chip mono">{{ gate }}</span>
                    } @empty {
                      <span class="muted">None required</span>
                    }
                  </div>
                </div>
              </div>
            </div>
          } @else {
            <cc-state-panel kind="not-found" title="Task not found" message="No Task with this identifier exists in the current data source.">
              <a class="btn" routerLink="/tasks">Back to Tasks</a>
            </cc-state-panel>
          }
        }
      }
    </section>
  `,
})
export class TaskDetailPage {
  /** Bound from the `:taskId` route parameter. */
  readonly taskId = input.required<string>();

  private readonly dataSource = inject(ControlCenterDataSource);

  protected readonly status = TASK_STATUS;
  protected readonly level = LEVEL;
  protected readonly approval = APPROVAL_LEVEL;
  protected readonly presentation = PRESENTATION_STATE;
  protected readonly continuationStatus = CONTINUATION_STATUS;
  protected readonly humanize = humanize;

  protected readonly state = toLoadStateFor(this.taskId, (id) => this.dataSource.getTask(id));
  private readonly runState = toLoadState(this.dataSource.listRuns());

  readonly selectedRunId = signal<string | null>(null);

  protected readonly task = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : undefined;
  });

  protected readonly runs = computed(() => {
    const task = this.task();
    const state = this.runState();
    if (!task || state.status !== 'ready') {
      return [];
    }
    return state.data.filter((run) => run.contract.taskId === task.id);
  });

  protected readonly activeRunId = computed(() => {
    const current = this.selectedRunId();
    if (current) {
      return current;
    }
    const list = this.runs();
    return list.length > 0 ? list[list.length - 1].runId : '';
  });

  protected readonly selectedRunState = toLoadStateFor(this.activeRunId, (id) =>
    id ? this.dataSource.getRun(id) : of(undefined),
  );

  protected readonly selectedRun = computed(() => {
    const s = this.selectedRunState();
    return s.status === 'ready' ? s.data : undefined;
  });

  selectRun(runId: string): void {
    this.selectedRunId.set(runId);
  }
}
