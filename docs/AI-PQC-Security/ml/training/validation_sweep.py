"""Compare bounded Random Forest candidates using validation data only."""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_baselines import (
    ARTIFACT_DIR,
    EXCLUDED,
    FILES,
    SEED,
    metrics,
    preprocessor,
    sha256,
)

BASELINE_VALIDATION = {
    "macro_f1": 0.94840158583486,
    "attack_recall": 0.959570991662826,
    "false_positive_rate": 0.0554464285714286,
    "inference_ms_per_sample": 0.00887128518064593,
}
GATES = {
    "macro_f1_strictly_above_baseline": True,
    "minimum_attack_recall": BASELINE_VALIDATION["attack_recall"] - 0.01,
    "maximum_false_positive_rate": BASELINE_VALIDATION["false_positive_rate"] + 0.01,
    "maximum_inference_ms_per_sample": BASELINE_VALIDATION["inference_ms_per_sample"] * 2,
}


def make_candidate(columns: list[str], *, trees: int, depth: int,
                   leaf: int, balanced: bool) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", RandomForestClassifier(
            n_estimators=trees,
            max_depth=depth,
            min_samples_leaf=leaf,
            class_weight="balanced_subsample" if balanced else None,
            n_jobs=4,
            random_state=SEED,
        )),
    ])


def main() -> None:
    # Read only the official training partition during model selection. This
    # intentionally avoids even loading the held-out official test file.
    training = pd.read_csv(FILES["training"][0])
    if len(training) != 175_341:
        raise ValueError("Unexpected training row count; validate the dataset first")
    features = [column for column in training.columns if column not in EXCLUDED]
    x_train_all = training[features]
    y_train_all = training["label"].astype(int)
    x_train, x_validation, y_train, y_validation = train_test_split(
        x_train_all, y_train_all, test_size=0.20,
        stratify=y_train_all, random_state=SEED,
    )
    candidates = {
        "rf_reference": {"trees": 250, "depth": 24, "leaf": 2, "balanced": True},
        "rf_shallower": {"trees": 200, "depth": 16, "leaf": 4, "balanced": True},
        "rf_deeper_leaf4": {"trees": 250, "depth": 28, "leaf": 4, "balanced": True},
        "rf_unweighted": {"trees": 200, "depth": 24, "leaf": 2, "balanced": False},
    }
    results = {}
    print(f"Training {len(candidates)} candidates on {len(x_train)} rows; validation={len(x_validation)}; test rows are not loaded.", flush=True)
    for name, parameters in candidates.items():
        model = make_candidate(list(x_train.columns), **parameters)
        started = time.perf_counter()
        model.fit(x_train, y_train)
        training_seconds = time.perf_counter() - started
        validation = metrics(model, x_validation, y_validation)
        results[name] = {
            "parameters": parameters,
            "training_seconds": training_seconds,
            "validation": validation,
            "clears_predeclared_gates": bool(
                validation["macro_f1"] > BASELINE_VALIDATION["macro_f1"]
                and validation["attack_recall"] >= GATES["minimum_attack_recall"]
                and validation["false_positive_rate"] <= GATES["maximum_false_positive_rate"]
                and validation["inference_ms_per_sample"] <= GATES["maximum_inference_ms_per_sample"]
            ),
        }
        print(
            f"{name}: macro_f1={validation['macro_f1']:.6f}, "
            f"attack_recall={validation['attack_recall']:.6f}, "
            f"fpr={validation['false_positive_rate']:.6f}, "
            f"accuracy={validation['accuracy']:.6f}, seconds={training_seconds:.1f}",
            flush=True,
        )

    eligible = [name for name, result in results.items() if result["clears_predeclared_gates"]]
    winner = max(eligible, key=lambda key: results[key]["validation"]["macro_f1"]) if eligible else None
    summary = {
        "run_id": "validation-sweep-2026-10-01",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "official training file only; fixed stratified 80/20 split; no official test data loaded or scored",
        "seed": SEED,
        "selection_metric": "validation_macro_f1",
        "baseline_validation": BASELINE_VALIDATION,
        "predeclared_gates": GATES,
        "environment": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
        "training_sha256": sha256(FILES["training"][0]),
        "split": {"train": len(x_train), "validation": len(x_validation)},
        "candidates": results,
        "eligible_candidates": eligible,
        "validation_winner": winner,
        "promotion_status": "validation candidate only; not promoted and not test-evaluated",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / "validation-sweep-20261001.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Eligible candidates: {eligible}; winner by validation macro-F1: {winner}; evidence: {output}", flush=True)


if __name__ == "__main__":
    main()
