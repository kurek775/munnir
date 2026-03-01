import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark', 'light');
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ThemeService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('defaults to dark theme when no localStorage', () => {
    expect(service.theme()).toBe('dark');
  });

  it('reads theme from localStorage', () => {
    localStorage.setItem('theme', 'light');
    // Create a new instance to pick up localStorage
    const freshService = new ThemeService();
    expect(freshService.theme()).toBe('light');
  });

  it('init applies current theme to document', () => {
    service.init();
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('toggle switches theme and persists', () => {
    service.init();
    expect(service.theme()).toBe('dark');

    service.toggle();
    expect(service.theme()).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);

    // Verify API call to persist preference
    const req = httpMock.expectOne('/api/v1/users/me');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ preferred_theme: 'light' });
    req.flush({});
  });

  it('setTheme sets a specific theme', () => {
    service.setTheme('light');
    expect(service.theme()).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });
});
