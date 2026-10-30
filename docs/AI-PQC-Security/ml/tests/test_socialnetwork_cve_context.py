from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from audit_socialnetwork_cve_context import NS, BASE, observe_line, period, select_cases


def case():
    return {'start_ns':100*NS, 'end_ns':102*NS, 'pod':'target-pod'}


def test_context_periods_do_not_relabel_post_context_as_attack():
    assert period(100*NS, case()) == 'annotated_exposure'
    assert period(103*NS, case()) == 'post_context_not_labeled'
    assert period(89*NS, case()) == 'pre_control_context'
    assert period(95*NS, case()) is None
    assert period(113*NS, case()) is None
    assert period(95*NS, case(), include_onset_gap=True) == 'pre_onset_context_not_labeled'
    assert period(89*NS, case(), include_onset_gap=True) == 'pre_control_context'


def test_target_and_other_containers_remain_distinct_and_raw_arguments_are_absent():
    states = {}
    observe_line(f'{100*NS} k8s_nginx_target-pod_ns_uid 12 < process unshare res=-1(EPERM) path=cgroup secret-payload', case(), states)
    observe_line(f'{100*NS} k8s_other_other-pod_ns_uid 21 > process execve secret-command', case(), states)
    assert {row['target_pod'] for row in states.values()} == {True, False}
    target = next(row for row in states.values() if row['target_pod'])
    assert target['negative_results']['unshare:-1'] == 1
    assert target['argument_marker_events']['cgroup'] == 1
    assert 'secret' not in str(states)


def test_only_two_previous_development_collections_are_eligible():
    cases = [{'id':'CVE-2022-0492', 'base':BASE + f'collection-{collection}',
              'traces':[BASE + f'collection-{collection}/node{node}/sysdig-socialnetwork-events_000.txt.zip' for node in (1,2)]}
             for collection in (1,2)]
    assert select_cases({'cases':cases}) == cases
    cases[0]['base'] = cases[0]['base'].replace('scenario5', 'scenario7')
    with pytest.raises(ValueError):
        select_cases({'cases':cases})


def test_unrecognized_syscall_direction_fails_instead_of_silently_inventing_features():
    with pytest.raises(ValueError):
        observe_line(f'{100*NS} pod 12 ? process execve', case(), {})
