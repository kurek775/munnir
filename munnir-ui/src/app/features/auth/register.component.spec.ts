import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { provideTransloco } from '@jsverse/transloco';
import { TranslocoHttpLoader } from '../../transloco-loader';
import { RegisterComponent } from './register.component';

describe('RegisterComponent', () => {
  let component: RegisterComponent;
  let fixture: ComponentFixture<RegisterComponent>;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'dashboard', component: RegisterComponent }]),
        provideTransloco({
          config: { availableLangs: ['en'], defaultLang: 'en' },
          loader: TranslocoHttpLoader,
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture.detectChanges();

    httpMock.match('/assets/i18n/en.json').forEach((req) =>
      req.flush({
        auth: {
          register: 'Register', username: 'Username', email: 'Email',
          password: 'Password', confirm_password: 'Confirm', have_account: '',
          login: 'Log In', passwords_mismatch: 'Passwords do not match',
          register_failed: 'Registration failed',
        },
        app: { logo_alt: 'Munnir' },
      })
    );
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows error when passwords do not match', () => {
    component.username = 'user';
    component.email = 'user@test.com';
    component.password = 'password123';
    component.confirmPassword = 'different';

    component.onSubmit();

    expect(component.error()).toBeTruthy();
    expect(component.submitting()).toBe(false);
  });

  it('calls auth.register and navigates on success', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.username = 'newuser';
    component.email = 'new@test.com';
    component.password = 'password123';
    component.confirmPassword = 'password123';

    component.onSubmit();
    expect(component.submitting()).toBe(true);

    const regReq = httpMock.expectOne('/api/v1/auth/register');
    expect(regReq.request.body).toEqual({ username: 'newuser', email: 'new@test.com', password: 'password123' });
    regReq.flush({ access_token: 'token', refresh_token: 'refresh', token_type: 'bearer' });

    const meReq = httpMock.expectOne('/api/v1/users/me');
    meReq.flush({ id: 1, username: 'newuser', email: 'new@test.com', preferred_theme: 'dark', preferred_language: 'en' });

    expect(navigateSpy).toHaveBeenCalledWith(['/dashboard']);
  });

  it('shows API error on register failure', () => {
    component.username = 'dup';
    component.email = 'dup@test.com';
    component.password = 'password123';
    component.confirmPassword = 'password123';

    component.onSubmit();

    const regReq = httpMock.expectOne('/api/v1/auth/register');
    regReq.flush({ detail: 'Username already registered' }, { status: 409, statusText: 'Conflict' });

    expect(component.error()).toBe('Username already registered');
    expect(component.submitting()).toBe(false);
  });
});
