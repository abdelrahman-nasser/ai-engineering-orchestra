import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Tone } from '../data/models';

/** Headline metric tile used on the Overview. */
@Component({
  selector: 'cc-stat-tile',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[attr.data-tone]': 'tone()',
    role: 'group',
    '[attr.aria-label]': 'ariaDescription()',
  },
  styles: `
    :host {
      --tone: var(--accent);
      position: relative;
      display: block;
      padding: var(--space-4) var(--space-5);
      overflow: hidden;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      transition:
        transform 0.2s var(--ease),
        border-color 0.2s var(--ease),
        box-shadow 0.2s var(--ease);
    }
    :host:hover {
      transform: translateY(-2px);
      border-color: var(--border-strong);
      box-shadow: var(--shadow-lg);
    }
    :host::after {
      content: '';
      position: absolute;
      inset: auto -30px -40px auto;
      width: 120px;
      height: 120px;
      border-radius: 50%;
      background: radial-gradient(circle, color-mix(in srgb, var(--tone) 28%, transparent), transparent 70%);
      pointer-events: none;
    }
    :host([data-tone='warning']) {
      --tone: var(--warning);
    }
    :host([data-tone='info']) {
      --tone: var(--info);
    }
    :host([data-tone='success']) {
      --tone: var(--success);
    }
    :host([data-tone='danger']) {
      --tone: var(--danger);
    }
    .value {
      font-family: var(--font-display);
      font-size: clamp(26px, 5vw, 34px);
      font-weight: 600;
      line-height: 1.1;
      margin-top: var(--space-2);
      color: var(--tone);
      letter-spacing: -0.02em;
    }
    .hint {
      margin-top: 4px;
      font-size: 12.5px;
      line-height: var(--leading-snug);
      color: var(--text-muted);
    }
  `,
  template: `
    <div class="eyebrow">{{ label() }}</div>
    <div class="value">{{ value() }}</div>
    @if (hint()) {
      <div class="hint">{{ hint() }}</div>
    }
  `,
})
export class StatTile {
  readonly label = input.required<string>();
  readonly value = input.required<string | number>();
  readonly hint = input<string>();
  readonly tone = input<Tone>('accent');

  protected readonly ariaDescription = computed(() => {
    const hintText = this.hint() ? ` (${this.hint()})` : '';
    return `${this.label()}: ${this.value()}${hintText}`;
  });
}
