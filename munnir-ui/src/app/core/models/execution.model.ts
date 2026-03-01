import { TradeResponse } from './trade.model';
import { PositionResponse } from './position.model';

export interface ExecuteSignalResponse {
  trade: TradeResponse;
  position: PositionResponse;
  new_balance: number;
}

export interface HoldExecuteResponse {
  signal_id: number;
  action: string;
  action_taken: string;
}

export interface SkipSignalResponse {
  signal_id: number;
  action_taken: string;
}

export interface ClosePositionResponse {
  trade: TradeResponse;
  position: PositionResponse;
  new_balance: number;
}
