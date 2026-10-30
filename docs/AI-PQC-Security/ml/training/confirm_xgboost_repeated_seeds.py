"""Confirm calibrated XGBoost behavior across independent training splits."""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.model_selection import train_test_split

from calibrate_xgboost_threshold import (
    FIXED_FPR_LIMIT,
    MINIMUM_ATTACK_RECALL,
    XGB_PARAMETERS,
    build_reference,
    build_xgboost,
    probabilities,
    threshold_metrics,
)
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, sha256

RUN_ID = "xgboost-repeated-seed-confirmation-v1"
SEEDS = [42, 123, 2026]


def describe(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "sample_std": float(array.std(ddof=1)) if len(array) > 1 else 0.0,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def display(value: float | None) -> str:
    return "none" if value is None else f"{value:.6f}"


def main() -> None:
    source = FILES["training"][0]
    data = pd.read_csv(source)
    if len(data) != FILES["training"][1]:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    columns = [column for column in data.columns if column not in EXCLUDED]
    features = data[columns]
    labels = data["label"].astype(int)
    runs = []

    print(
        f"{RUN_ID}: seeds={SEEDS}; official test data is not loaded.", flush=True
    )
    for seed in SEEDS:
        x_development, x_validation, y_development, y_validation = train_test_split(
            features, labels, test_size=0.15, stratify=labels, random_state=seed,
        )
        x_fit, x_calibration, y_fit, y_calibration = train_test_split(
            x_development,
            y_development,
            test_size=0.15 / 0.85,
            stratify=y_development,
            random_state=seed,
        )

        candidate = build_xgboost(columns)
        candidate.set_params(model__random_state=seed)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        candidate_seconds = time.perf_counter() - started
        calibration_probabilities, calibration_elapsed = probabilities(
            candidate, x_calibration
        )

        candidates = []
        for threshold in np.round(np.arange(0.30, 0.901, 0.005), 3):
            result = threshold_metrics(
                y_calibration,
                calibration_probabilities,
                float(threshold),
                calibration_elapsed,
            )
            result["feasible"] = bool(
                result["false_positive_rate"] <= FIXED_FPR_LIMIT
                and result["attack_recall"] >= MINIMUM_ATTACK_RECALL
            )
            candidates.append(result)
        feasible = [result for result in candidates if result["feasible"]]
        selected = max(feasible, key=lambda result: result["macro_f1"], default=None)

        candidate_validation = None
        if selected:
            values, elapsed = probabilities(candidate, x_validation)
            candidate_validation = threshold_metrics(
                y_validation, values, selected["threshold"], elapsed
            )

        reference = build_reference(columns)
        reference.set_params(model__random_state=seed)
        reference_started = time.perf_counter()
        reference.fit(x_fit, y_fit)
        reference_seconds = time.perf_counter() - reference_started
        reference_values, reference_elapsed = probabilities(reference, x_validation)
        reference_validation = threshold_metrics(
            y_validation, reference_values, 0.5, reference_elapsed
        )

        passes = bool(
            candidate_validation is not None
            and candidate_validation["false_positive_rate"] <= FIXED_FPR_LIMIT
            and candidate_validation["attack_recall"] >= MINIMUM_ATTACK_RECALL
            and candidate_validation["macro_f1"] > reference_validation["macro_f1"]
        )
        runs.append({
            "seed": seed,
            "split": {
                "fit": len(x_fit),
                "calibration": len(x_calibration),
                "validation": len(x_validation),
            },
            "selected_calibration": selected,
            "candidate_training_seconds": candidate_seconds,
            "candidate_validation": candidate_validation,
            "reference_training_seconds": reference_seconds,
            "reference_validation": reference_validation,
            "passes_validation_gates": passes,
        })
        print(
            f"seed={seed}: threshold={None if selected is None else selected['threshold']}, "
            f"candidate_f1={display(None if candidate_validation is None else candidate_validation['macro_f1'])}, "
            f"candidate_recall={display(None if candidate_validation is None else candidate_validation['attack_recall'])}, "
            f"candidate_fpr={display(None if candidate_validation is None else candidate_validation['false_positive_rate'])}, "
            f"reference_f1={reference_validation['macro_f1']:.6f}, passes={passes}",
            flush=True,
        )

    measured = [run for run in runs if run["candidate_validation"] is not None]
    fields = ["accuracy", "macro_f1", "attack_recall", "false_positive_rate",
              "roc_auc", "inference_ms_per_sample"]
    candidate_summary = {
        field: describe([run["candidate_validation"][field] for run in measured])
        for field in fields
    }
    reference_summary = {
        field: describe([run["reference_validation"][field] for run in runs])
        for field in fields
    }
    thresholds = [run["selected_calibration"]["threshold"] for run in measured]
    stable = bool(
        len(measured) == len(SEEDS)
        and all(run["passes_validation_gates"] for run in runs)
        and candidate_summary["false_positive_rate"]["mean"] <= FIXED_FPR_LIMIT
        and candidate_summary["attack_recall"]["mean"] >= MINIMUM_ATTACK_RECALL
        and candidate_summary["macro_f1"]["mean"] > reference_summary["macro_f1"]["mean"]
    )
    summary = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "three independent 70/15/15 fit-calibration-validation splits; official test not loaded",
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgb.__version__,
        },
        "seeds": SEEDS,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "candidate_parameters": XGB_PARAMETERS,
        "constraints": {
            "false_positive_rate_maximum": FIXED_FPR_LIMIT,
            "attack_recall_minimum": MINIMUM_ATTACK_RECALL,
            "must_beat_same_split_reference_macro_f1": True,
        },
        "runs": runs,
        "selected_thresholds": thresholds,
        "recommended_frozen_threshold": float(np.median(thresholds)) if thresholds else None,
        "candidate_summary": candidate_summary,
        "reference_summary": reference_summary,
        "stable_across_seeds": stable,
        "next_status": "eligible for frozen final evaluation" if stable else "not eligible",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"Stable across seeds: {stable}; recommended threshold: "
        f"{summary['recommended_frozen_threshold']}; saved {output}", flush=True,
    )


if __name__ == "__main__":
    main()
