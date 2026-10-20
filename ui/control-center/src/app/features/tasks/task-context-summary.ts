import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { RunDetail, RunSummary, TaskDetail } from '../../data/models';
import { toLoadState } from '../../shared/load-state';

/** Composition of existing mock subjects, never an acceptance or authority assessment. */
@Component({
  selector: 'cc-task-context-summary',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  styleUrl: './task-context-summary.css',
  template: `
    <section class="card context-summary" aria-labelledby="task-context-title">
      <div class="card-head">
        <div>
          <h2 id="task-context-title">Task context</h2>
          <p>
            Mock observations for <strong class="mono">{{ task().id }}</strong> · Read-only
            inspection
          </p>
        </div>
      </div>
      <dl class="context-grid">
        <div>
          <dt>Scope</dt>
          <dd>
            {{ task().scopeIncluded.length }} included · {{ task().scopeExcluded.length }} excluded
          </dd>
          <dd>{{ task().scopeIncluded.join('; ') || 'No included scope supplied.' }}</dd>
        </div>
        <div>
          <dt>Associated Runs</dt>
          <dd>
            @if (runReadStatus() === 'ready') {
              {{ runs().length }} matching Run records supplied.
              @if (task().runIds.length > runs().length) {
                Some Task Run references have no matching Run record.
              }
            } @else if (runReadStatus() === 'error') {
              Run records unavailable: the list could not be read.
            } @else {
              Loading Run records…
            }
          </dd>
          <dd>
            @if (selectedRun(); as run) {
              Inspecting <a class="mono" [routerLink]="['/runs', run.runId]">{{ run.runId }}</a> ·
              {{ run.contract.stageId }} · {{ run.contract.roleId }} · {{ run.contract.actorId }}
            } @else if (selectionStatus() === 'loading' && runs().length) {
              Loading selected Run details…
            } @else {
              No matching selected Run details available.
            }
          </dd>
        </div>
        <div>
          <dt>Actor / Role observations</dt>
          <dd>
            @if (agentState().status === 'ready') {
              <details>
                <summary>{{ assignments().length }} supplied assignments</summary>
                <ul>
                  @for (assignment of assignments(); track $index) {
                    <li>
                      <span class="mono">{{ assignment.actorId }}</span> ·
                      {{ assignment.stageId }} · {{ assignment.roleId }}
                    </li>
                  } @empty {
                    <li>No assignment observations supplied for this Task.</li>
                  }
                </ul>
              </details>
            } @else if (agentState().status === 'error') {
              Assignment observations unavailable: source read failed.
            } @else {
              Loading assignment observations…
            }
          </dd>
        </div>
        <div>
          <dt>Approval evidence</dt>
          <dd>
            @if (approvalState().status === 'ready') {
              <details>
                <summary>{{ approvals().length }} supplied approval records</summary>
                <ul>
                  @for (approval of approvals(); track approval.id) {
                    <li>
                      <span class="mono">{{ approval.id }}</span> · {{ approval.stageId }}
                      @if (approval.runId) {
                        · Run <span class="mono">{{ approval.runId }}</span>
                      }
                      <br />{{ approval.action }} <br />{{
                        approval.state === 'awaiting'
                          ? 'Awaiting — authorization unproven'
                          : approval.state
                      }}
                      @if (approval.authorityId) {
                        · Supplied authority: {{ approval.authorityId }}
                      }
                    </li>
                  } @empty {
                    <li>No approval records supplied for this Task. Authorization is unproven.</li>
                  }
                </ul>
              </details>
            } @else if (approvalState().status === 'error') {
              Approval evidence unavailable: source read failed.
            } @else {
              Loading approval evidence…
            }
          </dd>
          <dd>Illustrative records establish no operational permission or Task acceptance.</dd>
        </div>
        <div>
          <dt>Review evidence · selected Run only</dt>
          <dd>
            @if (selectedRun(); as run) {
              <span class="mono">{{ run.runId }}</span
              >:
              <ul>
                @for (evidence of reviewEvidence(); track evidence.id) {
                  <li>
                    {{ evidence.title }} ·
                    {{ evidence.isUnavailable ? 'unavailable' : evidence.outcome }} ·
                    <span class="mono">{{ evidence.referenceId || evidence.id }}</span> <br />{{
                      evidence.summary
                    }}
                    · Source: {{ evidence.source }}
                  </li>
                } @empty {
                  <li>No review evidence supplied for this Run.</li>
                }
              </ul>
            } @else {
              Review evidence unavailable until matching Run details are supplied.
            }
          </dd>
          <dd>Review notes do not certify independent review. Inspect other Runs separately.</dd>
        </div>
        <div>
          <dt>Human acceptance</dt>
          <dd>Not supplied by this mock data model.</dd>
          <dd>
            Task status, approval records and successful Runs do not establish final Human
            acceptance.
          </dd>
        </div>
      </dl>
    </section>
  `,
})
export class TaskContextSummary {
  readonly task = input.required<TaskDetail>();
  readonly runs = input.required<readonly RunSummary[]>();
  readonly selectedRun = input<RunDetail>();
  readonly runReadStatus = input.required<'loading' | 'ready' | 'error'>();
  readonly selectionStatus = input.required<'loading' | 'ready' | 'error'>();
  private readonly dataSource = inject(ControlCenterDataSource);
  protected readonly agentState = toLoadState(this.dataSource.listAgents());
  protected readonly approvalState = toLoadState(this.dataSource.listApprovals());
  protected readonly assignments = computed(() => {
    const state = this.agentState();
    return state.status === 'ready'
      ? state.data.flatMap((actor) =>
          actor.assignments
            .filter((assignment) => assignment.taskId === this.task().id)
            .map((assignment) => ({ ...assignment, actorId: actor.actorId })),
        )
      : [];
  });
  protected readonly approvals = computed(() => {
    const state = this.approvalState();
    return state.status === 'ready'
      ? state.data.filter((approval) => approval.taskId === this.task().id)
      : [];
  });
  protected readonly reviewEvidence = computed(
    () =>
      this.selectedRun()?.evidence.filter(
        (item) =>
          item.category === 'review-note' ||
          (item.category === 'quality-gate' && item.title === 'independent_review'),
      ) ?? [],
  );
}
