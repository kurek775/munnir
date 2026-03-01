import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('get() delegates to HttpClient.get', () => {
    service.get<{ ok: boolean }>('/api/test').subscribe((res) => {
      expect(res).toEqual({ ok: true });
    });
    const req = httpMock.expectOne('/api/test');
    expect(req.request.method).toBe('GET');
    req.flush({ ok: true });
  });

  it('post() delegates to HttpClient.post', () => {
    const body = { name: 'test' };
    service.post<{ id: number }>('/api/items', body).subscribe((res) => {
      expect(res).toEqual({ id: 1 });
    });
    const req = httpMock.expectOne('/api/items');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    req.flush({ id: 1 });
  });

  it('patch() delegates to HttpClient.patch', () => {
    service.patch('/api/items/1', { name: 'updated' }).subscribe();
    const req = httpMock.expectOne('/api/items/1');
    expect(req.request.method).toBe('PATCH');
    req.flush({});
  });

  it('delete() delegates to HttpClient.delete', () => {
    service.delete('/api/items/1').subscribe();
    const req = httpMock.expectOne('/api/items/1');
    expect(req.request.method).toBe('DELETE');
    req.flush({});
  });

  it('put() delegates to HttpClient.put', () => {
    service.put('/api/items/1', { name: 'replaced' }).subscribe();
    const req = httpMock.expectOne('/api/items/1');
    expect(req.request.method).toBe('PUT');
    req.flush({});
  });
});
