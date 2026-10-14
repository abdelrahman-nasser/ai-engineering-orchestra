import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Icon } from './icon';

/** Shared loading / error / empty feedback so every screen handles states alike. */
@Component({
  selector: 'cc-state-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  styles: `
    :host {
      display: block;
    }
    .panel {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--space-2);
      padding: var(--space-7) var(--space-5);
      text-align: center;
      color: var(--text-muted);
      border: 1px dashed var(--border-strong);
      border-radius: var(--radius);
    }
    .panel h2 {
      font-size: 16px;
    }
    .bars {
      display: grid;
      gap: var(--space-3);
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
        <div class="bars" role="status" aria-live="polite" aria-label="Loading">
          <div class="skeleton"></div>
          <div class="skeleton"></div>
          <div class="skeleton" style="width: 80%"></div>
          <div class="skeleton" style="width: 60%"></div>
        </div>
      }
      @default {
        <div class="panel" [attr.role]="kind() === 'error' ? 'alert' : null">
          <cc-icon [name]="kind() === 'error' ? 'alert' : 'file'" [size]="28" />
          <h2>{{ title() }}</h2>
          @if (message()) {
            <p>{{ message() }}</p>
          }
          <ng-content />
        </div>
      }
    }
  `,
})
export class StatePanel {
  readonly kind = input<'loading' | 'empty' | 'error' | 'not-found'>('empty');
  readonly title = input('Nothing to show');
  readonly message = input<string>();
}
