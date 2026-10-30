"""Extract user-provided paper text locally for citation review, without publishing PDFs."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
library = root / 'docs/research/papers'
output = root / 'ml/artifacts/literature-review-v1'
output.mkdir(exist_ok=False)
selected = [
    '01-adaptive-encryption-risk-based-selection-2026.pdf',
    '02-sageconv-gnn-transformer-ids-2026.pdf',
    '03-microservice-ids-benchmark-dataset-2024.pdf',
    '04-authenticated-ml-kem-ml-dsa-session-protocol-2026.pdf',
    '06-api-gateway-microservices-security-2024.pdf',
]
records = []
for name in selected:
    source = library / name
    reader = PdfReader(source)
    pages = [{'page': i + 1, 'text': page.extract_text() or ''} for i, page in enumerate(reader.pages)]
    record = {'file': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'pages': len(pages), 'metadata': {str(k): str(v) for k, v in (reader.metadata or {}).items()}}
    (output / (source.stem + '.json')).write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding='utf-8')
    records.append(record)
    print(name, 'pages=', len(pages))
    print(pages[0]['text'][:2200])
(output / 'manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
