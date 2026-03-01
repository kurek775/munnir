import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideTransloco } from '@jsverse/transloco';
import { TranslocoHttpLoader } from '../../transloco-loader';
import { DashboardComponent } from './dashboard.component';
import { SessionResponse } from '../../core/models/session.model';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let httpMock: HttpTestingController;

  const mockSession: SessionResponse = {
    id: 1,
    session_name: 'Test',
    starting_balance: 10000,
    current_balance: 10000,
    risk_tolerance: 'medium',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  const i18n = {
    dashboard: { title: 'Trading Sessions', create_session: 'New Session', empty: 'No sessions', balance: 'Balance', risk: 'Risk Level' },
    session: { name: 'Name', starting_balance: 'Balance ($)', risk_low: 'Low', risk_medium: 'Medium', risk_high: 'High', active: 'Active', inactive: 'Inactive' },
    common: { save: 'Save', cancel: 'Cancel', delete: 'Delete', confirm_delete: 'Confirm delete?' },
    app: { logo_alt: 'Munnir' },
  };

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        provideTransloco({
          config: { availableLangs: ['en'], defaultLang: 'en' },
          loader: TranslocoHttpLoader,
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();

    // Flush i18n and initial sessions load
    httpMock.match('/assets/i18n/en.json').forEach((req) => req.flush(i18n));
    httpMock.expectOne('/api/v1/sessions').flush([]);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads sessions on init', () => {
    expect(component.sessions()).toEqual([]);
  });

  it('displays sessions when available', () => {
    component.sessions.set([mockSession]);
    fixture.detectChanges();
    expect(component.sessions().length).toBe(1);
    expect(component.sessions()[0].session_name).toBe('Test');
  });

  it('createSession posts and reloads', () => {
    component.showForm.set(true);
    component.newName = 'New Session';
    component.newBalance = 5000;
    component.newRisk = 'low';

    component.createSession();

    const createReq = httpMock.expectOne('/api/v1/sessions');
    expect(createReq.request.method).toBe('POST');
    expect(createReq.request.body).toEqual({
      session_name: 'New Session',
      starting_balance: 5000,
      risk_tolerance: 'low',
    });
    createReq.flush(mockSession);

    // Reloads sessions
    const listReq = httpMock.expectOne('/api/v1/sessions');
    listReq.flush([mockSession]);

    expect(component.showForm()).toBe(false);
    expect(component.newName).toBe('');
  });

  it('riskClass returns correct token classes', () => {
    expect(component.riskClass('low')).toContain('text-success');
    expect(component.riskClass('medium')).toContain('text-warning');
    expect(component.riskClass('high')).toContain('text-danger');
    expect(component.riskClass('unknown')).toContain('text-muted');
  });
});
