import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { TaskStatus } from '../../data/models';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { APPROVAL_LEVEL, LEVEL, TASK_STATUS, humanize } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

type TaskFilter = 'all' | TaskStatus;

@Component({
  selector: 'cc-tasks',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: '../shared-list.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Tasks"
        lede="Tasks as defined by the Core Task contract. Status uses the Core lifecycle values."
      />

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load Tasks" />
        }
        @default {
          <div class="filters" role="group" aria-label="Filter tasks by status">
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
                      <th scope="col">Type</th>
                      <th scope="col">Risk</th>
                      <th scope="col">Mode</th>
                      <th scope="col">Workflow</th>
                      <th scope="col">Approval</th>
                      <th scope="col">Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (task of rows(); track task.id) {
                      <tr>
                        <td class="title-cell">
                          <a class="row-link" [routerLink]="['/tasks', task.id]">{{ task.id }}</a>
                          <div class="muted">{{ task.title }}</div>
                        </td>
                        <td><cc-status-badge [label]="status[task.status].label" [tone]="status[task.status].tone" /></td>
                        <td>{{ task.type }}</td>
                        <td><cc-status-badge [label]="level[task.risk].label" [tone]="level[task.risk].tone" /></td>
                        <td><span class="chip">{{ task.executionMode }}</span></td>
                        <td>{{ humanize(task.workflowId) }}</td>
                        <td><cc-status-badge [label]="approval[task.approvalLevel].label" [tone]="approval[task.approvalLevel].tone" /></td>
                        <td class="muted nowrap">{{ task.updatedLabel }}</td>
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
  ];

  private readonly tasks = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : [];
  });

  protected readonly rows = computed(() => {
    const filter = this.filter();
    return filter === 'all' ? this.tasks() : this.tasks().filter((task) => task.status === filter);
  });

  protected readonly counts = computed(() => {
    const tasks = this.tasks();
    const tally: Record<string, number> = { all: tasks.length };
    for (const option of this.filters.slice(1)) {
      tally[option.value] = tasks.filter((task) => task.status === option.value).length;
    }
    return tally;
  });
}
