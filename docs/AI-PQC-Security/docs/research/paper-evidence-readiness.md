# Paper evidence inventory and claim boundaries

Updated 2026-10-23. This is the evidence inventory supporting the paper, not a finished
paper, publication acceptance claim, plagiarism score or literature-superiority
claim. Study files and negative results must remain part of the record.

## Evidence available now

| Evidence | Supported statement | Important boundary |
|---|---|---|
| `ciciot2023-pilot-results.md` | Audited 309 source CSVs, 46,776,700 rows; bounded pilot data cleaning and detection baselines | IoT network data, not microservice HTTP; 90.90% XGB was outer development validation, not final/production accuracy |
| `ciciot2023-capacity-study.md` | Higher-capacity mean internal accuracy 90.035%, weak-family recall 60.926% | Repeated development splits; gates failed; test was unopened during this study |
| `ciciot2023-final-results.md` | One frozen54,552-row reserved-test evaluation: RF88.51%, XGB90.40% accuracy; eight-category80.14% | Bounded pilot only; both binary security gates failed; no promotion; test now exposed |
| `difficult-examples-and-local-traffic.md` | OOF hard-example weighting was evaluated and rejected; actual HTTP controls collected separately | Negative result, not an accuracy improvement; observations cannot be inserted into CIC feature columns |
| `microservice-session-study-v1.md` | Isolated-account HTTP model achieved 97.94% on 194 later requests | Small same-generator lab; per-account histories; no gateway transfer guarantee |
| `gateway-shadow-mode.md` | Default-disabled bounded passive capture and non-enforcing offline scoring work | Early handler-fixture gateway tests were plumbing evidence, not real Auth routing |
| `routed-http-study-v1.md` | Real Gateway/Auth flow, seven disjoint transport peers, frozen final comparison and release rejection | New candidate 64.43% accuracy/30.93% recall; earlier RF 80.41% false alarms on this test; do not hide the drop |
| `rich-context-http-v1.md` | New 24-feature privacy-preserving context pipeline: 97.10% on 276 fresh requests, versus 61.23% matched nine-feature pipeline | Single-host controlled lab; 94.07% recall misses strict 95% gate; no production promotion or external-dataset superiority claim |
| `security-enforcement-progress.md` plus passing Java tests | Auth/JWT checks, peer-based throttling, high-risk classical downgrade denial and crypto functional tests | Functional correctness under tested cases is not formal security certification or unknown-attack protection |
| `socialnetwork-local-import-v1.md` and `socialnetwork-dataset-intake-v1.md` | Public 2024 SocialNetwork subset has verified publisher checksums, project-local copies and recorded provenance | Publication year differs from capture year; syscall records are not compatible with network-flow model inputs |
| `socialnetwork-errors-results-v1.md` | Matched 557-window development ablation: best base logistic detects40/51 exposure windows with3/506 selected-control alarms; error features detect39/51 with2/506 alarms | No eligible model; eight CVE groups and16 recordings; correlated development data, not independent deployment accuracy |
| `initial-audit-failure-results-v1.md` and `post-crypto-audit-results-v1.md` | Controlled Spring/H2 tests distinguish initial write failure, crypto verification and failed durable completion | Not actual MySQL/disk/commit-ack failure or production availability proof |
| `text-first-dashboard-results-v1.md` |102 component tests and production build pass after text-first UI changes | Fresh browser review was blocked by browser policy; component tests do not certify layout/accessibility |
| `papers-manifest.md` and `dataset-references.bib` | Local literature index, exact local PDF hashes and existing dataset bibliography | Recheck actual paper passages/protocols before quoting accuracy, novelty or citation details |

The deployment model remains the separately governed historical UNSW Random
Forest. Its reported official split accuracy is approximately 89.79%, not the
95.8% training-validation figure. No model was trained on a blind concatenation
of UNSW, CICIoT and HTTP observations. The schemas and threat domains differ.
The 2024 public microservice SocialNetwork subset is now present under
`ml/data/raw/microservice-ids-2024/socialnetwork/`; intake, local import and
bounded syscall studies are documented separately. The earlier statement that
it was absent was an October19 snapshot and is superseded. No promoted model
jointly covers all three datasets, and the development exposure-label results
must not be presented as confirmed attacks or independent test accuracy.

## Suitable paper content already supported

Methods can describe the actual service architecture, causal feature contract,
dataset provenance, source/model checksums, peer/session holdouts, grouped CV,
calibration gates, frozen one-shot evaluation, bounded shadow capture and
independent authentication/rate-control checks. Results should distinguish
model classification from actual access rejection and cryptographic execution.

A useful measured research observation is that an apparently strong
isolated-account result did not transfer to peer-aggregated gateway history.
Within this lab, recalibration reduced false alarms only by sacrificing recall.
That is an empirical finding with explicit limitations, not proof of novelty
relative to all published work. Keep baselines and failed candidates in the
results/ablation narrative rather than selecting only attractive percentages.

## Claims currently unsupported

- 99% detection/precision/recall across all checks; perfect AI or universal security.
- Production or external-world accuracy based on a single local generator.
- Superior accuracy to the literature without the same dataset, split, features,
  task definition, leakage controls, prevalence and test protocol.
- Live gateway automatic-response readiness for any rejected candidate.
- End-to-end PQC transport, malicious-bot prevention, free-hosting reliability or
  a production MySQL deployment proved by these HTTP/H2 experiments alone.
- Publication acceptance, guaranteed originality, or a fixed similarity percentage.

## Writing checklist

1. Use the tracked evidence JSON packets as the source for numeric tables;
   preserve confusion matrices, operating thresholds, sample/group counts and
   negative results. Do not mix validation means and final-test measurements.
2. Verify literature claims from the locally indexed papers and their primary
   publication records. Cite algorithms, standards and datasets at the relevant
   statements; do not invent an accuracy for an architecture/PQC paper.
3. Separate a demonstrated prototype/system-design contribution from a
   detection-performance contribution that has not passed its release gates.
4. Explain controlled-intent labels, small sample size, same-host generation,
   shared-peer histories, two-peer uncertainty, and label-information limits.
5. State what remains unmeasured. Independent data and model/schema alignment
   are prerequisites for stronger effectiveness claims, not wording to conceal.

The teacher format and sample are now supplied; deliverables/deadlines are
tracked in `submission-requirements.md`. Expanded Overleaf-compatible draft source
is in `paper/main.tex`, with claim trace map and remaining gates in `paper/README.md`.
Source preflight and desktop-editor compilation pass. The latest exported PDF
has13 A4 pages and all13 were visually reviewed; see
`paper/pdf-review-2026-10-23.md`. It has16 references including all11 retained
sources,12 tables and4 figures. The paper includes the269-input and305-input
negative syscall studies and separate guard. Final author/guide details,
venue adaptation,legacy sample/template fidelity and a similarity report remain.

The rich-context experiment is the newest controlled routed result. Preserve the
earlier failed routed test alongside it; the gain has a paired fresh-test
comparison and broader scenarios, but does not erase the domain-shift finding
or justify automatically enabling AI enforcement.
