"""Bounded HistGradientBoosting validation study on official training data."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, CATEGORICAL, EXCLUDED, FILES, SEED, sha256
from validation_feature_selection_sweep import FPR_MAX, RECALL_MIN, REFERENCE_MACRO_F1

RUN_ID = "hist-gradient-boosting-validation-sweep-v1"
CANDIDATES = {
    "hgb_leaf31": {"max_iter": 300, "learning_rate": 0.08, "max_leaf_nodes": 31, "min_samples_leaf": 25, "l2_regularization": 1.0},
    "hgb_leaf63": {"max_iter": 300, "learning_rate": 0.06, "max_leaf_nodes": 63, "min_samples_leaf": 30, "l2_regularization": 1.5},
    "hgb_leaf127_regularized": {"max_iter": 250, "learning_rate": 0.05, "max_leaf_nodes": 127, "min_samples_leaf": 40, "l2_regularization": 2.5},
}


def preprocessing(columns: list[str]) -> ColumnTransformer:
    categorical = [column for column in CATEGORICAL if column in columns]
    numeric = [column for column in columns if column not in categorical]
    return ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ]), categorical),
    ], sparse_threshold=0.0)


def build(columns: list[str], parameters: dict, seed: int = SEED) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessing(columns)),
        ("model", HistGradientBoostingClassifier(
            **parameters, random_state=seed, early_stopping=True,
            validation_fraction=0.10, n_iter_no_change=25,
        )),
    ])


def probabilities(model: Pipeline, features: pd.DataFrame) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    values = model.predict_proba(features)[:, 1]
    return values, time.perf_counter() - started


def choose_threshold(labels, values, elapsed) -> tuple[dict | None, int]:
    options = []
    for threshold in np.round(np.arange(0.35, 0.851, 0.005), 3):
        result = threshold_metrics(labels, values, float(threshold), elapsed)
        result["feasible"] = bool(result["false_positive_rate"] <= FPR_MAX and result["attack_recall"] >= RECALL_MIN)
        options.append(result)
    feasible = [item for item in options if item["feasible"]]
    return max(feasible, key=lambda item: item["macro_f1"], default=None), len(feasible)


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    development, validation = train_test_split(data, test_size=0.15, stratify=data["label"], random_state=SEED)
    fit, calibration = train_test_split(development, test_size=0.15 / 0.85, stratify=development["label"], random_state=SEED)
    print(f"{RUN_ID}: fit={len(fit)}, calibration={len(calibration)}, validation={len(validation)}; official test is not loaded.", flush=True)
    results = {}
    for name, parameters in CANDIDATES.items():
        candidate = build(columns, parameters)
        started = time.perf_counter()
        candidate.fit(fit[columns], fit["label"].astype(int))
        training_seconds = time.perf_counter() - started
        calibration_values, calibration_elapsed = probabilities(candidate, calibration[columns])
        selected, feasible_count = choose_threshold(calibration["label"].astype(int), calibration_values, calibration_elapsed)
        validation_result = None
        passes = False
        if selected is not None:
            validation_values, validation_elapsed = probabilities(candidate, validation[columns])
            validation_result = threshold_metrics(validation["label"].astype(int), validation_values, selected["threshold"], validation_elapsed)
            passes = bool(validation_result["false_positive_rate"] <= FPR_MAX and validation_result["attack_recall"] >= RECALL_MIN and validation_result["macro_f1"] > REFERENCE_MACRO_F1)
        results[name] = {"parameters": parameters, "iterations_used": int(candidate.named_steps["model"].n_iter_), "training_seconds": training_seconds, "feasible_calibration_thresholds": feasible_count, "selected_calibration": selected, "validation": validation_result, "clears_validation_gates": passes}
        if validation_result:
            print(f"{name}: iterations={candidate.named_steps['model'].n_iter_}, threshold={selected['threshold']:.3f}, accuracy={validation_result['accuracy']:.6f}, macro_f1={validation_result['macro_f1']:.6f}, recall={validation_result['attack_recall']:.6f}, fpr={validation_result['false_positive_rate']:.6f}, eligible={passes}", flush=True)
        else:
            print(f"{name}: no feasible calibration threshold", flush=True)
    eligible = [name for name, item in results.items() if item["clears_validation_gates"]]
    winner = max(eligible, key=lambda name: results[name]["validation"]["macro_f1"], default=None)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "70/15/15 official-training-only split; ordinal categorical encoding fitted inside pipeline; official test not loaded",
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "constraints": {"false_positive_rate_maximum": FPR_MAX, "attack_recall_minimum": RECALL_MIN, "same_split_reference_macro_f1": REFERENCE_MACRO_F1},
        "split": {"fit": len(fit), "calibration": len(calibration), "validation": len(validation)},
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
