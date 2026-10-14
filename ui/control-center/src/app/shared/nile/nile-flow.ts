import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import {
  NileLabelSide,
  NileNode,
  NileNodeKind,
  NileTopology,
  PresentationState,
} from '../../data/models';
import { Icon } from '../icon';
import { PRESENTATION_STATE } from '../presentation';

/** Island radius per node kind (px, in SVG units). */
const RADIUS: Readonly<Record<NileNodeKind, number>> = {
  task: 11,
  stage: 13,
  run: 9,
  confluence: 15,
  outcome: 15,
};

const DEFAULT_LANE_HEIGHT = 66;
const SIDE_DEFAULT: Readonly<Record<NileNodeKind, NileLabelSide>> = {
  task: 'left',
  stage: 'below',
  run: 'above',
  confluence: 'right',
  outcome: 'right',
};

export interface PlacedNode {
  readonly node: NileNode;
  readonly x: number;
  readonly y: number;
  readonly r: number;
  readonly selectable: boolean;
  readonly aria: string;
  readonly label: string;
  readonly sublabel?: string;
  readonly anchor: 'start' | 'middle' | 'end';
  readonly labelX: number;
  readonly labelY: number;
  readonly subY: number;
  readonly attention: boolean;
}

export interface PlacedEdge {
  readonly id: string;
  readonly d: string;
  readonly weight: 'main' | 'tributary';
  readonly state: PresentationState | 'neutral';
}

export interface NileLayout {
  readonly width: number;
  readonly height: number;
  readonly nodes: readonly PlacedNode[];
  readonly edges: readonly PlacedEdge[];
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

/** Deterministic value in [-1, 1] derived from a string, for organic meander. */
function wobble(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) | 0;
  }
  return ((hash >>> 0) % 2000) / 1000 - 1;
}

/**
 * Nile / organic branch execution visualization.
 *
 * Renders a {@link NileTopology} as a river: a trunk that divides into
 * tributaries and rejoins. It is PRESENTATION ONLY. The flowing highlight is
 * decorative and uniform across channels; it encodes no progress, rate,
 * ordering, concurrency or scheduling. Island colour reflects only the
 * UI-local presentation state supplied with each node.
 */
@Component({
  selector: 'cc-nile-flow',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  templateUrl: './nile-flow.html',
  styleUrl: './nile-flow.css',
})
export class NileFlow {
  readonly topology = input.required<NileTopology>();
  readonly selectedId = input<string>();
  /** Horizontal distance between reaches (SVG units). */
  readonly columnWidth = input(170);
  /** Vertical distance between lanes (SVG units). Raise it for dense, label-heavy rivers. */
  readonly laneHeight = input(DEFAULT_LANE_HEIGHT);
  /** Node kinds that can be activated (click / Enter / Space). */
  readonly selectableKinds = input<readonly NileNodeKind[]>(['run', 'task']);
  readonly ariaLabel = input('Execution topology');

  readonly nodeSelect = output<NileNode>();

  protected readonly paused = signal(false);

  protected readonly layout = computed<NileLayout | null>(() => this.computeLayout());

  protected readonly legend = computed(() => {
    const present = new Set(this.topology().nodes.map((node) => node.state));
    return (Object.keys(PRESENTATION_STATE) as PresentationState[])
      .filter((state) => present.has(state))
      .map((state) => ({ state, label: PRESENTATION_STATE[state].label }));
  });

  protected choose(placed: PlacedNode): void {
    if (placed.selectable) {
      this.nodeSelect.emit(placed.node);
    }
  }

  private computeLayout(): NileLayout | null {
    const { nodes, edges } = this.topology();
    if (nodes.length === 0) {
      return null;
    }

    const colW = this.columnWidth();
    const laneH = this.laneHeight();
    const selectable = new Set(this.selectableKinds());
    const sideOf = (node: NileNode) => node.labelSide ?? SIDE_DEFAULT[node.kind];

    const minCol = Math.min(...nodes.map((node) => node.column));
    const maxCol = Math.max(...nodes.map((node) => node.column));
    const padL = nodes.some((node) => sideOf(node) === 'left') ? 210 : 60;
    const padR = nodes.some((node) => sideOf(node) === 'right') ? 160 : 60;

    // Vertical extents account for labels above/below the islands.
    const extent = (node: NileNode) => {
      const r = RADIUS[node.kind];
      const y = node.lane * laneH;
      const side = sideOf(node);
      return {
        top: y - r - (side === 'above' ? 42 : 12),
        bottom: y + r + (side === 'below' ? 42 : 12),
      };
    };
    const top = Math.min(...nodes.map((node) => extent(node).top));
    const bottom = Math.max(...nodes.map((node) => extent(node).bottom));
    const offsetY = -top + 14;

    const placed: PlacedNode[] = nodes.map((node) => {
      const r = RADIUS[node.kind];
      const side = sideOf(node);
      const state = PRESENTATION_STATE[node.state].label;
      const labelX = side === 'left' ? -(r + 14) : side === 'right' ? r + 14 : 0;
      let labelY = 0;
      let subY = 0;
      if (side === 'above') {
        labelY = -r - 24;
        subY = -r - 9;
      } else if (side === 'below') {
        labelY = r + 17;
        subY = r + 32;
      } else {
        labelY = -2;
        subY = 13;
      }
      return {
        node,
        x: padL + (node.column - minCol) * colW,
        y: node.lane * laneH + offsetY,
        r,
        selectable: selectable.has(node.kind),
        aria: `${node.kind} ${node.label}${node.sublabel ? `, ${node.sublabel}` : ''}: ${state}`,
        label: truncate(node.label, 20),
        sublabel: node.sublabel ? truncate(node.sublabel, 26) : undefined,
        anchor: side === 'left' ? 'end' : side === 'right' ? 'start' : 'middle',
        labelX,
        labelY,
        subY,
        attention: node.state === 'needs-attention' || node.state === 'in-progress',
      };
    });

    const byId = new Map(placed.map((item) => [item.node.id, item] as const));
    const placedEdges: PlacedEdge[] = [];
    for (const edge of edges) {
      const from = byId.get(edge.from);
      const to = byId.get(edge.to);
      if (!from || !to) {
        continue;
      }
      const x1 = from.x + from.r;
      const x2 = to.x - to.r;
      const dx = Math.max(x2 - x1, 12);
      const meander = wobble(`${edge.from}>${edge.to}`) * 9;
      const d = [
        `M ${x1} ${from.y}`,
        `C ${x1 + dx * 0.5} ${from.y + meander}`,
        `${x2 - dx * 0.5} ${to.y - meander}`,
        `${x2} ${to.y}`,
      ].join(' ');
      // A channel is only tinted by the Run it touches. Trunk stretches between
      // stages stay neutral so colour never suggests that flow is held up.
      const runEnd = from.node.kind === 'run' ? from.node : to.node.kind === 'run' ? to.node : undefined;
      placedEdges.push({
        id: `${edge.from}>${edge.to}`,
        d,
        weight: runEnd ? 'tributary' : 'main',
        state: runEnd?.state ?? 'neutral',
      });
    }

    return {
      width: padL + (maxCol - minCol) * colW + padR,
      height: bottom - top + 28,
      nodes: placed,
      edges: placedEdges,
    };
  }
}
