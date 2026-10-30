"""Matched 557-row error-feature development cache; no independent scenarios."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from socialnetwork_error_features import aggregate_errors, COLUMNS_WITH_ERRORS
from socialnetwork_syscalls import COLUMNS
from prepare_socialnetwork_temporal import context
from audit_socialnetwork_cve_context import digest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'training'))
from evaluate_socialnetwork_attacks import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('old', type=Path)
    parser.add_argument('temporal', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    old_manifest = json.loads((args.old / 'manifest.json').read_text())
    manifest = json.loads((args.temporal / 'manifest.json').read_text())
    if sha(args.old / 'windows.json') != old_manifest['windows_sha256'] or sha(args.old / 'manifest.json') != manifest['old_manifest_sha256']:
        raise ValueError('Frozen matched data changed')
    old_rows = json.loads((args.old / 'windows.json').read_text())
    old = {(r['trace'], r['window'], r['container_group']):r for r in old_rows}
    cases = manifest['cases']
    if len(cases) != 16 or any(not c['base'].startswith('scenario5/plain_workload/') for c in cases):
        raise ValueError('Development boundary changed')
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {'schema':'socialnetwork-error-development-v1', 'cases':cases, 'features':list(COLUMNS_WITH_ERRORS),
            'old_manifest_sha256':sha(args.old / 'manifest.json'), 'old_rows_sha256':sha(args.old / 'windows.json'),
            'temporal_manifest_sha256':sha(args.temporal / 'manifest.json'), 'script_sha256':sha(Path(__file__)),
            'features_sha256':sha(Path(__file__).with_name('socialnetwork_error_features.py')),
            'context_sha256':sha(Path(__file__).with_name('prepare_socialnetwork_temporal.py')),
            'aggregate_base_sha256':sha(Path(__file__).with_name('socialnetwork_syscalls.py')),
            'source_archive_sha256':digest(args.source / 'SocialNetwork-attack-data.zip'),
            'not_final_test':True, 'labels_unchanged':True, 'post_context_used_as_attack':False}
    with (args.output / 'plan.json').open('x') as handle:
        json.dump(plan, handle, indent=2)
    lookup = {trace:case for case in cases for trace in case['traces']}
    observed, audits = {}, []
    with zipfile.ZipFile(args.source / 'SocialNetwork-attack-data.zip') as outer:
        with outer.open('SocialNetwork-attack-data/scenario5.tar.gz') as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode='r|') as nested:
                for item in nested:
                    if item.name not in lookup:
                        continue
                    case, hashes = lookup[item.name], set()
                    audit = {'trace':item.name, 'scanned_events':0}
                    rows, _ = aggregate_errors(context(nested.extractfile(item), case, hashes, audit))
                    if audit.get('last_context_ns', 0) < case['end_ns']:
                        raise ValueError('Incomplete development context')
                    for row in rows:
                        key = (item.name, row['window'], row['container_group'])
                        if key not in old:
                            continue
                        prior = old[key]
                        if any(row['features'][k] != prior['features'][k] for k in COLUMNS):
                            raise ValueError('Matched base feature changed')
                        if key in observed:
                            raise ValueError('Duplicate observation')
                        observed[key] = {**prior, 'features':row['features']}
                    audits.append(audit)
                    print(f"Prepared error features: {item.name}", flush=True)
                    if len(audits) == len(lookup):
                        break
    if set(observed) != set(old):
        raise ValueError('Matched observation coverage changed')
    ordered = [observed[(r['trace'],r['window'],r['container_group'])] for r in old_rows]
    with (args.output / 'windows.json').open('x') as handle:
        json.dump(ordered, handle)
    with (args.output / 'manifest.json').open('x') as handle:
        json.dump({**plan, 'windows_sha256':sha(args.output / 'windows.json'),
                   'plan_sha256':sha(args.output / 'plan.json'), 'rows':len(ordered),
                   'matched_base_replay_verified':True, 'audits':audits}, handle, indent=2)


if __name__ == '__main__':
    main()
