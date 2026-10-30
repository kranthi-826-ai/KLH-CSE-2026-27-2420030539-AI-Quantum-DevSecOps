"""Train bounded CICIoT2023 baselines using train/calibration/validation only."""
from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    classification_report, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)

ML_ROOT = Path(__file__).resolve().parents[1]
DATA = ML_ROOT / 'data' / 'processed' / 'ciciot2023-pilot-v1'
OUTPUT = ML_ROOT / 'artifacts' / 'ciciot2023-pilot-validation-v1.json'
MODELS = ML_ROOT / 'models' / 'candidates' / 'ciciot2023-pilot-v1'
SEED = 20261019


def json_clean(value):
    if isinstance(value, dict):
        return {str(key):json_clean(item) for key,item in value.items()}
    if isinstance(value, (list,tuple)):
        return [json_clean(item) for item in value]
    if isinstance(value, np.generic):
        return json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def save_summary(summary: dict) -> None:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(json_clean(summary),indent=2,allow_nan=False),encoding='utf-8')


def binary_metrics(y, probabilities, threshold: float, categories=None) -> dict:
    prediction = (probabilities >= threshold).astype(int)
    tn,fp,fn,tp = confusion_matrix(y,prediction,labels=[0,1]).ravel()
    result = {
        'threshold':float(threshold), 'samples':len(y),
        'accuracy':float(accuracy_score(y,prediction)),
        'balanced_accuracy':float(balanced_accuracy_score(y,prediction)),
        'macro_precision':float(precision_score(y,prediction,average='macro',zero_division=0)),
        'macro_f1':float(f1_score(y,prediction,average='macro',zero_division=0)),
        'attack_recall':float(recall_score(y,prediction,zero_division=0)),
        'attack_precision':float(precision_score(y,prediction,zero_division=0)),
        'false_positive_rate':float(fp/(tn+fp)) if tn+fp else None,
        'roc_auc':float(roc_auc_score(y,probabilities)),
        'pr_auc':float(average_precision_score(y,probabilities)),
        'confusion_matrix':[[int(tn),int(fp)],[int(fn),int(tp)]],
    }
    if categories is not None:
        result['attack_recall_by_family'] = {
            str(label):{'samples':int(np.sum(categories==label)),
                        'recall':float(np.mean(prediction[categories==label]))}
            for label in sorted(set(categories)) if label != 'BenignTraffic'
        }
    return result


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f'Refusing to overwrite prior evidence: {OUTPUT}')
    manifest_path = DATA / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    columns = manifest['feature_columns']
    partitions = {}
    for split in ('train','calibration','validation'):
        path = DATA / f'{split}.pkl'
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['splits'][split]['sha256']:
            raise ValueError(f'Frozen {split} checksum mismatch')
        partitions[split] = pd.read_pickle(path)
    # No test file is opened by this script.
    train,calibration,validation = (partitions[name] for name in ('train','calibration','validation'))
    x_train,y_train = train[columns],train['_binary_label'].to_numpy()
    x_cal,y_cal = calibration[columns],calibration['_binary_label'].to_numpy()
    x_val,y_val = validation[columns],validation['_binary_label'].to_numpy()
    print(f'Train={len(train)}, calibration={len(calibration)}, validation={len(validation)}; test is not loaded.',flush=True)
    estimators = {
        'majority_baseline':DummyClassifier(strategy='most_frequent'),
        'random_forest':RandomForestClassifier(n_estimators=160,max_depth=20,
            min_samples_leaf=2,class_weight='balanced_subsample',n_jobs=4,random_state=SEED),
        'xgboost':xgb.XGBClassifier(n_estimators=220,max_depth=6,learning_rate=.07,
            min_child_weight=4,subsample=.85,colsample_bytree=.85,reg_alpha=.05,
            reg_lambda=2.0,tree_method='hist',eval_metric='logloss',n_jobs=4,random_state=SEED),
    }
    summary = {
        'run_id':'ciciot2023-pilot-validation-v1','created_utc':datetime.now(timezone.utc).isoformat(),
        'run_status':'running',
        'training_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dataset':'CICIoT2023 per-attack 39-feature CSV release',
        'scope':'Bounded pilot validation; not official full-dataset or production accuracy',
        'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'seed':SEED,'feature_columns':columns,
        'excluded_metadata':['filename','source','label','attack family','row position','feature hash','sampling priority'],
        'split_sizes':{name:len(frame) for name,frame in partitions.items()},
        'reserved_test_loaded':False,
        'selection_rule':'Calibration macro-F1 maximized with FPR <= 5% and attack recall >= 95%; validate once per predefined candidate.',
        'environment':{'python':platform.python_version(),'pandas':pd.__version__,
                       'numpy':np.__version__,'scikit_learn':sklearn.__version__,'xgboost':xgb.__version__},
        'models':{}, 'limitations':manifest['limitations'],
    }
    MODELS.mkdir(parents=True,exist_ok=True)
    for name,model in estimators.items():
        started = time.perf_counter()
        model.fit(x_train,y_train)
        fit_seconds = time.perf_counter()-started
        cal_probability = model.predict_proba(x_cal)[:,list(model.classes_).index(1)]
        feasible = []
        for threshold in np.round(np.arange(.10,.901,.01),2):
            metric = binary_metrics(y_cal,cal_probability,float(threshold))
            if metric['false_positive_rate'] <= .05 and metric['attack_recall'] >= .95:
                feasible.append(metric)
        selected = max(feasible,key=lambda result:result['macro_f1'],default=None)
        threshold = selected['threshold'] if selected else .5
        started = time.perf_counter()
        val_probability = model.predict_proba(x_val)[:,list(model.classes_).index(1)]
        infer_seconds = time.perf_counter()-started
        baseline_metrics = binary_metrics(y_val,val_probability,.5)
        val_metrics = binary_metrics(y_val,val_probability,threshold,validation['_label'].to_numpy())
        passes = bool(selected and val_metrics['false_positive_rate'] <= .05 and val_metrics['attack_recall'] >= .95)
        summary['models'][name] = {
            'parameters':model.get_params(),'fit_seconds':fit_seconds,
            'inference_ms_per_sample':infer_seconds*1000/len(validation),
            'feasible_calibration_thresholds':len(feasible),'selected_calibration':selected,
            'default_threshold_validation':baseline_metrics,'validation':val_metrics,
            'passes_predeclared_validation_gates':passes,
            'status':'validation candidate only' if passes else 'does not meet all validation gates',
        }
        if name != 'majority_baseline':
            joblib.dump({'model':model,'columns':columns,'threshold':threshold,
                         'manifest_sha256':summary['manifest_sha256'],
                         'status':'pilot candidate, not deployed'},MODELS / f'{name}.joblib')
        print(f"{name}: accuracy={val_metrics['accuracy']:.6f}, macro_f1={val_metrics['macro_f1']:.6f}, recall={val_metrics['attack_recall']:.6f}, FPR={val_metrics['false_positive_rate']:.6f}, threshold={threshold:.2f}, gates={passes}, fit={fit_seconds:.1f}s",flush=True)
        save_summary(summary)

    # A separate eight-group classifier answers which broad attack family is
    # predicted. A binary model alone cannot support attack-type claims.
    groups = sorted(train['_group'].unique())
    group_indices = {name:index for index,name in enumerate(groups)}
    group_model = xgb.XGBClassifier(n_estimators=160,max_depth=6,learning_rate=.07,
        min_child_weight=4,subsample=.85,colsample_bytree=.85,reg_lambda=2,
        tree_method='hist',eval_metric='mlogloss',n_jobs=4,random_state=SEED)
    started = time.perf_counter()
    group_model.fit(x_train,train['_group'].map(group_indices).to_numpy())
    fit_seconds = time.perf_counter()-started
    predicted = np.array(groups)[group_model.predict(x_val).astype(int)]
    actual = validation['_group'].to_numpy()
    summary['eight_group_classifier'] = {
        'labels':groups,'parameters':group_model.get_params(),'fit_seconds':fit_seconds,
        'accuracy':float(accuracy_score(actual,predicted)),
        'macro_f1':float(f1_score(actual,predicted,average='macro',zero_division=0)),
        'classification_report':classification_report(actual,predicted,labels=groups,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(actual,predicted,labels=groups).tolist(),
        'status':'validation baseline only; not deployed',
    }
    joblib.dump({'model':group_model,'columns':columns,'labels':groups,
                 'status':'pilot candidate, not deployed'},MODELS / 'eight_group_xgboost.joblib')
    summary['run_status'] = 'complete'
    save_summary(summary)
    print(f"8-group XGBoost: accuracy={summary['eight_group_classifier']['accuracy']:.6f}, macro_f1={summary['eight_group_classifier']['macro_f1']:.6f}; saved {OUTPUT}",flush=True)


if __name__ == '__main__':
    main()
