"""Add predeclared second DEVELOPMENT recordings, preserving independent scenarios."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from socialnetwork_rich_syscalls import rich_aggregate, RICH_COLUMNS
from prepare_socialnetwork_development import context_lines, classify_window
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_socialnetwork_attacks import parse_dates, sha


def additional_cases(metadata):
    record = next(r for r in metadata["attack_metadata"] if r["archive"].endswith("/scenario5.tar.gz"))
    if record.get("incomplete_budget_limit"):
        raise ValueError("Incomplete metadata")
    cases = []
    for item in record["small_text"]:
        if "/plain_workload/" not in item["name"] or not item["name"].endswith("/collection-2/dates.txt"):
            continue
        base = item["name"].removesuffix("/dates.txt")
        annotation = next(a for a in record["small_text"] if a["name"] == base + "/30min_attack_experiment.txt")
        dates = parse_dates(item["text"])
        if "CMDs: 0\n" not in annotation["text"] or item["text"].splitlines()[0] not in annotation["text"] or dates["pod"] not in annotation["text"]:
            raise ValueError("Conflicting annotation or enriched workload")
        traces = sorted(h["name"] for h in record["headers"] if h["name"].startswith(base + "/node") and h["name"].endswith("events_000.txt.zip"))
        if len(traces) != 2:
            raise ValueError("Missing worker")
        cases.append({"id": base.split("/")[-2], "base": base, "traces": traces, **dates})
    if len(cases) != 8 or len({case["id"] for case in cases}) != 8:
        raise ValueError("Expected all eight CVEs")
    return sorted(cases, key=lambda c: c["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    original_manifest = json.loads((args.old / "manifest.json").read_text())
    if sha(args.old / "windows.json") != original_manifest["windows_sha256"]:
        raise ValueError("Original feature data changed")
    cases = additional_cases(json.loads(args.metadata.read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-expanded-development-v1", "cases": cases, "not_final_test": True,
            "protocol_sha256": sha(Path(__file__).resolve().parents[2] / "docs/research/socialnetwork-development-expansion-protocol-v1.md"),
            "old_manifest_sha256": sha(args.old / "manifest.json"), "metadata_sha256": sha(args.metadata),
            "script_sha256": sha(Path(__file__)), "rich_feature_sha256": sha(Path(__file__).with_name("socialnetwork_rich_syscalls.py"))}
    if plan["rich_feature_sha256"] != original_manifest["rich_feature_sha256"]:
        raise ValueError("Feature definition changed")
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    old_rows = json.loads((args.old / "windows.json").read_text())
    additional = []
    coverage = []
    lookup = {trace: case for case in cases for trace in case["traces"]}
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case = lookup[trace.name]
                    hashes, timestamps = set(), []
                    def observed():
                        for line in context_lines(nested.extractfile(trace), case, hashes):
                            # Context only: a few seconds, not all scanned events.
                            timestamps.append(int(line.split(maxsplit=1)[0]))
                            yield line
                    rows, audit = rich_aggregate(observed())
                    if not timestamps or max(timestamps) < case["end_ns"]:
                        raise ValueError("Scan cap or trace end prevented annotation coverage")
                    selected = []
                    for row in rows:
                        label = classify_window(row["window"], case)
                        if label is not None and row["container_group"] in hashes:
                            selected.append({**row, "label": label, "case": case["id"], "trace": trace.name})
                    additional.extend(selected)
                    coverage.append({"trace": trace.name, "rows": len(selected), "reached_attack_end": True, "audit": audit})
                    print(f"{case['id']} {trace.name.split('/')[-2]}: {len(selected)} new development windows", flush=True)
    if len(coverage) != 16 or any(not any(row["label"] == 1 and row["case"] == case["id"] for row in additional) for case in cases):
        raise ValueError("Missing recording/positive coverage")
    rows = old_rows + additional
    keys = [(r["trace"], r["window"], r["container_group"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate observations")
    with (args.output / "windows.json").open("x") as handle:
        json.dump(rows, handle)
    manifest = {"schema": plan["schema"], "features": list(RICH_COLUMNS), "not_final_test": True,
                "old_rows_preserved": len(old_rows), "new_rows": len(additional), "rows": len(rows),
                "positive_rows": sum(r["label"] for r in rows), "control_rows": sum(r["label"] == 0 for r in rows),
                "base_rows_and_features_verified": True, "base_verification_scope": "old rows preserved; new base fields computed by unchanged original aggregate through rich wrapper",
                "rich_feature_sha256": plan["rich_feature_sha256"], "windows_sha256": sha(args.output / "windows.json"),
                "plan_sha256": sha(args.output / "plan.json"), "coverage": coverage}
    with (args.output / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
    print(json.dumps({key: manifest[key] for key in ("old_rows_preserved", "new_rows", "rows", "positive_rows", "control_rows")}), flush=True)


if __name__ == "__main__":
    main()
