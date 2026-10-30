"""Build a bounded, reproducible pilot; reserve test data before model fitting."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ciciot2023_common import ATTACK_GROUPS, filename_label
from validate_ciciot2023 import sha256

ML_ROOT = Path(__file__).resolve().parents[1]
AUDIT = ML_ROOT / 'artifacts' / 'ciciot2023-dataset-validation.json'
OUTPUT = ML_ROOT / 'data' / 'processed' / 'ciciot2023-pilot-v1'
SEED = 20261019
SPLITS = ('train', 'calibration', 'validation', 'test')
ATTACK_CAPS = {'train':6000, 'calibration':1000, 'validation':1500, 'test':1500}
BENIGN_CAPS = {'train':60000, 'calibration':12000, 'validation':12000, 'test':12000}


def frame_hash(frame: pd.DataFrame) -> np.ndarray:
    return pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype=np.uint64)


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f'Refusing to overwrite frozen pilot: {OUTPUT}')
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    if not audit['hashes_included']:
        raise ValueError('Complete SHA-256 audit is required')
    columns = [column for column in audit['columns'] if column != 'label']
    if len(columns) != 39:
        raise ValueError(f'Expected audited 39-feature release, got {len(columns)}')
    by_label: dict[str, list[dict]] = defaultdict(list)
    for report in audit['files']:
        path = Path(report['path'])
        if report['label_source'] != 'verified filename taxonomy':
            raise ValueError('This pilot is explicitly for the per-attack release')
        by_label[filename_label(path)].append(report)

    pools: dict[tuple[str,str], pd.DataFrame] = {}
    allocation = []
    dropped_invalid = 0
    dropped_rows_within_reservoir = 0
    for label, reports in sorted(by_label.items()):
        # Deterministic filename hash orders whole files independently of data.
        ordered = sorted(reports, key=lambda row: hashlib.sha256(
            f"{SEED}:{Path(row['path']).name}".encode()).hexdigest())
        held = {}
        if len(ordered) >= 4:
            held = {ordered[-1]['path']:'test', ordered[-2]['path']:'validation',
                    ordered[-3]['path']:'calibration'}
        for report in ordered:
            path = Path(report['path'])
            if path.stat().st_size != report['bytes'] or sha256(path) != report['sha256']:
                raise ValueError(f'Source changed since audit: {path}')
            whole_split = held.get(report['path'], 'train') if held else None
            allocation.append({'source':path.name,'label':label,
                               'strategy':'whole-source-file' if held else 'contiguous-row-ranges',
                               'split':whole_split or '60/10/15/15 contiguous ranges'})
            offset = 0
            rng = np.random.default_rng(int(hashlib.sha256(
                f'{SEED}:{path.name}'.encode()).hexdigest()[:16],16))
            for chunk in pd.read_csv(path, chunksize=100000, low_memory=False):
                numeric = chunk[columns].apply(pd.to_numeric, errors='coerce').astype(np.float32)
                valid = np.isfinite(numeric.to_numpy()).all(axis=1)
                dropped_invalid += int((~valid).sum())
                position = np.arange(offset,offset+len(chunk))/max(report['rows'],1)
                offset += len(chunk)
                priority = rng.random(len(chunk))
                row_splits = (np.repeat(whole_split,len(chunk)) if whole_split else
                    np.select([position < .60, position < .70, position < .85],
                              ['train','calibration','validation'], default='test'))
                hashes = frame_hash(numeric)
                # Pure feature hashes identify potential cross-split duplicates;
                # neither source filename nor attack label is an input feature.
                for split in SPLITS:
                    mask = valid & (row_splits == split)
                    if not mask.any():
                        continue
                    subset = numeric.loc[mask].astype(np.float32).copy()
                    subset['_priority'] = priority[mask]
                    subset['_hash'] = hashes[mask]
                    subset['_source'] = path.name
                    key = (label,split)
                    combined = pd.concat([pools[key],subset],ignore_index=True) if key in pools else subset
                    before = len(combined)
                    combined = combined.drop_duplicates('_hash', keep='first')
                    dropped_rows_within_reservoir += before-len(combined)
                    cap = (BENIGN_CAPS if label=='BenignTraffic' else ATTACK_CAPS)[split]
                    pools[key] = combined.nsmallest(cap, '_priority')
            print(f"prepared {path.name}: {report['rows']} rows; {whole_split or 'contiguous ranges'}",flush=True)

    # Float32 is the actual model input. Rehash that representation so no exact
    # model-input vector can occur in multiple splits, regardless of source.
    frames = {}
    for split in SPLITS:
        parts = []
        for label in sorted(by_label):
            part = pools.get((label,split))
            if part is None:
                continue
            part = part.copy()
            part['_label'] = label
            part['_group'] = ATTACK_GROUPS[label]
            parts.append(part)
        frames[split] = pd.concat(parts,ignore_index=True)
        frames[split]['_hash'] = frame_hash(frames[split][columns])
    conflicts: set[int] = set()
    all_labels: dict[int,str] = {}
    for frame in frames.values():
        for h,label in zip(frame['_hash'], frame['_label'], strict=True):
            prior = all_labels.get(int(h))
            if prior is not None and prior != label:
                conflicts.add(int(h))
            all_labels[int(h)] = label
    seen: set[int] = set()
    summaries = {}
    OUTPUT.mkdir(parents=True)
    for split in reversed(SPLITS):
        frame = frames[split]
        before = len(frame)
        frame = frame[~frame['_hash'].isin(conflicts)].drop_duplicates('_hash')
        frame = frame[~frame['_hash'].isin(seen)].copy()
        seen.update(int(value) for value in frame['_hash'])
        frame['_binary_label'] = (frame['_label'] != 'BenignTraffic').astype(np.int8)
        if frame['_binary_label'].nunique() != 2:
            raise ValueError(f'{split} lacks both binary classes')
        frame = frame.drop(columns=['_priority'])
        frame.to_pickle(OUTPUT / f'{split}.pkl')
        summaries[split] = {
            'rows':len(frame), 'removed_duplicate_or_conflict_rows':before-len(frame),
            'label_counts':{str(k):int(v) for k,v in frame['_label'].value_counts().items()},
            'group_counts':{str(k):int(v) for k,v in frame['_group'].value_counts().items()},
            'binary_counts':{str(k):int(v) for k,v in frame['_binary_label'].value_counts().items()},
            'sha256':hashlib.sha256((OUTPUT / f'{split}.pkl').read_bytes()).hexdigest(),
        }
    manifest = {
        'run_id':'ciciot2023-pilot-v1', 'created_utc':datetime.now(timezone.utc).isoformat(),
        'seed':SEED, 'source_audit_sha256':hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
        'feature_columns':columns, 'feature_dtype':'float32', 'attack_caps':ATTACK_CAPS,
        'benign_caps':BENIGN_CAPS, 'split_order':list(SPLITS), 'splits':summaries,
        'invalid_rows_excluded':dropped_invalid,
        'within_reservoir_duplicates_removed':dropped_rows_within_reservoir,
        'conflicting_feature_vectors_excluded':len(conflicts),
        'cross_split_exact_model_input_overlap':0,
        'duplicate_scope':'Exact float32 feature vectors in the bounded pilot; not a full-corpus duplicate census',
        'file_allocation':allocation,
        'limitations':[
            'Bounded per-label pilot changes class prevalence; accuracy is not a full-corpus or production estimate.',
            'Source files may be fragments of the same original capture; whole-file holdout does not prove capture independence.',
            'Labels with fewer than four files share sources across contiguous, disjoint row ranges.',
            'Test split is frozen and must remain unopened by model-selection scripts.',
            'CICIoT2023 network features differ from UNSW-NB15 and microservice system calls.',
        ],
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({split:summary['rows'] for split,summary in summaries.items()}),flush=True)


if __name__ == '__main__':
    main()
