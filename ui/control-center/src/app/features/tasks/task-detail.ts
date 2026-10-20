import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  linkedSignal,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { map, of } from 'rxjs';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { TaskDetail } from '../../data/models';
import { ContinuationShell } from '../../shared/continuation-shell';
import { EvidencePanel } from '../../shared/evidence-panel';
import { ExecutionTimeline } from '../../shared/execution-timeline';
import { LoadState, toLoadState, toLoadStateFor } from '../../shared/load-state';
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
import { TaskContextSummary } from './task-context-summary';

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
    TaskContextSummary,
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

            <cc-task-context-summary
              [task]="t"
              [runs]="runs()"
              [runReadStatus]="runState().status"
              [selectedRun]="selectedRun()"
              [selectionStatus]="selectedRunState().status"
            />

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
                      <p>
                        Associated runs for this Task. Select a run to inspect its continuation,
                        result, timeline, and evidence.
                      </p>
                    </div>
                  </div>
                  @if (runState().status === 'loading') {
                    <cc-state-panel kind="loading" title="Loading associated Runs" />
                  } @else if (runState().status === 'error') {
                    <cc-state-panel
                      kind="error"
                      title="Associated Runs unavailable"
                      message="The Run list could not be read. No Run association is established by this view."
                    />
                  } @else if (runs().length === 0) {
                    <cc-state-panel
                      kind="empty"
                      title="No matching Run records supplied"
                      [message]="
                        t.runIds.length
                          ? 'This Task supplies Run references, but matching observations are unavailable. Execution history is not established.'
                          : 'No Run references or matching observations were supplied for this Task. This does not establish that execution never occurred.'
                      "
                    />
                  } @else {
                    <div class="run-tree-wrapper">
                      <div class="run-tree">
                        <div class="tree-root">
                          <span class="mono tree-root-id">{{ t.id }}</span>
                          <span class="badge-count"
                            >{{ runs().length }} run{{ runs().length === 1 ? '' : 's' }}</span
                          >
                        </div>
                        <ul class="tree-children" [attr.aria-label]="'Runs for task ' + t.id">
                          @for (run of runs(); track run.runId; let last = $last) {
                            <li class="tree-item" [class.active]="activeRunId() === run.runId">
                              <div class="tree-branch-glyph" aria-hidden="true">
                                {{ last ? '└─' : '├─' }}
                              </div>
                              <button
                                type="button"
                                class="tree-node-main run-select"
                                [attr.aria-pressed]="activeRunId() === run.runId"
                                [attr.aria-label]="'Inspect Run ' + run.runId"
                                [attr.data-testid]="'run-tree-item-' + run.runId"
                                (click)="selectRun(run.runId)"
                              >
                                <span class="tree-node-header">
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
                                    <span class="chip-sm faint"
                                      >{{ run.evidenceCount }} evidence</span
                                    >
                                  }
                                </span>
                                <span class="tree-node-meta muted text-xs">
                                  <span
                                    >Stage: <strong>{{ run.contract.stageId }}</strong></span
                                  >
                                  <span
                                    >Role: <strong>{{ run.contract.roleId }}</strong></span
                                  >
                                  <span
                                    >Actor:
                                    <code class="mono">{{ run.contract.actorId }}</code></span
                                  >
                                  @if (run.lastActivityLabel) {
                                    <span>Activity: {{ run.lastActivityLabel }}</span>
                                  }
                                </span>
                              </button>
                              <div class="tree-node-actions">
                                <a
                                  class="btn-subtle"
                                  [routerLink]="['/runs', run.runId]"
                                  (click)="$event.stopPropagation()"
                                  [attr.aria-label]="
                                    'Open dedicated Run Detail page for ' + run.runId
                                  "
                                >
                                  Detail &rarr;
                                </a>
                              </div>
                            </li>
                          }
                        </ul>
                      </div>
                    </div>
                  }
                </div>

                @if (activeRunId() && selectedRunState().status === 'loading') {
                  <cc-state-panel kind="loading" title="Loading selected Run" />
                } @else if (activeRunId() && selectedRunState().status === 'error') {
                  <cc-state-panel
                    kind="error"
                    title="Selected Run unavailable"
                    message="No matching Run details or evidence can be shown for this Task."
                  />
                } @else if (activeRunId() && !selectedRun()) {
                  <cc-state-panel
                    kind="empty"
                    title="Selected Run details unavailable"
                    message="The current source supplied no matching Run details for this Task."
                  />
                }
                @if (selectedRun(); as sel) {
                  <div
                    class="card run-inspector"
                    [attr.aria-label]="'Inspection for run ' + sel.runId"
                    data-testid="run-inspection-card"
                  >
                    <div class="card-head">
                      <div>
                        <div class="inspector-badge-row">
                          <span class="inspector-tag">Selected Run</span>
                          <h2 class="mono">{{ sel.runId }}</h2>
                        </div>
                        <p>
                          Viewing Run in context of Task {{ t.id }}.
                          <a class="row-link" [routerLink]="['/runs', sel.runId]"
                            >Open full Run Detail page &rarr;</a
                          >
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
                          <p class="muted text-xs">
                            Mock continuation metadata; operational continuation is unavailable.
                          </p>
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
                            <p class="muted text-xs">
                              Mock presentation entries; this is not the canonical Journal.
                            </p>
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
                    <dt>Task ID</dt>
                    <dd class="mono">{{ t.id }}</dd>
                    <dt>Type</dt>
                    <dd>{{ t.type }}</dd>
                    <dt>Risk</dt>
                    <dd>
                      <cc-status-badge [label]="level[t.risk].label" [tone]="level[t.risk].tone" />
                    </dd>
                    <dt>Complexity</dt>
                    <dd>
                      <cc-status-badge
                        [label]="level[t.complexity].label"
                        [tone]="level[t.complexity].tone"
                      />
                    </dd>
                    <dt>Execution mode</dt>
                    <dd>
                      <span class="chip">{{ t.executionMode }}</span>
                    </dd>
                    <dt>Human approval</dt>
                    <dd>
                      <cc-status-badge
                        [label]="approval[t.approvalLevel].label"
                        [tone]="approval[t.approvalLevel].tone"
                      />
                    </dd>
                    <dt>Updated</dt>
                    <dd>{{ t.updatedLabel }}</dd>
                  </dl>
                </div>

                <div class="card">
                  <div class="card-head"><h2>Scope</h2></div>
                  <h3 class="sub">Included</h3>
                  <ul class="list">
                    @for (item of t.scopeIncluded; track item) {
                      <li>{{ item }}</li>
                    }
                  </ul>
                  <h3 class="sub">Excluded</h3>
                  <ul class="list">
                    @for (item of t.scopeExcluded; track item) {
                      <li>{{ item }}</li>
                    }
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
            <cc-state-panel
              kind="not-found"
              title="Task not found"
              message="No Task with this identifier exists in the current data source."
            >
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

  private readonly taskRead = toLoadStateFor(this.taskId, (id) =>
    this.dataSource.getTask(id).pipe(map((data) => ({ id, data }))),
  );
  protected readonly state = computed<LoadState<TaskDetail | undefined>>(() => {
    const read = this.taskRead();
    if (read.status !== 'ready') return read;
    if (read.data.id !== this.taskId()) return { status: 'loading' };
    if (read.data.data && read.data.data.id !== this.taskId()) {
      return { status: 'error', message: 'Task identity does not match the requested Task.' };
    }
    return { status: 'ready', data: read.data.data };
  });
  protected readonly runState = toLoadState(this.dataSource.listRuns());

  readonly selectedRunId = linkedSignal<string, string | null>({
    source: this.taskId,
    computation: () => null,
  });

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
    return state.data.filter(
      (run) => run.contract.taskId === task.id && task.runIds.includes(run.runId),
    );
  });

  protected readonly activeRunId = computed(() => {
    const current = this.selectedRunId();
    const list = this.runs();
    if (current && list.some((run) => run.runId === current)) {
      return current;
    }
    return list.length > 0 ? list[list.length - 1].runId : '';
  });

  protected readonly selectedRunState = toLoadStateFor(this.activeRunId, (id) =>
    id ? this.dataSource.getRun(id) : of(undefined),
  );

  protected readonly selectedRun = computed(() => {
    const s = this.selectedRunState();
    const task = this.task();
    return s.status === 'ready' &&
      task &&
      s.data?.runId === this.activeRunId() &&
      s.data.contract.taskId === task.id &&
      task.runIds.includes(s.data.runId)
      ? s.data
      : undefined;
  });

  selectRun(runId: string): void {
    if (this.runs().some((run) => run.runId === runId)) this.selectedRunId.set(runId);
  }
}
