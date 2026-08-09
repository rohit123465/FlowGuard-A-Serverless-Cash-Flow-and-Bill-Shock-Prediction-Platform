import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskPredictionCard } from "./RiskPredictionCard";

describe("RiskPredictionCard", () => {
  it("labels the probability as experimental and synthetic", () => {
    render(<RiskPredictionCard prediction={{
      probability: 0.734,
      risk_level: "high",
      model_version: "baseline-logistic-v1",
      model_type: "logistic_regression",
      training_data: "synthetic",
      features: {},
      explanation: ["upcoming commitments increased estimated risk"],
      disclaimer: "Experimental estimate trained on synthetic scenarios; not financial advice.",
    }} />);
    expect(screen.getByText("73% estimated shortfall risk")).toBeInTheDocument();
    expect(screen.getByText(/Synthetic training data/i)).toBeInTheDocument();
    expect(screen.getByText(/not financial advice/i)).toBeInTheDocument();
  });

  it("shows prevention guidance based on the financial risk features", () => {
    render(<RiskPredictionCard prediction={{
      probability: 0.82,
      risk_level: "high",
      model_version: "baseline-logistic-v1",
      model_type: "logistic_regression",
      training_data: "synthetic",
      features: {
        balance_buffer_gap_ratio: -0.25,
        commitment_outflow_ratio: 0.8,
        expense_outflow_ratio: 0.2,
        days_to_next_guaranteed_income: 20,
      },
      explanation: ["upcoming commitments increased estimated risk"],
      disclaimer: "Experimental estimate trained on synthetic scenarios; not financial advice.",
    }} />);

    expect(screen.getByText("Ways to reduce the estimated risk")).toBeInTheDocument();
    expect(screen.getByText(/Top up your balance/i)).toBeInTheDocument();
    expect(screen.getByText(/Review upcoming commitments/i)).toBeInTheDocument();
    expect(screen.getByText(/run the forecast again/i)).toBeInTheDocument();
  });
});
