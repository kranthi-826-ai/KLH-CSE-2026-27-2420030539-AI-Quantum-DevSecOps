"""Calibrate the selected XGBoost candidate without touching official test data."""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, preprocessor, sha256

RUN_ID = "xgboost-threshold-calibration-v1"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "candidates"
FIXED_FPR_LIMIT = 0.0604464285714286
MINIMUM_ATTACK_RECALL = 0.954570991662826

XGB_PARAMETERS = {
    "n_estimators": 260,
    "max_depth": 8,
    "learning_rate": 0.06,
    "min_child_weight": 5,
    "subsample": 0.80,
    "colsample_bytree": 0.80,
}


def build_xgboost(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", xgb.XGBClassifier(
            **XGB_PARAMETERS,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            reg_alpha=0.05,
            reg_lambda=1.5,
            n_jobs=2,
            random_state=SEED,
        )),
    ])


def build_reference(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", RandomForestClassifier(
            n_estimators=250,
            max_depth=24,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            # The reference is the slowest step. Use the available logical
            # processors so the bounded local experiment does not appear hung.
            n_jobs=-1,
            random_state=SEED,
        )),
    ])


def threshold_metrics(labels: pd.Series, probabilities: np.ndarray,
                      threshold: float, elapsed: float = 0.0) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    macro = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        labels, predictions, average="weighted", zero_division=0
    )
    attack = precision_recall_fscore_support(
        labels, predictions, labels=[1], average=None, zero_division=0
    )
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_precision": float(macro[0]),
        "macro_recall": float(macro[1]),
        "macro_f1": float(macro[2]),
        "weighted_precision": float(weighted[0]),
        "weighted_recall": float(weighted[1]),
        "weighted_f1": float(weighted[2]),
        "attack_precision": float(attack[0][0]),
        "attack_recall": float(attack[1][0]),
        "attack_f1": float(attack[2][0]),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
        "inference_total_seconds": float(elapsed),
        "inference_ms_per_sample": float(elapsed * 1000 / len(labels)),
        "confusion_matrix": [[int(value) for value in row] for row in matrix],
        "samples": int(len(labels)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def probabilities(model: Pipeline, features: pd.DataFrame) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    values = model.predict_proba(features)[:, 1]
    return values, time.perf_counter() - started


def main() -> None:
    # Only the official training partition is read during calibration/selection.
    source = FILES["training"][0]
    data = pd.read_csv(source)
    if len(data) != FILES["training"][1]:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    features = data[columns]
    labels = data["label"].astype(int)

    # 70% fit, 15% calibration, 15% untouched validation.
    x_development, x_validation, y_development, y_validation = train_test_split(
        features, labels, test_size=0.15, stratify=labels, random_state=SEED,
    )
    x_fit, x_calibration, y_fit, y_calibration = train_test_split(
        x_development,
        y_development,
        test_size=0.15 / 0.85,
        stratify=y_development,
        random_state=SEED,
    )
    print(
        f"{RUN_ID}: fit={len(x_fit)}, calibration={len(x_calibration)}, "
        f"validation={len(x_validation)}; official test is not loaded.", flush=True,
    )

    candidate = build_xgboost(columns)
    print("Training selected XGBoost candidate...", flush=True)
    started = time.perf_counter()
    candidate.fit(x_fit, y_fit)
    candidate_training_seconds = time.perf_counter() - started
    print(f"XGBoost fit completed in {candidate_training_seconds:.1f}s.", flush=True)

    calibration_probabilities, calibration_elapsed = probabilities(
        candidate, x_calibration
    )
    threshold_results = []
    for threshold in np.round(np.arange(0.30, 0.901, 0.005), 3):
        result = threshold_metrics(
            y_calibration, calibration_probabilities, float(threshold),
            calibration_elapsed,
        )
        result["feasible"] = bool(
            result["false_positive_rate"] <= FIXED_FPR_LIMIT
            and result["attack_recall"] >= MINIMUM_ATTACK_RECALL
        )
        threshold_results.append(result)

    feasible = [result for result in threshold_results if result["feasible"]]
    selected = max(feasible, key=lambda result: result["macro_f1"], default=None)
    print(
        f"Threshold search completed: {len(feasible)} feasible thresholds; "
        f"selected={None if selected is None else selected['threshold']}.",
        flush=True,
    )

    reference = build_reference(columns)
    print("Training same-split Random Forest reference; please do not interrupt...", flush=True)
    reference_started = time.perf_counter()
    reference.fit(x_fit, y_fit)
    reference_training_seconds = time.perf_counter() - reference_started
    print(f"Random Forest fit completed in {reference_training_seconds:.1f}s.", flush=True)
    reference_probabilities, reference_elapsed = probabilities(reference, x_validation)
    reference_validation = threshold_metrics(
        y_validation, reference_probabilities, 0.5, reference_elapsed
    )

    selected_validation = None
    clears_validation_gates = False
    if selected is not None:
        validation_probabilities, validation_elapsed = probabilities(
            candidate, x_validation
        )
        selected_validation = threshold_metrics(
            y_validation,
            validation_probabilities,
            selected["threshold"],
            validation_elapsed,
        )
        clears_validation_gates = bool(
            selected_validation["false_positive_rate"] <= FIXED_FPR_LIMIT
            and selected_validation["attack_recall"] >= MINIMUM_ATTACK_RECALL
            and selected_validation["macro_f1"] > reference_validation["macro_f1"]
        )

    summary = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "70/15/15 fit-calibration-validation from official training CSV; official test not loaded",
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgb.__version__,
        },
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "split": {
            "fit": len(x_fit),
            "calibration": len(x_calibration),
            "validation": len(x_validation),
        },
        "selection_constraints": {
            "false_positive_rate_maximum": FIXED_FPR_LIMIT,
            "attack_recall_minimum": MINIMUM_ATTACK_RECALL,
            "selection_metric": "calibration_macro_f1",
        },
        "candidate": {
            "name": "xgb_depth8_regularized",
            "parameters": XGB_PARAMETERS,
            "training_seconds": candidate_training_seconds,
        },
        "threshold_search": {
            "start": 0.30, "stop": 0.90, "step": 0.005,
            "evaluated": len(threshold_results),
            "feasible_count": len(feasible),
            "selected_calibration": selected,
        },
        "reference_random_forest": {
            "training_seconds": reference_training_seconds,
            "validation": reference_validation,
        },
        "candidate_validation": selected_validation,
        "clears_validation_gates": clears_validation_gates,
        "promotion_status": "validation candidate only" if clears_validation_gates else "rejected",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if clears_validation_gates:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"pipeline": candidate, "threshold": selected["threshold"],
             "run_id": RUN_ID},
            MODEL_DIR / f"{RUN_ID}.joblib",
        )

    print(
        f"Selected threshold: {None if selected is None else selected['threshold']}; "
        f"validation gates passed: {clears_validation_gates}; saved {output}",
        flush=True,
    )
    if selected_validation:
        print(
            f"Candidate validation: accuracy={selected_validation['accuracy']:.6f}, "
            f"macro_f1={selected_validation['macro_f1']:.6f}, "
            f"attack_recall={selected_validation['attack_recall']:.6f}, "
            f"fpr={selected_validation['false_positive_rate']:.6f}", flush=True,
        )
        print(
            f"Reference validation: accuracy={reference_validation['accuracy']:.6f}, "
            f"macro_f1={reference_validation['macro_f1']:.6f}, "
            f"attack_recall={reference_validation['attack_recall']:.6f}, "
            f"fpr={reference_validation['false_positive_rate']:.6f}", flush=True,
        )


if __name__ == "__main__":
    main()
