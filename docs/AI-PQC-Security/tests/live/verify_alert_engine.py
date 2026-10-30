"""Bounded loopback Prometheus rule-engine probe with synthetic, non-security-event metrics."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', required=True, type=Path)
    parser.add_argument('--verify-monitoring-api', action='store_true')
    parser.add_argument('--verify-loopback-email', action='store_true')
    parser.add_argument('--audit-write-failure', action='store_true',
                        help='Probe the process-lifetime adaptive audit failure alert instead of outbox DEAD.')
    args = parser.parse_args()
    folder = args.output_directory.resolve()
    if folder.exists() or folder.parent != (ROOT / 'ml/artifacts').resolve():
        raise RuntimeError('Use a new immediate child of the project artifacts directory')
    binary = ROOT / 'ml/artifacts/tools/prometheus-3.7.3/prometheus.exe'
    if not binary.is_file():
        raise RuntimeError('Prepare the checksummed pinned tools first')
    # Do not replace anything already listening on either test port.
    for port in (19090, 19091):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    folder.mkdir()
    state = {'dead': 0, 'audit_failure': 0}
    alert_name = 'AdaptiveAuditWriteFailure' if args.audit_write_failure else 'AuditOutboxDeadEvents'
    state_key = 'audit_failure' if args.audit_write_failure else 'dead'
    class Exporter(BaseHTTPRequestHandler):
        def do_GET(self):
            body = ('# TYPE audit_outbox_records gauge\n'
                    'audit_outbox_records{application="synthetic-alert-probe",status="PENDING"} 0\n'
                    f'audit_outbox_records{{application="synthetic-alert-probe",status="DEAD"}} {state["dead"]}\n'
                    '# TYPE audit_outbox_oldest_pending_event_age_seconds gauge\n'
                    'audit_outbox_oldest_pending_event_age_seconds{application="synthetic-alert-probe"} 0\n'
                    '# TYPE adaptive_security_failure_audit_errors_total counter\n'
                    f'adaptive_security_failure_audit_errors_total{{application="synthetic-alert-probe"}} {state["audit_failure"]}\n').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 19091), Exporter)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = {'global': {'scrape_interval': '1s', 'evaluation_interval': '1s'},
              'rule_files': [(ROOT / 'infrastructure/monitoring/audit-alerts.yml').as_posix()],
              'scrape_configs': [{'job_name': 'ai-pqc-local-java-services',
                                  'static_configs': [{'targets': ['127.0.0.1:19091']}]}]}
    if args.audit_write_failure:
        # Production rules scope the Business Service by instance port8082.
        # Relabel only this synthetic exporter; do not impersonate a real service scrape.
        config['scrape_configs'][0]['static_configs'][0]['labels'] = {'instance': 'synthetic-business:8082'}
    if args.verify_loopback_email:
        config['alerting'] = {'alertmanagers': [{'static_configs': [{'targets': ['127.0.0.1:19093']}]}]}
    # JSON is valid YAML; this generated config is local evidence, not a production deployment.
    (folder / 'prometheus.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    evidence = {'schema': 'audit-alert-engine-probe-v1', 'passed': False,
                'synthetic_metrics_only': True, 'external_notification_configured': False,
                'observed_states': []}
    evidence['synthetic_loopback_email_target_configured'] = args.verify_loopback_email
    evidence['alert_name'] = alert_name
    evidence['counter_reset_simulated'] = args.audit_write_failure
    evidence['database_fault_injected'] = False
    if args.verify_monitoring_api:
        evidence['monitoring_api_states'] = []
    process = None
    started = time.monotonic()
    log = (folder / 'prometheus.log').open('w', encoding='utf-8')
    def alerts():
        if process.poll() is not None:
            raise RuntimeError('Owned Prometheus process exited; inspect retained local log')
        with urllib.request.urlopen('http://127.0.0.1:19090/api/v1/alerts', timeout=2) as response:
            data = json.load(response)
        values = [a for a in data['data']['alerts'] if a['labels'].get('application') == 'synthetic-alert-probe']
        status = next((a['state'] for a in values if a['labels'].get('alertname') == alert_name), 'inactive')
        if not evidence['observed_states'] or evidence['observed_states'][-1]['state'] != status:
            evidence['observed_states'].append({'seconds': round(time.monotonic() - started, 2), 'state': status})
        if args.verify_monitoring_api:
            from verify_stack import operator_test_token, request, require
            code, receipt = request('/api/v1/events/operations/alerts', token=operator_test_token())
            require(code == 200 and receipt.get('source') == 'Prometheus', 'Monitoring API did not return a verified Prometheus receipt')
            backend_alerts = [alert for alert in receipt['alerts'] if alert.get('application') == 'synthetic-alert-probe']
            backend_state = next((alert['state'] for alert in backend_alerts if alert['name'] == alert_name), 'inactive')
            if not evidence['monitoring_api_states'] or evidence['monitoring_api_states'][-1]['state'] != backend_state:
                evidence['monitoring_api_states'].append({'seconds':round(time.monotonic()-started,2),'state':backend_state})
        return status
    try:
        if args.verify_monitoring_api:
            from verify_stack import operator_test_token, request, require
            code, _ = request('/api/v1/events/operations/alerts', token=operator_test_token('ROLE_USER'))
            require(code == 403, f'Expected ordinary-user403 through Gateway; observed HTTP{code}')
            code, unknown = request('/api/v1/events/operations/alerts', token=operator_test_token())
            require(code == 503 and 'unknown' in unknown.get('message', ''), 'Stopped alert source must be unknown, not healthy')
            evidence['ordinary_user_status'] = 403
            evidence['source_stopped_status'] = 503
        process = subprocess.Popen([str(binary), '--config.file=' + str(folder / 'prometheus.json'),
                  '--storage.tsdb.path=' + str(folder / 'tsdb'), '--storage.tsdb.retention.time=1h',
                  '--web.listen-address=127.0.0.1:19090'], stdout=log, stderr=subprocess.STDOUT,
                  creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        ready = time.monotonic() + 15
        while True:
            try:
                if alerts() != 'inactive':
                    raise RuntimeError('Healthy initial fixture unexpectedly alerted')
                break
            except urllib.error.URLError:
                if time.monotonic() >= ready:
                    raise RuntimeError('Prometheus readiness deadline exceeded')
                time.sleep(.5)
        time.sleep(3)
        if alerts() != 'inactive':
            raise RuntimeError('Healthy fixture must remain inactive')
        state[state_key] = 1
        deadline = started + 95
        while alerts() != 'firing':
            if time.monotonic() >= deadline:
                raise RuntimeError('Real alert did not fire within the bounded deadline')
            time.sleep(1)
        if not any(item['state'] == 'pending' for item in evidence['observed_states']):
            raise RuntimeError('Expected the production pending hold before firing')
        if args.verify_loopback_email:
            # Allow the synthetic SMTP retry before recovery; production hold is unchanged.
            time.sleep(8)
        state[state_key] = 0
        deadline = min(started + 110, time.monotonic() + 10)
        while alerts() != 'inactive':
            if time.monotonic() >= deadline:
                raise RuntimeError('Alert failed to resolve after the fixture recovered')
            time.sleep(1)
        if args.verify_monitoring_api:
            require([item['state'] for item in evidence['monitoring_api_states']] == ['inactive','pending','firing','inactive'],
                    'Monitoring API did not preserve the complete actual rule-engine state transition')
        evidence['passed'] = True
    except Exception as error:
        evidence['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        evidence['owned_process_stopped'] = process is None or process.poll() is not None
        evidence['total_seconds'] = round(time.monotonic() - started, 2)
        with (folder / 'verification.json').open('x', encoding='utf-8') as handle:
            json.dump(evidence, handle, indent=2)
    print('Verified actual Prometheus inactive→pending→firing→inactive flow; owned server stopped. No external notification claim.')


if __name__ == '__main__':
    main()
