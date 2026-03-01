import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/hello/hello.component').then((m) => m.HelloComponent),
  },
];
