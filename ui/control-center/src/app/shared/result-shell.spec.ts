import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { AgentExecutionResultPresentation } from '../data/models';
import { adaptResultReadModel } from '../data/result-adapter';
import { ResultShell } from './result-shell';

@Component({
  imports: [ResultShell],
  template: `<cc-result-shell [result]="result()" />`,
})
class TestHost {
  readonly result = signal<AgentExecutionResultPresentation | null>(null);
}

describe('ResultShell', () => {
  async function createHost() {
    await TestBed.configureTestingModule({ imports: [TestHost] }).compileComponents();
    const fixture = TestBed.createComponent(TestHost);
    await fixture.whenStable();
    return { fixture, host: fixture.componentInstance, el: fixture.nativeElement as HTMLElement };
  }

  it('renders honest empty state when result is null', async () => {
    const { fixture, host, el } = await createHost();
    host.result.set(null);
    await fixture.whenStable();

    expect(el.querySelector('.disclaimer-banner')?.textContent).toContain('Canonical ITRU-060 in-memory evidence');
    expect(el.querySelector('cc-state-panel')?.textContent).toContain('No Result published yet');
    expect(el.querySelector('cc-state-panel')?.textContent).toContain('absence is missing evidence');
  });

  it('renders succeeded result with text preview and identity provenance', async () => {
    const { fixture, host, el } = await createHost();
    const presentation = adaptResultReadModel({
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
        claimId: 'clm_123',
        executorInstanceId: 'exec_node_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Thu · 14:00',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 512,
        isText: true,
        isTruncated: false,
        previewByteCount: 512,
        textPreview: 'export const config = { verified: true };',
      },
      diagnostic: null,
    });

    host.result.set(presentation);
    await fixture.whenStable();

    const outcomeCard = el.querySelector('.outcome-card');
    expect(outcomeCard?.getAttribute('data-outcome')).toBe('succeeded');
    expect(outcomeCard?.textContent).toContain('Succeeded');
    expect(outcomeCard?.textContent).toContain('Operation completed successfully');

    // Payload
    const payloadSec = el.querySelector('.payload-section');
    expect(payloadSec?.textContent).toContain('512 bytes');
    expect(payloadSec?.textContent).toContain('UTF-8 text');
    expect(payloadSec?.querySelector('.code-preview')?.textContent).toContain('export const config');

    // No diagnostic or truncation warning
    expect(el.querySelector('.diagnostic-section')).toBeNull();
    expect(el.querySelector('.truncation-banner')).toBeNull();

    // Identity
    expect(el.querySelector('.tuple-full')?.textContent).toBe(
      '(ledg_inst_482a9f10, auth_dom_orchestra_core, human, maya, grnt_001)',
    );
  });

  it('renders succeeded result with truncation banner when bounded', async () => {
    const { fixture, host, el } = await createHost();
    const presentation = adaptResultReadModel({
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'policy',
        issuerId: 'policy-test',
        grantId: 'grnt_002',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_123',
        executorInstanceId: 'exec_node_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Thu · 14:00',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 65536,
        isText: true,
        isTruncated: true,
        previewByteCount: 1024,
        textPreview: 'Line 1\nLine 2',
      },
      diagnostic: null,
    });

    host.result.set(presentation);
    await fixture.whenStable();

    const banner = el.querySelector('.truncation-banner');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Showing first 1,024 of 65,536 bytes (bounded preview).');
  });

  it('renders succeeded binary payload with byte dump and no corrupt text decoding', async () => {
    const { fixture, host, el } = await createHost();
    const presentation = adaptResultReadModel({
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_003',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_123',
        executorInstanceId: 'exec_node_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Thu · 14:00',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 2048,
        isText: false,
        isTruncated: false,
        previewByteCount: 2048,
        bytesSampleHex: '00000000 7f 45 4c 46 |.ELF|',
      },
      diagnostic: null,
    });

    host.result.set(presentation);
    await fixture.whenStable();

    const payloadSec = el.querySelector('.payload-section');
    expect(payloadSec?.textContent).toContain('Raw binary');
    expect(payloadSec?.querySelector('.binary-dump')?.textContent).toContain('00000000 7f 45 4c 46');
    expect(payloadSec?.querySelector('.code-preview')).toBeNull();
  });

  it('renders failed_before_effect with diagnostic code and permanent consumption note', async () => {
    const { fixture, host, el } = await createHost();
    const presentation = adaptResultReadModel({
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'policy',
        issuerId: 'policy-test',
        grantId: 'grnt_004',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_123',
        executorInstanceId: 'exec_node_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Thu · 14:00',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'failed_before_effect',
      payload: null,
      diagnostic: {
        code: 'resource_missing',
      },
    });

    host.result.set(presentation);
    await fixture.whenStable();

    const outcomeCard = el.querySelector('.outcome-card');
    expect(outcomeCard?.getAttribute('data-outcome')).toBe('failed_before_effect');
    expect(outcomeCard?.textContent).toContain('Failed Before Effect');
    expect(outcomeCard?.textContent).toContain('Terminated before content-data effect');
    expect(outcomeCard?.textContent).toContain('Execution Entry is permanently consumed');

    // Diagnostic
    const diag = el.querySelector('.diagnostic-section');
    expect(diag).not.toBeNull();
    expect(diag?.textContent).toContain('resource_missing');
    expect(diag?.textContent).toContain('Resource Missing');

    // No payload section
    expect(el.querySelector('.payload-section')).toBeNull();
  });

  it('renders effect_ambiguous with prominent warning banner and retry prohibition', async () => {
    const { fixture, host, el } = await createHost();
    const presentation = adaptResultReadModel({
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_005',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_123',
        executorInstanceId: 'exec_node_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Thu · 14:00',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'effect_ambiguous',
      payload: null,
      diagnostic: {
        code: 'effect_ambiguous',
      },
    });

    host.result.set(presentation);
    await fixture.whenStable();

    const outcomeCard = el.querySelector('.outcome-card');
    expect(outcomeCard?.getAttribute('data-outcome')).toBe('effect_ambiguous');
    expect(outcomeCard?.textContent).toContain('Effect Ambiguous');
    expect(outcomeCard?.textContent).toContain('Uncertain effect boundary');

    const retryBox = el.querySelector('.retry-box.retry-ambiguous');
    expect(retryBox).not.toBeNull();
    expect(retryBox?.textContent).toContain('Critical effect boundary warning');
    expect(retryBox?.textContent).toContain('Do NOT automatically retry or replay');

    // Diagnostic
    expect(el.querySelector('.diagnostic-section')?.textContent).toContain('effect_ambiguous');

    // No payload
    expect(el.querySelector('.payload-section')).toBeNull();
  });
});
