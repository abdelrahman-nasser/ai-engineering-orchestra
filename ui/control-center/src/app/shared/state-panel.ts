import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Icon, IconName } from './icon';

export type StatePanelKind =
  | 'loading'
  | 'empty'
  | 'error'
  | 'not-found'
  | 'unavailable'
  | 'unknown'
  | 'blocked'
  | 'no-evidence';

const KIND_ICON: Readonly<Record<StatePanelKind, IconName>> = {
  loading: 'clock',
  empty: 'file',
  error: 'alert',
  'not-found': 'search',
  unavailable: 'slash',
  unknown: 'help',
  blocked: 'lock',
  'no-evidence': 'shield',
};

const DEFAULT_TITLES: Readonly<Record<StatePanelKind, string>> = {
  loading: 'Loading content…',
  empty: 'Nothing to show',
  error: 'Something went wrong',
  'not-found': 'Item not found',
  unavailable: 'Currently unavailable',
  unknown: 'No observation recorded',
  blocked: 'Execution blocked',
  'no-evidence': 'No evidence yet',
};

/**
 * Reusable presentation state panel.
 *
 * Provides standardized presentation for:
 * - loading
 * - empty
 * - error
 * - unavailable
 * - unknown (clarifying that lack of observation != failure)
 * - blocked (indicating prerequisite or human checkpoint)
 * - no-evidence (clarifying that absence of evidence != denial)
 * - not-found
 */
@Component({
  selector: 'cc-state-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  styles: `
    :host {
      display: block;
    }
    .panel {
      --panel-tone: var(--text-muted);
      --panel-border: var(--border-strong);
      --panel-bg: var(--surface);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--space-2);
      padding: var(--space-7) var(--space-5);
      text-align: center;
      color: var(--text-muted);
      background: var(--panel-bg);
      border: 1px dashed var(--panel-border);
      border-radius: var(--radius);
      transition: border-color 0.2s var(--ease);
    }
    .panel.compact {
      padding: var(--space-5) var(--space-4);
    }
    .panel-icon-wrap {
      display: grid;
      place-items: center;
      width: 48px;
      height: 48px;
      margin-bottom: var(--space-2);
      border-radius: 50%;
      background: color-mix(in srgb, var(--panel-tone) 12%, transparent);
      color: var(--panel-tone);
    }
    .panel.compact .panel-icon-wrap {
      width: 38px;
      height: 38px;
      margin-bottom: var(--space-1);
    }
    .panel h2 {
      font-size: 16px;
      color: var(--text);
    }
    .panel p {
      max-width: 55ch;
      font-size: 13.5px;
      line-height: var(--leading-normal);
      color: var(--text-muted);
    }
    .panel-actions {
      display: flex;
      gap: var(--space-3);
      align-items: center;
      margin-top: var(--space-3);
    }

    /* Kind-specific tones */
    .panel[data-kind='error'] {
      --panel-tone: var(--danger);
      --panel-border: color-mix(in srgb, var(--danger) 45%, transparent);
      --panel-bg: var(--danger-soft);
    }
    .panel[data-kind='blocked'] {
      --panel-tone: var(--warning);
      --panel-border: color-mix(in srgb, var(--warning) 45%, transparent);
      --panel-bg: var(--warning-soft);
    }
    .panel[data-kind='unavailable'] {
      --panel-tone: var(--danger);
      --panel-border: color-mix(in srgb, var(--danger) 35%, transparent);
    }
    .panel[data-kind='no-evidence'] {
      --panel-tone: var(--gold);
      --panel-border: color-mix(in srgb, var(--gold) 45%, transparent);
      --panel-bg: var(--gold-soft);
    }
    .panel[data-kind='unknown'] {
      --panel-tone: var(--muted);
      --panel-border: var(--border-strong);
    }
    .panel[data-kind='not-found'] {
      --panel-tone: var(--warning);
    }

    /* Loading skeleton bars */
    .bars {
      display: grid;
      gap: var(--space-3);
      padding: var(--space-4) 0;
    }
    .bars .skeleton {
      height: 18px;
    }
    .bars .skeleton:first-child {
      height: 28px;
      width: 40%;
    }
  `,
  template: `
    @switch (kind()) {
      @case ('loading') {
        <div class="bars" role="status" aria-live="polite" aria-busy="true" [attr.aria-label]="resolvedTitle()">
          <div class="skeleton"></div>
          <div class="skeleton"></div>
          <div class="skeleton" style="width: 80%"></div>
          <div class="skeleton" style="width: 60%"></div>
        </div>
      }
      @default {
        <div
          class="panel"
          [class.compact]="compact()"
          [attr.data-kind]="kind()"
          [attr.role]="kind() === 'error' ? 'alert' : null"
        >
          <div class="panel-icon-wrap" aria-hidden="true">
            <cc-icon [name]="resolvedIcon()" [size]="compact() ? 20 : 26" />
          </div>
          <h2>{{ resolvedTitle() }}</h2>
          @if (resolvedMessage(); as msg) {
            <p>{{ msg }}</p>
          }
          <div class="panel-actions">
            <ng-content />
          </div>
        </div>
      }
    }
  `,
})
export class StatePanel {
  readonly kind = input<StatePanelKind>('empty');
  readonly title = input<string>();
  readonly message = input<string>();
  readonly description = input<string>();
  readonly icon = input<IconName>();
  readonly compact = input<boolean>(false);

  protected readonly resolvedTitle = computed(() => this.title() ?? DEFAULT_TITLES[this.kind()]);
  protected readonly resolvedIcon = computed(() => this.icon() ?? KIND_ICON[this.kind()]);
  protected readonly resolvedMessage = computed(() => this.message() ?? this.description());
}
