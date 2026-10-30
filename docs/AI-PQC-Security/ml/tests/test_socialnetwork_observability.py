from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from audit_socialnetwork_observability import summarize


def fixture():
    case = {"id": "test", "base": "recording", "start_ns": 1_500_000_000,
            "end_ns": 2_100_000_000, "traces": ["trace"]}
    features = dict(events=2, sensitive_entry_execve=0, sensitive_entry_execveat=0,
                    prior5_execve=0, prior5_execveat=0)
    rows = [{"trace": "trace", "window": w, "container_group": "pod", "case": "test",
             "label": label, "features": features} for w, label in [(0, 0), (1, 1), (2, 1)]]
    return rows, [case]


def test_window_and_recording_metrics_stay_distinct():
    rows, cases = fixture()
    result = summarize(rows, [1, 0, 1], cases)
    record = result["recordings"][0]
    assert result["exposure_hits"] == 1 and result["exposure_windows"] == 2
    assert result["recordings_with_any_exposure_alert"] == 1
    assert result["control_alarms"] == 1
    assert record["first_alert_window_close_delay_millis"] == 1500
    assert record["missed_windows"][0]["overlap_millis"] == 500


def test_missing_detection_is_not_zero_delay():
    rows, cases = fixture()
    assert summarize(rows, [0, 0, 0], cases)["recordings"][0]["first_alert_window_close_delay_millis"] is None


def test_alignment_duplicate_and_label_errors_fail():
    rows, cases = fixture()
    with pytest.raises(ValueError):
        summarize(rows, [1], cases)
    with pytest.raises(ValueError, match="Duplicate observation"):
        summarize(rows + [rows[0]], [0] * 4, cases)
    rows[1]["label"] = 0
    with pytest.raises(ValueError, match="Exposure label"):
        summarize(rows, [0] * 3, cases)
