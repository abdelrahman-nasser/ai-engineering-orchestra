import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { TaskStatus } from '../../data/models';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { APPROVAL_LEVEL, LEVEL, TASK_STATUS, humanize } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

type TaskFilter =
  | 'all'
  | TaskStatus
  | 'attention-required'
  | 'continuation-available';

@Component({
  selector: 'cc-tasks',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: '../shared-list.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Tasks"
        lede="Tasks as defined by the Core Task contract. Associated runs, last activity, and continuation affordances are supplied by current data-source read models."
      />

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load Tasks" />
        }
        @default {
          <div class="filters" role="group" aria-label="Filter tasks by status or history affordance">
            @for (option of filters; track option.value) {
              <button
                type="button"
                class="filter"
                [attr.aria-pressed]="filter() === option.value"
                [attr.data-testid]="'task-filter-' + option.value"
                (click)="filter.set(option.value)"
              >
                {{ option.label }} <span class="count">{{ counts()[option.value] }}</span>
              </button>
            }
          </div>

          <div class="card card-flush">
            @if (rows().length === 0) {
              <cc-state-panel kind="empty" title="No tasks match this filter" />
            } @else {
              <div class="table-wrap">
                <table class="table" aria-label="Tasks">
                  <thead>
                    <tr>
                      <th scope="col">Task</th>
                      <th scope="col">Status</th>
                      <th scope="col">Associated runs</th>
                      <th scope="col">Result</th>
                      <th scope="col">Continuation</th>
                      <th scope="col">Type</th>
                      <th scope="col">Risk</th>
                      <th scope="col">Mode</th>
                      <th scope="col">Workflow</th>
                      <th scope="col">Last activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (task of rows(); track task.id) {
                      <tr>
                        <td class="title-cell">
                          <a class="row-link mono" [routerLink]="['/tasks', task.id]">{{ task.id }}</a>
                          <div class="muted">{{ task.title }}</div>
                        </td>
                        <td><cc-status-badge [label]="status[task.status].label" [tone]="status[task.status].tone" /></td>
                        <td>
                          @if (task.runCount && task.runCount > 0) {
                            <div>{{ task.runCount }} run{{ task.runCount === 1 ? '' : 's' }}</div>
                            @if (task.latestRunId) {
                              <a class="mono text-xs muted row-link" [routerLink]="['/runs', task.latestRunId]">latest: {{ task.latestRunId }}</a>
                            }
                          } @else {
                            <span class="muted text-xs">No runs yet</span>
                          }
                        </td>
                        <td>
                          @if (task.hasResult) {
                            <cc-status-badge label="Published" tone="info" />
                          } @else {
                            <span class="muted text-xs">—</span>
                          }
                        </td>
                        <td>
                          @if (task.continuationAvailable) {
                            <cc-status-badge label="Available" tone="success" />
                          } @else {
                            <span class="muted text-xs">—</span>
                          }
                        </td>
                        <td>{{ task.type }}</td>
                        <td><cc-status-badge [label]="level[task.risk].label" [tone]="level[task.risk].tone" /></td>
                        <td><span class="chip">{{ task.executionMode }}</span></td>
                        <td>{{ humanize(task.workflowId) }}</td>
                        <td class="muted nowrap text-xs">{{ task.lastActivityLabel || task.updatedLabel }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            }
          </div>
        }
      }
    </section>
  `,
})
export class Tasks {
  private readonly dataSource = inject(ControlCenterDataSource);

  protected readonly status = TASK_STATUS;
  protected readonly level = LEVEL;
  protected readonly approval = APPROVAL_LEVEL;
  protected readonly humanize = humanize;

  protected readonly state = toLoadState(this.dataSource.listTasks());
  protected readonly filter = signal<TaskFilter>('all');

  protected readonly filters: readonly { value: TaskFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'planned', label: 'Planned' },
    { value: 'in_progress', label: 'In progress' },
    { value: 'blocked', label: 'Blocked' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
    { value: 'attention-required', label: 'Attention required' },
    { value: 'continuation-available', label: 'Continuation available' },
  ];

  private readonly tasks = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : [];
  });

  protected readonly rows = computed(() => {
    const filter = this.filter();
    const all = this.tasks();
    switch (filter) {
      case 'all':
        return all;
      case 'planned':
      case 'in_progress':
      case 'blocked':
      case 'completed':
      case 'cancelled':
        return all.filter((task) => task.status === filter);
      case 'attention-required':
        return all.filter((task) => task.status === 'blocked' || task.latestRunState === 'needs-attention');
      case 'continuation-available':
        return all.filter((task) => Boolean(task.continuationAvailable));
    }
  });

  protected readonly counts = computed(() => {
    const tasks = this.tasks();
    return {
      all: tasks.length,
      planned: tasks.filter((t) => t.status === 'planned').length,
      in_progress: tasks.filter((t) => t.status === 'in_progress').length,
      blocked: tasks.filter((t) => t.status === 'blocked').length,
      completed: tasks.filter((t) => t.status === 'completed').length,
      cancelled: tasks.filter((t) => t.status === 'cancelled').length,
      'attention-required': tasks.filter((t) => t.status === 'blocked' || t.latestRunState === 'needs-attention').length,
      'continuation-available': tasks.filter((t) => Boolean(t.continuationAvailable)).length,
    };
  });
}
