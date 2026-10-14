import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { toLoadState, toLoadStateFor } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import {
  APPROVAL_LEVEL,
  LEVEL,
  PRESENTATION_STATE,
  TASK_STATUS,
  humanize,
} from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

@Component({
  selector: 'cc-task-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
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

                <div class="card card-flush">
                  <div class="card-head">
                    <div>
                      <h2>Runs</h2>
                      <p>Runs the data source associates with this Task.</p>
                    </div>
                  </div>
                  @if (runs().length === 0) {
                    <cc-state-panel kind="empty" title="No runs yet" message="Nothing has been run for this Task." />
                  } @else {
                    <div class="table-wrap">
                      <table class="table" aria-label="Runs for this task">
                        <thead>
                          <tr>
                            <th scope="col">Run</th><th scope="col">Stage</th><th scope="col">Role</th>
                            <th scope="col">Actor</th><th scope="col">Visual state</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (run of runs(); track run.runId) {
                            <tr>
                              <td><a class="row-link mono" [routerLink]="['/runs', run.runId]">{{ run.runId }}</a></td>
                              <td>{{ run.contract.stageId }}</td>
                              <td>{{ run.contract.roleId }}</td>
                              <td class="mono">{{ run.contract.actorId }}</td>
                              <td><cc-status-badge [label]="presentation[run.presentationState].label" [tone]="presentation[run.presentationState].tone" /></td>
                            </tr>
                          }
                        </tbody>
                      </table>
                    </div>
                  }
                </div>
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
  protected readonly humanize = humanize;

  protected readonly state = toLoadStateFor(this.taskId, (id) => this.dataSource.getTask(id));
  private readonly runState = toLoadState(this.dataSource.listRuns());

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
}
