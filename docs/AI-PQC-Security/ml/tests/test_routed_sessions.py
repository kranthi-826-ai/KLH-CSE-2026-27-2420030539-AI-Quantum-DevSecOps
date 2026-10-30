import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML/'data'))
sys.path.insert(0, str(ML/'training'))
from prepare_routed_sessions import prepare
from microservice_session_features import FEATURE_COLUMNS
from study_routed_sessions import validate_peers, evaluate
from refine_routed_operating_point import estimator, RECIPES


def fixture(source, mutation=None):
    raw = source/'raw'
    raw.mkdir(parents=True)
    manifest = {'status': 'complete', 'peer_split': 'explicit held-out peers',
        'feature_columns': FEATURE_COLUMNS, 'splits': {}, 'label_mapping': {'normal_use': 0, 'credential_guessing': 1}}
    observations, number = [], 0
    for split, size in (('train',3),('calibration',2),('test',2)):
        rows, sessions = [], []
        for i in range(size):
            peer = f'peer-{number}'
            if mutation == 'overlap' and split == 'test' and i == 0: peer = 'peer-0'
            scenario = 'normal_use' if i%2 == 0 else 'credential_guessing'
            obs_id = f'obs-{number}'
            session = f'session-{number}'
            observed = {'schema': 'gateway-peer-shadow-v1', 'shadow_only': True,
                'observation_id': obs_id, 'peer_id': peer, 'features': dict.fromkeys(FEATURE_COLUMNS, 0),
                'outcome': {'status': 200}}
            if mutation == 'outcome' and number == 0: observed['outcome']['status'] = 401
            observations.append(observed)
            rows.append({'session_id': session, 'sequence': 0, 'scenario': scenario,
                'target': manifest['label_mapping'][scenario], 'features': dict.fromkeys(FEATURE_COLUMNS, 999),
                'gateway_observation_id': 'missing' if mutation=='missing' and number==0 else obs_id,
                'outcome': {'status': 200}})
            sessions.append({'session_id': session, 'scenario': scenario, 'requests': 1})
            number += 1
        path = raw/f'{split}.json'
        path.write_text(json.dumps(rows), encoding='utf-8')
        manifest['splits'][split] = {'rows': len(rows), 'sessions': sessions,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (raw/'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (source/'gateway.jsonl').write_text('\n'.join(json.dumps(r) for r in observations), encoding='utf-8')


def test_server_features_replace_provisional_client_features(tmp_path):
    source, output = tmp_path/'source', tmp_path/'prepared'
    fixture(source)
    prepare(source, output)
    manifest = json.loads((output/'manifest.json').read_text())
    validate_peers(manifest)
    assert manifest['unique_transport_peers'] == 7
    assert manifest['joined_study_observations'] == 7
    rows = json.loads((output/'train.json').read_text())
    assert set(rows[0]['features'].values()) == {0}
    assert 'gateway_observation_id' not in rows[0]
    with pytest.raises(FileExistsError): prepare(source, output)


@pytest.mark.parametrize('mutation', ['overlap','outcome','missing'])
def test_bad_identity_and_label_joins_are_rejected(tmp_path, mutation):
    fixture(tmp_path/'source', mutation)
    with pytest.raises(ValueError): prepare(tmp_path/'source', tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_peer_holdout_must_be_independent(tmp_path):
    fixture(tmp_path/'source')
    prepare(tmp_path/'source', tmp_path/'out')
    manifest = json.loads((tmp_path/'out/manifest.json').read_text())
    bad = copy.deepcopy(manifest)
    bad['splits']['test']['peer_ids'][0] = manifest['splits']['train']['peer_ids'][0]
    with pytest.raises(ValueError): validate_peers(bad)


def test_final_test_cannot_be_repeated(tmp_path):
    (tmp_path/'test-started.json').write_text('{}')
    with pytest.raises(FileExistsError): evaluate(tmp_path, tmp_path, tmp_path)


@pytest.mark.parametrize('name', ['xgb_depth3','xgb_depth5'])
def test_followup_study_is_bounded_and_deterministic(name):
    params = estimator(name).get_params()
    assert len(RECIPES) == 4
    assert params['n_jobs'] == 4
    assert params['n_estimators'] == 160
    assert params['random_state'] == 20261019
