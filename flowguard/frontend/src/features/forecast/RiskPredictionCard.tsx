import type { RiskPrediction } from "../../types/finance";

export function RiskPredictionCard({ prediction }: { prediction: RiskPrediction }) {
  const percent = Math.round(prediction.probability * 100);
  return <section className={`risk-card ${prediction.risk_level}`}>
    <div><p className="eyebrow">Experimental ML baseline</p><h2>{percent}% estimated shortfall risk</h2><span className="risk-level">{prediction.risk_level} risk</span></div>
    <div><strong>Factors influencing this estimate</strong><ul>{prediction.explanation.map((item) => <li key={item}>{item}</li>)}</ul></div>
    <footer><strong>{prediction.model_version}</strong> · Logistic regression · Synthetic training data<p>{prediction.disclaimer}</p></footer>
  </section>;
}
