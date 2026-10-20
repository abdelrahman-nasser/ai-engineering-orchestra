import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  linkedSignal,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { NileNode, RunDetail } from '../../data/models';
import { map } from 'rxjs';
import { ContinuationShell } from '../../shared/continuation-shell';
import { EvidencePanel } from '../../shared/evidence-panel';
import { ExecutionTimeline } from '../../shared/execution-timeline';
import { LoadState, toLoadStateFor } from '../../shared/load-state';
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
    ContinuationShell,
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
              [lede]="
                r.contract.roleId +
                ' work in the ' +
                r.contract.stageId +
                ' stage of ' +
                r.contract.taskId +
                ' — ' +
                r.taskTitle
              "
            >
              <cc-status-badge
                [label]="states[r.presentationState].label"
                [tone]="states[r.presentationState].tone"
              />
            </cc-page-header>

            <div class="card">
              <div class="card-head">
                <div>
                  <h2>Workflow river</h2>
                  <p>
                    The {{ r.contract.workflowId }} Workflow as a trunk, with the Runs bound to each
                    Stage drawn as tributaries. This Run is highlighted; select another island to
                    open it.
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
                      <h2>Continuation &amp; Recovery</h2>
                      <p>Mock continuation metadata; operational continuation is unavailable.</p>
                    </div>
                  </div>
                  <cc-continuation-shell
                    [continuation]="r.continuation"
                    [runId]="r.runId"
                    [resultOutcome]="activeResult()?.outcome"
                  />
                </div>

                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Execution timeline</h2>
                      <p>Mock presentation entries; this is not the canonical Journal.</p>
                    </div>
                  </div>
                  <cc-execution-timeline
                    [entries]="r.timeline"
                    [(selectedId)]="selectedTimelineId"
                  />
                </div>

                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Result</h2>
                      @if (selectedTimelineEntry()?.hasResult) {
                        <p>
                          Linked outcome for selected event:
                          <strong>{{ selectedTimelineEntry()?.title }}</strong>
                        </p>
                      } @else {
                        <p>Terminal run execution outcome</p>
                      }
                    </div>
                  </div>
                  <cc-result-shell [result]="activeResult()" />
                </div>
              </div>

              <div class="stack column">
                <div class="card">
                  <div class="card-head"><h2>Run identity</h2></div>
                  <dl class="kv" aria-label="Run identity">
                    <dt>Run ID</dt>
                    <dd class="mono">{{ r.runId }}</dd>
                    <dt>Task</dt>
                    <dd>
                      <a [routerLink]="['/tasks', r.contract.taskId]">{{ r.contract.taskId }}</a>
                    </dd>
                    <dt>Workflow</dt>
                    <dd>{{ r.contract.workflowId }}</dd>
                    <dt>Stage</dt>
                    <dd>{{ r.contract.stageId }}</dd>
                    <dt>Role</dt>
                    <dd>{{ r.contract.roleId }}</dd>
                    <dt>Actor</dt>
                    <dd class="mono">{{ r.contract.actorId }}</dd>
                    <dt>Runtime option</dt>
                    <dd class="mono">{{ r.contract.runtimeOptionId }}</dd>
                    <dt>Inference option</dt>
                    <dd class="mono">{{ r.contract.optionId }}</dd>
                    <dt>Environment</dt>
                    <dd class="mono">{{ r.contract.environmentId }}</dd>
                    <dt>Operation</dt>
                    <dd class="mono">{{ r.contract.operationId }}</dd>
                    <dt>Resource</dt>
                    <dd class="mono">{{ r.contract.resource }}</dd>
                    <dt>Mode</dt>
                    <dd>
                      <span class="chip">{{ r.contract.executionMode }}</span>
                    </dd>
                  </dl>
                </div>

                <div class="card">
                  <div class="card-head">
                    <div>
                      <h2>Evidence Explorer</h2>
                      @if (selectedTimelineEntry(); as selected) {
                        <p>
                          Event-scoped evidence: <strong>{{ selected.title }}</strong>
                        </p>
                      } @else {
                        <p>
                          Run-wide evidence · {{ r.runId }}. These records are not attributed to an
                          individual event.
                        </p>
                      }
                    </div>
                    <button
                      type="button"
                      class="btn btn-ghost"
                      [attr.aria-pressed]="!selectedTimelineId()"
                      (click)="selectedTimelineId.set(null)"
                    >
                      Show Run-wide evidence
                    </button>
                  </div>
                  @if (selectedTimelineEntry() && activeEvidence().length === 0) {
                    <cc-state-panel
                      kind="empty"
                      title="No evidence supplied for this event"
                      message="Run-wide records are separate. No event relationship is inferred."
                    />
                  } @else {
                    <cc-evidence-panel [items]="activeEvidence()" />
                  }
                </div>
              </div>
            </div>
          } @else {
            <cc-state-panel
              kind="not-found"
              title="Run not found"
              message="No Run with this identifier exists in the current data source."
            >
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
  private readonly runRead = toLoadStateFor(this.runId, (id) =>
    this.dataSource.getRun(id).pipe(map((data) => ({ id, data }))),
  );
  protected readonly state = computed<LoadState<RunDetail | undefined>>(() => {
    const read = this.runRead();
    if (read.status !== 'ready') return read;
    if (read.data.id !== this.runId()) return { status: 'loading' };
    if (read.data.data && read.data.data.runId !== this.runId()) {
      return { status: 'error', message: 'Run identity does not match the requested Run.' };
    }
    return { status: 'ready', data: read.data.data };
  });

  readonly selectedTimelineId = linkedSignal<string, string | null>({
    source: this.runId,
    computation: () => null,
  });

  protected readonly run = computed(() => {
    const state = this.state();
    return state.status === 'ready' && state.data?.runId === this.runId() ? state.data : undefined;
  });

  protected readonly selectedTimelineEntry = computed(() => {
    const id = this.selectedTimelineId();
    const run = this.run();
    if (!id || !run) return null;
    return run.timeline.find((t) => t.id === id) ?? null;
  });

  protected readonly activeResult = computed(() => {
    const sel = this.selectedTimelineEntry();
    if (sel?.hasResult) {
      return sel.result;
    }
    return this.run()?.result ?? null;
  });

  protected readonly activeEvidence = computed(() => {
    const sel = this.selectedTimelineEntry();
    if (sel) {
      return sel.evidence;
    }
    return this.run()?.evidence ?? [];
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
