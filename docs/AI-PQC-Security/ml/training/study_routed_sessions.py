"""Frozen peer-grouped routed HTTP study; separate train and one-shot test stages."""
import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.model_selection import GroupKFold
from train_microservice_sessions import RECIPES, FEATURE_COLUMNS, build, choose_threshold, load_split, validate_manifest, sha
from train_ciciot2023_pilot import binary_metrics, json_clean
from evaluate_microservice_sessions import cluster_intervals


def validate_peers(manifest):
    validate_manifest(manifest)
    seen = set()
    for split, expected in (('train', 3), ('calibration', 2), ('test', 2)):
        peers = manifest['splits'][split]['peer_ids']
        if len(peers) != expected or len(set(peers)) != expected or seen.intersection(peers):
            raise ValueError('Transport peers overlap or are missing')
        seen.update(peers)


def load(data, manifest, split):
    rows, x, y, _ = load_split(data, manifest, split)
    peers = np.array([r['trusted_peer_id'] for r in rows])
    if set(peers) != set(manifest['splits'][split]['peer_ids']):
        raise ValueError('Peer rows disagree with manifest')
    return rows, x, y, peers


def train(data, output, reference):
    if output.exists():
        raise FileExistsError('Refusing to overwrite a frozen routed study')
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    validate_peers(manifest)
    rows, x, y, peers = load(data, manifest, 'train')
    output.mkdir(parents=True)
    helpers = {name: sha(Path(__file__).with_name(name)) for name in (
        'train_microservice_sessions.py', 'train_ciciot2023_pilot.py', 'evaluate_microservice_sessions.py')}
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(), 'run_id': output.name,
        'recipes': RECIPES, 'feature_columns': FEATURE_COLUMNS, 'seed': 20261019,
        'script_sha256': sha(__file__), 'helper_hashes': helpers,
        'manifest_sha256': sha(data/'manifest.json'), 'reference_model_sha256': sha(reference/'candidate.joblib'),
        'reference_frozen_sha256': sha(reference/'frozen.json'),
        'selection': 'Leave-one-transport-peer-out training CV across three peers; mean macro-F1; separate calibration; freeze before final peer holdout.',
        'gates': 'Calibration and final point estimates: recall >=95%, FPR <=5%. Never automatic deployment.',
        'test': 'Two unseen transport peers, one frozen evaluation; compare paired old per-account model and a predeclared history rule.',
        'intervals': '500 cluster bootstrap replicates by transport peer. Only two final peers: intervals are descriptive, not reliable population uncertainty.',
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'sklearn': sklearn.__version__},
        'automatic_response_enabled': False, 'production_accuracy_claim': False}
    (output/'plan.json').write_text(json.dumps(json_clean(plan), indent=2), encoding='utf-8')
    report = {**plan, 'cv': {}, 'reserved_test_loaded': False}
    for name in RECIPES:
        metrics = []
        for fitting, held in GroupKFold(3).split(x, y, peers):
            assert not set(peers[fitting]).intersection(peers[held])
            model = build(name)
            model.fit(x[fitting], y[fitting])
            metrics.append(binary_metrics(y[held], model.predict_proba(x[held])[:,1], .5))
        report['cv'][name] = {'folds': metrics, 'mean_macro_f1': float(np.mean([m['macro_f1'] for m in metrics]))}
    name = max(RECIPES, key=lambda name: report['cv'][name]['mean_macro_f1'])
    model = build(name)
    model.fit(x, y)
    _, xc, yc, _ = load(data, manifest, 'calibration')
    calibration, eligible = choose_threshold(yc, model.predict_proba(xc)[:,1])
    joblib.dump({'model': model, 'threshold': calibration['threshold'], 'feature_columns': FEATURE_COLUMNS,
                 'status': 'Routed lab candidate, not deployed'}, output/'candidate.joblib')
    report.update(selected_model=name, calibration=calibration, calibration_eligible=eligible,
                  model_sha256=sha(output/'candidate.joblib'), training_rows=len(rows))
    (output/'frozen.json').write_text(json.dumps(json_clean(report), indent=2, allow_nan=False), encoding='utf-8')
    print(f'Frozen {name}; calibration accuracy={calibration["accuracy"]:.4f}, recall={calibration["attack_recall"]:.4f}, FPR={calibration["false_positive_rate"]:.4f}; eligible={eligible}; final test unopened.')


