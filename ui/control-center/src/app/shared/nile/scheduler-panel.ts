import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import {
  DagNodePresentation,
  SchedulerPresentationState,
  SchedulerSummaryReadModel,
} from '../../data/models';
import { SCHEDULER_DISCLAIMER_NOTICE } from '../../data/dag-adapter';
import { Icon } from '../icon';

export interface SchedulerPillItem {
  readonly id: string;
  readonly label: string;
  readonly count: number;
  readonly tone: 'muted' | 'info' | 'warning' | 'danger' | 'success';
  readonly state?: SchedulerPresentationState;
}

@Component({
  selector: 'cc-scheduler-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  templateUrl: './scheduler-panel.html',
  styleUrl: './scheduler-panel.css',
})
export class SchedulerPanel {
  readonly summary = input.required<SchedulerSummaryReadModel>();
  readonly nodes = input<readonly DagNodePresentation[]>([]);
  readonly selectedNodeId = input<string | undefined>();
  readonly activeStateFilter = input<string>('all');

  readonly filterChange = output<string>();
  readonly nodeSelect = output<DagNodePresentation>();

  protected readonly disclaimerNotice = SCHEDULER_DISCLAIMER_NOTICE;

  protected readonly pills = computed<readonly SchedulerPillItem[]>(() => {
    const s = this.summary();
    const total = this.nodes().length;

    return [
      { id: 'all', label: 'All nodes', count: total, tone: 'muted' },
      { id: 'active-looking', label: 'Active (looking)', count: s.activeLookingCount, tone: 'info', state: 'active-looking' },
      { id: 'ready-looking', label: 'Ready (looking)', count: s.readyLookingCount, tone: 'info', state: 'ready-looking' },
      { id: 'blocked-looking', label: 'Blocked (looking)', count: s.blockedLookingCount, tone: 'warning', state: 'blocked-looking' },
      { id: 'attention', label: 'Needs Attention', count: s.attentionCount, tone: 'danger', state: 'attention' },
      { id: 'completed-looking', label: 'Completed (looking)', count: s.completedLookingCount, tone: 'success', state: 'completed-looking' },
      { id: 'queued', label: 'Queued', count: s.queuedCount, tone: 'muted', state: 'queued' },
    ];
  });

  protected readonly activeOrAttentionNodes = computed(() => {
    return this.nodes().filter(
      (node) =>
        node.schedulerState === 'active-looking' ||
        node.schedulerState === 'blocked-looking' ||
        node.schedulerState === 'attention' ||
        node.isEffectAmbiguous,
    );
  });

  protected setFilter(filterId: string): void {
    this.filterChange.emit(filterId);
  }

  protected selectNode(node: DagNodePresentation): void {
    this.nodeSelect.emit(node);
  }
}
