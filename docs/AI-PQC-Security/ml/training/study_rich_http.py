"""Fresh peer-holdout context-feature study with a matched nine-feature ablation."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import sklearn
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'data'))
from rich_http_features import RICH_COLUMNS
from microservice_session_features import FEATURE_COLUMNS
from train_microservice_sessions import choose_threshold, sha
from train_ciciot2023_pilot import binary_metrics, json_clean
from evaluate_microservice_sessions import cluster_intervals

SEED=20261021
NAMES=('logistic','rf','xgb')


def build(name):
    if name=='logistic': return make_pipeline(StandardScaler(),LogisticRegression(C=1.,class_weight='balanced',max_iter=1000,random_state=SEED))
    if name=='rf': return RandomForestClassifier(n_estimators=240,max_depth=8,min_samples_leaf=2,class_weight='balanced',n_jobs=4,random_state=SEED)
    return xgb.XGBClassifier(n_estimators=200,max_depth=4,learning_rate=.05,min_child_weight=4,reg_lambda=4.,
        subsample=.85,colsample_bytree=.85,tree_method='hist',eval_metric='logloss',n_jobs=4,random_state=SEED)


def validate(manifest):
    if manifest['status']!='complete' or tuple(manifest['feature_columns'])!=RICH_COLUMNS:
        raise ValueError('Expected complete, versioned rich-feature collection')
    seen, sessions=set(),set()
    for split,size in (('train',3),('calibration',2),('test',2)):
        peers=set(manifest['splits'][split]['peer_ids'])
        ids={s['session_id'] for s in manifest['splits'][split]['sessions']}
        if len(peers)!=size or peers.intersection(seen) or ids.intersection(sessions): raise ValueError('Peer/session overlap')
        seen.update(peers); sessions.update(ids)


def load(data,manifest,split,columns):
    path=data/f'{split}.json'
    if sha(path)!=manifest['splits'][split]['sha256']: raise ValueError('Partition checksum mismatch')
    rows=json.loads(path.read_text(encoding='utf-8'))
    for r in rows:
        if set(r['features'])!=set(RICH_COLUMNS): raise ValueError('Unexpected predictor/possible leakage')
        if r['target']!=manifest['label_mapping'][r['scenario']]: raise ValueError('Invalid target mapping')
    x=np.array([[r['features'][k] for k in columns] for r in rows],dtype=float)
    y=np.array([r['target'] for r in rows],dtype=int)
    peers=np.array([r['trusted_peer_id'] for r in rows])
    if len(rows)!=manifest['splits'][split]['rows'] or not np.isfinite(x).all() or set(y)!={0,1}:
        raise ValueError('Wrong rows, non-finite data or missing class')
    if set(peers)!=set(manifest['splits'][split]['peer_ids']): raise ValueError('Peer metadata mismatch')
    return rows,x,y,peers


def train(data,output,reference):
    if output.exists(): raise FileExistsError('Frozen rich study already exists')
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8')); validate(manifest)
    output.mkdir(parents=True)
    plan={'run_id':output.name,'created_utc':datetime.now(timezone.utc).isoformat(),
        'script_sha256':sha(__file__),'manifest_sha256':sha(data/'manifest.json'),
        'helper_hashes':{name:sha(Path(__file__).with_name(name)) for name in ('train_microservice_sessions.py','train_ciciot2023_pilot.py','evaluate_microservice_sessions.py')},
        'feature_module_sha256':sha(Path(__file__).resolve().parents[1]/'data/rich_http_features.py'),
        'reference_model_sha256':sha(reference/'candidate.joblib'),'reference_frozen_sha256':sha(reference/'frozen.json'),
        'seed':SEED,'recipe_names':NAMES,
        'parameters':{'rf':build('rf').get_params(),'xgb':build('xgb').get_params(),
                      'logistic':{'C':1.,'class_weight':'balanced','max_iter':1000,'scaler':'StandardScaler'}},
        'feature_sets':{'rich':RICH_COLUMNS,'base':FEATURE_COLUMNS},
        'selection':'For EACH feature set, select three-model mean partial AUC(max_fpr=.05) on leave-one-training-peer-out CV, then separate calibration and freeze.',
        'large_improvement_target':'On fresh matched test: rich accuracy >= old peer model accuracy +10 percentage points, recall >= old +20 points; rich FPR <=5%. Report matched feature ablation too.',
        'strict_quality_gates':'Calibration and fresh test recall >=95%, FPR <=5%. Never automatic production promotion.',
        'privacy':'Credential-context keys use random per-process HMAC, held only in bounded memory; keys/values/digests not exported as predictors.',
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'xgboost':xgb.__version__},
        'automatic_response_enabled':False,'reserved_test_loaded':False,'production_accuracy_claim':False}
    (output/'plan.json').write_text(json.dumps(json_clean(plan),indent=2),encoding='utf-8')
    report={**plan,'sets':{}}
    for feature_set,columns in (('rich',RICH_COLUMNS),('base',FEATURE_COLUMNS)):
        _,x,y,peers=load(data,manifest,'train',columns)
        comparisons={}
        for name in NAMES:
            folds=[]
            for fitting,held in GroupKFold(3).split(x,y,peers):
                assert not set(peers[fitting]).intersection(peers[held])
                model=build(name); model.fit(x[fitting],y[fitting])
                p=model.predict_proba(x[held])[:,1]
                folds.append({'partial_auc':float(roc_auc_score(y[held],p,max_fpr=.05)),
                              'default_metrics':binary_metrics(y[held],p,.5)})
            comparisons[name]={'folds':folds,'mean_partial_auc':float(np.mean([r['partial_auc'] for r in folds]))}
        chosen=max(NAMES,key=lambda n:comparisons[n]['mean_partial_auc'])
        model=build(chosen); model.fit(x,y)
        _,xc,yc,_=load(data,manifest,'calibration',columns)
        calibration,eligible=choose_threshold(yc,model.predict_proba(xc)[:,1])
        joblib.dump({'model':model,'threshold':calibration['threshold'],'feature_columns':columns,'status':'Fresh rich lab study, not deployed'},output/f'{feature_set}.joblib')
        report['sets'][feature_set]={'cv':comparisons,'selected_model':chosen,'calibration':calibration,
            'calibration_eligible':eligible,'model_sha256':sha(output/f'{feature_set}.joblib')}
        print(f'{feature_set} {chosen}: calibration accuracy={calibration["accuracy"]:.4f}, recall={calibration["attack_recall"]:.4f}, FPR={calibration["false_positive_rate"]:.4f}, eligible={eligible}',flush=True)
    (output/'frozen.json').write_text(json.dumps(json_clean(report),indent=2,allow_nan=False),encoding='utf-8')
    print('Both feature sets frozen; fresh final test unopened.')


def evaluate(data,output,reference):
    if (output/'final-test.json').exists() or (output/'test-started.json').exists(): raise FileExistsError('Final evaluation already attempted')
    frozen=json.loads((output/'frozen.json').read_text(encoding='utf-8'))
    checks=[(Path(__file__),frozen['script_sha256']),(data/'manifest.json',frozen['manifest_sha256']),
            (reference/'candidate.joblib',frozen['reference_model_sha256']),(reference/'frozen.json',frozen['reference_frozen_sha256'])]
    checks += [(Path(__file__).with_name(name),digest) for name,digest in frozen['helper_hashes'].items()]
    checks += [(output/f'{name}.joblib',info['model_sha256']) for name,info in frozen['sets'].items()]
    checks += [(Path(__file__).resolve().parents[1]/'data/rich_http_features.py',frozen['feature_module_sha256'])]
    for path,digest in checks:
        if sha(path)!=digest: raise ValueError(f'Frozen dependency changed: {path.name}')
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8')); validate(manifest)
    with (output/'test-started.json').open('x') as stream: json.dump({'frozen_sha256':sha(output/'frozen.json')},stream)
    results={}
    for name,path in (('rich',output/'rich.joblib'),('base',output/'base.joblib'),('old_peer_reference',reference/'candidate.joblib')):
        candidate=joblib.load(path)
        rows,x,y,peers=load(data,manifest,'test',candidate['feature_columns'])
        p=candidate['model'].predict_proba(x)[:,1]; prediction=p>=candidate['threshold']
        results[name]={'metrics':binary_metrics(y,p,candidate['threshold']),
            'peer_cluster_intervals':cluster_intervals(y,prediction,peers),
            'by_scenario':{s:{'samples':sum(r['scenario']==s for r in rows),
                'alert_rate':float(np.mean(prediction[[r['scenario']==s for r in rows]]))} for s in sorted({r['scenario'] for r in rows})}}
    rich,old,base=(results[n]['metrics'] for n in ('rich','old_peer_reference','base'))
    report={'run_id':output.name,'frozen_sha256':sha(output/'frozen.json'),'test_rows':len(rows),
        'test_sessions':len({r['session_id'] for r in rows}),'unseen_peers':len(set(peers)),'results':results,
        'improvement_vs_old':{k:rich[k]-old[k] for k in ('accuracy','macro_f1','attack_recall','false_positive_rate')},
        'improvement_vs_matched_base':{k:rich[k]-base[k] for k in ('accuracy','macro_f1','attack_recall','false_positive_rate')},
        'large_improvement_target_pass':bool(rich['accuracy']>=old['accuracy']+.10 and rich['attack_recall']>=old['attack_recall']+.20 and rich['false_positive_rate']<=.05),
        'strict_quality_gates_pass':bool(frozen['sets']['rich']['calibration_eligible'] and rich['attack_recall']>=.95 and rich['false_positive_rate']<=.05),
        'reserved_test_loaded':True,'promoted':False,'automatic_response_enabled':False,
        'scope':'Fresh real Gateway-to-Auth/H2, eight controlled scenarios, new seed; not production/unknown-attack or external dataset accuracy.',
        'limitations':['One host/generator/run; only two final peers; cluster intervals descriptive only.',
            'Same-format corrupt JWTs, rotation and legitimate refresh broaden the lab, but are not exhaustive adversarial validation.',
            'Contexts can be deliberately churned; aggregate history remains, but no evasion-proof or perfect-security claim.',
            'No current authentication result, token value/digest, account ID or scenario is a predictor.']}
    with (output/'final-test.json').open('x',encoding='utf-8') as stream: json.dump(json_clean(report),stream,indent=2,allow_nan=False)
    print(f'Fresh test rich: accuracy={rich["accuracy"]:.4f}, recall={rich["attack_recall"]:.4f}, FPR={rich["false_positive_rate"]:.4f}; large_gain={report["large_improvement_target_pass"]}; strict_gates={report["strict_quality_gates_pass"]}; no deployment.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('train','evaluate'))
    for arg in ('data','output','reference'): parser.add_argument('--'+arg,type=Path,required=True)
    args=parser.parse_args(); (train if args.stage=='train' else evaluate)(args.data,args.output,args.reference)
