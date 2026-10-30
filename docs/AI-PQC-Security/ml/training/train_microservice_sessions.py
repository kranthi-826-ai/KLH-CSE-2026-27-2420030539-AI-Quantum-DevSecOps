"""Select on grouped training folds, calibrate separately, freeze before one test."""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from microservice_session_features import FEATURE_COLUMNS
from train_ciciot2023_pilot import binary_metrics, json_clean

SEED = 20261019
RECIPES = {'logistic': {'C': 1., 'class_weight': 'balanced', 'max_iter': 1000},
           'random_forest': {'n_estimators': 128, 'max_depth': 6, 'min_samples_leaf': 3,
                             'class_weight': 'balanced', 'n_jobs': 4}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(name):
    if name == 'logistic':
        return make_pipeline(StandardScaler(), LogisticRegression(**RECIPES[name], random_state=SEED))
    return RandomForestClassifier(**RECIPES[name], random_state=SEED)


def validate_manifest(manifest):
    if manifest['status'] != 'complete' or tuple(manifest['feature_columns']) != FEATURE_COLUMNS:
        raise ValueError('Incomplete collection or wrong feature schema')
    seen = set()
    for name in ('train', 'calibration', 'test'):
        ids = [s['session_id'] for s in manifest['splits'][name]['sessions']]
        if len(ids) != len(set(ids)) or seen.intersection(ids):
            raise ValueError('Sessions overlap or are duplicated across partitions')
        seen.update(ids)


def load_split(data, manifest, split):
    path = Path(data) / f'{split}.json'
    if sha(path) != manifest['splits'][split]['sha256']:
        raise ValueError(f'{split} checksum mismatch')
    rows = json.loads(path.read_text(encoding='utf-8'))
    sessions = {s['session_id']: s for s in manifest['splits'][split]['sessions']}
    if len(rows) != manifest['splits'][split]['rows'] or not rows:
        raise ValueError('Wrong row count')
    for row in rows:
        if set(row['features']) != set(FEATURE_COLUMNS):
            raise ValueError('Unexpected predictor, possible target/outcome leakage')
        if row['session_id'] not in sessions or row['scenario'] != sessions[row['session_id']]['scenario']:
            raise ValueError('Unknown session or inconsistent scenario')
        if row['target'] != manifest['label_mapping'][row['scenario']]:
            raise ValueError('Target disagrees with harness intent')
    for session_id, info in sessions.items():
        sequence = [r['sequence'] for r in rows if r['session_id'] == session_id]
        if sequence != list(range(info['requests'])):
            raise ValueError('Missing or duplicated session observations')
    x = np.array([[r['features'][k] for k in FEATURE_COLUMNS] for r in rows], dtype=float)
    y = np.array([r['target'] for r in rows], dtype=int)
    groups = np.array([r['session_id'] for r in rows])
    if not np.isfinite(x).all() or set(y) != {0, 1}:
        raise ValueError('Non-finite features or absent target class')
    return rows, x, y, groups


def choose_threshold(y, probability):
    measurements = [binary_metrics(y, probability, float(t)) for t in np.arange(.05, .951, .025)]
    safe = [r for r in measurements if r['false_positive_rate'] <= .05]
    eligible = [r for r in safe if r['attack_recall'] >= .95]
    # A missing safe threshold is still evaluated diagnostically, never approved.
    selected = max(eligible or safe or measurements, key=lambda r: r['macro_f1'])
    return selected, bool(eligible)


def main(data, output):
    data, output = Path(data), Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite frozen study')
    manifest_path = data / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    _, x, y, groups = load_split(data, manifest, 'train')
    output.mkdir(parents=True)
    plan = {'run_id': output.name, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'recipes': RECIPES, 'seed': SEED, 'feature_columns': FEATURE_COLUMNS,
        'manifest_sha256': sha(manifest_path), 'script_sha256': sha(__file__),
        'evaluator_sha256': sha(Path(__file__).with_name('evaluate_microservice_sessions.py')),
        'feature_module_sha256': sha(Path(__file__).resolve().parents[1] / 'data' / 'microservice_session_features.py'),
        'metric_helper_sha256': sha(Path(__file__).with_name('train_ciciot2023_pilot.py')),
        'selection': 'Three-fold stratified GROUP training CV macro-F1; independent calibration thresholds, then freeze.',
        'gates': 'Calibration and final test: attack recall >=95%, FPR <=5%. Passing lab gates never authorizes production deployment.',
        'test_protocol': 'Reserved later-session test may be evaluated once after model/threshold/code hashes are frozen.',
        'bootstrap': '500 session-cluster bootstrap replicates, seed 20261019, percentile 95% intervals; conditional on this harness only.',
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'sklearn': sklearn.__version__},
        'automatic_response_enabled': False, 'production_accuracy_claim': False}
    (output / 'plan.json').write_text(json.dumps(json_clean(plan), indent=2), encoding='utf-8')
    report = {**plan, 'cv': {}, 'reserved_test_loaded': False}
    folds = list(StratifiedGroupKFold(3, shuffle=True, random_state=SEED).split(x, y, groups))
    for name in RECIPES:
        results = []
        for fitting, held in folds:
            if set(groups[fitting]).intersection(groups[held]):
                raise ValueError('CV group leakage')
            model = build(name)
            model.fit(x[fitting], y[fitting])
            results.append(binary_metrics(y[held], model.predict_proba(x[held])[:, 1], .5))
        report['cv'][name] = {'folds': results, 'mean_macro_f1': float(np.mean([r['macro_f1'] for r in results]))}
    selected = max(RECIPES, key=lambda name: report['cv'][name]['mean_macro_f1'])
    model = build(selected)
    model.fit(x, y)
    _, x_cal, y_cal, _ = load_split(data, manifest, 'calibration')
    calibrated, eligible = choose_threshold(y_cal, model.predict_proba(x_cal)[:, 1])
    report.update(selected_model=selected, calibration=calibrated, calibration_eligible=eligible,
                  training_rows=len(y), training_sessions=len(set(groups)))
    model_path = output / 'candidate.joblib'
    joblib.dump({'model': model, 'threshold': calibrated['threshold'], 'feature_columns': FEATURE_COLUMNS,
                 'status': 'Controlled HTTP lab candidate only; automatic responses disabled'}, model_path)
    report['model_sha256'] = sha(model_path)
    (output / 'frozen.json').write_text(json.dumps(json_clean(report), indent=2, allow_nan=False), encoding='utf-8')
    print(f'Frozen {selected}; calibration accuracy={calibrated["accuracy"]:.4f}, recall={calibrated["attack_recall"]:.4f}, '
          f'FPR={calibrated["false_positive_rate"]:.4f}; test unopened; no deployment.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.data, args.output)
