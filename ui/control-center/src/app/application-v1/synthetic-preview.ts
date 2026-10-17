import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { recordIdentity } from './decode';
import { scenarioSession, scenarios } from './fixtures';
import { runLabels, schedulerLabels, taskLabels, unsupported } from './presentation';

@Component({
  selector: 'cc-application-v1-preview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './synthetic-preview.html',
  styleUrl: './synthetic-preview.css',
})
export class SyntheticPreview {
  protected readonly scenarios = scenarios;
  protected readonly selected = signal('interrupted-success');
  protected readonly session = computed(() => scenarioSession(this.selected()));
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
    this.selected.set((event.target as HTMLSelectElement).value);
  }
}
