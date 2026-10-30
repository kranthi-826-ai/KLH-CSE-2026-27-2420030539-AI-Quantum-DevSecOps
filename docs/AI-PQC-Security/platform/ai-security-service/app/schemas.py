from typing import Annotated

from pydantic import BaseModel, Field


FeatureValue = str | int | float


class PredictionRequest(BaseModel):
    features: dict[str, FeatureValue] = Field(min_length=1)
    correlation_id: str | None = Field(default=None, max_length=80)
    source_service: str = Field(default="external", min_length=1, max_length=80)


class PredictionResponse(BaseModel):
    predicted_attack: bool
    risk_score: Annotated[float, Field(ge=0.0, le=1.0)]
    risk_level: str
    model_version: str
    model_name: str
    correlation_id: str | None
    explanation: str


class ModelStatus(BaseModel):
    ready: bool
    model_name: str
    model_version: str | None
    required_feature_count: int
    detail: str
