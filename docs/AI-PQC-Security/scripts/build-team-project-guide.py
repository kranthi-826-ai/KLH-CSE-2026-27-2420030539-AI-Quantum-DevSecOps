"""Create the editable project explainer using the bundled document runtime."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/team'
ART = ROOT / 'ml/artifacts/team-guide-2026-10-26'
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
TARGET = OUT / 'AI-PQC-Security-Team-Guide.docx'
if TARGET.exists() and '--replace-own-output' not in sys.argv:
    raise FileExistsError('Preserve the existing guide; choose a new revision.')

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin = sec.bottom_margin = Inches(.65)
sec.left_margin = sec.right_margin = Inches(.75)
for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'List Bullet', 'List Number'):
    st = doc.styles[name]
    st.font.name = 'Calibri'
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_after = Pt(6)
normal = doc.styles['Normal']
normal.font.size = Pt(11)
normal.paragraph_format.line_spacing = 1.08
doc.styles['Title'].font.size = Pt(27)
doc.styles['Title'].font.bold = True
doc.styles['Subtitle'].font.size = Pt(12)
doc.styles['Heading 1'].font.size = Pt(19)
doc.styles['Heading 2'].font.size = Pt(12)
for name in ('Heading 1', 'Heading 2'):
    doc.styles[name].paragraph_format.keep_with_next = True
    doc.styles[name].paragraph_format.space_before = Pt(10)
for name in ('Title','Subtitle','Heading 1','Heading 2'):
    st = doc.styles[name]
    if st.element.pPr is not None:
        for border in list(st.element.pPr.findall(qn('w:pBdr'))):
            st.element.pPr.remove(border)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = footer.add_run('Team project guide  |  ')
run.font.size = Pt(9)
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
doc.core_properties.title = 'AI PQC Security Project Guide'
doc.core_properties.subject = 'Team understanding and presentation preparation'
doc.core_properties.author = 'AI PQC Security project team'

def p(text, style=None):
    return doc.add_paragraph(text, style)

def h(text, level=1):
    doc.add_heading(text, level)

def page(title):
    doc.add_page_break(); h(title)

def bullets(items):
    for item in items: p(item, 'List Bullet')

def numbered(items):
    numbering = doc.part.numbering_part.element
    style_id = doc.styles['List Number'].element.pPr.numPr.numId.val
    original = numbering.num_having_numId(style_id)
    number = numbering.add_num(original.abstractNumId.val)
    number.add_lvlOverride(0).add_startOverride(1)
    for item in items:
        para = p(item, 'List Number')
        pr = para._p.get_or_add_pPr().get_or_add_numPr()
        pr.get_or_add_ilvl().val = 0
        pr.get_or_add_numId().val = number.numId

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for cell, text, width in zip(t.rows[0].cells, headers, widths):
        cell.width = Inches(width); cell.text = text
    for row in rows:
        cells = t.add_row().cells
        for cell, text, width in zip(cells, row, widths):
            cell.width = Inches(width); cell.text = str(text)
    for i, row in enumerate(t.rows):
        pr = row._tr.get_or_add_trPr()
        pr.append(OxmlElement('w:cantSplit'))
        if i == 0:
            pr.append(OxmlElement('w:tblHeader'))
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tc = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for edge in ('top','left','bottom','right','insideH','insideV'):
                e = OxmlElement('w:'+edge)
                for key, val in [('val','single'),('sz','4'),('color','D9D9D9')]: e.set(qn('w:'+key), val)
                borders.append(e)
            tc.append(borders)
            margins = OxmlElement('w:tcMar')
            for edge in ('top','bottom','left','right'):
                e=OxmlElement('w:'+edge); e.set(qn('w:w'),'85'); e.set(qn('w:type'),'dxa'); margins.append(e)
            tc.append(margins)
            shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), '20364A' if i==0 else ('F1F5F8' if i%2 else 'FFFFFF')); tc.append(shade)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(2)
                para.paragraph_format.line_spacing = 1.02
                for r in para.runs:
                    r.font.size = Pt(10)
                    r.font.bold = i==0
                    r.font.color.rgb = RGBColor(255,255,255) if i==0 else RGBColor(0,0,0)
    p('')
    return t

p('AI PQC Security Project Guide', 'Title')
p('Team understanding and presentation preparation', 'Subtitle')
p('Project snapshot 26 October 2026')
h('What we are building')
p('Our project is a backend security research platform with a web dashboard. It combines user authentication, AI risk assessment, policy-based cryptographic selection, and records that explain what happened to a protected business request.')
p('The formal project title is AI-Driven Adaptive Quantum-Resilient Security Framework for Secure Microservice Architectures.')
h('The explanation to remember', 2)
p('AI estimates risk from supplied traffic features. A policy combines that risk with data sensitivity and compatibility to choose classical, hybrid or post-quantum protection. The Business Service runs the selected cryptographic profile, verifies its local round trip, and records the outcome for monitoring and the dashboard.')
h('Why this is useful', 2)
p('Microservices spread a business operation across several services. We need to know who requested an operation, which protection was selected, whether that protection actually ran, and whether the outcome was saved. Our prototype connects these responsibilities rather than treating an AI score as complete security.')
h('What this guide helps the team do', 2)
bullets(['Explain the inputs and trace one request through the services.',
         'Describe the algorithms and the exact policy conditions.',
         'Present measured results without confusing a test pass with model accuracy.',
         'Demonstrate the dashboard and identify what is still future work.'])
p('Important boundary: this is a tested local research prototype. It is not a universal firewall, a guarantee of perfect detection, or completed end-to-end PQC transport between independent applications.')

page('The parts of the system')
p('A microservice is a small service with a defined responsibility and API. Our system separates identity, risk prediction, decisions, execution and monitoring so that each responsibility can be checked independently.')
table(['Component','Main responsibility'],[
 ('Web dashboard','Displays API results, decisions, execution records and permitted monitoring information.'),
 ('API Gateway','Provides the application entry point, routes requests and applies configured authentication and rate controls.'),
 ('Auth Service','Registers users, checks login credentials and issues JWT access tokens.'),
 ('Business Service','Demonstration application that requests a decision, runs the cryptographic profile and records execution.'),
 ('Adaptive Policy Engine','Combines model risk, sensitivity, compatibility and latency hints into a versioned decision.'),
 ('AI Security Service','Runs the deployed Random Forest pipeline and returns a risk score and category.'),
 ('Security Monitoring Service','Collects security events and supplies authorized monitoring and alert information.'),
 ('Eureka discovery server','Helps services locate one another. Discovery is not authorization.'),
 ('MySQL databases','Store service-owned users, policy decisions, execution audits, security events and related delivery records.')], [2.0,5.0])
h('Technologies in plain language',2)
p('Spring Boot and Java implement the Java services. Python runs model inference and training experiments. React provides the web dashboard. MySQL stores relational records. Bouncy Castle supplies cryptographic implementations. Prometheus evaluates operational metrics and alert rules.')
p('Service-oriented architecture, or SOA, means exposing capabilities through service interfaces. Microservices apply that idea through smaller, independently managed services. Our APIs are the contracts between those capabilities.')

page('Inputs and outputs')
h('Runtime inputs',2)
p('The adaptive operation is POST /api/v1/business/adaptive-secure-data through the gateway. It requires an authenticated request. The JWT is an HTTP authorization credential; it is not a training feature.')
table(['Field','What it means'],[
 ('data','The message or payload to protect. Use synthetic text in the demonstration.'),
 ('networkFeatures','A schema-compatible map of traffic measurements, such as duration, packets, bytes, protocol and connection state.'),
 ('dataSensitivity','PUBLIC, INTERNAL, CONFIDENTIAL or RESTRICTED.'),
 ('hybridSupported','Whether the request declares hybrid compatibility.'),
 ('pqcSupported','Whether the request declares PQC compatibility.'),
 ('maxCryptoLatencyMillis','A nonnegative selection hint used by policy. It is not an execution deadline.')], [2.05,4.95])
p('Current limitation: features, sensitivity and capability flags are supplied to the API. Shape validation does not prove that they are truthful live measurements. Trusted automatic collection and resource-owned sensitivity rules remain further work.')
h('Outputs',2)
p('A successful adaptive response includes the model risk score, effective risk level, selected mode, exact profile, encrypted payload, signature, local round-trip verification flag, timings and tracking IDs. Policy/model versions support traceability. The stored decision also explains why the profile was selected.')
p('An execution ID identifies the operation; a decision ID identifies the policy decision; a correlation ID links related records. MySQL records and monitoring events let us cross-check the result rather than relying only on what is visible in the dashboard.')
h('Training inputs are different',2)
p('Offline training uses prepared, labeled observations and defined evaluation splits. We do not upload an entire dataset for each API call. Network flows, HTTP histories and syscall windows have separate schemas and experiments; they are not blindly combined into one deployed model.')

page('The complete request workflow')
img = Image.new('RGB',(1680,660),'white'); draw = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',29)
labels=[('1','Login and JWT'),('2','Gateway checks'),('3','Business audit'),('4','Policy calls AI'),
        ('8','Dashboard view'),('7','Save and monitor'),('6','Crypto and verify'),('5','Select profile')]
boxes=[]
for i,(number,label) in enumerate(labels):
    row,col=divmod(i,4); x=20+col*420; y=45+row*340
    draw.rounded_rectangle((x,y,x+375,y+155),radius=13,outline='#20364A',width=4,fill='#F1F5F8')
    draw.text((x+24,y+22),number,font=font,fill='black')
    draw.text((x+24,y+82),label,font=font,fill='black')
    boxes.append((x,y))
for row in (0,1):
    for col in range(3):
        left=20+col*420+375; right=20+(col+1)*420; y=45+row*340+77
        draw.line((left,y,right,y),fill='#20364A',width=4)
        tip=right if row==0 else left
        back=tip-12 if row==0 else tip+12
        draw.polygon([(tip,y),(back,y-9),(back,y+9)],fill='#20364A')
x=20+3*420+187; draw.line((x,200,x,385),fill='#20364A',width=4); draw.polygon([(x,385),(x-9,371),(x+9,371)],fill='#20364A')
diagram=ART/'request-workflow.png'; img.save(diagram)
pic=doc.add_picture(str(diagram),width=Inches(7))
pic._inline.docPr.set('descr','Logical request journey from login to dashboard. AI returns its score to policy before profile selection. Failure can stop the successful path.')
p('This is the logical journey, not a drawing of every network connection. A failure or denial can stop the successful path.')
numbered([
 'The user logs in and receives a JWT. Registration and login do not themselves run the adaptive encryption operation.',
 'The gateway applies configured request controls and routes the protected operation to Business.',
 'Business creates a STARTED audit before policy evaluation or cryptography.',
 'Policy sends compatible traffic features to AI Security. The deployed Random Forest returns a score and risk category.',
 'Policy records its constrained selection. Business validates the decision and refuses an unsafe HIGH-risk classical fallback.',
 'The selected implementation generates local keys, encrypts and signs the envelope, then opens it and verifies the recovered data.',
 'Execution completion and delivery records are persisted. Monitoring receives security events.',
 'Authorized dashboard views retrieve and explain the recorded outcome.'
 ])
h('One worked example',2)
p('Assume AI returns MEDIUM, sensitivity is CONFIDENTIAL, PQC is supported and the hint is 100 ms. CONFIDENTIAL raises effective risk to HIGH. Policy selects PQC. If the operation and completion write succeed, the result records verified success. This is an illustrative policy example, not a new model prediction or measured timing.')

page('Policy and cryptographic algorithms')
p('AI predicts risk; policy chooses protection. Policy version 1.1.0 implements the following branches. The 8 ms and 15 ms values are heuristic selection thresholds, not measured completion guarantees.')
table(['Effective risk','Selection rule'],[
 ('LOW','Select Classical.'),
 ('MEDIUM','Select Hybrid if supported and hint is at least 8 ms; otherwise Classical.'),
 ('HIGH','Select PQC if supported and hint is at least 15 ms; otherwise Hybrid if supported and hint is at least 8 ms.'),
 ('HIGH with neither option','Policy records the fallback; Business rejects Classical execution with HTTP 422.')],[1.7,5.3])
p('Sensitivity adjustment: PUBLIC and INTERNAL keep the model category unchanged. CONFIDENTIAL raises it one level. RESTRICTED forces HIGH. HIGH remains HIGH when raised.')
table(['Mode','Key establishment','Payload encryption','Signature'],[
 ('Classical','X25519','AES-256-GCM','ECDSA P-256'),
 ('Hybrid','X-Wing combines X25519 and ML-KEM-768','AES-256-GCM','ML-DSA-65'),
 ('PQC','ML-KEM-768','AES-256-GCM','ML-DSA-65')],[.9,2.35,1.7,2.05])
h('Why AES is common to all three',2)
p('AES protects the actual payload using a shared secret key. AES-256 uses a 256-bit key; GCM also detects changes to the encrypted data. The profiles change public-key establishment and signing while retaining AES-256-GCM for the payload. Post-quantum migration does not require replacing every symmetric cipher.')
h('What the other algorithms do',2)
p('X25519 is classical key agreement. ML-KEM is a post-quantum key encapsulation mechanism derived from Kyber. X-Wing combines classical and post-quantum key establishment. ECDSA is a classical digital signature; ML-DSA is the standardized signature derived from Dilithium. A signature is checked under a public key; the current locally generated signing key does not independently authenticate a remote organization.')
p('Modes are selected for new operations. The system does not automatically re-encrypt all older records when a different mode is selected.')

page('AI research and measured results')
p('The adaptive API currently serves the historical UNSW-NB15 Random Forest. Other datasets support separate research experiments. A good development score is not automatically a deployable result, and no single percentage describes the whole security platform.')
table(['Study','Recorded finding','Interpretation'],[
 ('UNSW official test','89.79% accuracy; 97.65% attack recall; 19.85% false positives','Deployed historical reference; false alarms limit automatic enforcement.'),
 ('CICIoT2023 bounded final','RF 88.510% accuracy; XGBoost 90.396%','Neither passes both 95% recall and 5% false-positive gates; no promotion.'),
 ('2024 microservice SocialNetwork','Best base ML detects 40 of 51 exposure windows, with 3 of 506 selected-control alarms','Grouped development study; exposure is not confirmed malicious behavior in every second.'),
 ('Controlled routed HTTP','97.10% accuracy; 94.07% suspicious-intent recall; 0 alarms among 141 controls','Paired laboratory improvement, but recall misses 95% release gate; non-enforcing candidate.')],[1.55,2.65,2.8])
p('UNSW-NB15 dates to 2015. CICIoT2023 provides IoT traffic, including attack families relevant to broader networking, but does not alone validate microservice behavior. The microservice dataset was published in 2024 and contains 2023 captures. Our controlled HTTP observations come from the project laboratory.')
h('What MLOps means here',2)
p('We preserve preparation scripts, feature schemas, model versions, hashes, experiment results and acceptance gates. Candidates can be rejected while the existing artifact remains unchanged. MLflow supports local experiment tracking. This is controlled model lifecycle work, not a model that retrains itself on every user request.')
h('What we can honestly claim',2)
bullets(['Real profile execution and local round-trip verification have been tested.',
         'The retained 32-case service matrix produced 24 verified envelopes and eight expected downgrade denials, with matching MySQL records.',
         'Richer syscall features and causal history were studied; negative results remain recorded.',
         'Functional API tests, model accuracy and cryptographic strength are different kinds of evidence.'])

page('Presentation and demonstration plan')
h('A clear five minute presentation',2)
table(['Time','Explain or show'],[
 ('First minute','Describe the problem and name the platform responsibilities.'),
 ('Second minute','Show the input fields and the request workflow.'),
 ('Third minute','Explain one policy example and the three algorithm profiles.'),
 ('Fourth minute','Demonstrate a real adaptive operation and its recorded result.'),
 ('Final minute','Summarize the research findings and current limitations.')],[1.3,5.7])
h('Demonstration checklist',2)
numbered(['Check MySQL and required services are ready; use the project runbook rather than launching duplicate instances.',
 'Open the dashboard through its development or hosted HTTP address, not by double-clicking index.html.',
 'Log in with a demonstration account. Do not display real passwords, JWTs or private keys on a projector.',
 'Run a documented synthetic adaptive request. Explain every input before sending it.',
 'Read the actual score, effective risk, selected profile, verification flag and timings. Do not predict a fixed score for arbitrary features.',
 'Match the execution and decision IDs against API or authorized database records. Show what was actually persisted.',
 'If configured test cases are available, show missing-token rejection and HIGH-risk downgrade denial. Do not target external applications.',
 'Explain any failed or unavailable state honestly. A screenshot from a previous run is not a current live result.'])
h('Divide responsibilities',2)
p('Suggested team split: one person explains architecture and authentication; one explains datasets and AI; one explains policy and cryptography; one explains MySQL, dashboard and testing. Everyone should be able to trace the worked example and name the main limitations. Assign actual names within the team.')
h('What to say about attacks',2)
p('Invalid credentials are checked by authentication, and bounded request bursts can trigger configured rate controls. Choosing PQC protects a cryptographic operation; it does not by itself stop DDoS, fix a vulnerable application or guarantee detection of every new attack.')

page('Questions the team should be ready for')
for question, answer in [
 ('Where is AI integrated','AI Security returns a model score to Adaptive Policy. Business uses the checked policy decision, not an AI-generated encryption algorithm.'),
 ('Why have a policy engine','A score alone does not know the sensitivity of a resource or the supported cryptography. Policy combines those constraints and records a reason.'),
 ('Is this already a universal security product','No. Business Service is the integration example. Other applications need adapters, trusted telemetry, identity/key management and workload-specific testing.'),
 ('Does the system currently watch every live request','No. The adaptive API accepts supplied network features. Passive HTTP research collection is separate and does not automatically replace the deployed network model.'),
 ('What does verified mean','The local encrypted envelope was opened and checked under locally generated keys. It is not proof of an independently authenticated remote recipient or full production PQC transport.'),
 ('Can cryptography pass while the request fails','Yes. A later persistence step can fail after verification. FAILED with verified true is possible; STARTED can mean no durable completion is known.'),
 ('Can we claim 99 percent security','No. We report metrics for their exact datasets and splits. There is no defensible single percentage for the complete platform.')]:
    h(question,2); p(answer)
h('Where n8n could fit',2)
p('Recommendation: present the existing diagram and live evidence first. n8n is optional future notification automation, not an implemented core dependency. A possible route is a sanitized security event to an authenticated webhook, followed by an email or report workflow. Keep login enforcement, profile decisions and cryptography inside the backend. Do not send passwords, JWTs, private keys or confidential payloads into such workflows.')
p('Current next work includes trusted telemetry and sensitivity, authenticated key delivery, stronger deployment controls, independent microservice evaluation and external notification verification. n8n does not close those gaps.')
p('Read further in the project: docs/research/paper/main.tex for the research narrative; docs/research/paper-evidence-readiness.md for evidence boundaries; docs/research/rich-context-http-v1.md and socialnetwork-errors-results-v1.md for detector findings. Official n8n webhook documentation: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/')

doc.save(TARGET)
print(TARGET)
print('paragraphs',len(doc.paragraphs),'tables',len(doc.tables),'images',len(doc.inline_shapes))
