"""Continuous raw context for matched temporal development; no final scenarios."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from socialnetwork_syscalls import first_zip_lines
from socialnetwork_rich_syscalls import rich_aggregate, RICH_COLUMNS
from socialnetwork_temporal import add_history, TEMPORAL_COLUMNS
from prepare_socialnetwork_development import classify_window
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_socialnetwork_attacks import matching_pod, sha


def context(source, case, hashes, audit):
    low = case["start_ns"] - 70_000_000_000
    high = ((case["end_ns"] + 999_999_999) // 1_000_000_000 + 1) * 1_000_000_000
    previous_max = 0
    for line in first_zip_lines(source, max_lines=20_000_000, max_bytes=2 * 1024**3):
        parts = line.split(maxsplit=2)
        timestamp = int(parts[0])
        if timestamp < previous_max - 1_000_000_000:
            raise ValueError("More than1second timestamp regression; unsafe streaming cutoff")
        previous_max = max(previous_max, timestamp)
        audit["scanned_events"] += 1
        if timestamp > high + 1_000_000_000:
            break
        if not low <= timestamp <= high:
            continue
        audit["first_context_ns"] = min(audit.get("first_context_ns", timestamp), timestamp)
        audit["last_context_ns"] = max(audit.get("last_context_ns", timestamp), timestamp)
        if matching_pod(parts[1], case["pod"]):
            hashes.add(hashlib.sha256(parts[1].encode()).hexdigest())
        yield line


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("first_plan", type=Path)
    parser.add_argument("second_plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.old / "manifest.json").read_text())
    if sha(args.old / "windows.json") != manifest["windows_sha256"]:
        raise ValueError("Original development data changed")
    old_rows = json.loads((args.old / "windows.json").read_text())
    old = {(r["trace"], r["window"], r["container_group"]): r for r in old_rows}
    cases = json.loads(args.first_plan.read_text())["cases"] + json.loads(args.second_plan.read_text())["cases"]
    if len(cases) != 16 or any(not case["base"].startswith("scenario5/plain_workload/") for case in cases):
        raise ValueError("Development boundary changed")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-temporal-development-v1", "cases": cases, "features": list(TEMPORAL_COLUMNS),
            "context_before_seconds": 70, "prior_completed_windows_seconds": 5,
            "old_manifest_sha256": sha(args.old / "manifest.json"), "script_sha256": sha(Path(__file__)),
            "temporal_feature_sha256": sha(Path(__file__).with_name("socialnetwork_temporal.py")),
            "rich_feature_sha256": sha(Path(__file__).with_name("socialnetwork_rich_syscalls.py")), "not_final_test": True}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    lookup = {trace: case for case in cases for trace in case["traces"]}
    selected, audits = [], []
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case, hashes, audit = lookup[trace.name], set(), {"trace": trace.name, "scanned_events": 0}
                    rows, _ = rich_aggregate(context(nested.extractfile(trace), case, hashes, audit))
                    if audit.get("last_context_ns", 0) < case["end_ns"]:
                        raise ValueError("Incomplete scan")
                    first_full = (audit["first_context_ns"] + 999_999_999) // 1_000_000_000
                    # History is built on ALL context, before any annotation label selection.
                    enriched = add_history(rows, first_full)
                    count = 0
                    for row in enriched:
                        label = classify_window(row["window"], case)
                        if label is None or row["container_group"] not in hashes:
                            continue
                        key = (trace.name, row["window"], row["container_group"])
                        prior = old[key]
                        if label != prior["label"] or any(row["features"][k] != prior["features"][k] for k in RICH_COLUMNS):
                            raise ValueError("Matched row feature/label changed")
                        if not row["history_complete"]:
                            raise ValueError("Insufficient true warmup; do not fabricate history")
                        selected.append({**row, "label": label, "case": case["id"], "trace": trace.name})
                        count += 1
                    audits.append(audit)
                    print(f"{trace.name}: {count} matched temporal windows", flush=True)
    if {(r["trace"], r["window"], r["container_group"]) for r in selected} != set(old) or len(selected) != len(old):
        raise ValueError("Original observation coverage changed")
    with (args.output / "windows.json").open("x") as handle:
        json.dump(selected, handle)
    output = {**plan, "rows": len(selected), "windows_sha256": sha(args.output / "windows.json"),
              "plan_sha256": sha(args.output / "plan.json"), "matched_prior_features_and_labels": True,
              "all_selected_histories_complete": True, "audits": audits}
    with (args.output / "manifest.json").open("x") as handle:
        json.dump(output, handle, indent=2)


if __name__ == "__main__":
    main()
