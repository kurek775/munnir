export interface TradeResponse {
  id: number;
  session_id: number;
  signal_id: number | null;
  position_id: number | null;
  side: string;
  asset: string;
  quantity: number;
  market_price: number;
  execution_price: number;
  slippage_factor: number;
  fee: number;
  total_cost: number;
  realized_pnl: number;
  created_at: string;
}
