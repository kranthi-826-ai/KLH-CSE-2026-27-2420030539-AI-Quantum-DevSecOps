"""One-shot bounded exposure evaluation of the already-frozen syscall reference."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import tarfile
import time
import zipfile

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def epoch_ns(value):
    number = int(value)
    if 1_000_000_000 <= number < 10_000_000_000:
        return number * 1_000_000_000
    if 1_000_000_000_000_000_000 <= number < 10_000_000_000_000_000_000:
        return number
    raise ValueError("Unsupported timestamp unit; refuse to guess")


def parse_dates(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError("Expected interval and exactly one affected pod")
    start, end = [epoch_ns(v) for v in lines[0].split(";")]
    if not 0 < end - start <= 60_000_000_000:
        raise ValueError("Unsupported attack duration")
    return {"start_ns": start, "end_ns": end, "pod": lines[1]}


def matching_pod(container, pod):
    parts = container.split("_")
    return len(parts) >= 4 and parts[0] == "k8s" and parts[2] == pod


def cases_from_metadata(metadata):
    record = next(r for r in metadata["attack_metadata"] if r["archive"].endswith("/scenario5.tar.gz"))
    if record.get("incomplete_budget_limit"):
        raise ValueError("Incomplete attack annotation metadata")
    cases = []
    for entry in record["small_text"]:
        if "/plain_workload/" not in entry["name"] or not entry["name"].endswith("/collection-1/dates.txt"):
            continue
        base = entry["name"].removesuffix("/dates.txt")
        annotation = next(a for a in record["small_text"] if a["name"] == base + "/30min_attack_experiment.txt")
        dates = parse_dates(entry["text"])
        if dates["pod"] not in annotation["text"] or entry["text"].splitlines()[0] not in annotation["text"]:
            raise ValueError("Conflicting dates and experiment annotations")
        traces = [h["name"] for h in record["headers"] if h["name"].startswith(base + "/node")
                  and h["name"].endswith("events_000.txt.zip")]
        if len(traces) != 2:
            raise ValueError("Expected both worker-node traces")
        cases.append({"id": base.split("/")[-2], "base": base, "traces": sorted(traces), **dates})
    if len(cases) != 8 or len({case["id"] for case in cases}) != 8:
        raise ValueError("Expected eight distinct CVE cases")
    return sorted(cases, key=lambda case: case["id"])


def selected_lines(source, case, audit, pod_hashes):
    low = (case["start_ns"] // 1_000_000_000 - 1) * 1_000_000_000
    high = (math.ceil(case["end_ns"] / 1_000_000_000) + 1) * 1_000_000_000
    # No whole-trace accumulation: only a few seconds are retained for aggregation.
    for line in first_zip_lines(source, max_lines=20_000_000, max_bytes=2 * 1024**3):
        audit["scanned_events"] += 1
        fields = line.split(maxsplit=2)
        if len(fields) < 2:
            raise ValueError("Malformed timestamp/container")
        timestamp = int(fields[0])
        audit["max_timestamp_ns"] = max(audit["max_timestamp_ns"], timestamp)
        if timestamp > high:
            # Continue a 1s cushion: the audited feature slice ends at high.
            if timestamp > high + 1_000_000_000:
                break
            continue
        if timestamp < low:
            continue
        if matching_pod(fields[1], case["pod"]):
            pod_hashes.add(hashlib.sha256(fields[1].encode()).hexdigest())
        yield line


def score_trace(source, case, model, threshold):
    audit = {"scanned_events": 0, "max_timestamp_ns": 0}
    pod_hashes = set()
    rows, feature_audit = aggregate(selected_lines(source, case, audit, pod_hashes))
    overlap = [row for row in rows if row["container_group"] in pod_hashes
               and row["window"] * 1_000_000_000 < case["end_ns"]
               and (row["window"] + 1) * 1_000_000_000 > case["start_ns"]]
    scores = (-model.score_samples([[row["features"][key] for key in COLUMNS] for row in overlap])).tolist() if overlap else []
    records = [{"window": row["window"], "score": score, "alert": score >= threshold,
                "fully_inside_interval": row["window"] * 1_000_000_000 >= case["start_ns"]
                and (row["window"] + 1) * 1_000_000_000 <= case["end_ns"]}
               for row, score in zip(overlap, scores)]
    return {**audit, "feature_audit": feature_audit, "matched_container_groups": len(pod_hashes),
            "positive_exposure_windows": records, "coverage_reaches_attack_end": audit["max_timestamp_ns"] >= case["end_ns"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("One-shot evaluation output already exists")
    report = json.loads((args.candidate / "report.json").read_text())
    if sha(args.candidate / "reference.joblib") != report["model_sha256"] or sha(Path(__file__).resolve().parents[1] / "data" / "socialnetwork_syscalls.py") != report["features_sha256"]:
        raise ValueError("Frozen model or feature implementation changed")
    cases = cases_from_metadata(json.loads(args.metadata.read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-exposure-evaluation-v1", "cases": cases,
            "scope": "all eight CVEs, scenario5/plain_workload/collection1, both workers; other scenarios untouched",
            "labels": "affected-pod windows overlapping annotated execution intervals; exposure not guaranteed exploit success",
            "threshold": report["threshold"], "model_sha256": report["model_sha256"],
            "feature_sha256": report["features_sha256"], "evaluator_sha256": sha(Path(__file__)),
            "metadata_sha256": sha(args.metadata), "normal_check": report["normal_results"]["check_normal"],
            "max_events_per_trace": 20000000, "max_decoded_bytes_per_trace": 2 * 1024**3}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    model = joblib.load(args.candidate / "reference.joblib")
    started = time.perf_counter()
    outcomes = {case["id"]: {"traces": [], "case": case} for case in cases}
    lookup = {trace: case for case in cases for trace in case["traces"]}
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case = lookup[trace.name]
                    result = score_trace(nested.extractfile(trace), case, model, plan["threshold"])
                    outcomes[case["id"]]["traces"].append({"name": trace.name, **result})
                    print(f"{case['id']} {trace.name.split('/')[-2]}: {len(result['positive_exposure_windows'])} exposure windows", flush=True)
                    with (args.output / "progress.jsonl").open("a") as handle:
                        handle.write(json.dumps({"case": case["id"], "trace": trace.name, "result": result}) + "\n")
    results = []
    for case_id, entry in outcomes.items():
        windows = [w for trace in entry["traces"] for w in trace["positive_exposure_windows"]]
        results.append({**entry, "id": case_id, "exposure_windows": len(windows),
                        "alerts": sum(w["alert"] for w in windows), "case_alerted": any(w["alert"] for w in windows),
                        "both_workers_scanned": len(entry["traces"]) == 2})
    eligible = [r for r in results if r["exposure_windows"] > 0 and r["both_workers_scanned"]]
    final = {"plan_sha256": sha(args.output / "plan.json"), "results": results, "covered_cases": len(eligible),
             "alerted_cases": sum(r["case_alerted"] for r in eligible), "seconds": time.perf_counter() - started,
             "attack_accuracy": None, "enforcement_enabled": False}
    with (args.output / "result.json").open("x") as handle:
        json.dump(final, handle, indent=2)
    print(json.dumps({k: v for k, v in final.items() if k != "results"}), flush=True)


if __name__ == "__main__":
    main()
