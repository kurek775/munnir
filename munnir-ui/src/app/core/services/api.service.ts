import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface HelloResponse {
  message: string;
  cpp_result: number;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  getHello() {
    return this.http.get<HelloResponse>('/api/v1/hello');
  }
}
