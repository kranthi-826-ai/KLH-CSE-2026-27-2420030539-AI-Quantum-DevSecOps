from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_rich_syscalls import RICH_COLUMNS, rich_aggregate
from socialnetwork_syscalls import aggregate, COLUMNS


def test_richer_features_preserve_base_and_separate_entry_exit():
    lines = ["1000000000 c 1 > NET read res=0", "2000000000 c 1 > FILE openat secret-path",
             "2000000001 c 1 < FILE openat res=3", "2000000002 c 1 > PROC execve secret-argument",
             "3000000000 c 1 > NET read res=0"]
    base, _ = aggregate(lines)
    rich, _ = rich_aggregate(lines)
    features = rich[0]["features"]
    assert {key: features[key] for key in COLUMNS} == base[0]["features"]
    assert tuple(features) == RICH_COLUMNS and len(RICH_COLUMNS) == 269
    assert features["sensitive_entry_openat"] == 1
    assert features["sensitive_entry_execve"] == 1
    assert sum(features[f"thread_transition_{i}"] for i in range(64)) == 1
    assert "secret" not in str(features)


def test_no_transition_crosses_thread_or_window_boundary():
    lines = ["1000000000 c 1 > NET read", "2000000000 c 1 > FILE openat",
             "2000000001 c 2 > PROC execve", "3000000000 c 1 > NET read"]
    rows, _ = rich_aggregate(lines)
    assert sum(rows[0]["features"][f"thread_transition_{i}"] for i in range(64)) == 0
