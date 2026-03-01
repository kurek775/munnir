import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

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

@Injectable({ providedIn: 'root' })
export class SessionService {
  private http = inject(HttpClient);

  getSessions() {
    return this.http.get<SessionResponse[]>('/api/v1/sessions');
  }

  createSession(data: SessionCreate) {
    return this.http.post<SessionResponse>('/api/v1/sessions', data);
  }

  updateSession(id: number, data: Partial<SessionCreate & { is_active: boolean }>) {
    return this.http.patch<SessionResponse>(`/api/v1/sessions/${id}`, data);
  }

  deleteSession(id: number) {
    return this.http.delete(`/api/v1/sessions/${id}`);
  }
}
