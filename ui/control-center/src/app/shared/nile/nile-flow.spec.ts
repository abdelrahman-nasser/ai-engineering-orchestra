import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { NileNode, NileTopology } from '../../data/models';
import { NileFlow } from './nile-flow';

const TOPOLOGY: NileTopology = {
  nodes: [
    { id: 's1', label: 'understand', kind: 'stage', column: 0, lane: 0, state: 'unknown' },
    { id: 'r1', label: 'reviewer', sublabel: 'agent-a', kind: 'run', column: 0.5, lane: -0.6, state: 'in-progress' },
    { id: 'r2', label: 'architect', sublabel: 'agent-b', kind: 'run', column: 0.5, lane: 0.6, state: 'needs-attention' },
    { id: 'end', label: 'Result', sublabel: 'provisional', kind: 'outcome', column: 1, lane: 0, state: 'unknown' },
  ],
  edges: [
    { from: 's1', to: 'r1' },
    { from: 's1', to: 'r2' },
    { from: 'r1', to: 'end' },
    { from: 'r2', to: 'end' },
  ],
};

@Component({
  imports: [NileFlow],
  template: `<cc-nile-flow [topology]="topology()" [selectedId]="selected()" (nodeSelect)="picked.push($event)" />`,
})
class Host {
  readonly topology = signal<NileTopology>(TOPOLOGY);
  readonly selected = signal<string | undefined>('r1');
  readonly picked: NileNode[] = [];
}

describe('NileFlow', () => {
  async function render() {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture;
  }
  const root = (fixture: { nativeElement: HTMLElement }) => fixture.nativeElement;

  it('renders one island per node and one channel per edge', async () => {
    const el = root(await render());
    expect(el.querySelectorAll('g.node')).toHaveLength(4);
    expect(el.querySelectorAll('g.edge')).toHaveLength(4);
    expect(el.querySelectorAll('g.edge path.flow')).toHaveLength(8);
  });

  it('draws every channel as a non-empty cubic path', async () => {
    const el = root(await render());
    for (const path of Array.from(el.querySelectorAll('g.edge path.body'))) {
      expect(path.getAttribute('d')).toMatch(/^M [\d.-]+ [\d.-]+ C /);
    }
  });

  it('marks the selected island and exposes accessible names', async () => {
    const el = root(await render());
    const selected = el.querySelector('g.node.selected');
    expect(selected?.getAttribute('aria-label')).toContain('reviewer');
    expect(selected?.getAttribute('aria-pressed')).toBe('true');
    expect(el.querySelector('[role="group"]')?.getAttribute('aria-label')).toBe('Execution topology');
  });

  it('makes only runs and tasks interactive by default', async () => {
    const el = root(await render());
    expect(el.querySelectorAll('g.node[role="button"]')).toHaveLength(2);
    expect(el.querySelectorAll('g.node[role="img"]')).toHaveLength(2);
    expect(el.querySelector('g.node[data-kind="stage"]')?.hasAttribute('tabindex')).toBe(false);
  });

  it('emits on click and on Enter, but not for non-selectable nodes', async () => {
    const fixture = await render();
    const el = root(fixture);
    (el.querySelector('g.node[data-kind="run"]') as SVGGElement).dispatchEvent(new Event('click'));
    const second = el.querySelectorAll('g.node[data-kind="run"]')[1] as SVGGElement;
    second.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    (el.querySelector('g.node[data-kind="stage"]') as SVGGElement).dispatchEvent(new Event('click'));

    expect(fixture.componentInstance.picked.map((node) => node.id)).toEqual(['r1', 'r2']);
  });

  it('pauses and resumes the decorative flow', async () => {
    const fixture = await render();
    const el = root(fixture);
    const button = el.querySelector('button.flow-toggle') as HTMLButtonElement;
    expect(button.getAttribute('aria-pressed')).toBe('false');
    expect(el.querySelector('.nile')?.classList.contains('paused')).toBe(false);

    button.click();
    await fixture.whenStable();
    expect(button.getAttribute('aria-pressed')).toBe('true');
    expect(el.querySelector('.nile')?.classList.contains('paused')).toBe(true);
    expect(button.textContent).toContain('Resume');
  });

  it('states plainly that it is presentation topology only', async () => {
    const el = root(await render());
    expect(el.querySelector('.footnote')?.textContent).toContain('Presentation topology only');
  });

  it('shows a legend only for states that are present', async () => {
    const el = root(await render());
    const labels = Array.from(el.querySelectorAll('.legend li')).map((li) => li.textContent?.trim());
    expect(labels).toEqual(['In progress', 'Needs attention', 'No observation']);
  });

  it('survives an empty topology', async () => {
    const fixture = await render();
    fixture.componentInstance.topology.set({ nodes: [], edges: [] });
    await fixture.whenStable();
    expect(root(fixture).querySelector('svg.river')).toBeNull();
  });

  it('tints channels only by the Run they touch and keeps the trunk neutral', async () => {
    const fixture = await render();
    fixture.componentInstance.topology.set({
      nodes: [
        { id: 'a', label: 'a', kind: 'stage', column: 0, lane: 0, state: 'needs-attention' },
        { id: 'b', label: 'b', kind: 'stage', column: 1, lane: 0, state: 'needs-attention' },
        { id: 'r', label: 'r', kind: 'run', column: 1.5, lane: 0, state: 'in-progress' },
        { id: 'c', label: 'c', kind: 'stage', column: 2, lane: 0, state: 'needs-attention' },
      ],
      edges: [
        { from: 'a', to: 'b' },
        { from: 'b', to: 'r' },
        { from: 'r', to: 'c' },
      ],
    });
    await fixture.whenStable();
    const states = Array.from(root(fixture).querySelectorAll('g.edge')).map((edge) => [
      edge.getAttribute('data-weight'),
      edge.getAttribute('data-state'),
    ]);
    expect(states).toEqual([
      ['main', 'neutral'],
      ['tributary', 'in-progress'],
      ['tributary', 'in-progress'],
    ]);
  });

  it('spreads lanes further apart when laneHeight is increased', async () => {
    const gap = async (laneHeight?: number) => {
      const fixture = TestBed.createComponent(NileFlow);
      fixture.componentRef.setInput('topology', TOPOLOGY);
      if (laneHeight) {
        fixture.componentRef.setInput('laneHeight', laneHeight);
      }
      await fixture.whenStable();
      const ys = ['r1', 'r2'].map((id) => {
        const label = `${id === 'r1' ? 'reviewer' : 'architect'}`;
        const node = Array.from(fixture.nativeElement.querySelectorAll('g.node')).find((n) =>
          (n as Element).getAttribute('aria-label')?.includes(label),
        ) as Element;
        return Number(/translate\([\d.-]+ ([\d.-]+)\)/.exec(node.getAttribute('transform')!)![1]);
      });
      return ys[1] - ys[0];
    };
    expect(await gap(120)).toBeGreaterThan(await gap());
  });
});

