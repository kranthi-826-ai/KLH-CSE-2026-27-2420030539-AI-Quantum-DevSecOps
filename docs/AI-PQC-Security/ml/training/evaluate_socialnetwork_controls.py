"""One-shot matched pre-injection controls; never refit/recalibrate the model."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import time
import zipfile

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines
from evaluate_socialnetwork_attacks import cases_from_metadata, matching_pod, sha


def control_lines(source, case, audit, hashes):
    low = case["start_ns"] - 60_000_000_000
    high = case["start_ns"] - 10_000_000_000
    for line in first_zip_lines(source, max_lines=20_000_000, max_bytes=2 * 1024**3):
        audit["scanned_events"] += 1
        fields = line.split(maxsplit=2)
        timestamp = int(fields[0])
        audit["max_timestamp_ns"] = max(audit["max_timestamp_ns"], timestamp)
        if timestamp > high + 1_000_000_000:
            break
        if not low <= timestamp <= high:
            continue
        if matching_pod(fields[1], case["pod"]):
            hashes.add(hashlib.sha256(fields[1].encode()).hexdigest())
        yield line


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Control evaluation already started")
    report = json.loads((args.candidate / "report.json").read_text())
    if sha(args.candidate / "reference.joblib") != report["model_sha256"] or sha(Path(__file__).resolve().parents[1] / "data" / "socialnetwork_syscalls.py") != report["features_sha256"]:
        raise ValueError("Frozen model/features changed")
    metadata = json.loads(args.metadata.read_text())
    cases = cases_from_metadata(metadata)
    record = next(r for r in metadata["attack_metadata"] if r["archive"].endswith("/scenario5.tar.gz"))
    for case in cases:
        annotation = next(a for a in record["small_text"] if a["name"] == case["base"] + "/30min_attack_experiment.txt")
        if "CMDs: 0\n" not in annotation["text"]:
            raise ValueError("Control workload has enrichment commands")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-pre-injection-control-v1", "cases": cases,
            "interval": "60 to 10 seconds before injection; only annotated affected pod",
            "model_sha256": report["model_sha256"], "feature_sha256": report["features_sha256"],
            "threshold": report["threshold"], "script_sha256": sha(Path(__file__)),
            "protocol_sha256": sha(Path(__file__).resolve().parents[2] / "docs/research/socialnetwork-control-protocol-v1.md")}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    model = joblib.load(args.candidate / "reference.joblib")
    lookup = {trace: case for case in cases for trace in case["traces"]}
    outcomes = []
    started = time.perf_counter()
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case = lookup[trace.name]
                    audit = {"scanned_events": 0, "max_timestamp_ns": 0}
                    hashes = set()
                    rows, feature_audit = aggregate(control_lines(nested.extractfile(trace), case, audit, hashes))
                    low, high = case["start_ns"] - 60_000_000_000, case["start_ns"] - 10_000_000_000
                    rows = [row for row in rows if row["container_group"] in hashes and row["window"] * 1_000_000_000 >= low
                            and (row["window"] + 1) * 1_000_000_000 <= high]
                    scores = (-model.score_samples([[row["features"][key] for key in COLUMNS] for row in rows])).tolist() if rows else []
                    outcome = {"case": case["id"], "trace": trace.name, **audit, "feature_audit": feature_audit,
                               "windows": len(rows), "alarms": sum(s >= plan["threshold"] for s in scores),
                               "scores": scores, "control_window_ids": [r["window"] for r in rows]}
                    outcomes.append(outcome)
                    with (args.output / "progress.jsonl").open("a") as handle:
                        handle.write(json.dumps(outcome) + "\n")
                    print(f"{case['id']} {trace.name.split('/')[-2]}: {len(rows)} control windows", flush=True)
    total = sum(r["windows"] for r in outcomes)
    alarms = sum(r["alarms"] for r in outcomes)
    final = {"plan_sha256": sha(args.output / "plan.json"), "results": outcomes,
             "control_windows": total, "control_alarms": alarms,
             "control_alarm_fraction": alarms / total if total else None,
             "seconds": time.perf_counter() - started, "enforcement_enabled": False}
    with (args.output / "result.json").open("x") as handle:
        json.dump(final, handle, indent=2)
    print(json.dumps({k: v for k, v in final.items() if k != "results"}), flush=True)


if __name__ == "__main__":
    main()
