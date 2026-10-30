from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from socialnetwork_error_features import reported_error, aggregate_errors, COLUMNS_WITH_ERRORS


def test_only_leading_return_fields_are_used_not_payload_strings():
    assert reported_error('res=-11(EAGAIN) extra=value') == 11
    assert reported_error('fd=-2(ENOENT) name=x') == 2
    assert reported_error('res=0 payload=res=-1') is None
    assert reported_error('args=res=-1') is None
    assert reported_error('res=-0') is None
    assert reported_error('') is None


def test_error_features_keep_base_features_and_do_not_use_future_windows():
    lines = ['0 pod 1 > io read', '1000000000 pod 1 < io read res=-11(EAGAIN)',
             '1100000000 pod 1 < io open fd=-2(ENOENT)', '1200000000 pod 1 < io read res=0',
             '2000000000 pod 1 > io read']
    rows, _ = aggregate_errors(lines)
    assert len(rows) == 1
    features = rows[0]['features']
    assert tuple(features) == COLUMNS_WITH_ERRORS
    assert features['events'] == 3
    assert features['reported_error_count'] == 2
    assert features['reported_error_exit_fraction'] == 2/3
    assert features['reported_errno_11'] == .5
    future, _ = aggregate_errors(lines + ['3000000000 other 99 < io read res=-13'])
    assert future[0] == rows[0]


def test_container_identity_is_metadata_not_an_error_feature():
    lines = ['0 pod 1 > io read', '1000000000 pod 1 < io read res=-11',
             '1000000000 other 9 < io read res=0', '2000000000 pod 1 > io read']
    rows, _ = aggregate_errors(lines)
    assert {row['features']['reported_error_count'] for row in rows} == {0, 1}
    assert all('pod' not in row['features'] and 'label' not in row['features'] for row in rows)
