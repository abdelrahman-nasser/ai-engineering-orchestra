import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import {
  DagEdgePresentation,
  DagGraphPresentation,
  DagNodeKind,
  DagNodePresentation,
  PresentationState,
  Tone,
} from '../../data/models';
import { Icon } from '../icon';

const NODE_RADIUS: Readonly<Record<DagNodeKind, number>> = {
  stage: 14,
  run: 10,
  subagent: 11,
  join: 13,
  checkpoint: 12,
  outcome: 15,
  task: 12,
};

const TONE_COLORS: Readonly<Record<Tone, string>> = {
  info: 'var(--info)',
  warning: 'var(--warning)',
  danger: 'var(--danger)',
  success: 'var(--success)',
  accent: 'var(--accent)',
  muted: 'var(--text-muted)',
  neutral: 'var(--border)',
};

export interface PlacedDagNode {
  readonly node: DagNodePresentation;
  readonly x: number;
  readonly y: number;
  readonly r: number;
  readonly color: string;
  readonly label: string;
  readonly sublabel?: string;
  readonly labelX: number;
  readonly labelY: number;
  readonly subY: number;
  readonly anchor: 'start' | 'middle' | 'end';
  readonly isSelected: boolean;
  readonly isUpstream: boolean;
  readonly isDownstream: boolean;
  readonly isDimmed: boolean;
  readonly hasPulse: boolean;
  readonly aria: string;
}

export interface PlacedDagEdge {
  readonly edge: DagEdgePresentation;
  readonly d: string;
  readonly weight: 'main' | 'tributary';
  readonly state: PresentationState | 'neutral';
  readonly isUpstreamPath: boolean;
  readonly isDownstreamPath: boolean;
  readonly isDimmed: boolean;
}

export interface DagFlowLayout {
  readonly width: number;
  readonly height: number;
  readonly nodes: readonly PlacedDagNode[];
  readonly edges: readonly PlacedDagEdge[];
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

function wobble(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) | 0;
  }
  return ((hash >>> 0) % 2000) / 1000 - 1;
}

@Component({
  selector: 'cc-dag-flow',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  templateUrl: './dag-flow.html',
  styleUrl: './dag-flow.css',
  host: {
    '(keydown)': 'handleKeydown($event)',
  },
})
export class DagFlow {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  readonly graph = input<DagGraphPresentation | null>(null);
  readonly selectedNodeId = input<string | undefined>();
  readonly viewMode = input<'river' | 'list'>('river');
  readonly columnWidth = input(240);
  readonly laneHeight = input(80);

  readonly nodeSelect = output<DagNodePresentation>();
  readonly viewModeChange = output<'river' | 'list'>();

  protected readonly viewportEl = viewChild<ElementRef<HTMLDivElement>>('viewport');

  protected readonly paused = signal(false);
  protected readonly zoom = signal(1);
  protected readonly panX = signal(0);
  protected readonly panY = signal(0);
  protected readonly isDragging = signal(false);

  private dragStartX = 0;
  private dragStartY = 0;
  private initialPanX = 0;
  private initialPanY = 0;

  // Selected node upstream and downstream sets for visual illumination
  protected readonly relatedSets = computed(() => {
    const selectedId = this.selectedNodeId();
    const g = this.graph();
    if (!selectedId || !g) {
      return { upstream: new Set<string>(), downstream: new Set<string>() };
    }

    const selected = g.nodeMap.get(selectedId);
    if (!selected) {
      return { upstream: new Set<string>(), downstream: new Set<string>() };
    }

    const upstream = new Set<string>(selected.upstreamNodeIds);
    const downstream = new Set<string>(selected.downstreamNodeIds);
    return { upstream, downstream };
  });

