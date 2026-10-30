"""One frozen later-session evaluation, never reused to tune this candidate."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np

from train_microservice_sessions import load_split, sha, validate_manifest
from train_ciciot2023_pilot import binary_metrics, json_clean


def cluster_intervals(y, prediction, groups):
    rng = np.random.default_rng(20261019)
    unique = np.unique(groups)
    indices = {g: np.flatnonzero(groups == g) for g in unique}
    samples = {'accuracy': [], 'attack_recall': [], 'false_positive_rate': []}
    for _ in range(500):
        chosen = np.concatenate([indices[g] for g in rng.choice(unique, len(unique), replace=True)])
        actual, predicted = y[chosen], prediction[chosen]
        if not np.any(actual == 1) or not np.any(actual == 0):
            continue
        samples['accuracy'].append(float(np.mean(actual == predicted)))
        samples['attack_recall'].append(float(np.mean(predicted[actual == 1])))
        samples['false_positive_rate'].append(float(np.mean(predicted[actual == 0])))
    return {key: {'lower': float(np.quantile(values, .025)), 'upper': float(np.quantile(values, .975)),
                  'valid_replicates': len(values)} for key, values in samples.items()}


def main(data, study):
    data, study = Path(data), Path(study)
    result_path, lock_path = study / 'final-test.json', study / 'test-evaluation-started.json'
    if result_path.exists() or lock_path.exists():
        raise FileExistsError('Final-test evaluation already attempted; do not overwrite or retune')
    frozen_path = study / 'frozen.json'
    frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
    manifest_path = data / 'manifest.json'
    for path, expected in ((study / 'candidate.joblib', frozen['model_sha256']),
                           (manifest_path, frozen['manifest_sha256']),
                           (Path(__file__), frozen['evaluator_sha256']),
                           (Path(__file__).with_name('train_microservice_sessions.py'), frozen['script_sha256']),
                           (Path(__file__).resolve().parents[1] / 'data' / 'microservice_session_features.py', frozen['feature_module_sha256']),
                           (Path(__file__).with_name('train_ciciot2023_pilot.py'), frozen['metric_helper_sha256'])):
        if sha(path) != expected:
            raise ValueError(f'Frozen evidence changed: {path.name}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    with lock_path.open('x', encoding='utf-8') as stream:
        json.dump({'frozen_sha256': sha(frozen_path), 'status': 'one-shot evaluation started'}, stream)
    rows, x, y, groups = load_split(data, manifest, 'test')
    candidate = joblib.load(study / 'candidate.joblib')
    probability = candidate['model'].predict_proba(x)[:, 1]
    threshold = candidate['threshold']
    prediction = (probability >= threshold).astype(int)
    metrics = binary_metrics(y, probability, threshold)
    rule = np.array([int(r['features']['prior_failed_login_5s'] >= 3 or r['features']['prior_401_5s'] >= 4) for r in rows])
    scenarios = {s: {'samples': sum(r['scenario'] == s for r in rows),
        'alert_rate': float(np.mean(prediction[[r['scenario'] == s for r in rows]]))} for s in sorted({r['scenario'] for r in rows})}
    result = {'run_id': study.name, 'frozen_sha256': sha(frozen_path), 'manifest_sha256': sha(manifest_path),
        'reserved_test_loaded': True, 'test_rows': len(y), 'test_sessions': len(set(groups)),
        'candidate': metrics, 'session_cluster_95_intervals': cluster_intervals(y, prediction, groups),
        'always_normal_baseline': binary_metrics(y, np.zeros(len(y)), .5),
        'history_rule_baseline': binary_metrics(y, rule.astype(float), .5), 'by_scenario': scenarios,
        'lab_gates_pass': bool(frozen['calibration_eligible'] and metrics['attack_recall'] >= .95 and metrics['false_positive_rate'] <= .05),
        'automatic_response_enabled': False, 'promoted': False,
        'scope': 'Later sessions from the same controlled HTTP harness and host; NOT production or cross-dataset accuracy.',
        'limitations': ['Only 12 held-out sessions, same scenario generator, application, host and collection run.',
                       'No successful exploitation, distributed DDoS, unknown attack family or production users evaluated.',
                       'First suspicious requests may be indistinguishable from legitimate mistakes.',
                       'Observed labels are controlled intent; outcomes are independent control evidence, not model labels.',
                       'CICIoT/UNSW model and reserved datasets were not changed or opened.']}
    with result_path.open('x', encoding='utf-8') as stream:
        json.dump(json_clean(result), stream, indent=2, allow_nan=False)
    print(f'Final local lab: accuracy={metrics["accuracy"]:.4f}, recall={metrics["attack_recall"]:.4f}, '
          f'FPR={metrics["false_positive_rate"]:.4f}; lab_gates={result["lab_gates_pass"]}; no deployment.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--study', type=Path, required=True)
    args = parser.parse_args()
    main(args.data, args.study)
