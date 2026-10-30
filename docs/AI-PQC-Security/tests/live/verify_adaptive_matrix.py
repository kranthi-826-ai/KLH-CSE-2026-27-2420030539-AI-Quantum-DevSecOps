"""Frozen bounded live adaptive-policy matrix; synthetic API evidence, not ML accuracy."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import secrets
import time
import uuid
from verify_stack import ROOT, request, require, sql

MODEL_SHA='c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39'
PROFILES={'CLASSICAL':'X25519+AES-256-GCM+ECDSA-P256',
          'HYBRID':'X-Wing+AES-256-GCM+ML-DSA-65','PQC':'ML-KEM-768+AES-256-GCM+ML-DSA-65'}
# name, sensitivity, hybrid, pqc, selection threshold ms, effective risk, selected mode, HTTP
CASES=(
 ('medium_public','PUBLIC',True,True,100,'MEDIUM','HYBRID',200),
 ('medium_hybrid_boundary','PUBLIC',True,False,8,'MEDIUM','HYBRID',200),
 ('medium_below_hybrid','PUBLIC',True,True,7,'MEDIUM','CLASSICAL',200),
 ('medium_pqc_only','PUBLIC',False,True,100,'MEDIUM','CLASSICAL',200),
 ('internal_medium','INTERNAL',True,True,100,'MEDIUM','HYBRID',200),
 ('confidential_elevates','CONFIDENTIAL',True,True,100,'HIGH','PQC',200),
 ('restricted_pqc_boundary','RESTRICTED',True,True,15,'HIGH','PQC',200),
 ('restricted_below_pqc','RESTRICTED',True,True,14,'HIGH','HYBRID',200),
 ('restricted_hybrid_boundary','RESTRICTED',True,True,8,'HIGH','HYBRID',200),
 ('restricted_too_tight','RESTRICTED',True,True,7,'HIGH','CLASSICAL',422),
 ('restricted_pqc_too_tight','RESTRICTED',False,True,14,'HIGH','CLASSICAL',422),
 ('restricted_incompatible','RESTRICTED',False,False,100,'HIGH','CLASSICAL',422),
 ('restricted_hybrid_only','RESTRICTED',True,False,100,'HIGH','HYBRID',200),
 ('restricted_pqc_only','RESTRICTED',False,True,15,'HIGH','PQC',200),
 ('medium_zero_threshold','PUBLIC',False,False,0,'MEDIUM','CLASSICAL',200),
 ('confidential_incompatible','CONFIDENTIAL',False,False,100,'HIGH','CLASSICAL',422),
)


def prototype():
    raw=(ROOT/'tests/e2e/bruno/AI-PQC-Security/Adaptive_Secure_Data.bru').read_text()
    body,_=json.JSONDecoder().raw_decode(raw.split('body:json {',1)[1].lstrip())
    body['data']=('synthetic-research-fixture-'*200)[:4096]
    return body


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    require(not output.exists() and output.parent.parent==(ROOT/'ml/artifacts').resolve(),
            'Use a new receipt inside a project artifact run directory')
    model_hash=hashlib.sha256((ROOT/'ml/models/promoted/model.joblib').read_bytes()).hexdigest()
    require(model_hash==MODEL_SHA,'Promoted model differs from frozen matrix; review/refreeze before running')
    run_id=uuid.uuid4().hex
    username='matrix_'+run_id[:16]
    password=secrets.token_urlsafe(24)
    result={'schema':'adaptive-live-matrix-v1','passed':False,'rows':[],
        'model_sha256':model_hash,'scope':'Synthetic same-flow sensitivity/compatibility/threshold checks; no ML accuracy claim',
        'case_count':16,'repeats':2,'maximum_seconds':90,'payload_bytes':4096,
        'case_manifest_sha256':hashlib.sha256(json.dumps(CASES,separators=(',',':')).encode()).hexdigest(),
        'feature_fixture_sha256':hashlib.sha256(json.dumps(prototype()['networkFeatures'],sort_keys=True).encode()).hexdigest()}
    started=time.monotonic()
    try:
        code,_=request('/api/v1/auth/register',body={'username':username,'password':password})
        require(code==201,'Matrix account registration failed')
        code,login=request('/api/v1/auth/login',body={'username':username,'password':password})
        require(code==200 and login.get('token'),'Matrix account login failed')
        token=login['token'];base=prototype();score=None
        for repeat in range(2):
            for name,sensitivity,hybrid,pqc,budget,risk,mode,expected_status in CASES:
                require(time.monotonic()-started<90,'Matrix deadline exceeded')
                correlation=f'matrix-{run_id}-{repeat}-{name}'
                require(len(correlation)<=80,'Fixture correlation exceeds API boundary')
                body={**base,'dataSensitivity':sensitivity,'hybridSupported':hybrid,
                      'pqcSupported':pqc,'maxCryptoLatencyMillis':budget}
                before=time.perf_counter()
                status,response=request('/api/v1/business/adaptive-secure-data',body=body,token=token,correlation=correlation)
                elapsed=(time.perf_counter()-before)*1000
                row={'case':name,'repeat':repeat,'correlation_id':correlation,'expected_http':expected_status,
                    'actual_http':status,'expected_mode':mode,'expected_effective_risk':risk,
                    'selection_threshold_ms':budget,'observed_http_ms':round(elapsed,3),'passed':False}
                result['rows'].append(row)
                require(status==expected_status,f'{name}: unexpected HTTP status')
                raw=sql("SELECT JSON_OBJECT('executionId',execution_id,'decisionId',decision_id,'selectedMode',selected_mode,"
                    "'riskLevel',risk_level,'riskScore',risk_score,'modelVersion',model_version,'policyVersion',policy_version,"
                    "'outcome',outcome,'verified',CAST(round_trip_verified AS UNSIGNED),'cryptoMillis',crypto_latency_millis,"
                    "'totalMillis',total_latency_millis) FROM pqc_business_db.crypto_executions "
                    f"WHERE correlation_id='{correlation}' AND username='{username}';")
                require(raw and len(raw.splitlines())==1,f'{name}: exactly one execution audit required')
                audit=json.loads(raw)
                require(audit['selectedMode']==mode and audit['riskLevel']==risk and
                    audit['modelVersion']==MODEL_SHA[:16] and audit['policyVersion']=='1.1.0',f'{name}: execution audit mismatch')
                if score is None:score=audit['riskScore']
                require(abs(audit['riskScore']-score)<1e-12,f'{name}: unchanged flow produced a different model score')
                policy=json.loads(sql("SELECT JSON_OBJECT('decisionId',decision_id,'inputRisk',input_risk_level,"
                    "'effectiveRisk',effective_risk_level,'mode',selected_mode,'profile',algorithm_profile,"
                    "'sensitivity',data_sensitivity,'threshold',max_crypto_latency_millis) FROM pqc_policy_db.policy_decisions "
                    f"WHERE correlation_id='{correlation}';"))
                require(policy=={'decisionId':audit['decisionId'],'inputRisk':'MEDIUM','effectiveRisk':risk,
                    'mode':mode,'profile':PROFILES[mode],'sensitivity':sensitivity,'threshold':budget},f'{name}: policy audit mismatch')
                if expected_status==200:
                    require(response.get('selectedMode')==mode and response.get('riskLevel')==risk and
                        response.get('algorithmProfile')==PROFILES[mode] and response.get('roundTripVerified') is True and
                        response.get('executionId')==audit['executionId'] and response.get('decisionId')==audit['decisionId'] and
                        response.get('correlationId')==correlation and audit['outcome']=='SUCCESS' and audit['verified']==1,
                        f'{name}: successful envelope/audit mismatch')
                    require(len(base64.b64decode(response['encryptedPayload'],validate=True))==4112 and
                        len(base64.b64decode(response['nonce'],validate=True))==12,f'{name}: payload boundary mismatch')
                    row['observed_crypto_ms']=audit['cryptoMillis']
                    row['observed_recorded_total_ms']=audit['totalMillis']
                    row['crypto_above_selection_threshold']=audit['cryptoMillis']>budget
                else:
                    require(audit['outcome']=='FAILED' and audit['verified']==0 and not response.get('encryptedPayload') and
                        'High-risk operation denied' in response.get('message',''),f'{name}: denial executed/returned protection')
                row.update(passed=True,execution_id=audit['executionId'],decision_id=audit['decisionId'],risk_score=audit['riskScore'])
        # Producer/receiver are asynchronous; require every outcome in both stores.
        while True:
            delivered=int(sql(f"SELECT COUNT(DISTINCT correlation_id) FROM pqc_monitoring_db.security_events WHERE username='{username}' AND request_path='/api/v1/business/adaptive-secure-data';"))
            if delivered==32:break
            require(time.monotonic()-started<90,'Not every scenario reached the monitoring audit within deadline')
            time.sleep(.5)
        require(sql(f"SELECT outcome,COUNT(*) FROM pqc_monitoring_db.security_events WHERE username='{username}' AND request_path='/api/v1/business/adaptive-secure-data' GROUP BY outcome ORDER BY outcome;").splitlines()==['FAILURE\t8','SUCCESS\t24'],
            'Monitoring outcomes do not match successful/denied scenario counts')
        result.update(passed=True,monitoring_correlation_count=delivered,
            successful_crypto_executions=24,fail_closed_requests=8,
            successful_crypto_above_threshold=sum(row.get('crypto_above_selection_threshold',False) for row in result['rows']))
    except Exception as error:
        result['error']=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        raise
    finally:
        result['seconds']=round(time.monotonic()-started,2)
        with output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print('Verified32 frozen live adaptive scenarios and matching MySQL decision/execution/event audits; not a detection-accuracy benchmark.')


if __name__=='__main__':main()
