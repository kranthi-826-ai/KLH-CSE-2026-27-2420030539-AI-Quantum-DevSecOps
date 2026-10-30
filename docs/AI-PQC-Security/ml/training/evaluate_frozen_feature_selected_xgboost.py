"""Single official-test evaluation of the frozen 60-feature XGBoost recipe."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import joblib
import pandas as pd

from calibrate_xgboost_threshold import probabilities, threshold_metrics
from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, MODEL_DIR, SEED, sha256
from validation_feature_selection_sweep import XGB_PARAMETERS, build

RUN_ID = "xgboost-select60-frozen-final-evaluation-v1"
FEATURE_COUNT = 60
FROZEN_THRESHOLD = 0.58
CONFIRMATION = ARTIFACT_DIR / "xgboost-select60-repeated-seed-confirmation-v1.json"
OUTPUT = ARTIFACT_DIR / f"{RUN_ID}.json"
MODEL_OUTPUT = MODEL_DIR / "evaluated" / f"{RUN_ID}.joblib"
PROMOTED_BASELINE = {
    "accuracy": 0.8978890256522309,
    "macro_f1": 0.8945686190387647,
    "attack_recall": 0.9765287214329833,
    "false_positive_rate": 0.19845945945945945,
    "roc_auc": 0.9842660455832166,
}


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
        raise ValueError("Unexpected official dataset row count")
    if list(train.columns) != list(test.columns):
        raise ValueError("Official train/test schemas differ")
    columns = [column for column in train.columns if column not in EXCLUDED]
    model = build(columns, FEATURE_COUNT)
    model.set_params(model__random_state=SEED)
    print(f"Training frozen {FEATURE_COUNT}-feature XGBoost recipe on {len(train)} rows; threshold={FROZEN_THRESHOLD}.", flush=True)
    started = time.perf_counter()
    model.fit(train[columns], train["label"].astype(int))
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
    transformed = model.named_steps["preprocess"].get_feature_names_out()
    selected_features = [str(value) for value in transformed[model.named_steps["select"].get_support()]]
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "status": "final official-split evaluation",
        "prior_test_exposure_disclosure": "Historical repository baselines used the same official test file. This candidate was frozen from training-only selection and repeated validation, but the test distribution is not entirely unknown to the broader project history.",
        "seed": SEED,
        "dataset_sha256": {name: sha256(path) for name, (path, _) in FILES.items()},
        "split": {"train": len(train), "test": len(test)},
        "excluded_features": EXCLUDED,
        "feature_selection": {"method": "SelectKBest(f_classif)", "count": FEATURE_COUNT, "selected_features": selected_features},
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
