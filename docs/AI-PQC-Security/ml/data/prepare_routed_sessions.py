"""Join harness intent to server-side features; refuse identity or outcome mismatches."""
import argparse
import hashlib
import json
from pathlib import Path
from microservice_session_features import FEATURE_COLUMNS
from rich_http_features import RICH_COLUMNS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(source, output, rich=False):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError('Refusing to replace a routed dataset')
    raw = source / 'raw'
    manifest = json.loads((raw / 'manifest.json').read_text(encoding='utf-8'))
    columns = RICH_COLUMNS if rich else FEATURE_COLUMNS
    schema = 'gateway-peer-shadow-v2' if rich else 'gateway-peer-shadow-v1'
    if rich and manifest.get('feature_version') != schema:
        raise ValueError('Rich features require an explicitly versioned v2 collection')
    if manifest['status'] != 'complete' or 'peer_split' not in manifest:
        raise ValueError('Complete explicitly routed collection is required')
    observations = [json.loads(line) for line in (source/'gateway.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = {row['observation_id']: row for row in observations}
    if len(by_id) != len(observations):
        raise ValueError('Duplicate server observation IDs')
    all_ids, all_peers, prepared, splits = set(), set(), {}, {}
    for split, expected_peers in (('train', 3), ('calibration', 2), ('test', 2)):
        path = raw / f'{split}.json'
        if sha(path) != manifest['splits'][split]['sha256']:
            raise ValueError('Raw collection changed')
        rows = json.loads(path.read_text(encoding='utf-8'))
        peers, session_peers = set(), {}
        for row in rows:
            obs_id = row.pop('gateway_observation_id')
            if obs_id in all_ids or obs_id not in by_id:
                raise ValueError('Missing or reused observation join')
            all_ids.add(obs_id)
            observed = by_id[obs_id]
            if observed['schema'] != schema or observed['shadow_only'] is not True:
                raise ValueError('Wrong gateway observation mode/schema')
            if observed['outcome']['status'] != row['outcome']['status']:
                raise ValueError('Client/server outcome mismatch')
            if set(observed['features']) != set(columns):
                raise ValueError('Gateway predictor contract mismatch')
            peer = observed['peer_id']
            if row['session_id'] in session_peers and session_peers[row['session_id']] != peer:
                raise ValueError('A session unexpectedly changed transport peer')
            session_peers[row['session_id']] = peer
            peers.add(peer)
            row['features'] = observed['features']
            row['trusted_peer_id'] = peer
        if len(peers) != expected_peers or all_peers.intersection(peers):
            raise ValueError('Actual peer split does not match the frozen collection design')
        all_peers.update(peers)
        prepared[split] = rows
        splits[split] = {**manifest['splits'][split], 'peer_ids': sorted(peers)}
    output.mkdir(parents=True)
    for split, rows in prepared.items():
        path = output/f'{split}.json'
        path.write_text(json.dumps(rows, indent=2), encoding='utf-8')
        splits[split]['sha256'] = sha(path)
    result = {**manifest, 'splits': splits, 'feature_source': 'Actual gateway pre-request peer history, not client history.',
        'feature_columns': columns,
        'raw_manifest_sha256': sha(raw/'manifest.json'), 'gateway_log_sha256': sha(source/'gateway.jsonl'),
        'preparation_sha256': sha(__file__), 'unique_transport_peers': len(all_peers),
        'joined_study_observations': len(all_ids), 'gateway_observations_including_setup': len(observations),
        'cv_group': 'trusted_peer_id', 'automatic_response_enabled': False}
    (output/'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Prepared {len(all_ids)} gateway-feature rows across {len(all_peers)} disjoint transport peers; no model evaluation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rich', action='store_true')
    args = parser.parse_args()
    prepare(args.source, args.output, args.rich)
