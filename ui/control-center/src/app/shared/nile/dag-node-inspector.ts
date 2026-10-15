import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  DagGraphPresentation,
  DagNodePresentation,
} from '../../data/models';
import {
  DEPENDENCY_DISCLAIMER_NOTICE,
  EFFECT_AMBIGUOUS_DAG_WARNING,
} from '../../data/dag-adapter';
import { ContinuationShell } from '../continuation-shell';
import { EvidencePanel } from '../evidence-panel';
import { ExecutionTimeline } from '../execution-timeline';
import { Icon } from '../icon';
import { ResultShell } from '../result-shell';
import { StatusBadge } from '../status-badge';

@Component({
  selector: 'cc-dag-node-inspector',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    Icon,
    StatusBadge,
    ResultShell,
    ContinuationShell,
    ExecutionTimeline,
    EvidencePanel,
  ],
  templateUrl: './dag-node-inspector.html',
  styleUrl: './dag-node-inspector.css',
})
export class DagNodeInspector {
  readonly node = input<DagNodePresentation | null>(null);
  readonly graph = input<DagGraphPresentation | null>(null);

  readonly close = output<void>();
  readonly nodeSelect = output<DagNodePresentation>();

  protected readonly dependencyNotice = DEPENDENCY_DISCLAIMER_NOTICE;
  protected readonly effectAmbiguousWarning = EFFECT_AMBIGUOUS_DAG_WARNING;

  protected readonly upstreamNodes = computed<readonly DagNodePresentation[]>(() => {
    const n = this.node();
    const g = this.graph();
    if (!n || !g) {
      return [];
    }
    return n.upstreamNodeIds
      .map((id) => g.nodeMap.get(id))
      .filter((item): item is DagNodePresentation => Boolean(item));
  });

  protected readonly downstreamNodes = computed<readonly DagNodePresentation[]>(() => {
    const n = this.node();
    const g = this.graph();
    if (!n || !g) {
      return [];
    }
    return n.downstreamNodeIds
      .map((id) => g.nodeMap.get(id))
      .filter((item): item is DagNodePresentation => Boolean(item));
  });

  protected readonly blockedByNodes = computed<readonly DagNodePresentation[]>(() => {
    const n = this.node();
    const g = this.graph();
    if (!n || !g) {
      return [];
    }
    return n.blockedByNodeIds
      .map((id) => g.nodeMap.get(id))
      .filter((item): item is DagNodePresentation => Boolean(item));
  });

  protected selectRelated(relatedNode: DagNodePresentation): void {
    this.nodeSelect.emit(relatedNode);
  }

  protected dismiss(): void {
    this.close.emit();
  }
}
