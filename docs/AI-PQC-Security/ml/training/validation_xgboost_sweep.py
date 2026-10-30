"""Run a bounded, validation-only XGBoost search on UNSW-NB15.

The official test CSV is deliberately never loaded by this program. Candidate
selection therefore cannot accidentally tune against the final benchmark.
"""

from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, metrics, preprocessor

RUN_ID = "xgboost-validation-sweep-v1"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "candidates"

# Historical Random Forest validation evidence. These values are fixed before
# fitting candidates and are not read from the official test result.
BASELINE = {
    "macro_f1": 0.94840158583486,
    "attack_recall": 0.959570991662826,
    "false_positive_rate": 0.0554464285714286,
}
GATES = {
    "macro_f1_minimum": BASELINE["macro_f1"],
    "attack_recall_minimum": BASELINE["attack_recall"] - 0.005,
    "false_positive_rate_maximum": BASELINE["false_positive_rate"] + 0.005,
}

CANDIDATES = {
    "xgb_depth4_conservative": {
        "n_estimators": 350, "max_depth": 4, "learning_rate": 0.08,
        "min_child_weight": 3, "subsample": 0.85, "colsample_bytree": 0.85,
    },
    "xgb_depth6_balanced": {
        "n_estimators": 300, "max_depth": 6, "learning_rate": 0.07,
        "min_child_weight": 3, "subsample": 0.85, "colsample_bytree": 0.85,
    },
    "xgb_depth8_regularized": {
        "n_estimators": 260, "max_depth": 8, "learning_rate": 0.06,
        "min_child_weight": 5, "subsample": 0.80, "colsample_bytree": 0.80,
    },
    "xgb_depth6_low_fpr": {
        "n_estimators": 320, "max_depth": 6, "learning_rate": 0.06,
        "min_child_weight": 6, "subsample": 0.90, "colsample_bytree": 0.90,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pipeline(columns: list[str], parameters: dict) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", xgb.XGBClassifier(
            **parameters,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            reg_alpha=0.05,
            reg_lambda=1.5,
            n_jobs=2,
            random_state=SEED,
        )),
    ])


def passes_gates(result: dict) -> bool:
    return bool(
        result["macro_f1"] > GATES["macro_f1_minimum"]
        and result["attack_recall"] >= GATES["attack_recall_minimum"]
        and result["false_positive_rate"] <= GATES["false_positive_rate_maximum"]
    )


def main() -> None:
    source = FILES["training"][0]
    data = pd.read_csv(source)
    if len(data) != FILES["training"][1]:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")

    feature_names = [column for column in data.columns if column not in EXCLUDED]
    x_fit, x_validation, y_fit, y_validation = train_test_split(
        data[feature_names], data["label"].astype(int),
        test_size=0.20, stratify=data["label"], random_state=SEED,
    )

    print(
        f"{RUN_ID}: fit={len(x_fit)}, validation={len(x_validation)}; "
        "official test data is not loaded.", flush=True,
    )
    results: dict[str, dict] = {}
    best_model = None
    for name, parameters in CANDIDATES.items():
        candidate = pipeline(feature_names, parameters)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        training_seconds = time.perf_counter() - started
        validation = metrics(candidate, x_validation, y_validation)
        eligible = passes_gates(validation)
        results[name] = {
            "parameters": parameters,
            "training_seconds": training_seconds,
            "validation": validation,
            "clears_predeclared_gates": eligible,
        }
        print(
            f"{name}: accuracy={validation['accuracy']:.6f}, "
            f"macro_f1={validation['macro_f1']:.6f}, "
            f"attack_recall={validation['attack_recall']:.6f}, "
            f"fpr={validation['false_positive_rate']:.6f}, "
            f"eligible={eligible}, seconds={training_seconds:.1f}", flush=True,
        )

    eligible_names = [name for name, result in results.items()
                      if result["clears_predeclared_gates"]]
    winner = max(
        eligible_names,
        key=lambda name: results[name]["validation"]["macro_f1"],
        default=None,
    )
    if winner:
        best_model = pipeline(feature_names, CANDIDATES[winner])
        best_model.fit(x_fit, y_fit)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, MODEL_DIR / f"{RUN_ID}-{winner}.joblib")

    summary = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "official training CSV only; fixed stratified 80/20 split; official test not loaded",
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgb.__version__,
        },
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "split": {"fit": len(x_fit), "validation": len(x_validation)},
        "baseline_validation": BASELINE,
        "predeclared_gates": GATES,
        "candidates": results,
        "eligible_candidates": eligible_names,
        "validation_winner": winner,
        "promotion_status": "validation candidate only; no official-test evaluation or promotion",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {output}. Validation winner: {winner}", flush=True)


if __name__ == "__main__":
    main()
