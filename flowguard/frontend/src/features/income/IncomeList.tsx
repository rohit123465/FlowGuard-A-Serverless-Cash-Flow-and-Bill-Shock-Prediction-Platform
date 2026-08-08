import type { Income } from "../../types/finance";

interface Props { income: Income[]; loading?: boolean; onEdit(item: Income): void; onDelete(item: Income): void; }
const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function IncomeList({ income, loading, onEdit, onDelete }: Props) {
  if (loading) return <div className="empty-state">Loading expected income…</div>;
  if (!income.length) return <div className="empty-state"><div className="empty-icon income-icon">↗</div><h3>No income in this period</h3><p>Add salary, invoices or other expected payments.</p></div>;
  return <div className="expense-list">{income.map((item) => <article className="expense-row" key={item.income_id}>
    <div className="category-icon income-icon">↗</div><div className="expense-primary"><strong>{item.source}</strong><span>Expected {new Date(`${item.expected_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span></div>
    <span className={`pill confidence-${item.confidence}`}>{item.confidence}</span><strong className="amount positive">+{pounds.format(item.amount_minor / 100)}</strong><div className="row-actions"><button onClick={() => onEdit(item)}>Edit</button><button className="danger-link" onClick={() => onDelete(item)}>Delete</button></div>
  </article>)}</div>;
}
