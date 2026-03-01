import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SessionService } from './session.service';
import { SessionResponse } from '../models/session.model';

describe('SessionService', () => {
  let service: SessionService;
  let httpMock: HttpTestingController;

  const mockSession: SessionResponse = {
    id: 1,
    session_name: 'Test Session',
    starting_balance: 10000,
    current_balance: 10000,
    risk_tolerance: 'medium',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SessionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getSessions fetches list from API', () => {
    service.getSessions().subscribe((sessions) => {
      expect(sessions).toEqual([mockSession]);
    });
    const req = httpMock.expectOne('/api/v1/sessions');
    expect(req.request.method).toBe('GET');
    req.flush([mockSession]);
  });

  it('createSession posts to API', () => {
    const data = { session_name: 'New', starting_balance: 5000, risk_tolerance: 'low' };
    service.createSession(data).subscribe((res) => {
      expect(res.session_name).toBe('New');
    });
    const req = httpMock.expectOne('/api/v1/sessions');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(data);
    req.flush({ ...mockSession, session_name: 'New' });
  });

  it('updateSession patches session by ID', () => {
    service.updateSession(1, { session_name: 'Renamed' }).subscribe();
    const req = httpMock.expectOne('/api/v1/sessions/1');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ session_name: 'Renamed' });
    req.flush({ ...mockSession, session_name: 'Renamed' });
  });

  it('deleteSession sends DELETE by ID', () => {
    service.deleteSession(1).subscribe();
    const req = httpMock.expectOne('/api/v1/sessions/1');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
