"""Twelve loopback-only synthetic logins; never a general load generator."""
import argparse
import http.client
import json
from pathlib import Path
import time
import uuid

from verify_stack import require, sql


def validate_burst(rows, elapsed):
    require(elapsed < 6, 'Burst exceeded one token-refill interval; result is inconclusive')
    require([r['status'] for r in rows] == [401] * 10 + [429] * 2,
            'Expected ten authentication rejections followed by two gateway rate-limit responses')
    for row in rows[10:]:
        require(row['retry_after'].isdigit() and int(row['retry_after']) > 0,
                'Rate-limit response needs positive Retry-After')
        require(row['cache_control'] == 'no-store', 'Rate-limit response must not be cached')
        require(row['correlation_matches'], 'Rate-limit response lost the correlation ID')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), 'Refusing to overwrite burst evidence')
    username = 'burst_' + uuid.uuid4().hex[:16]
    evidence = {'schema': 'gateway-loopback-burst-v1', 'passed': False,
                'target': '127.0.0.1:8080', 'peer': '127.0.0.44',
                'request_cap': 12, 'requests': [], 'created_test_username': username,
                'credentials_recorded': False, 'not_an_ml_or_ddos_benchmark': True}
    started = time.monotonic()
    try:
        # Literal destination and source: no user-controlled remote targets.
        for index in range(12):
            remaining = 5.5 - (time.monotonic() - started)
            require(remaining > 0, 'Burst deadline reached; no additional requests sent')
            correlation = f'{username}-{index}'
            connection = http.client.HTTPConnection('127.0.0.1', 8080,
                         timeout=remaining, source_address=('127.0.0.44', 0))
            try:
                connection.request('POST', '/api/v1/auth/login',
                    body=json.dumps({'username': username, 'password': 'synthetic-invalid-password'}),
                    headers={'Content-Type': 'application/json', 'X-Correlation-ID': correlation,
                             'X-Forwarded-For': f'198.51.100.{index + 1}',
                             'Forwarded': f'for=198.51.100.{index + 1}'})
                response = connection.getresponse()
                # Bound response memory too; do not retain password-bearing responses.
                response.read(8192)
                evidence['requests'].append({'index': index + 1, 'status': response.status,
                    'retry_after': response.getheader('Retry-After', ''),
                    'cache_control': response.getheader('Cache-Control', ''),
                    'correlation_matches': response.getheader('X-Correlation-ID') == correlation})
            finally:
                connection.close()
        elapsed = time.monotonic() - started
        evidence['burst_seconds'] = round(elapsed, 4)
        validate_burst(evidence['requests'], elapsed)
        predicate = f"username='{username}' AND event_type='LOGIN_FAILED'"
        accepted = int(sql(f'SELECT COUNT(*) FROM pqc_auth_db.audit_outbox WHERE {predicate};'))
        require(accepted == 10, 'Auth outbox must contain only the ten admitted failed logins')
        deadline = time.monotonic() + 30
        delivered = 0
        while time.monotonic() < deadline:
            delivered = int(sql(f'SELECT COUNT(*) FROM pqc_monitoring_db.security_events WHERE {predicate};'))
            if delivered == 10:
                break
            time.sleep(1)
        require(delivered == 10, 'Monitoring delivery deadline exceeded')
        evidence.update(passed=True, auth_outbox_rows=accepted, monitoring_rows=delivered,
                        forwarded_header_rotation_bypass=False, retained_test_records=True)
    except Exception as error:
        evidence['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise
    finally:
        evidence['total_seconds'] = round(time.monotonic() - started, 4)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(evidence, handle, indent=2)
    print('Local burst passed: ten 401, two 429, ten persisted audit events; header rotation did not bypass the limit.')


if __name__ == '__main__':
    main()
