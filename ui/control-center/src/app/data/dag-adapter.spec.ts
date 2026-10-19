import { describe, expect, it } from 'vitest';
import {
  adaptDagEdgeReadModel,
  adaptDagGraphReadModel,
  adaptDagNodeReadModel,
  DEPENDENCY_DISCLAIMER_NOTICE,
  EFFECT_AMBIGUOUS_DAG_WARNING,
  SCHEDULER_DISCLAIMER_NOTICE,
  SCHEDULER_STATE_CONFIG,
} from './dag-adapter';
import { DagEdgeReadModel, DagGraphReadModel, DagNodeReadModel } from './models';

describe('dag-adapter', () => {
  it('exposes mandatory presentation disclaimers', () => {
    expect(SCHEDULER_DISCLAIMER_NOTICE).toContain('No operational Core scheduler is connected');
    expect(DEPENDENCY_DISCLAIMER_NOTICE).toContain('establish no Core readiness or dispatch eligibility');
    expect(EFFECT_AMBIGUOUS_DAG_WARNING).toContain('Automatic retry or replay is strictly prohibited');
  });

  it('maps scheduler states to correct presentation tones and labels', () => {
    expect(SCHEDULER_STATE_CONFIG['queued']).toEqual({
      label: 'Queued',
      tone: 'muted',
      presentationState: 'not-started',
    });
    expect(SCHEDULER_STATE_CONFIG['ready-looking']).toEqual({
      label: 'Ready (looking)',
      tone: 'info',
      presentationState: 'not-started',
    });
    expect(SCHEDULER_STATE_CONFIG['active-looking']).toEqual({
      label: 'Active (looking)',
      tone: 'info',
      presentationState: 'in-progress',
    });
    expect(SCHEDULER_STATE_CONFIG['blocked-looking']).toEqual({
      label: 'Blocked (looking)',
      tone: 'warning',
      presentationState: 'needs-attention',
    });
    expect(SCHEDULER_STATE_CONFIG['completed-looking']).toEqual({
      label: 'Completed (looking)',
      tone: 'success',
      presentationState: 'finished',
    });
    expect(SCHEDULER_STATE_CONFIG['attention']).toEqual({
      label: 'Needs Attention',
      tone: 'danger',
      presentationState: 'needs-attention',
    });
  });

  it('adapts a standard DAG node read model', () => {
    const raw: DagNodeReadModel = {
      id: 'node-stage-impl',
      label: 'Implement changes',
      sublabel: 'Agent Alpha',
      kind: 'stage',
      column: 1,
      lane: 0,
      taskId: 'DEMO-101',
      runId: 'run_impl_01',
      roleId: 'software-engineer',
      actorId: 'agent-alpha',
      stageId: 'implement',
      workflowId: 'standard-change',
      toolId: 'tool-editor',
      isMainFlow: true,
      schedulerState: 'active-looking',
      upstreamNodeIds: ['node-stage-plan'],
      downstreamNodeIds: ['node-stage-test'],
      blockedByNodeIds: [],
      hasResult: false,
      hasJournal: true,
      hasEvidence: true,
      evidenceCount: 3,
    };

    const adapted = adaptDagNodeReadModel(raw);
    expect(adapted.id).toBe('node-stage-impl');
    expect(adapted.schedulerState).toBe('active-looking');
    expect(adapted.schedulerStateLabel).toBe('Active (looking)');
    expect(adapted.schedulerTone).toBe('info');
    expect(adapted.presentationState).toBe('in-progress');
    expect(adapted.isEffectAmbiguous).toBe(false);
    expect(adapted.upstreamNodeIds).toEqual(['node-stage-plan']);
    expect(adapted.downstreamNodeIds).toEqual(['node-stage-test']);
    expect(adapted.hasJournal).toBe(true);
    expect(adapted.hasEvidence).toBe(true);
    expect(adapted.evidenceCount).toBe(3);
  });

  it('adapts effect_ambiguous node with strict hazard tone and warning boundary', () => {
    const raw: DagNodeReadModel = {
      id: 'node-ambiguous',
      label: 'Ambiguous file write',
      kind: 'run',
      column: 2,
      lane: 1,
      schedulerState: 'completed-looking', // even if data source claimed completed-looking
      resultOutcome: 'effect_ambiguous',
      upstreamNodeIds: ['node-1'],
      downstreamNodeIds: [],
    };

    const adapted = adaptDagNodeReadModel(raw);
    expect(adapted.isEffectAmbiguous).toBe(true);
    expect(adapted.resultOutcome).toBe('effect_ambiguous');
    expect(adapted.schedulerTone).toBe('danger');
    expect(adapted.presentationState).toBe('needs-attention');
  });

  it('adapts edges correctly with weight and tributary flag', () => {
    const edge1: DagEdgeReadModel = {
      id: 'e1',
      from: 'node-1',
      to: 'node-2',
      isTributary: false,
    };
    const adapted1 = adaptDagEdgeReadModel(edge1);
    expect(adapted1.isTributary).toBe(false);
    expect(adapted1.weight).toBe('main');

    const edge2: DagEdgeReadModel = {
      id: 'e2',
      from: 'node-2',
      to: 'node-sub-1',
      isTributary: true,
      state: 'in-progress',
    };
    const adapted2 = adaptDagEdgeReadModel(edge2);
    expect(adapted2.isTributary).toBe(true);
    expect(adapted2.weight).toBe('tributary');
    expect(adapted2.state).toBe('in-progress');
  });

  it('adapts a complete graph read model and builds an index map', () => {
    const graph: DagGraphReadModel = {
      id: 'graph-linear',
      name: 'Linear Pipeline',
      scenario: 'linear',
      description: 'A simple linear multi-stage workflow',
      updatedLabel: 'Just now',
      isStale: false,
      nodes: [
        {
          id: 'n1',
          label: 'Plan',
          kind: 'stage',
          column: 0,
          lane: 0,
          schedulerState: 'completed-looking',
          upstreamNodeIds: [],
          downstreamNodeIds: ['n2'],
        },
        {
          id: 'n2',
          label: 'Execute',
          kind: 'stage',
          column: 1,
          lane: 0,
          schedulerState: 'active-looking',
          upstreamNodeIds: ['n1'],
          downstreamNodeIds: [],
        },
      ],
      edges: [{ id: 'n1->n2', from: 'n1', to: 'n2' }],
      schedulerSummary: {
        queuedCount: 0,
        readyLookingCount: 0,
        activeLookingCount: 1,
        blockedLookingCount: 0,
        completedLookingCount: 1,
        attentionCount: 0,
        dataSourceNotice: SCHEDULER_DISCLAIMER_NOTICE,
      },
    };

    const adapted = adaptDagGraphReadModel(graph);
    expect(adapted).not.toBeNull();
    expect(adapted!.nodes.length).toBe(2);
    expect(adapted!.edges.length).toBe(1);
    expect(adapted!.nodeMap.get('n1')?.label).toBe('Plan');
    expect(adapted!.nodeMap.get('n2')?.label).toBe('Execute');
    expect(adapted!.isStale).toBe(false);
  });

  it('handles null / undefined graph gracefully', () => {
    expect(adaptDagGraphReadModel(undefined)).toBeNull();
  });
});
