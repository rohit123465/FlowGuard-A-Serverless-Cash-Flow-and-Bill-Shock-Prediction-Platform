import type { ForecastResult } from "../../types/finance";

const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });
interface Props { forecast: ForecastResult; }

export function SafeToSpendCard({ forecast }: Props) {
  const hasShortfall = forecast.first_shortfall_date !== null;
  return <section className={`forecast-hero ${hasShortfall ? "risk" : "safe"}`}>
    <div><p className="eyebrow">Safe to spend</p><strong>{pounds.format(forecast.safe_to_spend_minor / 100)}</strong><span>without crossing your {pounds.format(forecast.safety_buffer_minor / 100)} buffer</span></div>
    <div className="forecast-health"><span>{hasShortfall ? "Action needed" : "Buffer protected"}</span><h3>{hasShortfall ? `Pressure begins ${new Date(`${forecast.first_shortfall_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "long" })}` : "No buffer breach detected"}</h3><p>{hasShortfall ? `${pounds.format(forecast.shortfall_amount_minor / 100)} is needed to restore your buffer.` : `Lowest projected balance: ${pounds.format(forecast.minimum_balance_minor / 100)}.`}</p></div>
  </section>;
}
