"""Check label isolation and duplicate exclusion before real model fitting."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / 'data' / 'prepare_ciciot2023_pilot.py'
SPEC = importlib.util.spec_from_file_location('prepare_ciciot2023_pilot',MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_pilot_holds_out_files_and_removes_conflicts_and_overlap(tmp_path,monkeypatch):
    columns = [f'feature_{i}' for i in range(39)]
    reports = []
    for label_index,label in enumerate(('BenignTraffic','DDoS-UDP_Flood')):
        for file_index in range(4):
            path = tmp_path / f'{label}{file_index}.pcap.csv'
            values = (np.arange(100*39).reshape(100,39)+100000*label_index+10000*file_index).astype(float)
            values[0] = 0  # Same vector across different labels must be excluded.
            values[1] = 100 if label_index else 200  # Repeats within each label.
            pd.DataFrame(values,columns=columns).to_csv(path,index=False)
            reports.append({'path':str(path),'rows':100,'bytes':path.stat().st_size,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'label_source':'verified filename taxonomy'})
    audit = tmp_path / 'audit.json'
    audit.write_text(json.dumps({'hashes_included':True,'columns':columns,'files':reports}),encoding='utf-8')
    output = tmp_path / 'processed'
    monkeypatch.setattr(MODULE,'AUDIT',audit)
    monkeypatch.setattr(MODULE,'OUTPUT',output)
    MODULE.main()
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['conflicting_feature_vectors_excluded'] == 1
    seen_hashes,seen_sources = set(),set()
    for split in MODULE.SPLITS:
        frame = pd.read_pickle(output / f'{split}.pkl')
        assert set(frame['_binary_label']) == {0,1}
        assert frame[columns].shape[1] == 39
        hashes,sources = set(frame['_hash']),set(frame['_source'])
        assert not hashes.intersection(seen_hashes)
        assert not sources.intersection(seen_sources)
        seen_hashes.update(hashes)
        seen_sources.update(sources)


def test_feature_hash_does_not_depend_on_dataframe_index():
    a = pd.DataFrame({'Rate':np.array([1.,2.],dtype=np.float32)})
    b = a.copy()
    b.index = [100,200]
    np.testing.assert_array_equal(MODULE.frame_hash(a),MODULE.frame_hash(b))
