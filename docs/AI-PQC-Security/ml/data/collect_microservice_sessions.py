"""Collect bounded, session-separated controlled HTTP traffic from an isolated lab."""
import argparse
import hashlib
import http.client
import json
import platform
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler, HTTPHandler

from collect_microservice_lab import NoRedirect, validate_base
from microservice_session_features import FEATURE_COLUMNS, RequestHistory

SEED = 20261019
SCENARIOS = ('normal_use', 'normal_mistakes', 'legitimate_burst',
             'credential_guessing', 'invalid_token_burst', 'missing_token_burst')
SPLIT_BLOCKS = {'train': 6, 'calibration': 2, 'test': 2}
ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SourceBoundHandler(HTTPHandler):
    def __init__(self, address):
        super().__init__()
        self.address = address

    def http_open(self, request):
        def connection(host, **kwargs):
            return http.client.HTTPConnection(host, source_address=(self.address, 0), **kwargs)
        return self.do_open(connection, request)


def corrupt_token(token, index=0):
    parts = token.split('.')
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    prefix = 'A' + alphabet[index % len(alphabet)]
    if parts[2].startswith(prefix): prefix = 'B' + prefix[1]
    return '.'.join(parts[:2] + [prefix + parts[2][2:]])


def collect(base, destination, routed=False, rich=False, seed=SEED):
    base = validate_base(base)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Refusing to replace a session dataset')
    destination.mkdir(parents=True)
    run_id = 'microservice-sessions-' + uuid.uuid4().hex
    scenarios = SCENARIOS if not rich else SCENARIOS[:3] + ('legitimate_token_refresh',) + SCENARIOS[3:] + ('rotating_invalid_tokens',)
    attack_scenarios = set(SCENARIOS[3:]) | {'rotating_invalid_tokens'}
    request_limit, elapsed_limit = (2000, 270) if rich else (1320, 210)
    plan = {'run_id': run_id, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'seed': seed, 'scenarios': scenarios, 'split_blocks': SPLIT_BLOCKS,
        'feature_columns': FEATURE_COLUMNS, 'requests_per_session': [12, 20],
        'split_protocol': 'Chronological collection phases; disjoint ephemeral accounts/sessions. No session enters multiple partitions.',
        'identity_scope': 'Harness-owned per-account history; not an attacker-controlled session header. Production identity integration is not implemented.',
        'target': 'Controlled scenario intent, not HTTP outcome. Normal mistakes and legitimate bursts have target 0.',
        'label_mapping': {s: int(s in attack_scenarios) for s in scenarios},
        'maximum_http_requests': request_limit, 'maximum_elapsed_seconds': elapsed_limit,
        'source_hashes': {p.name: sha(p) for p in (Path(__file__), Path(__file__).with_name('microservice_session_features.py'),
                                                   Path(__file__).with_name('collect_microservice_lab.py'))},
        'python': platform.python_version(), 'production_traffic': False,
        'scope': 'Actual HTTP to isolated Auth Service/H2; monitoring publisher stubbed; no gateway or MySQL.',
        'excluded_predictors': ['scenario', 'target', 'session_id', 'split', 'sequence', 'status', 'duration_ms', 'expected_status'],
    }
    if routed:
        plan.update(scope='Real Gateway-to-Auth HTTP/H2, seven actual loopback connection peers; monitoring publisher stubbed.',
                    identity_scope='Gateway records are joined using server-generated observation IDs; source peer is never a caller header.',
                    feature_source='Client features are provisional; preparation replaces them with joined gateway pre-request features.',
                    peer_split='Three training peers, two calibration peers, two final-test peers; disjoint across partitions.')
    if rich:
        plan.update(feature_version='gateway-peer-shadow-v2', token_cases='Corrupted same-format real JWT signatures, repeated and rotated; legitimate token refresh negative control.')
    (destination / 'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    opener = build_opener(ProxyHandler({}), NoRedirect())
    last_observation_id = None
    rng = random.Random(seed)
    begun = time.perf_counter()
    http_count = 0

    def http(method, route, body=None, token=None):
        nonlocal http_count, last_observation_id
        if http_count >= request_limit or time.perf_counter() - begun > elapsed_limit:
            raise RuntimeError('Local collection safety budget exceeded')
        http_count += 1
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        req = Request(base + route, data=json.dumps(body).encode() if body else None, headers=headers, method=method)
        start = time.perf_counter()
        try:
            response = opener.open(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            last_observation_id = response.headers.get('X-Shadow-Observation-ID')
            payload, status = response.read(65536), response.code
        return start, time.perf_counter(), status, json.loads(payload)

    manifest = {**plan, 'status': 'collecting', 'splits': {}, 'setup_http_requests': 0}
    for split, blocks in SPLIT_BLOCKS.items():
        records, sessions = [], []
        for block in range(blocks):
            if routed:
                address_index = block % 3 + 1 if split == 'train' else block + (4 if split == 'calibration' else 6)
                opener = build_opener(ProxyHandler({}), NoRedirect(), SourceBoundHandler(f'127.0.0.{address_index}'))
            order = list(scenarios)
            rng.shuffle(order)
            for scenario in order:
                session_id = uuid.uuid4().hex
                credentials = {'username': 'study-' + uuid.uuid4().hex[:16], 'password': 'Ephemeral-Session42!'}
                assert http('POST', '/api/v1/auth/register', credentials)[2] == 201
                login = http('POST', '/api/v1/auth/login', credentials)
                assert login[2] == 200
                manifest['setup_http_requests'] += 2
                token = login[3]['token']
                history = RequestHistory()
                count = rng.randint(12, 20)
                # Mixed normal mistakes are negative controls, not attack labels.
                mistakes = set(rng.sample(range(1, count - 1), 2))
                for index in range(count):
                    route, method, body, bearer, expected = '/api/v1/auth/me', 'GET', None, token, 200
                    if scenario == 'credential_guessing' or (scenario == 'normal_mistakes' and index in mistakes):
                        route, method, body, bearer, expected = '/api/v1/auth/login', 'POST', {
                            **credentials, 'password': 'Wrong-Ephemeral42!'}, None, 401
                    elif scenario == 'invalid_token_burst':
                        bearer, expected = corrupt_token(token) if rich else 'invalid.study.token', 401
                    elif scenario == 'rotating_invalid_tokens':
                        bearer, expected = corrupt_token(token,index), 401
                    elif scenario == 'missing_token_burst':
                        bearer, expected = None, 401
                    elif scenario == 'normal_mistakes' and index == 0:
                        # A legitimate client can initially omit an expired/missing credential.
                        bearer, expected = None, 401
                    elif scenario == 'normal_use' and index in (3, 8):
                        route, method, body, bearer = '/api/v1/auth/login', 'POST', credentials, None
                    elif scenario == 'legitimate_token_refresh' and index % 3 == 0:
                        route, method, body, bearer = '/api/v1/auth/login', 'POST', credentials, None
                    decision_time = time.perf_counter()
                    features = history.before_request(decision_time, route, bool(bearer))
                    start, completed, status, payload = http(method, route, body, bearer)
                    if scenario == 'legitimate_token_refresh' and route.endswith('/login') and status == 200:
                        token = payload['token']
                    if status != expected:
                        raise RuntimeError(f'Unexpected response in {scenario}: {status}; no complete manifest will be produced')
                    # Freeze this row's features before incorporating its response.
                    records.append({'session_id': session_id, 'sequence': index, 'scenario': scenario,
                        'target': plan['label_mapping'][scenario], 'features': features,
                        'outcome': {'status': status, 'expected_status': expected, 'duration_ms': (completed-start)*1000}})
                    if routed:
                        if not last_observation_id:
                            raise RuntimeError('Gateway observation ID missing; refusing an unverified join')
                        records[-1]['gateway_observation_id'] = last_observation_id
                    history.after_response(start, completed, route, status)
                    delay = rng.uniform(.03, .09) if scenario in ('normal_use', 'normal_mistakes', 'legitimate_token_refresh') else rng.uniform(0, .005)
                    time.sleep(delay)
                sessions.append({'session_id': session_id, 'scenario': scenario, 'requests': count})
                print(f'{split}: {len(sessions)} sessions collected', flush=True)
        path = destination / f'{split}.json'
        path.write_text(json.dumps(records, indent=2), encoding='utf-8')
        manifest['splits'][split] = {'rows': len(records), 'sessions': sessions, 'sha256': sha(path)}
    manifest.update(status='complete', elapsed_seconds=time.perf_counter()-begun, total_http_requests=http_count,
                    retained_secrets=False, model_evaluated=False)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Completed {http_count} local HTTP requests in {manifest["elapsed_seconds"]:.1f}s; no AI accuracy claimed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--routed', action='store_true')
    parser.add_argument('--rich', action='store_true')
    parser.add_argument('--seed', type=int, default=SEED)
    args = parser.parse_args()
    collect(args.base_url, args.output, args.routed, args.rich, args.seed)
