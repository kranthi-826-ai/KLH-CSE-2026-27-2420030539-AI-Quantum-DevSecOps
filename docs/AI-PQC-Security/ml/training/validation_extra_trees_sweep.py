"""Run bounded Extra Trees experiments using the UNSW-NB15 training file only.

The official test CSV is deliberately not opened by this script.  It is for
final, one-time reporting after a validation-selected recipe is frozen.
"""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, metrics, preprocessor, sha256


RUN_ID = "extra-trees-validation-sweep-v1"

# These are validation gates declared before fitting.  They preserve the
# baseline's high recall while requiring a meaningful macro-F1 improvement and
# preventing an apparent improvement caused by excessive false alarms.
BASELINE = {
    "macro_f1": 0.94840158583486,
    "attack_recall": 0.959570991662826,
    "false_positive_rate": 0.0554464285714286,
    "inference_ms_per_sample": 0.00887128518064593,
}
GATES = {
    "macro_f1_strictly_above_baseline": True,
    "minimum_attack_recall": BASELINE["attack_recall"] - 0.005,
    "maximum_false_positive_rate": BASELINE["false_positive_rate"] + 0.005,
    "maximum_inference_ms_per_sample": BASELINE["inference_ms_per_sample"] * 2,
}

# Resource-bounded CPU-feasible candidate.  More variations are only justified
# after this first candidate produces a complete report on the target laptop.
CANDIDATES = {
    "et_balanced_depth20_leaf2": {
        "trees": 100, "depth": 20, "leaf": 2, "max_features": "sqrt", "balanced": True
    },
}


def pipeline(columns: list[str], parameters: dict) -> Pipeline:
    return Pipeline([
        ("preprocess", preprocessor(columns)),
        ("model", ExtraTreesClassifier(
            n_estimators=parameters["trees"],
            max_depth=parameters["depth"],
            min_samples_leaf=parameters["leaf"],
            max_features=parameters["max_features"],
            class_weight="balanced" if parameters["balanced"] else None,
            n_jobs=4,
            random_state=SEED,
        )),
    ])


def eligible(result: dict) -> bool:
    return bool(
        result["macro_f1"] > BASELINE["macro_f1"]
        and result["attack_recall"] >= GATES["minimum_attack_recall"]
        and result["false_positive_rate"] <= GATES["maximum_false_positive_rate"]
        and result["inference_ms_per_sample"] <= GATES["maximum_inference_ms_per_sample"]
    )


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; run validate_unsw_nb15.py first")

    features = [column for column in data.columns if column not in EXCLUDED]
    x_fit, x_validation, y_fit, y_validation = train_test_split(
        data[features], data["label"].astype(int), test_size=0.20,
        stratify=data["label"], random_state=SEED,
    )
    print(f"{RUN_ID}: fit={len(x_fit)}, validation={len(x_validation)}; official test data is not loaded.", flush=True)

    results: dict[str, dict] = {}
    for name, parameters in CANDIDATES.items():
        candidate = pipeline(features, parameters)
        started = time.perf_counter()
        candidate.fit(x_fit, y_fit)
        elapsed = time.perf_counter() - started
        validation = metrics(candidate, x_validation, y_validation)
        passed = eligible(validation)
        results[name] = {
            "parameters": parameters,
            "training_seconds": elapsed,
            "validation": validation,
            "clears_predeclared_gates": passed,
        }
        print(
            f"{name}: accuracy={validation['accuracy']:.6f}, macro_f1={validation['macro_f1']:.6f}, "
            f"attack_recall={validation['attack_recall']:.6f}, fpr={validation['false_positive_rate']:.6f}, "
            f"eligible={passed}, seconds={elapsed:.1f}", flush=True,
        )

    eligible_names = [name for name, result in results.items() if result["clears_predeclared_gates"]]
    winner = max(eligible_names, key=lambda name: results[name]["validation"]["macro_f1"], default=None)
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "UNSW-NB15 binary intrusion classification",
        "protocol": "official training CSV only; fixed stratified 80/20 split; official test not loaded",
        "selection_metric": "validation_macro_f1",
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "seed": SEED,
        "training_sha256": sha256(source),
        "excluded_features": EXCLUDED,
        "split": {"fit": len(x_fit), "validation": len(x_validation)},
        "baseline_validation": BASELINE,
        "predeclared_gates": GATES,
        "candidates": results,
        "eligible_candidates": eligible_names,
        "validation_winner": winner,
        "promotion_status": "validation candidates only; not promoted and not test-evaluated",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}. Validation winner: {winner}", flush=True)


if __name__ == "__main__":
    main()