def evaluate(data, output, reference):
    if (output/'final-test.json').exists() or (output/'test-started.json').exists():
        raise FileExistsError('Final evaluation already attempted; do not retune or overwrite')
    frozen = json.loads((output/'frozen.json').read_text(encoding='utf-8'))
    for path, digest in [(data/'manifest.json', frozen['manifest_sha256']),
                         (output/'candidate.joblib', frozen['model_sha256']),
                         (reference/'candidate.joblib', frozen['reference_model_sha256']),
                         (reference/'frozen.json', frozen['reference_frozen_sha256']),
                         (Path(__file__), frozen['script_sha256'])] + [
                             (Path(__file__).with_name(name), digest) for name,digest in frozen['helper_hashes'].items()]:
        if sha(path) != digest: raise ValueError(f'Frozen dependency changed: {path.name}')
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    validate_peers(manifest)
    with (output/'test-started.json').open('x', encoding='utf-8') as stream:
        json.dump({'frozen_sha256': sha(output/'frozen.json')}, stream)
    rows, x, y, peers = load(data, manifest, 'test')
    results = {}
    for name, folder in (('routed_candidate', output), ('per_account_reference', reference)):
        candidate = joblib.load(folder/'candidate.joblib')
        if tuple(candidate['feature_columns']) != tuple(FEATURE_COLUMNS): raise ValueError('Candidate feature mismatch')
        probabilities = candidate['model'].predict_proba(x)[:,1]
        predictions = probabilities >= candidate['threshold']
        results[name] = {'metrics': binary_metrics(y, probabilities, candidate['threshold']),
            'peer_cluster_intervals': cluster_intervals(y, predictions, peers),
            'by_scenario': {scenario: {'samples': sum(r['scenario']==scenario for r in rows),
                'alert_rate': float(np.mean(predictions[[r['scenario']==scenario for r in rows]]))}
                for scenario in sorted({r['scenario'] for r in rows})}}
    rule = np.array([int(r['features']['prior_failed_login_5s']>=3 or r['features']['prior_401_5s']>=4) for r in rows])
    results['history_rule'] = {'metrics': binary_metrics(y, rule.astype(float), .5)}
    m = results['routed_candidate']['metrics']
    report = {'run_id': output.name, 'frozen_sha256': sha(output/'frozen.json'), 'test_rows': len(rows),
        'test_sessions': len({r['session_id'] for r in rows}), 'unseen_transport_peers': len(set(peers)), 'results': results,
        'lab_gates_pass': bool(frozen['calibration_eligible'] and m['attack_recall']>=.95 and m['false_positive_rate']<=.05),
        'promoted': False, 'automatic_response_enabled': False, 'reserved_test_loaded': True,
        'scope': 'Real routed local HTTP, real authentication/H2; controlled intent scenarios, not production accuracy.',
        'limitations': ['Only seven collection peers and two final peers, one host/run/generator.',
            'Expanded lab limiter settings isolate detection from gateway blocking; default limiter is checked separately.',
            'No successful exploitation, DDoS saturation, MySQL or Business Service/PQC measured in this dataset.',
            'No claims of beating external research scores or detecting all unknown attacks.']}
    with (output/'final-test.json').open('x', encoding='utf-8') as stream:
        json.dump(json_clean(report), stream, indent=2, allow_nan=False)
    print(f'Final routed lab: accuracy={m["accuracy"]:.4f}, recall={m["attack_recall"]:.4f}, FPR={m["false_positive_rate"]:.4f}; gates={report["lab_gates_pass"]}; no deployment.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('train','evaluate'))
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    (train if args.stage=='train' else evaluate)(args.data,args.output,args.reference)
