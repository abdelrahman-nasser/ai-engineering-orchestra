import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { App, PRIMARY_NAV } from './app';
import { testProviders } from '../testing/providers';

describe('App shell', () => {
  async function createShell() {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    await TestBed.configureTestingModule({ imports: [App], providers: testProviders() }).compileComponents();
    const fixture = TestBed.createComponent(App);
    const router = TestBed.inject(Router);
    await fixture.whenStable();
    return { fixture, router, el: fixture.nativeElement as HTMLElement };
  }

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

  it('shows the primary destinations in order', async () => {
    const { el } = await createShell();
    const labels = Array.from(el.querySelectorAll('nav a.nav-link .nav-label')).map((n) => n.textContent?.trim());
    expect(labels).toEqual(['Overview', 'Flow', 'Runs', 'Tasks', 'Agents', 'Approvals']);
    expect(PRIMARY_NAV.map((item) => item.path)).toEqual(['/', '/flow', '/runs', '/tasks', '/agents', '/approvals']);
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
    const ctx = await createShell();
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
});
