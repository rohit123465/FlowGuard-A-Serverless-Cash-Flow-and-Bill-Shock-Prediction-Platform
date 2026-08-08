import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { incomeApi } from "../api/endpoints";
import { IncomeForm } from "../features/income/IncomeForm";
import { IncomeList } from "../features/income/IncomeList";
import { useAuth } from "../hooks/useAuth";
import type { Income, IncomeInput } from "../types/finance";

function monthRange(value: string) { const [year, month] = value.split("-").map(Number); const end = new Date(Date.UTC(year, month, 0)).getUTCDate(); return { start: `${value}-01`, end: `${value}-${String(end).padStart(2, "0")}` }; }

export function IncomePage() {
  const { getAccessToken } = useAuth(); const api = useMemo(() => incomeApi(getAccessToken), [getAccessToken]); const queryClient = useQueryClient();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7)); const [formOpen, setFormOpen] = useState(false); const [editing, setEditing] = useState<Income | null>(null); const [notice, setNotice] = useState(""); const range = monthRange(month);
  const query = useQuery({ queryKey: ["income", range.start, range.end], queryFn: () => api.list(range.start, range.end) });
  const save = useMutation({ mutationFn: (input: IncomeInput) => editing ? api.update(editing.income_id, input) : api.create(input), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["income"] }); setNotice(editing ? "Income updated." : "Income added."); setEditing(null); setFormOpen(false); } });
  const remove = useMutation({ mutationFn: (item: Income) => api.remove(item.income_id), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["income"] }); setNotice("Income deleted."); } });
  const records = query.data ?? []; const total = records.reduce((sum, item) => sum + item.amount_minor, 0); const guaranteed = records.filter((item) => item.confidence === "guaranteed").reduce((sum, item) => sum + item.amount_minor, 0); const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }); const error = query.error ?? save.error ?? remove.error;
  return <><div className="page-heading"><div><p className="eyebrow">Money coming in</p><h1>Expected income</h1><p className="muted">Record when money should arrive and how reliable it is.</p></div><button className="button button-primary" onClick={() => { setEditing(null); setFormOpen(true); }}>+ Add income</button></div>
    {notice && <div className="alert alert-success" role="status">{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}{error && <div className="alert alert-error" role="alert">{error instanceof Error ? error.message : "Something went wrong"}</div>}
    <section className="summary-grid"><div className="summary-card"><span>Total expected</span><strong className="positive">{pounds.format(total / 100)}</strong><small>{records.length} payments</small></div><div className="summary-card"><span>Guaranteed</span><strong>{pounds.format(guaranteed / 100)}</strong><small>Included by default</small></div><div className="summary-card accent-green"><span>Confidence coverage</span><strong>{total ? Math.round((guaranteed / total) * 100) : 0}%</strong><small>Guaranteed share</small></div></section>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Monthly view</p><h2>Income records</h2></div><label className="month-picker">Period<input type="month" value={month} onChange={(event) => setMonth(event.target.value)} /></label></div><IncomeList income={records} loading={query.isLoading} onEdit={(item) => { setEditing(item); setFormOpen(true); }} onDelete={(item) => { if (window.confirm(`Delete “${item.source}”?`)) remove.mutate(item); }} /></section>
    {formOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setFormOpen(false); }}><div className="modal" role="dialog" aria-modal="true"><IncomeForm income={editing} busy={save.isPending} onSubmit={(input) => save.mutateAsync(input)} onCancel={() => { setEditing(null); setFormOpen(false); }} /></div></div>}
  </>;
}
