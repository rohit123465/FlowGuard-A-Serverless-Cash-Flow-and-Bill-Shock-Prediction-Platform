import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CommitmentList } from "./CommitmentList";

describe("CommitmentList", () => {
  it("shows recurring commitment details", () => {
    render(<CommitmentList commitments={[{ commitment_id: "1", name: "Rent", amount_minor: 90000, next_due_date: "2031-01-20", recurrence: "monthly", essential: true }]} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText("Rent")).toBeInTheDocument();
    expect(screen.getByText("−£900.00")).toBeInTheDocument();
    expect(screen.getByText("monthly")).toBeInTheDocument();
  });
});
