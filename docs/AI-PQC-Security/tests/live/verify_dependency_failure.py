"""One bounded phase of the owned AI/policy outage/recovery experiment; no persisted tokens."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import time
import urllib.request
import uuid
from verify_adaptive_matrix import prototype
from verify_stack import ROOT, operator_test_token, request, require, sql

PHASES={'ai-down':8090,'policy-down':8091,'ai-recovered':None,'policy-recovered':None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=PHASES)
    parser.add_argument('folder',type=Path)
    args=parser.parse_args()
    folder=args.folder.resolve()
    require(folder.is_dir() and folder.parent==(ROOT/'ml/artifacts').resolve(),'Use this runner artifact directory')
    output=folder/f'dependency-{args.phase}.json'
    require(not output.exists(),'Do not overwrite a phase receipt')
    failed=PHASES[args.phase] is not None
    correlation='dependency-'+uuid.uuid4().hex+'-'+args.phase
    result={'schema':'dependency-failure-phase-v1','phase':args.phase,'passed':False,
        'correlation_id':correlation,'role_fixture':'short-lived signed ROLE_USER, no stored token',
        'expected_http':502 if failed else 200,'checks':[]}
    started=time.monotonic()
    def check(name, condition):
        require(condition,'Dependency phase failed: '+name)
        result['checks'].append(name)
    try:
        if failed:
            with socket.socket() as probe:
                probe.settimeout(1)
                check('failed_dependency_port_unreachable',probe.connect_ex(('127.0.0.1',PHASES[args.phase]))!=0)
        if args.phase=='policy-down':
            with urllib.request.urlopen('http://127.0.0.1:8090/health',timeout=3) as response:
                check('ai_remains_healthy',json.load(response).get('status')=='UP')
        body={**prototype(),'dataSensitivity':'RESTRICTED','hybridSupported':True,'pqcSupported':True,'maxCryptoLatencyMillis':100}
        before=time.perf_counter()
        status,reply=request('/api/v1/business/adaptive-secure-data',body=body,
            token=operator_test_token('ROLE_USER'),correlation=correlation)
        result['observed_http_ms']=round((time.perf_counter()-before)*1000,3)
        result['actual_http']=status
        check('expected_http',status==result['expected_http'])
        raw=sql("SELECT JSON_OBJECT('executionId',execution_id,'decisionId',decision_id,'mode',selected_mode,"
            "'outcome',outcome,'verified',CAST(round_trip_verified AS UNSIGNED),'cryptoMillis',crypto_latency_millis,"
            "'payloadSha',payload_sha256,'errorDetail',error_detail) FROM pqc_business_db.crypto_executions "
            f"WHERE correlation_id='{correlation}';")
        check('one_execution_audit',len(raw.splitlines())==1)
        audit=json.loads(raw)
        check('payload_fingerprint',audit['payloadSha']==hashlib.sha256(body['data'].encode()).hexdigest())
        decisions=int(sql(f"SELECT COUNT(*) FROM pqc_policy_db.policy_decisions WHERE correlation_id='{correlation}';"))
        check('expected_policy_persistence',decisions==(0 if failed else 1))
        if failed:
            check('generic_dependency_failure',reply.get('message')=='Adaptive security dependency failed')
            check('generic_persisted_dependency_reason',audit['errorDetail']=='Adaptive security dependency failed')
            check('no_encrypted_success_response',not reply.get('encryptedPayload') and not reply.get('roundTripVerified'))
            check('failed_without_crypto_or_decision',audit['outcome']=='FAILED' and audit['verified']==0
                and audit['mode'] is None and audit['decisionId'] is None and audit['cryptoMillis']==0)
        else:
            check('no_failure_reason_after_recovery',audit['errorDetail'] is None)
            check('verified_pqc_after_recovery',reply.get('selectedMode')=='PQC' and reply.get('roundTripVerified') is True
                and bool(reply.get('encryptedPayload')) and reply.get('executionId')==audit['executionId']
                and reply.get('decisionId')==audit['decisionId'] and audit['outcome']=='SUCCESS' and audit['verified']==1)
        read_status,records=request('/api/v1/business/executions',token=operator_test_token('ROLE_USER'))
        matching=[row for row in records if row.get('executionId')==audit['executionId']] if isinstance(records,list) else []
        check('matching_safe_read_api_reason',read_status==200 and len(matching)==1 and
              matching[0].get('errorDetail')==('Adaptive security dependency failed' if failed else None))
        deadline=time.monotonic()+15
        while True:
            event=sql(f"SELECT event_type,outcome FROM pqc_monitoring_db.security_events WHERE correlation_id='{correlation}';")
            if event:break
            require(time.monotonic()<deadline,'Timed out waiting for dependency outcome event')
            time.sleep(.25)
        check('matching_monitoring_event',event==('API_ACCESS_DENIED\tFAILURE' if failed else 'API_ACCESS_GRANTED\tSUCCESS'))
        result.update(passed=True,execution_id=audit['executionId'],decision_id=audit['decisionId'])
    except Exception as error:
        result['error']=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        raise
    finally:
        result['seconds']=round(time.monotonic()-started,2)
        with output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print('Verified owned dependency phase '+args.phase+'; outcome and event persisted; no credentials/envelope saved.')


if __name__=='__main__':main()
