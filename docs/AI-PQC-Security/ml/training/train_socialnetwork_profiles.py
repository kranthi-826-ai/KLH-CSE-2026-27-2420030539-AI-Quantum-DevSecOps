"""Service-role-conditioned normal references; no attack fitting or threshold search."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from train_socialnetwork_reference import sha, SEED
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS


def role_matrix(rows):
    return np.asarray([[row["features"][key] for key in COLUMNS] for row in rows], dtype=float)


def measure(rows, profiles, thresholds):
    flags = [None] * len(rows)
    for role in profiles:
        indexes = [i for i, row in enumerate(rows) if row["service_role"] == role]
        if not indexes:
            continue
        scores = -profiles[role].score_samples(role_matrix([rows[i] for i in indexes]))
        for index, score in zip(indexes, scores):
            flags[index] = bool(score >= thresholds[role])
    scored = sum(flag is not None for flag in flags)
    return flags, {"rows": len(rows), "scored": scored, "abstained": len(rows) - scored,
                   "alarms": sum(flag is True for flag in flags),
                   "alarm_fraction_scored": sum(flag is True for flag in flags) / scored if scored else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    sets = {}
    for name, digest in manifest["files_sha256"].items():
        path = args.data / f"{name}.json"
        if sha(path) != digest:
            raise ValueError("Role-mapped data changed")
        sets[name] = json.loads(path.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "socialnetwork-role-profiles-v1", "minimum_training_rows": 100,
            "minimum_calibration_rows": 30, "threshold_rule": "next float above role calibration95th percentile",
            "missing_profile": "abstain, never count as benign", "recipe": {"n_estimators": 128,
            "max_samples": 256, "n_jobs": 1, "contamination": "auto", "random_state": SEED},
            "features": list(COLUMNS), "role_is_routing_metadata_not_identity_or_label": True,
            "data_manifest_sha256": sha(args.data / "manifest.json"), "script_sha256": sha(Path(__file__)),
            "promotion_allowed": False, "development_gates": {"exposure_min": .95, "control_alarm_max": .05,
            "normal_alarm_max": .05, "normal_coverage_min": .95, "all_development_cases_alerted": True}}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    profiles, thresholds, supports = {}, {}, {}
    for role in sorted({row["service_role"] for row in sets["training"]}):
        train = [row for row in sets["training"] if row["service_role"] == role]
        cal = [row for row in sets["calibration"] if row["service_role"] == role]
        supports[role] = {"train": len(train), "calibration": len(cal), "eligible": len(train) >= 100 and len(cal) >= 30}
        if not supports[role]["eligible"]:
            continue
        model = IsolationForest(**plan["recipe"]).fit(role_matrix(train))
        scores = -model.score_samples(role_matrix(cal))
        thresholds[role] = float(np.nextafter(np.quantile(scores, .95, method="higher"), np.inf))
        profiles[role] = model
    joblib.dump({"profiles": profiles, "thresholds": thresholds, "features": COLUMNS}, args.output / "profiles.joblib")
    results = {}
    for name in ("calibration", "normal_check", "development"):
        flags, metrics = measure(sets[name], profiles, thresholds)
        if name == "development":
            rows = sets[name]
            positives = [i for i, row in enumerate(rows) if row["label"] == 1]
            negatives = [i for i, row in enumerate(rows) if row["label"] == 0]
            cases = sorted({row["case"] for row in rows})
            metrics.update({"exposure_windows": len(positives), "exposure_alerts": sum(flags[i] is True for i in positives),
                            "control_windows": len(negatives), "control_alarms": sum(flags[i] is True for i in negatives),
                            "cases": len(cases), "case_alerts": sum(any(flags[i] is True for i in positives if rows[i]["case"] == case) for case in cases)})
        results[name] = metrics
    dev, normal = results["development"], results["normal_check"]
    eligible = bool(dev["abstained"] == 0 and dev["exposure_alerts"] / dev["exposure_windows"] >= .95
        and dev["control_alarms"] / dev["control_windows"] <= .05 and dev["case_alerts"] == dev["cases"]
        and normal["scored"] / normal["rows"] >= .95 and normal["alarm_fraction_scored"] <= .05)
    report = {"schema": plan["schema"], "results": results, "supports": supports, "thresholds": thresholds,
              "passes_development_gates": eligible, "promoted": False, "enforcement_enabled": False,
              "independent_evaluation_required": True, "plan_sha256": sha(args.output / "plan.json"),
              "model_sha256": sha(args.output / "profiles.joblib"), "attack_accuracy": None}
    with (args.output / "report.json").open("x") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
