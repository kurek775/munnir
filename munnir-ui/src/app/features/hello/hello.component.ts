import { Component, inject, signal, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { ApiService } from '../../core/services/api.service';
import { HelloResponse } from '../../core/models/hello.model';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-hello',
  standalone: true,
  imports: [TranslocoModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen flex items-center justify-center bg-base p-8">
      <div class="max-w-md w-full space-y-8">

        <!-- Logo -->
        <div class="text-center" *transloco="let t">
          <img [src]="theme.logoSrc()" [attr.alt]="t('app.logo_alt')" class="h-14 mx-auto" />
          <p class="text-text-secondary mt-4 text-xs tracking-widest uppercase">
            {{ t('hello.subtitle') }}
          </p>
        </div>

        <!-- Language switcher -->
        <div class="flex justify-center items-center gap-2" *transloco="let t">
          <span class="text-xs text-text-secondary uppercase tracking-wider">{{ t('hello.language') }}</span>
          <button
            class="px-2.5 py-1 text-xs font-medium rounded transition-colors"
            [class]="activeLang() === 'en'
              ? 'bg-accent text-on-accent'
              : 'bg-elevated text-text-secondary hover:text-text-primary'"
            (click)="switchLang('en')"
          >EN</button>
          <button
            class="px-2.5 py-1 text-xs font-medium rounded transition-colors"
            [class]="activeLang() === 'cs'
              ? 'bg-accent text-on-accent'
              : 'bg-elevated text-text-secondary hover:text-text-primary'"
            (click)="switchLang('cs')"
          >CS</button>
        </div>

        <!-- Content area -->
        @if (loading()) {
          <div class="text-center py-8">
            <div class="inline-block w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
            <p class="text-text-secondary mt-3 text-sm" *transloco="let t">{{ t('hello.loading') }}</p>
          </div>
        } @else if (error()) {
          <div class="bg-danger-dim border border-danger/20 rounded-lg p-4 text-center">
            <p class="text-danger text-sm" *transloco="let t">{{ t('hello.error') }}: {{ error() }}</p>
          </div>
        } @else if (data()) {
          <div class="bg-surface border border-elevated rounded-lg divide-y divide-elevated" *transloco="let t">
            <div class="flex justify-between items-center px-5 py-4">
              <span class="text-text-secondary text-sm">{{ t('hello.result_label') }}</span>
              <span class="text-accent font-mono text-xl font-bold">{{ data()!.cpp_result }}</span>
            </div>
            <div class="flex justify-between items-center px-5 py-4">
              <span class="text-text-secondary text-sm">{{ t('hello.message_label') }}</span>
              <span class="text-text-primary text-sm">{{ data()!.message }}</span>
            </div>
            <div class="flex justify-between items-center px-5 py-4">
              <span class="text-text-secondary text-sm">{{ t('hello.timestamp_label') }}</span>
              <span class="text-text-secondary text-xs font-mono">{{ data()!.created_at }}</span>
            </div>
          </div>
        }

      </div>
    </div>
  `,
})
export class HelloComponent implements OnInit {
  private api = inject(ApiService);
  private transloco = inject(TranslocoService);
  protected theme = inject(ThemeService);

  data = signal<HelloResponse | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);
  activeLang = signal(this.transloco.getActiveLang());

  ngOnInit() {
    this.api.get<HelloResponse>('/api/v1/hello').subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message);
        this.loading.set(false);
      },
    });
  }

  switchLang(lang: string) {
    this.transloco.setActiveLang(lang);
    this.activeLang.set(lang);
  }
}
