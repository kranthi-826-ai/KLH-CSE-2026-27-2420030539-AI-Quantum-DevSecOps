from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_socialnetwork_attacks import epoch_ns, matching_pod, parse_dates


def test_seconds_and_nanoseconds_have_same_epoch():
    assert epoch_ns("1700237693") == epoch_ns("1700237693000000000")
    with pytest.raises(ValueError):
        epoch_ns("1700237693000")


def test_reversed_or_excessive_duration_rejected():
    with pytest.raises(ValueError):
        parse_dates("1700237695;1700237693\npod")
    with pytest.raises(ValueError):
        parse_dates("1700237693;1700237793\npod")


def test_exact_pod_match_not_substring():
    assert matching_pod("k8s_nginx_nginx-ab-12_default_uid_0", "nginx-ab-12")
    assert not matching_pod("k8s_nginx_nginx-ab-123_default_uid_0", "nginx-ab-12")
