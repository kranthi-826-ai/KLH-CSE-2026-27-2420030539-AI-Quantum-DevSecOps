"""Bounded family-aware study, selected on internal training partitions only."""
from __future__ import annotations
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from train_ciciot2023_pilot import DATA, ML_ROOT, binary_metrics, json_clean

RUN = 'ciciot2023-family-refinement-v1'
OUTPUT = ML_ROOT / 'artifacts' / f'{RUN}.json'
PLAN = ML_ROOT / 'artifacts' / f'{RUN}-plan.json'
SEEDS = (42,123,2026)
RECIPES = {
    'reference':{'weak_weight':1.,'benign_weight':1.,'depth':6,'trees':220},
    'family_weighted':{'weak_weight':2.,'benign_weight':1.5,'depth':6,'trees':280},
    'benign_weighted':{'weak_weight':2.,'benign_weight':3.,'depth':6,'trees':280},
    'family_deeper':{'weak_weight':3.,'benign_weight':2.,'depth':8,'trees':320},
}
WEAK = ('BruteForce','Recon','Web-based')


def build(recipe,seed):
    return xgb.XGBClassifier(n_estimators=recipe['trees'],max_depth=recipe['depth'],
        learning_rate=.07,min_child_weight=4,subsample=.85,colsample_bytree=.85,
        reg_alpha=.05,reg_lambda=2.,tree_method='hist',eval_metric='logloss',
        n_jobs=4,random_state=seed)


def weights(frame,recipe):
    return np.where(frame['_group']=='Benign',recipe['benign_weight'],
        np.where(frame['_group'].isin(WEAK),recipe['weak_weight'],1.))


def calibrate(labels,probabilities):
    # Choose within the false-alarm budget. Eligibility still requires recall
    # >=95%; a fallback threshold is a diagnostic, not a passing candidate.
    results = []
    for threshold in np.round(np.arange(.10,.901,.01),2):
        prediction = probabilities >= threshold
        fpr = float(np.mean(prediction[labels==0]))
        recall = float(np.mean(prediction[labels==1]))
        if fpr <= .05:
            result = binary_metrics(labels,probabilities,float(threshold))
            results.append(result)
    eligible = [row for row in results if row['attack_recall'] >= .95]
    pool = eligible or results
    selected = max(pool,key=lambda row:row['macro_f1'],default=None)
    return selected, bool(eligible)


def evaluate(model,frame,columns,threshold):
    started = time.perf_counter()
    probability = model.predict_proba(frame[columns])[:,1]
    seconds = time.perf_counter()-started
    result = binary_metrics(frame['_binary_label'].to_numpy(),probability,threshold,
                            frame['_label'].to_numpy())
    weak_mask = frame['_group'].isin(WEAK).to_numpy()
    result['weak_family_attack_recall'] = float(np.mean(probability[weak_mask] >= threshold))
    result['inference_ms_per_sample'] = seconds*1000/len(frame)
    return result


