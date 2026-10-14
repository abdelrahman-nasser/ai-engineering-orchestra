import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { ControlCenterDataSource } from './data/control-center-data-source';
import { MockControlCenterDataSource } from './data/mock/mock-control-center-data-source';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    // The one place a data origin is chosen. Swapping the implementation here
    // must not require touching any screen.
    { provide: ControlCenterDataSource, useClass: MockControlCenterDataSource },
  ],
};
