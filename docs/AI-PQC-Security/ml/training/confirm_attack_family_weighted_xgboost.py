"""Confirm the selected attack-family-weighted XGBoost recipe across seeds."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, sha256
from validation_attack_family_weighting_sweep import WEIGHT_RECIPES
from validation_feature_selection_sweep import (
    FPR_MAX,
    RECALL_MIN,
    REFERENCE_MACRO_F1,
    XGB_PARAMETERS,
    probabilities,
    select_threshold,
)
from validation_xgboost_sweep import pipeline

RUN_ID = "xgboost-family-weighted-repeated-seed-confirmation-v1"
RECIPE_NAME = "fuzzer_1_5_analysis_1_25"
RECIPE = WEIGHT_RECIPES[RECIPE_NAME]
SEEDS = (42, 123, 2026)


def build(columns: list[str], seed: int):
    model = pipeline(columns, {
        key: XGB_PARAMETERS[key]
        for key in ("n_estimators", "max_depth", "learning_rate", "min_child_weight", "subsample", "colsample_bytree")
    })
    model.set_params(model__reg_alpha=XGB_PARAMETERS["reg_alpha"], model__reg_lambda=XGB_PARAMETERS["reg_lambda"], model__random_state=seed)
    return model


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
        weights = fit["attack_cat"].map(RECIPE).fillna(1.0).astype(float)
        candidate = build(columns, seed)
        started = time.perf_counter()
        candidate.fit(fit[columns], fit["label"].astype(int), model__sample_weight=weights)
        training_seconds = time.perf_counter() - started
        calibration_probabilities, calibration_elapsed = probabilities(candidate, calibration[columns])
        selected, feasible_count = select_threshold(calibration["label"].astype(int), calibration_probabilities, calibration_elapsed)
        if selected is None:
            raise RuntimeError(f"Seed {seed} had no feasible calibration threshold")
        validation_probabilities, validation_elapsed = probabilities(candidate, validation[columns])
        result = threshold_metrics(validation["label"].astype(int), validation_probabilities, selected["threshold"], validation_elapsed)
        passes = bool(result["false_positive_rate"] <= FPR_MAX and result["attack_recall"] >= RECALL_MIN and result["macro_f1"] > REFERENCE_MACRO_F1)
        runs.append({"seed": seed, "training_seconds": training_seconds, "feasible_calibration_thresholds": feasible_count, "selected_threshold": selected["threshold"], "validation": result, "passes_validation_gates": passes})
        print(f"seed={seed}: threshold={selected['threshold']:.3f}, accuracy={result['accuracy']:.6f}, macro_f1={result['macro_f1']:.6f}, recall={result['attack_recall']:.6f}, fpr={result['false_positive_rate']:.6f}, pass={passes}", flush=True)
    thresholds = sorted(float(run["selected_threshold"]) for run in runs)
    stable = all(run["passes_validation_gates"] for run in runs)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "attack_cat used only for fit-sample weights across three 70/15/15 official-training-only splits; official test not loaded",
        "training_sha256": sha256(source),
        "seeds": list(SEEDS),
        "recipe_name": RECIPE_NAME,
        "sample_weight_recipe": RECIPE,
        "model_parameters": XGB_PARAMETERS,
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
