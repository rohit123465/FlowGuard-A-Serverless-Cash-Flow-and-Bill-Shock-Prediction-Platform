import type { RiskPrediction } from "../../types/finance";

function preventionGuidance(prediction: RiskPrediction): string[] {
  const features = prediction.features;
  const guidance: string[] = [];

  if ((features.balance_buffer_gap_ratio ?? 0) < 0) {
    guidance.push("Top up your balance until it reaches the safety buffer, or temporarily lower the buffer only if that target is no longer realistic.");
  }
  if ((features.commitment_outflow_ratio ?? 0) > 0.5) {
    guidance.push("Review upcoming commitments and move, reduce or cancel any flexible payment before its due date.");
  }
  if ((features.expense_outflow_ratio ?? 0) > 0.5) {
    guidance.push("Reduce or postpone non-essential planned expenses during this forecast period.");
  }
  if ((features.days_to_next_guaranteed_income ?? 0) > 14) {
    guidance.push("Plan for the gap until your next guaranteed income and avoid relying on uncertain income until it arrives.");
  }
  if (prediction.risk_level !== "low" && guidance.length < 2) {
    guidance.push("Increase your opening balance, lower upcoming outgoings, or shorten the period before your next guaranteed income.");
  }
  if (guidance.length === 0) {
    guidance.push("Keep your records up to date and preserve the amount currently held above your safety buffer.");
  }

  return guidance.slice(0, 3);
}

export function RiskPredictionCard({ prediction }: { prediction: RiskPrediction }) {
  const percent = Math.round(prediction.probability * 100);
  const guidance = preventionGuidance(prediction);

  return <section className={`risk-card ${prediction.risk_level}`}>
    <div className="risk-summary">
      <p className="eyebrow">Experimental ML baseline</p>
      <h2>{percent}% estimated shortfall risk</h2>
      <span className="risk-level">{prediction.risk_level} risk</span>
      <p className="risk-meaning">This estimates the chance that your balance will fall below your chosen safety buffer during this forecast.</p>
    </div>
    <div>
      <strong>Factors influencing this estimate</strong>
      <ul>{prediction.explanation.map((item) => <li key={item}>{item}</li>)}</ul>
    </div>
    <aside className="risk-guidance">
      <strong>Ways to reduce the estimated risk</strong>
      <p>Try the relevant actions below, then run the forecast again to compare the percentage.</p>
      <ol>{guidance.map((item) => <li key={item}>{item}</li>)}</ol>
    </aside>
    <footer><strong>{prediction.model_version}</strong> · Logistic regression · Synthetic training data<p>{prediction.disclaimer}</p></footer>
  </section>;
}
