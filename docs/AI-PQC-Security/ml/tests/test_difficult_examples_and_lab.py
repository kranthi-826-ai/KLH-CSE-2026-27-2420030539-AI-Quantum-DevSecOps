"""Keep difficult-example mining and local traffic collection bounded."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'training'))
from mine_ciciot2023_difficult import difficult_weights

SPEC = importlib.util.spec_from_file_location('collect_microservice_lab', ROOT / 'data' / 'collect_microservice_lab.py')
LAB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAB)


def test_only_out_of_fold_mistakes_gain_weight():
    original = np.array([2., 3., 2., 3.])
    actual, errors = difficult_weights([0, 1, 0, 1], [.1, .9, .8, .2], original)
    np.testing.assert_array_equal(actual, [2., 3., 4., 6.])
    np.testing.assert_array_equal(errors, [False, False, True, True])
    np.testing.assert_array_equal(original, [2., 3., 2., 3.])


@pytest.mark.parametrize('base', [
    'https://127.0.0.1:8081', 'http://example.com:8081', 'http://localhost:8081',
    'http://192.168.1.2:8081', 'http://127.0.0.1', 'http://127.0.0.1:8081/extra',
    'http://user:password@127.0.0.1:8081', 'http://127.0.0.1:8081?next=foo',
    'http://127.0.0.1:8081#fragment',
])
def test_collector_rejects_nonisolated_or_ambiguous_targets(base):
    with pytest.raises(ValueError):
        LAB.validate_base(base)


def test_local_target_and_redirect_prevention():
    assert LAB.validate_base('http://127.0.0.1:12345/') == 'http://127.0.0.1:12345'
    assert LAB.NoRedirect().redirect_request(None, None, 302, '', {}, 'http://example.com') is None


def test_collector_will_not_overwrite_evidence(tmp_path):
    output = tmp_path / 'evidence.json'
    output.write_text('preserve', encoding='utf-8')
    with pytest.raises(FileExistsError):
        LAB.collect('http://127.0.0.1:12345', output)
    assert output.read_text() == 'preserve'
