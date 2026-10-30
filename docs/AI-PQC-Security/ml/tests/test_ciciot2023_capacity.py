"""Quality gates and calibration must not turn failed candidates into passes."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'training'))
from compare_ciciot2023_capacity import RECIPES, build, passes
from refine_ciciot2023 import calibrate


@pytest.mark.parametrize('recall,fpr,expected', [
    (.95, .05, True), (.94999, .01, False), (.99, .05001, False),
    (float('nan'), .01, False), (.99, float('nan'), False),
])
def test_both_security_gates_are_required(recall, fpr, expected):
    assert passes({'attack_recall': recall, 'false_positive_rate': fpr}) is expected


def test_calibration_identifies_separable_predictions():
    metric, eligible = calibrate(np.array([0, 0, 1, 1]), np.array([.01, .02, .98, .99]))
    assert eligible
    assert metric['false_positive_rate'] == 0
    assert metric['attack_recall'] == 1


def test_calibration_diagnostic_fallback_is_not_eligible():
    metric, eligible = calibrate(np.array([0, 0, 1, 1]), np.array([.2, .2, .2, .2]))
    assert not eligible
    assert metric['attack_recall'] == 0


def test_calibration_reports_no_false_alarm_safe_threshold():
    metric, eligible = calibrate(np.array([0, 0, 1, 1]), np.array([.99, .99, .99, .99]))
    assert metric is None
    assert not eligible


@pytest.mark.parametrize('name', list(RECIPES))
def test_study_is_bounded_and_reproducible(name):
    model = build(RECIPES[name], 123)
    assert model.get_params()['random_state'] == 123
    assert model.get_params()['n_jobs'] == 4
    assert model.get_params()['n_estimators'] <= 500
