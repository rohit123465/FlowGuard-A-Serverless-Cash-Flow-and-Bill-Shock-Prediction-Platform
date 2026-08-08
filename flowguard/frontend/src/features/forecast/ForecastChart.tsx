import type { ForecastResult } from "../../types/finance";

const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 });
interface Props { forecast: ForecastResult; }

export function ForecastChart({ forecast }: Props) {
  const balances = [forecast.opening_balance_minor, ...forecast.timeline.map((event) => event.projected_balance_minor), forecast.safety_buffer_minor];
  const min = Math.min(...balances); const max = Math.max(...balances); const span = Math.max(max - min, 1);
  const points = [{ label: "Opening", balance: forecast.opening_balance_minor }, ...forecast.timeline.map((event) => ({ label: event.description, balance: event.projected_balance_minor }))];
  return <section className="panel forecast-panel"><div className="panel-heading"><div><p className="eyebrow">Projected timeline</p><h2>Balance after each event</h2></div><span className="legend"><i />Safety buffer</span></div>
    {!forecast.timeline.length ? <div className="empty-state"><h3>No financial events in this period</h3><p>Add records or choose a wider forecast range.</p></div> : <div className="balance-chart" role="img" aria-label="Projected cash balance timeline">
      <div className="buffer-line" style={{ bottom: `${((forecast.safety_buffer_minor - min) / span) * 100}%` }}><span>{pounds.format(forecast.safety_buffer_minor / 100)} buffer</span></div>
      {points.map((point, index) => { const height = ((point.balance - min) / span) * 75 + 12; return <div className="chart-point" key={`${point.label}-${index}`}><div className={`chart-bar ${point.balance < forecast.safety_buffer_minor ? "below" : ""}`} style={{ height: `${height}%` }}><span>{pounds.format(point.balance / 100)}</span></div><small>{index === 0 ? "Start" : new Date(`${forecast.timeline[index - 1].event_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</small></div>; })}
    </div>}
    <div className="timeline-list">{forecast.timeline.map((event) => <article key={event.event_id}><span className={`event-dot ${event.event_type}`} /><div><strong>{event.description}</strong><small>{event.event_type} · {event.event_date}</small></div><span className={event.change_minor > 0 ? "positive" : ""}>{event.change_minor > 0 ? "+" : "−"}{pounds.format(Math.abs(event.change_minor) / 100)}</span><strong>{pounds.format(event.projected_balance_minor / 100)}</strong></article>)}</div>
  </section>;
}
