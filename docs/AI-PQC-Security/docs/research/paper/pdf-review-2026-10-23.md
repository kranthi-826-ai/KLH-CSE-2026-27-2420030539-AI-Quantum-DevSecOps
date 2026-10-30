# Expanded manuscript export review — October 23

## Final reviewed source and export

- Existing `main.tex` revised in place; same editor remains open.
- Source SHA-256: `266810e57814884420218a823471b20127e4c43ca4f0d06dbdcd5c1095bd87ad`.
- Desktop editor compile: success after the final text revision.
- User export: `C:/Users/ykran/Downloads/document (4).pdf`,224955 bytes.
- PDF SHA-256: `b340c518c06c07c38f50eb5d88e3a29ebee45239252dbd83defe46220d81fa0d`.
-13 pages, A4 approximately595.28×841.89pt; no blank filler pages.
-12 tables,4 figures (two original diagrams,two measured-result graphs),16 refs.
- All13 pages rendered at1.45 scale and visually inspected individually.
- Times New Roman regular/bold/italic fonts embedded for body/heading styles;
  separate math/monospace fonts retained. No clipped tables,overlapping diagram
  text,missing glyphs or unreadable plots observed in the final export.
- References finish on the same final page as the artifact map rather than
  spilling four entries onto a nearly empty extra page.

Rendered pages,export copy,text,page geometry and font receipt:
`ml/artifacts/paper-pdf-review-2026-10-23-trimmed/`.
Reviewed deliverable: `output/AI-PQC-research-paper-reviewed-v2.pdf`.
Original Downloads exports unchanged; no alternate PDF was compiled.

## Iteration record

1. `document (2).pdf`:14 pages. All inspected. Business-to-outbox arrow crossed
   Policy text,state figure slightly wide,and body fonts mixed. Rerouted arrow,
   scaled figure and explicitly selected a Times body font for Unicode engines.
2. First font attempt failed: TeX Gyre Termes unavailable locally. Conditional
   Times New Roman fallback compiled; no system/security changes needed.
3. `document (3).pdf`:14 pages,all inspected. Font/diagram corrected but four
   references spilled onto an almost empty page. Removed duplicated summaries,
   retaining detailed findings and all measured tables.
4. `document (4).pdf`:13 pages,all inspected; final source preflight passes.

## Evidence and writing checks

- Citation-free168-word abstract,six prescribed scientific sections,
  acknowledgment and two reproducibility/reporting appendices.
- All11 retained sources cited; keys and cross-reference labels defined/unique.
  Receipt: `ml/artifacts/paper-preflight-ec458d39c09b4b05839420bf9c359f70/verification.json`.
- Tables/graphs use retained study results; no invented learning curves,attack
  outcomes,accuracy gains or literature-superiority claims.
- Checked actual source contracts:8/15ms heuristic thresholds,HIGH/classical
  refusal,SUCCESS/FAILED/STARTED names and HKDF-SHA256.
- Promoted model remains
  `c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.
  No training,test reopening,promotion or enforcement change in this revision.

## Before submission

Confirm final additional authors/order/guide,target venue/declarations and page
limit; compare teacher legacy DOC/rendered template; obtain actual institutional
similarity report. Existing first-author details retained. No similarity score,
acceptance,formal novelty proof or overall project completion is implied.
