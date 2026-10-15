import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { AgentExecutionResultOutcome, PresentationState, Tone } from '../../data/models';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { PRESENTATION_STATE } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

type RunFilter =
  | 'all'
  | 'in-progress'
  | 'needs-attention'
  | 'finished'
  | 'has-result'
  | 'has-evidence'
  | 'continuation-available';

function formatResult(outcome: AgentExecutionResultOutcome): { label: string; tone: Tone } {
  switch (outcome) {
    case 'succeeded':
      return { label: 'Succeeded', tone: 'success' };
    case 'failed_before_effect':
      return { label: 'Failed before effect', tone: 'neutral' };
    case 'effect_ambiguous':
      return { label: 'Effect ambiguous', tone: 'warning' };
  }
}

@Component({
  selector: 'cc-runs',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: '../shared-list.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Runs"
        lede="Historical and active runs across the workspace. Each Run represents one assigned action. Visual states, last activity, and continuation affordances are supplied by the current data source."
      />

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load Runs" />
        }
        @default {
          <div class="filters" role="group" aria-label="Filter runs by status or affordance">
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
                      <th scope="col">Stage &amp; Workflow</th>
                      <th scope="col">Role &amp; Actor</th>
                      <th scope="col">Visual state</th>
                      <th scope="col">Result</th>
                      <th scope="col">Evidence</th>
                      <th scope="col">Continuation</th>
                      <th scope="col">Last activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (run of rows(); track run.runId) {
                      <tr>
                        <td><a class="row-link mono" [routerLink]="['/runs', run.runId]">{{ run.runId }}</a></td>
                        <td><a [routerLink]="['/tasks', run.contract.taskId]">{{ run.contract.taskId }}</a></td>
                        <td>
                          <div>{{ run.contract.stageId }}</div>
                          <div class="muted text-xs">{{ run.contract.workflowId }}</div>
                        </td>
                        <td>
                          <div>{{ run.contract.roleId }}</div>
                          <div class="mono muted text-xs">{{ run.contract.actorId }}</div>
                        </td>
                        <td>
                          <cc-status-badge [label]="states[run.presentationState].label" [tone]="states[run.presentationState].tone" />
                          @if (run.statusLabel && run.statusLabel !== states[run.presentationState].label) {
                            <div class="text-xs muted">{{ run.statusLabel }}</div>
                          }
                        </td>
                        <td>
                          @if (run.resultOutcome) {
                            <cc-status-badge [label]="formatResult(run.resultOutcome).label" [tone]="formatResult(run.resultOutcome).tone" />
                          } @else if (run.hasResult) {
                            <cc-status-badge label="Published" tone="info" />
                          } @else {
                            <span class="muted text-xs">—</span>
                          }
                        </td>
                        <td>
                          @if (run.evidenceCount) {
                            <span class="chip">{{ run.evidenceCount }} item{{ run.evidenceCount === 1 ? '' : 's' }}</span>
                          } @else {
                            <span class="muted text-xs">—</span>
                          }
                        </td>
                        <td>
                          @if (run.continuation) {
                            <cc-status-badge [label]="run.continuation.statusLabel" [tone]="run.continuation.statusTone" />
                          } @else {
                            <span class="muted text-xs">—</span>
                          }
                        </td>
                        <td class="muted nowrap text-xs">{{ run.lastActivityLabel || run.startedLabel }}</td>
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
  protected readonly formatResult = formatResult;

  protected readonly filters: readonly { value: RunFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'in-progress', label: 'In progress' },
    { value: 'needs-attention', label: 'Needs attention' },
    { value: 'finished', label: 'Finished' },
    { value: 'has-result', label: 'Has Result' },
    { value: 'has-evidence', label: 'Has evidence' },
    { value: 'continuation-available', label: 'Continuation available' },
  ];

  private readonly runs = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : [];
  });

  protected readonly rows = computed(() => {
    const filter = this.filter();
    const all = this.runs();
    switch (filter) {
      case 'all':
        return all;
      case 'in-progress':
        return all.filter((r) => r.presentationState === 'in-progress');
      case 'needs-attention':
        return all.filter((r) => r.presentationState === 'needs-attention');
      case 'finished':
        return all.filter((r) => r.presentationState === 'finished');
      case 'has-result':
        return all.filter((r) => r.hasResult || r.resultOutcome !== undefined);
      case 'has-evidence':
        return all.filter((r) => Boolean(r.evidenceCount && r.evidenceCount > 0));
      case 'continuation-available':
        return all.filter((r) => Boolean(r.continuation?.isAvailable && r.resultOutcome !== 'effect_ambiguous'));
    }
  });

  protected readonly counts = computed(() => {
    const runs = this.runs();
    return {
      all: runs.length,
      'in-progress': runs.filter((r) => r.presentationState === 'in-progress').length,
      'needs-attention': runs.filter((r) => r.presentationState === 'needs-attention').length,
      finished: runs.filter((r) => r.presentationState === 'finished').length,
      'has-result': runs.filter((r) => r.hasResult || r.resultOutcome !== undefined).length,
      'has-evidence': runs.filter((r) => Boolean(r.evidenceCount && r.evidenceCount > 0)).length,
      'continuation-available': runs.filter((r) => Boolean(r.continuation?.isAvailable && r.resultOutcome !== 'effect_ambiguous')).length,
    };
  });
}
