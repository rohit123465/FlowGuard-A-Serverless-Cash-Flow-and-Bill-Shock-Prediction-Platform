import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MonthlyAnalytics } from "./MonthlyAnalytics";

describe("MonthlyAnalytics", () => {
  it("explains income, expenses, savings and category concentration", () => {
    render(<MonthlyAnalytics analytics={{ year: 2026, month: 8, total_income_minor: 200000, total_expenses_minor: 82000, essential_expenses_minor: 80000, discretionary_expenses_minor: 2000, net_cash_flow_minor: 118000, savings_rate_percent: 59, expense_count: 2, income_count: 1, highest_spending_category: "housing", category_breakdown: [{ category: "housing", amount_minor: 80000, percentage: 97.6 }, { category: "leisure", amount_minor: 2000, percentage: 2.4 }] }} />);
    expect(screen.getByText("£2,000.00")).toBeInTheDocument();
    expect(screen.getByText("£820.00")).toBeInTheDocument();
    expect(screen.getByText("+£1,180.00")).toBeInTheDocument();
    expect(screen.getByText("59% savings rate")).toBeInTheDocument();
    expect(screen.getAllByText("housing")).toHaveLength(2);
  });
});
