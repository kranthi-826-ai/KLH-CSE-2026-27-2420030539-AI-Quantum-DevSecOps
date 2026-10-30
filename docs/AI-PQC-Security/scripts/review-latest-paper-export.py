"""Read-only PDF export inspection; originals remain untouched."""
from pathlib import Path
import hashlib
import json
import re
import argparse
from pypdf import PdfReader
import pypdfium2 as pdfium

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path(r'C:\Users\ykran\Downloads\document (4).pdf'))
args = parser.parse_args()
source = args.source
digest = hashlib.sha256(source.read_bytes()).hexdigest()
out = root / f'ml/artifacts/paper-export-review-{digest[:12]}'
out.mkdir(parents=True, exist_ok=True)
reader = PdfReader(str(source))
doc = pdfium.PdfDocument(str(source))
pages = []
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ''
    (out / f'page-{i+1:02}.txt').write_text(text, encoding='utf-8')
    doc[i].render(scale=1.6).to_pil().save(out / f'page-{i+1:02}.png')
    pages.append({'page': i+1, 'characters':len(text), 'images':len(list(page.images)),
                  'figures': re.findall(r'Fig\.\s*\d+[^\n]*',text),
                  'citation_markers': sorted(set(re.findall(r'\[\d+(?:[\s,\u2013-]+\d+)*\]',text)))})
alltext = '\n'.join(p.extract_text() or '' for p in reader.pages)
report = {'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'pages':len(reader.pages), 'page_details':pages,
          'updated_workflow_present':'9. Inspect evidence' in alltext,
          'new_screenshot_caption_present':any(s in alltext for s in ('Actual PQC decision view','Actual verified PQC output')),
          'unresolved_markers':alltext.count('[?]'),
          'source_tex_sha256':hashlib.sha256((root/'docs/research/paper/main.tex').read_bytes()).hexdigest()}
(out/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
