import { Signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Observable, catchError, map, of, startWith, switchMap } from 'rxjs';

/** UI-local view of an asynchronous read. */
export type LoadState<T> =
  | { readonly status: 'loading' }
  | { readonly status: 'ready'; readonly data: T }
  | { readonly status: 'error'; readonly message: string };

const LOADING: LoadState<never> = { status: 'loading' };

/** Wraps a read in loading → ready | error states. */
export function loadState$<T>(source$: Observable<T>): Observable<LoadState<T>> {
  return source$.pipe(
    map((data): LoadState<T> => ({ status: 'ready', data })),
    catchError((error: unknown) =>
      of<LoadState<T>>({
        status: 'error',
        message: error instanceof Error ? error.message : 'The data source could not be read.',
      }),
    ),
    startWith<LoadState<T>>(LOADING),
  );
}

/** Must be called in an injection context. */
export function toLoadState<T>(source$: Observable<T>): Signal<LoadState<T>> {
  return toSignal(loadState$(source$), { initialValue: LOADING });
}

/**
 * Re-reads whenever `key` changes (e.g. a route parameter). Must be called in
 * an injection context.
 */
export function toLoadStateFor<T>(
  key: Signal<string>,
  fetch: (key: string) => Observable<T>,
): Signal<LoadState<T>> {
  return toSignal(
    toObservable(key).pipe(switchMap((value) => loadState$(fetch(value)))),
    { initialValue: LOADING },
  );
}
