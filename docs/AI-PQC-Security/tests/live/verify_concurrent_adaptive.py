"""Bounded four-client mixed adaptive requests; not a throughput or accuracy benchmark."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time
import uuid
from verify_stack import ROOT, request, require, sql
from verify_adaptive_matrix import MODEL_SHA, PROFILES, prototype

# Each batch deliberately mixes all modes with an incompatible HIGH-risk denial.
CASES = (
    ('classical', 'PUBLIC', False, False, 'MEDIUM', 'CLASSICAL', 200),
    ('hybrid', 'PUBLIC', True, True, 'MEDIUM', 'HYBRID', 200),
    ('pqc', 'RESTRICTED', True, True, 'HIGH', 'PQC', 200),
    ('denied', 'RESTRICTED', False, False, 'HIGH', 'CLASSICAL', 422),
)
BATCHES = 6
WORKERS = 4


def peak_overlap(rows):
    events = [(row['start_ms'], 1) for row in rows] + [(row['end_ms'], -1) for row in rows]
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    return peak


def verify_audits(rows, executions, policies, events, username):
    """Bind every response to exactly one persisted execution/decision/event."""
    require(len(rows) == len(executions) == len(policies) == len(events) == BATCHES * WORKERS,
            'Missing or duplicated concurrent audit rows')
    correlations = {row['correlation_id'] for row in rows}
    require(len(correlations) == len(rows), 'Reused request correlation')
    for records in (executions, policies, events):
        require({row['correlation'] for row in records} == correlations, 'Audit request identities differ')
    execution_map = {row['correlation']: row for row in executions}
    policy_map = {row['correlation']: row for row in policies}
    event_map = {row['correlation']: row for row in events}
    require(len({row['executionId'] for row in executions}) == len(rows), 'Reused execution identity')
    require(len({row['decisionId'] for row in policies}) == len(rows), 'Reused decision identity')
    require(len({row['eventId'] for row in events}) == len(rows), 'Reused event identity')
    payload_hash = hashlib.sha256(prototype()['data'].encode()).hexdigest()
    for row in rows:
        audit, policy, event = (mapping[row['correlation_id']] for mapping in (execution_map, policy_map, event_map))
        success = row['expected_http'] == 200
        require(audit['username'] == event['username'] == username and
                audit['decisionId'] == policy['decisionId'] and
                audit['mode'] == policy['mode'] == row['expected_mode'] and
                audit['risk'] == policy['risk'] == row['expected_risk'] and
                policy['inputRisk'] == 'MEDIUM' and policy['sensitivity'] == row['sensitivity'] and
                audit['modelVersion'] == policy['modelVersion'] == MODEL_SHA[:16] and
                audit['policyVersion'] == policy['policyVersion'] == '1.1.0' and
                audit['payloadHash'] == payload_hash and
                audit['outcome'] == ('SUCCESS' if success else 'FAILED') and
                audit['verified'] == int(success) and
                event['outcome'] == ('SUCCESS' if success else 'FAILURE') and
                event['eventType'] == ('API_ACCESS_GRANTED' if success else 'API_ACCESS_DENIED') and
                abs(audit['score'] - 0.5690423129295029) < 1e-12,
                'Concurrent response/audit data crossed requests or violated expected policy')
        if success:
            require(row['execution_id'] == audit['executionId'] and row['decision_id'] == policy['decisionId'],
                    'Successful response identity differs from its own audit')
        else:
            require(audit['cryptoMillis'] == 0, 'Denied request performed cryptographic work')
        row.update(execution_id=audit['executionId'], decision_id=policy['decisionId'], audit_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output.resolve()
    require(not output.exists() and output.parent.parent == (ROOT / 'ml/artifacts').resolve(),
            'Require a new receipt inside a project artifact directory')
    require(hashlib.sha256((ROOT / 'ml/models/promoted/model.joblib').read_bytes()).hexdigest() == MODEL_SHA,
            'Promoted model differs; review and refreeze the experiment')
    run_id = uuid.uuid4().hex
    username, password = 'concurrent_' + run_id[:16], secrets.token_urlsafe(24)
    started = time.monotonic()
    result = {'schema': 'concurrent-adaptive-v1', 'passed': False, 'rows': [], 'workers': WORKERS,
              'batches': BATCHES, 'model_sha256': MODEL_SHA, 'payload_bytes': 4096,
              'case_manifest_sha256': hashlib.sha256(json.dumps(CASES, separators=(',', ':')).encode()).hexdigest(),
              'scope': 'Bounded client overlap and request/audit isolation; not server parallelism, throughput, ML accuracy or a deployment SLA'}
    try:
        code, _ = request('/api/v1/auth/register', body={'username': username, 'password': password})
        require(code == 201, 'Concurrent fixture registration failed')
        code, login = request('/api/v1/auth/login', body={'username': username, 'password': password})
        require(code == 200 and login.get('token'), 'Concurrent fixture login failed')
        token = login['token']
        base = prototype()

        def invoke(batch, case, barrier):
            name, sensitivity, hybrid, pqc, risk, mode, expected = case
            correlation = f'concurrent-{run_id}-{batch}-{name}'
            body = {**base, 'dataSensitivity': sensitivity, 'hybridSupported': hybrid,
                    'pqcSupported': pqc, 'maxCryptoLatencyMillis': 100}
            barrier.wait(timeout=5)
            begin = time.monotonic()
            status, response = request('/api/v1/business/adaptive-secure-data', body=body,
                                       token=token, correlation=correlation)
            end = time.monotonic()
            row = {'batch': batch, 'case': name, 'correlation_id': correlation, 'sensitivity': sensitivity,
                   'expected_http': expected, 'actual_http': status, 'expected_mode': mode, 'expected_risk': risk,
                   'start_ms': round((begin-started)*1000, 3), 'end_ms': round((end-started)*1000, 3),
                   'http_ms': round((end-begin)*1000, 3), 'passed': False}
            require(status == expected, 'Unexpected concurrent request HTTP status')
            if expected == 200:
                require(response.get('correlationId') == correlation and response.get('selectedMode') == mode and
                        response.get('riskLevel') == risk and response.get('algorithmProfile') == PROFILES[mode] and
                        response.get('roundTripVerified') is True and response.get('modelVersion') == MODEL_SHA[:16] and
                        len(base64.b64decode(response['encryptedPayload'], validate=True)) == 4112 and
                        len(base64.b64decode(response['nonce'], validate=True)) == 12,
                        'Concurrent envelope response differs from its request')
                row.update(execution_id=response['executionId'], decision_id=response['decisionId'])
            else:
                require(not response.get('encryptedPayload') and not response.get('roundTripVerified') and
                        'High-risk operation denied' in response.get('message', ''),
                        'Concurrent denied request returned protection')
            row['passed'] = True
            return row

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for batch in range(BATCHES):
                require(time.monotonic()-started < 90, 'Concurrent submission deadline exceeded')
                barrier = threading.Barrier(WORKERS)
                # Rotate submission order; client intervals, not server thread timings, are measured.
                order = CASES[batch % WORKERS:] + CASES[:batch % WORKERS]
                futures = [pool.submit(invoke, batch, case, barrier) for case in order]
                failures = []
                for future in futures:
                    try:
                        result['rows'].append(future.result())
                    except Exception as error:
                        failures.append(type(error).__name__)
                require(not failures, 'Concurrent batch failed; no raw response or credentials recorded')
                require(peak_overlap([row for row in result['rows'] if row['batch'] == batch]) >= 2,
                        'No actual overlapping client request intervals observed')
        http_finished = time.monotonic()
        query_tail = f" WHERE username='{username}' AND request_path='/api/v1/business/adaptive-secure-data';"
        while int(sql('SELECT COUNT(*) FROM pqc_monitoring_db.security_events' + query_tail)) != 24:
            require(time.monotonic()-http_finished < 20, 'Concurrent monitoring delivery deadline exceeded')
            time.sleep(.5)

        def records(query):
            raw = sql(query)
            return [json.loads(line) for line in raw.splitlines()] if raw else []

        executions = records("SELECT JSON_OBJECT('correlation',correlation_id,'username',username,'executionId',execution_id,"
            "'decisionId',decision_id,'mode',selected_mode,'risk',risk_level,'score',risk_score,'modelVersion',model_version,"
            "'policyVersion',policy_version,'payloadHash',payload_sha256,'outcome',outcome,"
            "'verified',CAST(round_trip_verified AS UNSIGNED),'cryptoMillis',crypto_latency_millis)"
            f" FROM pqc_business_db.crypto_executions WHERE username='{username}';")
        policies = records("SELECT JSON_OBJECT('correlation',correlation_id,'decisionId',decision_id,'mode',selected_mode,"
            "'risk',effective_risk_level,'inputRisk',input_risk_level,'sensitivity',data_sensitivity,"
            "'modelVersion',model_version,'policyVersion',policy_version) FROM pqc_policy_db.policy_decisions"
            f" WHERE correlation_id LIKE 'concurrent-{run_id}-%';")
        events = records("SELECT JSON_OBJECT('correlation',correlation_id,'eventId',event_id,'username',username,"
            "'outcome',outcome,'eventType',event_type) FROM pqc_monitoring_db.security_events" + query_tail)
        verify_audits(result['rows'], executions, policies, events, username)
        result.update(passed=True, successful_crypto_executions=18, fail_closed_requests=6,
                      matching_audits=24, client_overlap_by_batch=[peak_overlap([row for row in result['rows']
                      if row['batch'] == batch]) for batch in range(BATCHES)])
    except Exception as error:
        result['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise
    finally:
        result['seconds'] = round(time.monotonic()-started, 2)
        with output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
    print('Verified24 bounded concurrent requests and matching policy/execution/event audits; not a load-capacity benchmark.')


if __name__ == '__main__':
    main()
