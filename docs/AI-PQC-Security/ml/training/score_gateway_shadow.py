"""Offline passive scoring, never an enforcement endpoint or an accuracy evaluator."""
import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np

from train_microservice_sessions import sha
from train_ciciot2023_pilot import json_clean


def score(source, study, output):
    source, study, output = Path(source), Path(study), Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite shadow assessments')
    if source.stat().st_size > 10 * 1024 * 1024:
        raise ValueError('This bounded offline scorer accepts at most 10 MiB per snapshot')
    frozen = json.loads((study / 'frozen.json').read_text(encoding='utf-8'))
    if frozen['automatic_response_enabled'] or sha(study / 'candidate.joblib') != frozen['model_sha256']:
        raise ValueError('Expected an unchanged, non-enforcing lab candidate')
    candidate = joblib.load(study / 'candidate.joblib')
    columns = tuple(candidate['feature_columns'])
    if tuple(frozen['feature_columns']) != columns:
        raise ValueError('Frozen feature contract mismatch')
    # Bounded immutable snapshot; a concurrent partial JSON line fails validation.
    with source.open('rb') as stream:
        raw = stream.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError('Shadow snapshot grew beyond the bounded size')
    source_hash = hashlib.sha256(raw).hexdigest()
    observations = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    ids = set()
    for row in observations:
        if row.get('schema') != 'gateway-peer-shadow-v1' or row.get('shadow_only') is not True:
            raise ValueError('Wrong observation schema or mode')
        if set(row['features']) != set(columns) or row['observation_id'] in ids:
            raise ValueError('Unknown predictors or duplicate observation ID')
        ids.add(row['observation_id'])
    if not observations:
        raise ValueError('Empty shadow snapshot')
    x = np.array([[r['features'][k] for k in columns] for r in observations], dtype=float)
    if not np.isfinite(x).all():
        raise ValueError('Non-finite shadow features')
    probability = candidate['model'].predict_proba(x)[:, 1]
    results = [{'observation_id': row['observation_id'],
                'suspicious_intent_score': float(p), 'would_alert': bool(p >= candidate['threshold'])}
               for row, p in zip(observations, probability, strict=True)]
    report = {'source_sha256': source_hash, 'model_sha256': frozen['model_sha256'],
        'frozen_sha256': sha(study / 'frozen.json'), 'threshold': candidate['threshold'],
        'scorer_sha256': sha(__file__), 'observations': len(results), 'assessments': results,
        'shadow_only': True, 'automatic_response_enabled': False, 'model_promoted': False,
        'accuracy_measured': False, 'would_alert_count': sum(r['would_alert'] for r in results),
        'limitations': ['Gateway history is per actual peer, unlike the training harness per-account history.',
            'Shared/NAT/proxy clients and concurrency can change feature distributions; scores are experimental.',
            'Only supported synchronous authentication routes are observed; no unknown-attack or production accuracy claim.',
            'No traffic labels were inferred from HTTP outcomes. No decisions were sent back to the gateway.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(json_clean(report), stream, indent=2, allow_nan=False)
    print(f'Scored {len(results)} passive gateway observations; {report["would_alert_count"]} would-alerts; '
          'no blocking, no accuracy claim.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    score(args.source, args.study, args.output)
