export interface TradeSignalResponse {
  id: number;
  session_id: number;
  article_id: number | null;
  action: string;
  asset: string;
  conviction: number;
  reasoning: string;
  risk_score: number;
  model_used: string;
  action_taken: string;
  created_at: string;
}

export interface AnalyzeResponse {
  signal: TradeSignalResponse;
  articles_used: number;
}
