import type { ReactNode } from "react";
import type { Expense } from "../../types/finance";

interface ExpenseListProps {
  expenses: Expense[];
  loading?: boolean;
  onEdit(expense: Expense): void;
  onDelete(expense: Expense): void;
  renderReceipt?(expense: Expense): ReactNode;
}

const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function ExpenseList({ expenses, loading, onEdit, onDelete, renderReceipt }: ExpenseListProps) {
  if (loading) return <div className="empty-state">Loading your expenses…</div>;
  if (!expenses.length) return <div className="empty-state"><div className="empty-icon">↘</div><h3>No expenses in this period</h3><p>Add your first expense to begin tracking cash flow.</p></div>;

  return (
    <div className="expense-list">
      {expenses.map((expense) => (
        <article className="expense-row" key={expense.expense_id}>
          <div className={`category-icon ${expense.essential ? "essential" : ""}`}>{expense.category.slice(0, 1).toUpperCase()}</div>
          <div className="expense-primary"><strong>{expense.description}</strong><span>{expense.category} · {new Date(`${expense.expense_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span></div>
          <span className={`pill ${expense.status}`}>{expense.status}</span>
          <strong className="amount">−{pounds.format(expense.amount_minor / 100)}</strong>
          <div className="row-actions"><button onClick={() => onEdit(expense)}>Edit</button><button className="danger-link" onClick={() => onDelete(expense)}>Delete</button>{renderReceipt?.(expense)}</div>
        </article>
      ))}
    </div>
  );
}
