"""Training-only RF/XGBoost probability-ensemble calibration experiment."""

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
    build_reference,
    build_xgboost,
    probabilities,
    threshold_metrics,
)
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, sha256

RUN_ID = "rf-xgboost-ensemble-validation-v1"


def main() -> None:
    source = FILES["training"][0]
    data = pd.read_csv(source)
    if len(data) != FILES["training"][1]:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")

    columns = [column for column in data.columns if column not in EXCLUDED]
    features = data[columns]
    labels = data["label"].astype(int)
    x_development, x_validation, y_development, y_validation = train_test_split(
        features, labels, test_size=0.15, stratify=labels, random_state=SEED
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
        f"validation={len(x_validation)}; official test is not loaded.",
        flush=True,
    )

    models = {
        "balanced_random_forest": build_reference(columns),
        "xgboost_depth8": build_xgboost(columns),
    }
    fit_seconds: dict[str, float] = {}
    calibration_probabilities: dict[str, np.ndarray] = {}
    validation_probabilities: dict[str, np.ndarray] = {}
    for name, model in models.items():
        started = time.perf_counter()
        model.fit(x_fit, y_fit)
        fit_seconds[name] = time.perf_counter() - started
        calibration_probabilities[name], _ = probabilities(model, x_calibration)
        validation_probabilities[name], _ = probabilities(model, x_validation)
        print(f"{name} trained in {fit_seconds[name]:.1f}s.", flush=True)

    candidates: list[dict] = []
    for xgb_weight in np.round(np.arange(0.0, 1.01, 0.10), 2):
        blended = (
            (1.0 - xgb_weight) * calibration_probabilities["balanced_random_forest"]
            + xgb_weight * calibration_probabilities["xgboost_depth8"]
        )
        for threshold in np.round(np.arange(0.40, 0.751, 0.005), 3):
            result = threshold_metrics(y_calibration, blended, float(threshold))
            feasible = bool(
                result["false_positive_rate"] <= FIXED_FPR_LIMIT
                and result["attack_recall"] >= MINIMUM_ATTACK_RECALL
            )
            candidates.append(
                {
                    "xgboost_weight": float(xgb_weight),
                    "random_forest_weight": float(1.0 - xgb_weight),
                    "feasible": feasible,
                    **result,
                }
            )

    feasible = [candidate for candidate in candidates if candidate["feasible"]]
    selected = max(
        feasible,
        key=lambda row: (row["macro_f1"], row["accuracy"], -row["false_positive_rate"]),
        default=None,
    )
    reference_validation = threshold_metrics(
        y_validation, validation_probabilities["balanced_random_forest"], 0.5
    )
    selected_validation = None
    clears_gates = False
    if selected is not None:
        weight = selected["xgboost_weight"]
        blended_validation = (
            (1.0 - weight) * validation_probabilities["balanced_random_forest"]
            + weight * validation_probabilities["xgboost_depth8"]
        )
        selected_validation = threshold_metrics(
            y_validation, blended_validation, selected["threshold"]
        )
        clears_gates = bool(
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
        "fit_seconds": fit_seconds,
        "search": {
            "weights_evaluated": 11,
            "thresholds_per_weight": 71,
            "total_candidates": len(candidates),
            "feasible_candidates": len(feasible),
        },
        "selected_calibration": selected,
        "reference_random_forest_validation": reference_validation,
        "selected_ensemble_validation": selected_validation,
        "clears_validation_gates": clears_gates,
        "promotion_status": "confirmation candidate only" if clears_gates else "rejected",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"selected={None if selected is None else (selected['xgboost_weight'], selected['threshold'])}; "
        f"validation_gates={clears_gates}; saved {output}",
        flush=True,
    )
    if selected_validation:
        print(
            f"validation: accuracy={selected_validation['accuracy']:.6f}, "
            f"macro_f1={selected_validation['macro_f1']:.6f}, "
            f"recall={selected_validation['attack_recall']:.6f}, "
            f"fpr={selected_validation['false_positive_rate']:.6f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
