import type { ApiEnvelope, ApiErrorEnvelope } from "../types/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type AccessTokenProvider = () => Promise<string>;

export function createApiClient(getAccessToken: AccessTokenProvider) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    throw new Error("VITE_API_BASE_URL is not configured");
  }

  return async function request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = await getAccessToken();
    const headers = new Headers(options.headers);
    headers.set("Authorization", `Bearer ${token}`);
    if (options.body) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    if (response.status === 204) {
      return undefined as T;
    }

    const payload = (await response.json()) as ApiEnvelope<T> & ApiErrorEnvelope;
    if (!response.ok) {
      throw new ApiError(
        payload.error?.message ?? payload.message ?? "Request failed",
        response.status,
        payload.error?.code,
      );
    }
    return payload.data;
  };
}
