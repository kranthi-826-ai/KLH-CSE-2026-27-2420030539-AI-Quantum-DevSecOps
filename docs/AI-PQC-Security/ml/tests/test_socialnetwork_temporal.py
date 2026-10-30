from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_temporal import add_history, TEMPORAL_COLUMNS
from socialnetwork_rich_syscalls import RICH_COLUMNS


def row(window, group="a", recording="one", calls=0):
    features = {key: 0 for key in RICH_COLUMNS}
    features.update({"events": 10, "sensitive_entry_execve": calls})
    return {"window": window, "container_group": group, "recording": recording, "features": features}


def test_future_prefix_invariance_and_current_window_exclusion():
    prefix = [row(10, calls=2), row(11, calls=4)]
    before = add_history(prefix, 0)
    after = add_history(prefix + [row(12, calls=999)], 0)
    assert before == after[:2]
    assert before[1]["features"]["prior5_execve"] == 2
    assert tuple(before[1]["features"]) == TEMPORAL_COLUMNS


def test_container_and_recording_isolation():
    rows = [row(10, calls=5), row(11, group="b"), row(11, recording="two")]
    assert all(r["features"]["prior5_execve"] == 0 for r in add_history(rows, 0))


def test_verified_zero_activity_gap_and_warmup():
    out = add_history([row(10, calls=5), row(16)], 10)
    assert not out[0]["history_complete"] and out[1]["history_complete"]
    assert out[1]["features"]["prior5_execve"] == 0
    assert out[1]["features"]["prior5_observed_windows"] == 0


def test_model_comparison_preserves_reference_row_order():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
    from study_socialnetwork_temporal import canonical_rows
    reference = [{"trace": "x", "window": i, "container_group": "a"} for i in range(3)]
    assert canonical_rows(list(reversed(reference)), reference) == reference


def test_execution_guard_is_explicit_and_does_not_use_labels():
    from study_frontend_execution_guard import guard
    features = {key: 0 for key in TEMPORAL_COLUMNS}
    assert not guard(features)
    features["prior5_execve"] = 1
    assert guard(features)
