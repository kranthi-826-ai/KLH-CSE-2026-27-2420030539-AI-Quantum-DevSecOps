"""Use the packaged PNG renderer with the verified native Word PDF export."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'ml/artifacts/team-guide-2026-10-26'
revision = '-v2' if '--v2' in sys.argv else ''
pdf = ART / ('word-review' + revision + '.pdf')
source = ROOT / 'docs/team/AI-PQC-Security-Team-Guide.docx'
skill = Path('C:/Users/ykran/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
spec = importlib.util.spec_from_file_location('packaged_docx_renderer', skill)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
def word_conversion(doc_path, user_profile, conversion_dir, stem, verbose=False):
    if Path(doc_path).resolve() != source.resolve() or not pdf.is_file():
        raise ValueError('Use only the task-specific Word export.')
    return str(pdf), 'Native Microsoft Word export; LibreOffice unavailable.'
renderer.convert_to_pdf = word_conversion
images = renderer.rasterize(str(source), str(ART / ('pages' + revision)), 130, False, False)
reader = PdfReader(pdf)
texts = []
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ''
    texts.append({'page':i+1, 'text':text})
    print(i+1, len(text), text[:70].replace('\n',' '), '|',text[-80:].replace('\n',' '))
(ART / ('page-text' + revision + '.json')).write_text(json.dumps(texts,indent=2),encoding='utf-8')
(ART / ('review' + revision + '.json')).write_text(json.dumps({
    'docx_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
    'page_count':len(reader.pages), 'rendered_pages':len(images),
    'render_engine':'Microsoft Word PDF export plus packaged render_docx rasterization',
    'visual_review_complete':False},indent=2),encoding='utf-8')
