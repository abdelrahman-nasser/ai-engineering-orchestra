import { EnvironmentProviders, Provider } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { routes } from '../app/app.routes';
import { ControlCenterDataSource } from '../app/data/control-center-data-source';
import {
  MOCK_LATENCY_MS,
  MockControlCenterDataSource,
} from '../app/data/mock/mock-control-center-data-source';

/** Providers mirroring `app.config.ts` with the mock latency removed. */
export function testProviders(): (Provider | EnvironmentProviders)[] {
  return [
    provideRouter(routes, withComponentInputBinding()),
    { provide: MOCK_LATENCY_MS, useValue: 0 },
    { provide: ControlCenterDataSource, useClass: MockControlCenterDataSource },
  ];
}
