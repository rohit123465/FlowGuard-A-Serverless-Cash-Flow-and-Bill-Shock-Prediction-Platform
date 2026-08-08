export type ExpenseStatus = "planned" | "cleared";

export interface Expense {
  expense_id: string;
  description: string;
  amount_minor: number;
  expense_date: string;
  category: string;
  status: ExpenseStatus;
  essential: boolean;
  receipt_key: string | null;
}

export interface ExpenseInput {
  description: string;
  amount_minor: number;
  expense_date: string;
  category: string;
  status: ExpenseStatus;
  essential: boolean;
}

export type IncomeConfidence = "guaranteed" | "likely" | "uncertain";

export interface Income {
  income_id: string;
  source: string;
  amount_minor: number;
  expected_date: string;
  confidence: IncomeConfidence;
}

export type IncomeInput = Omit<Income, "income_id">;

export type Recurrence = "once" | "weekly" | "monthly" | "yearly";

export interface Commitment {
  commitment_id: string;
  name: string;
  amount_minor: number;
  next_due_date: string;
  recurrence: Recurrence;
  essential: boolean;
}

export type CommitmentInput = Omit<Commitment, "commitment_id">;

export interface ForecastRequest {
  opening_balance_minor: number;
  safety_buffer_minor: number;
  start_date: string;
  end_date: string;
  include_likely_income: boolean;
  include_uncertain_income: boolean;
}

export type ForecastEventType = "income" | "expense" | "commitment";

export interface ForecastEvent {
  event_id: string;
  event_date: string;
  description: string;
  event_type: ForecastEventType;
  change_minor: number;
  projected_balance_minor: number;
}

export interface ForecastResult {
  opening_balance_minor: number;
  safety_buffer_minor: number;
  safe_to_spend_minor: number;
  minimum_balance_minor: number;
  first_shortfall_date: string | null;
  shortfall_amount_minor: number;
  excluded_income_count: number;
  timeline: ForecastEvent[];
}

export interface ReceiptUploadForm {
  upload_url: string;
  fields: Record<string, string>;
  receipt_key: string;
  expires_in: number;
}

export interface MonthlyCategory {
  category: string;
  amount_minor: number;
  percentage: number;
}

export interface MonthlyAnalyticsResult {
  year: number;
  month: number;
  total_income_minor: number;
  total_expenses_minor: number;
  essential_expenses_minor: number;
  discretionary_expenses_minor: number;
  net_cash_flow_minor: number;
  savings_rate_percent: number | null;
  expense_count: number;
  income_count: number;
  highest_spending_category: string | null;
  category_breakdown: MonthlyCategory[];
}
