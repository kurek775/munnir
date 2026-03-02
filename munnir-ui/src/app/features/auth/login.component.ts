import { Component, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, TranslocoModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen flex items-center justify-center bg-base p-8">
      <div class="max-w-sm w-full space-y-8" *transloco="let t">
        <div class="text-center">
          <img [src]="theme.logoSrc()" [attr.alt]="t('app.logo_alt')" class="h-14 mx-auto" />
          <h1 class="text-xl font-bold text-text-primary mt-4">{{ t('auth.login') }}</h1>
        </div>

        @if (error()) {
          <div class="bg-danger-dim border border-danger/20 rounded-lg p-3 text-center">
            <p class="text-danger text-sm">{{ error() }}</p>
          </div>
        }

        <form (ngSubmit)="onSubmit()" class="space-y-4">
          <div>
            <label class="block text-sm text-text-secondary mb-1">{{ t('auth.username') }}</label>
            <input
              type="text"
              [(ngModel)]="username"
              name="username"
              required
              class="w-full px-3 py-2 bg-surface border border-elevated rounded-lg text-text-primary
                     focus:outline-none focus:border-accent text-sm"
            />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">{{ t('auth.password') }}</label>
            <input
              type="password"
              [(ngModel)]="password"
              name="password"
              required
              class="w-full px-3 py-2 bg-surface border border-elevated rounded-lg text-text-primary
                     focus:outline-none focus:border-accent text-sm"
            />
          </div>
          <button
            type="submit"
            [disabled]="submitting()"
            class="w-full py-2 bg-accent hover:bg-accent-dim text-on-accent font-medium rounded-lg
                   text-sm transition-colors disabled:opacity-50"
          >
            {{ t('auth.login') }}
          </button>
        </form>

        <p class="text-center text-sm text-text-secondary">
          {{ t('auth.no_account') }}
          <a routerLink="/register" class="text-accent hover:text-accent-dim">{{ t('auth.register') }}</a>
        </p>
      </div>
    </div>
  `,
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private transloco = inject(TranslocoService);
  protected theme = inject(ThemeService);

  username = '';
  password = '';
  error = signal<string | null>(null);
  submitting = signal(false);

  onSubmit() {
    this.submitting.set(true);
    this.error.set(null);
    this.auth.login(this.username, this.password).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.error.set(err.error?.detail || this.transloco.translate('auth.login_failed'));
        this.submitting.set(false);
      },
    });
  }
}
