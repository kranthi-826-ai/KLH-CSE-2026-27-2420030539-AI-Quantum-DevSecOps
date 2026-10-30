from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "data" / "validate_ciciot2023.py"
SPEC = importlib.util.spec_from_file_location("validate_ciciot2023", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_validate_file_counts_labels_and_quality_issues(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "flow_duration": [1.0, float("inf"), None],
            "Rate": [2.0, 3.0, 4.0],
            "label": ["BenignTraffic", "DDoS-UDP_Flood", "BenignTraffic"],
        }
    ).to_csv(source, index=False)

    result = MODULE.validate_file(source, chunk_size=2, include_hash=True)

    assert result["rows"] == 3
    assert result["label_counts"] == {"BenignTraffic": 2, "DDoS-UDP_Flood": 1}
    assert result["missing_by_column"] == {"flow_duration": 1}
    assert result["non_finite_by_column"] == {"flow_duration": 1}
    assert len(result["sha256"]) == 64


def test_validate_file_requires_label_column(tmp_path: Path) -> None:
    source = tmp_path / "missing-label.csv"
    pd.DataFrame({"flow_duration": [1.0]}).to_csv(source, index=False)

    with pytest.raises(ValueError, match="Unrecognized unlabeled filename"):
        MODULE.validate_file(source, chunk_size=2, include_hash=False)


def test_per_attack_release_derives_label_without_using_it_as_feature(tmp_path: Path) -> None:
    source = tmp_path / "DDoS-UDP_Flood12.pcap.csv"
    pd.DataFrame({"Rate": [1.0, 2.0]}).to_csv(source, index=False)
    result = MODULE.validate_file(source, chunk_size=1, include_hash=True)
    assert result["label_counts"] == {"DDoS-UDP_Flood": 2}
    assert result["label_source"] == "verified filename taxonomy"


def test_unrecognized_attack_filename_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "NewUnknownAttack.pcap.csv"
    pd.DataFrame({"Rate": [1.0]}).to_csv(source, index=False)
    with pytest.raises(ValueError, match="Unknown attack label"):
        MODULE.validate_file(source, chunk_size=2, include_hash=False)
