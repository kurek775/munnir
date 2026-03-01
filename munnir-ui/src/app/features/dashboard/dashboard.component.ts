import { Component, inject, signal, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { SessionService } from '../../core/services/session.service';
import { SessionResponse } from '../../core/models/session.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DecimalPipe, FormsModule, TranslocoModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="max-w-4xl mx-auto p-6" *transloco="let t">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-text-primary">{{ t('dashboard.title') }}</h1>
        <button
          (click)="showForm.set(!showForm())"
          class="px-4 py-2 bg-accent hover:bg-accent-dim text-on-accent font-medium rounded-lg text-sm transition-colors"
        >
          {{ t('dashboard.create_session') }}
        </button>
      </div>

      <!-- Create session form -->
      @if (showForm()) {
        <div class="bg-surface border border-elevated rounded-lg p-5 mb-6">
          <form (ngSubmit)="createSession()" class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">{{ t('session.name') }}</label>
              <input
                type="text"
                [(ngModel)]="newName"
                name="name"
                required
                class="w-full px-3 py-2 bg-base border border-elevated rounded-lg text-text-primary
                       focus:outline-none focus:border-accent text-sm"
              />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-text-secondary mb-1">{{ t('session.starting_balance') }}</label>
                <input
                  type="number"
                  [(ngModel)]="newBalance"
                  name="balance"
                  required
                  min="1"
                  class="w-full px-3 py-2 bg-base border border-elevated rounded-lg text-text-primary
                         focus:outline-none focus:border-accent text-sm"
                />
              </div>
              <div>
                <label class="block text-sm text-text-secondary mb-1">{{ t('dashboard.risk') }}</label>
                <select
                  [(ngModel)]="newRisk"
                  name="risk"
                  class="w-full px-3 py-2 bg-base border border-elevated rounded-lg text-text-primary
                         focus:outline-none focus:border-accent text-sm"
                >
                  <option value="low">{{ t('session.risk_low') }}</option>
                  <option value="medium">{{ t('session.risk_medium') }}</option>
                  <option value="high">{{ t('session.risk_high') }}</option>
                </select>
              </div>
            </div>
            <div class="flex gap-2 justify-end">
              <button
                type="button"
                (click)="showForm.set(false)"
                class="px-4 py-2 bg-elevated hover:bg-elevated/80 text-text-secondary rounded-lg text-sm transition-colors"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-accent hover:bg-accent-dim text-on-accent font-medium rounded-lg text-sm transition-colors"
              >
                {{ t('common.save') }}
              </button>
            </div>
          </form>
        </div>
      }

      <!-- Session cards -->
      @if (sessions().length === 0) {
        <div class="text-center py-16">
          <div class="text-6xl mb-4 opacity-20">&#x1F4C8;</div>
          <p class="text-text-secondary">{{ t('dashboard.empty') }}</p>
        </div>
      } @else {
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          @for (s of sessions(); track s.id) {
            <div class="bg-surface border border-elevated rounded-lg p-5 hover:border-accent/30 transition-colors">
              <div class="flex items-start justify-between mb-3">
                <h3 class="font-semibold text-text-primary">{{ s.session_name }}</h3>
                <div class="flex items-center gap-2">
                  @if (s.is_active) {
                    <span class="px-2 py-0.5 text-xs rounded-full bg-success-dim text-success">{{ t('session.active') }}</span>
                  } @else {
                    <span class="px-2 py-0.5 text-xs rounded-full bg-muted-dim text-muted">{{ t('session.inactive') }}</span>
                  }
                  <button
                    (click)="deleteSession(s.id)"
                    class="text-danger/60 hover:text-danger text-sm transition-colors"
                    [title]="t('common.delete')"
                  >&#x2715;</button>
                </div>
              </div>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-text-secondary">{{ t('dashboard.balance') }}</span>
                  <span class="text-accent font-mono font-medium">\${{ s.current_balance | number:'1.2-2' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-text-secondary">{{ t('dashboard.risk') }}</span>
                  <span
                    class="px-2 py-0.5 text-xs rounded-full"
                    [class]="riskClass(s.risk_tolerance)"
                  >{{ t('session.risk_' + s.risk_tolerance) }}</span>
                </div>
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  private sessionService = inject(SessionService);
  private transloco = inject(TranslocoService);

  sessions = signal<SessionResponse[]>([]);
  showForm = signal(false);
  newName = '';
  newBalance = 10000;
  newRisk = 'medium';

  ngOnInit() {
    this.loadSessions();
  }

  loadSessions() {
    this.sessionService.getSessions().subscribe({
      next: (data) => this.sessions.set(data),
    });
  }

  createSession() {
    this.sessionService.createSession({
      session_name: this.newName,
      starting_balance: this.newBalance,
      risk_tolerance: this.newRisk,
    }).subscribe({
      next: () => {
        this.showForm.set(false);
        this.newName = '';
        this.newBalance = 10000;
        this.newRisk = 'medium';
        this.loadSessions();
      },
    });
  }

  deleteSession(id: number) {
    if (!window.confirm(this.transloco.translate('common.confirm_delete'))) {
      return;
    }
    this.sessionService.deleteSession(id).subscribe({
      next: () => this.loadSessions(),
    });
  }

  riskClass(risk: string): string {
    switch (risk) {
      case 'low': return 'bg-success-dim text-success';
      case 'medium': return 'bg-warning-dim text-warning';
      case 'high': return 'bg-danger-dim text-danger';
      default: return 'bg-muted-dim text-muted';
    }
  }
}
