import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { AgentExecutionResultPresentation } from '../data/models';
import { Icon } from './icon';
import { StatePanel } from './state-panel';
import { StatusBadge } from './status-badge';

/**
 * Result presentation shell aligned with canonical ITRU-060 semantics.
 *
 * It presents in-memory terminal evidence for an Agent Execution Run:
 * - 3 exact terminal outcomes: `succeeded`, `failed_before_effect`, `effect_ambiguous`
 * - Bounded payload preview for success (text vs binary, truncation indicator)
 * - Diagnostics report with canonical ITRU-060 codes and explanations
 * - Derived 5-part Result identity and execution entry provenance
 * - Explicit effect-boundary uncertainty warning and retry prohibition
 * - Transport and persistence disclaimer
 */
@Component({
  selector: 'cc-result-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatePanel, StatusBadge],
  styles: `
    :host {
      display: block;
    }

    .disclaimer-banner {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
      margin-bottom: var(--space-4);
      padding: 5px 12px;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-soft);
      border: 1px dashed color-mix(in srgb, var(--gold) 45%, transparent);
      border-radius: var(--radius-full);
      width: fit-content;
      max-width: 100%;
    }

    .result-container {
      display: flex;
      flex-direction: column;
      gap: var(--space-4);
    }

    /* Outcome card */
    .outcome-card {
      padding: var(--space-4);
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      transition: border-color 0.2s ease, background 0.2s ease;
    }

    .outcome-card[data-outcome='succeeded'] {
      border-color: color-mix(in srgb, var(--success) 35%, transparent);
      background: linear-gradient(135deg, var(--surface-2) 0%, color-mix(in srgb, var(--success) 5%, var(--surface-2)) 100%);
    }

    .outcome-card[data-outcome='failed_before_effect'] {
      border-color: color-mix(in srgb, var(--border-strong) 60%, transparent);
      background: var(--surface-2);
    }

    .outcome-card[data-outcome='effect_ambiguous'] {
      border-color: color-mix(in srgb, var(--warning) 60%, transparent);
      background: linear-gradient(135deg, var(--surface-2) 0%, color-mix(in srgb, var(--warning) 9%, var(--surface-2)) 100%);
    }

    .outcome-header {
      display: flex;
      flex-direction: column;
      gap: var(--space-2);
    }

    .outcome-badge-row {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      flex-wrap: wrap;
    }

    .outcome-kind-chip {
      font-size: 11px;
      padding: 2px 8px;
      background: var(--surface-3);
      border: 1px solid var(--border);
      border-radius: var(--radius-xs);
      color: var(--text-muted);
    }

    .outcome-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
      line-height: var(--leading-snug);
      margin: 0;
    }

    .outcome-desc {
      font-size: 13px;
      color: var(--text-muted);
      line-height: var(--leading-normal);
      margin: 0;
    }

    /* Retry / Effect Boundary Warnings */
    .retry-box {
      display: flex;
      align-items: flex-start;
      gap: var(--space-3);
      margin-top: var(--space-3);
      padding: var(--space-3) var(--space-4);
      background: var(--surface-3);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 12.5px;
      line-height: 1.5;
    }

    .retry-box.retry-ambiguous {
      background: var(--warning-soft);
      border-color: color-mix(in srgb, var(--warning) 50%, transparent);
      color: var(--text);
    }

    .retry-box cc-icon {
      flex-shrink: 0;
      margin-top: 2px;
    }

    .retry-box.retry-ambiguous cc-icon {
      color: var(--warning);
    }

    .retry-text strong {
      display: block;
      margin-bottom: 2px;
      font-weight: 600;
    }

    .retry-text p {
      margin: 0;
      color: var(--text-muted);
    }

    .retry-box.retry-ambiguous .retry-text p {
      color: var(--text);
    }

    /* Generic section */
    .result-section {
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow: hidden;
    }

    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-2);
      padding: var(--space-3) var(--space-4);
      background: color-mix(in srgb, var(--surface-3) 50%, var(--surface-2));
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
    }

    .head-left {
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .section-title {
      font-size: 13.5px;
      font-weight: 600;
      margin: 0;
      color: var(--text);
    }

    .head-chips {
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .chip {
      font-size: 11px;
      padding: 2px 7px;
      background: var(--surface-3);
      border: 1px solid var(--border);
      border-radius: var(--radius-xs);
      color: var(--text-muted);
    }

    .chip-accent {
      background: var(--accent-soft);
      border-color: color-mix(in srgb, var(--accent) 40%, transparent);
      color: var(--accent);
    }

    /* Truncation warning */
    .truncation-banner {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      padding: 8px var(--space-4);
      background: var(--gold-soft);
      border-bottom: 1px solid color-mix(in srgb, var(--gold) 30%, transparent);
      font-size: 12px;
      color: var(--gold);
      font-weight: 500;
    }

    /* Payload text preview */
    .code-preview-frame {
      padding: var(--space-3) var(--space-4);
      background: var(--bg);
      overflow: auto;
      max-height: 280px;
    }

    .code-preview {
      margin: 0;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      color: var(--text);
      white-space: pre;
    }

    /* Binary preview */
    .binary-preview-box {
      padding: var(--space-3) var(--space-4);
      background: var(--bg);
    }

    .binary-note {
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: var(--space-2);
    }

    .binary-dump {
      margin: 0;
      font-family: var(--font-mono);
      font-size: 11.5px;
      line-height: 1.5;
      color: var(--text-muted);
      white-space: pre;
      overflow-x: auto;
    }

    /* Diagnostic presentation */
    .diagnostic-body {
      padding: var(--space-4);
    }

    .diagnostic-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: var(--space-1);
    }

    .diagnostic-explanation {
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      margin: 0 0 var(--space-3);
    }

    .diagnostic-boundary-note {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      padding: 8px 12px;
      background: var(--surface-3);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 11.5px;
      color: var(--text-muted);
    }

    /* Identity and provenance accordion */
    .identity-details {
      border: none;
    }

    .identity-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-3);
      padding: var(--space-3) var(--space-4);
      background: color-mix(in srgb, var(--surface-3) 50%, var(--surface-2));
      cursor: pointer;
      user-select: none;
      list-style: none;
      flex-wrap: wrap;
    }

    .identity-summary::-webkit-details-marker {
      display: none;
    }

    .summary-left {
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .tuple-preview {
      font-size: 11px;
      color: var(--text-muted);
      max-width: 380px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .identity-content {
      padding: var(--space-4);
      border-top: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: var(--space-3);
    }

    .tuple-box {
      padding: var(--space-3);
      background: var(--surface-3);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
    }

    .eyebrow {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: var(--space-1);
    }

    .tuple-full {
      font-size: 11.5px;
      word-break: break-all;
      color: var(--text);
    }

    .kv-grid {
      display: grid;
      grid-template-columns: 140px minmax(0, 1fr);
      gap: var(--space-2) var(--space-3);
      margin: 0;
      font-size: 12px;
    }

    .kv-grid dt {
      color: var(--text-muted);
      font-weight: 500;
    }

    .kv-grid dd {
      margin: 0;
      color: var(--text);
      word-break: break-word;
    }

    @media (max-width: 640px) {
      .kv-grid {
        grid-template-columns: minmax(0, 1fr);
        gap: var(--space-1);
      }
      .kv-grid dd {
        margin-bottom: var(--space-2);
      }
      .tuple-preview {
        max-width: 100%;
      }
    }
  `,
  template: `
    <div class="disclaimer-banner" role="note">
      <cc-icon name="shield" [size]="14" />
      <span>Canonical ITRU-060 in-memory evidence · Transport & persistence uninvented</span>
    </div>

    @if (result(); as r) {
      <div class="result-container">
        <!-- Outcome Status & Semantic Effect -->
        <section class="outcome-card" [attr.data-outcome]="r.outcome" aria-labelledby="outcome-heading">
          <div class="outcome-header">
            <div class="outcome-badge-row">
              <cc-status-badge [label]="r.outcomeLabel" [tone]="r.outcomeTone" />
              <span class="outcome-kind-chip mono">{{ r.outcome }}</span>
            </div>
            <h3 id="outcome-heading" class="outcome-title">{{ r.semanticEffect.headline }}</h3>
            <p class="outcome-desc">{{ r.semanticEffect.description }}</p>
          </div>

          @if (r.semanticEffect.retryNotice; as retry) {
            <div
              class="retry-box"
              [class.retry-ambiguous]="r.outcome === 'effect_ambiguous'"
              role="alert"
            >
              <cc-icon [name]="r.outcome === 'effect_ambiguous' ? 'alert' : 'cross-circle'" [size]="16" />
              <div class="retry-text">
                <strong>{{ r.outcome === 'effect_ambiguous' ? 'Critical effect boundary warning' : 'Permanent Entry Consumption' }}</strong>
                <p>{{ retry }}</p>
              </div>
            </div>
          }
        </section>

        <!-- Bounded Payload UX (Success only) -->
        @if (r.payload; as p) {
          <section class="result-section payload-section" aria-labelledby="payload-heading">
            <div class="section-head">
              <div class="head-left">
                <cc-icon name="file" [size]="15" />
                <h4 id="payload-heading" class="section-title">Bounded content payload</h4>
              </div>
              <div class="head-chips">
                <span class="chip mono">{{ p.formattedByteCount }}</span>
                <span class="chip" [class.chip-accent]="p.isText">{{ p.isText ? 'UTF-8 text' : 'Raw binary' }}</span>
              </div>
            </div>

            @if (p.isTruncated && p.truncationNotice) {
              <div class="truncation-banner" role="status">
                <cc-icon name="alert" [size]="14" />
                <span>{{ p.truncationNotice }}</span>
              </div>
            }

            @if (p.isText && p.textPreview) {
              <div class="code-preview-frame">
                <pre class="code-preview"><code>{{ p.textPreview }}</code></pre>
              </div>
            } @else if (p.bytesSampleHex) {
              <div class="binary-preview-box">
                <div class="binary-note">
                  Raw binary payload: safe byte dump preview (no inferred text decoding).
                </div>
                <pre class="binary-dump"><code>{{ p.bytesSampleHex }}</code></pre>
              </div>
            }
          </section>
        }

        <!-- Diagnostic Presentation (Failures / Ambiguity) -->
        @if (r.diagnostic; as d) {
          <section class="result-section diagnostic-section" aria-labelledby="diagnostic-heading">
            <div class="section-head">
              <div class="head-left">
                <cc-icon name="cross-circle" [size]="15" />
                <h4 id="diagnostic-heading" class="section-title">Execution diagnostic</h4>
              </div>
              <span class="chip mono">{{ d.code }}</span>
            </div>
            <div class="diagnostic-body">
              <div class="diagnostic-title">{{ d.title }}</div>
              <p class="diagnostic-explanation">{{ d.explanation }}</p>
              <div class="diagnostic-boundary-note">
                <cc-icon name="shield" [size]="13" />
                <span>ITRU-060 boundary: No success content was captured or disclosed for this failure disposition.</span>
              </div>
            </div>
          </section>
        }

        <!-- Identity & Provenance Accordion -->
        <section class="result-section identity-section" aria-labelledby="identity-heading">
          <details class="identity-details" [open]="r.outcome !== 'succeeded'">
            <summary class="identity-summary">
              <div class="summary-left">
                <cc-icon name="branch" [size]="15" />
                <span id="identity-heading" class="section-title">Evidence provenance & identity</span>
              </div>
              <span class="mono tuple-preview" [title]="r.identity.derivedIdentityFormatted">{{ r.identity.derivedIdentityFormatted }}</span>
            </summary>
            <div class="identity-content">
              <div class="tuple-box">
                <div class="eyebrow">Derived 5-part Result Identity (ledger, domain, issuer kind, issuer id, grant id)</div>
                <div class="mono tuple-full">{{ r.identity.derivedIdentityFormatted }}</div>
              </div>
              <dl class="kv-grid" aria-label="Result provenance metadata">
                <dt>Domain</dt><dd class="mono">{{ r.identity.domainId }}</dd>
                <dt>Ledger Instance</dt><dd class="mono">{{ r.identity.ledgerInstanceId }}</dd>
                <dt>Issuer</dt><dd class="mono">{{ r.identity.issuer }}</dd>
                <dt>Grant ID</dt><dd class="mono">{{ r.identity.grantId }}</dd>
                <dt>Claim ID</dt><dd class="mono">{{ r.identity.claimId }}</dd>
                <dt>Executor Instance</dt><dd class="mono">{{ r.identity.executorInstanceId }}</dd>
                <dt>Lease Generation</dt><dd class="mono">{{ r.identity.leaseGeneration }}</dd>
                <dt>Entry Time</dt><dd>{{ r.identity.entryTimeLabel }}</dd>
                <dt>Tool Identity</dt><dd class="mono">{{ r.identity.toolIdentity }}</dd>
                <dt>Configured Route</dt><dd class="mono">{{ r.identity.configuredRoute }}</dd>
              </dl>
            </div>
          </details>
        </section>
      </div>
    } @else {
      <cc-state-panel
        kind="empty"
        [compact]="true"
        title="No Result published yet"
        message="No terminal Agent Execution Result has been published for this execution attempt. In ITRU-060, absence is missing evidence—never an implicit success or failure."
      />
    }
  `,
})
export class ResultShell {
  readonly result = input.required<AgentExecutionResultPresentation | null>();
}
