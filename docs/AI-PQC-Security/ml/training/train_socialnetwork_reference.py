"""Bounded unsupervised reference pilot; measures normal alarms, NOT attack accuracy."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import time
import zipfile
from datetime import datetime, timezone, timedelta

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines

SEED = 20261020


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prefix(source, archive_name, scenario=None):
    with zipfile.ZipFile(source / archive_name) as outer:
        selected = [m for m in outer.infolist() if m.filename.endswith(".tar.gz")
                    and (scenario is None or m.filename.endswith(f"/{scenario}.tar.gz"))]
        if len(selected) != 1:
            raise ValueError("Ambiguous or missing recording")
        member = selected[0]
        with outer.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as uncompressed:
            with tarfile.open(fileobj=uncompressed, mode="r|") as nested:
                for trace in nested:
                    if trace.isfile() and "/node1/" in trace.name and trace.name.endswith("events_000.txt.zip"):
                        rows, audit = aggregate(first_zip_lines(nested.extractfile(trace)))
                        return rows, {"archive": archive_name, "recording": member.filename,
                                      "trace": trace.name, **audit, "rows": len(rows)}
    raise ValueError("No matching trace")


def matrix(rows):
    result = np.asarray([[row["features"][key] for key in COLUMNS] for row in rows], dtype=float)
    if result.ndim != 2 or result.shape[0] < 50 or not np.isfinite(result).all():
        raise ValueError("Insufficient finite complete windows for reference pilot")
    return result


def check_metadata(training, validation):
    record = training["training_metadata"][0]
    if record.get("incomplete_budget_limit"):
        raise ValueError("Incomplete training metadata")
    annotations = [a for a in record["small_text"] if "commands_" in a["name"] or "scaling_" in a["name"]]
    exclusions = []
    for annotation in annotations:
        for line in annotation["text"].splitlines():
            parts = line.split(";")
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                exclusions.append((int(parts[0]) - 1, int(parts[1]) + 1))
    if not exclusions:
        raise ValueError("Missing command/scaling exclusion intervals")
    normal_intervals = {}
    for scenario in ("scenario5", "scenario3"):
        record = next(r for r in validation["validation_metadata"] if r["archive"].endswith(f"/{scenario}.tar.gz"))
        normal = [a for a in record["small_text"] if "/collection-1/" in a["name"]
                  and a["name"].endswith("experiment.txt") and "Attack: NONE" in a["text"]]
        if len(normal) != 1 or record.get("incomplete_budget_limit"):
            raise ValueError("Normal calibration/check annotation missing")
        annotation = normal[0]
        if not annotation["name"].endswith("/30min_NO_attack_experiment.txt"):
            raise ValueError("Unknown normal experiment duration")
        start_line = next(line for line in annotation["text"].splitlines() if line.startswith("Start date: "))
        parts = start_line.removeprefix("Start date: ").split()
        if len(parts) != 6 or parts[4] not in {"WEST", "WET", "UTC"}:
            raise ValueError("Unknown experiment timezone")
        date = datetime.strptime(" ".join([parts[1], parts[2], parts[3], parts[5]]), "%b %d %H:%M:%S %Y")
        date = date.replace(tzinfo=timezone(timedelta(hours=1 if parts[4] == "WEST" else 0)))
        start = int(date.timestamp())
        normal_intervals[scenario] = (start, start + 1800)
    return exclusions, normal_intervals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--training-intake", type=Path, required=True)
    parser.add_argument("--validation-intake", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    training = json.loads(args.training_intake.read_text(encoding="utf-8"))
    validation = json.loads(args.validation_intake.read_text(encoding="utf-8"))
    exclusions, normal_intervals = check_metadata(training, validation)
    parts, audits = {}, {}
    for name, archive, scenario in (("reference", "SocialNetwork-training-data.zip", None),
                                     ("calibration_normal", "SocialNetwork-validation-data.zip", "scenario5"),
                                     ("check_normal", "SocialNetwork-validation-data.zip", "scenario3")):
        rows, audit = prefix(args.source, archive, scenario)
        if name == "reference":
            filtered = [row for row in rows if not any(lo <= row["window"] <= hi for lo, hi in exclusions)]
            audit["excluded_command_scaling_windows"] = len(rows) - len(filtered)
            rows = filtered
        else:
            start, end = normal_intervals[scenario]
            filtered = [row for row in rows if start <= row["window"] and row["window"] + 1 <= end]
            audit["outside_annotated_normal_interval"] = len(rows) - len(filtered)
            rows = filtered
        parts[name], audits[name] = rows, audit
        print(f"{name}: {len(rows)} complete container-second windows, {audit['parsed_events']} events", flush=True)
    matrices = {name: matrix(rows) for name, rows in parts.items()}
    # Frozen recipe before either normal evaluation; no model or feature search.
    model = IsolationForest(n_estimators=128, max_samples=256, contamination="auto", n_jobs=2, random_state=SEED)
    model.fit(matrices["reference"])
    calibration = -model.score_samples(matrices["calibration_normal"])
    threshold = float(np.nextafter(np.quantile(calibration, .95, method="higher"), np.inf))
    joblib.dump(model, args.output / "reference.joblib")
    report = {"schema": "socialnetwork-reference-pilot-v1", "experimental": True,
              "enforcement_enabled": False, "attack_accuracy": None, "attack_recall": None,
              "reference_normality": "publisher training partition; contamination not ruled out",
              "scope": "first 500000 events or 128MiB per selected node1 trace; not full dataset",
              "features": list(COLUMNS), "seed": SEED, "sklearn_version": sklearn.__version__,
              "threshold": threshold, "calibration_target_fpr": .05, "audits": audits,
              "excluded_intervals": exclusions,
              "annotated_normal_intervals": normal_intervals,
              "model_sha256": sha(args.output / "reference.joblib"),
              "script_sha256": sha(Path(__file__)),
              "features_sha256": sha(Path(__file__).resolve().parents[1] / "data" / "socialnetwork_syscalls.py"),
              "intake_sha256": {str(p.name): sha(p) for p in (args.training_intake, args.validation_intake)},
              "normal_results": {}}
    for name in ("calibration_normal", "check_normal"):
        scores = -model.score_samples(matrices[name])
        alarms = int(np.sum(scores >= threshold))
        report["normal_results"][name] = {"windows": len(scores), "alarms": alarms,
                                          "observed_alarm_fraction": alarms / len(scores)}
    for name, rows in parts.items():
        with (args.output / f"{name}.json").open("x", encoding="utf-8") as handle:
            json.dump(rows, handle)
        report["audits"][name]["features_sha256"] = sha(args.output / f"{name}.json")
    report["seconds"] = time.perf_counter() - started
    with (args.output / "report.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report["normal_results"], indent=2), flush=True)


if __name__ == "__main__":
    main()
