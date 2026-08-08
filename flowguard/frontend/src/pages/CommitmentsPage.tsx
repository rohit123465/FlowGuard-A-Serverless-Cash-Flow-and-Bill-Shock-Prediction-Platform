import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { commitmentApi } from "../api/endpoints";
import { CommitmentForm } from "../features/commitments/CommitmentForm";
import { CommitmentList } from "../features/commitments/CommitmentList";
import { useAuth } from "../hooks/useAuth";
import type { Commitment, CommitmentInput } from "../types/finance";

export function CommitmentsPage() {
  const { getAccessToken } = useAuth(); const api = useMemo(() => commitmentApi(getAccessToken), [getAccessToken]); const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false); const [editing, setEditing] = useState<Commitment | null>(null); const [notice, setNotice] = useState("");
  const query = useQuery({ queryKey: ["commitments"], queryFn: api.list });
  const save = useMutation({ mutationFn: (input: CommitmentInput) => editing ? api.update(editing.commitment_id, input) : api.create(input), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["commitments"] }); setNotice(editing ? "Commitment updated." : "Commitment added."); setEditing(null); setFormOpen(false); } });
  const remove = useMutation({ mutationFn: (item: Commitment) => api.remove(item.commitment_id), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["commitments"] }); setNotice("Commitment deleted."); } });
  const records = query.data ?? []; const monthly = records.filter((item) => item.recurrence === "monthly").reduce((sum, item) => sum + item.amount_minor, 0); const essential = records.filter((item) => item.essential).length; const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }); const error = query.error ?? save.error ?? remove.error;
  return <><div className="page-heading"><div><p className="eyebrow">Bills and obligations</p><h1>Commitments</h1><p className="muted">Make recurring financial pressure visible before it arrives.</p></div><button className="button button-primary" onClick={() => { setEditing(null); setFormOpen(true); }}>+ Add commitment</button></div>
    {notice && <div className="alert alert-success" role="status">{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}{error && <div className="alert alert-error" role="alert">{error instanceof Error ? error.message : "Something went wrong"}</div>}
    <section className="summary-grid"><div className="summary-card"><span>Active commitments</span><strong>{records.length}</strong><small>Across all recurrence types</small></div><div className="summary-card"><span>Monthly obligations</span><strong>{pounds.format(monthly / 100)}</strong><small>Before other spending</small></div><div className="summary-card accent"><span>Essential bills</span><strong>{essential}</strong><small>Prioritised in planning</small></div></section>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">All schedules</p><h2>Commitment records</h2></div></div><CommitmentList commitments={records} loading={query.isLoading} onEdit={(item) => { setEditing(item); setFormOpen(true); }} onDelete={(item) => { if (window.confirm(`Delete “${item.name}”?`)) remove.mutate(item); }} /></section>
    {formOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setFormOpen(false); }}><div className="modal" role="dialog" aria-modal="true"><CommitmentForm commitment={editing} busy={save.isPending} onSubmit={(input) => save.mutateAsync(input)} onCancel={() => { setEditing(null); setFormOpen(false); }} /></div></div>}
  </>;
}
