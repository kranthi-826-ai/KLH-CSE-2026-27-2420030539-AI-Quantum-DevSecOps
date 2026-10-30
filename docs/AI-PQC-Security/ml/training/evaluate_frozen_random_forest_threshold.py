"""Perform a single official-test evaluation of the frozen calibrated RF recipe."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from calibrate_random_forest_threshold import build
from calibrate_xgboost_threshold import probabilities, threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, MODEL_DIR, SEED, sha256

RUN_ID = "random-forest-unweighted-frozen-final-evaluation-v1"
FROZEN_THRESHOLD = 0.60
CONFIRMATION = ARTIFACT_DIR / "random-forest-unweighted-repeated-seed-confirmation-v1.json"
OUTPUT = ARTIFACT_DIR / f"{RUN_ID}.json"
MODEL_OUTPUT = MODEL_DIR / "evaluated" / f"{RUN_ID}.joblib"


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Final evidence already exists at {OUTPUT}; refusing to rerun")
    if not CONFIRMATION.exists():
        raise FileNotFoundError("Repeated-seed confirmation evidence is missing")
    confirmation = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    if not confirmation.get("stable_across_seeds"):
        raise RuntimeError("Candidate did not pass repeated-seed confirmation")
    if confirmation.get("recommended_frozen_threshold") != FROZEN_THRESHOLD:
        raise RuntimeError("Frozen threshold differs from confirmation evidence")
    train = pd.read_csv(FILES["training"][0])
    test = pd.read_csv(FILES["testing"][0])
    if len(train) != FILES["training"][1] or len(test) != FILES["testing"][1]:
        raise ValueError("Unexpected official data row count")
    if list(train.columns) != list(test.columns):
        raise ValueError("Official train/test schemas differ")
    columns = [column for column in train.columns if column not in EXCLUDED]
    model = build(columns)
    model.set_params(model__random_state=SEED)
    print(f"Training frozen Random Forest recipe on {len(train)} rows; threshold={FROZEN_THRESHOLD}.", flush=True)
    started = time.perf_counter()
    model.fit(train[columns], train["label"].astype(int))
    training_seconds = time.perf_counter() - started
    values, inference_seconds = probabilities(model, test[columns])
    evaluation = threshold_metrics(test["label"].astype(int), values, FROZEN_THRESHOLD, inference_seconds)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "status": "final official-split evaluation",
        "prior_test_exposure_disclosure": "Historical repository baselines used the same official test file. This candidate's model and threshold were frozen from training/calibration/validation evidence, but the test distribution is not entirely unknown to the broader project history.",
        "seed": SEED,
        "dataset_sha256": {name: sha256(path) for name, (path, _) in FILES.items()},
        "split": {"train": len(train), "test": len(test)},
        "excluded_features": EXCLUDED,
        "parameters": {"n_estimators": 250, "max_depth": 24, "min_samples_leaf": 2, "class_weight": None},
        "threshold": FROZEN_THRESHOLD,
        "training_seconds": training_seconds,
        "test": evaluation,
        "selection_evidence": str(CONFIRMATION.relative_to(ARTIFACT_DIR.parent.parent)),
        "promotion_status": "evaluated; promotion requires explicit quality review",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    joblib.dump({"pipeline": model, "threshold": FROZEN_THRESHOLD, "run_id": RUN_ID}, MODEL_OUTPUT)
    print(f"Final test: accuracy={evaluation['accuracy']:.6f}, macro_f1={evaluation['macro_f1']:.6f}, attack_recall={evaluation['attack_recall']:.6f}, fpr={evaluation['false_positive_rate']:.6f}; saved {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
