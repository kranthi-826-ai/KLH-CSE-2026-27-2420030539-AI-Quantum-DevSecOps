"""Test training-only attack-family sample weights with calibrated XGBoost.

Attack family is used only to calculate fit-sample costs. It is excluded from
the feature matrix and is not required or available during inference.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from calibrate_xgboost_threshold import threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, sha256
from validation_feature_selection_sweep import (
    FPR_MAX,
    RECALL_MIN,
    REFERENCE_MACRO_F1,
    XGB_PARAMETERS,
    probabilities,
    select_threshold,
)
from validation_xgboost_sweep import pipeline

RUN_ID = "xgboost-attack-family-weighting-validation-v1"
WEIGHT_RECIPES = {
    "fuzzer_1_5_analysis_1_25": {"Fuzzers": 1.5, "Analysis": 1.25},
    "fuzzer_2_analysis_1_5": {"Fuzzers": 2.0, "Analysis": 1.5},
    "fuzzer_3_analysis_2": {"Fuzzers": 3.0, "Analysis": 2.0},
}


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    development, validation = train_test_split(
        data, test_size=0.15, stratify=data["label"], random_state=SEED,
    )
    fit, calibration = train_test_split(
        development, test_size=0.15 / 0.85,
        stratify=development["label"], random_state=SEED,
    )
    print(f"{RUN_ID}: fit={len(fit)}, calibration={len(calibration)}, validation={len(validation)}; official test is not loaded.", flush=True)
    results = {}
    for name, recipe in WEIGHT_RECIPES.items():
        weights = fit["attack_cat"].map(recipe).fillna(1.0).astype(float)
        candidate = pipeline(columns, {
            key: XGB_PARAMETERS[key]
            for key in ("n_estimators", "max_depth", "learning_rate", "min_child_weight", "subsample", "colsample_bytree")
        })
        candidate.set_params(
            model__reg_alpha=XGB_PARAMETERS["reg_alpha"],
            model__reg_lambda=XGB_PARAMETERS["reg_lambda"],
            model__random_state=SEED,
        )
        started = time.perf_counter()
        candidate.fit(fit[columns], fit["label"].astype(int), model__sample_weight=weights)
        training_seconds = time.perf_counter() - started
        calibration_probabilities, calibration_elapsed = probabilities(candidate, calibration[columns])
        selected, feasible_count = select_threshold(calibration["label"].astype(int), calibration_probabilities, calibration_elapsed)
        validation_result = None
        passes = False
        if selected is not None:
            validation_probabilities, validation_elapsed = probabilities(candidate, validation[columns])
            validation_result = threshold_metrics(validation["label"].astype(int), validation_probabilities, selected["threshold"], validation_elapsed)
            passes = bool(
                validation_result["false_positive_rate"] <= FPR_MAX
                and validation_result["attack_recall"] >= RECALL_MIN
                and validation_result["macro_f1"] > REFERENCE_MACRO_F1
            )
        results[name] = {
            "sample_weight_recipe": recipe,
            "training_seconds": training_seconds,
            "feasible_calibration_thresholds": feasible_count,
            "selected_calibration": selected,
            "validation": validation_result,
            "clears_validation_gates": passes,
        }
        if validation_result:
            print(f"{name}: threshold={selected['threshold']:.3f}, accuracy={validation_result['accuracy']:.6f}, macro_f1={validation_result['macro_f1']:.6f}, recall={validation_result['attack_recall']:.6f}, fpr={validation_result['false_positive_rate']:.6f}, eligible={passes}", flush=True)
        else:
            print(f"{name}: no feasible calibration threshold", flush=True)
    eligible = [name for name, item in results.items() if item["clears_validation_gates"]]
    winner = max(eligible, key=lambda name: results[name]["validation"]["macro_f1"], default=None)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "attack_cat excluded from inference features and used only for fit-sample weighting; 70/15/15 official-training-only split; official test not loaded",
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "model_parameters": XGB_PARAMETERS,
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
