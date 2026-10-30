# Paper working sources

October23 current status supersedes historical details below: `main.tex` is a
full-length13-page A4 draft with12 tables,4 figures and16 references including
all11 retained sources. It compiles successfully; all13 exported pages were
visually reviewed. See `pdf-review-2026-10-23.md` for hashes and review evidence.
Reviewed PDF: `output/AI-PQC-research-paper-reviewed-v2.pdf`.
Overleaf: self-contained source,TikZ/pgfplots,inline bibliography; XeLaTeX
recommended (TeX Gyre Termes where available,Times New Roman fallback locally).
No external image or bibliography files required. All figures are native/editable.
The existing confirmed first author is preserved; final additional names/order,
guide details,venue-specific adaptation and actual similarity checking remain.
Current source preflight:168 abstract words,16 refs,all11 retained sources cited,
12 tables,4 figures,defined/unique cross-reference labels and checked arithmetic.
Receipt: `ml/artifacts/paper-preflight-ec458d39c09b4b05839420bf9c359f70/verification.json`.
Neither this draft nor its tests establish publication acceptance/project completion.

## Historical October21 checkpoint (superseded by the review above)

`main.tex` was an initial IEEEtran conference-style draft, not a submission-ready
paper or a claim that the project is complete. It follows the supplied section
outline; exact fidelity to the teacher's Word layout is not yet verified.
Upload the TeX file to Overleaf using IEEEtran; no external images or bibliography
file are currently needed. The first author and affiliation now match the user's
confirmed details. Additional authors and guide details remain unconfirmed.

Export review update:the user exported a four-page PDF. All four pages were
visually reviewed; see `pdf-review-v1.md`. Source now corrects A4/Times-compatible
typography,numeric spacing,citation order and bibliography balance,and compiles
successfully. A new export is required to inspect those corrections. The old
PDF review cannot establish the layout of this revised source.

Source preflight: `scripts/verify-paper-source.ps1` passed with168 abstract words,
eleven defined bibliography entries, the six prescribed sections and consistent
recorded confusion-matrix arithmetic. Receipt:
`ml/artifacts/paper-preflight-4d11278c4a284b5ca2c2a17bdbd70a3f/verification.json`.
This is not a plagiarism, layout or publication-readiness check. The first app
compile timed out. A subsequent compile of the current eleven-reference source
returned success from the desktop editor's compiler. Its result and source hash
are recorded in `ml/artifacts/paper-compile-success-2026-10-21/verification.json`.
The tool does not export a PDF. No rendered pages or exact teacher-template
fidelity have yet been verified. A PDF export is requested from the user for
visual inspection. Rerun preflight after subsequent source changes.

## Before submission

- Confirm any additional authors/order and guide details; first-author details are supplied.
- Review the supplied legacy DOC sample and render the teacher DOCX template.
- Complete the final citation/format audit. Five core retained papers now have
  scoped direct reviews recorded in `literature-review-2026-10-21.md`; eleven
  total references also include standards and dataset records.
- Add an architecture figure and a scope-matched prior-work comparison.
- Validate every assertion and numerical table against the trace map below.
- Inspect every rendered page after exporting the successfully compiled source.
- Produce the teacher-format Word/PDF and requested review PPT.
- Obtain an actual similarity report with the institution's required settings;
  do not claim a score from writing style or a citation check.

## Claim to evidence map

Paths below are relative to `docs/research/` unless noted.

| Draft result | Authoritative evidence to retain |
|---|---|
| UNSW official RF89.79%,recall97.65%,FPR19.85%,confusion matrix | `phase-3-baseline-results.md`; `ml/training/train_baselines.py`; promoted model hash in completion audit |
| CIC RF88.510%,XGB90.396%,both fail gates | `ciciot2023-final-results.md`; `evidence/ciciot2023-frozen-final-v1.json`; frozen local result packet |
| SocialNetwork40/51 vs39/51,3/506 vs2/506 | `socialnetwork-errors-results-v1.md`; `evidence/socialnetwork-errors-results-v1.json` |
| HTTP97.10% vs61.23%,recall94.07%,0/141alarms | `rich-context-http-v1.md`; frozen paired result packet identified there; controlled intent labels only |
|32-case constraint coverage | `adaptive-matrix-results-v1.md`; actual MySQL join receipt identified there |
|24concurrent requests,18verified/sixdenied | `concurrent-adaptive-results-v1.md`; matching database receipts |
| Initial/post-crypto persistence states | `initial-audit-failure-results-v1.md`; `post-crypto-audit-results-v1.md`; current controlled Spring/H2 tests |
|44fresh API/MySQL checks | `submission-live-regression-2026-10-21.md`; actual verification packet identified there |
|180Java collected,175pass,fiveskip | `ml/artifacts/audit-alert-java-regression-v1.json`;54fresh hashed XML reports; package log |
|104frontend checks/build;15monitoring scenarios | `adaptive-audit-alerts-v1.md`; actual UI/promtool artifacts identified there |
| Synthetic audit counter through real Prometheus and administrator API | `adaptive-audit-alert-live-results-v1.md`; state trace,403/503 and cleanup receipts; not a real storage fault |

Do not conflate percentage improvement across these distinct datasets, or
replace classification findings with functional test pass rates. A local
ephemeral-key seal/open check is not production service-to-service PQC transport.
Future implementation changes require updating the draft and evidence revision.

## Source verification October21

Official NIST records were opened for FIPS203,FIPS204 and SP800-204A; UNSW and
UNB dataset pages and the publisher Zenodo record were inspected. The Elsevier
publication metadata was returned by search, but full-page retrieval failed403;
the MDPI article body returned429. Do not claim full-text literature review from
those results. Recheck locally retained PDFs before adding detailed comparisons.
Existing local paper/library hashes remain in `papers-manifest.md`.

Subsequent review:five retained PDFs were extracted locally and relevant methods/
results pages inspected,including rendered P01Tables11/12/26 and P02results.
All five hashes match the tracked index. Those local documents,not failed web
retrievals,support the expanded Related Work section. This supersedes the earlier
pending-local-review statement only for the five sources listed in the new review.

Official links used:

- https://csrc.nist.gov/pubs/fips/203/final
- https://csrc.nist.gov/pubs/fips/204/final
- https://csrc.nist.gov/pubs/sp/800/204/a/final
- https://research.unsw.edu.au/projects/unsw-nb15-dataset
- https://www.unb.ca/cic/datasets/iotdataset-2023.html
- https://zenodo.org/records/10655126
- https://doi.org/10.1016/j.jss.2024.112142

NIST records include potential-update/errata notices; deployment compatibility
requires reviewing applicable corrections, not assuming a standard citation is
implementation certification. No sample/template example references or numbers
are used as project results.
