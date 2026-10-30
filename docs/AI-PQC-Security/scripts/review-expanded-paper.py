"""Read and render the user-exported manuscript; never compile a second PDF."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import pypdfium2 as pdfium
from pypdf import PdfReader

parser = argparse.ArgumentParser()
parser.add_argument('pdf', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(exist_ok=False, parents=True)
reader = PdfReader(args.pdf)
document = pdfium.PdfDocument(str(args.pdf))
pages = []
for index, page in enumerate(reader.pages):
    text = page.extract_text() or ''
    pages.append({'page': index + 1, 'width': float(page.mediabox.width),
                  'height': float(page.mediabox.height), 'text': text})
    document[index].render(scale=1.45).to_pil().save(args.output / f'page-{index+1:02}.png')
    print(index + 1, len(text), text[:75].replace('\n', ' '), '|', text[-100:].replace('\n', ' '))
shutil.copy2(args.pdf, args.output / 'reviewed-export.pdf')
(args.output / 'pages.json').write_text(json.dumps(pages, indent=2), encoding='utf-8')
receipt = {'source': str(args.pdf), 'sha256': hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
           'pages': len(pages), 'minimum_twelve_pages': len(pages) >= 12,
           'rendered_pages': len(pages), 'visual_review_complete': False,
           'source_sha256': hashlib.sha256(Path('docs/research/paper/main.tex').read_bytes()).hexdigest()}
receipt['embedded_fonts'] = sorted({str(font.get_object().get('/BaseFont'))
    for page in reader.pages for font in page['/Resources'].get('/Font', {}).values()})
(args.output / 'verification.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
