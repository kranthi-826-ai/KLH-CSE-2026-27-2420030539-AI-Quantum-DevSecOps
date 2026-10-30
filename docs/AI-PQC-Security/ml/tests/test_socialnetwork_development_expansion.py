from pathlib import Path
import sys

import pytest
import numpy as np
from sklearn.model_selection import LeaveOneGroupOut

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from expand_socialnetwork_development import additional_cases


def metadata():
    record = {"archive": "SocialNetwork-attack-data/scenario5.tar.gz", "headers": [], "small_text": []}
    for index in range(8):
        base = f"scenario5/plain_workload/CVE-{index}/collection-2"
        dates = "1700000000;1700000002\npod-test\n"
        record["small_text"].extend([
            {"name": base + "/dates.txt", "text": dates},
            {"name": base + "/30min_attack_experiment.txt", "text": "CMDs: 0\n" + dates}])
        record["headers"].extend({"name": base + f"/node{node}/sysdig-events_000.txt.zip"} for node in (1, 2))
    return {"attack_metadata": [record]}


def test_selection_is_only_predeclared_second_collection():
    cases = additional_cases(metadata())
    assert len(cases) == 8
    assert all("scenario5/plain_workload/" in c["base"] and c["base"].endswith("collection-2") for c in cases)
    assert all(len(c["traces"]) == 2 for c in cases)


def test_enriched_workload_cannot_silently_become_normal_control():
    data = metadata()
    data["attack_metadata"][0]["small_text"][1]["text"] = "CMDs: 1\n1700000000;1700000002\npod-test\n"
    with pytest.raises(ValueError, match="enriched"):
        additional_cases(data)


def test_both_recordings_of_cve_stay_on_same_fold_side():
    groups = np.asarray([f"CVE-{index}" for index in range(8) for _ in range(2)])
    for train, validation in LeaveOneGroupOut().split(np.zeros((16, 1)), groups=groups):
        assert len(validation) == 2
        assert not set(groups[train]) & set(groups[validation])
