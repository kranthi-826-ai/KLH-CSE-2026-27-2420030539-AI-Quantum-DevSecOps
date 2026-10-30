from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from compare_socialnetwork_development import summarize


def test_case_hits_do_not_hide_window_misses_or_false_alarms():
    rows = [{"case": "a", "label": 1}, {"case": "a", "label": 1},
            {"case": "a", "label": 0}, {"case": "b", "label": 1}, {"case": "b", "label": 0}]
    metrics = summarize(rows, [True, False, True, True, False])
    assert metrics["alerted_cases"] == 2
    assert metrics["exposure_alert_fraction"] == 2 / 3
    assert metrics["control_alarm_fraction"] == .5
