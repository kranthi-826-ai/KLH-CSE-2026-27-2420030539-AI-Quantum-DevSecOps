from __future__ import annotations

import hashlib
from pathlib import Path

import joblib
import pandas as pd

from .schemas import PredictionRequest, PredictionResponse


class ModelUnavailableError(RuntimeError):
    pass


class InvalidFeaturesError(ValueError):
    pass


class IntrusionModel:
    MODEL_NAME = "unsw-nb15-random-forest"

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.pipeline = None
        self.model_version: str | None = None
        self.required_features: list[str] = []
        self.load_error: str | None = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.is_file():
            self.load_error = f"Model file not found: {self.model_path}"
            return
        try:
            self.pipeline = joblib.load(self.model_path)
            feature_names = getattr(self.pipeline, "feature_names_in_", None)
            if feature_names is None:
                raise ValueError("Model does not contain feature_names_in_")
            self.required_features = [str(name) for name in feature_names]
            self.model_version = self._sha256(self.model_path)[:16]
        except Exception as exception:  # startup status must remain inspectable
            self.pipeline = None
            self.load_error = f"Unable to load model: {exception}"

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @property
    def ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        if not self.ready:
            raise ModelUnavailableError(self.load_error or "Model is unavailable")
        missing = sorted(set(self.required_features).difference(request.features))
        unexpected = sorted(set(request.features).difference(self.required_features))
        if missing or unexpected:
            raise InvalidFeaturesError(
                f"Feature schema mismatch; missing={missing}, unexpected={unexpected}"
            )
        frame = pd.DataFrame(
            [[request.features[name] for name in self.required_features]],
            columns=self.required_features,
        )
        attack_probability = float(self.pipeline.predict_proba(frame)[0][1])
        predicted_attack = bool(self.pipeline.predict(frame)[0])
        risk_level = self.risk_level(attack_probability)
        return PredictionResponse(
            predicted_attack=predicted_attack,
            risk_score=attack_probability,
            risk_level=risk_level,
            model_version=self.model_version or "unknown",
            model_name=self.MODEL_NAME,
            correlation_id=request.correlation_id,
            explanation=(
                f"UNSW-NB15 model attack probability {attack_probability:.4f}; "
                f"threshold mapping selected {risk_level} risk"
            ),
        )

    @staticmethod
    def risk_level(score: float) -> str:
        if score >= 0.70:
            return "HIGH"
        if score >= 0.35:
            return "MEDIUM"
        return "LOW"
