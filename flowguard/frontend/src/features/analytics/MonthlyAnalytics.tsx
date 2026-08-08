import type { MonthlyAnalyticsResult } from "../../types/finance";

interface Props { analytics: MonthlyAnalyticsResult; }
const pounds = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

export function MonthlyAnalytics({ analytics }: Props) {
  const positive = analytics.net_cash_flow_minor >= 0;
  return <>
    <section className="summary-grid analytics-summary">
      <div className="summary-card"><span>Expected income</span><strong className="positive">{pounds.format(analytics.total_income_minor / 100)}</strong><small>{analytics.income_count} income records</small></div>
      <div className="summary-card"><span>Total expenses</span><strong>{pounds.format(analytics.total_expenses_minor / 100)}</strong><small>{analytics.expense_count} expense records</small></div>
      <div className={`summary-card ${positive ? "accent-green" : "accent"}`}><span>Net cash flow</span><strong className={positive ? "positive" : "negative"}>{positive ? "+" : "−"}{pounds.format(Math.abs(analytics.net_cash_flow_minor) / 100)}</strong><small>Income minus expenses</small></div>
    </section>
    <div className="analytics-grid">
      <section className="panel analytics-panel"><div className="panel-heading"><div><p className="eyebrow">Spending mix</p><h2>Where the money went</h2></div></div>
        {!analytics.category_breakdown.length ? <div className="empty-state"><h3>No spending to analyse</h3><p>Add expenses in this month to see category patterns.</p></div> : <div className="category-bars">{analytics.category_breakdown.map((item) => <article key={item.category}><div><strong>{item.category}</strong><span>{pounds.format(item.amount_minor / 100)} · {item.percentage}%</span></div><div className="bar-track"><span style={{ width: `${item.percentage}%` }} /></div></article>)}</div>}
      </section>
      <section className="insight-panel"><p className="eyebrow">Monthly interpretation</p><h2>{analytics.savings_rate_percent === null ? "Add income to calculate savings" : `${analytics.savings_rate_percent}% savings rate`}</h2><p>Savings rate shows the percentage of expected income left after recorded expenses. A negative value means spending is higher than expected income.</p>
        <dl><div><dt>Essential spending</dt><dd>{pounds.format(analytics.essential_expenses_minor / 100)}</dd></div><div><dt>Discretionary spending</dt><dd>{pounds.format(analytics.discretionary_expenses_minor / 100)}</dd></div><div><dt>Top category</dt><dd>{analytics.highest_spending_category ?? "None yet"}</dd></div></dl>
      </section>
    </div>
  </>;
}
