from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from socialnetwork_paths import SOCIALNETWORK_RAW, ARCHIVES, source_directory


def test_default_location_is_project_local_not_downloads():
    assert SOCIALNETWORK_RAW.parts[-3:] == ("raw", "microservice-ids-2024", "socialnetwork")
    assert "Downloads" not in SOCIALNETWORK_RAW.parts
    assert SOCIALNETWORK_RAW.parent.name == "microservice-ids-2024"


def test_missing_files_fail_without_creating_placeholder_data(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing verified"):
        source_directory(tmp_path)
    assert list(tmp_path.iterdir()) == []
