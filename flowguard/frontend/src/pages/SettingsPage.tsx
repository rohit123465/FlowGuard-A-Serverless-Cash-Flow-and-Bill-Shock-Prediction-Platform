import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { notificationApi } from "../api/endpoints";
import { useAuth } from "../hooks/useAuth";
import type { BillShockSettings } from "../types/finance";

export function SettingsPage() {
  const { getAccessToken } = useAuth();
  const api = useMemo(() => notificationApi(getAccessToken), [getAccessToken]);
  const settings = useQuery({ queryKey: ["notification-settings"], queryFn: api.getSettings });
  const [enabled, setEnabled] = useState(false);
  const [balance, setBalance] = useState("0.00");
  const [buffer, setBuffer] = useState("0.00");
  const [horizon, setHorizon] = useState(30);
  const [includeLikely, setIncludeLikely] = useState(false);
  const save = useMutation({ mutationFn: api.updateSettings });

  useEffect(() => {
    if (!settings.data) return;
    setEnabled(settings.data.enabled);
    setBalance((settings.data.opening_balance_minor / 100).toFixed(2));
    setBuffer((settings.data.safety_buffer_minor / 100).toFixed(2));
    setHorizon(settings.data.horizon_days);
    setIncludeLikely(settings.data.include_likely_income);
  }, [settings.data]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const payload: BillShockSettings = { enabled, opening_balance_minor: Math.round(Number(balance) * 100), safety_buffer_minor: Math.round(Number(buffer) * 100), horizon_days: horizon, include_likely_income: includeLikely };
    save.mutate(payload);
  }
  const error = settings.error ?? save.error;

  return <><div className="page-heading"><div><p className="eyebrow">Automatic protection</p><h1>Bill-shock warnings</h1><p className="muted">FlowGuard checks your upcoming cash flow every morning and displays an in-app warning if your balance may fall below your buffer.</p></div></div><section className="settings-panel"><form className="expense-form" onSubmit={submit}>
    <label className="checkbox-label"><input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} /><span><strong>Enable daily warnings</strong><small>The AWS scheduler runs daily at 07:00 UTC.</small></span></label>
    <div className="form-grid">
      <label>Current balance (£)<input type="number" step="0.01" required value={balance} onChange={(event) => setBalance(event.target.value)} /><small>Update this when your real account balance changes.</small></label>
      <label>Safety buffer (£)<input type="number" min="0" step="0.01" required value={buffer} onChange={(event) => setBuffer(event.target.value)} /><small>The minimum amount you want to protect.</small></label>
      <label>Forecast window<select value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}><option value={14}>14 days</option><option value={30}>30 days</option><option value={60}>60 days</option><option value={90}>90 days</option></select></label>
      <label className="checkbox-label"><input type="checkbox" checked={includeLikely} onChange={(event) => setIncludeLikely(event.target.checked)} /><span><strong>Include likely income</strong><small>Guaranteed income is included; uncertain income is excluded.</small></span></label>
    </div>
    <div className="settings-explanation"><strong>What is computed?</strong><p>The scheduler orders upcoming expenses, commitments and included income by date, calculates the balance after each event, and compares the lowest balance with your safety buffer.</p></div>
    {save.isSuccess && <div className="alert alert-success">Warning settings saved.</div>}
    {error && <div className="alert alert-error">{error instanceof Error ? error.message : "Settings could not be saved."}</div>}
    <button className="button button-primary" disabled={save.isPending || settings.isLoading}>{save.isPending ? "Saving…" : "Save warning settings"}</button>
  </form></section></>;
}
