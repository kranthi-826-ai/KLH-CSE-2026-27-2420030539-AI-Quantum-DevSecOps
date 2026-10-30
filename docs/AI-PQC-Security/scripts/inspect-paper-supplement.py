"""Read the six remaining retained PDFs for the expanded manuscript review."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ml/artifacts/literature-supplement-2026-10-23'
OUT.mkdir(exist_ok=False)
records = []
for prefix in ('05-', '07-', '08-', '09-', '10-', '11-'):
    path, = (ROOT / 'docs/research/papers').glob(prefix + '*.pdf')
    reader = PdfReader(path)
    pages = [{'page': i + 1, 'text': page.extract_text() or ''}
             for i, page in enumerate(reader.pages)]
    (OUT / (path.stem + '.json')).write_text(
        json.dumps(pages, indent=2, ensure_ascii=False), encoding='utf-8')
    records.append({'file': path.name, 'pages': len(pages),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    print(path.name, len(pages), 'pages')
    print('\n'.join(p['text'] for p in pages[:2])[:7500])
(OUT / 'manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
