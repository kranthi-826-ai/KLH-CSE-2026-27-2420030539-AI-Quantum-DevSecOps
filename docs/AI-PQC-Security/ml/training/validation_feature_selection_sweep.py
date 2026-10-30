"""Evaluate training-only feature selection for the calibrated XGBoost model."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, preprocessor, sha256

RUN_ID = "xgboost-feature-selection-validation-v1"
FPR_MAX = 0.0604464285714286
RECALL_MIN = 0.954570991662826
REFERENCE_MACRO_F1 = 0.9486477207065251
FEATURE_COUNTS = (20, 30, 40, 60)
XGB_PARAMETERS = {
    "n_estimators": 260,
    "max_depth": 8,
    "learning_rate": 0.06,
    "min_child_weight": 5,
    "subsample": 0.80,
    "colsample_bytree": 0.80,
    "reg_alpha": 0.05,
    "reg_lambda": 1.5,
}


def build(columns: list[str], feature_count: int) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("select", SelectKBest(score_func=f_classif, k=feature_count)),
        ("model", xgb.XGBClassifier(
            **XGB_PARAMETERS, objective="binary:logistic", eval_metric="logloss",
            tree_method="hist", n_jobs=2, random_state=SEED,
        )),
    ])


def probabilities(model: Pipeline, features: pd.DataFrame) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    values = model.predict_proba(features)[:, 1]
    return values, time.perf_counter() - started


def select_threshold(labels, probability_values, elapsed) -> tuple[dict | None, int]:
    results = []
    for threshold in np.round(np.arange(0.35, 0.851, 0.005), 3):
        result = threshold_metrics(labels, probability_values, float(threshold), elapsed)
        result["feasible"] = bool(
            result["false_positive_rate"] <= FPR_MAX
            and result["attack_recall"] >= RECALL_MIN
        )
        results.append(result)
    feasible = [item for item in results if item["feasible"]]
    return max(feasible, key=lambda item: item["macro_f1"], default=None), len(feasible)


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    x_development, x_validation, y_development, y_validation = train_test_split(
        data[columns], data["label"].astype(int), test_size=0.15,
        stratify=data["label"], random_state=SEED,
    )
    x_fit, x_calibration, y_fit, y_calibration = train_test_split(
        x_development, y_development, test_size=0.15 / 0.85,
        stratify=y_development, random_state=SEED,
    )
    print(f"{RUN_ID}: fit={len(x_fit)}, calibration={len(x_calibration)}, validation={len(x_validation)}; official test is not loaded.", flush=True)
    results = {}
    for feature_count in FEATURE_COUNTS:
        name = f"xgb_select_{feature_count}"
        candidate = build(columns, feature_count)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        training_seconds = time.perf_counter() - started
        calibration_probabilities, calibration_elapsed = probabilities(candidate, x_calibration)
        selected, feasible_count = select_threshold(y_calibration, calibration_probabilities, calibration_elapsed)
        validation = None
        passes = False
        selected_features: list[str] = []
        if selected is not None:
            validation_probabilities, validation_elapsed = probabilities(candidate, x_validation)
            validation = threshold_metrics(y_validation, validation_probabilities, selected["threshold"], validation_elapsed)
            passes = bool(
                validation["false_positive_rate"] <= FPR_MAX
                and validation["attack_recall"] >= RECALL_MIN
                and validation["macro_f1"] > REFERENCE_MACRO_F1
            )
            transformed = candidate.named_steps["preprocess"].get_feature_names_out()
            mask = candidate.named_steps["select"].get_support()
            selected_features = [str(value) for value in transformed[mask]]
        results[name] = {
            "feature_count": feature_count,
            "training_seconds": training_seconds,
            "feasible_calibration_thresholds": feasible_count,
            "selected_calibration": selected,
            "validation": validation,
            "selected_features": selected_features,
            "clears_validation_gates": passes,
        }
        if validation:
            print(f"{name}: threshold={selected['threshold']:.3f}, accuracy={validation['accuracy']:.6f}, macro_f1={validation['macro_f1']:.6f}, recall={validation['attack_recall']:.6f}, fpr={validation['false_positive_rate']:.6f}, eligible={passes}", flush=True)
        else:
            print(f"{name}: no feasible calibration threshold", flush=True)
    eligible = [name for name, item in results.items() if item["clears_validation_gates"]]
    winner = max(eligible, key=lambda name: results[name]["validation"]["macro_f1"], default=None)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "feature selection fitted inside each training pipeline; 70/15/15 official-training-only split; official test not loaded",
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "selection_method": "SelectKBest(f_classif)",
        "selection_metric": "validation_macro_f1",
        "constraints": {"false_positive_rate_maximum": FPR_MAX, "attack_recall_minimum": RECALL_MIN, "same_split_reference_macro_f1": REFERENCE_MACRO_F1},
        "model_parameters": XGB_PARAMETERS,
        "split": {"fit": len(x_fit), "calibration": len(x_calibration), "validation": len(x_validation)},
        "candidates": results,
        "eligible_candidates": eligible,
        "validation_winner": winner,
        "promotion_status": "validation candidates only; no official-test evaluation or promotion",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}. Validation winner: {winner}")


if __name__ == "__main__":
    main()
