import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export type IconName =
  | 'overview'
  | 'runs'
  | 'tasks'
  | 'agents'
  | 'approvals'
  | 'sun'
  | 'moon'
  | 'menu'
  | 'close'
  | 'check'
  | 'alert'
  | 'clock'
  | 'branch'
  | 'file'
  | 'shield'
  | 'chevron-right'
  | 'play'
  | 'pause'
  | 'nile'
  | 'lock'
  | 'help'
  | 'slash'
  | 'search'
  | 'filter'
  | 'cross-circle'
  | 'tool'
  | 'info'
  | 'code';

/** Stroke-based 24px glyphs. Each entry is one or more SVG path `d` values. */
const PATHS: Readonly<Record<IconName, readonly string[]>> = {
  overview: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'],
  runs: ['M4 12c3-6 5 6 8 0s5 6 8 0', 'M4 18c3-6 5 6 8 0s5 6 8 0', 'M4 6c3-6 5 6 8 0s5 6 8 0'],
  tasks: ['M9 6h11', 'M9 12h11', 'M9 18h11', 'M3.5 6l1.2 1.2L7 5', 'M3.5 12l1.2 1.2L7 11', 'M3.5 18l1.2 1.2L7 17'],
  agents: ['M12 3a4 4 0 100 8 4 4 0 000-8z', 'M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7'],
  approvals: ['M12 3l8 3v6c0 4.6-3.2 8.3-8 9.5C7.2 20.300 4 16.600 4 12V6z', 'M8.500 12l2.500 2.500 4.500-5'],
  sun: ['M12 8a4 4 0 100 8 4 4 0 000-8z', 'M12 2v2', 'M12 20v2', 'M4.900 4.900l1.400 1.400', 'M17.700 17.700l1.400 1.400', 'M2 12h2', 'M20 12h2', 'M4.900 19.100l1.400-1.400', 'M17.700 6.300l1.400-1.400'],
  moon: ['M20 14.500A8 8 0 019.500 4 8.500 8.500 0 1020 14.500z'],
  menu: ['M4 7h16', 'M4 12h16', 'M4 17h16'],
  close: ['M6 6l12 12', 'M18 6L6 18'],
  check: ['M5 12.500l4.500 4.500L19 7.500'],
  alert: ['M12 3l10 18H2z', 'M12 10v5', 'M12 18.200v.1'],
  clock: ['M12 3a9 9 0 100 18 9 9 0 000-18z', 'M12 7v5l3 2'],
  branch: ['M6 3v12', 'M18 9a3 3 0 100-6 3 3 0 000 6z', 'M6 21a3 3 0 100-6 3 3 0 000 6z', 'M18 9c0 6-12 3-12 6'],
  file: ['M6 3h8l5 5v13H6z', 'M14 3v5h5'],
  shield: ['M12 3l8 3v6c0 4.600-3.200 8.300-8 9.500C7.200 20.300 4 16.600 4 12V6z'],
  'chevron-right': ['M9 6l6 6-6 6'],
  play: ['M7 4.500v15l12-7.500z'],
  pause: ['M8 5v14', 'M16 5v14'],
  nile: ['M2 16c4-8 6 8 10 0s6 8 10 0', 'M2 10c4-8 6 8 10 0s6 8 10 0'],
  lock: ['M7 11V7a5 5 0 0110 0v4', 'M5 11h14v10H5z', 'M12 15v2'],
  help: ['M12 22a10 10 0 100-20 10 10 0 000 20z', 'M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3', 'M12 17h.01'],
  slash: ['M12 22a10 10 0 100-20 10 10 0 000 20z', 'M4.93 4.93l14.14 14.14'],
  search: ['M11 19a8 8 0 100-16 8 8 0 000 16z', 'M21 21l-4.35-4.35'],
  filter: ['M3 4h18l-7 8v6l-4 2v-8z'],
  'cross-circle': ['M12 22a10 10 0 100-20 10 10 0 000 20z', 'M15 9l-6 6', 'M9 9l6 6'],
  tool: ['M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z'],
  info: ['M12 22a10 10 0 100-20 10 10 0 000 20z', 'M12 16v-4', 'M12 8h.01'],
  code: ['M16 18l6-6-6-6', 'M8 6l-6 6 6 6'],
};

@Component({
  selector: 'cc-icon',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { 'aria-hidden': 'true', '[style.width.px]': 'size()', '[style.height.px]': 'size()' },
  styles: `
    :host {
      display: inline-flex;
      flex: none;
    }
    svg {
      width: 100%;
      height: 100%;
    }
  `,
  template: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      @for (d of paths(); track d) {
        <path [attr.d]="d" />
      }
    </svg>
  `,
})
export class Icon {
  readonly name = input.required<IconName>();
  readonly size = input(18);

  protected readonly paths = computed(() => PATHS[this.name()]);
}
