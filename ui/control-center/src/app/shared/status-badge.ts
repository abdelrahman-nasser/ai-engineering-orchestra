import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Tone } from '../data/models';

/** Compact pill showing a status label in one of the shared tones. */
@Component({
  selector: 'cc-status-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[attr.data-tone]': 'tone()',
    '[class.pulse]': 'pulse()',
    role: 'status',
  },
  styles: `
    :host {
      --tone: var(--muted);
      --tone-soft: var(--muted-soft);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px 2px 8px;
      font-size: 12px;
      font-weight: 600;
      line-height: 1.6;
      white-space: nowrap;
      color: var(--tone);
      background: var(--tone-soft);
      border: 1px solid color-mix(in srgb, var(--tone) 28%, transparent);
      border-radius: 999px;
      transition: background-color 0.15s var(--ease), color 0.15s var(--ease);
    }
    :host::before {
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--tone);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--tone) 20%, transparent);
      flex: none;
    }
    :host([data-tone='info']) {
      --tone: var(--info);
      --tone-soft: var(--info-soft);
    }
    :host([data-tone='success']) {
      --tone: var(--success);
      --tone-soft: var(--success-soft);
    }
    :host([data-tone='warning']) {
      --tone: var(--warning);
      --tone-soft: var(--warning-soft);
    }
    :host([data-tone='danger']) {
      --tone: var(--danger);
      --tone-soft: var(--danger-soft);
    }
    :host([data-tone='accent']) {
      --tone: var(--accent);
      --tone-soft: var(--accent-soft);
    }
    :host([data-tone='neutral']) {
      --tone: var(--text-muted);
      --tone-soft: var(--surface-2);
    }

    :host(.pulse)::before {
      animation: badge-pulse 2s infinite ease-out;
    }
    @keyframes badge-pulse {
      0% {
        box-shadow: 0 0 0 0 color-mix(in srgb, var(--tone) 60%, transparent);
      }
      70% {
        box-shadow: 0 0 0 6px transparent;
      }
      100% {
        box-shadow: 0 0 0 0 transparent;
      }
    }

    @media (forced-colors: active) {
      :host {
        border: 1px solid ButtonText;
      }
      :host::before {
        background: ButtonText;
      }
    }
  `,
  template: `{{ label() }}`,
})
export class StatusBadge {
  readonly label = input.required<string>();
  readonly tone = input<Tone>('muted');
  readonly pulse = input<boolean>(false);
}
