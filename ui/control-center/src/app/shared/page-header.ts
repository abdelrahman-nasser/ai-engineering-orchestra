import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from './icon';

export interface Crumb {
  readonly label: string;
  readonly link?: readonly string[];
}

/** Page title block: breadcrumbs, the single h1, a lede and an actions slot. */
@Component({
  selector: 'cc-page-header',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icon],
  styles: `
    :host {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: var(--space-4);
      flex-wrap: wrap;
    }
    .crumbs {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: var(--space-2);
      font-size: 12px;
      color: var(--text-faint);
    }
    .crumbs a {
      color: var(--text-muted);
    }
    .lede {
      margin-top: var(--space-2);
      max-width: 70ch;
      color: var(--text-muted);
      font-size: 14px;
    }
    .actions {
      display: flex;
      gap: var(--space-2);
      align-items: center;
    }
  `,
  template: `
    <div>
      @if (crumbs().length) {
        <nav class="crumbs" aria-label="Breadcrumb">
          @for (crumb of crumbs(); track crumb.label; let last = $last) {
            @if (crumb.link && !last) {
              <a [routerLink]="crumb.link">{{ crumb.label }}</a>
              <cc-icon name="chevron-right" [size]="12" />
            } @else {
              <span [attr.aria-current]="last ? 'page' : null">{{ crumb.label }}</span>
            }
          }
        </nav>
      }
      <h1>{{ title() }}</h1>
      @if (lede()) {
        <p class="lede">{{ lede() }}</p>
      }
    </div>
    <div class="actions"><ng-content /></div>
  `,
})
export class PageHeader {
  readonly title = input.required<string>();
  readonly lede = input<string>();
  readonly crumbs = input<readonly Crumb[]>([]);
}
