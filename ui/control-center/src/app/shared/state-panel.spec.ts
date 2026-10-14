import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { StatePanel, StatePanelKind } from './state-panel';

@Component({
  imports: [StatePanel],
  template: `
    <cc-state-panel
      [kind]="kind()"
      [title]="customTitle()"
      [message]="customMessage()"
      [compact]="compact()"
    >
      <button type="button" class="btn">Retry Action</button>
    </cc-state-panel>
  `,
})
class TestHost {
  readonly kind = signal<StatePanelKind>('empty');
  readonly customTitle = signal<string | undefined>(undefined);
  readonly customMessage = signal<string | undefined>(undefined);
  readonly compact = signal<boolean>(false);
}

describe('StatePanel', () => {
  async function createHost() {
    await TestBed.configureTestingModule({ imports: [TestHost] }).compileComponents();
    const fixture = TestBed.createComponent(TestHost);
    await fixture.whenStable();
    return { fixture, host: fixture.componentInstance, el: fixture.nativeElement as HTMLElement };
  }

  it('renders loading skeleton with polite status role', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('loading');
    await fixture.whenStable();
    const bars = el.querySelector('.bars');
    expect(bars).not.toBeNull();
    expect(bars?.getAttribute('role')).toBe('status');
    expect(bars?.getAttribute('aria-live')).toBe('polite');
    expect(bars?.getAttribute('aria-busy')).toBe('true');
  });

  it('renders error state with alert role and error title', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('error');
    await fixture.whenStable();
    const panel = el.querySelector('.panel');
    expect(panel?.getAttribute('role')).toBe('alert');
    expect(panel?.getAttribute('data-kind')).toBe('error');
    expect(el.querySelector('h2')?.textContent).toContain('Something went wrong');
  });

  it('renders blocked state with lock icon and execution blocked title', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('blocked');
    await fixture.whenStable();
    const panel = el.querySelector('.panel');
    expect(panel?.getAttribute('data-kind')).toBe('blocked');
    expect(el.querySelector('h2')?.textContent).toContain('Execution blocked');
  });

  it('renders no-evidence state clarifying absence of proof', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('no-evidence');
    await fixture.whenStable();
    const panel = el.querySelector('.panel');
    expect(panel?.getAttribute('data-kind')).toBe('no-evidence');
    expect(el.querySelector('h2')?.textContent).toContain('No evidence yet');
  });

  it('renders unknown state distinguishing unobserved from failed', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('unknown');
    await fixture.whenStable();
    const panel = el.querySelector('.panel');
    expect(panel?.getAttribute('data-kind')).toBe('unknown');
    expect(el.querySelector('h2')?.textContent).toContain('No observation recorded');
  });

  it('renders unavailable state with slash icon', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('unavailable');
    await fixture.whenStable();
    const panel = el.querySelector('.panel');
    expect(panel?.getAttribute('data-kind')).toBe('unavailable');
    expect(el.querySelector('h2')?.textContent).toContain('Currently unavailable');
  });

  it('supports custom title, message and projected action content', async () => {
    const { fixture, host, el } = await createHost();
    host.kind.set('empty');
    host.customTitle.set('Custom empty headline');
    host.customMessage.set('Detailed explanation of why this is empty.');
    await fixture.whenStable();
    expect(el.querySelector('h2')?.textContent).toContain('Custom empty headline');
    expect(el.querySelector('p')?.textContent).toContain('Detailed explanation of why this is empty.');
    expect(el.querySelector('button.btn')?.textContent).toContain('Retry Action');
  });

  it('supports compact mode for dense embedded presentation', async () => {
    const { fixture, host, el } = await createHost();
    host.compact.set(true);
    await fixture.whenStable();
    expect(el.querySelector('.panel')?.classList.contains('compact')).toBe(true);
  });
});
