from __future__ import annotations

import os
import time
from hmac import compare_digest
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .model_service import InvalidFeaturesError, IntrusionModel, ModelUnavailableError
from .schemas import ModelStatus, PredictionRequest, PredictionResponse


def default_model_path() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    return repository_root / "ml" / "models" / "promoted" / "model.joblib"


def configured_model_path() -> Path:
    configured_path = os.getenv("AI_MODEL_PATH")
    return Path(configured_path) if configured_path else default_model_path()


model = IntrusionModel(configured_model_path())
app = FastAPI(title="AI-PQC AI Security Service", version="0.1.0")
REQUESTS = Counter("ai_security_requests_total", "AI service requests", ["path", "method", "status"])
LATENCY = Histogram("ai_security_request_duration_seconds", "AI service request latency", ["path"])
PREDICTIONS = Counter("ai_security_predictions_total", "AI risk predictions", ["risk_level", "predicted_attack"])


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = request.url.path
    REQUESTS.labels(route, request.method, str(response.status_code)).inc()
    LATENCY.labels(route).observe(time.perf_counter() - started)
    return response


def require_internal_api_key(
    x_internal_api_key: Annotated[str | None, Header()] = None,
) -> None:
    configured_key = os.getenv("MONITORING_API_KEY")
    if not configured_key:
        raise HTTPException(status_code=503, detail="Internal API key is not configured")
    if x_internal_api_key is None or not compare_digest(x_internal_api_key, configured_key):
        raise HTTPException(status_code=401, detail="A valid internal API key is required")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP" if model.ready else "DEGRADED"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/ai/model", response_model=ModelStatus)
def model_status() -> ModelStatus:
    return ModelStatus(
        ready=model.ready,
        model_name=model.MODEL_NAME,
        model_version=model.model_version,
        required_feature_count=len(model.required_features),
        detail="Model loaded" if model.ready else (model.load_error or "Model unavailable"),
    )


@app.post(
    "/api/v1/ai/predict",
    response_model=PredictionResponse,
    dependencies=[Depends(require_internal_api_key)],
)
def predict(request: PredictionRequest) -> PredictionResponse:
    try:
        result = model.predict(request)
        PREDICTIONS.labels(result.risk_level, str(result.predicted_attack).lower()).inc()
        return result
    except InvalidFeaturesError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except ModelUnavailableError as exception:
        raise HTTPException(status_code=503, detail=str(exception)) from exception
