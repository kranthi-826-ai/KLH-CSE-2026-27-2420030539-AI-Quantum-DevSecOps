"""Read supplied academic handouts locally without modifying the PDFs."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ml/artifacts/course-handouts-2026-10-27'
OUT.mkdir(exist_ok=False)
sources = {
    'ias': Path('C:/Users/ykran/Downloads/ias.pdf'),
    'cacd': Path('C:/Users/ykran/Desktop/CACD/co1/Handout CACD Final.pdf'),
    'ase': Path('C:/Users/ykran/Downloads/ase.pdf'),
}
manifest = []
for key, path in sources.items():
    reader = PdfReader(path)
    pages = [{'page':i+1,'text':page.extract_text() or ''}
             for i,page in enumerate(reader.pages)]
    (OUT / (key+'.json')).write_text(json.dumps(pages,indent=2),encoding='utf-8')
    manifest.append({'subject':key,'path':str(path),'pages':len(pages),
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    print(key, len(pages), 'pages')
    for page in pages[:3]:
        print('PAGE',page['page']); print(page['text'])
    pdf = pdfium.PdfDocument(str(path))
    pdf[0].render(scale=1.5).to_pil().save(OUT / (key+'-page-1.png'))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
