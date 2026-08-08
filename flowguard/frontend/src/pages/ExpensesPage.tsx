import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { downloadExpenseCsv, expenseApi } from "../api/endpoints";
import { ExpenseForm } from "../features/expenses/ExpenseForm";
import { ExpenseList } from "../features/expenses/ExpenseList";
import { ReceiptUploader } from "../features/receipts/ReceiptUploader";
import { useAuth } from "../hooks/useAuth";
import type { Expense, ExpenseInput } from "../types/finance";

function monthRange(value: string) {
  const [year, month] = value.split("-").map(Number);
  const end = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return { start: `${value}-01`, end: `${value}-${String(end).padStart(2, "0")}` };
}

export function ExpensesPage() {
  const { getAccessToken } = useAuth();
  const api = useMemo(() => expenseApi(getAccessToken), [getAccessToken]);
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [notice, setNotice] = useState("");
  const range = monthRange(month);
  const queryKey = ["expenses", range.start, range.end];
  const query = useQuery({ queryKey, queryFn: () => api.list(range.start, range.end) });

  const save = useMutation({
    mutationFn: (input: ExpenseInput) => editing ? api.update(editing.expense_id, input) : api.create(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["expenses"] });
      setNotice(editing ? "Expense updated." : "Expense added.");
      setEditing(null); setFormOpen(false);
    },
  });
  const remove = useMutation({
    mutationFn: (expense: Expense) => api.remove(expense.expense_id),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["expenses"] }); setNotice("Expense deleted."); },
  });
  const exportCsv = useMutation({
    mutationFn: () => downloadExpenseCsv(getAccessToken, range.start, range.end),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob); const link = document.createElement("a");
      link.href = url; link.download = `flowguard-expenses-${month}.csv`; link.click(); URL.revokeObjectURL(url);
      setNotice("CSV export downloaded.");
    },
  });

  const total = (query.data ?? []).reduce((sum, item) => sum + item.amount_minor, 0);
  const essential = (query.data ?? []).filter((item) => item.essential).reduce((sum, item) => sum + item.amount_minor, 0);
  const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });
  const error = query.error ?? save.error ?? remove.error ?? exportCsv.error;

  return (
    <>
      <div className="page-heading"><div><p className="eyebrow">Spending ledger</p><h1>Expenses</h1><p className="muted">Track spending, attach private receipt evidence, or export the selected month for budgeting and tax records.</p></div><div className="heading-actions"><button className="button button-secondary" disabled={exportCsv.isPending} onClick={() => exportCsv.mutate()}>{exportCsv.isPending ? "Preparing…" : "Download CSV"}</button><button className="button button-primary" onClick={() => { setEditing(null); setFormOpen(true); }}>+ Add expense</button></div></div>
      {notice && <div className="alert alert-success" role="status">{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
      {error && <div className="alert alert-error" role="alert">{error instanceof Error ? error.message : "Something went wrong"}</div>}
      <section className="summary-grid">
        <div className="summary-card"><span>Total this month</span><strong>{pounds.format(total / 100)}</strong><small>{query.data?.length ?? 0} records</small></div>
        <div className="summary-card"><span>Essential spending</span><strong>{pounds.format(essential / 100)}</strong><small>{total ? Math.round((essential / total) * 100) : 0}% of total</small></div>
        <div className="summary-card accent"><span>Still planned</span><strong>{pounds.format((query.data ?? []).filter((item) => item.status === "planned").reduce((sum, item) => sum + item.amount_minor, 0) / 100)}</strong><small>Upcoming pressure</small></div>
      </section>
      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">Monthly view</p><h2>Expense records</h2></div><label className="month-picker">Period<input type="month" value={month} onChange={(event) => setMonth(event.target.value)} /></label></div>
        <ExpenseList expenses={query.data ?? []} loading={query.isLoading} onEdit={(expense) => { setEditing(expense); setFormOpen(true); }} onDelete={(expense) => { if (window.confirm(`Delete “${expense.description}”?`)) remove.mutate(expense); }} renderReceipt={(expense) => <ReceiptUploader expense={expense} onChanged={() => queryClient.invalidateQueries({ queryKey: ["expenses"] })} />} />
      </section>
      {formOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setFormOpen(false); }}><div className="modal" role="dialog" aria-modal="true"><ExpenseForm expense={editing} busy={save.isPending} onSubmit={(input) => save.mutateAsync(input)} onCancel={() => { setEditing(null); setFormOpen(false); }} /></div></div>}
    </>
  );
}
