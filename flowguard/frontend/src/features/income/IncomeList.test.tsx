import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { IncomeList } from "./IncomeList";

describe("IncomeList", () => {
  it("shows expected income in pounds with confidence", () => {
    render(<IncomeList income={[{ income_id: "1", source: "Salary", amount_minor: 250000, expected_date: "2031-01-15", confidence: "guaranteed" }]} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText("Salary")).toBeInTheDocument();
    expect(screen.getByText("+£2,500.00")).toBeInTheDocument();
    expect(screen.getByText("guaranteed")).toBeInTheDocument();
  });
});
