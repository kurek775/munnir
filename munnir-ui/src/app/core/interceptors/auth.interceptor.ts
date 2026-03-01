import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { tap } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');

  if (token && req.url.startsWith('/api/')) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req).pipe(
    tap({
      error: (err) => {
        if (err.status === 401 && !req.url.includes('/auth/')) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          router.navigate(['/login']);
        }
      },
    }),
  );
};
