import { computed, Injectable, signal } from '@angular/core';
import { scenarioSession, scenarios } from './fixtures';

/** Local presentation only. Shared with the preview, never with the mock data source. */
@Injectable({ providedIn: 'root' })
export class GuidedExplorerState {
  readonly active = signal(false);
  readonly expanded = signal(true);
  readonly step = signal(0);
  readonly selected = signal('interrupted-success');
  readonly openRequest = signal(0);
  readonly steps = ['Task', 'Approval preview', 'Run', 'Result', 'Journal'] as const;
  readonly scenarios = scenarios;
  readonly session = computed(() => scenarioSession(this.selected()));

  open(): void {
    this.active.set(true);
    this.expanded.set(true);
    this.openRequest.update((value) => value + 1);
  }
  minimize(): void {
    this.expanded.set(false);
  }
  exit(): void {
    this.active.set(false);
  }
  go(index: number): void {
    if (Number.isInteger(index) && index >= 0 && index < this.steps.length) this.step.set(index);
  }
  choose(id: string): void {
    if (scenarios.some(([key]) => key === id)) this.selected.set(id);
  }
}
