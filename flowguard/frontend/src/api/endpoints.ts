import type { AccessTokenProvider } from "./client";
import { createApiClient } from "./client";
import type { Expense, ExpenseInput } from "../types/finance";

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
