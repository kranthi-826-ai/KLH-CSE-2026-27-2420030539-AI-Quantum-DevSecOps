import copy
import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.dummy import DummyClassifier

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML / 'training'))
sys.path.insert(0, str(ML / 'data'))
from microservice_session_features import FEATURE_COLUMNS
from score_gateway_shadow import score


@pytest.fixture
def files(tmp_path):
    model = DummyClassifier(strategy='prior').fit(np.zeros((4, 9)), [0, 0, 1, 1])
    joblib.dump({'model': model, 'feature_columns': FEATURE_COLUMNS, 'threshold': .55}, tmp_path/'candidate.joblib')
    frozen = {'model_sha256': hashlib.sha256((tmp_path/'candidate.joblib').read_bytes()).hexdigest(),
              'feature_columns': FEATURE_COLUMNS, 'automatic_response_enabled': False}
    (tmp_path/'frozen.json').write_text(json.dumps(frozen), encoding='utf-8')
    row = {'schema': 'gateway-peer-shadow-v1', 'shadow_only': True,
           'observation_id': 'one', 'peer_id': 'anonymous', 'features': dict.fromkeys(FEATURE_COLUMNS, 0),
           'outcome': {'status': 401}}
    source = tmp_path/'source.jsonl'
    source.write_text(json.dumps(row)+'\n', encoding='utf-8')
    return source, tmp_path, row


def test_scoring_is_passive_and_does_not_infer_accuracy(files):
    source, study, row = files
    result = score(source, study, study/'first.json')
    assert result['automatic_response_enabled'] is False
    assert result['accuracy_measured'] is False
    assert result['model_promoted'] is False
    assert result['observations'] == 1
    row['outcome']['status'] = 200
    source.write_text(json.dumps(row)+'\n', encoding='utf-8')
    changed = score(source, study, study/'second.json')
    assert result['assessments'] == changed['assessments']


@pytest.mark.parametrize('mutation', ['outcome_feature', 'duplicate', 'wrong_schema', 'nonfinite'])
def test_invalid_observations_rejected(files, mutation):
    source, study, row = files
    rows = [row]
    if mutation == 'outcome_feature': row['features']['status'] = 401
    if mutation == 'duplicate': rows.append(copy.deepcopy(row))
    if mutation == 'wrong_schema': row['schema'] = 'untrusted'
    if mutation == 'nonfinite': row['features']['is_login'] = float('nan')
    source.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
    with pytest.raises(ValueError):
        score(source, study, study/'result.json')
    assert not (study/'result.json').exists()


def test_model_tampering_and_result_overwrite_are_rejected(files):
    source, study, _ = files
    (study/'existing.json').write_text('{}', encoding='utf-8')
    with pytest.raises(FileExistsError): score(source, study, study/'existing.json')
    with (study/'candidate.joblib').open('ab') as stream: stream.write(b'tampered')
    with pytest.raises(ValueError): score(source, study, study/'result.json')
