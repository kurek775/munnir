import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideTransloco } from '@jsverse/transloco';
import { TranslocoHttpLoader } from '../../transloco-loader';
import { HelloComponent } from './hello.component';

describe('HelloComponent', () => {
  let component: HelloComponent;
  let fixture: ComponentFixture<HelloComponent>;
  let httpMock: HttpTestingController;

  const i18n = {
    hello: {
      title: 'Pipeline Test', subtitle: 'Angular -> FastAPI -> C++ -> SQLite',
      result_label: 'C++ Result', message_label: 'Message', timestamp_label: 'Timestamp',
      loading: 'Loading...', error: 'Error', language: 'Language',
    },
    app: { logo_alt: 'Munnir' },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HelloComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        provideTransloco({
          config: { availableLangs: ['en', 'cs'], defaultLang: 'en' },
          loader: TranslocoHttpLoader,
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HelloComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();

    httpMock.match('/assets/i18n/en.json').forEach((req) => req.flush(i18n));
  });

  afterEach(() => httpMock.verify());

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('starts in loading state', () => {
    expect(component.loading()).toBe(true);
    expect(component.data()).toBeNull();
    expect(component.error()).toBeNull();

    // Flush the pending hello request
    const req = httpMock.expectOne('/api/v1/hello');
    req.flush({ message: 'Hello', cpp_result: 42, created_at: '2026-01-01T00:00:00Z' });
  });

  it('sets data on successful API response', () => {
    const req = httpMock.expectOne('/api/v1/hello');
    req.flush({ message: 'Hello from Munnir!', cpp_result: 42, created_at: '2026-01-01T00:00:00Z' });

    expect(component.loading()).toBe(false);
    expect(component.data()).toEqual({
      message: 'Hello from Munnir!',
      cpp_result: 42,
      created_at: '2026-01-01T00:00:00Z',
    });
  });

  it('sets error on API failure', () => {
    const req = httpMock.expectOne('/api/v1/hello');
    req.error(new ProgressEvent('error'));

    expect(component.loading()).toBe(false);
    expect(component.error()).toBeTruthy();
  });

  it('switchLang changes active language', () => {
    // Flush initial request
    httpMock.expectOne('/api/v1/hello').flush({ message: 'Hello', cpp_result: 42, created_at: '' });

    expect(component.activeLang()).toBe('en');
    component.switchLang('cs');
    expect(component.activeLang()).toBe('cs');

    // Flush the cs.json load
    httpMock.match('/assets/i18n/cs.json').forEach((req) => req.flush(i18n));
  });
});
