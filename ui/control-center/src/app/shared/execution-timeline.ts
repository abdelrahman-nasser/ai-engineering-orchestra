import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { PresentationState, TimelineEntry, TimelineKind } from '../data/models';
import { Icon, IconName } from './icon';
import { PRESENTATION_STATE } from './presentation';
import { StatusBadge } from './status-badge';

const KIND_ICON: Readonly<Record<TimelineKind, IconName>> = {
  stage: 'branch',
  agent: 'agents',
  'quality-gate': 'check',
  approval: 'shield',
  note: 'file',
};

/**
 * Reusable Execution Timeline.
 *
 * Renders UI-local {@link TimelineEntry} values in array order. It is not a
 * Journal view: Core defines no Journal, so no ordering, timestamps or event
 * semantics are asserted beyond what the caller supplies.
 */
@Component({
  selector: 'cc-execution-timeline',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatusBadge],
  styleUrl: './execution-timeline.css',
  template: `
    @if (entries().length === 0) {
      <p class="muted empty">No timeline entries to show.</p>
    } @else {
      <ol class="timeline" aria-label="Execution timeline">
        @for (entry of entries(); track entry.id) {
          <li class="entry" [attr.data-state]="entry.state">
            <span class="marker" aria-hidden="true"><cc-icon [name]="icon(entry)" [size]="14" /></span>
            <div class="body">
              <div class="head">
                <strong>{{ entry.title }}</strong>
                <cc-status-badge [label]="label(entry.state)" [tone]="tone(entry.state)" />
              </div>
              @if (entry.detail) {
                <p class="detail">{{ entry.detail }}</p>
              }
              <div class="meta">
                <span>{{ entry.atLabel }}</span>
                @if (entry.stageId) {
                  <span class="chip">{{ entry.stageId }}</span>
                }
                @if (entry.actorId) {
                  <span class="chip mono">{{ entry.actorId }}</span>
                }
              </div>
            </div>
          </li>
        }
      </ol>
    }
  `,
})
export class ExecutionTimeline {
  readonly entries = input.required<readonly TimelineEntry[]>();

  protected icon(entry: TimelineEntry): IconName {
    return KIND_ICON[entry.kind];
  }
  protected label(state: PresentationState): string {
    return PRESENTATION_STATE[state].label;
  }
  protected tone(state: PresentationState) {
    return PRESENTATION_STATE[state].tone;
  }
}
