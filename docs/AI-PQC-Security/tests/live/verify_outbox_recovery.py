"""Real MySQL audit recovery across an owned producer restart and Monitoring outage."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import uuid
from verify_stack import request, require, sql, operator_test_token


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def state(folder):
    saved = json.loads((folder / 'outage-prepared.json').read_text())
    uuid.UUID(saved['event_id'])
    require(bool(re.fullmatch(r'outage_[0-9a-f]{16}', saved['username'])), 'Invalid recovery evidence identity')
    return saved


def run(args):
    if args.phase == 'prepare':
        try:
            with urllib.request.urlopen('http://127.0.0.1:8083/actuator/health', timeout=2):
                raise RuntimeError('Monitoring must actually be stopped before this probe')
        except urllib.error.URLError:
            pass
        username = 'outage_' + uuid.uuid4().hex[:16]
        status, _ = request('/api/v1/auth/login', body={'username':username, 'password':'not-a-real-account-password'}, port=8081)
        require(status == 401, 'Probe must exercise failed authentication, not bypass it')
        rows = sql(f"SELECT event_id,status FROM pqc_auth_db.audit_outbox WHERE username='{username}';").splitlines()
        require(len(rows) == 1, 'Expected one durable audit event during Monitoring outage')
        event_id, status = rows[0].split('\t')
        require(status == 'PENDING', 'Event must be pending while Monitoring is stopped')
        write(args.folder / 'outage-prepared.json', {'event_id':event_id, 'username':username,
              'monitoring_unreachable':True, 'producer_response':401, 'status_before_restart':status,
              'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print('Confirmed durable pending event while Monitoring is stopped; no credentials recorded.')
        return
    saved = state(args.folder)
    event_id = saved['event_id']
    if args.phase == 'replay':
        # Only this run's newly created synthetic outage event may be changed.
        require((args.folder / 'outage-after-restart.json').is_file(), 'Restart proof required before replay fixture')
        changed = sql(f"UPDATE pqc_auth_db.audit_outbox SET status='DEAD',last_error_code='DELIVERY_UNAVAILABLE' WHERE event_id='{event_id}' AND username='{saved['username']}' AND event_type='LOGIN_FAILED' AND status='PENDING'; SELECT ROW_COUNT();")
        require(changed == '1', 'Synthetic replay fixture must change exactly one newly prepared pending event')
        body = {'eventId': event_id, 'reason': 'RESTORED_DEPENDENCY'}
        path = '/api/v1/auth/audit-outbox/replay'
        status, _ = request(path, body=body, token=operator_test_token('ROLE_USER'), port=8081)
        require(status == 403, 'Ordinary user must not preview or replay dead audit records')
        operator = operator_test_token()
        status, preview = request(path, body=body, token=operator, port=8081)
        require(status == 200 and preview.get('applied') is False, 'Omitting apply must be a nonmutating preview')
        require(sql(f"SELECT status FROM pqc_auth_db.audit_outbox WHERE event_id='{event_id}';") == 'DEAD', 'Preview changed queue state')
        require(sql(f"SELECT COUNT(*) FROM pqc_auth_db.audit_outbox_replay_log WHERE event_id='{event_id}';") == '0', 'Preview created a replay operation')
        status, applied = request(path, body={**body, 'apply': True}, token=operator, port=8081)
        require(status == 200 and applied.get('applied') is True, 'Explicit authorized replay was not accepted')
        status, _ = request(path, body={**body, 'apply': True}, token=operator, port=8081)
        require(status == 409, 'Already pending event must not be requeued a second time')
        require(sql(f"SELECT COUNT(*) FROM pqc_auth_db.audit_outbox_replay_log WHERE event_id='{event_id}';") == '1', 'Expected exactly one durable replay operation')
        write(args.folder / 'outage-replay-verification.json', {'schema':'outbox-replay-v1', 'passed':True,
              'event_id':event_id, 'fixture':'Only this new synthetic event was manually marked DEAD; not natural retry exhaustion',
              'ordinary_user_status':403,'dry_run_mutated':False,'replay_applied':True,'duplicate_replay_status':409,
              'operation_id':applied['operationId'],'replay_log_rows':1,'credentials_recorded':False})
        print('Verified administrator-only dry-run/replay with one durable operation; same synthetic event awaits delivery.')
        return
    if args.phase == 'check-pending':
        status = sql(f"SELECT status FROM pqc_auth_db.audit_outbox WHERE event_id='{event_id}';")
        require(status == 'PENDING', 'Pending event was not retained across the actual producer restart')
        write(args.folder / 'outage-after-restart.json', {'event_id':event_id, 'retained_pending':True})
        print('Confirmed the same pending event survived the producer process restart.')
        return
    restarted = json.loads((args.folder / 'outage-after-restart.json').read_text())
    require(restarted['event_id'] == event_id and restarted['retained_pending'], 'Restart proof missing')
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        status = sql(f"SELECT status FROM pqc_auth_db.audit_outbox WHERE event_id='{event_id}';")
        count = int(sql(f"SELECT COUNT(*) FROM pqc_monitoring_db.security_events WHERE event_id='{event_id}';"))
        if status == 'DELIVERED' and count == 1:
            break
        time.sleep(2)
    require(status == 'DELIVERED' and count == 1, 'Recovery deadline exceeded; preserve pending/dead event evidence')
    payload = json.loads(sql(f"""SELECT JSON_OBJECT('eventId',event_id,
        'occurredAt',DATE_FORMAT(occurred_at,'%Y-%m-%dT%H:%i:%s.%fZ'),
        'eventType',event_type,'outcome',outcome,'sourceService',source_service,
        'username',username,'correlationId',correlation_id,'requestMethod',request_method,
        'requestPath',request_path,'sourceIp',source_ip,'detail',detail)
        FROM pqc_monitoring_db.security_events WHERE event_id='{event_id}';"""))
    status, _ = request('/api/v1/events/internal', body=payload, key=os.environ['MONITORING_API_KEY'], port=8083)
    require(status == 200, 'Identical HTTP retry was not acknowledged idempotently')
    status, _ = request('/api/v1/events/internal', body={**payload,'detail':'different content for an existing ID'}, key=os.environ['MONITORING_API_KEY'], port=8083)
    write(args.folder / 'outage-http-probe.json', {'event_id':event_id,'duplicate_status':200,'conflict_status':status})
    require(status == 409, 'Conflicting event ID must not overwrite audit content')
    require(int(sql(f"SELECT COUNT(*) FROM pqc_monitoring_db.security_events WHERE event_id='{event_id}';")) == 1,
            'Duplicate audit rows after retries')
    write(args.folder / 'outage-verification.json', {'schema':'audit-outage-recovery-v1','passed':True,
          'event_id':event_id,'producer_restart_retained_event':True,'monitoring_outage_recovered':True,
          'identical_http_retry_status':200,'conflicting_http_retry_status':409,'stored_event_rows':1,
          'credentials_recorded':False,'not_an_ml_benchmark':True})
    print('Verified outage recovery, producer restart durability, duplicate acceptance and conflict rejection.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'check-pending', 'replay', 'verify'])
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    try:
        run(args)
    except Exception as error:
        write(args.folder / f'outage-failure-{args.phase}.json', {'passed':False, 'phase':args.phase,
              'error':str(error) if isinstance(error, RuntimeError) else type(error).__name__,
              'credentials_recorded':False})
        raise


if __name__ == '__main__':
    main()
