import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {randomUUID} from 'node:crypto';

// Use the bundled runtime reported by load_workspace_dependencies, not project dependencies.
const root = process.cwd();
const modules = process.env.REVIEW_RUNTIME_MODULES;
const skill = process.env.REVIEW_PRESENTATION_SKILL;
const python = process.env.REVIEW_RUNTIME_PYTHON;
if (!modules || !skill || !python) throw new Error('Set the three REVIEW runtime paths from workspace dependencies.');
process.env.RUNTIME_NODE_MODULES=modules;
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(modules,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation,resolvePresentationFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const revision=process.env.REVIEW_DECK_REVISION || 'v1';
if(!/^v[1-9][0-9]*$/.test(revision))throw new Error('Use a revision such as v2.');
const build=path.join(root,`ml/artifacts/review-presentation-${revision}-${randomUUID()}`);
const output=path.join(root,'docs/research/presentation/output');
const finalPath=path.join(output,`AI-PQC-review-${revision}.pptx`);
await fs.mkdir(build,{recursive:true}); await fs.mkdir(output,{recursive:true});
try {await fs.access(finalPath);throw new Error('Final file exists. Use a new revision rather than overwrite it.');}
catch(error){if(error.code!=='ENOENT')throw error;}
const font=resolvePresentationFont({fontFamily:'Arial'});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
deck.theme.defaultFont=font;
const ink='#172635', muted='#4B5C6C',accent='#176C78';
const nativeTables=[];
function text(slide,value,left,top,width,height,size=28,bold=false,color=ink){
  const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=value; shape.text.style={typeface:font,fontSize:size,bold,color};return shape;
}
function page(title,notes=''){
  const slide=deck.slides.add();slide.background.fill='#FFFFFF';
  text(slide,title,72,52,1136,100,44,true);
  text(slide,String(deck.slides.items.length).padStart(2,'0'),1150,668,58,26,18,false,muted);
  slide.speakerNotes.text=notes;return slide;
}
function lines(slide,values,top=190,size=30,spacing=84){values.forEach((value,i)=>text(slide,value,76,top+i*spacing,1120,spacing-12,size));}
function table(slide,values,widths,top=175,height=340,size=25){
  const owner=deck.slides.items.length;nativeTables.push(owner);
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:72,top,width:1136,height,columnWidths:widths,values});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);cell.text.style={typeface:font,fontSize:size,bold:r===0,color:r===0?'#FFFFFF':ink};
    cell.fill=r===0?accent:(r%2?'#F3F6F8':'#FFFFFF');
  }
  t.borders.assign({style:'solid',fill:'#D5DFE5',width:1});return t;
}
let s=page('AI-PQC Security','Project title: AI-Driven Adaptive Quantum-Resilient Security Framework for Secure Microservice Architectures. PRM-3 review October29,2026. First author: Yellanki Kranthi Giri Venkata Chary. Email: y.kranthi826@gmail.com. Student, Department of Computer Science and Engineering, Koneru Lakshmaiah Education Foundation, Bowrampet, Hyderabad-500043, Telangana, India. Additional authors/guide remain unconfirmed.');
text(s,'Adaptive security for\nmicroservice architectures',76,190,1100,180,56,true);
text(s,'Project execution review',76,430,1100,60,32,false,accent);
text(s,'Research prototype evaluated on local services and separate detection studies',76,495,1100,75,25,false,muted);
text(s,'Yellanki Kranthi Giri Venkata Chary',76,582,1100,42,27,true);
text(s,'y.kranthi826@gmail.com',76,630,1030,36,23,false,muted);

s=page('What the system does','Sources: docs/architecture/phase-5-adaptive-flow-integration.md; docs/completion-status.md. The endpoint generates ephemeral keys and verifies its own round trip. It is not a transparent production security layer for arbitrary applications.');
lines(s,['A caller signs in and requests protected business data.','The system evaluates a submitted flow and application constraints.','Policy selects CLASSICAL, HYBRID or PQC, or refuses the request.','MySQL records the outcome and monitoring receives audit events.'],175,30,100);

s=page('Services and responsibilities','Sources: current source under backend/ and platform/; docs/architecture/phase-5-adaptive-flow-integration.md. Eureka supports discovery. MySQL is the operational database.');
table(s,[['Service','Responsibility'],['API Gateway','Routing and request controls'],['Auth Service','Registration, password checks and JWT'],['Business Service','Execute protection and record outcome'],['AI Security Service','Score the supported flow representation'],['Adaptive Policy Engine','Apply sensitivity and compatibility rules'],['Security Monitoring','Collect events and restricted operator alerts'],['Eureka','Discover registered services']],[380,756],165,440,24);

s=page('One adaptive request','Sources: backend/business-service/.../AdaptiveSecurityService.java; docs/research/adaptive-matrix-results-v1.md. Flow inputs are currently caller supplied. Authenticating the caller does not prove its submitted features are truthful.');
lines(s,['1   Authenticate the request and create an execution identity.','2   Persist STARTED before policy and crypto.','3   Validate the model-informed policy decision.','4   Seal, open and verify with the selected profile.','5   Save the outcome and publish the audit through an outbox.'],168,28,83);

s=page('Cryptographic profiles','Sources: docs/architecture/phase-5-crypto-agility.md; platform/crypto-agility/hybrid/.../CryptoProfileFactory.java; NIST FIPS203 https://csrc.nist.gov/pubs/fips/203/final and FIPS204 https://csrc.nist.gov/pubs/fips/204/final. X-Wing is the provider composition. No FIPS140 module-validation claim.');
table(s,[['Mode','Key establishment','Signature'],['CLASSICAL','X25519','ECDSA P-256'],['HYBRID','X-Wing','ML-DSA-65'],['PQC','ML-KEM-768','ML-DSA-65']],[290,440,406],185,270,27);
text(s,'AES-256-GCM protects the payload in every profile.',76,495,1100,60,29);
text(s,'Current evidence covers ephemeral-key round trips. Production recipient identity and key delivery remain open.',76,565,1100,82,25,false,muted);

