import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { recordIdentity } from './decode';
import { scenarios } from './fixtures';
import { runLabels, schedulerLabels, taskLabels, unsupported } from './presentation';
import { GuidedExplorerState } from './guided-explorer-state';

@Component({
  selector: 'cc-application-v1-preview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './synthetic-preview.html',
  styleUrl: './synthetic-preview.css',
})
export class SyntheticPreview {
  protected readonly explorer = inject(GuidedExplorerState);
  protected readonly scenarios = scenarios;
  protected readonly selected = this.explorer.selected;
  protected readonly scenarioLabel = computed(() =>
    scenarios.find(([id]) => id === this.selected())?.[1] ?? '',
  );
  protected readonly session = this.explorer.session;
  protected readonly inspection = computed(() => this.session().inspection.value);
  protected readonly journal = computed(() => this.session().journal.value);
  protected readonly taskLabels = taskLabels;
  protected readonly runLabels = runLabels;
  protected readonly schedulerLabels = schedulerLabels;
  protected readonly unsupported = unsupported;
  protected readonly physicalIdentity = recordIdentity;
  protected readonly contractEntries = computed(() =>
    Object.entries(this.inspection()?.lifecycle.binding.run.contract ?? {}),
  );
  protected choose(event: Event): void {
    this.explorer.choose((event.target as HTMLSelectElement).value);
  }
}