def main():
    if OUTPUT.exists() or PLAN.exists():
        raise FileExistsError('Refusing to overwrite frozen experiment evidence')
    manifest_path = DATA / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    train_path = DATA / 'train.pkl'
    if hashlib.sha256(train_path.read_bytes()).hexdigest() != manifest['splits']['train']['sha256']:
        raise ValueError('Training partition checksum mismatch')
    train = pd.read_pickle(train_path)
    columns = manifest['feature_columns']
    plan = {'run_id':RUN,'created_utc':datetime.now(timezone.utc).isoformat(),
        'recipes':RECIPES,'confirmation_seeds':list(SEEDS),'weak_families':list(WEAK),
        'selection':'Internal validation macro-F1, FPR <=5%, recall >=95%. If no recipe qualifies, stop without opening outer calibration/validation/test.',
        'internal_split':'70/15/15 stratified by attack subtype, drawn from frozen train only',
        'outer_validation_prior_exposure':'The earlier baseline study evaluated outer validation. New recipe selection uses internal training splits; outer validation is a development confirmation, not untouched evidence.',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    PLAN.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    report = {**plan,'status':'running','inner_runs':[], 'reserved_test_loaded':False,
              'outer_calibration_loaded':False,'outer_validation_loaded':False}

    def persist():
        OUTPUT.write_text(json.dumps(json_clean(report),indent=2,allow_nan=False),encoding='utf-8')

    chosen = None
    for seed in SEEDS:
        fit_index,hold_index = train_test_split(train.index,test_size=.30,
            stratify=train['_label'],random_state=seed)
        calibration_index,validation_index = train_test_split(hold_index,test_size=.50,
            stratify=train.loc[hold_index,'_label'],random_state=seed)
        fit,cal,val = train.loc[fit_index],train.loc[calibration_index],train.loc[validation_index]
        names = list(RECIPES) if chosen is None else ['reference',chosen]
        seed_runs = []
        for name in dict.fromkeys(names):
            recipe = RECIPES[name]
            model = build(recipe,seed)
            started = time.perf_counter()
            model.fit(fit[columns],fit['_binary_label'],sample_weight=weights(fit,recipe))
            fit_seconds = time.perf_counter()-started
            calibration,feasible = calibrate(cal['_binary_label'].to_numpy(),model.predict_proba(cal[columns])[:,1])
            threshold = calibration['threshold'] if calibration else .5
            metrics = evaluate(model,val,columns,threshold)
            passes = bool(feasible and metrics['false_positive_rate']<=.05 and metrics['attack_recall']>=.95)
            row = {'seed':seed,'recipe':name,'fit_seconds':fit_seconds,
                'calibration':calibration,'calibration_eligible':feasible,
                'validation':metrics,'passes_security_gates':passes}
            seed_runs.append(row)
            report['inner_runs'].append(row)
            persist()
            print(f"seed={seed} {name}: accuracy={metrics['accuracy']:.5f}, macro_f1={metrics['macro_f1']:.5f}, recall={metrics['attack_recall']:.5f}, weak_recall={metrics['weak_family_attack_recall']:.5f}, fpr={metrics['false_positive_rate']:.5f}, pass={passes}",flush=True)
        if chosen is None:
            candidates = [row for row in seed_runs if row['passes_security_gates'] and row['recipe']!='reference']
            if not candidates:
                report['status'] = 'complete; no internally eligible candidate; outer partitions unopened'
                persist()
                print(report['status'],flush=True)
                return
            chosen = max(candidates,key=lambda row:row['validation']['macro_f1'])['recipe']
            report['selected_recipe'] = chosen
    stable = all(row['passes_security_gates'] for row in report['inner_runs'] if row['recipe']==chosen)
    report['stable_across_seeds'] = stable
    if not stable:
        report['status'] = 'complete; confirmation failed; outer partitions unopened'
        persist()
        return
    outer = {}
    for split in ('calibration','validation'):
        path = DATA / f'{split}.pkl'
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['splits'][split]['sha256']:
            raise ValueError(f'{split} checksum mismatch')
        outer[split] = pd.read_pickle(path)
        report[f'outer_{split}_loaded'] = True
    model = build(RECIPES[chosen],SEEDS[0])
    model.fit(train[columns],train['_binary_label'],sample_weight=weights(train,RECIPES[chosen]))
    selected,feasible = calibrate(outer['calibration']['_binary_label'].to_numpy(),model.predict_proba(outer['calibration'][columns])[:,1])
    report['outer_calibration'] = selected
    threshold = selected['threshold'] if selected else .5
    metrics = evaluate(model,outer['validation'],columns,threshold)
    report['outer_validation'] = metrics
    report['passes_outer_gates'] = bool(feasible and metrics['false_positive_rate']<=.05 and metrics['attack_recall']>=.95)
    report['status'] = 'complete; development confirmation only; not deployed'
    destination = ML_ROOT / 'models' / 'candidates' / f'{RUN}.joblib'
    joblib.dump({'model':model,'columns':columns,'threshold':threshold,'plan':plan,
                'status':'not deployed'},destination)
    persist()
    print(f"Outer validation: accuracy={metrics['accuracy']:.5f}, macro_f1={metrics['macro_f1']:.5f}, recall={metrics['attack_recall']:.5f}, fpr={metrics['false_positive_rate']:.5f}, pass={report['passes_outer_gates']}",flush=True)


if __name__ == '__main__':
    main()
