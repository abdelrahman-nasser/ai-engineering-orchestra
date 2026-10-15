import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';
import { ControlCenterDataSource } from './data/control-center-data-source';
import { Icon, IconName } from './shared/icon';
import { ThemeService } from './shared/theme.service';

interface NavItem {
  readonly label: string;
  readonly path: string;
  readonly icon: IconName;
  readonly exact: boolean;
}

/** Primary navigation. Order is the order shown in the sidebar. */
export const PRIMARY_NAV: readonly NavItem[] = [
  { label: 'Overview', path: '/', icon: 'overview', exact: true },
  { label: 'Flow', path: '/flow', icon: 'nile', exact: false },
  { label: 'Runs', path: '/runs', icon: 'runs', exact: false },
  { label: 'Tasks', path: '/tasks', icon: 'tasks', exact: false },
  { label: 'Agents', path: '/agents', icon: 'agents', exact: false },
  { label: 'Approvals', path: '/approvals', icon: 'approvals', exact: false },
];

/** Application shell: primary navigation, topbar, theme toggle and routed content. */
@Component({
  selector: 'cc-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icon],
  templateUrl: './app.html',
  styleUrl: './app.css',
  host: { '(document:keydown.escape)': 'closeNav()' },
})
export class App {
  private readonly dataSource = inject(ControlCenterDataSource);
  private readonly router = inject(Router);
  protected readonly theme = inject(ThemeService);

  protected readonly nav = PRIMARY_NAV;
  protected readonly originLabel = this.dataSource.originLabel;
  protected readonly navOpen = signal(false);

  private readonly approvals = toSignal(this.dataSource.listApprovals(), { initialValue: [] });
  /** Approvals with no grant/deny evidence yet; drives the nav badge. */
  protected readonly awaitingCount = computed(
    () => this.approvals().filter((approval) => approval.state === 'awaiting').length,
  );

  constructor() {
    // Close the mobile drawer after any navigation.
    toSignal(
      this.router.events.pipe(
        filter((event) => event instanceof NavigationEnd),
        map(() => this.navOpen.set(false)),
      ),
    );
  }

  protected toggleNav(): void {
    this.navOpen.update((open) => !open);
  }

  protected closeNav(): void {
    this.navOpen.set(false);
  }
}
