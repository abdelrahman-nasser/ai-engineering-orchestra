import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { App, PRIMARY_NAV } from './app';
import { testProviders } from '../testing/providers';

describe('App shell', () => {
  async function createShell(width = 1024) {
    Object.defineProperty(window, 'innerWidth', { configurable: true, writable: true, value: width });
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    await TestBed.configureTestingModule({ imports: [App], providers: testProviders() }).compileComponents();
    const fixture = TestBed.createComponent(App);
    const router = TestBed.inject(Router);
    await fixture.whenStable();
    // jsdom does not apply responsive media rules when innerWidth is changed.
    // Real viewport visibility and tab exclusion are verified in Chrome separately.
    if (width <= 900) {
      for (const button of fixture.nativeElement.querySelectorAll('.menu-btn, .drawer-close')) {
        (button as HTMLElement).style.display = 'inline-flex';
      }
    }
    return { fixture, router, el: fixture.nativeElement as HTMLElement };
  }

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, writable: true, value: 1024 });
  });

  /** Navigates and waits for lazy route + data to settle. */
  async function go(
    ctx: Awaited<ReturnType<typeof createShell>>,
    url: string,
  ): Promise<void> {
    await ctx.router.navigateByUrl(url);
    await ctx.fixture.whenStable();
    await ctx.fixture.whenStable();
  }

  it('creates the shell with a skip link and a single main landmark', async () => {
    const { el } = await createShell();
    expect(el.querySelector('a.skip-link')?.getAttribute('href')).toBe('#main');
    expect(el.querySelectorAll('main')).toHaveLength(1);
  });

  it('skips to current routed content without navigating to Overview', async () => {
    const ctx = await createShell();
    await go(ctx, '/application-v1-preview');
    ctx.el.querySelector<HTMLAnchorElement>('.skip-link')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.router.url).toBe('/application-v1-preview');
    expect(document.activeElement).toBe(ctx.el.querySelector('main'));
    expect(ctx.el.querySelector('h1')?.textContent).toContain('Guided developer demo');
  });

  it('shows the primary destinations in order', async () => {
    const { el } = await createShell();
    const labels = Array.from(el.querySelectorAll('nav a.nav-link .nav-label')).map((n) => n.textContent?.trim());
    expect(labels).toEqual(['Overview', 'Flow', 'Runs', 'Tasks', 'Agents', 'Approvals']);
    expect(PRIMARY_NAV.map((item) => item.path)).toEqual(['/', '/flow', '/runs', '/tasks', '/agents', '/approvals']);
  });

  it('discovers the demo from Overview and focuses detailed evidence without leaving its route', async () => {
    const ctx = await createShell();
    await go(ctx, '/');
    expect(ctx.el.querySelector('.demo-entry a')?.getAttribute('href')).toBe('/application-v1-preview');
    expect(ctx.el.querySelector('.preview-link')?.textContent).toContain('Guided developer demo');
    await go(ctx, '/application-v1-preview');
    ctx.el.querySelector<HTMLAnchorElement>('cc-guided-journey a[href="#lifecycle-evidence"]')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.router.url).toBe('/application-v1-preview');
    expect(document.activeElement).toBe(ctx.el.querySelector('#lifecycle-evidence'));
  });

  it('labels the data origin as mock in the shell', async () => {
    const { el } = await createShell();
    expect(el.querySelector('[data-testid="data-origin"]')?.textContent).toContain('Mock data');
    expect(el.querySelector('.pill-origin')?.textContent).toContain('Mock data');
  });

  it('shows how many approvals are awaiting evidence', async () => {
    const { el } = await createShell();
    expect(el.querySelector('.nav-badge')?.textContent?.trim()).toBe('3');
  });

  it('separates the synthetic application preview from mock approval counts', async () => {
    const ctx = await createShell();
    await go(ctx, '/application-v1-preview#evidence');
    expect(ctx.el.querySelector('.nav-badge')?.textContent?.trim()).toBe('—');
    expect(ctx.el.querySelector('.nav-badge')?.getAttribute('aria-label')).toContain('unavailable');
    expect(ctx.el.querySelector('.pill-origin')?.textContent).toContain('Synthetic application v1.0');
    expect(ctx.el.querySelector('h1')?.textContent).toContain('Guided developer demo');
    await go(ctx, '/');
    expect(ctx.el.querySelector('.nav-badge')?.textContent?.trim()).toBe('3');
    expect(ctx.el.querySelector('.pill-origin')?.textContent).toContain('Mock data');
  });

  const destinations: readonly [string, string][] = [
    ['/', 'Overview'],
    ['/flow', 'Nile Flow & Scheduler'],
    ['/runs', 'Runs'],
    ['/tasks', 'Tasks'],
    ['/agents', 'Agents'],
    ['/approvals', 'Approvals'],
    ['/runs/run_f27a9c58', 'run_f27a9c58'],
    ['/tasks/DEMO-102', 'Rework authentication token refresh'],
    ['/nowhere', 'Page not found'],
  ];


  for (const [url, heading] of destinations) {
    it(`renders ${url} with a single h1 "${heading}"`, async () => {
      const ctx = await createShell();
      await go(ctx, url);
      const h1 = ctx.el.querySelectorAll('h1');
      expect(h1).toHaveLength(1);
      expect(h1[0].textContent).toContain(heading);
    });
  }

  it('marks the active primary destination with aria-current', async () => {
    const ctx = await createShell();
    await go(ctx, '/tasks');
    const current = ctx.el.querySelectorAll('nav a[aria-current="page"]');
    expect(current).toHaveLength(1);
    expect(current[0].textContent).toContain('Tasks');
  });

  it('keeps Runs active on a run detail route but not Overview', async () => {
    const ctx = await createShell();
    await go(ctx, '/runs/run_f27a9c58');
    const current = Array.from(ctx.el.querySelectorAll('nav a[aria-current="page"]')).map((n) => n.textContent?.trim());
    expect(current).toEqual(['Runs']);
  });

  it('navigates when a primary link is clicked', async () => {
    const ctx = await createShell();
    const link = Array.from(ctx.el.querySelectorAll<HTMLAnchorElement>('nav a.nav-link')).find((a) =>
      a.textContent?.includes('Agents'),
    )!;
    link.click();
    await ctx.fixture.whenStable();
    await ctx.fixture.whenStable();
    expect(ctx.router.url).toBe('/agents');
    expect(ctx.el.querySelector('h1')?.textContent).toContain('Agents');
  });

  it('toggles between dark and light and reflects it on the document', async () => {
    const ctx = await createShell();
    const button = ctx.el.querySelector<HTMLButtonElement>('[data-testid="theme-toggle"]')!;
    expect(button.getAttribute('aria-label')).toBe('Switch to light theme');

    button.click();
    await ctx.fixture.whenStable();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(button.getAttribute('aria-label')).toBe('Switch to dark theme');

    button.click();
    await ctx.fixture.whenStable();
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('opens and closes the navigation drawer', async () => {
    const ctx = await createShell(390);
    const toggle = ctx.el.querySelector<HTMLButtonElement>('.menu-btn')!;
    expect(ctx.el.querySelector('.shell')?.classList.contains('nav-open')).toBe(false);
    toggle.click();
    await ctx.fixture.whenStable();
    expect(ctx.el.querySelector('.shell')?.classList.contains('nav-open')).toBe(true);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    ctx.el.querySelector<HTMLButtonElement>('.scrim')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.el.querySelector('.shell')?.classList.contains('nav-open')).toBe(false);
  });

  it('contains mobile keyboard focus, excludes the closed drawer and restores the opener', async () => {
    const { el, fixture } = await createShell(390);
    const sidebar = el.querySelector<HTMLElement>('#primary-sidebar')!;
    const content = el.querySelector<HTMLElement>('.content')!;
    const toggle = el.querySelector<HTMLButtonElement>('.menu-btn')!;
    expect(sidebar.inert).toBe(true);
    expect(content.inert).toBe(false);
    toggle.click();
    await fixture.whenStable();
    const close = el.querySelector<HTMLButtonElement>('.drawer-close')!;
    const last = el.querySelector<HTMLAnchorElement>('.preview-link')!;
    expect(sidebar.inert).toBe(false);
    expect(sidebar.getAttribute('role')).toBe('dialog');
    expect(sidebar.getAttribute('aria-modal')).toBe('true');
    expect(content.inert).toBe(true);
    await expect.poll(() => document.activeElement).toBe(close);
    close.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(last);
    last.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(close);
    close.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await fixture.whenStable();
    expect(sidebar.inert).toBe(true);
    expect(content.inert).toBe(false);
    await expect.poll(() => document.activeElement).toBe(toggle);
  });

  it('restores usable desktop navigation when resizing an open mobile drawer', async () => {
    const { el, fixture } = await createShell(390);
    el.querySelector<HTMLButtonElement>('.menu-btn')!.click();
    await fixture.whenStable();
    window.innerWidth = 1024;
    window.dispatchEvent(new Event('resize'));
    await fixture.whenStable();
    expect(el.querySelector<HTMLElement>('#primary-sidebar')!.inert).toBe(false);
    expect(el.querySelector('#primary-sidebar')!.hasAttribute('aria-modal')).toBe(false);
    expect(el.querySelector<HTMLElement>('.content')!.inert).toBe(false);
    await expect.poll(() => document.activeElement).toBe(el.querySelector('.brand'));
    window.innerWidth = 390;
    window.dispatchEvent(new Event('resize'));
    await fixture.whenStable();
    expect(el.querySelector<HTMLElement>('#primary-sidebar')!.inert).toBe(true);
    await expect.poll(() => document.activeElement).toBe(el.querySelector('.menu-btn'));
  });

  it('moves focus from the closed mobile menu toggle when desktop hides it', async () => {
    const { el, fixture } = await createShell(390);
    el.querySelector<HTMLButtonElement>('.menu-btn')!.focus();
    window.innerWidth = 1024;
    window.dispatchEvent(new Event('resize'));
    await fixture.whenStable();
    await expect.poll(() => document.activeElement).toBe(el.querySelector('.brand'));
    expect(el.querySelector<HTMLElement>('#primary-sidebar')!.inert).toBe(false);
  });
});
