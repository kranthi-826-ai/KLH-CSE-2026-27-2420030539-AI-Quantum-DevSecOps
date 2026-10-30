"""Fixed-recipe reference expansion across both workers and both trace segments."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import tarfile
import time
import zipfile

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

from train_socialnetwork_reference import check_metadata, matrix, sha, SEED
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--training-intake", type=Path, required=True)
    parser.add_argument("--validation-intake", type=Path, required=True)
    args = parser.parse_args()
    old = json.loads((args.reference / "report.json").read_text())
    feature_path = Path(__file__).resolve().parents[1] / "data" / "socialnetwork_syscalls.py"
    if old["features_sha256"] != sha(feature_path):
        raise ValueError("Reference representation changed")
    training = json.loads(args.training_intake.read_text())
    validation = json.loads(args.validation_intake.read_text())
    exclusions, intervals = check_metadata(training, validation)
    trace_names = sorted(h["name"] for h in training["training_metadata"][0]["headers"] if h["name"].endswith(".txt.zip"))
    if len(trace_names) != 4:
        raise ValueError("Expected four training trace segments")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"traces": trace_names, "max_events_per_trace": 500000, "max_bytes_per_trace": 128 * 1024**2,
            "recipe": {"n_estimators": 128, "max_samples": 256, "contamination": "auto", "n_jobs": 2, "random_state": SEED},
            "threshold_rule": "next float above calibration 95th percentile, higher quantile",
            "feature_sha256": sha(feature_path), "script_sha256": sha(Path(__file__)),
            "reference_report_sha256": sha(args.reference / "report.json"),
            "promotion_gate": "Do not promote on this exposed development comparison"}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    started = time.perf_counter()
    all_rows, audits = [], []
    with zipfile.ZipFile(args.source / "SocialNetwork-training-data.zip") as outer:
        member = next(m for m in outer.infolist() if m.filename.endswith(".tar.gz"))
        with outer.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in trace_names:
                        continue
                    rows, audit = aggregate(first_zip_lines(nested.extractfile(trace)))
                    kept = [row for row in rows if not any(lo <= row["window"] <= hi for lo, hi in exclusions)]
                    audit.update({"trace": trace.name, "rows": len(kept), "excluded_windows": len(rows) - len(kept)})
                    for row in kept:
                        row["trace"] = trace.name
                    all_rows.extend(kept)
                    audits.append(audit)
                    print(f"{trace.name}: {len(kept)} windows", flush=True)
    if len(audits) != 4:
        raise ValueError("Missing training traces")
    if any(any(lo <= row["window"] <= hi for lo, hi in intervals.values()) for row in all_rows):
        raise ValueError("Training and normal evaluation timestamps overlap")
    model = IsolationForest(**plan["recipe"])
    model.fit(matrix(all_rows))
    calibration_path = args.reference / "calibration_normal.json"
    check_path = args.reference / "check_normal.json"
    for key, path in (("calibration_normal", calibration_path), ("check_normal", check_path)):
        if old["audits"][key]["features_sha256"] != sha(path):
            raise ValueError("Original normal features changed")
    calibration = json.loads(calibration_path.read_text())
    scores = -model.score_samples(matrix(calibration))
    threshold = float(np.nextafter(np.quantile(scores, .95, method="higher"), np.inf))
    joblib.dump(model, args.output / "reference.joblib")
    with (args.output / "reference.json").open("x") as handle:
        json.dump(all_rows, handle)
    report = {"schema": "socialnetwork-expanded-reference-v1", "experimental": True, "enforcement_enabled": False,
              "features": list(COLUMNS), "features_sha256": sha(feature_path), "model_sha256": sha(args.output / "reference.joblib"),
              "script_sha256": sha(Path(__file__)), "plan_sha256": sha(args.output / "plan.json"),
              "reference_rows_sha256": sha(args.output / "reference.json"), "threshold": threshold,
              "scope": "four 500k-event prefixes, both workers/segments; not full eight-day recording",
              "audits": audits, "training_windows": len(all_rows), "sklearn_version": sklearn.__version__,
              "normal_results": {}, "attack_accuracy": None, "reference_normality": "contamination not ruled out"}
    for name, path in (("calibration_normal", calibration_path), ("check_normal", check_path)):
        rows = json.loads(path.read_text())
        scores = -model.score_samples(matrix(rows))
        alarms = int(np.sum(scores >= threshold))
        report["normal_results"][name] = {"windows": len(rows), "alarms": alarms, "observed_alarm_fraction": alarms / len(rows)}
    report["seconds"] = time.perf_counter() - started
    with (args.output / "report.json").open("x") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report["normal_results"]), flush=True)


if __name__ == "__main__":
    main()
