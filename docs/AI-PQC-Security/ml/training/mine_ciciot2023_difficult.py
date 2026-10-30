"""Mine difficult fitting examples out-of-fold; no outer partitions are opened."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from compare_ciciot2023_capacity import build, passes, RECIPES
from refine_ciciot2023 import calibrate, evaluate, weights
from train_ciciot2023_pilot import DATA, ML_ROOT, json_clean

RUN = 'ciciot2023-difficult-examples-v1'
SEEDS = (42, 123, 2026)
RECIPE = RECIPES['xgb_higher_capacity']


def difficult_weights(labels, probabilities, base_weights):
    """Double weight for misclassified OOF examples; never duplicate rows."""
    incorrect = (np.asarray(probabilities) >= .5) != np.asarray(labels)
    return np.asarray(base_weights) * np.where(incorrect, 2., 1.), incorrect


def main():
    output = ML_ROOT / 'artifacts' / f'{RUN}.json'
    plan_path = output.with_name(f'{RUN}-plan.json')
    if output.exists() or plan_path.exists():
        raise FileExistsError('Evidence already exists; refusing overwrite')
    manifest_path = DATA / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    train_path = DATA / 'train.pkl'
    if hashlib.sha256(train_path.read_bytes()).hexdigest() != manifest['splits']['train']['sha256']:
        raise ValueError('Training checksum mismatch')
    train = pd.read_pickle(train_path)
    columns = manifest['feature_columns']
    plan = {'run_id': RUN, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'seeds': SEEDS, 'recipe': RECIPE,
        'protocol': 'Subtype-stratified 70/15/15 inside frozen train; identical splits to capacity study. '
                    'Within fitting only, 3-fold out-of-fold predictions mark errors at threshold 0.5; '
                    'double their predeclared base weights. Fit reference and mined candidate; '
                    'threshold calibration is separate. No new raw rows or synthetic oversampling.',
        'gates': 'All seeds: calibration eligible, validation recall >=95%, FPR <=5%; '
                 'mean macro-F1 must beat paired reference. No automatic deployment.',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('compare_ciciot2023_capacity.py', 'refine_ciciot2023.py', 'train_ciciot2023_pilot.py')},
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'limitations': 'Repeated development splits, not independent capture or production evaluation. '
                      'Hard-example weights can amplify label noise; compare before accepting.'}
    plan_path.write_text(json.dumps(json_clean(plan), indent=2), encoding='utf-8')
    report = {**plan, 'status': 'running', 'mining': [], 'runs': [], 'promoted': False,
              'reserved_test_loaded': False, 'outer_validation_loaded': False, 'outer_calibration_loaded': False}

    def persist():
        output.write_text(json.dumps(json_clean(report), indent=2, allow_nan=False), encoding='utf-8')

    persist()
    started_all = time.perf_counter()
    for seed in SEEDS:
        fitting, hold = train_test_split(train.index, test_size=.30, stratify=train['_label'], random_state=seed)
        cal_i, val_i = train_test_split(hold, test_size=.5, stratify=train.loc[hold, '_label'], random_state=seed)
        fit, cal, val = train.loc[fitting].reset_index(drop=True), train.loc[cal_i], train.loc[val_i]
        oof = np.full(len(fit), np.nan)
        for fold, (learn, held) in enumerate(StratifiedKFold(3, shuffle=True, random_state=seed).split(fit, fit['_label'])):
            miner = build(RECIPE, seed + fold)
            miner.fit(fit.loc[learn, columns], fit.loc[learn, '_binary_label'], sample_weight=weights(fit.loc[learn], RECIPE))
            oof[held] = miner.predict_proba(fit.loc[held, columns])[:, 1]
            del miner
        if not np.isfinite(oof).all():
            raise ValueError('Missing OOF predictions')
        base = weights(fit, RECIPE)
        mined, errors = difficult_weights(fit['_binary_label'], oof, base)
        inventory = fit[['_label', '_group']].copy()
        inventory['difficult'] = errors
        report['mining'].append({'seed': seed, 'fitting_rows': len(fit), 'difficult_rows': int(errors.sum()),
            'by_subtype': inventory.groupby('_label')['difficult'].agg(['size', 'sum', 'mean']).to_dict('index')})
        for name, sample_weights in (('reference', base), ('oof_difficult_weighted', mined)):
            model = build(RECIPE, seed)
            started = time.perf_counter()
            model.fit(fit[columns], fit['_binary_label'], sample_weight=sample_weights)
            fit_seconds = time.perf_counter() - started
            selected, feasible = calibrate(cal['_binary_label'].to_numpy(), model.predict_proba(cal[columns])[:, 1])
            metrics = evaluate(model, val, columns, selected['threshold'] if selected else .5)
            row = {'seed': seed, 'name': name, 'fit_seconds': fit_seconds, 'calibration': selected,
                'calibration_eligible': feasible, 'validation': metrics,
                'passes_security_gates': bool(feasible and passes(metrics))}
            report['runs'].append(row)
            persist()
            print(f"{seed} {name}: accuracy={metrics['accuracy']:.5f}, recall={metrics['attack_recall']:.5f}, "
                  f"weak_recall={metrics['weak_family_attack_recall']:.5f}, FPR={metrics['false_positive_rate']:.5f}", flush=True)
            del model
    report['summary'] = {}
    for name in ('reference', 'oof_difficult_weighted'):
        rows = [r for r in report['runs'] if r['name'] == name]
        report['summary'][name] = {'all_seeds_pass': all(r['passes_security_gates'] for r in rows),
            'mean': {key: float(np.mean([r['validation'][key] for r in rows]))
                for key in ('accuracy', 'macro_f1', 'attack_recall', 'weak_family_attack_recall', 'false_positive_rate')}}
    report['eligible_for_future_confirmation'] = bool(report['summary']['oof_difficult_weighted']['all_seeds_pass']
        and report['summary']['oof_difficult_weighted']['mean']['macro_f1'] > report['summary']['reference']['mean']['macro_f1'])
    report['elapsed_seconds'] = time.perf_counter() - started_all
    report['status'] = 'complete; outer partitions unopened; no model deployed'
    persist()
    print(json.dumps(report['summary']), flush=True)


if __name__ == '__main__':
    main()
