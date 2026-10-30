"""Posthoc development-label audit; never retrains, relabels or opens raw attacks."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from study_socialnetwork_temporal import canonical_rows
from train_socialnetwork_reference import sha

NS = 1_000_000_000


def summarize(rows, predictions, cases):
    if len(rows) != len(predictions) or any(p not in (0, 1) for p in predictions):
        raise ValueError("Predictions must be aligned binary decisions")
    lookup = {}
    for case in cases:
        if case["end_ns"] <= case["start_ns"]:
            raise ValueError("Invalid annotation interval")
        for trace in case["traces"]:
            if trace in lookup:
                raise ValueError("Duplicate trace annotation")
            lookup[trace] = case
    seen, grouped = set(), defaultdict(list)
    for row, prediction in zip(rows, predictions):
        key = (row["trace"], row["window"], row["container_group"])
        if key in seen:
            raise ValueError("Duplicate observation")
        seen.add(key)
        case = lookup[row["trace"]]
        if row["case"] != case["id"] or row["label"] not in (0, 1):
            raise ValueError("Annotation identity or label mismatch")
        overlap = max(0, min((row["window"] + 1) * NS, case["end_ns"]) - max(row["window"] * NS, case["start_ns"]))
        if bool(overlap) != bool(row["label"]):
            raise ValueError("Exposure label does not match annotation overlap")
        grouped[case["base"]].append((row, prediction, overlap))
    records = []
    for case in cases:
        entries = grouped[case["base"]]
        positive = [(r, p, overlap) for r, p, overlap in entries if r["label"]]
        controls = [(r, p, overlap) for r, p, overlap in entries if not r["label"]]
        hits = [r for r, p, _ in positive if p]
        missed = [{"window": r["window"], "overlap_millis": overlap / 1_000_000,
                   "events": r["features"]["events"],
                   "current_exec_count": sum(r["features"][k] for k in ("sensitive_entry_execve", "sensitive_entry_execveat")),
                   "prior5_exec_count": sum(r["features"][k] for k in ("prior5_execve", "prior5_execveat"))}
                  for r, p, overlap in positive if not p]
        records.append({"recording": case["base"], "cve": case["id"],
                        "annotation_duration_millis": (case["end_ns"] - case["start_ns"]) / 1_000_000,
                        "exposure_windows": len(positive), "exposure_hits": len(hits),
                        "control_windows": len(controls), "control_alarms": sum(p for _, p, _ in controls),
                        "has_observed_exposure": bool(positive), "any_exposure_alert": bool(hits),
                        # Detection is possible only after a full feature window closes.
                        "first_alert_window_close_delay_millis": min(((r["window"] + 1) * NS - case["start_ns"]) / 1_000_000 for r in hits) if hits else None,
                        "missed_windows": missed})
    observed = [r for r in records if r["has_observed_exposure"]]
    return {"recordings": records, "observed_recordings": len(observed),
            "recordings_with_any_exposure_alert": sum(r["any_exposure_alert"] for r in observed),
            "exposure_windows": sum(r["exposure_windows"] for r in records),
            "exposure_hits": sum(r["exposure_hits"] for r in records),
            "control_windows": sum(r["control_windows"] for r in records),
            "control_alarms": sum(r["control_alarms"] for r in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("original_order", type=Path)
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text())
    plan_path = args.study.parent / "plan.json"
    plan = json.loads(plan_path.read_text())
    study = json.loads(args.study.read_text())
    checks = ((args.data / "windows.json", manifest["windows_sha256"]),
              (args.data / "manifest.json", plan["manifest_sha256"]),
              (args.original_order, plan["row_order_sha256"]),
              (plan_path, study["plan_sha256"]))
    if any(sha(path) != expected for path, expected in checks):
        raise ValueError("Frozen evidence changed")
    rows = canonical_rows(json.loads((args.data / "windows.json").read_text()), json.loads(args.original_order.read_text()))
    result = summarize(rows, study["results"]["base_logistic"]["window_predictions"], manifest["cases"])
    report = {"schema": "socialnetwork-observability-audit-v1", "posthoc_development_only": True,
              "prediction_source": "unchanged base_logistic grouped out-of-fold predictions",
              "raw_archives_opened": False, "labels_changed": False, "promoted": False,
              "case_metric_replaces_failed_window_gate": False,
              "delay_is_window_close_not_online_runtime_measurement": True,
              "limitations": ["Exposure does not certify exploit success or malicious activity in every window.",
                              "Selected matched controls do not estimate deployment-wide false positives.",
                              "Related windows/recordings are not independent trials.",
                              "Any-alert recording summaries are posthoc diagnostics, not new accuracy claims."],
              "input_sha256": {str(path): sha(path) for path, _ in checks},
              "study_sha256": sha(args.study), "script_sha256": sha(Path(__file__)), **result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "recordings"}, indent=2))


if __name__ == "__main__":
    main()
