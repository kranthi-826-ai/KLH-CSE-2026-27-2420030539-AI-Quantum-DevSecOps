"""Bounded calibrated XGBoost tuning using training data only.

Candidate parameters and constraints are fixed in this file before fitting.
The official UNSW-NB15 test CSV is intentionally never loaded.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, preprocessor, sha256

RUN_ID = "xgboost-tuning-validation-sweep-v1"
FPR_MAX = 0.0604464285714286
RECALL_MIN = 0.954570991662826
# Same-split Random Forest validation macro-F1 from the existing 70/15/15
# protocol. A candidate must exceed this, not merely its own calibration score.
REFERENCE_MACRO_F1 = 0.9486477207065251

CANDIDATES = {
    "xgb_depth7_regularized": {
        "n_estimators": 420, "max_depth": 7, "learning_rate": 0.045,
        "min_child_weight": 5, "subsample": 0.88, "colsample_bytree": 0.88,
        "reg_alpha": 0.08, "reg_lambda": 2.0,
    },
    "xgb_depth9_regularized": {
        "n_estimators": 360, "max_depth": 9, "learning_rate": 0.045,
        "min_child_weight": 8, "subsample": 0.80, "colsample_bytree": 0.80,
        "reg_alpha": 0.10, "reg_lambda": 2.5,
    },
    "xgb_depth6_stable": {
        "n_estimators": 500, "max_depth": 6, "learning_rate": 0.040,
        "min_child_weight": 4, "subsample": 0.90, "colsample_bytree": 0.90,
        "reg_alpha": 0.05, "reg_lambda": 1.8,
    },
}


def build(columns: list[str], params: dict) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", xgb.XGBClassifier(
            **params, objective="binary:logistic", eval_metric="logloss",
            tree_method="hist", n_jobs=2, random_state=SEED,
        )),
    ])


def probability_values(model: Pipeline, features: pd.DataFrame) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    values = model.predict_proba(features)[:, 1]
    return values, time.perf_counter() - started


def choose_threshold(labels: pd.Series, probabilities: np.ndarray, elapsed: float) -> tuple[dict | None, int]:
    options = []
    for threshold in np.round(np.arange(0.35, 0.851, 0.005), 3):
        result = threshold_metrics(labels, probabilities, float(threshold), elapsed)
        result["feasible"] = bool(
            result["false_positive_rate"] <= FPR_MAX
            and result["attack_recall"] >= RECALL_MIN
        )
        options.append(result)
    feasible = [option for option in options if option["feasible"]]
    return max(feasible, key=lambda option: option["macro_f1"], default=None), len(feasible)


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; run validate_unsw_nb15.py first")
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
    for name, params in CANDIDATES.items():
        candidate = build(columns, params)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        training_seconds = time.perf_counter() - started
        calibration_probs, calibration_elapsed = probability_values(candidate, x_calibration)
        chosen, feasible_count = choose_threshold(y_calibration, calibration_probs, calibration_elapsed)
        validation = None
        passes = False
        if chosen is not None:
            validation_probs, validation_elapsed = probability_values(candidate, x_validation)
            validation = threshold_metrics(y_validation, validation_probs, chosen["threshold"], validation_elapsed)
            passes = bool(
                validation["false_positive_rate"] <= FPR_MAX
                and validation["attack_recall"] >= RECALL_MIN
                and validation["macro_f1"] > REFERENCE_MACRO_F1
            )
        results[name] = {
            "parameters": params,
            "training_seconds": training_seconds,
            "feasible_calibration_thresholds": feasible_count,
            "selected_calibration": chosen,
            "validation": validation,
            "clears_validation_gates": passes,
        }
        if validation:
            print(f"{name}: threshold={chosen['threshold']:.3f}, accuracy={validation['accuracy']:.6f}, macro_f1={validation['macro_f1']:.6f}, attack_recall={validation['attack_recall']:.6f}, fpr={validation['false_positive_rate']:.6f}, eligible={passes}, seconds={training_seconds:.1f}", flush=True)
        else:
            print(f"{name}: no threshold met calibration constraints, seconds={training_seconds:.1f}", flush=True)
    eligible = [name for name, item in results.items() if item["clears_validation_gates"]]
    winner = max(eligible, key=lambda name: results[name]["validation"]["macro_f1"], default=None)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "70/15/15 fit-calibration-validation from official training CSV; official test not loaded",
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "selection_metric": "validation_macro_f1",
        "constraints": {"false_positive_rate_maximum": FPR_MAX, "attack_recall_minimum": RECALL_MIN, "same_split_random_forest_macro_f1": REFERENCE_MACRO_F1},
        "split": {"fit": len(x_fit), "calibration": len(x_calibration), "validation": len(x_validation)},
        "candidates": results,
        "eligible_candidates": eligible,
        "validation_winner": winner,
        "promotion_status": "validation candidates only; no official-test evaluation or promotion",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}. Validation winner: {winner}", flush=True)


if __name__ == "__main__":
    main()
