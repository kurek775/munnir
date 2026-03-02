import { Injectable, inject } from '@angular/core';
import { ApiService } from './api.service';
import { SessionResponse, SessionCreate } from '../models/session.model';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private api = inject(ApiService);

  getSessions() {
    return this.api.get<SessionResponse[]>('/api/v1/sessions');
  }

  createSession(data: SessionCreate) {
    return this.api.post<SessionResponse>('/api/v1/sessions', data);
  }

  updateSession(id: number, data: Partial<SessionCreate & { is_active: boolean; auto_pilot: boolean; auto_pilot_interval_minutes: number }>) {
    return this.api.patch<SessionResponse>(`/api/v1/sessions/${id}`, data);
  }

  deleteSession(id: number) {
    return this.api.delete(`/api/v1/sessions/${id}`);
  }
}
