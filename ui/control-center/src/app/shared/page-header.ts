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
    .header-main {
      flex: 1;
      min-width: 0;
    }
    .crumbs {
      margin-bottom: var(--space-2);
    }
    .crumb-list {
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;
      font-size: 12px;
      color: var(--text-faint);
    }
    .crumb-item {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .crumb-item a {
      color: var(--text-muted);
      border-radius: var(--radius-xs);
    }
    .crumb-item a:hover {
      color: var(--accent);
    }
    .crumb-current {
      color: var(--text-faint);
    }
    .lede {
      margin-top: var(--space-2);
      max-width: 72ch;
      color: var(--text-muted);
      font-size: 14px;
      line-height: var(--leading-normal);
    }
    .actions {
      display: flex;
      gap: var(--space-2);
      align-items: center;
      flex-wrap: wrap;
    }
    @media (max-width: 640px) {
      :host {
        align-items: flex-start;
      }
    }
  `,
  template: `
    <div class="header-main">
      @if (crumbs().length) {
        <nav class="crumbs" aria-label="Breadcrumb">
          <ol class="crumb-list">
            @for (crumb of crumbs(); track crumb.label; let last = $last) {
              <li class="crumb-item">
                @if (crumb.link && !last) {
                  <a [routerLink]="crumb.link">{{ crumb.label }}</a>
                  <cc-icon name="chevron-right" [size]="12" />
                } @else {
                  <span class="crumb-current" [attr.aria-current]="last ? 'page' : null">{{ crumb.label }}</span>
                }
              </li>
            }
          </ol>
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
