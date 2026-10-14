import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { toLoadState } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { APPROVAL_LEVEL, APPROVAL_STATE } from '../../shared/presentation';
import { StatePanel } from '../../shared/state-panel';
import { StatusBadge } from '../../shared/status-badge';

@Component({
  selector: 'cc-approvals',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel, StatusBadge],
  styleUrl: './approvals.css',
  template: `
    <section class="page">
      <cc-page-header
        title="Approvals"
        lede="Human control checkpoints and the authorization evidence supplied for exact actions."
      />

      <div class="notice" role="note">
        <div>
          <strong>Read-only.</strong> This view only displays evidence. Granting or denying is not available until Core
          defines how an approval decision is recorded. “No evidence yet” means authorization is unproven, not denied.
        </div>
      </div>

      @switch (state().status) {
        @case ('loading') {
          <cc-state-panel kind="loading" />
        }
        @case ('error') {
          <cc-state-panel kind="error" title="Could not load approvals" />
        }
        @default {
          @for (group of groups(); track group.key) {
            <section class="group" [attr.aria-labelledby]="'group-' + group.key">
              <h2 [id]="'group-' + group.key">
                {{ group.title }} <span class="count">{{ group.items.length }}</span>
              </h2>
              @if (group.items.length === 0) {
                <cc-state-panel kind="empty" [title]="group.empty" />
              } @else {
                <ul class="items">
                  @for (item of group.items; track item.id) {
                    <li class="card item" [attr.data-state]="item.state">
                      <div class="top">
                        <div class="row">
                          <cc-status-badge [label]="approvalState[item.state].label" [tone]="approvalState[item.state].tone" />
                          <cc-status-badge [label]="level[item.level].label + ' approval'" [tone]="level[item.level].tone" />
                        </div>
                        <span class="muted">{{ item.requestedLabel }}</span>
                      </div>
                      <p class="action">{{ item.action }}</p>
                      <div class="meta row">
                        <a [routerLink]="['/tasks', item.taskId]">{{ item.taskId }}</a>
                        <span class="chip">{{ item.stageId }}</span>
                        @if (item.runId) {
                          <a class="mono" [routerLink]="['/runs', item.runId]">{{ item.runId }}</a>
                        }
                        @if (item.authorityId) {
                          <span class="muted">by <span class="mono">{{ item.authorityId }}</span></span>
                        }
                      </div>
                    </li>
                  }
                </ul>
              }
            </section>
          }
        }
      }
    </section>
  `,
})
export class Approvals {
  private readonly dataSource = inject(ControlCenterDataSource);

  protected readonly level = APPROVAL_LEVEL;
  protected readonly approvalState = APPROVAL_STATE;
  protected readonly state = toLoadState(this.dataSource.listApprovals());

  protected readonly groups = computed(() => {
    const state = this.state();
    const items = state.status === 'ready' ? state.data : [];
    return [
      {
        key: 'awaiting',
        title: 'Waiting for a person',
        empty: 'Nothing is waiting for approval evidence',
        items: items.filter((item) => item.state === 'awaiting'),
      },
      {
        key: 'decided',
        title: 'Evidence recorded',
        empty: 'No evidence has been recorded',
        items: items.filter((item) => item.state !== 'awaiting'),
      },
    ];
  });
}
