"""Map cached container groups to collector-observed service roles, not labels."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from train_socialnetwork_reference import sha
from socialnetwork_syscalls import first_zip_lines


def service_role(container):
    parts = container.split("_")
    if len(parts) < 6 or parts[0] != "k8s" or not parts[1]:
        raise ValueError("Unknown collector container format")
    return parts[1]


def map_trace(source, wanted, mapping):
    found = set()
    for line in first_zip_lines(source):
        fields = line.split(maxsplit=2)
        if len(fields) < 2:
            raise ValueError("Malformed trace")
        group = hashlib.sha256(fields[1].encode()).hexdigest()
        if group not in wanted:
            continue
        role = service_role(fields[1])
        if group in mapping and mapping[group] != role:
            raise ValueError("Conflicting service role")
        mapping[group] = role
        found.add(group)
        if found == wanted:
            break
    if found != wanted:
        raise ValueError("Could not map every cached group within original prefix budget")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("expanded", type=Path)
    parser.add_argument("development", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    datasets = {"training": json.loads((args.expanded / "reference.json").read_text()),
                "calibration": json.loads((args.reference / "calibration_normal.json").read_text()),
                "normal_check": json.loads((args.reference / "check_normal.json").read_text()),
                "development": json.loads((args.development / "windows.json").read_text())}
    normal_report = json.loads((args.reference / "report.json").read_text())
    for name, filename in (("calibration_normal", "calibration_normal.json"), ("check_normal", "check_normal.json")):
        if normal_report["audits"][name]["features_sha256"] != sha(args.reference / filename):
            raise ValueError("Normal cache changed")
    expanded = json.loads((args.expanded / "report.json").read_text())
    if expanded["reference_rows_sha256"] != sha(args.expanded / "reference.json"):
        raise ValueError("Training cache changed")
    requests = {}
    for row in datasets["training"]:
        requests.setdefault(("SocialNetwork-training-data.zip", "SocialNetwork-training-data/collection-1.tar.gz", row["trace"]), set()).add(row["container_group"])
    for name, scenario in (("calibration", "scenario5"), ("normal_check", "scenario3")):
        trace = f"{scenario}/plain_workload/collection-1/node1/sysdig-socialnetwork-events_000.txt.zip"
        requests[("SocialNetwork-validation-data.zip", f"SocialNetwork-validation-data/{scenario}.tar.gz", trace)] = {r["container_group"] for r in datasets[name]}
    for row in datasets["development"]:
        requests.setdefault(("SocialNetwork-attack-data.zip", "SocialNetwork-attack-data/scenario5.tar.gz", row["trace"]), set()).add(row["container_group"])
    mapping = {}
    for archive_name, member_name in sorted({(a, m) for a, m, _ in requests}):
        with zipfile.ZipFile(args.source / archive_name) as outer:
            with outer.open(member_name) as compressed, gzip.GzipFile(fileobj=compressed) as raw:
                with tarfile.open(fileobj=raw, mode="r|") as nested:
                    for trace in nested:
                        wanted = requests.get((archive_name, member_name, trace.name))
                        if wanted:
                            map_trace(nested.extractfile(trace), wanted, mapping)
                            print(f"Mapped {len(wanted)} groups: {trace.name}", flush=True)
    counts = {}
    for name, rows in datasets.items():
        role_counts = {}
        for row in rows:
            row["service_role"] = mapping[row["container_group"]]
            role_counts[row["service_role"]] = role_counts.get(row["service_role"], 0) + 1
        counts[name] = role_counts
        with (args.output / f"{name}.json").open("x") as handle:
            json.dump(rows, handle)
    manifest = {"schema": "socialnetwork-role-map-v1", "role_source": "collector k8s container-name field, never pod suffix or attack label",
                "script_sha256": sha(Path(__file__)), "role_counts": counts,
                "files_sha256": {name: sha(args.output / f"{name}.json") for name in datasets},
                "groups_mapped": len(mapping), "not_final_test": True}
    with (args.output / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
    print(json.dumps(counts, indent=2), flush=True)


if __name__ == "__main__":
    main()
