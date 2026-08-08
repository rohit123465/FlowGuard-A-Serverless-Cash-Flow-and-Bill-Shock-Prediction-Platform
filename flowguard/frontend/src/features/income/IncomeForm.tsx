import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Income, IncomeInput } from "../../types/finance";

const schema = z.object({
  source: z.string().trim().min(1, "Source is required").max(120),
  amount: z.number().positive("Amount must be greater than zero"),
  expected_date: z.string().min(1, "Date is required"),
  confidence: z.enum(["guaranteed", "likely", "uncertain"]),
});
type FormValues = z.infer<typeof schema>;

interface Props {
  income?: Income | null;
  busy?: boolean;
  onSubmit(input: IncomeInput): Promise<unknown>;
  onCancel(): void;
}

function defaults(income?: Income | null): FormValues {
  return {
    source: income?.source ?? "",
    amount: income ? income.amount_minor / 100 : 0,
    expected_date: income?.expected_date ?? new Date().toISOString().slice(0, 10),
    confidence: income?.confidence ?? "guaranteed",
  };
}

export function IncomeForm({ income, busy, onSubmit, onCancel }: Props) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults(income) });
  useEffect(() => reset(defaults(income)), [income, reset]);

  async function submit(values: FormValues) {
    await onSubmit({ source: values.source.trim(), amount_minor: Math.round(values.amount * 100), expected_date: values.expected_date, confidence: values.confidence });
  }

  return <form className="expense-form" onSubmit={handleSubmit(submit)}>
    <div className="panel-heading"><div><p className="eyebrow">{income ? "Update record" : "New inflow"}</p><h2>{income ? "Edit income" : "Add expected income"}</h2></div><button type="button" className="icon-button" onClick={onCancel} aria-label="Close form">×</button></div>
    <label>Income source<input {...register("source")} placeholder="e.g. Monthly salary" />{errors.source && <span className="field-error">{errors.source.message}</span>}</label>
    <div className="form-grid"><label>Amount (£)<input type="number" step="0.01" min="0.01" {...register("amount", { valueAsNumber: true })} />{errors.amount && <span className="field-error">{errors.amount.message}</span>}</label><label>Expected date<input type="date" {...register("expected_date")} />{errors.expected_date && <span className="field-error">{errors.expected_date.message}</span>}</label></div>
    <label>Confidence<select {...register("confidence")}><option value="guaranteed">Guaranteed</option><option value="likely">Likely</option><option value="uncertain">Uncertain</option></select><small className="help-text">Forecasts include guaranteed income by default.</small></label>
    <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Saving…" : income ? "Save changes" : "Add income"}</button>
  </form>;
}
