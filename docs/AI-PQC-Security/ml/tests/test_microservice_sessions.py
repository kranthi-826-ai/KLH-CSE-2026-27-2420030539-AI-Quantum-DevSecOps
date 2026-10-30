"""Verify causal features, whole-session isolation and frozen evaluation guards."""
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML / 'data'))
sys.path.insert(0, str(ML / 'training'))
from microservice_session_features import FEATURE_COLUMNS, RequestHistory
from train_microservice_sessions import load_split, validate_manifest, choose_threshold
from evaluate_microservice_sessions import cluster_intervals, main as final_evaluate


def test_current_response_cannot_change_existing_feature_snapshot():
    history = RequestHistory()
    snapshot = history.before_request(1., '/api/v1/auth/login', False)
    original = dict(snapshot)
    assert snapshot['prior_401_5s'] == 0
    history.after_response(1.01, 1.2, '/api/v1/auth/login', 401)
    assert snapshot == original
    following = history.before_request(1.3, '/api/v1/auth/me', True)
    assert following['prior_401_5s'] == 1
    assert following['prior_failed_login_5s'] == 1
    assert following['prior_requests_1s'] == 1
    assert set(following) == set(FEATURE_COLUMNS)
    assert not {'status', 'target', 'scenario', 'duration_ms'}.intersection(following)


def test_later_response_is_not_usable_and_expired_events_are_evicted():
    history = RequestHistory()
    history.after_response(1., 3., '/api/v1/auth/login', 401)
    assert history.before_request(2., '/api/v1/auth/me', True)['prior_401_5s'] == 0
    assert history.before_request(9., '/api/v1/auth/me', True)['prior_401_5s'] == 0
    assert len(history.events) == 0


def test_session_histories_are_isolated():
    one, two = RequestHistory(), RequestHistory()
    one.after_response(1., 1.1, '/api/v1/auth/login', 401)
    assert one.before_request(2., '/api/v1/auth/me', True)['prior_401_5s'] == 1
    assert two.before_request(2., '/api/v1/auth/me', True)['prior_401_5s'] == 0


@pytest.mark.parametrize('clock', [float('nan'), float('inf'), .1])
def test_bad_or_reversed_clock_rejected(clock):
    history = RequestHistory()
    history.after_response(1., 1.1, '/api/v1/auth/login', 401)
    with pytest.raises(ValueError):
        history.before_request(clock, '/api/v1/auth/me', False)


def test_response_clock_rejected():
    with pytest.raises(ValueError):
        RequestHistory().after_response(2., 1., '/api/v1/auth/login', 401)


def manifest():
    return {'status': 'complete', 'feature_columns': list(FEATURE_COLUMNS),
            'splits': {s: {'sessions': [{'session_id': s}]} for s in ('train', 'calibration', 'test')}}


def test_shared_session_across_partitions_is_rejected():
    valid = manifest()
    validate_manifest(valid)
    invalid = copy.deepcopy(valid)
    invalid['splits']['test']['sessions'][0]['session_id'] = 'train'
    with pytest.raises(ValueError, match='overlap'):
        validate_manifest(invalid)


def test_data_loader_rejects_outcome_as_a_feature(tmp_path):
    row = {'session_id': 'one', 'sequence': 0, 'scenario': 'normal_use', 'target': 0,
           'features': dict.fromkeys(FEATURE_COLUMNS, 0)}
    row['features']['status'] = 401
    path = tmp_path / 'train.json'
    path.write_text(json.dumps([row]), encoding='utf-8')
    info = {'rows': 1, 'sessions': [{'session_id': 'one', 'scenario': 'normal_use', 'requests': 1}],
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match='predictor'):
        load_split(tmp_path, {'splits': {'train': info}, 'label_mapping': {'normal_use': 0}}, 'train')


def test_threshold_failure_is_not_an_approval():
    _, eligible = choose_threshold(np.array([0, 0, 1, 1]), np.array([.5, .5, .5, .5]))
    assert not eligible


def test_final_evaluation_cannot_be_run_twice(tmp_path):
    (tmp_path / 'test-evaluation-started.json').write_text('{}', encoding='utf-8')
    with pytest.raises(FileExistsError):
        final_evaluate(tmp_path / 'nonexistent', tmp_path)


def test_cluster_bootstrap_is_deterministic_and_resamples_sessions():
    y = np.array([0, 0, 1, 1, 0, 1])
    prediction = np.array([0, 1, 1, 1, 0, 0])
    groups = np.array(['a', 'a', 'b', 'b', 'c', 'd'])
    result = cluster_intervals(y, prediction, groups)
    assert result == cluster_intervals(y, prediction, groups)
    assert 0 <= result['false_positive_rate']['lower'] <= result['false_positive_rate']['upper'] <= 1
    assert 0 < result['accuracy']['valid_replicates'] <= 500
