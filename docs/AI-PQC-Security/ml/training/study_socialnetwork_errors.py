"""One declared generic-error ablation on existing grouped development data only."""
import argparse
from importlib.metadata import version as package_version
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.model_selection import LeaveOneGroupOut

from study_socialnetwork_supervised import build, metrics, RECIPES
from train_socialnetwork_reference import sha
from train_socialnetwork_reference import SEED
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from socialnetwork_syscalls import COLUMNS
from socialnetwork_error_features import COLUMNS_WITH_ERRORS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    parser.add_argument('reference', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.data / 'manifest.json').read_text())
    if not manifest['matched_base_replay_verified'] or sha(args.data / 'windows.json') != manifest['windows_sha256']:
        raise ValueError('Unverified matched development data')
    feature_path = Path(__file__).resolve().parents[1] / 'data/socialnetwork_error_features.py'
    if sha(feature_path) != manifest['features_sha256']:
        raise ValueError('Feature implementation changed')
    rows = json.loads((args.data / 'windows.json').read_text())
    previous = json.loads(args.reference.read_text())
    y = np.asarray([r['label'] for r in rows])
    groups = np.asarray([r['case'] for r in rows])
    if len(rows) != 557 or len(set(groups)) != 8 or sum(y) != 51:
        raise ValueError('Original development scope changed')
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {'schema':'socialnetwork-error-grouped-v1','data_manifest_sha256':sha(args.data / 'manifest.json'),
            'reference_sha256':sha(args.reference),'feature_sha256':sha(feature_path),'script_sha256':sha(Path(__file__)),
            'recipe_sha256':sha(Path(__file__).with_name('study_socialnetwork_supervised.py')),
            'reference_helpers_sha256':sha(Path(__file__).with_name('train_socialnetwork_reference.py')),
            'seed':SEED, 'python_version':sys.version,
            'package_versions':{name:package_version(name) for name in ('numpy','scikit-learn','xgboost','joblib')},
            'features':{'base':list(COLUMNS),'errors':list(COLUMNS_WITH_ERRORS)},'recipes':list(RECIPES),
            'threshold':.5,'validation':'eight CVE-group folds holding both recordings out together',
            'minimum_exposure_recall':.95,'maximum_control_alarm_fraction':.05,
            'minimum_macro_f1':previous['results']['base_logistic']['metrics']['macro_f1'],
            'independent_evaluation_required':True,'promotion_allowed':False,'not_final_test':True}
    with (args.output / 'plan.json').open('x') as handle:
        json.dump(plan, handle, indent=2)
    results = {}
    for version, columns in (('base', COLUMNS),('errors', COLUMNS_WITH_ERRORS)):
        x = np.asarray([[r['features'][k] for k in columns] for r in rows])
        if not np.isfinite(x).all():
            raise ValueError('Nonfinite model input')
        for recipe in RECIPES:
            predictions = np.zeros(len(rows), dtype=int)
            folds = []
            for train, validation in LeaveOneGroupOut().split(x, y, groups):
                if set(groups[train]) & set(groups[validation]):
                    raise ValueError('CVE leakage')
                model = build(recipe).fit(x[train], y[train])
                predictions[validation] = model.predict_proba(x[validation])[:,1] >= .5
                folds.append({'held_out':str(groups[validation][0]), **metrics(y[validation], predictions[validation])})
            summary = metrics(y, predictions)
            key = version + '_' + recipe
            if version == 'base' and summary != previous['results'][key]['metrics']:
                raise ValueError('Matched baseline no longer reproduces')
            eligible = bool(summary['exposure_recall'] >= .95 and summary['control_alarm_fraction'] <= .05
                            and summary['macro_f1'] >= plan['minimum_macro_f1'])
            results[key] = {'metrics':summary,'folds':folds,'eligible':eligible,'window_predictions':predictions.tolist()}
            print(f'{key}: {summary}; eligible={eligible}', flush=True)
    eligible = [k for k,v in results.items() if k.startswith('errors_') and v['eligible']]
    winner = max(eligible, key=lambda key: results[key]['metrics']['macro_f1']) if eligible else None
    result = {'schema':plan['schema'],'results':results,'selected_candidate':winner,'promoted':False,
              'enforcement_enabled':False,'not_final_test':True,'attack_accuracy':None,
              'plan_sha256':sha(args.output / 'plan.json')}
    if winner:
        model = build(winner.removeprefix('errors_')).fit(
            np.asarray([[r['features'][k] for k in COLUMNS_WITH_ERRORS] for r in rows]), y)
        joblib.dump(model, args.output / 'candidate.joblib')
        result['candidate_sha256'] = sha(args.output / 'candidate.joblib')
    with (args.output / 'report.json').open('x') as handle:
        json.dump(result, handle, indent=2)


if __name__ == '__main__':
    main()
