"""Freeze and evaluate saved CICIoT pilot baselines once; never fit or retune."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from train_ciciot2023_pilot import binary_metrics, json_clean

ML = Path(__file__).resolve().parents[1]
NAMES = ("random_forest", "xgboost", "eight_group_xgboost")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(data, models, validation, output):
    report = json.loads(validation.read_text())
    manifest_path = data / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if report["run_status"] != "complete" or report["manifest_sha256"] != sha(manifest_path):
        raise ValueError("Validation evidence or data manifest changed")
    bundles = {}
    for name in NAMES:
        path = models / f"{name}.joblib"
        bundle = joblib.load(path)
        if bundle["columns"] != manifest["feature_columns"]:
            raise ValueError("Model feature schema mismatch")
        if name != "eight_group_xgboost":
            if bundle["manifest_sha256"] != sha(manifest_path) or bundle["threshold"] != report["models"][name]["validation"]["threshold"]:
                raise ValueError("Frozen threshold or manifest mismatch")
        bundles[name] = {"path": str(path.resolve()), "sha256": sha(path),
                         "threshold": bundle.get("threshold"),
                         "validation_eligible": report["models"][name]["passes_predeclared_validation_gates"] if name != "eight_group_xgboost" else False}
    output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "ciciot2023-frozen-pilot-final-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "data": str(data.resolve()), "manifest_sha256": sha(manifest_path),
            "test_sha256": manifest["splits"]["test"]["sha256"], "models": bundles,
            "feature_columns": manifest["feature_columns"], "validation_sha256": sha(validation),
            "evaluator_sha256": sha(Path(__file__)), "metrics_helper_sha256": sha(Path(__file__).with_name("train_ciciot2023_pilot.py")),
            "scope": "one reserved-test evaluation of saved bounded-pilot baselines, NOT all47million rows",
            "selection": "All predeclared baselines reported; no winner selection or threshold tuning on final test",
            "promotion_allowed": False, "test_loaded": False}
    with (output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    print("Frozen three saved baselines; test data has not been loaded", flush=True)


def evaluate(output):
    if (output / "test-started.json").exists() or (output / "result.json").exists():
        raise FileExistsError("Reserved test already attempted; refuse rerun/overwrite")
    plan = json.loads((output / "plan.json").read_text())
    if plan["evaluator_sha256"] != sha(Path(__file__)) or plan["metrics_helper_sha256"] != sha(Path(__file__).with_name("train_ciciot2023_pilot.py")):
        raise ValueError("Frozen evaluation code changed")
    data = Path(plan["data"])
    if sha(data / "manifest.json") != plan["manifest_sha256"]:
        raise ValueError("Manifest changed")
    for bundle in plan["models"].values():
        if sha(Path(bundle["path"])) != bundle["sha256"]:
            raise ValueError("Frozen model changed")
    with (output / "test-started.json").open("x") as handle:
        json.dump({"started_utc": datetime.now(timezone.utc).isoformat(), "plan_sha256": sha(output / "plan.json")}, handle)
    started = time.perf_counter()
    test_path = data / "test.pkl"
    if sha(test_path) != plan["test_sha256"]:
        raise ValueError("Reserved test checksum mismatch; preserve failed attempt")
    frame = pd.read_pickle(test_path)
    x = frame[plan["feature_columns"]]
    if not np.isfinite(x.to_numpy()).all() or not set(frame["_binary_label"].unique()).issubset({0, 1}):
        raise ValueError("Invalid frozen test data")
    result = {"schema": plan["schema"], "plan_sha256": sha(output / "plan.json"), "reserved_test_loaded": True,
              "samples": len(frame), "benign": int(np.sum(frame["_binary_label"] == 0)),
              "models": {}, "promoted": False, "enforcement_enabled": False,
              "scope": plan["scope"], "no_test_based_selection": True}
    for name in NAMES:
        bundle = joblib.load(plan["models"][name]["path"])
        if name == "eight_group_xgboost":
            labels = bundle["labels"]
            actual = frame["_group"].to_numpy()
            predicted = np.asarray(labels)[bundle["model"].predict(x).astype(int)]
            result["models"][name] = {"accuracy": float(accuracy_score(actual, predicted)),
                "macro_f1": float(f1_score(actual, predicted, average="macro", zero_division=0)),
                "labels": labels, "confusion_matrix": confusion_matrix(actual, predicted, labels=labels).tolist(),
                "classification_report": classification_report(actual, predicted, labels=labels, output_dict=True, zero_division=0)}
        else:
            probability = bundle["model"].predict_proba(x)[:, list(bundle["model"].classes_).index(1)]
            metric = binary_metrics(frame["_binary_label"].to_numpy(), probability,
                                    plan["models"][name]["threshold"], frame["_label"].to_numpy())
            metric["passes_test_security_gates"] = bool(metric["attack_recall"] >= .95 and metric["false_positive_rate"] <= .05)
            metric["validation_eligible"] = plan["models"][name]["validation_eligible"]
            result["models"][name] = metric
        print(f"{name}: { {key: result['models'][name][key] for key in ('accuracy','macro_f1')} }", flush=True)
    result["seconds"] = time.perf_counter() - started
    with (output / "result.json").open("x") as handle:
        json.dump(json_clean(result), handle, indent=2, allow_nan=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "evaluate"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(ML / "data/processed/ciciot2023-pilot-v1", ML / "models/candidates/ciciot2023-pilot-v1",
               ML / "artifacts/ciciot2023-pilot-validation-v1.json", args.output)
    else:
        evaluate(args.output)
