import type { ApiError } from "@/types/api";

/**
 * Typed error thrown by the API client on non-2xx responses.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly error: string;
  public readonly detail?: unknown;

  constructor(
    status: number,
    error: string,
    message: string,
    detail?: unknown
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.error = error;
    this.detail = detail;
  }
}

/**
 * Typed fetch wrapper for the ResumeForge API.
 */
class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    const defaultHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options?.headers,
      },
    });

    if (!response.ok) {
      let errorBody: ApiError = {
        error: "request_failed",
        message: `Request failed with status ${response.status}`,
      };

      try {
        const parsed = (await response.json()) as Partial<ApiError>;
        errorBody = {
          error: parsed.error ?? errorBody.error,
          message: parsed.message ?? errorBody.message,
          detail: parsed.detail,
        };
      } catch {
        // Ignore JSON parse errors — use the default error body
      }

      throw new ApiClientError(
        response.status,
        errorBody.error,
        errorBody.message,
        errorBody.detail
      );
    }

    // Handle empty responses (e.g. 204 No Content)
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return response.json() as Promise<T>;
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "GET" });
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }
}

export const apiClient = new ApiClient(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
);
