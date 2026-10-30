"""Compare fixed references on replay-verified, already exposed development cases."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np

from train_socialnetwork_reference import sha
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS


def summarize(rows, predictions):
    positive = [(r, bool(p)) for r, p in zip(rows, predictions) if r["label"] == 1]
    negative = [(r, bool(p)) for r, p in zip(rows, predictions) if r["label"] == 0]
    cases = sorted({r["case"] for r in rows})
    hits = sum(any(p for r, p in positive if r["case"] == case) for case in cases)
    return {"exposure_windows": len(positive), "exposure_alerts": sum(p for _, p in positive),
            "exposure_alert_fraction": sum(p for _, p in positive) / len(positive),
            "control_windows": len(negative), "control_alarms": sum(p for _, p in negative),
            "control_alarm_fraction": sum(p for _, p in negative) / len(negative),
            "cases": len(cases), "alerted_cases": hits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("expanded", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Development comparison already exists")
    manifest = json.loads((args.data / "manifest.json").read_text())
    if not manifest["baseline_replay_verified"] or sha(args.data / "windows.json") != manifest["windows_sha256"]:
        raise ValueError("Development cache invalid")
    rows = json.loads((args.data / "windows.json").read_text())
    x = np.asarray([[row["features"][key] for key in COLUMNS] for row in rows])
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {"data_manifest_sha256": sha(args.data / "manifest.json"), "script_sha256": sha(Path(__file__)),
            "not_final_test": True, "promotion_allowed": False,
            "gates": {"exposure_alert_fraction_min": .95, "control_alarm_fraction_max": .05,
                      "normal_check_alarm_fraction_max": .05, "all_cases_alerted": True}}
    with (args.output / "plan.json").open("x") as handle:
        json.dump(plan, handle, indent=2)
    results = {}
    for name, path in (("baseline", args.baseline), ("expanded", args.expanded)):
        report = json.loads((path / "report.json").read_text())
        if sha(path / "reference.joblib") != report["model_sha256"] or report["features_sha256"] != manifest["feature_sha256"]:
            raise ValueError("Frozen model or features changed")
        model = joblib.load(path / "reference.joblib")
        predictions = -model.score_samples(x) >= report["threshold"]
        metrics = summarize(rows, predictions)
        metrics["normal_check"] = report["normal_results"]["check_normal"]
        metrics["passes_development_gates"] = bool(metrics["exposure_alert_fraction"] >= .95
            and metrics["control_alarm_fraction"] <= .05
            and metrics["normal_check"]["observed_alarm_fraction"] <= .05
            and metrics["alerted_cases"] == metrics["cases"])
        results[name] = {"metrics": metrics, "model_sha256": report["model_sha256"],
                         "report_sha256": sha(path / "report.json"), "threshold": report["threshold"]}
    result = {"schema": "socialnetwork-reference-expansion-comparison-v1", "results": results,
              "plan_sha256": sha(args.output / "plan.json"), "selected_candidate": None,
              "enforcement_enabled": False, "attack_accuracy": None}
    with (args.output / "result.json").open("x") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
