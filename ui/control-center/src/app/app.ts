import { DOCUMENT } from '@angular/common';
import { afterNextRender, ChangeDetectionStrategy, Component, computed, DestroyRef, effect, ElementRef, inject, Injector, signal, untracked } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';
import { ControlCenterDataSource } from './data/control-center-data-source';
import { Icon, IconName } from './shared/icon';
import { ThemeService } from './shared/theme.service';
import { GuidedExplorerState } from './application-v1/guided-explorer-state';
import { GuidedJourney } from './application-v1/guided-journey';

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
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icon, GuidedJourney],
  templateUrl: './app.html',
  styleUrl: './app.css',
  host: {
    '(document:keydown)': 'handleNavKeydown($event)',
    '(window:resize)': 'updateViewport()',
    '(focusin)': 'handleEditingFocus($event)',
  },
})
export class App {
  private readonly dataSource = inject(ControlCenterDataSource);
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  private readonly element = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  protected readonly theme = inject(ThemeService);
  protected readonly explorer = inject(GuidedExplorerState);
  protected readonly keyboardInset = signal(0);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly nav = PRIMARY_NAV;
  protected readonly originLabel = this.dataSource.originLabel;
  private readonly routeUrl = toSignal(this.router.events.pipe(
    filter((event) => event instanceof NavigationEnd),
    map((event) => event.urlAfterRedirects),
  ), { initialValue: this.router.url });
  protected readonly applicationPreview = computed(
    () => this.routeUrl().split(/[?#;]/)[0].replace(/\/+$/, '') === '/application-v1-preview',
  );
  protected readonly navOpen = signal(false);
  protected readonly isDrawer = signal((this.document.defaultView?.innerWidth ?? 1024) <= 900);

  private readonly approvals = toSignal(this.dataSource.listApprovals(), { initialValue: [] });
  /** Approvals with no grant/deny evidence yet; drives the nav badge. */
  protected readonly awaitingCount = computed(
    () => this.approvals().filter((approval) => approval.state === 'awaiting').length,
  );

  constructor() {
    effect(() => {
      if (this.explorer.openRequest() > 0) {
        untracked(() => afterNextRender(() => {
          if (this.explorer.active() && this.explorer.expanded()) {
            const region = this.element.nativeElement.querySelector<HTMLElement>('.guide-scroll');
            region?.focus({ preventScroll: true });
          }
        }, { injector: this.injector }));
      }
    });
    const viewport = this.document.defaultView?.visualViewport;
    const updateKeyboard = () => {
      const editing = this.document.activeElement?.matches('input, textarea, [contenteditable="true"]');
      const inset = viewport && editing ? Math.max(0, (this.document.defaultView?.innerHeight ?? 0) - viewport.height - viewport.offsetTop) : 0;
      this.keyboardInset.set(inset);
      if (inset > 120 && this.isDrawer()) this.explorer.minimize();
    };
    viewport?.addEventListener('resize', updateKeyboard);
    viewport?.addEventListener('scroll', updateKeyboard);
    this.destroyRef.onDestroy(() => {
      viewport?.removeEventListener('resize', updateKeyboard);
      viewport?.removeEventListener('scroll', updateKeyboard);
    });
    updateKeyboard();
    // Close the mobile drawer after any navigation.
    toSignal(
      this.router.events.pipe(
        filter((event) => event instanceof NavigationEnd),
        map(() => this.closeNav()),
      ),
    );
  }

  protected handleEditingFocus(event: FocusEvent): void {
    const target = event.target;
    if (this.isDrawer() && target instanceof Element && target.matches('input, textarea, [contenteditable="true"]') && !target.closest('cc-guided-journey')) {
      this.explorer.minimize();
    }
  }

  protected toggleNav(): void {
    if (this.navOpen()) {
      this.closeNav();
    } else if (this.isDrawer()) {
      this.navOpen.set(true);
      this.focusAfterRender('.drawer-close');
    }
  }

  protected closeNav(): void {
    if (!this.navOpen()) return;
    this.navOpen.set(false);
    if (this.isDrawer()) this.focusAfterRender('.menu-btn');
  }

  protected skipToContent(event: Event): void {
    // The document base href would otherwise send nested routes to /#main.
    event.preventDefault();
    const main = this.element.nativeElement.querySelector<HTMLElement>('#main');
    main?.focus({ preventScroll: true });
    main?.scrollIntoView?.({ block: 'start' });
  }

  private focusAfterRender(selector: string): void {
    afterNextRender(() => this.element.nativeElement.querySelector<HTMLElement>(selector)?.focus(),
      { injector: this.injector });
  }

  protected updateViewport(): void {
    const drawer = (this.document.defaultView?.innerWidth ?? 1024) <= 900;
    if (drawer === this.isDrawer()) return;
    const sidebar = this.element.nativeElement.querySelector('#primary-sidebar');
    const focusInSidebar = sidebar?.contains(this.document.activeElement);
    const focusOnToggle = this.document.activeElement === this.element.nativeElement.querySelector('.menu-btn');
    const wasOpen = this.navOpen();
    this.isDrawer.set(drawer);
    this.navOpen.set(false);
    if (drawer && focusInSidebar) this.focusAfterRender('.menu-btn');
    else if (!drawer && (wasOpen || focusOnToggle)) this.focusAfterRender('.brand');
  }

  protected handleNavKeydown(event: KeyboardEvent): void {
    if (!this.isDrawer() || !this.navOpen()) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      this.closeNav();
    } else if (event.key === 'Tab') {
      const links = Array.from(this.element.nativeElement.querySelectorAll<HTMLElement>(
        '#primary-sidebar a[href], #primary-sidebar button',
      ));
      const first = links[0];
      const last = links.at(-1);
      if (event.shiftKey && this.document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && this.document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
  }
}
