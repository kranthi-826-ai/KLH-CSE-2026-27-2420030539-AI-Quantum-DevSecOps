"""Bounded loopback live checks, including direct MySQL rows; never dumps tokens/secrets."""
import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]


def request(path, *, body=None, token=None, key=None, correlation=None, port=8080):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if key:
        headers["X-Internal-API-Key"] = key
    if correlation:
        headers["X-Correlation-ID"] = correlation
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode() if body is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, {}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sql(query):
    binary = Path(r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe")
    require(binary.is_file(), "MySQL CLI unavailable for direct persistence verification")
    environment = {**os.environ, "MYSQL_PWD": os.environ["DB_PASSWORD"]}
    result = subprocess.run([str(binary), "--host=127.0.0.1", "--port=3306", "--user=root", "--batch", "--skip-column-names", "--execute", query], env=environment, capture_output=True, text=True, timeout=10)
    require(result.returncode == 0, "Direct MySQL read failed; no secret or CLI stderr is included")
    return result.stdout.strip()


def operator_test_token(role='ROLE_ADMIN'):
    """Short-lived operator fixture using this isolated run's signing key, never saved."""
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).rstrip(b'=')
    unsigned = encode({'alg': 'HS256', 'typ': 'JWT'}) + b'.' + encode({
        'sub': 'local-verification-operator', 'role': role, 'exp': int(time.time()) + 60})
    signature = hmac.new(os.environ['JWT_SECRET'].encode(), unsigned, hashlib.sha256).digest()
    return (unsigned + b'.' + base64.urlsafe_b64encode(signature).rstrip(b'=')).decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "Refusing to overwrite live evidence")
    run_id = uuid.uuid4().hex
    username = f"live_{run_id[:12]}"
    password = secrets.token_urlsafe(24)
    evidence = {"schema": "live-stack-verification-v1", "run_id": run_id, "checks": [],
                "scope": "Real local services and MySQL, demonstration fixtures not ML evaluation", "passed": False}
    def check(name, condition):
        require(condition, f"Live check failed: {name}")
        evidence["checks"].append(name)
    try:
        # Fail early before creating test records if database access is invalid.
        check("direct_mysql_connection", sql("SELECT 1;") == "1")
        for _ in range(30):
            status, _ = request('/api/v1/business/secure-data')
            if status not in (502, 503):
                break
            time.sleep(2)
        check("anonymous_business_rejected", status == 401)
        status, _ = request('/api/v1/events')
        check("anonymous_events_rejected", status == 401)
        # Eureka-to-gateway propagation is asynchronous; wait only for route availability.
        for _ in range(30):
            status, _ = request('/api/v1/auth/register', body={"username":username,"password":password})
            if status not in (502, 503):
                break
            time.sleep(2)
        check("gateway_registration", status == 201)
        status, _ = request('/api/v1/auth/login', body={"username":username,"password":"incorrect-test-password"})
        check("wrong_password_rejected", status == 401)
        status, logged_in = request('/api/v1/auth/login', body={"username":username,"password":password})
        token = logged_in.get('token')
        check("gateway_login", status == 200 and isinstance(token, str) and bool(token))
        status, current = request('/api/v1/auth/me', token=token)
        check("authenticated_identity", status == 200 and current.get('username') == username)
        status, _ = request('/api/v1/business/secure-data', token=token + 'tampered')
        check("tampered_jwt_rejected", status == 401)
        # A healthy HTTP listener is not proof that this publisher's discovery
        # cache contains monitoring. Confirm a real routed event before testing
        # the adaptive flow. Startup event loss remains a separate reliability gap.
        readiness_correlation = f"live-{run_id}-event-readiness"
        event_ready = False
        for _ in range(20):
            request('/api/v1/business/secure-data', token=token, correlation=readiness_correlation)
            status, seen_events = request('/api/v1/events', token=token, port=8083)
            if status == 200 and any(r.get('correlationId') == readiness_correlation for r in seen_events):
                event_ready = True
                break
            time.sleep(2)
        check("real_event_pipeline_ready", event_ready)
        raw = (ROOT / 'tests/e2e/bruno/AI-PQC-Security/Adaptive_Secure_Data.bru').read_text()
        prototype, _ = json.JSONDecoder().raw_decode(raw.split('body:json {', 1)[1].lstrip())
        successful = []
        evidence['executions'] = successful
        for name, sensitivity, pqc, hybrid, expected in (
            ('pqc', 'RESTRICTED', True, True, 'PQC'),
            ('hybrid', 'RESTRICTED', False, True, 'HYBRID'),
            ('classical', 'PUBLIC', False, False, 'CLASSICAL'),
        ):
            correlation = f"live-{run_id}-{name}"
            body = {**prototype, 'dataSensitivity':sensitivity, 'pqcSupported':pqc, 'hybridSupported':hybrid}
            started = time.perf_counter()
            status, result = request('/api/v1/business/adaptive-secure-data', body=body, token=token, correlation=correlation)
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            check(f"{name}_verified_envelope", status == 200 and result.get('selectedMode') == expected and result.get('roundTripVerified') is True and result.get('correlationId') == correlation and bool(result.get('encryptedPayload')))
            successful.append({k:result[k] for k in ('executionId','decisionId','correlationId','selectedMode','riskLevel','riskScore','modelVersion','policyVersion','policyLatencyMillis','cryptoLatencyMillis','totalLatencyMillis')})
            successful[-1]['observed_http_millis'] = elapsed
            row = sql(f"SELECT selected_mode,CAST(round_trip_verified AS UNSIGNED),outcome FROM pqc_business_db.crypto_executions WHERE execution_id='{result['executionId']}';")
            check(f"{name}_mysql_execution", row == f"{expected}\t1\tSUCCESS")
        correlation = f"live-{run_id}-downgrade"
        status, _ = request('/api/v1/business/adaptive-secure-data', body={**prototype,'dataSensitivity':'RESTRICTED','pqcSupported':False,'hybridSupported':False}, token=token, correlation=correlation)
        check("high_risk_classical_downgrade_rejected", status == 422)
        status, executions = request('/api/v1/business/executions', token=token)
        check("dashboard_execution_api", status == 200 and {r['executionId'] for r in successful}.issubset({r['executionId'] for r in executions}))
        correlations = {r['correlationId'] for r in successful}
        for _ in range(15):
            status, events = request('/api/v1/events', token=token)
            if status == 200 and correlations.issubset({r.get('correlationId') for r in events}):
                break
            time.sleep(2)
        check("dashboard_event_api", status == 200 and correlations.issubset({r.get('correlationId') for r in events}))
        check("mysql_audit_events", int(sql(f"SELECT COUNT(*) FROM pqc_monitoring_db.security_events WHERE username='{username}';")) >= 4)
        check("bcrypt_not_plaintext", sql(f"SELECT LEFT(password_hash,4) FROM pqc_auth_db.users WHERE username='{username}';") in ('$2a$', '$2b$', '$2y$'))
        status, _ = request('/api/v1/policies/decisions', port=8091)
        check("internal_policy_key_required", status == 401)
        check("user_execution_records_are_own", bool(executions) and all(r.get('username') == username for r in executions))
        check("user_event_records_are_own", bool(events) and all(r.get('username') == username for r in events))
        second_user = 'other_' + run_id[:12]
        status, registered = request('/api/v1/auth/register', body={
            'username': second_user, 'password': password, 'role': 'ROLE_ADMIN'})
        check("registration_cannot_assign_admin", status == 201 and registered.get('role') == 'ROLE_USER'
              and sql(f"SELECT role FROM pqc_auth_db.users WHERE username='{second_user}';") == 'ROLE_USER')
        status, second_login = request('/api/v1/auth/login', body={'username': second_user, 'password': password})
        check("second_user_login", status == 200 and second_login.get('role') == 'ROLE_USER' and bool(second_login.get('token')))
        second_token = second_login['token']
        status, other_runs = request('/api/v1/business/executions?username=' + username + '&role=ROLE_ADMIN', token=second_token)
        check("cross_user_execution_query_denied", status == 200 and other_runs == [])
        status, other_events = request('/api/v1/events?username=' + username + '&role=ROLE_ADMIN', token=second_token)
        check("cross_user_event_query_denied", status == 200 and isinstance(other_events, list)
              and all(r.get('username') == second_user for r in other_events))
        operator = operator_test_token()
        status, operator_runs = request('/api/v1/business/executions', token=operator)
        check("signed_operator_execution_view", status == 200 and {r['executionId'] for r in successful}.issubset(
              {r.get('executionId') for r in operator_runs}))
        status, operator_events = request('/api/v1/events', token=operator)
        check("signed_operator_event_view", status == 200 and any(r.get('username') == username for r in operator_events))
        for producer in ('auth', 'business'):
            path = f'/api/v1/{producer}/audit-outbox'
            status, _ = request(path, token=token)
            check(f"{producer}_outbox_user_denied", status == 403)
            status, summary = request(path, token=operator)
            check(f"{producer}_outbox_admin_summary", status == 200 and isinstance(summary.get('recentDead'), list)
                  and all(isinstance(summary.get(field), (int, float)) and summary[field] >= 0
                          for field in ('pending', 'dead', 'delivered', 'oldestPendingEventAgeSeconds')))
            metrics_port = 8081 if producer == 'auth' else 8082
            with urllib.request.urlopen(f'http://127.0.0.1:{metrics_port}/actuator/prometheus', timeout=5) as metrics:
                metrics_text = metrics.read(2_000_000).decode()
            check(f"{producer}_outbox_metrics_exported", 'audit_outbox_oldest_pending_event_age_seconds' in metrics_text
                  and 'audit_outbox_records' in metrics_text and 'status="DEAD"' in metrics_text)
        for guarded_port in (8080, 8081, 8082, 8083, 8091):
            status, rejected = request('/api/v1/input-boundary-probe', correlation='x' * 81, port=guarded_port)
            check(f"invalid_correlation_rejected_{guarded_port}", status == 400 and rejected.get('message') == 'Invalid correlation ID')
        status, _ = request('/api/v1/auth/me', token=token, correlation='a' * 80)
        check("maximum_safe_correlation_accepted", status == 200)
        status, rejected = request('/api/v1/auth/login', body={'data': 'x' * 262144})
        check("oversized_json_body_rejected", status == 413 and rejected.get('status') == 413)
        status, rejected = request('/api/v1/auth/login', body={'username': 'x' * 51, 'password': 'invalid-secret-marker'})
        check("oversized_login_identity_rejected", status == 400 and 'invalid-secret-marker' not in json.dumps(rejected))
        status, rejected = request('/api/v1/auth/register', body={'username': 'unicode_' + run_id[:12], 'password': 'é' * 37})
        check("bcrypt_utf8_byte_limit_enforced", status == 400 and 'é' not in json.dumps(rejected, ensure_ascii=False))
        evidence.update(passed=True, executions=successful, created_test_username=username,
                        retained_test_records=True, tokens_and_passwords_recorded=False)
    except Exception as error:
        evidence['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(evidence, handle, indent=2)
    print(f"Passed {len(evidence['checks'])} live checks; no tokens/passwords saved.")


if __name__ == '__main__':
    main()