s=page('Model score and effective policy risk','Source: docs/research/adaptive-matrix-results-v1.md. All32constraint cases use one MEDIUM-scored flow with score0.5690423129295029. Sensitivity changes policy risk, not the model output. The latency parameter is a hint, not a hard SLA.');
text(s,'One tested flow scores 0.569 and maps to MEDIUM model risk.',76,180,1100,90,32,true);
lines(s,['Sensitivity can elevate effective policy risk.','Supported modes and the latency hint constrain selection.','HIGH-risk CLASSICAL execution returns an expected denial.'],305,29,82);
text(s,'A score is neither model accuracy nor proof of an attack.',76,585,1100,60,27,false,accent);

s=page('Three separate data domains','Sources: official UNSW https://research.unsw.edu.au/projects/unsw-nb15-dataset; CIC https://www.unb.ca/cic/datasets/iotdataset-2023.html; Flora/Antunes https://zenodo.org/records/10655126; docs/research/socialnetwork-local-import-v1.md. The2024publication contains earlier captures. Data are not blindly concatenated.');
table(s,[['Dataset','Representation','Role in this project'],['UNSW-NB15 (2015)','Network flows','Retained historical model'],['CICIoT2023','IoT network features','Closed bounded pilot'],['Microservice dataset (2024)','SocialNetwork syscalls','Grouped development study']],[360,340,436],185,310,25);
text(s,'The schemas and labels differ. One combined model does not cover all three.',76,550,1100,90,29,false,accent);

s=page('Held-out network results','Sources: docs/research/phase-3-baseline-results.md; docs/research/ciciot2023-final-results.md; tracked frozen evidence. Accuracy, recall and FPR are percentages. These are different evaluations, not a matched cross-dataset improvement.');
table(s,[['Evaluation','Accuracy','Recall','FPR'],['UNSW official test RF','89.79%','97.65%','19.85%'],['CIC bounded test RF','88.510%','86.506%','4.383%'],['CIC bounded test XGBoost','90.396%','91.399%','13.158%']],[470,222,222,222],185,290,26);
text(s,'Neither CIC candidate meets both 95% recall and 5% FPR.',76,520,1100,65,29,true);
text(s,'No eligible replacement was promoted.',76,590,1100,50,27,false,muted);

s=page('Application-specific experiments','Sources: docs/research/rich-context-http-v1.md and socialnetwork-errors-results-v1.md. HTTP labels express controlled intent. Syscall labels express annotated exposure. These are separate experiments with distinct independence limitations.');
text(s,'Controlled routed HTTP',76,180,1100,55,32,true,accent);
text(s,'Rich-context pipeline: 97.10% accuracy versus 61.23% on the same 276 requests. Recall 94.07% misses the 95% release gate.',76,245,1100,120,29);
text(s,'Grouped syscall development',76,400,1100,55,32,true,accent);
text(s,'Base logistic: 40/51 exposure hits and 3/506 control alarms. Error features: 39/51 hits and 2/506 alarms. No accepted improvement.',76,465,1100,125,29);

s=page('Verification and request failure','Sources: docs/research/initial-audit-failure-results-v1.md; post-crypto-audit-results-v1.md. Controlled Spring/H2 injections, not actual MySQL disk faults. Absence of a completed record cannot prove crypto never ran.');
table(s,[['Situation','Recorded meaning'],['Successful request','Verified crypto and completed persistence'],['Crypto verifies, later save fails','FAILED may retain verified=true'],['Initial audit save fails','No policy or crypto execution'],['Fallback persistence also fails','Durable outcome may remain unknown']],[530,606],185,330,25);
text(s,'The dashboard excludes failed requests from successful protection shares.',76,555,1100,90,29,false,accent);

s=page('Current verification evidence','Sources: docs/research/adaptive-audit-alerts-v1.md; submission-live-regression-2026-10-21.md; adaptive-audit-alert-live-results-v1.md.175pass/fiveskip is not180passing. Synthetic counter metrics drive the alert chain, not actual storage fault injection.');
table(s,[['Check','Measured result'],['Full Java package','175 passed, 5 skipped, no failures'],['Dashboard tests and build','104 passed, build succeeded'],['Actual API and MySQL baseline','44 checks passed'],['Prometheus rule scenarios','15 scenarios passed'],['Synthetic alert through real API','Pending, firing, reset observed']],[560,576],175,370,25);

s=page('Demonstration and remaining work','Sources: docs/research/submission-requirements.md; docs/completion-status.md; paper/README.md. This is a preparation deck. No guaranteed originality, similarity score, publication acceptance, production security or99%accuracy claim. Teacher requests paper/similarity by25Oct and PRM3 on29Oct2026.');
text(s,'Demonstration sequence',76,172,1100,55,32,true,accent);
text(s,'Login, inspect a saved decision, compare model score with policy risk, verify the crypto outcome, then inspect related audit events.',76,235,1100,118,29);
text(s,'Remaining acceptance work',76,400,1100,55,32,true,accent);
text(s,'Browser review, trusted telemetry, recipient key identity, production hardening and external email verification remain open. Paper formatting, author details and an actual similarity report are pending.',76,463,1100,145,27);

for(const [i,slide] of deck.slides.items.entries()){
  const png=await deck.export({slide,format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidatePath=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(deck)).save(candidatePath);
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:python,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:nativeTables,
  fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...nativeTables.flatMap(n=>['--require-native-table-slide',String(n)])],
  receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify({finalPath,slides:deck.slides.items.length,result}));
