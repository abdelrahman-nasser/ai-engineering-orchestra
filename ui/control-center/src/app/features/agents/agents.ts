import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { ActorKind } from '../../data/models';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { AVAILABILITY } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

type KindFilter = 'all' | ActorKind;

@Component({
  selector: 'cc-agents',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: '../shared-list.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Agents"
        lede="Actors who can fulfil Roles. Availability is a snapshot observation: unknown is not unavailable."
      />

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load Agents" />
        }
        @default {
          <div class="filters" role="group" aria-label="Filter actors by kind">
            @for (option of filters; track option.value) {
              <button
                type="button"
                class="filter"
                [attr.aria-pressed]="filter() === option.value"
                [attr.data-testid]="'agent-filter-' + option.value"
                (click)="filter.set(option.value)"
              >
                {{ option.label }}
              </button>
            }
          </div>

          <div class="grid grid-3 cards">
            @for (agent of rows(); track agent.actorId) {
              <article class="card actor" [attr.aria-label]="agent.name">
                <header class="actor-head">
                  <span class="avatar" [attr.data-kind]="agent.kind" aria-hidden="true">{{ agent.name.charAt(0) }}</span>
                  <div class="who">
                    <h2>{{ agent.name }}</h2>
                    <span class="mono faint">{{ agent.actorId }}</span>
                  </div>
                  <cc-status-badge [label]="availability[agent.availability].label" [tone]="availability[agent.availability].tone" />
                </header>

                <dl class="kv">
                  <dt>Kind</dt>
                  <dd><span class="chip">{{ agent.kind }}</span></dd>
                  <dt>Roles</dt>
                  <dd class="row">
                    @for (role of agent.roleIds; track role) { <span class="chip">{{ role }}</span> }
                  </dd>
                  @if (agent.kind === 'agent') {
                    <dt>Runtime</dt>
                    <dd class="row">
                      @for (option of agent.runtimeOptionIds; track option) { <span class="chip mono">{{ option }}</span> }
                    </dd>
                  }
                </dl>

                <div class="assignments">
                  <div class="eyebrow">Assignments</div>
                  @for (assignment of agent.assignments; track assignment.taskId + assignment.stageId + assignment.roleId) {
                    <a class="assignment" [routerLink]="['/tasks', assignment.taskId]">
                      <strong>{{ assignment.taskId }}</strong>
                      <span class="muted">{{ assignment.stageId }} · {{ assignment.roleId }}</span>
                    </a>
                  } @empty {
                    <span class="muted">None</span>
                  }
                </div>
              </article>
            } @empty {
              <cc-state-panel kind="empty" title="No actors match this filter" />
            }
          </div>
        }
      }
    </section>
  `,
  styles: `
    .actor {
      display: flex;
      flex-direction: column;
      gap: var(--space-4);
      transition:
        transform 0.2s var(--ease),
        border-color 0.2s var(--ease);
    }
    .actor:hover {
      transform: translateY(-2px);
      border-color: var(--border-strong);
    }
    .actor-head {
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }
    .who {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
    }
    .who h2 {
      font-size: 17px;
    }
    .avatar {
      display: grid;
      place-items: center;
      flex: none;
      width: 42px;
      height: 42px;
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 600;
      color: var(--accent-ink);
      background: linear-gradient(135deg, var(--accent), var(--lapis));
      border-radius: 14px;
    }
    .avatar[data-kind='human'] {
      background: linear-gradient(135deg, var(--gold), color-mix(in srgb, var(--gold) 65%, var(--warning)));
      border-radius: 50%;
    }
    .assignments {
      display: flex;
      flex-direction: column;
      gap: var(--space-2);
    }
    .assignment {
      display: flex;
      justify-content: space-between;
      gap: var(--space-3);
      padding: 8px var(--space-3);
      color: var(--text);
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 13px;
    }
    .assignment:hover {
      text-decoration: none;
      border-color: var(--border-strong);
    }
  `,
})
export class Agents {
  private readonly dataSource = inject(ControlCenterDataSource);

  protected readonly availability = AVAILABILITY;
  protected readonly state = toLoadState(this.dataSource.listAgents());
  protected readonly filter = signal<KindFilter>('all');

  protected readonly filters: readonly { value: KindFilter; label: string }[] = [
    { value: 'all', label: 'All actors' },
    { value: 'agent', label: 'Agents' },
    { value: 'human', label: 'Humans' },
  ];

  protected readonly rows = computed(() => {
    const state = this.state();
    if (state.status !== 'ready') {
      return [];
    }
    const filter = this.filter();
    return filter === 'all' ? state.data : state.data.filter((actor) => actor.kind === filter);
  });
}
