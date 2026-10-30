"""Perform the one-time official-test evaluation of the frozen XGBoost recipe."""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
import xgboost as xgb

from calibrate_xgboost_threshold import XGB_PARAMETERS, build_xgboost, probabilities, threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, MODEL_DIR, SEED, sha256

RUN_ID = "xgboost-frozen-final-evaluation-v1"
FROZEN_THRESHOLD = 0.575
CONFIRMATION_ARTIFACT = ARTIFACT_DIR / "xgboost-repeated-seed-confirmation-v1.json"
OUTPUT = ARTIFACT_DIR / f"{RUN_ID}.json"
MODEL_OUTPUT = MODEL_DIR / "evaluated" / f"{RUN_ID}.joblib"


def main() -> None:
    # Fail closed: do not silently repeat or overwrite the final evaluation.
    if OUTPUT.exists():
        raise FileExistsError(
            f"Final evidence already exists at {OUTPUT}; refusing to rerun."
        )
    if not CONFIRMATION_ARTIFACT.exists():
        raise FileNotFoundError("Repeated-seed confirmation evidence is missing")
    confirmation = json.loads(CONFIRMATION_ARTIFACT.read_text(encoding="utf-8"))
    if not confirmation.get("stable_across_seeds"):
        raise RuntimeError("Candidate did not pass repeated-seed confirmation")
    if confirmation.get("recommended_frozen_threshold") != FROZEN_THRESHOLD:
        raise RuntimeError("Frozen threshold differs from confirmation evidence")

    train = pd.read_csv(FILES["training"][0])
    test = pd.read_csv(FILES["testing"][0])
    if len(train) != FILES["training"][1] or len(test) != FILES["testing"][1]:
        raise ValueError("Unexpected official dataset row count")
    if list(train.columns) != list(test.columns):
        raise ValueError("Official training and test schemas differ")
    columns = [column for column in train.columns if column not in EXCLUDED]

    model = build_xgboost(columns)
    model.set_params(model__random_state=SEED)
    print(
        f"Training frozen recipe on {len(train)} official training rows; "
        f"threshold={FROZEN_THRESHOLD}.", flush=True,
    )
    started = time.perf_counter()
    model.fit(train[columns], train["label"].astype(int))
    training_seconds = time.perf_counter() - started
    test_probabilities, inference_seconds = probabilities(model, test[columns])
    test_result = threshold_metrics(
        test["label"].astype(int),
        test_probabilities,
        FROZEN_THRESHOLD,
        inference_seconds,
    )

    summary = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "status": "final official-split evaluation",
        "prior_test_exposure_disclosure": (
            "The repository contains historical evaluations on the same official "
            "test file. Hyperparameters and threshold for this run were frozen from "
            "training/calibration/validation evidence, but the test distribution is "
            "not entirely unknown to the broader project history."
        ),
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgb.__version__,
        },
        "seed": SEED,
        "dataset_sha256": {
            name: sha256(path) for name, (path, _) in FILES.items()
        },
        "split": {"train": len(train), "test": len(test)},
        "excluded_features": EXCLUDED,
        "parameters": XGB_PARAMETERS,
        "threshold": FROZEN_THRESHOLD,
        "training_seconds": training_seconds,
        "test": test_result,
        "selection_evidence": str(CONFIRMATION_ARTIFACT.relative_to(ARTIFACT_DIR.parent.parent)),
        "promotion_status": "evaluated; promotion requires explicit quality review",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    joblib.dump(
        {"pipeline": model, "threshold": FROZEN_THRESHOLD, "run_id": RUN_ID},
        MODEL_OUTPUT,
    )
    print(
        f"Final test: accuracy={test_result['accuracy']:.6f}, "
        f"macro_f1={test_result['macro_f1']:.6f}, "
        f"attack_recall={test_result['attack_recall']:.6f}, "
        f"fpr={test_result['false_positive_rate']:.6f}; saved {OUTPUT}",
        flush=True,
    )


if __name__ == "__main__":
    main()