  protected readonly layout = computed<DagFlowLayout | null>(() => {
    const g = this.graph();
    if (!g || g.nodes.length === 0) {
      return null;
    }

    const colW = this.columnWidth();
    const laneH = this.laneHeight();
    const selectedId = this.selectedNodeId();
    const { upstream, downstream } = this.relatedSets();
    const hasSelection = Boolean(selectedId);

    const minCol = Math.min(...g.nodes.map((n) => n.column));
    const maxCol = Math.max(...g.nodes.map((n) => n.column));
    const padL = 120;
    const padR = 120;

    const minLane = Math.min(...g.nodes.map((n) => n.lane));
    const maxLane = Math.max(...g.nodes.map((n) => n.lane));
    const totalLaneSpan = (maxLane - minLane) * laneH;
    const offsetY = -minLane * laneH + 60;

    const placedNodes: PlacedDagNode[] = g.nodes.map((node) => {
      const r = NODE_RADIUS[node.kind] ?? 12;
      const x = padL + (node.column - minCol) * colW;
      const y = node.lane * laneH + offsetY;
      const isSelected = node.id === selectedId;
      const isUpstream = upstream.has(node.id);
      const isDownstream = downstream.has(node.id);
      const isDimmed = hasSelection && !isSelected && !isUpstream && !isDownstream;
      const color = node.isEffectAmbiguous
        ? 'var(--danger)'
        : (TONE_COLORS[node.schedulerTone] ?? 'var(--text-muted)');
      const hasPulse =
        node.schedulerState === 'active-looking' ||
        node.schedulerState === 'attention' ||
        node.isEffectAmbiguous;

      const side = node.lane > 0 ? 'below' : node.lane < 0 ? 'above' : 'below';
      let labelY = 0;
      let subY = 0;
      if (side === 'above') {
        labelY = -r - 20;
        subY = -r - 7;
      } else {
        labelY = r + 16;
        subY = r + 30;
      }

      const aria = `${node.kind} ${node.label}: ${node.schedulerStateLabel}${
        node.attentionReason ? `, ${node.attentionReason}` : ''
      }`;

      return {
        node,
        x,
        y,
        r,
        color,
        label: truncate(node.label, 24),
        sublabel: node.sublabel ? truncate(node.sublabel, 28) : undefined,
        labelX: 0,
        labelY,
        subY,
        anchor: 'middle',
        isSelected,
        isUpstream,
        isDownstream,
        isDimmed,
        hasPulse,
        aria,
      };
    });

    const nodeCoordMap = new Map(placedNodes.map((n) => [n.node.id, n]));
    const placedEdges: PlacedDagEdge[] = [];

    for (const edge of g.edges) {
      const from = nodeCoordMap.get(edge.from);
      const to = nodeCoordMap.get(edge.to);
      if (!from || !to) {
        continue;
      }

      const x1 = from.x + from.r;
      const x2 = to.x - to.r;
      const dx = Math.max(x2 - x1, 20);
      const dy = to.y - from.y;
      const meander = wobble(`${edge.from}->${edge.to}`) * 10;

      const cp1x = x1 + dx * 0.45;
      const cp2x = x2 - dx * 0.45;
      const cp1y = from.y + dy * 0.12 + meander;
      const cp2y = to.y - dy * 0.12 - meander;
      const d = `M ${x1} ${from.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${to.y}`;

      const isUpstreamPath =
        (selectedId !== undefined && edge.to === selectedId) ||
        (upstream.has(edge.from) && upstream.has(edge.to));
      const isDownstreamPath =
        (selectedId !== undefined && edge.from === selectedId) ||
        (downstream.has(edge.from) && downstream.has(edge.to));
      const isDimmed = hasSelection && !isUpstreamPath && !isDownstreamPath;

      placedEdges.push({
        edge,
        d,
        weight: edge.weight,
        state: edge.state,
        isUpstreamPath,
        isDownstreamPath,
        isDimmed,
      });
    }

    const width = padL + (maxCol - minCol) * colW + padR;
    const height = Math.max(totalLaneSpan + 140, 480);

    return {
      width,
      height,
      nodes: placedNodes,
      edges: placedEdges,
    };
  });

  protected chooseNode(node: DagNodePresentation): void {
    this.nodeSelect.emit(node);
  }

  /** Explicit inspector dismissal only; query/history changes never steal focus. */
  restoreNodeFocus(nodeId: string | undefined): boolean {
    if (!nodeId || !this.graph()?.nodeMap.has(nodeId)) return false;
    const trigger = Array.from(
      this.host.nativeElement.querySelectorAll<HTMLElement | SVGElement>('[data-node-id]'),
    ).find((element) => element.getAttribute('data-node-id') === nodeId);
    if (!trigger || trigger.closest('[hidden], [inert]')) return false;
    const viewport = this.viewportEl()?.nativeElement;
    if (viewport && this.viewMode() === 'river') {
      const nodeBounds = trigger.getBoundingClientRect();
      const bounds = viewport.getBoundingClientRect();
      // Do not return focus to a node clipped out of its panned canvas.
      if (
        bounds.width > 0 &&
        nodeBounds.width > 0 &&
        (nodeBounds.right <= bounds.left ||
          nodeBounds.left >= bounds.right ||
          nodeBounds.bottom <= bounds.top ||
          nodeBounds.top >= bounds.bottom)
      )
        return false;
    }
    trigger.focus({ preventScroll: true });
    return trigger.ownerDocument.activeElement === trigger;
  }

