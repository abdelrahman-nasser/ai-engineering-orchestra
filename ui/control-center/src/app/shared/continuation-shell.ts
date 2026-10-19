import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { AgentExecutionResultOutcome, RunContinuationPresentation } from '../data/models';
import { Icon } from './icon';
import { StatePanel } from './state-panel';
import { StatusBadge } from './status-badge';

/**
 * Continuation & Resume UX shell for presenting future resume/recovery affordances.
 *
 * STRICT BOUNDARY:
 * - This component defines NO resume semantics, checkpoint IDs, recovery rules, or replay behavior.
 * - All eligibility and metadata are strictly supplied by the UI-local read model.
 * - Actions are presentation-only / disabled demo behaviors (no fake backend mutations).
 * - Enforces strict prohibition of retry/continuation when Result outcome is `effect_ambiguous`.
 * - Never claims Journal presence proves resume safety.
 */
@Component({
  selector: 'cc-continuation-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, StatePanel, StatusBadge],
  styleUrl: './continuation-shell.css',
  template: `
    <section class="continuation-container" role="region" [attr.aria-label]="regionLabel()">
      <div class="disclaimer-banner" role="note">
        <cc-icon name="info" />
        <span>Mock continuation metadata only · No operational resume controls are connected.</span>
      </div>

      @if (loading()) {
        <cc-state-panel kind="loading" message="Loading continuation metadata..." />
      } @else if (error()) {
        <cc-state-panel kind="error" title="Could not load continuation metadata" [message]="error()!" />
      } @else if (effectiveContinuation(); as c) {
        <div class="continuation-card" [attr.data-status]="c.status" [attr.data-testid]="'continuation-card-' + c.status">
          <div class="card-header-row">
            <div class="status-group">
              <span class="status-caption">Continuation status</span>
              <cc-status-badge [label]="c.statusLabel" [tone]="c.statusTone" />
            </div>
            @if (c.lastKnownActivity) {
              <span class="muted nowrap text-xs">Last known: {{ c.lastKnownActivity }}</span>
            }
          </div>

          @if (isEffectAmbiguous()) {
            <div class="callout callout-danger" role="alert" data-testid="effect-ambiguous-continuation-alert">
              <strong>CRITICAL EFFECT UNCERTAINTY.</strong> Execution ended in an <code>effect_ambiguous</code> outcome. Core semantics strictly prohibit automated retry, replay, or continuation to prevent duplicated side effects.
            </div>
          }

          @if (c.isInterrupted && c.interruptionNotice) {
            <div class="callout callout-warning" role="note" data-testid="interruption-notice">
              <strong>Interruption notice:</strong> {{ c.interruptionNotice }}
            </div>
          }

          @if (c.isBlocked && c.blockedReason && !isEffectAmbiguous()) {
            <div class="callout callout-warning" role="note" data-testid="continuation-blocked-notice">
              <strong>Continuation blocked:</strong> {{ c.blockedReason }}
            </div>
          }

          @if (c.isStale && c.staleNotice) {
            <div class="callout callout-warning" role="note" data-testid="stale-notice">
              <strong>Stale observation:</strong> {{ c.staleNotice }}
            </div>
          }

          @if (c.isMissing) {
            <p class="muted-text" data-testid="missing-continuation-notice">
              No continuation metadata supplied by current data source.
            </p>
          } @else {
            <dl class="details-list" aria-label="Continuation details">
              @if (c.label) {
                <dt>Proposed action</dt>
                <dd><strong>{{ c.label }}</strong></dd>
              }
              @if (c.reason) {
                <dt>Context / reason</dt>
                <dd>{{ c.reason }}</dd>
              }
              @if (c.lastKnownActivity) {
                <dt>Last activity</dt>
                <dd>{{ c.lastKnownActivity }}</dd>
              }
            </dl>
          }

          <div class="action-row">
            @if (c.isAvailable && !isEffectAmbiguous()) {
              <button
                type="button"
                class="btn btn-primary"
                [disabled]="true"
                [attr.aria-disabled]="true"
                [title]="c.actionDisabledReason ?? 'Presentation demo only'"
                data-testid="continuation-resume-button"
              >
                <cc-icon name="play" />
                {{ c.label || 'Resume Run' }}
              </button>
            }
            <span class="action-note">
              {{ c.actionDisabledReason || 'Read-only presentation affordance · No Core resume mutation exists in v0.1.x Foundation' }}
            </span>
          </div>

          <div class="safety-note muted">
            Notice: Display of Journal entries or evidence does not prove continuation safety. This mock view establishes no continuation eligibility.
          </div>
        </div>
      }
    </section>
  `,
})
export class ContinuationShell {
  readonly continuation = input<RunContinuationPresentation | null | undefined>();
  readonly runId = input<string | undefined>();
  readonly resultOutcome = input<AgentExecutionResultOutcome | undefined>();
  readonly loading = input<boolean>(false);
  readonly error = input<string | null>(null);

  protected readonly isEffectAmbiguous = computed(() => {
    return this.resultOutcome() === 'effect_ambiguous';
  });

  protected readonly effectiveContinuation = computed(() => {
    const raw = this.continuation();
    if (!raw) {
      return {
        status: 'missing' as const,
        statusLabel: 'No continuation info',
        statusTone: 'muted' as const,
        isAvailable: false,
        isBlocked: false,
        isInterrupted: false,
        isCompleted: false,
        isStale: false,
        isMissing: true,
        label: undefined,
        reason: 'No continuation metadata supplied by current data source.',
        blockedReason: undefined,
        lastKnownActivity: undefined,
        interruptionNotice: undefined,
        staleNotice: undefined,
        disclaimer: 'Continuation availability supplied by current data source.',
        actionDisabled: true,
        actionDisabledReason: 'No continuation metadata supplied by current data source.',
      };
    }
    return raw;
  });

  protected readonly regionLabel = computed(() => {
    const id = this.runId();
    return id ? `Continuation and recovery for run ${id}` : 'Continuation and recovery';
  });
}
