import { useRef, useState } from "react";
import { receiptApi } from "../../api/endpoints";
import { useAuth } from "../../hooks/useAuth";
import type { Expense } from "../../types/finance";

interface Props {
  expense: Expense;
  onChanged(): Promise<unknown> | void;
}

const allowed = ["image/jpeg", "image/png", "application/pdf"];

export function ReceiptUploader({ expense, onChanged }: Props) {
  const { getAccessToken } = useAuth();
  const api = receiptApi(getAccessToken);
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function upload(file?: File) {
    if (!file) return;
    if (!allowed.includes(file.type)) {
      setError("Choose a JPEG, PNG or PDF.");
      return;
    }
    if (file.size === 0) {
      setError("The selected receipt is empty.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Receipt must be 5 MB or smaller.");
      return;
    }

    setBusy(true);
    setProgress(0);
    setError("");
    try {
      const form = await api.requestUpload(expense.expense_id, file);
      await api.uploadToS3(form, file, setProgress);
      await api.confirm(expense.expense_id, form.receipt_key);
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Receipt upload failed. Please try again.");
    } finally {
      setBusy(false);
      setProgress(null);
      if (input.current) input.current.value = "";
    }
  }

  async function view() {
    setBusy(true);
    setError("");
    try {
      const result = await api.getDownload(expense.expense_id);
      window.open(result.download_url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Receipt could not be opened.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm("Remove this receipt?")) return;
    setBusy(true);
    setError("");
    try {
      await api.remove(expense.expense_id);
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Receipt could not be removed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="receipt-control">
      <input
        ref={input}
        className="sr-only"
        type="file"
        accept="image/jpeg,image/png,application/pdf"
        onChange={(event) => upload(event.target.files?.[0])}
      />
      {expense.receipt_key ? (
        <>
          <button disabled={busy} onClick={view}>View receipt</button>
          <button className="danger-link" disabled={busy} onClick={remove}>Remove</button>
        </>
      ) : (
        <button disabled={busy} onClick={() => input.current?.click()}>
          {busy ? `Uploading${progress === null ? "…" : ` ${progress}%`}` : "+ Receipt"}
        </button>
      )}
      {busy && progress !== null && (
        <progress aria-label="Receipt upload progress" max="100" value={progress}>{progress}%</progress>
      )}
      {error && <span className="receipt-error" role="alert">{error}</span>}
    </div>
  );
}
