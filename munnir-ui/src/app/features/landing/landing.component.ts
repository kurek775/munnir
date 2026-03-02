import { Component, ChangeDetectionStrategy, inject, OnInit, OnDestroy, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [RouterLink, TranslocoModule],
  templateUrl: './landing.html',
  styleUrl: './landing.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingComponent implements OnInit, OnDestroy {
  protected theme = inject(ThemeService);
  private transloco = inject(TranslocoService);

  readonly tickerItems = [
    { symbol: 'AAPL', price: '189.24', change: '+1.42%' },
    { symbol: 'TSLA', price: '248.50', change: '-0.87%' },
    { symbol: 'NVDA', price: '875.30', change: '+3.21%' },
    { symbol: 'XOM', price: '104.18', change: '+0.65%' },
    { symbol: 'LMT', price: '452.90', change: '+2.10%' },
    { symbol: 'BA', price: '178.44', change: '-1.33%' },
    { symbol: 'GLD', price: '192.55', change: '+0.48%' },
    { symbol: 'JPM', price: '198.70', change: '+0.92%' },
  ];

  readonly balancePoints = signal<{ x: number; y: number }[]>([]);
  private animFrame = 0;

  ngOnInit() {
    this.theme.init();
    this.generateBalanceCurve();
  }

  ngOnDestroy() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
  }

  private generateBalanceCurve() {
    const points: { x: number; y: number }[] = [];
    let balance = 10000;
    for (let i = 0; i <= 60; i++) {
      const drift = 15 + Math.random() * 30;
      const noise = (Math.random() - 0.4) * 80;
      balance += drift + noise;
      points.push({ x: (i / 60) * 100, y: balance });
    }
    const min = Math.min(...points.map(p => p.y));
    const max = Math.max(...points.map(p => p.y));
    const range = max - min || 1;
    const normalized = points.map(p => ({
      x: p.x,
      y: 90 - ((p.y - min) / range) * 70,
    }));
    this.balancePoints.set(normalized);
  }

  get balancePath(): string {
    const pts = this.balancePoints();
    if (!pts.length) return '';
    return 'M ' + pts.map(p => `${p.x},${p.y}`).join(' L ');
  }

  switchLang(lang: string) {
    this.transloco.setActiveLang(lang);
  }

  getActiveLang() {
    return this.transloco.getActiveLang();
  }

  get balanceAreaPath(): string {
    const pts = this.balancePoints();
    if (!pts.length) return '';
    return this.balancePath + ` L 100,95 L 0,95 Z`;
  }
}
