import { describe, expect, it } from 'vitest';
import { AgentExecutionResultReadModel } from './models';
import { adaptResultReadModel } from './result-adapter';

describe('adaptResultReadModel', () => {
  const baseIdentity = {
    ledgerInstanceId: 'ledg_inst_482a9f10',
    authorizationDomainId: 'auth_dom_orchestra_core',
    issuerKind: 'human',
    issuerId: 'maya',
    grantId: 'grnt_123',
  };

  const baseEntry = {
    claimId: 'clm_456',
    executorInstanceId: 'exec_node_01',
    leaseGeneration: 1,
    entryTimeLabel: 'Today · 12:00',
    timeKey: 1728900000,
  };

  const baseTool = {
    toolIdentity: 'tool::itru-native-repository-file-read::v1',
    configuredRoute: 'native::posix_read_direct',
  };

  it('returns null when input read model is null or undefined', () => {
    expect(adaptResultReadModel(null)).toBeNull();
    expect(adaptResultReadModel(undefined)).toBeNull();
  });

  it('adapts a succeeded text outcome with bounded preview', () => {
    const model: AgentExecutionResultReadModel = {
      derivedIdentity: baseIdentity,
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: baseEntry,
      toolBinding: baseTool,
      outcome: 'succeeded',
      payload: {
        byteCount: 842,
        isText: true,
        isTruncated: false,
        previewByteCount: 842,
        textPreview: '# Sample Content',
      },
      diagnostic: null,
    };

    const res = adaptResultReadModel(model)!;
    expect(res).not.toBeNull();
    expect(res.outcome).toBe('succeeded');
    expect(res.outcomeLabel).toBe('Succeeded');
    expect(res.outcomeTone).toBe('success');
    expect(res.semanticEffect.headline).toBe('Operation completed successfully');
    expect(res.semanticEffect.retryNotice).toBeUndefined();

    expect(res.identity.derivedIdentityFormatted).toBe(
      '(ledg_inst_482a9f10, auth_dom_orchestra_core, human, maya, grnt_123)',
    );
    expect(res.identity.issuer).toBe('human:maya');
    expect(res.identity.claimId).toBe('clm_456');

    expect(res.payload).not.toBeNull();
    expect(res.payload?.byteCount).toBe(842);
    expect(res.payload?.formattedByteCount).toBe('842 bytes');
    expect(res.payload?.isText).toBe(true);
    expect(res.payload?.textPreview).toBe('# Sample Content');
    expect(res.payload?.isTruncated).toBe(false);
    expect(res.payload?.truncationNotice).toBeUndefined();

    // Diagnostic must remain null on success (ITRU-060 invariant)
    expect(res.diagnostic).toBeNull();
  });

  it('adapts a succeeded truncated payload with a truncation notice', () => {
    const model: AgentExecutionResultReadModel = {
      derivedIdentity: baseIdentity,
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: baseEntry,
      toolBinding: baseTool,
      outcome: 'succeeded',
      payload: {
        byteCount: 32768,
        isText: true,
        isTruncated: true,
        previewByteCount: 1024,
        textPreview: 'First 1024 bytes...',
      },
      diagnostic: null,
    };

    const res = adaptResultReadModel(model)!;
    expect(res.payload?.isTruncated).toBe(true);
    expect(res.payload?.truncationNotice).toBe('Showing first 1,024 of 32,768 bytes (bounded preview).');
  });

  it('adapts a succeeded binary payload without text preview', () => {
    const model: AgentExecutionResultReadModel = {
      derivedIdentity: baseIdentity,
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: baseEntry,
      toolBinding: baseTool,
      outcome: 'succeeded',
      payload: {
        byteCount: 4096,
        isText: false,
        isTruncated: false,
        previewByteCount: 4096,
        bytesSampleHex: '00000000 7f 45 4c 46',
      },
      diagnostic: null,
    };

    const res = adaptResultReadModel(model)!;
    expect(res.payload?.isText).toBe(false);
    expect(res.payload?.bytesSampleHex).toBe('00000000 7f 45 4c 46');
  });

  it('adapts a failed_before_effect outcome with no payload and canonical diagnostic', () => {
    const model: AgentExecutionResultReadModel = {
      derivedIdentity: baseIdentity,
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: baseEntry,
      toolBinding: baseTool,
      outcome: 'failed_before_effect',
      payload: null,
      diagnostic: {
        code: 'containment_rejected',
      },
    };

    const res = adaptResultReadModel(model)!;
    expect(res.outcome).toBe('failed_before_effect');
    expect(res.outcomeLabel).toBe('Failed Before Effect');
    expect(res.outcomeTone).toBe('neutral');
    expect(res.semanticEffect.description).toContain('proves that no content-data read request began');
    expect(res.semanticEffect.retryNotice).toContain('permanently consumed');

    // Payload must be absent on failure
    expect(res.payload).toBeNull();

    // Diagnostic populated with closed canonical explanation
    expect(res.diagnostic).not.toBeNull();
    expect(res.diagnostic?.code).toBe('containment_rejected');
    expect(res.diagnostic?.title).toBe('Containment Rejected');
    expect(res.diagnostic?.explanation).toContain('containment');
  });

  it('adapts an effect_ambiguous outcome with critical retry prohibition and no payload', () => {
    const model: AgentExecutionResultReadModel = {
      derivedIdentity: baseIdentity,
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: baseEntry,
      toolBinding: baseTool,
      outcome: 'effect_ambiguous',
      payload: null,
      diagnostic: {
        code: 'effect_ambiguous',
      },
    };

    const res = adaptResultReadModel(model)!;
    expect(res.outcome).toBe('effect_ambiguous');
    expect(res.outcomeLabel).toBe('Effect Ambiguous');
    expect(res.outcomeTone).toBe('warning');
    expect(res.semanticEffect.headline).toBe('Uncertain effect boundary');
    expect(res.semanticEffect.retryNotice).toContain('Do NOT automatically retry or replay');

    // No payload allowed on ambiguity
    expect(res.payload).toBeNull();
    expect(res.diagnostic?.code).toBe('effect_ambiguous');
  });
});
