// Emit a bounded apply_patch migration; this script never writes source files.
// Only known dashboard files and known imported icon components are considered.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const patch=['*** Begin Patch'];
function appendPatch(file,before,after) {
  if(before===after) return;
  const a=before.split(/\r?\n/),b=after.split(/\r?\n/);
  const table=Array.from({length:a.length+1},()=>new Uint16Array(b.length+1));
  for(let i=a.length-1;i>=0;i--) for(let j=b.length-1;j>=0;j--)
    table[i][j]=a[i]===b[j] ? table[i+1][j+1]+1 : Math.max(table[i+1][j],table[i][j+1]);
  const operations=[];
  let i=0,j=0;
  while(i<a.length||j<b.length) {
    if(i<a.length&&j<b.length&&a[i]===b[j]) {operations.push(' '+a[i]);i++;j++;}
    else if(j<b.length&&(i===a.length||table[i][j+1]>=table[i+1][j])) operations.push('+'+b[j++]);
    else operations.push('-'+a[i++]);
  }
  const ranges=[];
  operations.forEach((line,index)=>{
    if(line[0]===' ') return;
    const start=Math.max(0,index-3),end=Math.min(operations.length,index+4);
    if(ranges.length&&start<=ranges.at(-1)[1]) ranges.at(-1)[1]=Math.max(end,ranges.at(-1)[1]);
    else ranges.push([start,end]);
  });
  patch.push('*** Update File: '+file.replaceAll('\\','/'));
  for(const [start,end] of ranges) patch.push('@@',...operations.slice(start,end));
}
for(const name of ['main.jsx','EvidenceOverview.jsx','OperationalTelemetry.jsx','OperationalAlerts.jsx']) {
  const file=path.join(root,'src',name);
  const original=fs.readFileSync(file,'utf8');
  const imported=/^import\s*\{([^}]+)\}\s*from\s*['"]lucide-react['"];\r?\n/m;
  const match=original.match(imported);
  if(!match) continue; // Idempotent: do not modify unrelated source after migration.
  const icons=new Set(match[1].split(',').map(value=>value.trim()).filter(Boolean));
  if([...icons].some(value=>!/^\w+$/.test(value))) throw new Error('Review non-simple icon imports before migration');
  let source=original.replace(imported,'');
  source=source.replace(/\s+icon=\{<([A-Za-z]\w*)\s*\/>\}/g,(whole,component)=>icons.has(component) ? '' : whole);
  source=source.replace(/^[ \t]*<span aria-hidden="true" className=\{`event-icon[^\r\n]*<\/span>\r?\n/gm,'');
  source=source.replace(/<([A-Za-z]\w*)\b[^>]*\/>/g,(whole,component)=>icons.has(component) ? '' : whole);
  source=source.replace(/<span(?: className="step-icon")?>\{icon\}<\/span>/g,'');
  source=source.replace('<span className={`metric-icon ${tone}`}>{icon}</span>','');
  source=source.replace(/<span className="(?:brand-mark|icon-box(?: [^"]*)?)">\s*<\/span>/g,'');
  source=source.replace('function FlowPoint({icon, title, text})','function FlowPoint({title, text})');
  source=source.replace('function Metric({icon, label, value, detail, tone})','function Metric({label, value, detail})');
  source=source.replace('function JourneyStep({number, icon, title, badge, tone','function JourneyStep({number, title, badge, tone');
  source=source.replace(/<Metric\b[^>]+\/>/g,whole=>whole.replace(/\s+tone="[^"]*"/g,''));
  source=source.replace('<span className="workspace-avatar">S</span>','');
  appendPatch(file,original,source);
}
const styles=path.join(root,'src/styles.css');
const source=fs.readFileSync(styles,'utf8');
const stable=source.replace('.spin{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}','')
  .replace('.primary-button:hover{transform:translateY(-1px)}','');
appendPatch(styles,source,stable);
patch.push('*** End Patch');
console.log(patch.join('\n'));
