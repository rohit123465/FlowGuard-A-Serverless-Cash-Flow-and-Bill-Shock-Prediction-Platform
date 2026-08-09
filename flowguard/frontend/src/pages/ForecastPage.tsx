import { useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { forecastApi, riskApi } from "../api/endpoints";
import { ForecastChart } from "../features/forecast/ForecastChart";
import { RiskPredictionCard } from "../features/forecast/RiskPredictionCard";
import { SafeToSpendCard } from "../features/forecast/SafeToSpendCard";
import { ScenarioSimulator } from "../features/forecast/ScenarioSimulator";
import { useAuth } from "../hooks/useAuth";
import type { ForecastRequest } from "../types/finance";

export function ForecastPage() {
  const { getAccessToken } = useAuth();
  const deterministicApi = useMemo(() => forecastApi(getAccessToken), [getAccessToken]);
  const mlApi = useMemo(() => riskApi(getAccessToken), [getAccessToken]);
  const forecast = useMutation({ mutationFn: deterministicApi.calculate });
  const risk = useMutation({ mutationFn: mlApi.predict });
  async function run(request: ForecastRequest) {
    await Promise.all([forecast.mutateAsync(request), risk.mutateAsync(request)]);
  }
  const error = forecast.error ?? risk.error;
  return <><div className="page-heading"><div><p className="eyebrow">Forecast intelligence</p><h1>Cash-flow forecast</h1><p className="muted">Compare an exact deterministic timeline with an experimental probability from the logistic-regression baseline.</p></div></div>
    {error && <div className="alert alert-error" role="alert">{error instanceof Error ? error.message : "Forecast failed"}</div>}
    <div className="forecast-layout"><ScenarioSimulator busy={forecast.isPending || risk.isPending} onRun={run} /><div className="forecast-output">{forecast.data ? <><SafeToSpendCard forecast={forecast.data} />{risk.data && <RiskPredictionCard prediction={risk.data} />}<ForecastChart forecast={forecast.data} />{forecast.data.excluded_income_count > 0 && <div className="alert forecast-note">{forecast.data.excluded_income_count} lower-confidence income record(s) were excluded from this conservative scenario.</div>}</> : <div className="forecast-placeholder"><div>⌁</div><h2>Your projection will appear here</h2><p>Choose a balance, safety buffer and date range, then run both forecast layers.</p></div>}</div></div>
  </>;
}
