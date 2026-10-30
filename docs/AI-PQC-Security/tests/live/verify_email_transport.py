"""Bounded real Alertmanager to synthetic loopback SMTP proof. Never sends external mail."""
import argparse
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', required=True, type=Path)
    parser.add_argument('--rule-engine', action='store_true')
    args = parser.parse_args()
    folder = args.output_directory.resolve()
    if folder.exists() or folder.parent != (ROOT / 'ml/artifacts').resolve():
        raise RuntimeError('Use a new immediate artifact child directory')
    tools = ROOT / 'ml/artifacts/tools/alertmanager-0.34.1'
    for name in ('alertmanager.exe', 'amtool.exe'):
        if not (tools / name).is_file():
            raise RuntimeError('Prepare publisher-checksummed Alertmanager tools first')
    for port in (19093, 19094):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    folder.mkdir()
    result = {'schema': 'email-loopback-transport-v1', 'passed': False,
              'external_delivery': False, 'tls_auth_provider_delivery_verified': False,
              'accepted_statuses': [], 'temporary_rejections': 0}
    result['real_prometheus_rule_engine'] = args.rule_engine
    lock = threading.Lock()

    class Sink(socketserver.StreamRequestHandler):
        def reply(self, value):
            self.wfile.write((value + '\r\n').encode())
            self.wfile.flush()

        def handle(self):
            self.connection.settimeout(5)
            self.reply('220 synthetic.local ESMTP')
            sender = recipient = False
            while True:
                line = self.rfile.readline(4097)
                if not line or len(line) > 4096:
                    return
                command = line.decode('ascii', errors='replace').strip()
                upper = command.upper()
                if upper.startswith(('EHLO ', 'HELO ')):
                    self.reply('250 synthetic.local')  # No TLS or authentication advertised.
                elif upper == 'MAIL FROM:<ALERTS@EXAMPLE.TEST>':
                    sender = True
                    self.reply('250 OK')
                elif upper == 'RCPT TO:<OPERATOR@EXAMPLE.TEST>' and sender:
                    recipient = True
                    self.reply('250 OK')
                elif upper == 'DATA' and recipient:
                    self.reply('354 End with dot')
                    chunks, size = [], 0
                    while True:
                        data = self.rfile.readline(65537)
                        size += len(data)
                        if not data or size > 262144:
                            return
                        if data == b'.\r\n':
                            break
                        chunks.append(data[1:] if data.startswith(b'..') else data)
                    with lock:
                        if result['temporary_rejections'] == 0:
                            result['temporary_rejections'] += 1
                            self.reply('451 Synthetic temporary failure; retry')
                            continue
                        message = BytesParser(policy=policy.default).parsebytes(b''.join(chunks))
                        subject = str(message['Subject'])
                        status = 'resolved' if 'resolved' in subject else 'firing' if 'firing' in subject else 'unknown'
                        result['accepted_statuses'].append(status)
                    self.reply('250 Accepted locally; not relayed')
                elif upper == 'RSET':
                    sender = recipient = False
                    self.reply('250 OK')
                elif upper == 'QUIT':
                    self.reply('221 Bye')
                    return
                elif upper == 'NOOP':
                    self.reply('250 OK')
                else:
                    self.reply('550 Synthetic sink accepts only fixed test envelopes')

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True

    server = Server(('127.0.0.1', 19094), Sink)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = {'global': {'smtp_smarthost': '127.0.0.1:19094', 'smtp_from': 'alerts@example.test',
                         'smtp_require_tls': False},
              'route': {'receiver': 'synthetic', 'group_by': ['alertname'], 'group_wait': '1s',
                        'group_interval': '2s', 'repeat_interval': '1h'},
              'receivers': [{'name': 'synthetic', 'email_configs': [{'to': 'operator@example.test',
                  'send_resolved': True, 'headers': {'Subject': 'Synthetic {{ .Status }}'},
                  'text': 'Synthetic transport fixture only', 'html': ''}]}]}
    # TLS disabled ONLY for this fixed loopback sink. Production renderer requires TLS.
    path = folder / 'alertmanager.json'
    path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    process = None
    engine = None
    engine_log = None
    started = time.monotonic()
    log = (folder / 'alertmanager.log').open('w', encoding='utf-8')
    now = datetime.now(timezone.utc)
    alert = {'labels': {'alertname': 'SyntheticTransportOnly', 'application': 'synthetic-email-probe'},
             'annotations': {'summary': 'Synthetic only'}, 'startsAt': now.isoformat(),
             'endsAt': (now + timedelta(minutes=5)).isoformat()}

    def post():
        request = urllib.request.Request('http://127.0.0.1:19093/api/v2/alerts',
            data=json.dumps([alert]).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=2) as response:
            if response.status != 200:
                raise RuntimeError('Synthetic alert injection failed')

    def wait_status(status):
        while time.monotonic() - started < (115 if args.rule_engine else 50):
            with lock:
                if status in result['accepted_statuses']:
                    return
            if process.poll() is not None:
                raise RuntimeError('Owned Alertmanager exited')
            time.sleep(.25)
        raise RuntimeError('Bounded email delivery deadline exceeded')

    try:
        checked = subprocess.run([str(tools / 'amtool.exe'), 'check-config', str(path)],
                                 capture_output=True, timeout=10)
        if checked.returncode:
            raise RuntimeError('Synthetic Alertmanager configuration rejected')
        process = subprocess.Popen([str(tools / 'alertmanager.exe'), '--config.file=' + str(path),
            '--storage.path=' + str(folder / 'storage'), '--web.listen-address=127.0.0.1:19093',
            '--cluster.listen-address='], stdout=log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for attempt in range(40):
            try:
                with urllib.request.urlopen('http://127.0.0.1:19093/-/ready', timeout=.5):
                    break
            except OSError:
                if attempt == 39:
                    raise RuntimeError('Alertmanager readiness deadline exceeded')
                time.sleep(.25)
        if args.rule_engine:
            engine_folder = folder.with_name(folder.name + '-engine')
            if engine_folder.exists():
                raise RuntimeError('Rule engine artifact directory already exists')
            engine_log = (folder / 'engine-run.log').open('w', encoding='utf-8')
            engine = subprocess.Popen([sys.executable, str(ROOT / 'tests/live/verify_alert_engine.py'),
                '--output-directory', str(engine_folder), '--verify-loopback-email'],
                stdout=engine_log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            result['engine_evidence'] = engine_folder.name + '/verification.json'
            wait_status('firing')
            wait_status('resolved')
            if engine.wait(timeout=10) != 0:
                raise RuntimeError('Real rule engine probe failed; inspect retained evidence')
            engine_result = json.loads((engine_folder / 'verification.json').read_text(encoding='utf-8'))
            if not engine_result['passed']:
                raise RuntimeError('Real rule engine evidence failed')
        else:
            post()
            wait_status('firing')
            # Same identity and start time must not create another immediate firing message.
            for _ in range(3):
                post()
            time.sleep(5)
            if result['accepted_statuses'] != ['firing']:
                raise RuntimeError('Repeated fixture notifications were not grouped/suppressed')
            alert['endsAt'] = datetime.now(timezone.utc).isoformat()
            post()
            wait_status('resolved')
        if result['accepted_statuses'] != ['firing', 'resolved'] or result['temporary_rejections'] != 1:
            raise RuntimeError('Unexpected transport receipts')
        result['passed'] = True
    except Exception as error:
        result['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise
    finally:
        # On an integration timeout let the bounded child execute its own cleanup first.
        if engine is not None and engine.poll() is None:
            try:
                engine.wait(timeout=20)
            except subprocess.TimeoutExpired:
                engine.terminate()
                engine.wait(timeout=5)
        if engine_log is not None:
            engine_log.close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        log.close()
        result['owned_process_stopped'] = process is None or process.poll() is not None
        result['seconds'] = round(time.monotonic() - started, 2)
        (folder / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Verified local synthetic SMTP firing, temporary-failure retry, duplicate suppression and recovery; owned processes stopped. External email NOT verified.')


if __name__ == '__main__':
    main()
