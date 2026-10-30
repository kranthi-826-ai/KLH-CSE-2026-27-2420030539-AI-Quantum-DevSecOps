"""Matched grouped temporal ablation; fixed recipes and no independent-test access."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.model_selection import LeaveOneGroupOut

from study_socialnetwork_supervised import RECIPES, build, metrics
from train_socialnetwork_reference import sha
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS
from socialnetwork_rich_syscalls import RICH_COLUMNS
from socialnetwork_temporal import TEMPORAL_COLUMNS


def canonical_rows(rows, reference):
    key = lambda row: (row["trace"], row["window"], row["container_group"])
    lookup = {key(row): row for row in rows}
    if len(lookup) != len(rows) or set(lookup) != {key(row) for row in reference}:
        raise ValueError("Matched observation keys changed")
    return [lookup[key(row)] for row in reference]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("previous_report", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--old-data", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    if not manifest["all_selected_histories_complete"] or not manifest["matched_prior_features_and_labels"] or sha(args.data / "windows.json") != manifest["windows_sha256"]:
        raise ValueError("Unverified temporal data")
    feature_path = Path(__file__).resolve().parents[1] / "data" / "socialnetwork_temporal.py"
    if sha(feature_path) != manifest["temporal_feature_sha256"]:
        raise ValueError("Temporal implementation changed")
    rows = json.loads((args.data / "windows.json").read_text())
    old_manifest = json.loads((args.old_data / "manifest.json").read_text())
    if sha(args.old_data / "manifest.json") != manifest["old_manifest_sha256"] or sha(args.old_data / "windows.json") != old_manifest["windows_sha256"]:
        raise ValueError("Original matched row order changed")
    rows = canonical_rows(rows, json.loads((args.old_data / "windows.json").read_text()))
    previous = json.loads(args.previous_report.read_text())
    y = np.asarray([r["label"] for r in rows])
    groups = np.asarray([r["case"] for r in rows])
    args.output.mkdir(parents=True, exist_ok=False)
    versions = {"base": COLUMNS, "rich": RICH_COLUMNS, "temporal": TEMPORAL_COLUMNS}
    plan = {"schema": "socialnetwork-temporal-grouped-v1", "features": {k: list(v) for k, v in versions.items()},
            "recipes": list(RECIPES), "threshold": .5, "validation": "leave one CVE out across both recordings, eight folds",
            "script_sha256": sha(Path(__file__)), "recipe_sha256": sha(Path(__file__).with_name("study_socialnetwork_supervised.py")),
            "feature_sha256": sha(feature_path), "manifest_sha256": sha(args.data / "manifest.json"),
            "previous_report_sha256": sha(args.previous_report), "recall_min": .95, "control_alarm_max": .05,
            "row_order_sha256": sha(args.old_data / "windows.json"),
            "independent_evaluation_required": True, "promotion_allowed": False}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    results = {}
    for version, columns in versions.items():
        x = np.asarray([[r["features"][key] for key in columns] for r in rows])
        if not np.isfinite(x).all():
            raise ValueError("Nonfinite features")
        for name in RECIPES:
            pred = np.zeros(len(rows), dtype=int)
            folds = []
            for train, validation in LeaveOneGroupOut().split(x, y, groups):
                if set(groups[train]) & set(groups[validation]):
                    raise ValueError("CVE group leakage")
                model = build(name).fit(x[train], y[train])
                prediction = model.predict_proba(x[validation])[:, 1] >= .5
                pred[validation] = prediction
                folds.append({"held_out": str(groups[validation][0]), "train_cves": sorted(set(groups[train])),
                              **metrics(y[validation], prediction)})
            summary = metrics(y, pred)
            if version != "temporal" and summary != previous["results"][f"{version}_{name}"]["metrics"]:
                raise ValueError("Matched baseline no longer reproduces")
            eligible = bool(summary["exposure_recall"] >= .95 and summary["control_alarm_fraction"] <= .05)
            key = f"{version}_{name}"
            results[key] = {"metrics": summary, "folds": folds, "eligible": eligible,
                            "window_predictions": pred.tolist()}
            print(f"{key}: {summary}; eligible={eligible}", flush=True)
    eligible = [k for k, v in results.items() if k.startswith("temporal_") and v["eligible"]]
    winner = max(eligible, key=lambda k: results[k]["metrics"]["macro_f1"]) if eligible else None
    report = {"schema": plan["schema"], "results": results, "selected_candidate": winner,
              "promoted": False, "enforcement_enabled": False, "independent_evaluation_required": True,
              "plan_sha256": sha(args.output / "plan.json"), "not_final_test": True, "attack_accuracy": None}
    if winner:
        model = build(winner.removeprefix("temporal_")).fit(
            np.asarray([[r["features"][k] for k in TEMPORAL_COLUMNS] for r in rows]), y)
        joblib.dump(model, args.output / "candidate.joblib")
        report["model_sha256"] = sha(args.output / "candidate.joblib")
    with (args.output / "report.json").open("x") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    main()
