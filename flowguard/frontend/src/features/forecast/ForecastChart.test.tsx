import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ForecastChart } from "./ForecastChart";
import { SafeToSpendCard } from "./SafeToSpendCard";
import type { ForecastResult } from "../../types/finance";

const forecast: ForecastResult = {
  opening_balance_minor: 100000,
  safety_buffer_minor: 10000,
  safe_to_spend_minor: 50000,
  minimum_balance_minor: 60000,
  first_shortfall_date: null,
  shortfall_amount_minor: 0,
  excluded_income_count: 0,
  timeline: [
    { event_id: "1", event_date: "2032-08-10", description: "Electricity", event_type: "expense", change_minor: -10000, projected_balance_minor: 90000 },
    { event_id: "2", event_date: "2032-08-15", description: "Salary", event_type: "income", change_minor: 50000, projected_balance_minor: 140000 },
    { event_id: "3", event_date: "2032-08-20", description: "Rent", event_type: "commitment", change_minor: -80000, projected_balance_minor: 60000 },
  ],
};

describe("forecast presentation", () => {
  it("shows the deterministic safe-to-spend result", () => {
    render(<SafeToSpendCard forecast={forecast} />);
    expect(screen.getByText("£500.00")).toBeInTheDocument();
    expect(screen.getByText("No buffer breach detected")).toBeInTheDocument();
    expect(screen.getByText("Lowest projected balance: £600.00.")).toBeInTheDocument();
  });

  it("renders each event in chronological order", () => {
    render(<ForecastChart forecast={forecast} />);
    const events = screen.getAllByRole("article");
    expect(events.map((event) => event.textContent)).toEqual([
      expect.stringContaining("Electricity"),
      expect.stringContaining("Salary"),
      expect.stringContaining("Rent"),
    ]);
  });
});
