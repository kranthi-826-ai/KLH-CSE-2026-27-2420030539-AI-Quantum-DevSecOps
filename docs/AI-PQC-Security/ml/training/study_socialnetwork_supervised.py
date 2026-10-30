"""Small grouped development study; exposure labels do not imply exploit success."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from train_socialnetwork_reference import sha, SEED
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS

RECIPES = ("logistic", "random_forest", "xgboost")


def build(name):
    if name == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(C=.5, class_weight="balanced", max_iter=1000, random_state=SEED))
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=128, max_depth=4, min_samples_leaf=2, class_weight="balanced", n_jobs=2, random_state=SEED)
    if name == "xgboost":
        return XGBClassifier(n_estimators=128, max_depth=2, learning_rate=.05, min_child_weight=3,
                             reg_lambda=4, n_jobs=2, random_state=SEED, tree_method="hist", eval_metric="logloss")
    raise ValueError("Unknown recipe")


def metrics(y, predictions):
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "macro_f1": float(f1_score(y, predictions, average="macro")),
            "exposure_recall": float(tp / (tp + fn)), "control_alarm_fraction": float(fp / (fp + tn))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    if sha(args.data / "windows.json") != manifest["windows_sha256"] or not manifest["baseline_replay_verified"]:
        raise ValueError("Unverified development data")
    rows = json.loads((args.data / "windows.json").read_text())
    x = np.asarray([[row["features"][key] for key in COLUMNS] for row in rows])
    y = np.asarray([row["label"] for row in rows])
    groups = np.asarray([row["case"] for row in rows])
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-supervised-development-v1", "recipes": list(RECIPES),
            "threshold": .5, "validation": "leave-one-CVE-recording-group-out, eight folds",
            "data_manifest_sha256": sha(args.data / "manifest.json"), "script_sha256": sha(Path(__file__)),
            "features": list(COLUMNS), "exposure_recall_min": .95, "control_alarm_fraction_max": .05,
            "not_final_test": True, "independent_evaluation_required": True, "promotion_allowed": False}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    results = {}
    for name in RECIPES:
        predictions = np.zeros(len(y), dtype=int)
        folds = []
        for train, validation in LeaveOneGroupOut().split(x, y, groups):
            if set(groups[train]) & set(groups[validation]):
                raise ValueError("Group leakage")
            model = build(name).fit(x[train], y[train])
            pred = model.predict_proba(x[validation])[:, 1] >= .5
            predictions[validation] = pred
            folds.append({"held_out": str(groups[validation][0]), "train_rows": len(train),
                          "validation_rows": len(validation), **metrics(y[validation], pred)})
        summary = metrics(y, predictions)
        eligible = summary["exposure_recall"] >= .95 and summary["control_alarm_fraction"] <= .05
        results[name] = {"metrics": summary, "folds": folds, "eligible_for_independent_evaluation": bool(eligible)}
        print(f"{name}: {summary}; eligible={eligible}", flush=True)
    eligible = [name for name in RECIPES if results[name]["eligible_for_independent_evaluation"]]
    winner = max(eligible, key=lambda name: results[name]["metrics"]["macro_f1"]) if eligible else None
    report = {"schema": plan["schema"], "results": results, "selected_candidate": winner,
              "plan_sha256": sha(args.output / "plan.json"), "enforcement_enabled": False,
              "independent_evaluation_required": True, "accuracy_not_reported_for_artificial_class_ratio": True}
    if winner:
        model = build(winner).fit(x, y)
        joblib.dump(model, args.output / "candidate.joblib")
        report["model_sha256"] = sha(args.output / "candidate.joblib")
    with (args.output / "report.json").open("x") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    main()
