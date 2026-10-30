"""Bounded development-only observability audit; no training, relabeling or final traces."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile
import zipfile

from socialnetwork_paths import source_directory, PROJECT_ROOT
from socialnetwork_syscalls import first_zip_lines
from socialnetwork_rich_syscalls import SENSITIVE
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'training'))
from evaluate_socialnetwork_attacks import matching_pod

NS = 1_000_000_000
BASE = 'scenario5/plain_workload/CVE-2022-0492/'
MARKERS = ('cgroup', 'release_agent', 'notify_on_release')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024**2), b''):
            result.update(chunk)
    return result.hexdigest()


def select_cases(manifest):
    cases = [case for case in manifest['cases'] if case['id'] == 'CVE-2022-0492']
    expected = {BASE + 'collection-1', BASE + 'collection-2'}
    if len(cases) != 2 or {case['base'] for case in cases} != expected:
        raise ValueError('Only the two previously exposed development recordings are eligible')
    for case in cases:
        traces = {f"{case['base']}/node{node}/sysdig-socialnetwork-events_000.txt.zip" for node in (1, 2)}
        if set(case['traces']) != traces:
            raise ValueError('Trace scope changed')
    return cases


def period(timestamp, case, include_onset_gap=False):
    if case['start_ns'] - 60 * NS <= timestamp < case['start_ns'] - 10 * NS:
        return 'pre_control_context'
    if case['start_ns'] <= timestamp <= case['end_ns']:
        return 'annotated_exposure'
    if case['end_ns'] < timestamp <= case['end_ns'] + 10 * NS:
        return 'post_context_not_labeled'
    if include_onset_gap and case['start_ns'] - 10 * NS <= timestamp < case['start_ns']:
        return 'pre_onset_context_not_labeled'
    return None


def observe_line(line, case, states, include_onset_gap=False):
    fields = line.split(maxsplit=6)
    if len(fields) < 6 or fields[3] not in ('<', '>'):
        raise ValueError('Malformed observed syscall')
    timestamp = int(fields[0])
    selected = period(timestamp, case, include_onset_gap)
    if not selected:
        return
    container = fields[1]
    target = matching_pod(container, case['pod'])
    group = hashlib.sha256(container.encode()).hexdigest()
    key = (selected, group)
    state = states.setdefault(key, {'target_pod':target, 'container_group':group,
        'role':container.split('_')[1] if container.startswith('k8s_') else 'non-k8s',
        'events':0, 'entries':Counter(), 'exits':Counter(), 'negative_results':Counter(),
        'argument_marker_events':Counter()})
    state['events'] += 1
    state['entries' if fields[3] == '>' else 'exits'][fields[5]] += 1
    arguments = fields[6] if len(fields) == 7 else ''
    # Audit only generic markers and syscall/error counts, never raw arguments,
    # executable commands, user paths, process IDs, or exploit payload text.
    for marker in MARKERS:
        state['argument_marker_events'][marker] += marker in arguments
    if fields[3] == '<':
        match = re.search(r'(?:^|\s)res=(-\d+)(?:\D|$)', arguments)
        if match:
            state['negative_results'][fields[5] + ':' + match[1]] += 1


def scan(source, case, include_onset_gap=False):
    states = {}
    maximum = first = last = 0
    scanned = 0
    stop = case['end_ns'] + 10 * NS
    for line in first_zip_lines(source, max_lines=20_000_000, max_bytes=2 * 1024**3):
        timestamp = int(line.split(maxsplit=1)[0])
        if timestamp < maximum - NS:
            raise ValueError('Timestamp regression exceeds the safe streaming cushion')
        maximum = max(maximum, timestamp)
        scanned += 1
        if timestamp > stop + NS:
            break
        if case['start_ns'] - 60 * NS <= timestamp <= stop:
            first = timestamp if not first else min(first, timestamp)
            last = max(last, timestamp)
            observe_line(line, case, states, include_onset_gap)
    if last < stop - NS or first > case['start_ns'] - 59 * NS:
        raise ValueError('Context coverage is incomplete; do not interpret missing data as zero activity')
    records = []
    for (selected, group), state in sorted(states.items()):
        records.append({'period':selected, **state})
    return {'scanned_prefix_events':scanned, 'first_context_ns':first, 'last_context_ns':last,
            'inner_zip_prefix_crc_verified':False, 'records':records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--manifest', type=Path, default=PROJECT_ROOT / 'ml/data/processed/socialnetwork-temporal-development-v1/manifest.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-onset-gap', action='store_true', help='Audit the unlabelled ten seconds before injection; never relabel them')
    args = parser.parse_args()
    source = source_directory(args.source)
    manifest = json.loads(args.manifest.read_text())
    cases = select_cases(manifest)
    args.output.mkdir(parents=True, exist_ok=False)
    archive = source / 'SocialNetwork-attack-data.zip'
    plan = {'schema':'socialnetwork-cve-context-audit-v2' if args.include_onset_gap else 'socialnetwork-cve-context-audit-v1', 'cases':cases,
        'before_seconds':60, 'pre_control_exclusion_seconds':10, 'after_seconds':10,
        'all_worker_containers_observed':True, 'raw_arguments_saved':False,
        'training_allowed':False, 'labels_changed':False, 'final_scenarios_opened':False,
        'exploit_success_inference_allowed':False, 'sensitive_syscall_names':list(SENSITIVE),
        'pre_onset_gap_included_as_unlabeled_context':args.include_onset_gap,
        'archive_sha256':digest(archive), 'manifest_sha256':digest(args.manifest),
        'script_sha256':digest(Path(__file__))}
    with (args.output / 'plan.json').open('x') as handle:
        json.dump(plan, handle, indent=2)
    lookup = {trace:case for case in cases for trace in case['traces']}
    reports = []
    with zipfile.ZipFile(archive) as outer:
        with outer.open('SocialNetwork-attack-data/scenario5.tar.gz') as compressed, gzip.GzipFile(fileobj=compressed) as raw:
            with tarfile.open(fileobj=raw, mode='r|') as nested:
                for item in nested:
                    if item.name not in lookup:
                        continue
                    report = {'trace':item.name, **scan(nested.extractfile(item), lookup[item.name], args.include_onset_gap)}
                    reports.append(report)
                    print(f"Audited development trace {item.name}: {report['scanned_prefix_events']} prefix events", flush=True)
                    if len(reports) == len(lookup):
                        break
    if {r['trace'] for r in reports} != set(lookup):
        raise ValueError('Missing development worker trace')
    with (args.output / 'report.json').open('x') as handle:
        json.dump({'schema':plan['schema'], 'plan_sha256':digest(args.output / 'plan.json'),
                   'traces':reports, 'not_an_accuracy_result':True, 'promoted':False}, handle, indent=2)


if __name__ == '__main__':
    main()
