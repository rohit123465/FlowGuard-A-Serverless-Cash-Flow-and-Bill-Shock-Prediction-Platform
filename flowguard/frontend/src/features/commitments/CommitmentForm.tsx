import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Commitment, CommitmentInput } from "../../types/finance";

const schema = z.object({
  name: z.string().trim().min(1, "Name is required").max(120),
  amount: z.number().positive("Amount must be greater than zero"),
  next_due_date: z.string().min(1, "Due date is required"),
  recurrence: z.enum(["once", "weekly", "monthly", "yearly"]),
  essential: z.boolean(),
});
type FormValues = z.infer<typeof schema>;
interface Props { commitment?: Commitment | null; busy?: boolean; onSubmit(input: CommitmentInput): Promise<unknown>; onCancel(): void; }

function defaults(item?: Commitment | null): FormValues {
  return { name: item?.name ?? "", amount: item ? item.amount_minor / 100 : 0, next_due_date: item?.next_due_date ?? new Date().toISOString().slice(0, 10), recurrence: item?.recurrence ?? "monthly", essential: item?.essential ?? true };
}

export function CommitmentForm({ commitment, busy, onSubmit, onCancel }: Props) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: defaults(commitment) });
  useEffect(() => reset(defaults(commitment)), [commitment, reset]);
  async function submit(values: FormValues) { await onSubmit({ name: values.name.trim(), amount_minor: Math.round(values.amount * 100), next_due_date: values.next_due_date, recurrence: values.recurrence, essential: values.essential }); }
  return <form className="expense-form" onSubmit={handleSubmit(submit)}>
    <div className="panel-heading"><div><p className="eyebrow">{commitment ? "Update bill" : "New obligation"}</p><h2>{commitment ? "Edit commitment" : "Add commitment"}</h2></div><button type="button" className="icon-button" onClick={onCancel} aria-label="Close form">×</button></div>
    <label>Name<input {...register("name")} placeholder="e.g. Monthly rent" />{errors.name && <span className="field-error">{errors.name.message}</span>}</label>
    <div className="form-grid"><label>Amount (£)<input type="number" min="0.01" step="0.01" {...register("amount", { valueAsNumber: true })} />{errors.amount && <span className="field-error">{errors.amount.message}</span>}</label><label>Next due date<input type="date" {...register("next_due_date")} />{errors.next_due_date && <span className="field-error">{errors.next_due_date.message}</span>}</label></div>
    <label>Recurrence<select {...register("recurrence")}><option value="once">Once</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select></label>
    <label className="checkbox-label"><input type="checkbox" {...register("essential")} /><span><strong>Essential commitment</strong><small>Required bill or contractual obligation</small></span></label>
    <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Saving…" : commitment ? "Save changes" : "Add commitment"}</button>
  </form>;
}
