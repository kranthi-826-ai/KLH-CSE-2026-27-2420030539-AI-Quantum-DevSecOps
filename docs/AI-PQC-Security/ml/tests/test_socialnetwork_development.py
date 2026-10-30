from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from prepare_socialnetwork_development import classify_window


def test_attack_overlap_and_pre_injection_controls_are_disjoint():
    case = {"start_ns": 1700000000500000000, "end_ns": 1700000001600000000}
    assert classify_window(1700000000, case) == 1
    assert classify_window(1700000001, case) == 1
    assert classify_window(1700000002, case) is None
    assert classify_window(1699999980, case) == 0
    assert classify_window(1699999995, case) is None
    assert classify_window(1699999900, case) is None
