"""Confirm the frozen RF/XGBoost ensemble recipe across training-only splits."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from calibrate_xgboost_threshold import (
    FIXED_FPR_LIMIT,
    MINIMUM_ATTACK_RECALL,
    build_reference,
    build_xgboost,
    probabilities,
    threshold_metrics,
)
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, sha256

RUN_ID = "rf-xgboost-ensemble-repeated-seed-confirmation-v1"
SEEDS = (42, 123, 2026)
XGBOOST_WEIGHT = 0.90
RANDOM_FOREST_WEIGHT = 0.10
FROZEN_THRESHOLD = 0.565


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    runs = []

    for seed in SEEDS:
        x_development, x_validation, y_development, y_validation = train_test_split(
            data[columns], data["label"].astype(int), test_size=0.15,
            stratify=data["label"], random_state=seed,
        )
        x_fit, _, y_fit, _ = train_test_split(
            x_development, y_development, test_size=0.15 / 0.85,
            stratify=y_development, random_state=seed,
        )
        rf = build_reference(columns)
        xgb_model = build_xgboost(columns)
        rf.set_params(model__random_state=seed)
        xgb_model.set_params(model__random_state=seed)
        started = time.perf_counter()
        rf.fit(x_fit, y_fit)
        xgb_model.fit(x_fit, y_fit)
        fit_seconds = time.perf_counter() - started

        rf_probability, _ = probabilities(rf, x_validation)
        xgb_probability, _ = probabilities(xgb_model, x_validation)
        reference = threshold_metrics(y_validation, rf_probability, 0.5)
        blended = RANDOM_FOREST_WEIGHT * rf_probability + XGBOOST_WEIGHT * xgb_probability
        ensemble = threshold_metrics(y_validation, blended, FROZEN_THRESHOLD)
        passes = bool(
            ensemble["false_positive_rate"] <= FIXED_FPR_LIMIT
            and ensemble["attack_recall"] >= MINIMUM_ATTACK_RECALL
            and ensemble["macro_f1"] > reference["macro_f1"]
        )
        runs.append({
            "seed": seed,
            "fit_seconds": fit_seconds,
            "reference_random_forest": reference,
            "ensemble": ensemble,
            "passes_validation_gates": passes,
        })
        print(
            f"seed={seed}: accuracy={ensemble['accuracy']:.6f}, "
            f"macro_f1={ensemble['macro_f1']:.6f}, recall={ensemble['attack_recall']:.6f}, "
            f"fpr={ensemble['false_positive_rate']:.6f}, pass={passes}",
            flush=True,
        )

    stable = all(run["passes_validation_gates"] for run in runs)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "three independent 70/15/15 official-training-only splits; fixed ensemble recipe; official test not loaded",
        "training_sha256": sha256(source),
        "seeds": list(SEEDS),
        "recipe": {
            "xgboost_weight": XGBOOST_WEIGHT,
            "random_forest_weight": RANDOM_FOREST_WEIGHT,
            "threshold": FROZEN_THRESHOLD,
        },
        "constraints": {
            "false_positive_rate_maximum": FIXED_FPR_LIMIT,
            "attack_recall_minimum": MINIMUM_ATTACK_RECALL,
            "macro_f1_must_beat_same_split_random_forest": True,
        },
        "runs": runs,
        "stable_across_seeds": stable,
        "promotion_status": (
            "confirmed training-only candidate; hold from official test pending research review"
            if stable else "rejected"
        ),
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Stable={stable}; saved {output}", flush=True)


if __name__ == "__main__":
    main()
