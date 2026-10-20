import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { NileNode } from '../../data/models';
import { PageHeader } from '../../shared/page-header';
import { StatTile } from '../../shared/stat-tile';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';
import { NileFlow } from '../../shared/nile/nile-flow';
import { buildPortfolioTopology } from '../../shared/nile/nile-topology';
import { toLoadState } from '../../shared/load-state';
import { AVAILABILITY, PRESENTATION_STATE, TASK_STATUS } from '../../shared/presentation';
import { GuidedExplorerState } from '../../application-v1/guided-explorer-state';

@Component({
  selector: 'cc-overview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatTile, StatePanel, StatusBadge, NileFlow],
  styleUrl: './overview.css',
  template: `
    <section class="page" aria-labelledby="overview-title">
      <cc-page-header
        title="Overview"
        lede="A calm look at what is moving through the workspace, and what needs a person."
      />

      <div class="card demo-entry">
        <div>
          <p class="eyebrow">New here? · Synthetic Developer Alpha</p>
          <h2>Follow a Task from scope to evidence</h2>
          <p>Browse freely with an optional guide and 18 synthetic scenarios. No Core connection or operational actions.</p>
        </div>
        <button type="button" class="btn btn-primary" (click)="explorer.open()">Open Guided Explorer</button>
      </div>

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load the overview" />
        }
        @default {
          @if (view(); as v) {
            <div class="grid grid-4" aria-label="Key figures">
              <cc-stat-tile label="Active tasks" [value]="v.activeTasks" hint="In progress or blocked" tone="info" />
              <cc-stat-tile label="Runs needing attention" [value]="v.attentionRuns.length" hint="Waiting on a person" tone="warning" />
              <cc-stat-tile label="Approvals without evidence" [value]="v.awaitingApprovals.length" hint="Authorization unproven" tone="warning" />
              <cc-stat-tile label="Agents available" [value]="v.availableAgents + ' / ' + v.totalAgents" hint="By latest observation" tone="success" />
            </div>

            <div class="stack river-layout">
              <div class="card">
                <div class="card-head">
                  <div>
                    <h2>Workspace river</h2>
                    <p>Active Tasks and their Runs, drawn as tributaries. Select an island to open it.</p>
                  </div>
                  <a routerLink="/flow" class="btn btn-ghost">Open Flow &amp; Scheduler &rarr;</a>
                </div>
                <cc-nile-flow
                  [topology]="v.topology"
                  [columnWidth]="250"
                  [laneHeight]="84"
                  ariaLabel="Active tasks and runs"
                  (nodeSelect)="open($event)"
                />
              </div>

              <div class="card">
                <div class="card-head">
                  <div>
                    <h2>Needs a person</h2>
                    <p>Items that cannot move without a decision.</p>
                  </div>
                </div>
                <ul class="attention">
                  @for (run of v.attentionRuns; track run.runId) {
                    <li>
                      <a [routerLink]="['/runs', run.runId]" class="row-link">
                        <strong class="mono">{{ run.runId }}</strong>
                        <span class="muted">{{ run.contract.taskId }} · {{ run.contract.stageId }}</span>
                      </a>
                      <cc-status-badge label="Needs attention" tone="warning" />
                    </li>
                  }
                  @for (approval of v.awaitingApprovals; track approval.id) {
                    <li>
                      <a routerLink="/approvals" class="row-link">
                        <strong>{{ approval.taskId }}</strong>
                        <span class="muted">{{ approval.stageId }} · {{ approval.level }} approval</span>
                      </a>
                      <cc-status-badge label="No evidence yet" tone="warning" />
                    </li>
                  }
                  @if (v.attentionRuns.length + v.awaitingApprovals.length === 0) {
                    <li class="muted">Nothing is waiting on a person.</li>
                  }
                </ul>
              </div>
            </div>

            <div class="grid grid-2">
              <div class="card card-flush">
                <div class="card-head">
                  <div>
                    <h2>Tasks</h2>
                    <p>Most recently updated first.</p>
                  </div>
                  <a routerLink="/tasks" class="btn btn-ghost">View all</a>
                </div>
                <div class="table-wrap">
                  <table class="table">
                    <thead>
                      <tr><th scope="col">Task</th><th scope="col">Status</th></tr>
                    </thead>
                    <tbody>
                      @for (task of v.recentTasks; track task.id) {
                        <tr>
                          <td>
                            <a class="row-link" [routerLink]="['/tasks', task.id]">{{ task.id }}</a>
                            <div class="muted">{{ task.title }}</div>
                          </td>
                          <td><cc-status-badge [label]="taskStatus[task.status].label" [tone]="taskStatus[task.status].tone" /></td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </div>

              <div class="card card-flush">
                <div class="card-head">
                  <div>
                    <h2>Agents</h2>
                    <p>Availability is an observation, not a guarantee.</p>
                  </div>
                  <a routerLink="/agents" class="btn btn-ghost">View all</a>
                </div>
                <div class="table-wrap">
                  <table class="table">
                    <thead>
                      <tr><th scope="col">Actor</th><th scope="col">Availability</th></tr>
                    </thead>
                    <tbody>
                      @for (agent of v.agents; track agent.actorId) {
                        <tr>
                          <td>
                            <strong>{{ agent.name }}</strong>
                            <div class="muted mono">{{ agent.actorId }}</div>
                          </td>
                          <td><cc-status-badge [label]="availability[agent.availability].label" [tone]="availability[agent.availability].tone" /></td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          }
        }
      }
    </section>
  `,
})
export class Overview {
  protected readonly explorer = inject(GuidedExplorerState);
  private readonly dataSource = inject(ControlCenterDataSource);
  private readonly router = inject(Router);

  protected readonly taskStatus = TASK_STATUS;
  protected readonly availability = AVAILABILITY;
  protected readonly presentation = PRESENTATION_STATE;

  protected readonly state = toLoadState(this.dataSource.getOverview());

  protected readonly view = computed(() => {
    const state = this.state();
    if (state.status !== 'ready') {
      return null;
    }
    const { tasks, runs, agents, approvals } = state.data;
    return {
      activeTasks: tasks.filter((task) => task.status === 'in_progress' || task.status === 'blocked').length,
      attentionRuns: runs.filter((run) => run.presentationState === 'needs-attention'),
      awaitingApprovals: approvals.filter((approval) => approval.state === 'awaiting'),
      availableAgents: agents.filter((agent) => agent.availability === 'available').length,
      totalAgents: agents.length,
      topology: buildPortfolioTopology(tasks, runs),
      recentTasks: tasks.slice(0, 5),
      agents: agents.slice(0, 5),
    };
  });

  protected open(node: NileNode): void {
    if (node.kind === 'run') {
      void this.router.navigate(['/runs', node.id]);
    } else if (node.kind === 'task') {
      void this.router.navigate(['/tasks', node.id]);
    }
  }
}
