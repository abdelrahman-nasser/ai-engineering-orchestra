import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { PresentationState } from '../../data/models';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { PRESENTATION_STATE } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

type RunFilter = 'all' | PresentationState;

@Component({
  selector: 'cc-runs',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: '../shared-list.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Runs"
        lede="Each Run is one assigned action: one Stage, one Role, one Actor. The visual state shown here is a UI-local presentation, not a Core status."
      />

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load Runs" />
        }
        @default {
          <div class="filters" role="group" aria-label="Filter runs by visual state">
            @for (option of filters; track option.value) {
              <button
                type="button"
                class="filter"
                [attr.aria-pressed]="filter() === option.value"
                [attr.data-testid]="'run-filter-' + option.value"
                (click)="filter.set(option.value)"
              >
                {{ option.label }} <span class="count">{{ counts()[option.value] }}</span>
              </button>
            }
          </div>

          <div class="card card-flush">
            @if (rows().length === 0) {
              <cc-state-panel kind="empty" title="No runs match this filter" />
            } @else {
              <div class="table-wrap">
                <table class="table" aria-label="Runs">
                  <thead>
                    <tr>
                      <th scope="col">Run</th>
                      <th scope="col">Task</th>
                      <th scope="col">Stage</th>
                      <th scope="col">Role</th>
                      <th scope="col">Actor</th>
                      <th scope="col">Mode</th>
                      <th scope="col">Visual state</th>
                      <th scope="col">Started</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (run of rows(); track run.runId) {
                      <tr>
                        <td><a class="row-link mono" [routerLink]="['/runs', run.runId]">{{ run.runId }}</a></td>
                        <td><a [routerLink]="['/tasks', run.contract.taskId]">{{ run.contract.taskId }}</a></td>
                        <td>{{ run.contract.stageId }}</td>
                        <td>{{ run.contract.roleId }}</td>
                        <td class="mono">{{ run.contract.actorId }}</td>
                        <td><span class="chip">{{ run.contract.executionMode }}</span></td>
                        <td><cc-status-badge [label]="states[run.presentationState].label" [tone]="states[run.presentationState].tone" /></td>
                        <td class="muted nowrap">{{ run.startedLabel }}</td>
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
export class Runs {
  private readonly dataSource = inject(ControlCenterDataSource);

  protected readonly states = PRESENTATION_STATE;
  protected readonly state = toLoadState(this.dataSource.listRuns());
  protected readonly filter = signal<RunFilter>('all');

  protected readonly filters: readonly { value: RunFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'in-progress', label: 'In progress' },
    { value: 'needs-attention', label: 'Needs attention' },
    { value: 'finished', label: 'Finished' },
  ];

  private readonly runs = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : [];
  });

  protected readonly rows = computed(() => {
    const filter = this.filter();
    return filter === 'all' ? this.runs() : this.runs().filter((run) => run.presentationState === filter);
  });

  protected readonly counts = computed(() => {
    const runs = this.runs();
    const tally: Record<string, number> = { all: runs.length };
    for (const option of this.filters.slice(1)) {
      tally[option.value] = runs.filter((run) => run.presentationState === option.value).length;
    }
    return tally;
  });
}
