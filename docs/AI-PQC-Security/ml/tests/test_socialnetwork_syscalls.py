import io
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_syscalls import COLUMNS, aggregate, first_zip_lines


def test_streaming_zip_prefix_cap():
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("events.txt", "one\ntwo\nthree\n")
    assert list(first_zip_lines(io.BytesIO(source.getvalue()), max_lines=2)) == ["one", "two"]


def test_reject_non_zip():
    with pytest.raises(ValueError):
        list(first_zip_lines(io.BytesIO(b"garbage")))


def test_window_boundaries_identifiers_and_outcome_semantics():
    rows, audit = aggregate([
        "1000000000 c1 1 > IPC futex res=-1",
        "2000000000 c1 1 > IPC futex res=-1",
        "2000000001 c1 2 < IPC futex res=-1",
        "3000000000 c1 1 < IPC futex res=0",
        "not a valid line",
    ])
    assert len(rows) == 1 and rows[0]["window"] == 2
    features = rows[0]["features"]
    assert tuple(features) == COLUMNS and len(COLUMNS) == 29
    assert features["negative_exit_fraction"] == 1
    assert features["exit_fraction"] == .5
    assert features["unique_threads"] == 2
    assert sum(features[f"syscall_bin_{i}"] for i in range(16)) == 1
    assert audit["rejected_events"] == 1
    assert not {"container", "thread", "timestamp", "target", "scenario"}.intersection(features)


def test_identity_changes_do_not_change_features():
    lines = [f"{i * 1000000000} service-a 19 < IPC futex res=0" for i in range(4)]
    alternate = [line.replace("service-a", "service-b").replace(" 19 ", " 999 ") for line in lines]
    left, _ = aggregate(lines)
    right, _ = aggregate(alternate)
    assert [r["features"] for r in left] == [r["features"] for r in right]
