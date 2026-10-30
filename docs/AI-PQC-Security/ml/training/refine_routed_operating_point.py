"""Training-only model selection at low FPR; no routed final-test access."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from study_routed_sessions import validate_peers, load
from train_microservice_sessions import build, choose_threshold, sha, FEATURE_COLUMNS
from train_ciciot2023_pilot import binary_metrics, json_clean

RECIPES = ('logistic_reference','rf_reference','xgb_depth3','xgb_depth5')


def estimator(name):
    if name == 'logistic_reference': return build('logistic')
    if name == 'rf_reference': return build('random_forest')
    return xgb.XGBClassifier(n_estimators=160,max_depth=3 if name.endswith('3') else 5,
        learning_rate=.05,min_child_weight=4,reg_lambda=4.,subsample=.85,colsample_bytree=.85,
        tree_method='hist',eval_metric='logloss',n_jobs=4,random_state=20261019)


def main(data, output):
    if output.exists(): raise FileExistsError('Refusing to overwrite refinement evidence')
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    validate_peers(manifest)
    _,x,y,peers = load(data,manifest,'train')
    output.mkdir(parents=True)
    plan = {'run_id':output.name,'script_sha256':sha(__file__),'manifest_sha256':sha(data/'manifest.json'),
        'recipes':{name:estimator(name).get_params() if name.startswith('xgb') else name for name in RECIPES},
        'selection':'Mean standardized partial ROC-AUC with max_fpr=0.05, leave-one-transport-peer-out training CV. Calibration only after one recipe selected.',
        'calibration_status':'Previously observed development calibration, NOT untouched test evidence.',
        'promotion_rule':'Never deploy from this study. If calibration recall >=95% and FPR <=5%, require a newly collected independent holdout.',
        'final_test_loaded':False,'automatic_response_enabled':False}
    (output/'plan.json').write_text(json.dumps(json_clean(plan),indent=2),encoding='utf-8')
    report={**plan,'cv':{}}
    for name in RECIPES:
        folds=[]
        for learn,held in GroupKFold(3).split(x,y,peers):
            model=estimator(name)
            model.fit(x[learn],y[learn])
            probability=model.predict_proba(x[held])[:,1]
            folds.append({'partial_auc_fpr05':float(roc_auc_score(y[held],probability,max_fpr=.05)),
                          'default_metrics':binary_metrics(y[held],probability,.5)})
        report['cv'][name]={'folds':folds,'mean_partial_auc_fpr05':float(np.mean([r['partial_auc_fpr05'] for r in folds]))}
        print(f'{name}: training peer-CV partial AUC={report["cv"][name]["mean_partial_auc_fpr05"]:.5f}',flush=True)
    name=max(RECIPES,key=lambda n:report['cv'][n]['mean_partial_auc_fpr05'])
    model=estimator(name)
    model.fit(x,y)
    _,xc,yc,_=load(data,manifest,'calibration')
    metric,eligible=choose_threshold(yc,model.predict_proba(xc)[:,1])
    report.update(selected_model=name,development_calibration=metric,eligible_for_fresh_holdout=eligible,
                  status='complete; old final test not opened; not deployed')
    joblib.dump({'model':model,'threshold':metric['threshold'],'feature_columns':FEATURE_COLUMNS,
                 'status':'Development-only candidate; needs fresh holdout'},output/'candidate.joblib')
    report['model_sha256']=sha(output/'candidate.joblib')
    (output/'result.json').write_text(json.dumps(json_clean(report),indent=2,allow_nan=False),encoding='utf-8')
    print(f'Development calibration {name}: recall={metric["attack_recall"]:.4f}, FPR={metric["false_positive_rate"]:.4f}, eligible={eligible}; no test evaluation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    main(args.data,args.output)
