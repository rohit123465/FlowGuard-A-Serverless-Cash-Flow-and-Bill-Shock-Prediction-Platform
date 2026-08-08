export interface ApiEnvelope<T> {
  data: T;
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
  };
  message?: string;
}
