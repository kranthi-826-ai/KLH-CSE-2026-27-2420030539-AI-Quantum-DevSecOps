"""Calibrate an unweighted Random Forest without loading the official test set."""

from __future__ import annotations

import json
import time
import argparse
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from calibrate_xgboost_threshold import probabilities, threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, preprocessor, sha256

RUN_ID = "random-forest-unweighted-threshold-calibration-v1"
FPR_MAX = 0.0604464285714286
RECALL_MIN = 0.954570991662826
REFERENCE_MACRO_F1 = 0.9486477207065251


def build(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", RandomForestClassifier(
            n_estimators=250, max_depth=24, min_samples_leaf=2,
            class_weight=None, n_jobs=4, random_state=SEED,
        )),
    ])


def select_threshold(labels, probabilities_values, elapsed):
    results = []
    for threshold in np.round(np.arange(0.35, 0.851, 0.005), 3):
        result = threshold_metrics(labels, probabilities_values, float(threshold), elapsed)
        result["feasible"] = bool(
            result["false_positive_rate"] <= FPR_MAX
            and result["attack_recall"] >= RECALL_MIN
        )
        results.append(result)
    feasible = [item for item in results if item["feasible"]]
    return max(feasible, key=lambda item: item["macro_f1"], default=None), len(feasible)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    run_seed = args.seed
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; run validate_unsw_nb15.py first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    x_development, x_validation, y_development, y_validation = train_test_split(
        data[columns], data["label"].astype(int), test_size=0.15,
        stratify=data["label"], random_state=run_seed,
    )
    x_fit, x_calibration, y_fit, y_calibration = train_test_split(
        x_development, y_development, test_size=0.15 / 0.85,
        stratify=y_development, random_state=run_seed,
    )
    print(f"{RUN_ID}: fit={len(x_fit)}, calibration={len(x_calibration)}, validation={len(x_validation)}; official test is not loaded.", flush=True)
    candidate = build(columns)
    candidate.set_params(model__random_state=run_seed)
    started = time.perf_counter()
    candidate.fit(x_fit, y_fit)
    training_seconds = time.perf_counter() - started
    calibration_probs, calibration_elapsed = probabilities(candidate, x_calibration)
    selected, feasible_count = select_threshold(y_calibration, calibration_probs, calibration_elapsed)
    validation = None
    passes = False
    if selected is not None:
        validation_probs, validation_elapsed = probabilities(candidate, x_validation)
        validation = threshold_metrics(y_validation, validation_probs, selected["threshold"], validation_elapsed)
        passes = bool(
            validation["false_positive_rate"] <= FPR_MAX
            and validation["attack_recall"] >= RECALL_MIN
            and validation["macro_f1"] > REFERENCE_MACRO_F1
        )
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "70/15/15 fit-calibration-validation from official training CSV; official test not loaded",
        "seed": run_seed,
        "training_sha256": sha256(source),
        "model": {"family": "RandomForestClassifier", "class_weight": None, "n_estimators": 250, "max_depth": 24, "min_samples_leaf": 2},
        "constraints": {"false_positive_rate_maximum": FPR_MAX, "attack_recall_minimum": RECALL_MIN, "same_split_reference_macro_f1": REFERENCE_MACRO_F1},
        "split": {"fit": len(x_fit), "calibration": len(x_calibration), "validation": len(x_validation)},
        "training_seconds": training_seconds,
        "feasible_calibration_thresholds": feasible_count,
        "selected_calibration": selected,
        "validation": validation,
        "clears_validation_gates": passes,
        "promotion_status": "validation candidate only" if passes else "rejected",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}-seed{run_seed}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}. selected_threshold={None if selected is None else selected['threshold']}; validation_gates={passes}", flush=True)
    if validation:
        print(f"validation: accuracy={validation['accuracy']:.6f}, macro_f1={validation['macro_f1']:.6f}, attack_recall={validation['attack_recall']:.6f}, fpr={validation['false_positive_rate']:.6f}", flush=True)


if __name__ == "__main__":
    main()
