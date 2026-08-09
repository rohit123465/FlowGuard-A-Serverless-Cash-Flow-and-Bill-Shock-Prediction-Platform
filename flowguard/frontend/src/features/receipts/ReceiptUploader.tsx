import { useRef, useState } from "react";
import { expenseApi, receiptApi } from "../../api/endpoints";
import { useAuth } from "../../hooks/useAuth";
import type { Expense, ReceiptAnalysis } from "../../types/finance";
import { prepareReceiptFile } from "./receiptFiles";

interface Props {
  expense: Expense;
  onChanged(): Promise<unknown> | void;
  onApplied?(updated: Expense): Promise<unknown> | void;
}
const allowed = ["image/jpeg", "image/png", "application/pdf"];
const confidence = (value: number | null) => value === null ? "Not detected" : `${Math.round(value)}% confidence`;

export function ReceiptUploader({ expense, onChanged, onApplied }: Props) {
  const { getAccessToken } = useAuth();
  const api = receiptApi(getAccessToken); const expenses = expenseApi(getAccessToken);
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false); const [progress, setProgress] = useState<number | null>(null); const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<ReceiptAnalysis | null>(null);
  const [vendor, setVendor] = useState(""); const [receiptDate, setReceiptDate] = useState(""); const [total, setTotal] = useState("");

  async function upload(file?: File) {
    if (!file) return;
    setBusy(true); setProgress(0); setError("");
    try {
      const prepared = await prepareReceiptFile(file);
      if (!allowed.includes(prepared.type)) throw new Error("Choose a JPEG, PNG or PDF.");
      if (prepared.size === 0) throw new Error("The selected receipt is empty.");
      if (prepared.size > 5 * 1024 * 1024) throw new Error("Receipt must be 5 MB or smaller after conversion.");
      const form = await api.requestUpload(expense.expense_id, prepared);
      await api.uploadToS3(form, prepared, setProgress);
      await api.confirm(expense.expense_id, form.receipt_key);
      await onChanged();
    }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Receipt upload failed. Please try again."); }
    finally { setBusy(false); setProgress(null); if (input.current) input.current.value = ""; }
  }
  async function view() { setBusy(true); setError(""); try { const result = await api.getDownload(expense.expense_id); window.open(result.download_url, "_blank", "noopener,noreferrer"); } catch (caught) { setError(caught instanceof Error ? caught.message : "Receipt could not be opened."); } finally { setBusy(false); } }
  async function remove() { if (!window.confirm("Remove this receipt?")) return; setBusy(true); setError(""); try { await api.remove(expense.expense_id); setAnalysis(null); await onChanged(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Receipt could not be removed."); } finally { setBusy(false); } }
  async function scan() {
    setBusy(true); setError("");
    try { const result = await api.analyze(expense.expense_id); setAnalysis(result); setVendor(result.vendor_name ?? expense.description); setReceiptDate(result.receipt_date ?? expense.expense_date); setTotal(result.total_minor === null ? (expense.amount_minor / 100).toFixed(2) : (result.total_minor / 100).toFixed(2)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Textract could not scan this receipt."); }
    finally { setBusy(false); }
  }
  async function applySuggestions() {
    const amount = Number(total);
    if (!vendor.trim() || !receiptDate || !Number.isFinite(amount) || amount <= 0) { setError("Check the merchant, date and total before applying them."); return; }
    setBusy(true); setError("");
    try {
      const updated = await expenses.update(expense.expense_id, { description: vendor.trim(), amount_minor: Math.round(amount * 100), expense_date: receiptDate, category: expense.category, status: expense.status, essential: expense.essential });
      setAnalysis(null);
      if (onApplied) await onApplied(updated); else await onChanged();
    }
    catch (caught) { setError(caught instanceof Error ? caught.message : "The suggestions could not be applied."); }
    finally { setBusy(false); }
  }

  return <div className="receipt-control">
    <input ref={input} className="sr-only" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => upload(event.target.files?.[0])} />
    {expense.receipt_key ? <><button disabled={busy} onClick={view}>View</button><button disabled={busy} onClick={scan}>{busy ? "Scanning…" : "Scan"}</button><button className="danger-link" disabled={busy} onClick={remove}>Remove</button></> : <button disabled={busy} onClick={() => input.current?.click()}>{busy ? `Uploading${progress === null ? "…" : ` ${progress}%`}` : "+ Receipt"}</button>}
    {busy && progress !== null && <progress aria-label="Receipt upload progress" max="100" value={progress}>{progress}%</progress>}
    {error && <span className="receipt-error" role="alert">{error}</span>}
    {analysis && <div className="modal-backdrop" role="presentation"><div className="modal receipt-analysis" role="dialog" aria-modal="true" aria-labelledby="receipt-analysis-title"><div className="panel-heading"><div><p className="eyebrow">Amazon Textract suggestion</p><h2 id="receipt-analysis-title">Review receipt details</h2></div><button className="icon-button" onClick={() => setAnalysis(null)} aria-label="Close">×</button></div><p className="muted">OCR can make mistakes. Check every value before updating your expense.</p><div className="receipt-analysis-grid">
      <label>Merchant<input value={vendor} onChange={(event) => setVendor(event.target.value)} /><small>{confidence(analysis.vendor_confidence)}</small></label>
      <label>Receipt date<input type="date" value={receiptDate} onChange={(event) => setReceiptDate(event.target.value)} /><small>{confidence(analysis.date_confidence)}{!analysis.receipt_date && analysis.date_text ? ` · Read as “${analysis.date_text}”` : ""}</small></label>
      <label>Total (£)<input type="number" min="0.01" step="0.01" value={total} onChange={(event) => setTotal(event.target.value)} /><small>{confidence(analysis.total_confidence)}{analysis.total_minor === null && analysis.total_text ? ` · Read as “${analysis.total_text}”` : ""}</small></label>
    </div><div className="receipt-analysis-actions"><button className="button button-secondary" onClick={() => setAnalysis(null)}>Cancel</button><button className="button button-primary" disabled={busy} onClick={applySuggestions}>Apply to expense</button></div></div></div>}
  </div>;
}
