"""Test-only compiled-dashboard host with explicit authorized-read corruption.

Never use for deployment. Authentication/authorization comes from the actual
gateway; only successful read bodies may be replaced by a named fault fixture.
"""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MODES = {'healthy', 'malformed-events', 'malformed-runs', 'malformed-both'}
READS = {'/api/v1/events': 'events', '/api/v1/business/executions': 'runs'}


def inject(mode, path, status):
    if mode not in MODES:
        raise ValueError('Unreviewed fault mode')
    return status == 200 and path in READS and mode in {'malformed-both', 'malformed-' + READS[path]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--port', type=int, default=5175, choices=[5175])
    args = parser.parse_args()
    control = args.control.resolve()
    if control.parent.parent != (ROOT/'ml/artifacts').resolve() or not control.is_file():
        raise ValueError('Require an existing control file in an immediate artifact-run directory')
    dist = ROOT/'frontend/web-dashboard/dist'
    if not (dist/'index.html').is_file():
        raise ValueError('Build the dashboard before starting the fault fixture')

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *params, **kwargs):
            super().__init__(*params, directory=str(dist), **kwargs)

        def log_message(self, *params):
            pass  # No credentials, headers or request bodies in fixture logs.

        def list_directory(self, path):
            self.send_error(404)
            return None

        def do_POST(self):
            if self.path == '/api/v1/auth/login':
                self.forward()
            else:
                self.send_error(404)

        def do_GET(self):
            if self.path.startswith('/api/'):
                if self.path in READS:
                    self.forward()
                else:
                    self.send_error(404)
            else:
                super().do_GET()

        def forward(self):
            try:
                mode = json.loads(control.read_text(encoding='utf-8'))['mode']
                if mode not in MODES:
                    raise ValueError('Unknown control mode')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 <= length <= 262144 or self.headers.get('Transfer-Encoding'):
                    self.send_error(413)
                    return
                body = self.rfile.read(length) if length else None
                headers = {'Content-Type': 'application/json'}
                if self.headers.get('Authorization'):
                    headers['Authorization'] = self.headers['Authorization']
                upstream = urllib.request.Request('http://127.0.0.1:8080' + self.path,
                    data=body, headers=headers, method=self.command)
                try:
                    response = urllib.request.urlopen(upstream, timeout=20)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    status = response.status
                    raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError('Upstream fixture response too large')
                if inject(mode, self.path, status):
                    raw = b'[null]'
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (OSError, ValueError, KeyError):
                self.send_error(502, 'Local test fixture source unavailable')

    with ThreadingHTTPServer(('127.0.0.1', args.port), Handler) as server:
        print('Test-only loopback dashboard fixture ready; real gateway authorization retained.', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
