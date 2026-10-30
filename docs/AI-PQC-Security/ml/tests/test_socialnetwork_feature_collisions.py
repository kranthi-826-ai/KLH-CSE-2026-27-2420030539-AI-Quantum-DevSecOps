from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from audit_socialnetwork_feature_collisions import summarize


def test_conflicting_rows_are_counted_without_relabeling_or_removal():
    rows = [{'label':label,'features':{'value':1}} for label in (0,0,1)]
    before = deepcopy(rows)
    result = summarize(rows, ['value'])
    assert result['conflicting_feature_groups'] == 1
    assert result['rows_in_conflicts'] == 3
    assert result['deterministic_minimum_misclassified_rows_on_this_cache'] == 1
    assert rows == before


def test_numeric_equivalence_and_row_order_do_not_change_the_audit():
    rows = [{'label':0,'features':{'value':1}}, {'label':1,'features':{'value':1.0}},
            {'label':0,'features':{'value':2}}]
    assert summarize(rows, ['value']) == summarize(list(reversed(rows)), ['value'])
    assert summarize([rows[0],rows[2]], ['value'])['conflicting_feature_groups'] == 0


def test_invalid_labels_and_nonfinite_vectors_are_rejected():
    with pytest.raises(ValueError):
        summarize([{'label':2,'features':{'value':1}}], ['value'])
    with pytest.raises(ValueError):
        summarize([{'label':0,'features':{'value':float('nan')}}], ['value'])
    for invalid in (None, '', False):
        with pytest.raises(ValueError):
            summarize([{'label':0,'features':{'value':invalid}}], ['value'])
