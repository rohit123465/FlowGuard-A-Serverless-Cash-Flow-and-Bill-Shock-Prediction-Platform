import type { AccessTokenProvider } from "./client";
import { ApiError, authorizedFetch, createApiClient } from "./client";
import type {
  Commitment,
  CommitmentInput,
  Expense,
  ExpenseInput,
  ForecastRequest,
  ForecastResult,
  Income,
  IncomeInput,
  MonthlyAnalyticsResult,
  ReceiptUploadForm,
} from "../types/finance";

export function expenseApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);

  return {
    list(startDate: string, endDate: string) {
      const query = new URLSearchParams({ startDate, endDate });
      return request<Expense[]>(`/expenses?${query.toString()}`);
    },
    create(input: ExpenseInput) {
      return request<Expense>("/expenses", {
        method: "POST",
        body: JSON.stringify(input),
      });
    },
    update(expenseId: string, input: ExpenseInput) {
      return request<Expense>(`/expenses/${expenseId}`, {
        method: "PUT",
        body: JSON.stringify(input),
      });
    },
    remove(expenseId: string) {
      return request<void>(`/expenses/${expenseId}`, { method: "DELETE" });
    },
  };
}

export function incomeApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);
  return {
    list(startDate: string, endDate: string) {
      const query = new URLSearchParams({ startDate, endDate });
      return request<Income[]>(`/income?${query.toString()}`);
    },
    create(input: IncomeInput) {
      return request<Income>("/income", { method: "POST", body: JSON.stringify(input) });
    },
    update(incomeId: string, input: IncomeInput) {
      return request<Income>(`/income/${incomeId}`, { method: "PUT", body: JSON.stringify(input) });
    },
    remove(incomeId: string) {
      return request<void>(`/income/${incomeId}`, { method: "DELETE" });
    },
  };
}

export function commitmentApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);
  return {
    list() {
      return request<Commitment[]>("/commitments");
    },
    create(input: CommitmentInput) {
      return request<Commitment>("/commitments", { method: "POST", body: JSON.stringify(input) });
    },
    update(commitmentId: string, input: CommitmentInput) {
      return request<Commitment>(`/commitments/${commitmentId}`, { method: "PUT", body: JSON.stringify(input) });
    },
    remove(commitmentId: string) {
      return request<void>(`/commitments/${commitmentId}`, { method: "DELETE" });
    },
  };
}

export function forecastApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);
  return {
    calculate(input: ForecastRequest) {
      const query = new URLSearchParams({
        openingBalanceMinor: String(input.opening_balance_minor),
        safetyBufferMinor: String(input.safety_buffer_minor),
        startDate: input.start_date,
        endDate: input.end_date,
        includeLikelyIncome: String(input.include_likely_income),
        includeUncertainIncome: String(input.include_uncertain_income),
      });
      return request<ForecastResult>(`/forecast?${query.toString()}`);
    },
  };
}

export function receiptApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);
  return {
    requestUpload(expenseId: string, file: File) {
      return request<ReceiptUploadForm>(`/expenses/${expenseId}/receipt-upload`, {
        method: "POST",
        body: JSON.stringify({ filename: file.name, content_type: file.type, size_bytes: file.size }),
      });
    },
    async uploadToS3(form: ReceiptUploadForm, file: File) {
      const body = new FormData();
      Object.entries(form.fields).forEach(([key, value]) => body.append(key, value));
      body.append("file", file);
      const response = await fetch(form.upload_url, { method: "POST", body });
      if (!response.ok) throw new Error("S3 could not store the receipt");
    },
    confirm(expenseId: string, receiptKey: string) {
      return request<Expense>(`/expenses/${expenseId}/receipt-confirm`, { method: "POST", body: JSON.stringify({ receipt_key: receiptKey }) });
    },
    getDownload(expenseId: string) {
      return request<{ download_url: string; expires_in: number }>(`/expenses/${expenseId}/receipt`);
    },
    remove(expenseId: string) {
      return request<void>(`/expenses/${expenseId}/receipt`, { method: "DELETE" });
    },
  };
}

export function analyticsApi(getAccessToken: AccessTokenProvider) {
  const request = createApiClient(getAccessToken);
  return {
    monthly(year: number, month: number) {
      const query = new URLSearchParams({ year: String(year), month: String(month) });
      return request<MonthlyAnalyticsResult>(`/analytics/monthly?${query.toString()}`);
    },
  };
}

export async function downloadExpenseCsv(
  getAccessToken: AccessTokenProvider,
  startDate: string,
  endDate: string,
) {
  const query = new URLSearchParams({ startDate, endDate });
  const response = await authorizedFetch(getAccessToken, `/exports/expenses.csv?${query.toString()}`);
  if (!response.ok) {
    const payload = await response.json();
    throw new ApiError(payload.error?.message ?? "CSV export failed", response.status, payload.error?.code);
  }
  return response.blob();
}
