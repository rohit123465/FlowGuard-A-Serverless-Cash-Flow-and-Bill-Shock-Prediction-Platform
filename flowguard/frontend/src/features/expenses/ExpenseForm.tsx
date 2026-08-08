import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Expense, ExpenseInput } from "../../types/finance";

const schema = z.object({
  description: z.string().trim().min(1, "Description is required").max(200),
  amount: z.number().positive("Amount must be greater than zero"),
  expense_date: z.string().min(1, "Date is required"),
  category: z.string().trim().min(1, "Category is required").max(80),
  status: z.enum(["planned", "cleared"]),
  essential: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

interface ExpenseFormProps {
  expense?: Expense | null;
  busy?: boolean;
  onSubmit(input: ExpenseInput): Promise<unknown>;
  onCancel(): void;
}

function defaults(expense?: Expense | null): FormValues {
  return {
    description: expense?.description ?? "",
    amount: expense ? expense.amount_minor / 100 : 0,
    expense_date: expense?.expense_date ?? new Date().toISOString().slice(0, 10),
    category: expense?.category ?? "",
    status: expense?.status ?? "planned",
    essential: expense?.essential ?? false,
  };
}

export function ExpenseForm({ expense, busy, onSubmit, onCancel }: ExpenseFormProps) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaults(expense),
  });

  useEffect(() => reset(defaults(expense)), [expense, reset]);

  async function submit(values: FormValues) {
    await onSubmit({
      description: values.description.trim(),
      amount_minor: Math.round(values.amount * 100),
      expense_date: values.expense_date,
      category: values.category.trim().toLowerCase(),
      status: values.status,
      essential: values.essential,
    });
    if (!expense) reset(defaults());
  }

  return (
    <form className="expense-form" onSubmit={handleSubmit(submit)}>
      <div className="panel-heading">
        <div><p className="eyebrow">{expense ? "Update record" : "New record"}</p><h2>{expense ? "Edit expense" : "Add an expense"}</h2></div>
        <button type="button" className="icon-button" onClick={onCancel} aria-label="Close form">×</button>
      </div>
      <label>Description<input {...register("description")} placeholder="e.g. Weekly groceries" />{errors.description && <span className="field-error">{errors.description.message}</span>}</label>
      <div className="form-grid">
        <label>Amount (£)<input type="number" step="0.01" min="0.01" {...register("amount", { valueAsNumber: true })} />{errors.amount && <span className="field-error">{errors.amount.message}</span>}</label>
        <label>Date<input type="date" {...register("expense_date")} />{errors.expense_date && <span className="field-error">{errors.expense_date.message}</span>}</label>
      </div>
      <div className="form-grid">
        <label>Category<input {...register("category")} placeholder="groceries" />{errors.category && <span className="field-error">{errors.category.message}</span>}</label>
        <label>Status<select {...register("status")}><option value="planned">Planned</option><option value="cleared">Cleared</option></select></label>
      </div>
      <label className="checkbox-label"><input type="checkbox" {...register("essential")} /><span><strong>Essential expense</strong><small>Needed for basic living or contractual obligations</small></span></label>
      <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Saving…" : expense ? "Save changes" : "Add expense"}</button>
    </form>
  );
}
