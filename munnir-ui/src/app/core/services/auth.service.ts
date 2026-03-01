import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { tap } from 'rxjs';
import { ApiService } from './api.service';
import { ThemeService } from './theme.service';
import { TokenResponse, UserResponse } from '../models/auth.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);
  private router = inject(Router);
  private themeService = inject(ThemeService);

  currentUser = signal<UserResponse | null>(null);
  isLoggedIn = computed(() => !!this.getToken());

  login(username: string, password: string) {
    return this.api.post<TokenResponse>('/api/v1/auth/login', { username, password }).pipe(
      tap((res) => {
        this.storeTokens(res);
        this.fetchCurrentUser();
      }),
    );
  }

  register(username: string, email: string, password: string) {
    return this.api.post<TokenResponse>('/api/v1/auth/register', { username, email, password }).pipe(
      tap((res) => {
        this.storeTokens(res);
        this.fetchCurrentUser();
      }),
    );
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  fetchCurrentUser() {
    this.api.get<UserResponse>('/api/v1/users/me').subscribe({
      next: (user) => {
        this.currentUser.set(user);
        this.themeService.setTheme(user.preferred_theme as 'dark' | 'light');
      },
    });
  }

  private storeTokens(res: TokenResponse) {
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
  }
}
