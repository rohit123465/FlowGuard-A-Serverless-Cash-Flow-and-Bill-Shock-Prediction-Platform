from pydantic import BaseModel, ConfigDict, Field


class RiskPrediction(BaseModel):
    model_config = ConfigDict(frozen=True)

    probability: float = Field(ge=0, le=1)
    risk_level: str
    model_version: str
    model_type: str
    training_data: str
    features: dict[str, float]
    explanation: tuple[str, ...]
    disclaimer: str
