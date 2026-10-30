from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from train_socialnetwork_profiles import measure


def test_missing_role_is_an_abstention_not_a_benign_prediction():
    flags, metrics = measure([{"service_role": "unseen-role", "features": {}}], {}, {})
    assert flags == [None]
    assert metrics["abstained"] == 1
    assert metrics["scored"] == 0
    assert metrics["alarm_fraction_scored"] is None
