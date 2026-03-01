import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { provideTransloco } from '@jsverse/transloco';
import { TranslocoHttpLoader } from '../../transloco-loader';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'dashboard', component: LoginComponent }]),
        provideTransloco({
          config: { availableLangs: ['en'], defaultLang: 'en' },
          loader: TranslocoHttpLoader,
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture.detectChanges();

    // Flush i18n load
    httpMock.match('/assets/i18n/en.json').forEach((req) =>
      req.flush({ auth: { login: 'Log In', username: 'Username', password: 'Password', no_account: '', register: 'Register', login_failed: 'Login failed' }, app: { logo_alt: 'Munnir' } })
    );
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('initializes with empty fields', () => {
    expect(component.username).toBe('');
    expect(component.password).toBe('');
    expect(component.error()).toBeNull();
    expect(component.submitting()).toBe(false);
  });

  it('calls auth.login on submit and navigates to dashboard on success', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.username = 'testuser';
    component.password = 'testpass123';

    component.onSubmit();
    expect(component.submitting()).toBe(true);

    const loginReq = httpMock.expectOne('/api/v1/auth/login');
    loginReq.flush({ access_token: 'token', refresh_token: 'refresh', token_type: 'bearer' });

    // fetchCurrentUser fires
    const meReq = httpMock.expectOne('/api/v1/users/me');
    meReq.flush({ id: 1, username: 'testuser', email: 'test@test.com', preferred_theme: 'dark', preferred_language: 'en' });

    expect(navigateSpy).toHaveBeenCalledWith(['/dashboard']);
  });

  it('shows error on login failure', () => {
    component.username = 'bad';
    component.password = 'bad';

    component.onSubmit();

    const loginReq = httpMock.expectOne('/api/v1/auth/login');
    loginReq.flush({ detail: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });

    expect(component.error()).toBe('Invalid credentials');
    expect(component.submitting()).toBe(false);
  });
});
