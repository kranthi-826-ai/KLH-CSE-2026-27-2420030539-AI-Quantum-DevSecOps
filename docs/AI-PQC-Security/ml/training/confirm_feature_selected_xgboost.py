"""Confirm the 60-feature calibrated XGBoost recipe across fixed seeds."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, sha256
from validation_feature_selection_sweep import (
    FPR_MAX,
    RECALL_MIN,
    REFERENCE_MACRO_F1,
    build,
    probabilities,
    select_threshold,
)

RUN_ID = "xgboost-select60-repeated-seed-confirmation-v1"
SEEDS = (42, 123, 2026)
FEATURE_COUNT = 60


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
        x_fit, x_calibration, y_fit, y_calibration = train_test_split(
            x_development, y_development, test_size=0.15 / 0.85,
            stratify=y_development, random_state=seed,
        )
        candidate = build(columns, FEATURE_COUNT)
        candidate.set_params(model__random_state=seed)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        training_seconds = time.perf_counter() - started
        calibration_probabilities, calibration_elapsed = probabilities(candidate, x_calibration)
        selected, feasible_count = select_threshold(y_calibration, calibration_probabilities, calibration_elapsed)
        if selected is None:
            raise RuntimeError(f"Seed {seed} had no feasible calibration threshold")
        validation_probabilities, validation_elapsed = probabilities(candidate, x_validation)
        from calibrate_xgboost_threshold import threshold_metrics
        validation = threshold_metrics(y_validation, validation_probabilities, selected["threshold"], validation_elapsed)
        passes = bool(
            validation["false_positive_rate"] <= FPR_MAX
            and validation["attack_recall"] >= RECALL_MIN
            and validation["macro_f1"] > REFERENCE_MACRO_F1
        )
        transformed = candidate.named_steps["preprocess"].get_feature_names_out()
        selected_features = [str(value) for value in transformed[candidate.named_steps["select"].get_support()]]
        runs.append({
            "seed": seed,
            "training_seconds": training_seconds,
            "feasible_calibration_thresholds": feasible_count,
            "selected_threshold": selected["threshold"],
            "validation": validation,
            "selected_features": selected_features,
            "passes_validation_gates": passes,
        })
        print(f"seed={seed}: threshold={selected['threshold']:.3f}, accuracy={validation['accuracy']:.6f}, macro_f1={validation['macro_f1']:.6f}, recall={validation['attack_recall']:.6f}, fpr={validation['false_positive_rate']:.6f}, pass={passes}", flush=True)
    thresholds = sorted(float(run["selected_threshold"]) for run in runs)
    stable = all(run["passes_validation_gates"] for run in runs)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "three independent 70/15/15 official-training-only splits; feature selection fitted inside each pipeline; official test not loaded",
        "training_sha256": sha256(source),
        "seeds": list(SEEDS),
        "feature_count": FEATURE_COUNT,
        "constraints": {"false_positive_rate_maximum": FPR_MAX, "attack_recall_minimum": RECALL_MIN, "same_split_reference_macro_f1": REFERENCE_MACRO_F1},
        "runs": runs,
        "recommended_frozen_threshold": thresholds[len(thresholds) // 2],
        "stable_across_seeds": stable,
        "promotion_status": "confirmed validation candidate only; eligible for one frozen official-test evaluation" if stable else "rejected",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Stable={stable}; frozen threshold={report['recommended_frozen_threshold']:.3f}; saved {output}")


if __name__ == "__main__":
    main()
