export interface SessionResponse {
  id: number;
  session_name: string;
  starting_balance: number;
  current_balance: number;
  risk_tolerance: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SessionCreate {
  session_name: string;
  starting_balance: number;
  risk_tolerance?: string;
}
