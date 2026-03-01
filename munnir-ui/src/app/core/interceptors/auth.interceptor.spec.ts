import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('adds Authorization header for /api/ requests when token exists', () => {
    localStorage.setItem('access_token', 'my-token');
    http.get('/api/v1/test').subscribe();
    const req = httpMock.expectOne('/api/v1/test');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-token');
    req.flush({});
  });

  it('does not add Authorization header when no token', () => {
    http.get('/api/v1/test').subscribe();
    const req = httpMock.expectOne('/api/v1/test');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('does not add Authorization header for non-api URLs', () => {
    localStorage.setItem('access_token', 'my-token');
    http.get('/assets/i18n/en.json').subscribe();
    const req = httpMock.expectOne('/assets/i18n/en.json');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('clears tokens and navigates on 401 for non-auth endpoints', () => {
    localStorage.setItem('access_token', 'expired');
    localStorage.setItem('refresh_token', 'old');
    const navigateSpy = vi.spyOn(router, 'navigate');

    http.get('/api/v1/sessions').subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/sessions');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });

  it('does not clear tokens on 401 for auth endpoints', () => {
    localStorage.setItem('access_token', 'token');
    http.post('/api/v1/auth/login', {}).subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/auth/login');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem('access_token')).toBe('token');
  });
});
