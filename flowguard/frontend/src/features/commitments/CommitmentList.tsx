import type { Commitment } from "../../types/finance";

interface Props { commitments: Commitment[]; loading?: boolean; onEdit(item: Commitment): void; onDelete(item: Commitment): void; }
const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function CommitmentList({ commitments, loading, onEdit, onDelete }: Props) {
  if (loading) return <div className="empty-state">Loading commitments…</div>;
  if (!commitments.length) return <div className="empty-state"><div className="empty-icon commitment-icon">⌁</div><h3>No commitments yet</h3><p>Add rent, utilities, subscriptions or other upcoming bills.</p></div>;
  return <div className="expense-list">{commitments.map((item) => <article className="expense-row" key={item.commitment_id}>
    <div className={`category-icon commitment-icon ${item.essential ? "essential" : ""}`}>⌁</div><div className="expense-primary"><strong>{item.name}</strong><span>Next due {new Date(`${item.next_due_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span></div>
    <span className="pill recurrence">{item.recurrence}</span><strong className="amount">−{pounds.format(item.amount_minor / 100)}</strong><div className="row-actions"><button onClick={() => onEdit(item)}>Edit</button><button className="danger-link" onClick={() => onDelete(item)}>Delete</button></div>
  </article>)}</div>;
}
