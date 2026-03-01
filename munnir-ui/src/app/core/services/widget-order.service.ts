import { Injectable } from '@angular/core';

export type WidgetPanelId = 'chart' | 'signals' | 'positions' | 'trades';
export const DEFAULT_PANEL_ORDER: WidgetPanelId[] = ['chart', 'signals', 'positions', 'trades'];

@Injectable({ providedIn: 'root' })
export class WidgetOrderService {
  getCardOrder(userId: number): number[] | null {
    const raw = localStorage.getItem(`munnir_card_order_${userId}`);
    return raw ? JSON.parse(raw) : null;
  }

  saveCardOrder(userId: number, sessionIds: number[]): void {
    localStorage.setItem(`munnir_card_order_${userId}`, JSON.stringify(sessionIds));
  }

  getPanelOrder(sessionId: number): WidgetPanelId[] {
    const raw = localStorage.getItem(`munnir_widget_order_${sessionId}`);
    if (!raw) return [...DEFAULT_PANEL_ORDER];
    const parsed: WidgetPanelId[] = JSON.parse(raw);
    const missing = DEFAULT_PANEL_ORDER.filter(p => !parsed.includes(p));
    return [...parsed, ...missing];
  }

  savePanelOrder(sessionId: number, order: WidgetPanelId[]): void {
    localStorage.setItem(`munnir_widget_order_${sessionId}`, JSON.stringify(order));
  }
}
