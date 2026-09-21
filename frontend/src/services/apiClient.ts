import { ApiErrorResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private getToken(): string | null {
    return localStorage.getItem('faceattend_token');
  }

  public setToken(token: string): void {
    localStorage.setItem('faceattend_token', token);
  }

  public clearToken(): void {
    localStorage.removeItem('faceattend_token');
    localStorage.removeItem('faceattend_user');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = DEFAULT_TIMEOUT_MS
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Do not set Content-Type if body is FormData (browser will set with boundary)
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle 401 Unauthorized globally
      if (response.status === 401) {
        this.clearToken();
        window.dispatchEvent(new CustomEvent('faceattend_unauthorized'));
      }

      if (!response.ok) {
        let errorData: any;
        let errorMessage = `HTTP ${response.status} ${response.statusText}`;

        try {
          errorData = await response.json();
          if (errorData && errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
            }
          }
        } catch {
          // Non-JSON error body
        }

        throw new ApiError(response.status, errorMessage, errorData);
      }

      // 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: any) {
      clearTimeout(timeoutId);

      if (err.name === 'AbortError') {
        throw new ApiError(408, 'Request timed out. Please check your network connection.');
      }

      if (err instanceof ApiError) {
        throw err;
      }

      // Network / connection refused error
      throw new ApiError(0, err.message || 'Network connection failed. Ensure backend API is online.');
    }
  }

  public get<T>(endpoint: string, params?: Record<string, any>, timeoutMs?: number): Promise<T> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.request<T>(url, { method: 'GET' }, timeoutMs);
  }

  public post<T>(endpoint: string, body?: any, timeoutMs?: number): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
  }

  public put<T>(endpoint: string, body?: any, timeoutMs?: number): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
  }

  public patch<T>(endpoint: string, body?: any, timeoutMs?: number): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: body !== undefined ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
  }

  public postMultipart<T>(endpoint: string, formData: FormData, timeoutMs: number = 30000): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: formData,
      },
      timeoutMs
    );
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
