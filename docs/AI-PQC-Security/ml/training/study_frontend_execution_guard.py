"""Exploratory process-execution guard plus existing OOF ML; NOT pure-ML accuracy."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from study_socialnetwork_supervised import metrics
from study_socialnetwork_temporal import canonical_rows
from train_socialnetwork_reference import sha


def guard(features):
    return any(features[key] > 0 for key in ("sensitive_entry_execve", "sensitive_entry_execveat", "prior5_execve", "prior5_execveat"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    if sha(args.data / "windows.json") != manifest["windows_sha256"]:
        raise ValueError("Temporal data changed")
    rows = canonical_rows(json.loads((args.data / "windows.json").read_text()), json.loads((args.old / "windows.json").read_text()))
    study = json.loads(args.study.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "frontend-process-guard-development-v1", "rule": "current or prior5-second observed execve/execveat count>0",
            "scope": "only selected frontend target-pod development observations; NOT universal microservice blocking policy",
            "ml": "unchanged grouped OOF base_logistic predictions", "posthoc_development_hypothesis": True,
            "pure_ml_improvement_claim_allowed": False, "promotion_allowed": False,
            "data_sha256": sha(args.data / "windows.json"), "study_sha256": sha(args.study), "script_sha256": sha(Path(__file__)),
            "independent_evaluation_required": True}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    y = np.asarray([r["label"] for r in rows])
    ml = np.asarray(study["results"]["base_logistic"]["window_predictions"], dtype=bool)
    rule = np.asarray([guard(r["features"]) for r in rows])
    result = {"schema": plan["schema"], "ml_only": metrics(y, ml), "guard_only": metrics(y, rule),
              "combined": metrics(y, ml | rule), "plan_sha256": sha(args.output / "plan.json"),
              "not_final_test": True, "promoted": False, "enforcement_enabled": False}
    with (args.output / "report.json").open("x") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
