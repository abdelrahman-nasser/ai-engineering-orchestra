import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { vi } from 'vitest';
import { App } from '../app';
import { testProviders } from '../../testing/providers';
import { GuidedExplorerState } from './guided-explorer-state';
import { scenarios } from './fixtures';

describe('non-modal Guided Explorer', () => {
  async function open(width = 1440, url = '/application-v1-preview') {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: width,
    });
    await TestBed.configureTestingModule({
      imports: [App],
      providers: testProviders(),
    }).compileComponents();
    const fixture = TestBed.createComponent(App);
    const router = TestBed.inject(Router);
    const state = TestBed.inject(GuidedExplorerState);
    await router.navigateByUrl(url);
    await fixture.whenStable();
    state.open();
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    const guide = () => element.querySelector<HTMLElement>('cc-guided-journey')!;
    const stage = async (index: number) => {
      const select = guide().querySelector<HTMLSelectElement>('#explorer-stage')!;
      select.value = String(index);
      select.dispatchEvent(new Event('change'));
      await fixture.whenStable();
    };
    const choose = async (id: string) => {
      const select = guide().querySelector<HTMLSelectElement>('#explorer-scenario')!;
      select.value = id;
      select.dispatchEvent(new Event('change'));
      await fixture.whenStable();
    };
    return { fixture, router, state, element, guide, stage, choose };
  }

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: 1024,
    });
    vi.restoreAllMocks();
  });

  it('opens from Overview without navigating and stays beside freely navigable pages', async () => {
    const ctx = await open(1440, '/');
    ctx.state.exit();
    await ctx.fixture.whenStable();
    ctx.element.querySelector<HTMLButtonElement>('.demo-entry button')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.router.url).toBe('/');
    expect(ctx.guide()).not.toBeNull();
    expect(document.activeElement).toBe(ctx.guide().querySelector('.guide-scroll'));
    await ctx.stage(3);
    await ctx.choose('conflict');
    const instance = ctx.guide();
    await ctx.router.navigateByUrl('/flow');
    await ctx.fixture.whenStable();
    expect(ctx.guide()).toBe(instance);
    expect(ctx.state.step()).toBe(3);
    expect(ctx.state.selected()).toBe('conflict');
    expect(ctx.guide().textContent).toContain('Other pages use separate mock models');
    expect(ctx.element.querySelector('.pill-origin')?.textContent).toContain('Mock data');
    expect(ctx.guide().querySelectorAll('[data-testid="guided-result"]')).toHaveLength(2);
    await ctx.router.navigateByUrl('/application-v1-preview');
    await ctx.fixture.whenStable();
    expect(ctx.element.querySelector<HTMLSelectElement>('#application-scenario')!.value).toBe(
      'conflict',
    );
  });

  it('changes explanations only, preserving focus, route and application scroll APIs', async () => {
    const ctx = await open();
    const scroll = vi.fn();
    const focus = vi.spyOn(HTMLElement.prototype, 'focus');
    ctx.element.querySelector<HTMLElement>('#lifecycle-evidence')!.scrollIntoView = scroll;
    ctx.guide().querySelector<HTMLElement>('#guided-step-title')!.scrollIntoView = scroll;
    const next = ctx.guide().querySelector<HTMLButtonElement>('footer button:nth-child(2)')!;
    next.focus();
    focus.mockClear();
    next.click();
    await ctx.fixture.whenStable();
    expect(ctx.state.step()).toBe(1);
    expect(document.activeElement).toBe(next);
    expect(focus).not.toHaveBeenCalled();
    expect(scroll).not.toHaveBeenCalled();
    expect(ctx.router.url).toBe('/application-v1-preview');
    await ctx.stage(4);
    expect(focus).not.toHaveBeenCalled();
    expect(scroll).not.toHaveBeenCalled();
    expect(
      ctx
        .guide()
        .querySelector<HTMLButtonElement>('footer button:nth-child(2)')!
        .getAttribute('aria-disabled'),
    ).toBe('true');
    ctx.guide().querySelector<HTMLButtonElement>('footer button')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.state.step()).toBe(3);
    expect(scroll).not.toHaveBeenCalled();
  });

  it('retains the activating footer button at both endpoints and ignores unavailable navigation', async () => {
    const ctx = await open();
    const previous = ctx.guide().querySelector<HTMLButtonElement>('footer button')!;
    const next = ctx.guide().querySelector<HTMLButtonElement>('footer button:nth-child(2)')!;
    const focus = vi.spyOn(HTMLElement.prototype, 'focus');
    const navigate = vi.spyOn(ctx.router, 'navigateByUrl');
    const scroll = vi.fn();
    ctx.guide().querySelector<HTMLElement>('#guided-step-title')!.scrollIntoView = scroll;
    ctx.element.querySelector<HTMLElement>('#lifecycle-evidence')!.scrollIntoView = scroll;

    for (const [from, endpoint, button] of [
      [3, 4, next],
      [1, 0, previous],
    ] as const) {
      await ctx.stage(from);
      button.focus();
      focus.mockClear();
      button.click();
      await ctx.fixture.whenStable();
      expect(ctx.state.step()).toBe(endpoint);
      expect(button.disabled).toBe(false);
      expect(button.getAttribute('aria-disabled')).toBe('true');
      expect(document.activeElement).toBe(button);
      const boundaryAnnouncement = ctx.guide().querySelector('[role="status"]')!.textContent;
      button.click();
      button.click();
      await ctx.fixture.whenStable();
      expect(ctx.state.step()).toBe(endpoint);
      expect(document.activeElement).toBe(button);
      expect(ctx.guide().querySelector('[role="status"]')!.textContent).toBe(boundaryAnnouncement);
      expect(focus).not.toHaveBeenCalled();
      expect(scroll).not.toHaveBeenCalled();
      expect(navigate).not.toHaveBeenCalled();
      expect(ctx.router.url).toBe('/application-v1-preview');
    }
  });

  it('allows wheel, touch and scrolling keys through before, during and after the guide', async () => {
    const ctx = await open(390);
    const bodyOverflow = document.body.style.overflow;
    const htmlOverflow = document.documentElement.style.overflow;
    const assertEvents = (target: HTMLElement) => {
      for (const type of ['wheel', 'touchstart', 'touchmove']) {
        const event = new Event(type, { bubbles: true, cancelable: true });
        expect(target.dispatchEvent(event)).toBe(true);
        expect(event.defaultPrevented).toBe(false);
      }
      for (const key of ['PageDown', 'PageUp', 'Home', 'End', 'Tab']) {
        const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
        expect(target.dispatchEvent(event)).toBe(true);
        expect(event.defaultPrevented).toBe(false);
      }
    };
    ctx.state.exit();
    await ctx.fixture.whenStable();
    assertEvents(ctx.element.querySelector('main')!);
    ctx.state.open();
    await ctx.fixture.whenStable();
    assertEvents(ctx.element.querySelector('main')!);
    assertEvents(ctx.guide().querySelector('.guide-scroll')!);
    ctx.guide().querySelector<HTMLButtonElement>('[aria-label="Exit Guided Explorer"]')!.click();
    await ctx.fixture.whenStable();
    assertEvents(ctx.element.querySelector('main')!);
    expect(document.body.style.overflow).toBe(bodyOverflow);
    expect(document.documentElement.style.overflow).toBe(htmlOverflow);
    expect(ctx.element.querySelector('.content')!.hasAttribute('inert')).toBe(false);
    expect(ctx.element.querySelector('[aria-modal="true"]')).toBeNull();
  });

  it('minimizes and exits without trapping focus and re-enters the selected explanation', async () => {
    const ctx = await open();
    await ctx.stage(3);
    await ctx.choose('long-text');
    ctx.guide().querySelector<HTMLButtonElement>('[aria-label="Minimize guide"]')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.state.expanded()).toBe(false);
    expect(document.activeElement).toBe(ctx.guide().querySelector('.explorer-expand'));
    expect(ctx.guide().querySelector('.guide-scroll')).toBeNull();
    ctx.guide().querySelector<HTMLButtonElement>('.explorer-expand')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.guide().querySelector('h3')?.textContent).toBe('Result');
    const exit = ctx
      .guide()
      .querySelector<HTMLButtonElement>('[aria-label="Exit Guided Explorer"]')!;
    const tab = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
    exit.dispatchEvent(tab);
    expect(tab.defaultPrevented).toBe(false);
    exit.click();
    await ctx.fixture.whenStable();
    expect(ctx.guide()).toBeNull();
    expect(document.activeElement).toBe(ctx.element.querySelector('.explorer-launch'));
    ctx.element.querySelector<HTMLButtonElement>('.explorer-launch')!.click();
    await ctx.fixture.whenStable();
    expect(ctx.state.step()).toBe(3);
    expect(ctx.state.selected()).toBe('long-text');
    expect(ctx.guide().querySelector<HTMLSelectElement>('#explorer-stage')!.value).toBe('3');
    expect(ctx.guide().querySelector<HTMLSelectElement>('#explorer-scenario')!.value).toBe(
      'long-text',
    );
  });

  it('locates only on explicit request, including same-route Contract details', async () => {
    const ctx = await open();
    await ctx.stage(1);
    const target = ctx.element.querySelector<HTMLDetailsElement>('#contract-evidence')!;
    target.scrollIntoView = vi.fn();
    const locate = ctx.guide().querySelector<HTMLButtonElement>('.locate')!;
    locate.click();
    await ctx.fixture.whenStable();
    expect(target.open).toBe(true);
    expect(document.activeElement).toBe(target);
    expect(target.scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'instant' });
    expect(ctx.router.url).toBe('/application-v1-preview');
  });

  it('locates synthetic sections across routes and honestly falls back when unavailable', async () => {
    const ctx = await open(1440, '/flow');
    await ctx.stage(4);
    ctx.guide().querySelector<HTMLButtonElement>('.locate')!.click();
    await ctx.fixture.whenStable();
    await ctx.fixture.whenStable();
    expect(ctx.router.url).toBe('/application-v1-preview');
    expect(document.activeElement).toBe(ctx.element.querySelector('#journal-evidence'));
    await ctx.choose('denied');
    await ctx.stage(1);
    ctx.guide().querySelector<HTMLButtonElement>('.locate')!.click();
    await ctx.fixture.whenStable();
    expect(document.activeElement).toBe(ctx.element.querySelector('#lifecycle-evidence'));
    expect(ctx.guide().querySelector('[role="status"]')?.textContent).toContain(
      'Selected section unavailable',
    );
    await ctx.stage(3);
    ctx.guide().querySelector<HTMLButtonElement>('.locate')!.click();
    await ctx.fixture.whenStable();
    expect(document.activeElement).toBe(ctx.element.querySelector('#journal-evidence'));
  });

  it('preserves all 18 scenarios, exact long subjects and nonoperational actions', async () => {
    const ctx = await open();
    expect(ctx.guide().querySelectorAll('#explorer-scenario option')).toHaveLength(18);
    for (const [id] of scenarios) {
      await ctx.choose(id);
      expect(ctx.state.selected()).toBe(id);
      expect(ctx.element.querySelector<HTMLSelectElement>('#application-scenario')!.value).toBe(id);
      expect(ctx.guide().querySelector('.explore')?.textContent).not.toContain(
        'Explore the supplied synthetic observations.',
      );
      const actions = ctx.element.querySelectorAll<HTMLButtonElement>(
        '[aria-label="Operational controls"] button',
      );
      expect(actions).toHaveLength(4);
      expect([...actions].every((button) => button.disabled)).toBe(true);
    }
    await ctx.stage(1);
    expect(ctx.guide().textContent).toContain(`synthetic/${'resource'.repeat(24)}/example.txt`);
    expect(ctx.guide().textContent).toContain('no authorization is requested or granted');
    expect(ctx.guide().textContent).toContain('Continuation remains unassessed');
  });

  it('clears denied subjects at every stop across expanded, minimized and re-entry states', async () => {
    const ctx = await open();
    for (let step = 0; step < 5; step++) {
      await ctx.choose('interrupted-success');
      await ctx.stage(step);
      await ctx.choose('denied');
      expect(ctx.guide().textContent).not.toMatch(
        /SYNTHETIC-(task|run|grant|ledger|actor|runtime|inference)/,
      );
      expect(ctx.guide().textContent).toContain('denied');
    }
    ctx.state.minimize();
    await ctx.fixture.whenStable();
    expect(ctx.guide().textContent).not.toContain('SYNTHETIC-');
    ctx.state.exit();
    ctx.state.open();
    await ctx.fixture.whenStable();
    expect(ctx.guide().textContent).not.toMatch(/SYNTHETIC-(task|run|grant)/);
  });

  it('retains independent summaries, stale times and distinct Journal coverage claims', async () => {
    const ctx = await open();
    await ctx.stage(3);
    expect(ctx.guide().textContent).toContain('Lifecycle accepted Result identity:');
    expect(ctx.guide().textContent).toContain('Unavailable — explicit null');
    expect(ctx.guide().textContent).toContain('byte count: 0');
    await ctx.choose('conflict');
    expect(ctx.guide().querySelectorAll('[data-testid="guided-result"]')).toHaveLength(2);
    await ctx.choose('entry-only');
    expect(ctx.guide().querySelectorAll('[data-testid="guided-result"]')).toHaveLength(0);
    await ctx.choose('stale');
    expect(ctx.guide().textContent).toContain('2026-10-17T10:00:01.000000Z');
    await ctx.choose('invalid');
    expect(ctx.guide().querySelectorAll('[data-testid="guided-result"]')).toHaveLength(0);
    await ctx.stage(4);
    await ctx.choose('partial-empty');
    expect(ctx.guide().textContent).toContain('subject uniqueness remain unproven');
    await ctx.choose('complete-empty');
    expect(ctx.guide().textContent).toContain('does not establish absence of invocation');
  });

  it('keeps seven educational Run meanings and a named keyboard-scrollable long explanation', async () => {
    const ctx = await open();
    await ctx.stage(2);
    const region = ctx.guide().querySelector<HTMLElement>('.guide-scroll')!;
    expect(region.tabIndex).toBe(0);
    expect(region.getAttribute('aria-label')).toBe('Scrollable guide explanation');
    expect(region.querySelectorAll('details dt')).toHaveLength(7);
    expect(region.textContent).toContain('No operation content-data request began');
    expect(region.textContent).toContain('blocks continuation and automatic retry or replay');
    expect(region.textContent).toContain('not a transition sequence');
  });

  it('minimizes for mobile editing without moving input focus or locking the page', async () => {
    const ctx = await open(390, '/flow');
    const input = ctx.element.querySelector<HTMLInputElement>('input')!;
    input.focus();
    await ctx.fixture.whenStable();
    expect(ctx.state.expanded()).toBe(false);
    expect(document.activeElement).toBe(input);
    expect(ctx.element.querySelector('.content')!.hasAttribute('inert')).toBe(false);
    expect(document.body.style.overflow).not.toBe('hidden');
  });
  it('accounts for an editable visual viewport, preserves zoom use and removes viewport listeners', async () => {
    const descriptor = Object.getOwnPropertyDescriptor(window, 'visualViewport');
    const viewport = Object.assign(new EventTarget(), { height: window.innerHeight, offsetTop: 0 });
    Object.defineProperty(window, 'visualViewport', { configurable: true, value: viewport });
    try {
      const ctx = await open(390, '/flow');
      ctx.element.querySelector<HTMLInputElement>('input')!.focus();
      viewport.height = window.innerHeight - 200;
      viewport.dispatchEvent(new Event('resize'));
      await ctx.fixture.whenStable();
      expect(
        ctx.element
          .querySelector<HTMLElement>('.workspace')!
          .style.getPropertyValue('--explorer-keyboard-inset'),
      ).toBe('200px');
      expect(ctx.state.expanded()).toBe(false);
      ctx.element.querySelector<HTMLButtonElement>('.explorer-launch')!.click();
      await ctx.fixture.whenStable();
      viewport.dispatchEvent(new Event('resize'));
      await ctx.fixture.whenStable();
      expect(ctx.state.expanded()).toBe(true);
      expect(
        ctx.element
          .querySelector<HTMLElement>('.workspace')!
          .style.getPropertyValue('--explorer-keyboard-inset'),
      ).toBe('0px');
      ctx.fixture.destroy();
      viewport.height = window.innerHeight - 300;
      expect(() => viewport.dispatchEvent(new Event('resize'))).not.toThrow();
    } finally {
      if (descriptor) Object.defineProperty(window, 'visualViewport', descriptor);
      else Reflect.deleteProperty(window, 'visualViewport');
    }
  });
});