  protected setViewMode(mode: 'river' | 'list'): void {
    this.viewModeChange.emit(mode);
  }

  protected zoomIn(): void {
    this.zoom.update((z) => Math.min(Number((z + 0.15).toFixed(2)), 1.8));
  }

  protected zoomOut(): void {
    this.zoom.update((z) => Math.max(Number((z - 0.15).toFixed(2)), 0.1));
  }

  protected resetView(): void {
    this.zoom.set(1);
    this.panX.set(0);
    this.panY.set(0);
  }

  protected fitGraph(): void {
    const l = this.layout();
    const vp = this.viewportEl()?.nativeElement;
    if (!l || !vp) {
      return;
    }
    const vpWidth = vp.clientWidth;
    const vpHeight = vp.clientHeight;
    if (vpWidth <= 0 || vpHeight <= 0) return;
    const scaleX = vpWidth / (l.width + 40);
    const scaleY = vpHeight / (l.height + 40);
    const scale = Math.min(scaleX, scaleY, 1.2);
    this.zoom.set(scale);
    this.panX.set(0);
    this.panY.set(0);
  }

  protected focusSelected(selectedId = this.selectedNodeId()): void {
    const l = this.layout();
    const vp = this.viewportEl()?.nativeElement;
    if (!selectedId || !l || !vp) {
      return;
    }
    const node = l.nodes.find((n) => n.node.id === selectedId);
    if (!node) {
      return;
    }
    const vpCenter = { x: vp.clientWidth / 2, y: vp.clientHeight / 2 };
    this.panX.set(Math.round(vpCenter.x - node.x * this.zoom()));
    this.panY.set(Math.round(vpCenter.y - node.y * this.zoom()));
  }

  protected startPan(event: MouseEvent): void {
    // Only pan on primary button
    if (event.button !== 0) {
      return;
    }
    this.isDragging.set(true);
    this.dragStartX = event.clientX;
    this.dragStartY = event.clientY;
    this.initialPanX = this.panX();
    this.initialPanY = this.panY();
  }

  protected onPan(event: MouseEvent): void {
    if (!this.isDragging()) {
      return;
    }
    const dx = event.clientX - this.dragStartX;
    const dy = event.clientY - this.dragStartY;
    this.panX.set(this.initialPanX + dx);
    this.panY.set(this.initialPanY + dy);
  }

  protected endPan(): void {
    this.isDragging.set(false);
  }

  protected handleKeydown(event: KeyboardEvent): void {
    const viewport = this.viewportEl()?.nativeElement;
    const target = event.target;
    if (
      this.viewMode() !== 'river' ||
      !viewport ||
      !(target instanceof Element) ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey
    )
      return;
    const focusedNode = target.closest<SVGElement>('.node[data-node-id]');
    // Toolbar and structured-list keys must retain their native behavior.
    if (target !== viewport && !focusedNode) return;
    const g = this.graph();
    const selectedId = focusedNode?.getAttribute('data-node-id') ?? this.selectedNodeId();
    if (!g || g.nodes.length === 0) {
      return;
    }

    let next: DagNodePresentation | undefined;
    if (!selectedId) {
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
        next = g.nodes[0];
      }
    } else {
      const current = g.nodeMap.get(selectedId);
      if (!current) return;
      if (event.key === 'ArrowRight') {
        next = g.nodeMap.get(current.downstreamNodeIds[0]);
      } else if (event.key === 'ArrowLeft') {
        next = g.nodeMap.get(current.upstreamNodeIds[0]);
      } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        const siblings = g.nodes
          .filter((n) => Math.abs(n.column - current.column) <= 0.5 && n.id !== current.id)
          .sort((a, b) => a.lane - b.lane);
        next =
          event.key === 'ArrowDown'
            ? siblings.find((n) => n.lane > current.lane)
            : [...siblings].reverse().find((n) => n.lane < current.lane);
      }
    }
    if (!next) return;
    this.nodeSelect.emit(next);
    Array.from(viewport.querySelectorAll<SVGElement>('.node[data-node-id]'))
      .find((node) => node.getAttribute('data-node-id') === next.id)
      ?.focus({ preventScroll: true });
    this.focusSelected(next.id);
    event.preventDefault();
  }
}
