import { Component, inject, signal, computed, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { CdkDropList, CdkDrag, CdkDragDrop, CdkDragHandle, CdkDragPlaceholder, moveItemInArray } from '@angular/cdk/drag-drop';
import { SessionService } from '../../core/services/session.service';
import { AuthService } from '../../core/services/auth.service';
import { WidgetOrderService } from '../../core/services/widget-order.service';
import { SessionResponse } from '../../core/models/session.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DecimalPipe, FormsModule, RouterLink, TranslocoModule, CdkDropList, CdkDrag, CdkDragHandle, CdkDragPlaceholder],
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
        <div cdkDropList (cdkDropListDropped)="onCardDrop($event)" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          @for (s of orderedSessions(); track s.id) {
            <div cdkDrag class="relative">
              <div *cdkDragPlaceholder class="bg-surface border-2 border-dashed border-accent/40 rounded-lg h-full min-h-[120px]"></div>
              <a [routerLink]="['/sessions', s.id]" class="block bg-surface border border-elevated rounded-lg p-5 hover:border-accent/30 transition-colors cursor-pointer">
                <div class="flex items-start justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <button
                      cdkDragHandle
                      type="button"
                      class="cursor-grab active:cursor-grabbing text-text-secondary/40 hover:text-text-secondary transition-colors"
                      [title]="t('common.drag_handle')"
                      (click)="$event.preventDefault(); $event.stopPropagation()"
                    >
                      <svg class="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="5" cy="3" r="1.5"/><circle cx="11" cy="3" r="1.5"/>
                        <circle cx="5" cy="8" r="1.5"/><circle cx="11" cy="8" r="1.5"/>
                        <circle cx="5" cy="13" r="1.5"/><circle cx="11" cy="13" r="1.5"/>
                      </svg>
                    </button>
                    <h3 class="font-semibold text-text-primary">{{ s.session_name }}</h3>
                  </div>
                  <div class="flex items-center gap-2">
                    @if (s.is_active) {
                      <span class="px-2 py-0.5 text-xs rounded-full bg-success-dim text-success">{{ t('session.active') }}</span>
                    } @else {
                      <span class="px-2 py-0.5 text-xs rounded-full bg-muted-dim text-muted">{{ t('session.inactive') }}</span>
                    }
                    <button
                      (click)="deleteSession(s.id); $event.preventDefault(); $event.stopPropagation()"
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
              </a>
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
  private auth = inject(AuthService);
  private widgetOrder = inject(WidgetOrderService);

  sessions = signal<SessionResponse[]>([]);
  showForm = signal(false);
  newName = '';
  newBalance = 10000;
  newRisk = 'medium';

  orderedSessions = computed(() => {
    const all = this.sessions();
    const userId = this.auth.currentUser()?.id;
    if (!userId || all.length === 0) return all;

    const saved = this.widgetOrder.getCardOrder(userId);
    if (!saved) return all;

    const byId = new Map(all.map(s => [s.id, s]));
    const ordered: SessionResponse[] = [];

    for (const id of saved) {
      const s = byId.get(id);
      if (s) {
        ordered.push(s);
        byId.delete(id);
      }
    }
    // Append any new sessions not in saved order
    for (const s of byId.values()) {
      ordered.push(s);
    }
    return ordered;
  });

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

  onCardDrop(event: CdkDragDrop<void>) {
    const userId = this.auth.currentUser()?.id;
    if (!userId) return;

    const reordered = [...this.orderedSessions()];
    moveItemInArray(reordered, event.previousIndex, event.currentIndex);
    this.sessions.set(reordered);
    this.widgetOrder.saveCardOrder(userId, reordered.map(s => s.id));
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
