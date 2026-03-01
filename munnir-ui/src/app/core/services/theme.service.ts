import { Injectable, signal, inject } from '@angular/core';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private api = inject(ApiService);

  theme = signal<'dark' | 'light'>(this.loadTheme());

  toggle() {
    const next = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    localStorage.setItem('theme', next);
    this.applyTheme(next);
    this.api.patch('/api/v1/users/me', { preferred_theme: next }).subscribe();
  }

  init() {
    this.applyTheme(this.theme());
  }

  setTheme(theme: 'dark' | 'light') {
    this.theme.set(theme);
    localStorage.setItem('theme', theme);
    this.applyTheme(theme);
  }

  private loadTheme(): 'dark' | 'light' {
    const stored = localStorage.getItem('theme');
    return stored === 'light' ? 'light' : 'dark';
  }

  private applyTheme(theme: string) {
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(theme);
  }
}
