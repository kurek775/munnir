import { Component, inject, signal, computed, OnInit, effect, ChangeDetectionStrategy } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DecimalPipe, DatePipe, PercentPipe } from '@angular/common';
import { TranslocoModule } from '@jsverse/transloco';
import { NgxEchartsDirective, provideEchartsCore } from 'ngx-echarts';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, DataZoomComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsCoreOption } from 'echarts/core';
import { ExecutionService } from '../../core/services/execution.service';
import { ThemeService } from '../../core/services/theme.service';
import { SessionResponse } from '../../core/models/session.model';
import { TradeResponse } from '../../core/models/trade.model';
import { PositionResponse } from '../../core/models/position.model';
import { TradeSignalResponse } from '../../core/models/signal.model';

echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, MarkLineComponent, CanvasRenderer]);

@Component({
  selector: 'app-session-detail',
  standalone: true,
  imports: [DecimalPipe, DatePipe, PercentPipe, RouterLink, TranslocoModule, NgxEchartsDirective],
  providers: [provideEchartsCore({ echarts })],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="max-w-5xl mx-auto p-6" *transloco="let t">

      @if (loading()) {
        <div class="text-center py-16">
          <div class="inline-block w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
        </div>
      } @else if (session()) {
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <a routerLink="/dashboard" class="text-text-secondary hover:text-text-primary transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
            </svg>
          </a>
          <h1 class="text-2xl font-bold text-text-primary">{{ session()!.session_name }}</h1>
          @if (session()!.is_active) {
            <span class="px-2 py-0.5 text-xs rounded-full bg-success-dim text-success">{{ t('session.active') }}</span>
          } @else {
            <span class="px-2 py-0.5 text-xs rounded-full bg-muted-dim text-muted">{{ t('session.inactive') }}</span>
          }
        </div>

        <!-- Stats row -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-surface border border-elevated rounded-lg p-4">
            <div class="text-xs text-text-secondary mb-1">{{ t('detail.current_balance') }}</div>
            <div class="text-lg font-mono font-semibold text-accent">\${{ session()!.current_balance | number:'1.2-2' }}</div>
          </div>
          <div class="bg-surface border border-elevated rounded-lg p-4">
            <div class="text-xs text-text-secondary mb-1">{{ t('detail.pnl') }}</div>
            <div class="text-lg font-mono font-semibold" [class]="pnl() >= 0 ? 'text-success' : 'text-danger'">
              {{ pnl() >= 0 ? '+' : '' }}\${{ pnl() | number:'1.2-2' }}
            </div>
          </div>
          <div class="bg-surface border border-elevated rounded-lg p-4">
            <div class="text-xs text-text-secondary mb-1">{{ t('detail.pnl_percent') }}</div>
            <div class="text-lg font-mono font-semibold" [class]="pnl() >= 0 ? 'text-success' : 'text-danger'">
              {{ pnl() >= 0 ? '+' : '' }}{{ pnlPercent() | number:'1.2-2' }}%
            </div>
          </div>
          <div class="bg-surface border border-elevated rounded-lg p-4">
            <div class="text-xs text-text-secondary mb-1">{{ t('detail.risk_tolerance') }}</div>
            <span class="px-2 py-0.5 text-xs rounded-full" [class]="riskClass(session()!.risk_tolerance)">
              {{ t('session.risk_' + session()!.risk_tolerance) }}
            </span>
          </div>
        </div>

        <!-- Balance chart -->
        <div class="bg-surface border border-elevated rounded-lg p-5 mb-6">
          <h2 class="text-sm font-semibold text-text-primary mb-3">{{ t('detail.chart_title') }}</h2>
          @if (trades().length === 0) {
            <div class="flex items-center justify-center h-[320px] text-text-secondary text-sm">
              {{ t('detail.chart_empty') }}
            </div>
          } @else {
            <div echarts [options]="chartOptions()" class="h-[320px]"></div>
          }
        </div>

        <!-- AI Signals -->
        <div class="bg-surface border border-elevated rounded-lg p-5 mb-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-text-primary">{{ t('detail.signals_title') }}</h2>
            <button
              (click)="analyzeNews()"
              [disabled]="analyzing()"
              class="px-3 py-1.5 bg-accent hover:bg-accent-dim text-on-accent font-medium rounded-lg text-xs transition-colors disabled:opacity-50"
            >
              {{ analyzing() ? t('detail.analyzing') : t('detail.analyze_btn') }}
            </button>
          </div>

          <!-- Pending signals -->
          @if (pendingSignals().length === 0) {
            <p class="text-text-secondary text-sm py-4 text-center">{{ t('detail.pending_empty') }}</p>
          } @else {
            <div class="space-y-3 mb-4">
              @for (sig of pendingSignals(); track sig.id) {
                <div class="border border-elevated rounded-lg p-4">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 text-xs font-semibold rounded-full" [class]="actionClass(sig.action)">
                      {{ sig.action }}
                    </span>
                    <span class="font-mono font-semibold text-text-primary text-sm">{{ sig.asset }}</span>
                  </div>
                  <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                    <div>
                      <span class="text-text-secondary">{{ t('detail.signal_conviction') }}: </span>
                      <span class="text-text-primary font-mono">{{ sig.conviction | number:'1.0-0' }}%</span>
                    </div>
                    <div>
                      <span class="text-text-secondary">{{ t('detail.signal_risk') }}: </span>
                      <span class="text-text-primary font-mono">{{ sig.risk_score | number:'1.1-1' }}</span>
                    </div>
                  </div>
                  <p class="text-xs text-text-secondary mb-3 leading-relaxed">{{ sig.reasoning }}</p>
                  <div class="flex gap-2">
                    <button
                      (click)="executeSignal(sig.id)"
                      [disabled]="executing()"
                      class="px-3 py-1 bg-success/20 hover:bg-success/30 text-success font-medium rounded text-xs transition-colors disabled:opacity-50"
                    >
                      {{ executing() ? t('detail.executing') : t('detail.execute_btn') }}
                    </button>
                    <button
                      (click)="skipSignal(sig.id)"
                      [disabled]="executing()"
                      class="px-3 py-1 bg-muted-dim hover:bg-muted/30 text-muted font-medium rounded text-xs transition-colors disabled:opacity-50"
                    >
                      {{ t('detail.skip_btn') }}
                    </button>
                  </div>
                </div>
              }
            </div>
          }

          <!-- Signal history -->
          @if (historySignals().length > 0) {
            <details class="mt-2">
              <summary class="text-xs text-text-secondary cursor-pointer hover:text-text-primary">
                {{ t('detail.signal_history') }} ({{ historySignals().length }})
              </summary>
              <div class="mt-2 space-y-2">
                @for (sig of historySignals(); track sig.id) {
                  <div class="flex items-center gap-2 text-xs border border-elevated rounded p-2 opacity-70">
                    <span class="px-2 py-0.5 rounded-full" [class]="actionClass(sig.action)">{{ sig.action }}</span>
                    <span class="font-mono text-text-primary">{{ sig.asset }}</span>
                    <span class="ml-auto px-2 py-0.5 rounded-full" [class]="sig.action_taken === 'executed' ? 'bg-success-dim text-success' : 'bg-muted-dim text-muted'">
                      {{ sig.action_taken === 'executed' ? t('detail.signal_executed') : t('detail.signal_skipped') }}
                    </span>
                  </div>
                }
              </div>
            </details>
          }
        </div>

        <!-- Positions -->
        <div class="bg-surface border border-elevated rounded-lg p-5 mb-6">
          <h2 class="text-sm font-semibold text-text-primary mb-4">{{ t('detail.positions_title') }}</h2>
          @if (openPositions().length === 0) {
            <p class="text-text-secondary text-sm py-4 text-center">{{ t('detail.positions_empty') }}</p>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-text-secondary border-b border-elevated">
                    <th class="pb-2 pr-4">{{ t('detail.pos_asset') }}</th>
                    <th class="pb-2 pr-4 text-right">{{ t('detail.pos_quantity') }}</th>
                    <th class="pb-2 pr-4 text-right">{{ t('detail.pos_avg_price') }}</th>
                    <th class="pb-2 pr-4 text-right">{{ t('detail.pos_cost_basis') }}</th>
                    <th class="pb-2 pr-4 text-right">{{ t('detail.pos_pnl') }}</th>
                    <th class="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  @for (pos of openPositions(); track pos.id) {
                    <tr class="border-b border-elevated/50">
                      <td class="py-2 pr-4 font-mono font-semibold text-text-primary">{{ pos.asset }}</td>
                      <td class="py-2 pr-4 text-right font-mono text-text-primary">{{ pos.quantity | number:'1.2-4' }}</td>
                      <td class="py-2 pr-4 text-right font-mono text-text-primary">\${{ pos.wapp | number:'1.2-2' }}</td>
                      <td class="py-2 pr-4 text-right font-mono text-text-primary">\${{ pos.total_cost_basis | number:'1.2-2' }}</td>
                      <td class="py-2 pr-4 text-right font-mono" [class]="pos.realized_pnl >= 0 ? 'text-success' : 'text-danger'">
                        {{ pos.realized_pnl >= 0 ? '+' : '' }}\${{ pos.realized_pnl | number:'1.2-2' }}
                      </td>
                      <td class="py-2 text-right">
                        <button
                          (click)="closePosition(pos.id)"
                          [disabled]="closingPositionId() === pos.id"
                          class="px-2 py-1 bg-danger/20 hover:bg-danger/30 text-danger font-medium rounded text-xs transition-colors disabled:opacity-50"
                        >
                          {{ closingPositionId() === pos.id ? t('detail.pos_closing') : t('detail.pos_close') }}
                        </button>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }

          <!-- Closed positions -->
          @if (closedPositions().length > 0) {
            <details class="mt-4">
              <summary class="text-xs text-text-secondary cursor-pointer hover:text-text-primary">
                {{ t('detail.closed_positions') }} ({{ closedPositions().length }})
              </summary>
              <div class="mt-2 overflow-x-auto">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="text-left text-text-secondary border-b border-elevated">
                      <th class="pb-2 pr-4">{{ t('detail.pos_asset') }}</th>
                      <th class="pb-2 pr-4 text-right">{{ t('detail.pos_quantity') }}</th>
                      <th class="pb-2 pr-4 text-right">{{ t('detail.pos_avg_price') }}</th>
                      <th class="pb-2 pr-4 text-right">{{ t('detail.pos_cost_basis') }}</th>
                      <th class="pb-2 text-right">{{ t('detail.pos_pnl') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (pos of closedPositions(); track pos.id) {
                      <tr class="border-b border-elevated/50 opacity-60">
                        <td class="py-2 pr-4 font-mono text-text-primary">{{ pos.asset }}</td>
                        <td class="py-2 pr-4 text-right font-mono text-text-primary">{{ pos.quantity | number:'1.2-4' }}</td>
                        <td class="py-2 pr-4 text-right font-mono text-text-primary">\${{ pos.wapp | number:'1.2-2' }}</td>
                        <td class="py-2 pr-4 text-right font-mono text-text-primary">\${{ pos.total_cost_basis | number:'1.2-2' }}</td>
                        <td class="py-2 text-right font-mono" [class]="pos.realized_pnl >= 0 ? 'text-success' : 'text-danger'">
                          {{ pos.realized_pnl >= 0 ? '+' : '' }}\${{ pos.realized_pnl | number:'1.2-2' }}
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </details>
          }
        </div>

        <!-- Trade History -->
        <div class="bg-surface border border-elevated rounded-lg p-5">
          <h2 class="text-sm font-semibold text-text-primary mb-4">{{ t('detail.trades_title') }}</h2>
          @if (trades().length === 0) {
            <p class="text-text-secondary text-sm py-4 text-center">{{ t('detail.trades_empty') }}</p>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-text-secondary border-b border-elevated">
                    <th class="pb-2 pr-3">{{ t('detail.trade_date') }}</th>
                    <th class="pb-2 pr-3">{{ t('detail.trade_side') }}</th>
                    <th class="pb-2 pr-3">{{ t('detail.trade_asset') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_qty') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_market') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_exec') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_slippage') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_fee') }}</th>
                    <th class="pb-2 pr-3 text-right">{{ t('detail.trade_total') }}</th>
                    <th class="pb-2 text-right">{{ t('detail.trade_pnl') }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (tr of sortedTrades(); track tr.id) {
                    <tr class="border-b border-elevated/50">
                      <td class="py-2 pr-3 font-mono text-text-secondary">{{ tr.created_at | date:'short' }}</td>
                      <td class="py-2 pr-3">
                        <span class="px-1.5 py-0.5 rounded text-xs font-semibold" [class]="tr.side === 'BUY' ? 'bg-success-dim text-success' : 'bg-danger-dim text-danger'">
                          {{ tr.side }}
                        </span>
                      </td>
                      <td class="py-2 pr-3 font-mono font-semibold text-text-primary">{{ tr.asset }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-primary">{{ tr.quantity | number:'1.2-4' }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-primary">\${{ tr.market_price | number:'1.2-2' }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-primary">\${{ tr.execution_price | number:'1.2-2' }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-secondary">{{ tr.slippage_factor | percent:'1.2-2' }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-secondary">\${{ tr.fee | number:'1.2-2' }}</td>
                      <td class="py-2 pr-3 text-right font-mono text-text-primary">\${{ tr.total_cost | number:'1.2-2' }}</td>
                      <td class="py-2 text-right font-mono" [class]="tr.realized_pnl >= 0 ? 'text-success' : 'text-danger'">
                        {{ tr.realized_pnl !== 0 ? (tr.realized_pnl >= 0 ? '+' : '') : '' }}\${{ tr.realized_pnl | number:'1.2-2' }}
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class SessionDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private exec = inject(ExecutionService);
  private themeService = inject(ThemeService);

  session = signal<SessionResponse | null>(null);
  trades = signal<TradeResponse[]>([]);
  positions = signal<PositionResponse[]>([]);
  signals = signal<TradeSignalResponse[]>([]);
  loading = signal(true);
  analyzing = signal(false);
  executing = signal(false);
  closingPositionId = signal<number | null>(null);

  pnl = computed(() => {
    const s = this.session();
    return s ? s.current_balance - s.starting_balance : 0;
  });

  pnlPercent = computed(() => {
    const s = this.session();
    return s && s.starting_balance > 0 ? (this.pnl() / s.starting_balance) * 100 : 0;
  });

  openPositions = computed(() => this.positions().filter(p => p.is_open));
  closedPositions = computed(() => this.positions().filter(p => !p.is_open));
  pendingSignals = computed(() => this.signals().filter(s => s.action_taken === 'pending'));
  historySignals = computed(() => this.signals().filter(s => s.action_taken !== 'pending'));
  sortedTrades = computed(() => [...this.trades()].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));

  chartOptions = computed<EChartsCoreOption>(() => {
    const isDark = this.themeService.theme() === 'dark';
    const textColor = isDark ? '#9CA3AF' : '#6B7280';
    const lineColor = isDark ? '#1F2937' : '#E5E7EB';
    const s = this.session();
    const sorted = [...this.trades()].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    if (!s || sorted.length === 0) return {};

    const startBalance = s.starting_balance;
    let balance = startBalance;
    const data: [string, number][] = [[sorted[0].created_at, startBalance]];

    for (const trade of sorted) {
      if (trade.side === 'BUY') {
        balance -= trade.total_cost;
      } else {
        balance += trade.total_cost;
      }
      data.push([trade.created_at, Math.round(balance * 100) / 100]);
    }

    return {
      tooltip: { trigger: 'axis' },
      grid: { left: 60, right: 20, top: 20, bottom: 60 },
      xAxis: {
        type: 'time',
        axisLabel: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: lineColor } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor, fontSize: 10, formatter: '${value}' },
        splitLine: { lineStyle: { color: lineColor } },
      },
      dataZoom: [{ type: 'inside' }],
      series: [{
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#F59E0B', width: 2 },
        itemStyle: { color: '#F59E0B' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,158,11,0.3)' },
          { offset: 1, color: 'rgba(245,158,11,0.02)' },
        ])},
        markLine: {
          silent: true,
          data: [{ yAxis: startBalance, label: { formatter: 'Start', color: textColor, fontSize: 10 }, lineStyle: { color: '#6B7280', type: 'dashed' } }],
        },
        data,
      }],
    };
  });

  constructor() {
    // Rebuild chart on theme change by depending on themeService.theme() in chartOptions computed
    effect(() => {
      this.themeService.theme();
    });
  }

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadAll(id);
  }

  private loadAll(id: number) {
    this.loading.set(true);
    this.exec.getSession(id).subscribe({
      next: (s) => {
        this.session.set(s);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.exec.getTrades(id).subscribe({ next: (t) => this.trades.set(t) });
    this.exec.getPositions(id).subscribe({ next: (p) => this.positions.set(p) });
    this.exec.getSignals(id).subscribe({ next: (s) => this.signals.set(s) });
  }

  analyzeNews() {
    const id = this.session()?.id;
    if (!id) return;
    this.analyzing.set(true);
    this.exec.analyze(id).subscribe({
      next: (res) => {
        this.signals.update(sigs => [...sigs, res.signal]);
        this.analyzing.set(false);
      },
      error: () => this.analyzing.set(false),
    });
  }

  executeSignal(signalId: number) {
    const id = this.session()?.id;
    if (!id) return;
    this.executing.set(true);
    this.exec.executeSignal(id, signalId).subscribe({
      next: (res) => {
        this.session.update(s => s ? { ...s, current_balance: res.new_balance } : s);
        this.trades.update(t => [...t, res.trade]);
        this.positions.update(p => {
          const idx = p.findIndex(x => x.id === res.position.id);
          return idx >= 0 ? p.map(x => x.id === res.position.id ? res.position : x) : [...p, res.position];
        });
        this.signals.update(sigs => sigs.map(s => s.id === signalId ? { ...s, action_taken: 'executed' } : s));
        this.executing.set(false);
      },
      error: () => this.executing.set(false),
    });
  }

  skipSignal(signalId: number) {
    const id = this.session()?.id;
    if (!id) return;
    this.executing.set(true);
    this.exec.skipSignal(id, signalId).subscribe({
      next: () => {
        this.signals.update(sigs => sigs.map(s => s.id === signalId ? { ...s, action_taken: 'skipped' } : s));
        this.executing.set(false);
      },
      error: () => this.executing.set(false),
    });
  }

  closePosition(positionId: number) {
    const id = this.session()?.id;
    if (!id) return;
    this.closingPositionId.set(positionId);
    this.exec.closePosition(id, positionId).subscribe({
      next: (res) => {
        this.session.update(s => s ? { ...s, current_balance: res.new_balance } : s);
        this.trades.update(t => [...t, res.trade]);
        this.positions.update(p => p.map(x => x.id === res.position.id ? res.position : x));
        this.closingPositionId.set(null);
      },
      error: () => this.closingPositionId.set(null),
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

  actionClass(action: string): string {
    switch (action) {
      case 'BUY': return 'bg-success-dim text-success';
      case 'SELL': return 'bg-danger-dim text-danger';
      case 'HOLD': return 'bg-warning-dim text-warning';
      default: return 'bg-muted-dim text-muted';
    }
  }
}
