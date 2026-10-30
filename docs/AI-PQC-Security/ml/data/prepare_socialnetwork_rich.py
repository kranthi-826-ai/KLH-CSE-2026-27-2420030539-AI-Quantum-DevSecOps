"""Reconstruct richer features on exposed development recordings, preserving base rows."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from socialnetwork_rich_syscalls import RICH_COLUMNS, rich_aggregate
from socialnetwork_syscalls import COLUMNS
from prepare_socialnetwork_development import context_lines, classify_window
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from train_socialnetwork_reference import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("development", type=Path)
    parser.add_argument("exposure", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    old_manifest = json.loads((args.development / "manifest.json").read_text())
    if sha(args.development / "windows.json") != old_manifest["windows_sha256"]:
        raise ValueError("Original development data changed")
    old = json.loads((args.development / "windows.json").read_text())
    lookup_old = {(r["trace"], r["window"], r["container_group"]): r for r in old}
    plan = json.loads((args.exposure / "plan.json").read_text())
    lookup = {trace: case for case in plan["cases"] for trace in case["traces"]}
    args.output.mkdir(parents=True, exist_ok=False)
    definition = {"schema": "socialnetwork-rich-development-v1", "features": list(RICH_COLUMNS),
                  "script_sha256": sha(Path(__file__)), "rich_feature_sha256": sha(Path(__file__).with_name("socialnetwork_rich_syscalls.py")),
                  "base_manifest_sha256": sha(args.development / "manifest.json"), "scope": "same exposed eight cases and pre-injection controls",
                  "not_final_test": True, "preserve_all_base_rows": True}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(definition, handle, indent=2)
    rows_out = []
    with zipfile.ZipFile(args.source / "SocialNetwork-attack-data.zip") as outer:
        with outer.open("SocialNetwork-attack-data/scenario5.tar.gz") as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode="r|") as nested:
                for trace in nested:
                    if trace.name not in lookup:
                        continue
                    case = lookup[trace.name]
                    hashes = set()
                    rows, _ = rich_aggregate(context_lines(nested.extractfile(trace), case, hashes))
                    selected = []
                    for row in rows:
                        label = classify_window(row["window"], case)
                        if row["container_group"] not in hashes or label is None:
                            continue
                        key = (trace.name, row["window"], row["container_group"])
                        baseline = lookup_old[key]
                        if label != baseline["label"] or any(row["features"][name] != baseline["features"][name] for name in COLUMNS):
                            raise ValueError("Base features or annotations differ")
                        selected.append({**row, "label": label, "trace": trace.name, "case": case["id"]})
                    rows_out.extend(selected)
                    print(f"{case['id']} {trace.name.split('/')[-2]}: {len(selected)} enriched windows", flush=True)
    if {(r["trace"], r["window"], r["container_group"]) for r in rows_out} != set(lookup_old):
        raise ValueError("Not exactly the original development observations")
    with (args.output / "windows.json").open("x") as handle:
        json.dump(rows_out, handle)
    manifest = {**definition, "rows": len(rows_out), "windows_sha256": sha(args.output / "windows.json"),
                "base_rows_and_features_verified": True, "plan_sha256": sha(args.output / "plan.json")}
    with (args.output / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
    print(f"Saved {len(rows_out)} rows with {len(RICH_COLUMNS)} features", flush=True)


if __name__ == "__main__":
    main()
