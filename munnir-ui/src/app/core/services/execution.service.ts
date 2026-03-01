import { Injectable, inject } from '@angular/core';
import { ApiService } from './api.service';
import { SessionResponse } from '../models/session.model';
import { TradeResponse } from '../models/trade.model';
import { PositionResponse } from '../models/position.model';
import { TradeSignalResponse, AnalyzeResponse } from '../models/signal.model';
import { ExecuteSignalResponse, SkipSignalResponse, ClosePositionResponse } from '../models/execution.model';

@Injectable({ providedIn: 'root' })
export class ExecutionService {
  private api = inject(ApiService);

  getSession(id: number) {
    return this.api.get<SessionResponse>(`/api/v1/sessions/${id}`);
  }

  getTrades(sessionId: number) {
    return this.api.get<TradeResponse[]>(`/api/v1/sessions/${sessionId}/trades`);
  }

  getPositions(sessionId: number) {
    return this.api.get<PositionResponse[]>(`/api/v1/sessions/${sessionId}/positions`);
  }

  getSignals(sessionId: number) {
    return this.api.get<TradeSignalResponse[]>(`/api/v1/sessions/${sessionId}/signals`);
  }

  analyze(sessionId: number) {
    return this.api.post<AnalyzeResponse>(`/api/v1/sessions/${sessionId}/analyze`, {});
  }

  executeSignal(sessionId: number, signalId: number) {
    return this.api.post<ExecuteSignalResponse>(`/api/v1/sessions/${sessionId}/signals/${signalId}/execute`, {});
  }

  skipSignal(sessionId: number, signalId: number) {
    return this.api.post<SkipSignalResponse>(`/api/v1/sessions/${sessionId}/signals/${signalId}/skip`, {});
  }

  closePosition(sessionId: number, positionId: number) {
    return this.api.post<ClosePositionResponse>(`/api/v1/sessions/${sessionId}/positions/${positionId}/close`, {});
  }
}
