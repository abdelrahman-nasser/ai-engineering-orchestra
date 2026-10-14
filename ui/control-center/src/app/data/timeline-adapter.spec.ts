import { describe, expect, it } from 'vitest';
import {
  adaptEvidenceReadModel,
  adaptEvidenceReadModels,
  adaptTimelineReadModel,
  adaptTimelineReadModels,
} from './timeline-adapter';
import { EvidenceItemReadModel, TimelineItemReadModel } from './models';

describe('timeline-adapter', () => {
  describe('adaptEvidenceReadModel', () => {
    it('adapts standard passed evidence item with outcome metadata and category label', () => {
      const readModel: EvidenceItemReadModel = {
        id: 'ev-1',
        category: 'quality-gate',
        title: 'unit-tests',
        summary: 'All 73 unit tests passed.',
        outcome: 'passed',
        source: 'python -B -m unittest discover',
        referenceId: 'ref_gate_001',
        lines: ['test_1 ... ok', 'test_2 ... ok'],
        recordedAtLabel: '14:02',
      };

      const result = adaptEvidenceReadModel(readModel);

      expect(result.id).toBe('ev-1');
      expect(result.category).toBe('quality-gate');
      expect(result.categoryLabel).toBe('Quality Gate');
      expect(result.kind).toBe('quality-gate');
      expect(result.outcome).toBe('passed');
      expect(result.outcomeLabel).toBe('Passed');
      expect(result.outcomeTone).toBe('success');
      expect(result.isTruncated).toBe(false);
      expect(result.isBinary).toBe(false);
      expect(result.isUnavailable).toBe(false);
      expect(result.referenceId).toBe('ref_gate_001');
      expect(result.integrityBadge).toBeUndefined();
    });

    it('formats truncation notice when evidence is bounded', () => {
      const readModel: EvidenceItemReadModel = {
        id: 'ev-2',
        category: 'command-output',
        title: 'system-scan',
        summary: 'Large output log',
        outcome: 'passed',
        source: 'scan.sh',
        byteCount: 34816,
        isTruncated: true,
        textPreview: 'Log header...',
      };

      const result = adaptEvidenceReadModel(readModel);

      expect(result.isTruncated).toBe(true);
      expect(result.formattedByteCount).toBe('34,816 bytes');
      expect(result.truncationNotice).toBe('Showing bounded preview of 34,816 bytes.');
    });

    it('identifies binary evidence and sample hex dump', () => {
      const readModel: EvidenceItemReadModel = {
        id: 'ev-3',
        category: 'payload-sample',
        title: 'binary-artifact',
        summary: 'ELF binary header sample',
        outcome: 'passed',
        source: 'posix_read',
        byteCount: 4096,
        binaryHexSample: '00000000  7f 45 4c 46 ...',
      };

      const result = adaptEvidenceReadModel(readModel);

      expect(result.isBinary).toBe(true);
      expect(result.binaryHexSample).toContain('7f 45 4c 46');
    });

    it('formats unavailable evidence state with custom or fallback reason', () => {
      const withCustom: EvidenceItemReadModel = {
        id: 'ev-4',
        category: 'audit-trail',
        title: 'audit-trace',
        summary: 'Trace collector output',
        outcome: 'unverified',
        source: 'audit-collector',
        isUnavailable: true,
        unavailableReason: 'Trace expired due to 24h retention window policy.',
      };

      const adaptedCustom = adaptEvidenceReadModel(withCustom);
      expect(adaptedCustom.isUnavailable).toBe(true);
      expect(adaptedCustom.unavailableReason).toBe('Trace expired due to 24h retention window policy.');

      const withFallback: EvidenceItemReadModel = {
        id: 'ev-5',
        category: 'diagnostic',
        title: 'telemetry',
        summary: 'Telemetry dump',
        outcome: 'failed',
        source: 'telemetry-daemon',
        isUnavailable: true,
      };

      const adaptedFallback = adaptEvidenceReadModel(withFallback);
      expect(adaptedFallback.isUnavailable).toBe(true);
      expect(adaptedFallback.unavailableReason).toBe(
        'Evidence record could not be resolved from current data source.',
      );
    });

    it('formats integrity badge when explicitly provided', () => {
      const verified: EvidenceItemReadModel = {
        id: 'ev-6',
        category: 'authorization',
        title: 'auth-proof',
        summary: 'Signature proof',
        outcome: 'passed',
        source: 'policy-engine',
        integrityStatus: 'verified',
      };

      expect(adaptEvidenceReadModel(verified).integrityBadge).toEqual({
        label: 'Integrity Verified',
        tone: 'success',
      });

      const mismatch: EvidenceItemReadModel = {
        id: 'ev-7',
        category: 'authorization',
        title: 'auth-proof',
        summary: 'Signature proof',
        outcome: 'failed',
        source: 'policy-engine',
        integrityStatus: 'mismatch',
      };

      expect(adaptEvidenceReadModel(mismatch).integrityBadge).toEqual({
        label: 'Digest Mismatch',
        tone: 'danger',
      });
    });

    it('handles empty evidence read model arrays', () => {
      expect(adaptEvidenceReadModels(undefined)).toEqual([]);
      expect(adaptEvidenceReadModels([])).toEqual([]);
    });
  });

  describe('adaptTimelineReadModel', () => {
    it('adapts a basic timeline entry with presentation state metadata', () => {
      const readModel: TimelineItemReadModel = {
        id: 'tl-1',
        atLabel: 'Today · 14:02',
        kind: 'stage',
        title: 'Stage "implement" entered',
        detail: 'Work began under software-engineer role.',
        state: 'finished',
        actorId: 'agent-forge',
        stageId: 'implement',
      };

      const result = adaptTimelineReadModel(readModel);

      expect(result.id).toBe('tl-1');
      expect(result.atLabel).toBe('Today · 14:02');
      expect(result.stateLabel).toBe('Finished');
      expect(result.stateTone).toBe('success');
      expect(result.hasResult).toBe(false);
      expect(result.result).toBeNull();
      expect(result.hasEvidence).toBe(false);
      expect(result.evidenceCount).toBe(0);
      expect(result.hasUnavailableEvidence).toBe(false);
    });

    it('adapts timeline entry with linked Result and associated evidence', () => {
      const readModel: TimelineItemReadModel = {
        id: 'tl-2',
        atLabel: 'Today · 14:05',
        kind: 'tool',
        title: 'Tool invocation completed',
        state: 'finished',
        toolId: 'tool::itru-native-repository-file-read::v1',
        executionEntryRef: 'clm_1b2c3d4e',
        runIdRef: 'run_3c81f0a7',
        result: {
          derivedIdentity: {
            ledgerInstanceId: 'ledg_inst_482a9f10',
            authorizationDomainId: 'auth_dom_orchestra_core',
            issuerKind: 'human',
            issuerId: 'maya',
            grantId: 'grnt_001',
          },
          ledgerIdentity: {
            domainId: 'auth_dom_orchestra_core',
            ledgerInstanceId: 'ledg_inst_482a9f10',
            domainGeneration: 1,
          },
          executionEntry: {
            claimId: 'clm_1b2c3d4e',
            executorInstanceId: 'exec_node_worker_01',
            leaseGeneration: 1,
            entryTimeLabel: 'Today · 14:05',
            timeKey: 1728984300,
          },
          toolBinding: {
            toolIdentity: 'tool::itru-native-repository-file-read::v1',
            configuredRoute: 'native::posix_read_direct',
          },
          outcome: 'succeeded',
          payload: {
            byteCount: 124,
            isText: true,
            isTruncated: false,
            previewByteCount: 124,
            textPreview: 'export const hello = "world";',
          },
          diagnostic: null,
        },
        evidence: [
          {
            id: 'ev-tool-1',
            category: 'diagnostic',
            title: 'containment_check',
            summary: 'Passed path check',
            outcome: 'passed',
            source: 'containment_guard',
          },
          {
            id: 'ev-tool-2',
            category: 'audit-trail',
            title: 'audit_trace',
            summary: 'Trace collector',
            outcome: 'unverified',
            source: 'audit-daemon',
            isUnavailable: true,
          },
        ],
      };

      const result = adaptTimelineReadModel(readModel);

      expect(result.hasResult).toBe(true);
      expect(result.result).not.toBeNull();
      expect(result.result?.outcome).toBe('succeeded');
      expect(result.result?.payload?.textPreview).toBe('export const hello = "world";');
      expect(result.hasEvidence).toBe(true);
      expect(result.evidenceCount).toBe(2);
      expect(result.hasUnavailableEvidence).toBe(true);
      expect(result.toolId).toBe('tool::itru-native-repository-file-read::v1');
      expect(result.executionEntryRef).toBe('clm_1b2c3d4e');
      expect(result.runIdRef).toBe('run_3c81f0a7');
    });

    it('handles empty timeline read model arrays', () => {
      expect(adaptTimelineReadModels(undefined)).toEqual([]);
      expect(adaptTimelineReadModels([])).toEqual([]);
    });
  });
});
