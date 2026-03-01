import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { ThemeService } from './theme.service';
import { TokenResponse, UserResponse } from '../models/auth.model';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let router: Router;

  const mockTokens: TokenResponse = {
    access_token: 'access-123',
    refresh_token: 'refresh-456',
    token_type: 'bearer',
  };

  const mockUser: UserResponse = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    preferred_theme: 'dark',
    preferred_language: 'en',
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('login stores tokens and fetches current user', () => {
    service.login('user', 'pass').subscribe();

    const loginReq = httpMock.expectOne('/api/v1/auth/login');
    expect(loginReq.request.method).toBe('POST');
    expect(loginReq.request.body).toEqual({ username: 'user', password: 'pass' });
    loginReq.flush(mockTokens);

    expect(localStorage.getItem('access_token')).toBe('access-123');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-456');

    // fetchCurrentUser fires after login
    const meReq = httpMock.expectOne('/api/v1/users/me');
    meReq.flush(mockUser);
    expect(service.currentUser()).toEqual(mockUser);
  });

  it('register stores tokens and fetches current user', () => {
    service.register('user', 'test@test.com', 'pass').subscribe();

    const regReq = httpMock.expectOne('/api/v1/auth/register');
    expect(regReq.request.method).toBe('POST');
    regReq.flush(mockTokens);

    expect(localStorage.getItem('access_token')).toBe('access-123');

    const meReq = httpMock.expectOne('/api/v1/users/me');
    meReq.flush(mockUser);
    expect(service.currentUser()).toEqual(mockUser);
  });

  it('logout clears tokens and navigates to /login', () => {
    localStorage.setItem('access_token', 'token');
    localStorage.setItem('refresh_token', 'refresh');
    service.currentUser.set(mockUser);
    const navigateSpy = vi.spyOn(router, 'navigate');

    service.logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(service.currentUser()).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });

  it('getToken returns stored token', () => {
    expect(service.getToken()).toBeNull();
    localStorage.setItem('access_token', 'abc');
    expect(service.getToken()).toBe('abc');
  });

  it('isLoggedIn is computed from getToken', () => {
    expect(service.isLoggedIn()).toBe(false);
    localStorage.setItem('access_token', 'abc');
    // isLoggedIn reads from localStorage via getToken, which is not reactive
    // but the computed signal will re-evaluate when accessed
    expect(service.isLoggedIn()).toBe(true);
  });
});
