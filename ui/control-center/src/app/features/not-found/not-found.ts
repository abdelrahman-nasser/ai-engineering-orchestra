import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageHeader } from '../../shared/page-header';
import { StatePanel } from '../../shared/state-panel';

@Component({
  selector: 'cc-not-found',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, PageHeader, StatePanel],
  template: `
    <section class="page">
      <cc-page-header title="Page not found" />
      <cc-state-panel kind="not-found" title="This page does not exist" message="Use the navigation to get back on course.">
        <a class="btn" routerLink="/">Go to Overview</a>
      </cc-state-panel>
    </section>
  `,
})
export class NotFound {}
