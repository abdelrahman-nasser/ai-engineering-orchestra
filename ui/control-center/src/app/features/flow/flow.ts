import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { map } from 'rxjs';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { adaptDagGraphReadModel } from '../../data/dag-adapter';
import { DagGraphPresentation, DagNodePresentation } from '../../data/models';
import { DagFlow } from '../../shared/nile/dag-flow';
import { DagNodeInspector } from '../../shared/nile/dag-node-inspector';
import { SchedulerPanel } from '../../shared/nile/scheduler-panel';
import { Icon } from '../../shared/icon';
import { toLoadStateFor } from '../../shared/load-state';
import { PageHeader } from '../../shared/page-header';
import { StatePanel } from '../../shared/state-panel';

@Component({
  selector: 'cc-flow',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, PageHeader, StatePanel, Icon, SchedulerPanel, DagFlow, DagNodeInspector],
  templateUrl: './flow.html',
  styleUrl: './flow.css',
})
export class Flow {
  /** Bound from query params (e.g. `/flow?scenario=blocked-branch`). */
  readonly scenario = input<string>();
  /** Bound from query params (e.g. `/flow?node=fo-sub-api`). */
  readonly node = input<string>();

  private readonly dataSource = inject(ControlCenterDataSource);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly dag = viewChild(DagFlow);

  protected readonly scenarios = toSignal(this.dataSource.listDagScenarios(), {
    initialValue: [],
  });

  // Query inputs are authoritative, including their removal on Back/Forward.
  protected readonly selectedScenarioId = computed(() => this.scenario() ?? 'fan-out-fan-in');
  protected readonly searchQuery = signal<string>('');
  protected readonly activeStateFilter = signal<string>('all');
  protected readonly featureFilter = signal<string>('all');
  protected readonly actorFilter = signal<string>('all');
  protected readonly viewMode = signal<'river' | 'list'>('river');
  private readonly graphState = toLoadStateFor(this.selectedScenarioId, (scenarioId) =>
    this.dataSource.getDagGraph(scenarioId).pipe(
      map((readModel) => ({
        scenarioId,
        graph: adaptDagGraphReadModel(readModel),
      })),
    ),
  );

  protected readonly state = computed(() => {
    const state = this.graphState();
    // The previous response must not be presented under a newly bound query.
    return state.status === 'ready' && state.data.scenarioId !== this.selectedScenarioId()
      ? { status: 'loading' as const }
      : state;
  });

  protected readonly graph = computed<DagGraphPresentation | null>(() => {
    const s = this.state();
    return s.status === 'ready' ? s.data.graph : null;
  });

  /** Distinct actors observed across current graph for filter dropdown. */
  protected readonly availableActors = computed<readonly string[]>(() => {
    const g = this.graph();
    if (!g) {
      return [];
    }

    const actors = new Set<string>();
    for (const node of g.nodes) {
      if (node.actorId) {
        actors.add(node.actorId);
      }
    }
    return Array.from(actors).sort();
  });

  /** Filtered graph presentation according to user toolbar selections. */
  protected readonly filteredGraph = computed<DagGraphPresentation | null>(() => {
    const original = this.graph();
    if (!original) {
      return null;
    }

    const query = this.searchQuery().trim().toLowerCase();
    const stateFilter = this.activeStateFilter();
    const featFilter = this.featureFilter();
    const actFilter = this.actorFilter();

    let filteredNodes = original.nodes;

    if (query) {
      filteredNodes = filteredNodes.filter(
        (n) =>
          n.label.toLowerCase().includes(query) ||
          n.id.toLowerCase().includes(query) ||
          (n.sublabel && n.sublabel.toLowerCase().includes(query)) ||
          (n.actorId && n.actorId.toLowerCase().includes(query)) ||
          (n.roleId && n.roleId.toLowerCase().includes(query)) ||
          (n.toolId && n.toolId.toLowerCase().includes(query)),
      );
    }

    if (stateFilter !== 'all') {
      filteredNodes = filteredNodes.filter((n) => n.schedulerState === stateFilter);
    }

    if (featFilter !== 'all') {
      if (featFilter === 'has-result') {
        filteredNodes = filteredNodes.filter((n) => n.hasResult);
      } else if (featFilter === 'has-evidence') {
        filteredNodes = filteredNodes.filter((n) => n.hasEvidence);
      } else if (featFilter === 'has-continuation') {
        filteredNodes = filteredNodes.filter((n) => n.hasContinuation);
      }
    }

    if (actFilter !== 'all') {
      filteredNodes = filteredNodes.filter((n) => n.actorId === actFilter);
    }

    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = original.edges.filter(
      (e) => visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to),
    );
    const nodeMap = new Map(filteredNodes.map((n) => [n.id, n]));

    return {
      ...original,
      nodes: filteredNodes,
      edges: filteredEdges,
      nodeMap,
    };
  });

  /** The currently selected node presentation object. */
  protected readonly selectedNode = computed<DagNodePresentation | null>(() => {
    const selectedId = this.node();
    const g = this.graph();
    if (!selectedId || !g) {
      return null;
    }
    return g.nodeMap.get(selectedId) ?? null;
  });
  protected readonly selectedNodeId = computed(() => this.selectedNode()?.id);

  protected changeScenario(scenarioId: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { scenario: scenarioId, node: null },
      queryParamsHandling: 'merge',
    });
  }

  protected onStateFilterChange(filterId: string): void {
    this.activeStateFilter.set(filterId);
  }

  protected onNodeSelect(node: DagNodePresentation): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { node: node.id },
      queryParamsHandling: 'merge',
    });
  }

  protected closeInspector(): void {
    // Restore a surviving control before query navigation removes Close.
    // The graph owns its river/list trigger; filtered-out nodes use search.
    if (!this.dag()?.restoreNodeFocus(this.selectedNodeId())) {
      const fallback =
        this.host.nativeElement.querySelector<HTMLElement>('.search-input') ??
        this.host.nativeElement.querySelector<HTMLElement>('#scenario-dropdown');
      fallback?.focus({ preventScroll: true });
    }
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { node: null },
      queryParamsHandling: 'merge',
    });
  }

  protected resetFilters(): void {
    this.searchQuery.set('');
    this.activeStateFilter.set('all');
    this.featureFilter.set('all');
    this.actorFilter.set('all');
  }
}
