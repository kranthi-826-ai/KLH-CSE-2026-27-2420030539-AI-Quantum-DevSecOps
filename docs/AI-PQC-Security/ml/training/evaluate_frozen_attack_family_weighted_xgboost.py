"""Single official-test evaluation of frozen family-weighted XGBoost."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import joblib
import pandas as pd

from calibrate_xgboost_threshold import probabilities, threshold_metrics
from confirm_attack_family_weighted_xgboost import RECIPE, RECIPE_NAME, build
from evaluate_frozen_feature_selected_xgboost import PROMOTED_BASELINE
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, MODEL_DIR, SEED, sha256
from validation_feature_selection_sweep import XGB_PARAMETERS

RUN_ID = "xgboost-family-weighted-frozen-final-evaluation-v1"
FROZEN_THRESHOLD = 0.665
CONFIRMATION = ARTIFACT_DIR / "xgboost-family-weighted-repeated-seed-confirmation-v1.json"
OUTPUT = ARTIFACT_DIR / f"{RUN_ID}.json"
MODEL_OUTPUT = MODEL_DIR / "evaluated" / f"{RUN_ID}.joblib"


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Final evidence already exists at {OUTPUT}; refusing to rerun")
    confirmation = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    if not confirmation.get("stable_across_seeds") or confirmation.get("recommended_frozen_threshold") != FROZEN_THRESHOLD:
        raise RuntimeError("Repeated-seed evidence does not authorize this frozen evaluation")
    train = pd.read_csv(FILES["training"][0])
    test = pd.read_csv(FILES["testing"][0])
    if len(train) != FILES["training"][1] or len(test) != FILES["testing"][1] or list(train.columns) != list(test.columns):
        raise ValueError("Official dataset validation failed")
    columns = [column for column in train.columns if column not in EXCLUDED]
    weights = train["attack_cat"].map(RECIPE).fillna(1.0).astype(float)
    model = build(columns, SEED)
    print(f"Training frozen family-weighted XGBoost on {len(train)} rows; threshold={FROZEN_THRESHOLD}.", flush=True)
    started = time.perf_counter()
    model.fit(train[columns], train["label"].astype(int), model__sample_weight=weights)
    training_seconds = time.perf_counter() - started
    values, inference_seconds = probabilities(model, test[columns])
    evaluation = threshold_metrics(test["label"].astype(int), values, FROZEN_THRESHOLD, inference_seconds)
    beats_baseline = bool(
        evaluation["accuracy"] > PROMOTED_BASELINE["accuracy"]
        and evaluation["macro_f1"] > PROMOTED_BASELINE["macro_f1"]
        and evaluation["attack_recall"] >= PROMOTED_BASELINE["attack_recall"]
        and evaluation["false_positive_rate"] < PROMOTED_BASELINE["false_positive_rate"]
        and evaluation["roc_auc"] >= PROMOTED_BASELINE["roc_auc"]
    )
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "status": "final official-split evaluation",
        "prior_test_exposure_disclosure": "Historical repository baselines used the same official test file. This candidate was frozen using training-only repeated validation, but the test distribution is not entirely unknown to the broader project history.",
        "seed": SEED,
        "dataset_sha256": {name: sha256(path) for name, (path, _) in FILES.items()},
        "split": {"train": len(train), "test": len(test)},
        "excluded_features": EXCLUDED,
        "sample_weight_recipe": {"name": RECIPE_NAME, "weights": RECIPE, "inference_dependency": False},
        "parameters": XGB_PARAMETERS,
        "threshold": FROZEN_THRESHOLD,
        "training_seconds": training_seconds,
        "test": evaluation,
        "promoted_baseline": PROMOTED_BASELINE,
        "beats_promoted_baseline_on_all_gates": beats_baseline,
        "selection_evidence": str(CONFIRMATION.relative_to(ARTIFACT_DIR.parent.parent)),
        "promotion_status": "eligible for explicit promotion review" if beats_baseline else "rejected",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    joblib.dump({"pipeline": model, "threshold": FROZEN_THRESHOLD, "run_id": RUN_ID}, MODEL_OUTPUT)
    print(f"Final test: accuracy={evaluation['accuracy']:.6f}, macro_f1={evaluation['macro_f1']:.6f}, recall={evaluation['attack_recall']:.6f}, fpr={evaluation['false_positive_rate']:.6f}, roc_auc={evaluation['roc_auc']:.6f}, beats_all={beats_baseline}; saved {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
