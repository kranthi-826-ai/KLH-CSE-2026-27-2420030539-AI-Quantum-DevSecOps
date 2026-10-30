# Reviewed literature and comparison boundaries

Five retained user-provided papers were reviewed for the current draft. Exact
PDF hashes match `papers-manifest.md`; page-text extraction and page inventory
are retained locally under `ml/artifacts/literature-review-v1/`. The inspected
pages below support the stated claims, not a claim that every citation or
experiment in every paper has been independently reproduced.

| ID and source | Inspected pages | Reported evidence | Difference from this project |
|---|---|---|---|
|P01,Stasac et al.,Applied Sciences2026,DOI10.3390/app16178889|1,22–26,37–39; Tables11/12/26 visually inspected|100% expected-zone decisions on27designed scenarios; separately Table26 CSIC2010 held-out21,065requests has65.1%zone accuracy,77.7%attack recall at selected20%budget|Risk-zone assignment differs from binary network IDS. Our Java prototype executes classical/hybrid/PQC profiles and records failure semantics; no matched superiority or system-speed claim|
|P02,Binh et al.,Electronics2026,DOI10.3390/electronics15081737|1,7–10; p9results visually inspected|98.41%mean accuracy,std0.06percentage points overfive seeds; approximately100k sampledflows,time-basedsplit,graph/context representation|Our RF uses official predefined UNSW partitions and tabular observations. No matched experiment demonstrates a gain; implementation would require new graph features/evaluation|
|P03,Flora and Antunes,JSS2024,DOI10.1016/j.jss.2024.112142|1,9,14|Sixdetectors,threeapplications and deployment/version scenarios; results include model reuse/risk-tolerance rankings|Our SocialNetwork development subset and exposure/control metrics do not reproduce the whole900h benchmark or its evaluation. No single paper-wide accuracy is extracted|
|P04,Olushola and Meenakshi,Frontiers in Physics2026,DOI10.3389/fphy.2025.1723966|1,22,25; publisher article also retrieved|Authenticated session prototype,ML-KEM-1024/ML-DSA-65/AES-256-GCM,transcript-bound key schedule; separate primitive/session timing scopes|Our ML-KEM-768/ephemeral local round-trip does not authenticate an external recipient. No direct timing comparison or adoption of the paper's broad security claims|
|P06,Matias et al.,Procedia Computer Science2024,DOI10.1016/j.procs.2024.05.148|1,8–10|Gateway/JWT/HTTPS scenarios,54benchmarks repeated10times,latency distributions|Architecture/performance source,not IDS accuracy. Do not disable internal transport security to imitate a faster measured configuration|

## Corrections to earlier summaries

P01's27-scenario100%result must appear with its task and support count. Its
held-out CSIC result is a different evaluation and is included rather than
hidden. Table13's separate scoring-formulation results must not be substituted
for Table26's selected operating-point result. This review cites Table26/27
explicitly and does not reconcile untested differences between those analyses.

P02's98.41% is a five-seed mean in a sampled/time-split graph experiment, not
proof of98.41% on our official predefined test. No percentage-point improvement
is calculated between that paper and our RF. P03 is a multi-case benchmark, and
P04/P06 do not provide a classification percentage to beat. The year in P04's
DOI is2025,while its displayed publication date is January8,2026; preserve the
actual DOI and cite the publication date rather than rewriting the identifier.

## Traceability and access

Local extraction script: `scripts/inspect-research-library.py`. It refuses an
existing output directory, preserves exact inputs and writes only ignored local
text/metadata. No PDFs or extracted full text are added to Git. Key P01/P02
metric pages were rendered and visually checked to confirm table/column meaning.
The publisher Frontiers page was retrieved; MDPI pages returned429 and Elsevier
retrievals failed. The local supplied PDFs therefore remain the direct evidence
for detailed comparisons that publisher access did not re-establish.

Manuscript now cites these five core papers as well as the CICIoT paper,
dataset records and standards. It does not claim exhaustive novelty search,
independent reproduction,publication acceptance or literature-leading accuracy.
The retained P09/P10matrix rows have not been re-reviewed in this batch and must
not silently become newly verified comparison claims.
