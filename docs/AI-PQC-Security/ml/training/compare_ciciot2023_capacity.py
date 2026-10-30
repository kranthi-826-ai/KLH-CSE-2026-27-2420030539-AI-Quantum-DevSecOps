"""Predeclared, training-only capacity study. Never opens outer partitions."""
from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import train_test_split

from refine_ciciot2023 import calibrate, evaluate, weights
from train_ciciot2023_pilot import DATA, ML_ROOT, json_clean

RUN = 'ciciot2023-capacity-study-v1'
SEEDS = (42, 123, 2026)
RECIPES = {
    'previous_deeper_reference': {'kind': 'xgb', 'trees': 320, 'depth': 8,
                                 'weak_weight': 3., 'benign_weight': 2.},
    'xgb_higher_capacity': {'kind': 'xgb', 'trees': 500, 'depth': 10,
                            'weak_weight': 3., 'benign_weight': 2.},
    'extra_trees': {'kind': 'extra_trees', 'trees': 240, 'depth': None,
                    'weak_weight': 3., 'benign_weight': 2.},
}


def build(recipe, seed):
    if recipe['kind'] == 'extra_trees':
        return ExtraTreesClassifier(n_estimators=recipe['trees'], max_depth=None,
            min_samples_leaf=1, max_features=1., n_jobs=4, random_state=seed)
    return xgb.XGBClassifier(n_estimators=recipe['trees'], max_depth=recipe['depth'],
        learning_rate=.07, min_child_weight=4, subsample=.85, colsample_bytree=.85,
        reg_alpha=.05, reg_lambda=2., tree_method='hist', eval_metric='logloss',
        n_jobs=4, random_state=seed)


def passes(metrics):
    return bool(metrics['false_positive_rate'] <= .05 and metrics['attack_recall'] >= .95)


def main():
    output = ML_ROOT / 'artifacts' / f'{RUN}.json'
    plan_path = output.with_name(f'{RUN}-plan.json')
    if output.exists() or plan_path.exists():
        raise FileExistsError('Refusing to overwrite experiment evidence')
    manifest_path = DATA / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    train_path = DATA / 'train.pkl'
    if hashlib.sha256(train_path.read_bytes()).hexdigest() != manifest['splits']['train']['sha256']:
        raise ValueError('Training checksum mismatch')
    train = pd.read_pickle(train_path)
    columns = manifest['feature_columns']
    plan = {
        'run_id': RUN, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'recipes': RECIPES, 'seeds': SEEDS, 'threads': 4,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                          for name in ('refine_ciciot2023.py', 'train_ciciot2023_pilot.py')},
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'protocol': 'Frozen train only: subtype-stratified 70/15/15 fit/calibration/validation. '
                    'Same split as prior study for seed 42. Repeats are sensitivity checks, not independent datasets.',
        'calibration': 'Select macro-F1 with FPR <=5%, preferring recall >=95%; no feasible threshold is ineligible.',
        'selection': 'All three seeds must pass recall >=95% and FPR <=5%; '
                     'compare mean macro-F1 to repeated reference. No promotion or outer evaluation in this script.',
        'scope': 'Internal development experiment, not production or official-test accuracy.',
        'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                        'pandas': pd.__version__, 'sklearn': sklearn.__version__, 'xgboost': xgb.__version__},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(json_clean(plan), indent=2, allow_nan=False), encoding='utf-8')
    report = {**plan, 'status': 'running', 'runs': [], 'reserved_test_loaded': False,
              'outer_calibration_loaded': False, 'outer_validation_loaded': False,
              'promoted': False}

    def persist():
        output.write_text(json.dumps(json_clean(report), indent=2, allow_nan=False), encoding='utf-8')

    persist()
    started_all = time.perf_counter()
    for seed in SEEDS:
        fit_index, hold_index = train_test_split(train.index, test_size=.30,
            stratify=train['_label'], random_state=seed)
        cal_index, val_index = train_test_split(hold_index, test_size=.50,
            stratify=train.loc[hold_index, '_label'], random_state=seed)
        fit, cal, val = train.loc[fit_index], train.loc[cal_index], train.loc[val_index]
        for name, recipe in RECIPES.items():
            model = build(recipe, seed)
            started = time.perf_counter()
            model.fit(fit[columns], fit['_binary_label'], sample_weight=weights(fit, recipe))
            seconds = time.perf_counter() - started
            calibrated, feasible = calibrate(cal['_binary_label'].to_numpy(), model.predict_proba(cal[columns])[:, 1])
            threshold = calibrated['threshold'] if calibrated else .5
            metrics = evaluate(model, val, columns, threshold)
            row = {'seed': seed, 'recipe': name, 'parameters': model.get_params(),
                   'fit_seconds': seconds, 'calibration': calibrated,
                   'calibration_eligible': feasible, 'validation': metrics,
                   'passes_security_gates': bool(feasible and passes(metrics))}
            report['runs'].append(row)
            persist()
            print(f"{seed} {name}: accuracy={metrics['accuracy']:.5f}, macro_f1={metrics['macro_f1']:.5f}, "
                  f"recall={metrics['attack_recall']:.5f}, weak_recall={metrics['weak_family_attack_recall']:.5f}, "
                  f"FPR={metrics['false_positive_rate']:.5f}, pass={row['passes_security_gates']}, fit={seconds:.1f}s", flush=True)
            del model
    report['summary'] = {}
    for name in RECIPES:
        rows = [row for row in report['runs'] if row['recipe'] == name]
        report['summary'][name] = {
            'all_seeds_pass': all(row['passes_security_gates'] for row in rows),
            'metrics': {key: {'mean': float(np.mean([row['validation'][key] for row in rows])),
                              'min': min(row['validation'][key] for row in rows),
                              'max': max(row['validation'][key] for row in rows)}
                        for key in ('accuracy', 'macro_f1', 'attack_recall', 'weak_family_attack_recall', 'false_positive_rate')},
        }
    reference = report['summary']['previous_deeper_reference']['metrics']['macro_f1']['mean']
    report['eligible_for_future_confirmation'] = [name for name, row in report['summary'].items()
        if name != 'previous_deeper_reference' and row['all_seeds_pass'] and row['metrics']['macro_f1']['mean'] > reference]
    report['elapsed_seconds'] = time.perf_counter() - started_all
    report['status'] = 'complete; no deployment changes; outer partitions unopened'
    persist()
    print(f"Complete in {report['elapsed_seconds']:.1f}s; eligible={report['eligible_for_future_confirmation']}", flush=True)


if __name__ == '__main__':
    main()
