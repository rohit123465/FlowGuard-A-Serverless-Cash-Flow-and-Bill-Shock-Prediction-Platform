import { useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { forecastApi } from "../api/endpoints";
import { ForecastChart } from "../features/forecast/ForecastChart";
import { SafeToSpendCard } from "../features/forecast/SafeToSpendCard";
import { ScenarioSimulator } from "../features/forecast/ScenarioSimulator";
import { useAuth } from "../hooks/useAuth";

export function ForecastPage() {
  const { getAccessToken } = useAuth(); const api = useMemo(() => forecastApi(getAccessToken), [getAccessToken]); const forecast = useMutation({ mutationFn: api.calculate });
  return <><div className="page-heading"><div><p className="eyebrow">Deterministic intelligence</p><h1>Cash-flow forecast</h1><p className="muted">Understand exactly when your balance may approach its safety buffer.</p></div></div>
    {forecast.error && <div className="alert alert-error" role="alert">{forecast.error instanceof Error ? forecast.error.message : "Forecast failed"}</div>}
    <div className="forecast-layout"><ScenarioSimulator busy={forecast.isPending} onRun={(request) => forecast.mutateAsync(request)} /><div className="forecast-output">{forecast.data ? <><SafeToSpendCard forecast={forecast.data} /><ForecastChart forecast={forecast.data} />{forecast.data.excluded_income_count > 0 && <div className="alert forecast-note">{forecast.data.excluded_income_count} lower-confidence income record(s) were excluded from this conservative scenario.</div>}</> : <div className="forecast-placeholder"><div>⌁</div><h2>Your projection will appear here</h2><p>Choose a balance, safety buffer and date range, then run the forecast.</p></div>}</div></div>
  </>;
}
