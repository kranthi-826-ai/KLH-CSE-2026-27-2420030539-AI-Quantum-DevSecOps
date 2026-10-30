"""Bounded loopback-only HTTP measurements; never substitute CIC network features."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_base(base):
    parsed = urlsplit(base)
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port
        or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('Only explicit http://127.0.0.1:PORT isolated test servers are allowed')
    return base.rstrip('/')


def collect(base, output):
    base = validate_base(base)
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite collected observations')
    opener = build_opener(ProxyHandler({}), NoRedirect())
    run_id = 'http-lab-' + uuid.uuid4().hex
    observations = []
    started = time.perf_counter()

    def request(method, route, scenario, expected, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        req = Request(base + route, data=json.dumps(body).encode() if body else None, headers=headers, method=method)
        offset = time.perf_counter() - started
        before = time.perf_counter()
        try:
            response = opener.open(req, timeout=10)
        except HTTPError as exc:
            response = exc
        with response:
            payload = response.read(65536)
            status = response.code
        elapsed = (time.perf_counter() - before) * 1000
        observations.append({'sequence': len(observations), 'method': method, 'route': route,
            'scenario': scenario, 'expected_status': expected, 'status': status,
            'offset_seconds': offset, 'duration_ms': elapsed, 'matches_expected': status == expected})
        if status != expected:
            raise RuntimeError(f'Unexpected status for {scenario}: {status}; collection aborted')
        return json.loads(payload)

    credentials = {'username': 'lab-' + uuid.uuid4().hex[:16], 'password': 'Ephemeral-Test42!'}
    request('POST', '/api/v1/auth/register', 'setup_registration', 201, credentials)
    login = request('POST', '/api/v1/auth/login', 'normal_login', 200, credentials)
    token = login['token']
    # Scenario intent is known from the test harness, NOT inferred from HTTP status.
    # Invalid-token and missing-token probes are not successful exploits.
    for _ in range(5):
        request('GET', '/api/v1/auth/me', 'normal_authenticated', 200, token=token)
        time.sleep(.10)
    for _ in range(5):
        request('POST', '/api/v1/auth/login', 'credential_guess_probe', 401,
                {**credentials, 'password': 'Wrong-Test-Password42!'})
        time.sleep(.05)
    for _ in range(5):
        request('GET', '/api/v1/auth/me', 'missing_token_probe', 401)
        time.sleep(.05)
    for _ in range(5):
        request('GET', '/api/v1/auth/me', 'invalid_token_probe', 401, token='invalid.test.token')
        time.sleep(.05)
    report = {'run_id': run_id, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Controlled loopback HTTP against actual Auth Service; ephemeral H2; monitoring publisher stubbed.',
        'production_traffic': False, 'model_evaluated': False, 'network_flow_features_collected': False,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'python': platform.python_version(), 'request_count': len(observations),
        'elapsed_seconds': time.perf_counter() - started, 'observations': observations,
        'limitations': ['Small harness-generated scenarios, not independent real-world attacks.',
            'No PCAP, network extractor, gateway routing, MySQL, policy or crypto measured in this collection.',
            'Status, latency and outcome are post-response evidence; exclude from pre-request prediction.',
            'No passwords, tokens, response bodies or personal identifiers retained.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(f'Collected {len(observations)} measured requests; all expected statuses matched; no model accuracy claimed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.base_url, args.output)
