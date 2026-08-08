import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ExpenseList } from "./ExpenseList";
import type { Expense } from "../../types/finance";

const expense: Expense = {
  expense_id: "0788fd5b-7d67-4494-919a-c61e0eb88219",
  description: "Weekly groceries",
  amount_minor: 4250,
  expense_date: "2026-08-20",
  category: "groceries",
  status: "cleared",
  essential: true,
  receipt_key: null,
};

describe("ExpenseList", () => {
  it("renders money in pounds and exposes edit and delete actions", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(
      <ExpenseList
        expenses={[expense]}
        onEdit={onEdit}
        onDelete={onDelete}
      />,
    );

    expect(screen.getByText("Weekly groceries")).toBeInTheDocument();
    expect(screen.getByText("−£42.50")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(onEdit).toHaveBeenCalledWith(expense);
    expect(onDelete).toHaveBeenCalledWith(expense);
  });

  it("shows a useful empty state", () => {
    render(<ExpenseList expenses={[]} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText("No expenses in this period")).toBeInTheDocument();
  });
});
