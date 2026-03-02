import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    canActivate: [authGuard],
  },
  {
    path: 'sessions/:id',
    loadComponent: () =>
      import('./features/session-detail/session-detail.component').then((m) => m.SessionDetailComponent),
    canActivate: [authGuard],
  },
  {
    path: 'hello',
    loadComponent: () =>
      import('./features/hello/hello.component').then((m) => m.HelloComponent),
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/landing/landing.component').then((m) => m.LandingComponent),
  },
];
