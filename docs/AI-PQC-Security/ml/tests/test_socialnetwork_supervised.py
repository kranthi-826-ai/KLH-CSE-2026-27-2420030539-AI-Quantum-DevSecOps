from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from study_socialnetwork_supervised import RECIPES, build, metrics


@pytest.mark.parametrize("name", RECIPES)
def test_supervised_recipes_have_fixed_small_budgets(name):
    params = build(name).get_params()
    if name != "logistic":
        assert params["n_estimators"] == 128
        assert params["n_jobs"] == 2
        assert params["max_depth"] <= 4


def test_metrics_keep_false_alarms_and_misses_separate():
    result = metrics([0, 0, 1, 1], [0, 1, 1, 0])
    assert result["fn"] == result["fp"] == 1
    assert result["exposure_recall"] == result["control_alarm_fraction"] == .5
