import { Component, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink, TranslocoModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen flex items-center justify-center bg-base p-8">
      <div class="max-w-sm w-full space-y-8" *transloco="let t">
        <div class="text-center">
          <img src="assets/logo.svg" alt="Munnir" class="h-14 mx-auto" />
          <h1 class="text-xl font-bold text-text-primary mt-4">{{ t('auth.register') }}</h1>
        </div>

        @if (error()) {
          <div class="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
            <p class="text-red-400 text-sm">{{ error() }}</p>
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
            <label class="block text-sm text-text-secondary mb-1">{{ t('auth.email') }}</label>
            <input
              type="email"
              [(ngModel)]="email"
              name="email"
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
          <div>
            <label class="block text-sm text-text-secondary mb-1">{{ t('auth.confirm_password') }}</label>
            <input
              type="password"
              [(ngModel)]="confirmPassword"
              name="confirmPassword"
              required
              class="w-full px-3 py-2 bg-surface border border-elevated rounded-lg text-text-primary
                     focus:outline-none focus:border-accent text-sm"
            />
          </div>
          <button
            type="submit"
            [disabled]="submitting()"
            class="w-full py-2 bg-accent hover:bg-accent-dim text-gray-900 font-medium rounded-lg
                   text-sm transition-colors disabled:opacity-50"
          >
            {{ t('auth.register') }}
          </button>
        </form>

        <p class="text-center text-sm text-text-secondary">
          {{ t('auth.have_account') }}
          <a routerLink="/login" class="text-accent hover:text-accent-dim">{{ t('auth.login') }}</a>
        </p>
      </div>
    </div>
  `,
})
export class RegisterComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private transloco = inject(TranslocoService);

  username = '';
  email = '';
  password = '';
  confirmPassword = '';
  error = signal<string | null>(null);
  submitting = signal(false);

  onSubmit() {
    if (this.password !== this.confirmPassword) {
      this.error.set(this.transloco.translate('auth.passwords_mismatch'));
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.auth.register(this.username, this.email, this.password).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.error.set(err.error?.detail || 'Registration failed');
        this.submitting.set(false);
      },
    });
  }
}
