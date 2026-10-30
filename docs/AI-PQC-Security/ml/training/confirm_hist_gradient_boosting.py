"""Confirm the selected HistGradientBoosting recipe across fixed seeds."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, sha256
from validation_feature_selection_sweep import FPR_MAX, RECALL_MIN, REFERENCE_MACRO_F1
from validation_hist_gradient_boosting_sweep import CANDIDATES, build, choose_threshold, probabilities

RUN_ID = "hist-gradient-boosting-repeated-seed-confirmation-v1"
CANDIDATE_NAME = "hgb_leaf127_regularized"
PARAMETERS = CANDIDATES[CANDIDATE_NAME]
SEEDS = (42, 123, 2026)


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    runs = []
    for seed in SEEDS:
        development, validation = train_test_split(data, test_size=0.15, stratify=data["label"], random_state=seed)
        fit, calibration = train_test_split(development, test_size=0.15 / 0.85, stratify=development["label"], random_state=seed)
        candidate = build(columns, PARAMETERS, seed)
        started = time.perf_counter()
        candidate.fit(fit[columns], fit["label"].astype(int))
        training_seconds = time.perf_counter() - started
        calibration_values, calibration_elapsed = probabilities(candidate, calibration[columns])
        selected, feasible_count = choose_threshold(calibration["label"].astype(int), calibration_values, calibration_elapsed)
        if selected is None:
            raise RuntimeError(f"Seed {seed} had no feasible calibration threshold")
        validation_values, validation_elapsed = probabilities(candidate, validation[columns])
        result = threshold_metrics(validation["label"].astype(int), validation_values, selected["threshold"], validation_elapsed)
        passes = bool(result["false_positive_rate"] <= FPR_MAX and result["attack_recall"] >= RECALL_MIN and result["macro_f1"] > REFERENCE_MACRO_F1)
        runs.append({"seed": seed, "training_seconds": training_seconds, "iterations_used": int(candidate.named_steps["model"].n_iter_), "feasible_calibration_thresholds": feasible_count, "selected_threshold": selected["threshold"], "validation": result, "passes_validation_gates": passes})
        print(f"seed={seed}: threshold={selected['threshold']:.3f}, accuracy={result['accuracy']:.6f}, macro_f1={result['macro_f1']:.6f}, recall={result['attack_recall']:.6f}, fpr={result['false_positive_rate']:.6f}, pass={passes}", flush=True)
    thresholds = sorted(float(run["selected_threshold"]) for run in runs)
    stable = all(run["passes_validation_gates"] for run in runs)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "three independent 70/15/15 official-training-only splits; official test not loaded",
        "training_sha256": sha256(source),
        "seeds": list(SEEDS),
        "candidate_name": CANDIDATE_NAME,
        "parameters": PARAMETERS,
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
