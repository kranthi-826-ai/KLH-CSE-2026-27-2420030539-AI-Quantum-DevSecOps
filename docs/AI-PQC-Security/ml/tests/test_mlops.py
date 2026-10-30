import json
from pathlib import Path

import pandas as pd
import pytest

from ml.evaluation.detect_drift import drift_report
from ml.mlops.promote_candidate import gate_failures, promote, sha256


def passing_results() -> dict:
    return {
        "validation_winner": "random_forest",
        "selection_metric": "validation_macro_f1",
        "dataset_sha256": {"training": "train-hash", "testing": "test-hash"},
        "models": {
            "random_forest": {
                "test": {
                    "macro_f1": 0.90,
                    "attack_recall": 0.97,
                    "false_positive_rate": 0.18,
                    "roc_auc": 0.99,
                }
            }
        },
    }


def test_promotion_is_hash_verified_and_writes_metadata(tmp_path: Path):
    results = tmp_path / "results.json"
    model = tmp_path / "random_forest.joblib"
    results.write_text(json.dumps(passing_results()), encoding="utf-8")
    model.write_bytes(b"verified-model")

    metadata = promote(results, model, tmp_path / "promoted")

    assert metadata["model_sha256"] == sha256(model)
    assert (tmp_path / "promoted/model.joblib").read_bytes() == b"verified-model"
    assert json.loads((tmp_path / "promoted/metadata.json").read_text())["model_name"] == "random_forest"


def test_failed_quality_gate_blocks_promotion(tmp_path: Path):
    results_data = passing_results()
    results_data["models"]["random_forest"]["test"]["macro_f1"] = 0.50
    results = tmp_path / "results.json"
    model = tmp_path / "random_forest.joblib"
    results.write_text(json.dumps(results_data), encoding="utf-8")
    model.write_bytes(b"model")

    with pytest.raises(ValueError, match="macro_f1"):
        promote(results, model, tmp_path / "promoted")


def test_gate_failures_enforce_false_positive_limit():
    metrics = {
        "macro_f1": 0.90,
        "attack_recall": 0.97,
        "false_positive_rate": 0.21,
        "roc_auc": 0.99,
    }
    assert gate_failures(metrics) == ["false_positive_rate"]


def test_drift_report_detects_shift_and_ignores_stable_feature():
    reference = pd.DataFrame({"rate": range(100), "proto": ["tcp", "udp"] * 50})
    current = pd.DataFrame({"rate": range(1000, 1100), "proto": ["tcp", "udp"] * 50})
    report = drift_report(reference, current)

    assert report["drift_detected"] is True
    assert "rate" in report["drifted_features"]
    assert "proto" not in report["drifted_features"]
