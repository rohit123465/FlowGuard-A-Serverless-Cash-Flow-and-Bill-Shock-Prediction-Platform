import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ForecastRequest } from "../../types/finance";

const schema = z.object({
  opening_balance: z.number().min(-1_000_000, "Enter a valid balance"),
  safety_buffer: z.number().nonnegative("Buffer cannot be negative"),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
  include_likely_income: z.boolean(),
  include_uncertain_income: z.boolean(),
}).refine((value) => value.end_date >= value.start_date, { message: "End date must be after the start date", path: ["end_date"] });
type FormValues = z.infer<typeof schema>;
interface Props { busy?: boolean; onRun(request: ForecastRequest): Promise<unknown>; }

function nextMonth(date: Date) { const result = new Date(date); result.setMonth(result.getMonth() + 1); return result.toISOString().slice(0, 10); }

export function ScenarioSimulator({ busy, onRun }: Props) {
  const today = new Date();
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { opening_balance: 1000, safety_buffer: 200, start_date: today.toISOString().slice(0, 10), end_date: nextMonth(today), include_likely_income: false, include_uncertain_income: false } });
  return <form className="scenario-panel" onSubmit={handleSubmit((values) => onRun({ opening_balance_minor: Math.round(values.opening_balance * 100), safety_buffer_minor: Math.round(values.safety_buffer * 100), start_date: values.start_date, end_date: values.end_date, include_likely_income: values.include_likely_income, include_uncertain_income: values.include_uncertain_income }))}>
    <div><p className="eyebrow">Scenario inputs</p><h2>Run a cash-flow forecast</h2><p className="muted">The calculation uses your stored expenses, income and commitments.</p></div>
    <div className="form-grid"><label>Opening balance (£)<input type="number" step="0.01" {...register("opening_balance", { valueAsNumber: true })} />{errors.opening_balance && <span className="field-error">{errors.opening_balance.message}</span>}</label><label>Safety buffer (£)<input type="number" min="0" step="0.01" {...register("safety_buffer", { valueAsNumber: true })} />{errors.safety_buffer && <span className="field-error">{errors.safety_buffer.message}</span>}</label></div>
    <div className="form-grid"><label>Start date<input type="date" {...register("start_date")} /></label><label>End date<input type="date" {...register("end_date")} />{errors.end_date && <span className="field-error">{errors.end_date.message}</span>}</label></div>
    <div className="forecast-options"><label className="checkbox-label"><input type="checkbox" {...register("include_likely_income")} /><span><strong>Include likely income</strong><small>Useful for an optimistic comparison</small></span></label><label className="checkbox-label"><input type="checkbox" {...register("include_uncertain_income")} /><span><strong>Include uncertain income</strong><small>Higher-risk scenario</small></span></label></div>
    <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Calculating…" : "Run forecast"}</button>
  </form>;
}
