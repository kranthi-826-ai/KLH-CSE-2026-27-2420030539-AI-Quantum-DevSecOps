import io
from pathlib import Path
import sys
import zipfile
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from inspect_socialnetwork_archives import BudgetExceeded, LimitedReader, inspect


def test_reader_caps_decompressed_bytes():
    reader = LimitedReader(io.BytesIO(b"abcdef"), 3)
    assert reader.read(100) == b"abc"
    with pytest.raises(BudgetExceeded):
        reader.read(1)


def test_attack_archive_is_inventory_only(tmp_path):
    path = tmp_path / "SocialNetwork-attack-data.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("not-a-real.tar.gz", b"not compressed")
    assert inspect(path)["members"][0]["bytes"] == 14
    with pytest.raises(ValueError, match="restricted"):
        inspect(path, probe=True)


def test_nested_trace_prefix_without_extraction(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("events.txt", "123 container 5 > IPC futex res=0\n" * 10)
    tar_data = io.BytesIO()
    with tarfile.open(fileobj=tar_data, mode="w:gz") as archive:
        header = tarfile.TarInfo("scenario/plain_workload/events.txt.zip")
        header.size = len(inner.getvalue())
        archive.addfile(header, io.BytesIO(inner.getvalue()))
    path = tmp_path / "SocialNetwork-validation-data.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("scenario.tar.gz", tar_data.getvalue())
    result = inspect(path, probe=True)
    assert len(result["probe"]["samples"][0]["lines"]) == 8
    assert result["probe"]["bounded"]
    assert list(tmp_path.iterdir()) == [path]
