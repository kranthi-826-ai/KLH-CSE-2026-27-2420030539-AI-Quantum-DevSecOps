"""Cache exposed development features, requiring exact replay of frozen scores."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_socialnetwork_attacks import matching_pod, sha
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines


def context_lines(source, case, hashes):
    low = case["start_ns"] - 60_000_000_000
    high = ((case["end_ns"] + 999_999_999) // 1_000_000_000 + 1) * 1_000_000_000
    for line in first_zip_lines(source, max_lines=20_000_000, max_bytes=2 * 1024**3):
        parts = line.split(maxsplit=2)
        timestamp = int(parts[0])
        if timestamp > high + 1_000_000_000:
            break
        if not low <= timestamp <= high:
            continue
        if matching_pod(parts[1], case["pod"]):
            hashes.add(hashlib.sha256(parts[1].encode()).hexdigest())
        yield line


def classify_window(window, case):
    start, end = window * 1_000_000_000, (window + 1) * 1_000_000_000
    if start < case["end_ns"] and end > case["start_ns"]:
        return 1
    if start >= case["start_ns"] - 60_000_000_000 and end <= case["start_ns"] - 10_000_000_000:
        return 0
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("exposure", type=Path)
    parser.add_argument("controls", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    exposure = json.loads((args.exposure / "result.json").read_text())
    controls = json.loads((args.controls / "result.json").read_text())
    plan = json.loads((args.exposure / "plan.json").read_text())
    if sha(args.candidate / "reference.joblib") != plan["model_sha256"]:
        raise ValueError("Wrong frozen baseline")
    args.output.mkdir(parents=True, exist_ok=False)
    model = joblib.load(args.candidate / "reference.joblib")
    positive = {trace["name"]: trace["positive_exposure_windows"] for case in exposure["results"] for trace in case["traces"]}
    negative = {trace["trace"]: trace for trace in controls["results"]}
    lookup = {trace: case for case in plan["cases"] for trace in case["traces"]}
    rows_out = []
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case = lookup[trace.name]
                    hashes = set()
                    rows, _ = aggregate(context_lines(nested.extractfile(trace), case, hashes))
                    selected = []
                    for row in rows:
                        label = classify_window(row["window"], case)
                        if row["container_group"] not in hashes or label is None:
                            continue
                        selected.append({**row, "label": label, "case": case["id"], "trace": trace.name})
                    for label in (0, 1):
                        part = [row for row in selected if row["label"] == label]
                        expected_windows = negative[trace.name]["control_window_ids"] if label == 0 else [w["window"] for w in positive[trace.name]]
                        expected_scores = negative[trace.name]["scores"] if label == 0 else [w["score"] for w in positive[trace.name]]
                        if [row["window"] for row in part] != expected_windows:
                            raise ValueError("Cached windows differ from the frozen evaluation")
                        scores = -model.score_samples([[row["features"][key] for key in COLUMNS] for row in part]) if part else []
                        if not np.allclose(scores, expected_scores, rtol=0, atol=1e-12):
                            raise ValueError("Feature reconstruction does not replay frozen scores")
                    rows_out.extend(selected)
                    print(f"{case['id']} {trace.name.split('/')[-2]}: {len(selected)} replay-verified windows", flush=True)
    with (args.output / "windows.json").open("x") as handle:
        json.dump(rows_out, handle)
    manifest = {"schema": "socialnetwork-exposed-development-v1", "not_final_test": True,
                "features": list(COLUMNS), "feature_sha256": plan["feature_sha256"],
                "baseline_replay_verified": True, "rows": len(rows_out),
                "positive_rows": sum(row["label"] for row in rows_out),
                "negative_rows": sum(row["label"] == 0 for row in rows_out),
                "windows_sha256": sha(args.output / "windows.json"), "script_sha256": sha(Path(__file__)),
                "exposure_result_sha256": sha(args.exposure / "result.json"),
                "control_result_sha256": sha(args.controls / "result.json")}
    with (args.output / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
    print(json.dumps(manifest), flush=True)


if __name__ == "__main__":
    main()
