import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/endpoints";
import { MonthlyAnalytics } from "../features/analytics/MonthlyAnalytics";
import { useAuth } from "../hooks/useAuth";

export function AnalyticsPage() {
  const { getAccessToken } = useAuth(); const api = useMemo(() => analyticsApi(getAccessToken), [getAccessToken]); const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7)); const [year, month] = period.split("-").map(Number);
  const query = useQuery({ queryKey: ["analytics", year, month], queryFn: () => api.monthly(year, month) });
  return <><div className="page-heading"><div><p className="eyebrow">Monthly patterns</p><h1>Analytics</h1><p className="muted">A simple summary of expected income, recorded spending, net cash flow and category concentration. These are descriptive statistics—not financial advice or an ML prediction.</p></div><label className="month-picker standalone">Period<input type="month" value={period} onChange={(event) => setPeriod(event.target.value)} /></label></div>
    {query.error && <div className="alert alert-error" role="alert">{query.error instanceof Error ? query.error.message : "Analytics could not be loaded"}</div>}
    {query.isLoading ? <div className="forecast-placeholder"><h2>Computing monthly analytics…</h2></div> : query.data && <MonthlyAnalytics analytics={query.data} />}
  </>;
}
