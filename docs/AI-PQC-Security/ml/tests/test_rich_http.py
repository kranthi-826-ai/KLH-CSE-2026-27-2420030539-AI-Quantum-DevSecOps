import sys
from pathlib import Path
import pytest

ML=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ML/'data')); sys.path.insert(0,str(ML/'training'))
from rich_http_features import RICH_COLUMNS
from microservice_session_features import FEATURE_COLUMNS
from collect_microservice_sessions import corrupt_token
from study_rich_http import evaluate, build, NAMES


def test_rich_schema_is_versioned_and_excludes_secrets_and_outcomes():
    assert len(RICH_COLUMNS)==24 and len(set(RICH_COLUMNS))==24
    assert tuple(RICH_COLUMNS[:9])==FEATURE_COLUMNS
    assert not {'token','token_hash','context_key','target','scenario','status','duration_ms','peer_id'}.intersection(RICH_COLUMNS)


def test_same_format_token_corruption_is_not_a_fixed_short_marker():
    token='header.payload.AABCDEFGHIJKLMNOPQRSTUV'
    corrupted=[corrupt_token(token,i) for i in range(20)]
    assert all(len(t)==len(token) and len(t.split('.'))==3 and t!=token for t in corrupted)
    assert len(set(corrupted))==20
    assert all(t.split('.')[:2]==token.split('.')[:2] for t in corrupted)


def test_fresh_test_cannot_be_repeated(tmp_path):
    (tmp_path/'test-started.json').write_text('{}')
    with pytest.raises(FileExistsError): evaluate(tmp_path,tmp_path,tmp_path)


@pytest.mark.parametrize('name',NAMES)
def test_search_is_small_and_tree_threads_bounded(name):
    params=build(name).get_params()
    if name!='logistic':
        assert params['n_jobs']==4
        assert params['n_estimators']<=240
