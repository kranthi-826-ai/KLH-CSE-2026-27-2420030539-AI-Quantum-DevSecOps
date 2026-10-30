from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf' / 'AI-PQC-Project-Abstract.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
REVIEW = ROOT / 'tmp' / 'pdfs' / 'project-abstract'
REVIEW.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUT), pagesize=A4)
c.setTitle('AI-Driven Adaptive Post-Quantum Cryptographic Security for Distributed Applications')
c.setAuthor('LAXMANA B V; SAI HARSHA ALLA; MORAMPUDI GIRISH VENKATA SAI; YELLANKI KRANTHI GIRI VENKATA CHARY')
W, H = A4
left, width = 46, W - 92
logo = ImageReader('C:/Users/ykran/Downloads/logo (1).png')
iw, ih = logo.getSize()
lw = 125
c.drawImage(logo, (W-lw)/2, H-100, width=lw, height=lw*ih/iw, mask='auto')

def paragraph(text, y, size=11, leading=15, align=0, font='Times-Roman', color='#20202a'):
    p = Paragraph(text, ParagraphStyle('body', fontName=font, fontSize=size, leading=leading,
                                     alignment=align, textColor=colors.HexColor(color)))
    _, h = p.wrap(width, H)
    p.drawOn(c, left, y-h)
    return y-h

y = H-117
y = paragraph('AI-Driven Adaptive Post-Quantum Cryptographic<br/>Security for Distributed Applications', y, 19, 23, 1, 'Times-Bold')
y = paragraph('Preparing distributed microservice applications for the post-quantum era<br/>using AI-assisted adaptive security', y-12, 10.5, 13, 1, 'Times-Italic')
c.setStrokeColor(colors.HexColor('#a31c2f'))
c.line(left, y-13, W-left, y-13)
y -= 29
rows = [['Roll No.', 'Name'],
        ['2420090064', 'LAXMANA B V'],
        ['2420030482', 'SAI HARSHA ALLA'],
        ['2420030031', 'MORAMPUDI GIRISH VENKATA SAI'],
        ['2420030539', 'YELLANKI KRANTHI GIRI VENKATA CHARY']]
table = Table(rows, colWidths=[112, width-112], rowHeights=[23]*5)
table.setStyle(TableStyle([
    ('FONTNAME',(0,0),(-1,0),'Times-Bold'), ('FONTNAME',(0,1),(-1,-1),'Times-Roman'),
    ('FONTSIZE',(0,0),(-1,-1),10), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f2f3f5')),
    ('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#dadce0')),
    ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),7),
]))
table.wrap(width,H)
table.drawOn(c,left,y-115)
y -= 131
y = paragraph('<b>Guide:</b> VINISHA VELTHURU<br/><b>Department:</b> CSE &nbsp;&nbsp; | &nbsp;&nbsp; <b>College:</b> KL University',y,10.5,15)
y = paragraph('ABSTRACT',y-21,12,15,1,'Times-Bold')
abstract = (
    'Distributed applications require coordinated protection for user identity, application data and communication between services. '
    'The transition towards post-quantum cryptography introduces an additional challenge: selecting suitable protection without ignoring compatibility and computational overhead. '
    'This project presents an AI-driven adaptive security research prototype that integrates threat assessment, policy-based cryptographic selection and auditable execution within a microservice architecture. '
    'A machine-learning inference service assesses network-flow features, while a versioned policy combines the predicted risk with data sensitivity, supported cryptographic capabilities and latency hints to select a classical, hybrid or post-quantum profile. '
    'The classical profile uses X25519, AES-256-GCM and ECDSA; the hybrid profile uses X-Wing, AES-256-GCM and ML-DSA-65; and the post-quantum profile uses ML-KEM-768, AES-256-GCM and ML-DSA-65. '
    'Authentication, gateway routing, policy evaluation, business operations and security monitoring are separated into API-connected services. '
    'MySQL stores policy decisions, execution outcomes and timing measurements, while a web dashboard presents risk assessments, selected modes and security events. '
    'Evaluation separates dataset-based detection experiments from functional checks of encrypted-envelope round trips, tamper rejection and unsafe-downgrade refusal. '
    'The prototype demonstrates an explainable integration of AI-assisted risk assessment and cryptographic agility; it does not claim universal attack prevention or deployment-wide quantum security. '
    'The resulting framework supports reproducible experimentation on adaptive protection for distributed applications.'
)
y = paragraph(abstract,y-10,11,14.3,4)
y = paragraph('<b>Keywords:</b> Distributed applications; microservices; adaptive security; post-quantum cryptography; machine learning; crypto-agility.',y-13,10,13)
assert y > 42, f'Content exceeds page: {y}'
c.showPage()
c.save()
reader = PdfReader(str(OUT))
assert len(reader.pages) == 1
text = reader.pages[0].extract_text()
for value in ['2420090064', '2420030482', '2420030031', '2420030539', 'ABSTRACT', 'ML-KEM-768']:
    assert value in text, value
pdf = pdfium.PdfDocument(str(OUT))
pdf[0].render(scale=1.5).to_pil().save(REVIEW/'page-1.png')
print(f'PDF: {OUT}\nPages: {len(reader.pages)}\nBottom position: {y:.1f}\nPreview: {REVIEW / "page-1.png"}')
