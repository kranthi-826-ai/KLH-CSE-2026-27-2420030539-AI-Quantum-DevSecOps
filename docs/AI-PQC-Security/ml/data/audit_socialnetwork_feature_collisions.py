"""Read-only feature/label ambiguity audit; never remove or majority-relabel rows."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

from socialnetwork_syscalls import COLUMNS
from socialnetwork_error_features import COLUMNS_WITH_ERRORS


def summarize(rows, columns):
    groups = defaultdict(list)
    for row in rows:
        if type(row['label']) is not int or row['label'] not in (0, 1):
            raise ValueError('Expected binary integer labels')
        raw_values = [row['features'][key] for key in columns]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in raw_values):
            raise ValueError('Missing or nonnumeric features must not be interpreted as zero')
        values = tuple(float(value) if value else 0.0 for value in raw_values)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite features cannot support a collision comparison')
        groups[values].append(row['label'])
    conflicts = []
    for values, labels in groups.items():
        positive = sum(labels)
        negative = len(labels) - positive
        if positive and negative:
            fingerprint = hashlib.sha256(json.dumps(values, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            conflicts.append({'feature_vector_sha256':fingerprint,'positive_rows':positive,'negative_rows':negative})
    return {'conflicting_feature_groups':len(conflicts), 'rows_in_conflicts':sum(x['positive_rows']+x['negative_rows'] for x in conflicts),
            'positive_rows_in_conflicts':sum(x['positive_rows'] for x in conflicts),
            'deterministic_minimum_misclassified_rows_on_this_cache':sum(min(x['positive_rows'],x['negative_rows']) for x in conflicts),
            'conflicts':sorted(conflicts, key=lambda x:x['feature_vector_sha256'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / 'manifest.json').read_text())
    raw = (args.data / 'windows.json').read_bytes()
    data_hash = hashlib.sha256(raw).hexdigest()
    if data_hash != manifest['windows_sha256']:
        raise ValueError('Frozen data changed')
    rows = json.loads(raw)
    report = {'schema':'socialnetwork-feature-collision-audit-v1','data_sha256':data_hash,
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'not_a_generalization_score':True,'rows_removed':0,'labels_changed':False,
              'results':{name:summarize(rows, columns) for name,columns in (('base',COLUMNS),('errors',COLUMNS_WITH_ERRORS))}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({name:{k:v for k,v in result.items() if k!='conflicts'} for name,result in report['results'].items()},indent=2))


if __name__ == '__main__':
    main()
