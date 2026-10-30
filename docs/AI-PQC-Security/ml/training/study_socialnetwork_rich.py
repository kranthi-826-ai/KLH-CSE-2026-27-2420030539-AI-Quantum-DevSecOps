"""Matched grouped comparison: base versus richer syscall features, no final test."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    if sha(args.data / "windows.json") != manifest["windows_sha256"] or not manifest["base_rows_and_features_verified"]:
        raise ValueError("Rich development data unverified")
    if manifest["rich_feature_sha256"] != sha(Path(__file__).resolve().parents[1] / "data" / "socialnetwork_rich_syscalls.py"):
        raise ValueError("Rich feature code changed")
    rows = json.loads((args.data / "windows.json").read_text())
    y = np.asarray([row["label"] for row in rows])
    groups = np.asarray([row["case"] for row in rows])
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-rich-supervised-development-v1", "recipes": list(RECIPES),
            "feature_sets": {"base": list(COLUMNS), "rich": list(RICH_COLUMNS)}, "threshold": .5,
            "validation": "eight leave-one-CVE-recording-group-out folds", "promotion_allowed": False,
            "data_manifest_sha256": sha(args.data / "manifest.json"), "script_sha256": sha(Path(__file__)),
            "recipe_sha256": sha(Path(__file__).with_name("study_socialnetwork_supervised.py")),
            "exposure_recall_min": .95, "control_alarm_fraction_max": .05,
            "independent_evaluation_required": True, "not_final_test": True}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    results = {}
    for version, columns in (("base", COLUMNS), ("rich", RICH_COLUMNS)):
        x = np.asarray([[row["features"][key] for key in columns] for row in rows])
        for name in RECIPES:
            predictions = np.zeros(len(y), dtype=int)
            folds = []
            for train, validation in LeaveOneGroupOut().split(x, y, groups):
                if set(groups[train]) & set(groups[validation]):
                    raise ValueError("CVE group leakage")
                model = build(name).fit(x[train], y[train])
                pred = model.predict_proba(x[validation])[:, 1] >= .5
                predictions[validation] = pred
                folds.append({"held_out": str(groups[validation][0]), **metrics(y[validation], pred)})
            summary = metrics(y, predictions)
            eligible = bool(summary["exposure_recall"] >= .95 and summary["control_alarm_fraction"] <= .05)
            results[f"{version}_{name}"] = {"metrics": summary, "folds": folds, "eligible": eligible}
            print(f"{version}_{name}: {summary}, eligible={eligible}", flush=True)
    eligible = [key for key in results if key.startswith("rich_") and results[key]["eligible"]]
    winner = max(eligible, key=lambda key: results[key]["metrics"]["macro_f1"]) if eligible else None
    report = {"schema": plan["schema"], "results": results, "selected_candidate": winner,
              "enforcement_enabled": False, "promoted": False, "plan_sha256": sha(args.output / "plan.json"),
              "independent_evaluation_required": True, "attack_accuracy": None}
    if winner:
        model = build(winner.removeprefix("rich_")).fit(
            np.asarray([[row["features"][key] for key in RICH_COLUMNS] for row in rows]), y)
        joblib.dump(model, args.output / "candidate.joblib")
        report["model_sha256"] = sha(args.output / "candidate.joblib")
    with (args.output / "report.json").open("x") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    main()
