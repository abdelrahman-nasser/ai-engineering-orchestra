import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { NileNode } from '../../data/models';
import { EvidencePanel } from '../../shared/evidence-panel';
import { ExecutionTimeline } from '../../shared/execution-timeline';
import { toLoadStateFor } from '../../shared/load-state';
import { NileFlow } from '../../shared/nile/nile-flow';
import { buildRunTopology } from '../../shared/nile/nile-topology';
import { PageHeader } from '../../shared/page-header';
import { PRESENTATION_STATE } from '../../shared/presentation';
import { ResultShell } from '../../shared/result-shell';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

@Component({
  selector: 'cc-run-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    PageHeader,
    StatePanel,
    StatusBadge,
    NileFlow,
    ExecutionTimeline,
    EvidencePanel,
    ResultShell,
  ],
  styleUrl: './run-detail.css',
  template: `
    <section class="page">
      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load this Run" />
        }
        @default {
          @if (run(); as r) {
            <cc-page-header
              [title]="r.runId"
              [crumbs]="[{ label: 'Runs', link: ['/runs'] }, { label: r.runId }]"
              [lede]="r.contract.roleId + ' work in the ' + r.contract.stageId + ' stage of ' + r.contract.taskId + ' — ' + r.taskTitle"
            >
              <cc-status-badge [label]="states[r.presentationState].label" [tone]="states[r.presentationState].tone" />
            </cc-page-header>

            <div class="card">
              <div class="card-head">
                <div>
                  <h2>Workflow river</h2>
                  <p>
                    The {{ r.contract.workflowId }} Workflow as a trunk, with the Runs bound to each Stage drawn as
                    tributaries. This Run is highlighted; select another island to open it.
                  </p>
                </div>
              </div>
              <cc-nile-flow
                [topology]="topology()!"
                [selectedId]="r.runId"
                [columnWidth]="175"
                ariaLabel="Workflow stages and runs"
                (nodeSelect)="open($event)"
              />
            </div>

            <div class="grid grid-main-aside">
              <div class="stack column">
                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Execution timeline</h2>
                      <p>Presentation entries only. Core defines no Journal yet.</p>
                    </div>
                  </div>
                  <cc-execution-timeline [entries]="r.timeline" />
                </div>

                <div class="card">
                  <div class="card-head"><h2>Result</h2></div>
                  <cc-result-shell [result]="r.result" />
                </div>
              </div>

              <div class="stack column">
                <div class="card">
                  <div class="card-head"><h2>Run identity</h2></div>
                  <dl class="kv" aria-label="Run identity">
                    <dt>Run ID</dt><dd class="mono">{{ r.runId }}</dd>
                    <dt>Task</dt><dd><a [routerLink]="['/tasks', r.contract.taskId]">{{ r.contract.taskId }}</a></dd>
                    <dt>Workflow</dt><dd>{{ r.contract.workflowId }}</dd>
                    <dt>Stage</dt><dd>{{ r.contract.stageId }}</dd>
                    <dt>Role</dt><dd>{{ r.contract.roleId }}</dd>
                    <dt>Actor</dt><dd class="mono">{{ r.contract.actorId }}</dd>
                    <dt>Runtime option</dt><dd class="mono">{{ r.contract.runtimeOptionId }}</dd>
                    <dt>Inference option</dt><dd class="mono">{{ r.contract.optionId }}</dd>
                    <dt>Environment</dt><dd class="mono">{{ r.contract.environmentId }}</dd>
                    <dt>Operation</dt><dd class="mono">{{ r.contract.operationId }}</dd>
                    <dt>Resource</dt><dd class="mono">{{ r.contract.resource }}</dd>
                    <dt>Mode</dt><dd><span class="chip">{{ r.contract.executionMode }}</span></dd>
                  </dl>
                </div>

                <div class="card">
                  <div class="card-head"><h2>Evidence</h2></div>
                  <cc-evidence-panel [items]="r.evidence" />
                </div>
              </div>
            </div>
          } @else {
            <cc-state-panel kind="not-found" title="Run not found" message="No Run with this identifier exists in the current data source.">
              <a class="btn" routerLink="/runs">Back to Runs</a>
            </cc-state-panel>
          }
        }
      }
    </section>
  `,
})
export class RunDetailPage {
  /** Bound from the `:runId` route parameter. */
  readonly runId = input.required<string>();

  private readonly dataSource = inject(ControlCenterDataSource);
  private readonly router = inject(Router);

  protected readonly states = PRESENTATION_STATE;
  protected readonly state = toLoadStateFor(this.runId, (id) => this.dataSource.getRun(id));

  protected readonly run = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : undefined;
  });

  protected readonly topology = computed(() => {
    const run = this.run();
    return run ? buildRunTopology(run) : null;
  });

  protected open(node: NileNode): void {
    if (node.kind === 'run') {
      void this.router.navigate(['/runs', node.id]);
    }
  }
}
