export interface PositionResponse {
  id: number;
  session_id: number;
  asset: string;
  quantity: number;
  wapp: number;
  total_cost_basis: number;
  realized_pnl: number;
  is_open: boolean;
  opened_at: string;
  closed_at: string | null;
  updated_at: string;
}
