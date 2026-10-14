import { DOCUMENT } from '@angular/common';
import { Injectable, effect, inject, signal } from '@angular/core';

export type ThemeMode = 'dark' | 'light';

export const THEME_STORAGE_KEY = 'itru-control-center-theme';

/** Owns dark/light mode. Persists the user's choice; defaults to the OS preference. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);

  readonly mode = signal<ThemeMode>(this.initialMode());

  constructor() {
    effect(() => {
      const mode = this.mode();
      this.document.documentElement.setAttribute('data-theme', mode);
      this.document.documentElement.style.colorScheme = mode;
      try {
        this.document.defaultView?.localStorage.setItem(THEME_STORAGE_KEY, mode);
      } catch {
        // Storage may be unavailable (private mode); the theme still applies.
      }
    });
  }

  toggle(): void {
    this.mode.update((current) => (current === 'dark' ? 'light' : 'dark'));
  }

  set(mode: ThemeMode): void {
    this.mode.set(mode);
  }

  private initialMode(): ThemeMode {
    const view = this.document.defaultView;
    try {
      const stored = view?.localStorage.getItem(THEME_STORAGE_KEY);
      if (stored === 'dark' || stored === 'light') {
        return stored;
      }
    } catch {
      // fall through to OS preference
    }
    return view?.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
}
