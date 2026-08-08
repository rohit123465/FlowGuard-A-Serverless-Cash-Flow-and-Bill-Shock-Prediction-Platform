import type { AccessTokenProvider } from "./client";
import { createApiClient } from "./client";
import type {
  Commitment,
  CommitmentInput,
  Expense,
  ExpenseInput,
  ForecastRequest,
  ForecastResult,
  Income,
  IncomeInput,
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
