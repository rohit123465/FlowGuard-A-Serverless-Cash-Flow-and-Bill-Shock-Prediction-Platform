export type ExpenseStatus = "planned" | "cleared";

export interface Expense {
  expense_id: string;
  description: string;
  amount_minor: number;
  expense_date: string;
  category: string;
  status: ExpenseStatus;
  essential: boolean;
}

export interface ExpenseInput {
  description: string;
  amount_minor: number;
  expense_date: string;
  category: string;
  status: ExpenseStatus;
  essential: boolean;
}
