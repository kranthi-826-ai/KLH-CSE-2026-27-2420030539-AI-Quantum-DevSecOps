# Research Journal

## 2026-10-20 — Guarded initial execution audit persistence

- Frozena139be0. Three before-tests failed because initial save bypassed the
  failure/finally guard. Moved it inside without starting policy/crypto first.
- Spring/H2 writer-spy cases now pass:transient failure commits a sanitized
  FAILED record/event;continued failure has no invented durable evidence;distinct
  secondary causes are suppressed and identical exceptions are not self-suppressed.
  All cases verify no policy-client interaction and exact metric deltas.
- Full root179 total/174 passed/five skipped across54 fresh suites;actual44
  API/MySQL baseline passed. Owned services stopped,ports absent,MySQL untouched.
  Frontend/model unchanged;no accuracy improvement or real DB-fault claim.
- Read-only GitHub connector checks confirm correct account/repo write permission,
  but available commit API cannot preserve local commit metadata/hashes. No
  remote writes/history changes;requested ordinary Git sign-in asynchronously.
- Details,hashes/limits:initial-audit-failure-protocol-v1.md/results-v1.md.

## 2026-10-20 — Crypto verification versus failed audit completion

- Frozen38ce71d. Two original Spring/H2 tests failed:failed metrics discarded
  known selection and secondary audit failure masked the primary exception.
  A legitimate FAILED/verified=true row also exposed an overly strict frontend
  assumption;its new App test initially failed. Before artifacts retained.
- Preserve actual crypto proof while marking the whole request failed;never
  count it as successful protection. Persistent write failure retains the older
  STARTED/unknown stored state,throws original with suppressed secondary cause
  and increments an initialized process-local failure-audit counter.
- Actual crypto/transaction/outbox tests verify rollback,failure-event commit
  or absence on persistent failure,metrics and no successful return. Controlled
  H2 enqueue injections are not live MySQL/disk faults.
- Full root176 total/171 passed/five skipped across53 fresh suites;frontend100
  tests/build pass. One intermediate UI failure was an old wording assertion;
  report retained,updated to more accurate recorded wording.
- Actual44 baseline/32 adaptive cases passed;independent MySQL joins all32
  consistent,24 verified/eight denied. Owned services stopped,MySQL untouched.
  No model/accuracy change. Initial audit-write and wider failure cases remain.
- See post-crypto-audit-protocol-v1.md/results-v1.md;earlier snapshot contract
  now explicitly identifies its superseded FAILED/true assumption.

## 2026-10-20 — Typed adaptive failure disclosure boundary

- Five before-tests reproduced raw exception-text disclosure in failed audits
  and public crypto/argument errors. Original XML retained;synthetic markers only.
- Frozen6be230e adds typed fixed policy reasons,generic new failure messages and
  safe legacy read DTOs without rewriting historical storage. New19 unit/service
  and five HTTP/H2 disclosure tests pass;all prior security/crypto tests retained.
- First HTTP assertion expected failed for an invalid-argument message;kept the
  one-failure report and replaced with exact per-category message assertions.
  Optional metadata tally had a typed-variable error;invalid original retained,
  corrected v2 independently verifies fresh XML totals.
- Full root174 total/169 pass/five skip across52 fresh suites.26 verifier/config
  tests pass. Actual44 baseline plus AI/Policy stop/recovery phases passed:
  generic failed reasons in MySQL/read API;verified PQC recovery and null errors.
- Owned services stopped,project ports absent,MySQL/historical data untouched.
  No model/accuracy change. Wider privacy and post-crypto persistence failures
  remain open. See failure-disclosure-protocol-v1.md/results-v1.md.

## 2026-10-20 — Compiled dashboard live and malformed-source browser acceptance

- Actual stack44-check baseline passed. Built production dashboard accepted
  real MySQL-backed normal-user records and created a valid downloadable export.
- Added test-only loopback proxy64b2274:forwards real authentication/reads and
  corrupts only reviewed upstream200 reads. Actual anonymous401 was preserved.
- Browser observed event-stale,then both-stale,initial-both-unavailable/export
  disabled,and healthy recovery. Stale export retained seven valid prior events
  with explicit provenance and three current executions,not injected null rows.
- All26 verifier/config tests pass; prior frontend99/build remains applicable.
  DOM/screenshot/export receipts retained and checked. Negative bodies were
  explicit HTTP injections,not actual backend attack/fault or ML measurements.
- Both sessions signed out; all owned AI/Java/preview/proxy services stopped,
  project ports absent,MySQL untouched. No production/model changes.
- Details,hashes,reproduction/limits:dashboard-browser-contract-results-v1.md.

## 2026-10-20 — Validated dashboard record snapshots

- Two before-tests failed against8db4e78:null event rendering failure and
  string verification flag accepted as truthy by the overview. Receipt retained.
- Added bounded known-field record validation before source acceptance. Reject
  the entire malformed snapshot,not individual records that bias denominators;
  retain valid old data only with explicit stale provenance.401/403 still clears.
- New44 contract cases/four App cases pass; full frontend99 passed,production
  build passed. Actual saved browser export accepted:three executions/six events.
- No fresh live/browser verification or model change is implied. No servers
  started. See dashboard-snapshot-contract-v1.md for requirements,hashes/limits.

## 2026-10-20 — Immediate operational snapshot revocation

- New timing tests reproduced a retained-privileged-snapshot gap:operational
  Promise.allSettled delayed401/403 handling behind slow peers. Initial four
  tests:one pass,three failures; retained the before report.
- Added immediate per-source clearing/cancellation/sign-out or panel locking;
  late aborted/old-token responses cannot repopulate or log out a new session.
- Retained first fixed-code report10/12:two assertions incorrectly included
  the already-completed denial fetch in pending-peer cancellation checks.
  Corrected only that scope; immediate clearing/no-repopulation checks retained.
- Final seven new component/App tests pass;full frontend51 passed,production
  build passed. This is controlled mocked-response timing evidence,not live
  administrator-browser permission-race acceptance. No servers/model changes.
- Protocol,failures,hashes and limits:operational-session-results-v1.md.

## 2026-10-20 — Real dashboard normal-user acceptance review

- Actual44-check backend suite passed before browser sign-in. Created three
  real execution outcomes for a fresh normal user; dashboard showed two
  verified protections and one denied selection excluded from protected shares.
- Desktop1280/mobile390/narrow320px views showed no horizontal document overflow.
  Inspect/related-event navigation,JSON export read-back,normal-user admin denial,
  required login fields and keyboard navigation/logout were observed working.
- Found/corrected misleading empty-search instructions. Frontend44 tests and
  production build pass; screenshots/DOM/export retained in the owned run.
- Browser capture now works; this does not erase earlier capture limitations
  or prove admin visual/WCAG/permission-race acceptance. Temporary viewport reset.
- Stopped owned backend/AI/Vite processes and verified project ports absent;
  MySQL/unrelated apps untouched. Timestamp type mismatch initially refused
  cleanup safely; matching process start instants/paths verified before retry.
- Details and limitations: dashboard-browser-review-v2.md. No model change.

## 2026-10-20 — Bounded concurrent adaptive requests

- Frozen protocol/verifier be576d9; actual binaries from d17924f root package.
  No production-code/model changes or fabricated inference for this experiment.
- Actual44-check baseline passed,then six batches of four mixed requests:
  six CLASSICAL,six HYBRID,six PQC verified envelopes and six expected422
  HIGH-risk denials. Every batch had four overlapping client HTTP intervals.
- All24 execution/policy/event MySQL identities,owners,versions,risks,modes,
  payload hashes and outcomes matched. Denials recorded no crypto work.
  Whole verifier6.55s; client ranges259.455–328.405ms are not throughput/tail SLAs.
- All25 verifier/config unit tests pass,including new crossed-audit guards.
  Owned services stopped and project ports absent; MySQL left running.
- Single user/flow and non-isolated laptop conditions limit generalization;
  no server-parallelism,tenant-isolation,capacity or accuracy improvement claim.
  See concurrent-adaptive-protocol-v1.md and concurrent-adaptive-results-v1.md.

## 2026-10-20 — Adaptive dependency response contracts

- Frozen source/contract d17924f: boxed scores/classifier label retain missing
  JSON fields; validators reject inconsistent risk/correlation, sensitivity
  weakening, unsupported modes and invalid reviewed provenance before crypto.
- Full root package passed150 total/145 passed/five skipped,zero failures/errors
  across50 suites. AI negative/valid-boundary HTTP fixtures26 passed; Business
  added eight malformed decisions plus two omitted/null-score HTTP cases.
- All21 verifier/config tests pass. Actual rebuilt stack passed44 base checks
  and all32 frozen matrix cases; independent MySQL joins confirmed24 verified,
  eight denied and32 consistent execution/decision/event identities/outcomes.
- Owned test service trees stopped; project listeners absent,MySQL untouched.
  No retraining,model promotion or accuracy change. Contract validation is not
  attestation; broader failures/load/trusted telemetry remain open.
- Evidence and limits: dependency-response-contract-v1.md and
  dependency-response-results-v1.md.

Project: **AI-Driven Adaptive Post-Quantum Cryptographic Security Framework for
Distributed Applications**

Started: **2026-10-01 (Asia/Calcutta)**

This is the ongoing record for preparing the research paper. Record meaningful
design decisions, changes, experiments, failures, and limitations as they happen.
Entries distinguish proposals, implementations, historical measurements, and
newly verified results. Do not infer a measured result from a feature existing.
Earlier work below is reconstructed from saved evidence and project documents;
it is not a complete contemporaneous log of every earlier action.

## Evidence index

- [Project scope and publication objective](../PRD.md)
- [Paper inventory and exact local-copy hashes](papers-manifest.md)
- [Literature comparison and comparability limitations](literature-matrix.md)
- [Dataset, split, and iterative experiment protocol](phase-3-experiment-protocol.md)
- [Recorded ML baseline](phase-3-baseline-results.md)
- [Recorded crypto benchmark](phase-5-crypto-benchmark-results.md)
- [System evaluation and claim boundaries](system-evaluation-summary.md)

## Earlier milestones: reconstructed evidence

| Work | Evidence | Status and interpretation |
|---|---|---|
| Microservice foundation, authentication and audit | PRD and system evaluation summary | Implementation and previously reported API evidence; services are currently stopped |
| Binary intrusion model | Baseline report and local `ml/artifacts/baseline-results.json` | Saved experiment dated 2026-09-27; measurements checked on 2026-10-01, training not rerun |
| Adaptive policy and crypto execution | System evaluation summary and architecture documentation | Implemented risk-to-mode flow with recorded decisions; policy/crypto quality must be measured separately from IDS accuracy |
| Crypto performance | Phase 5 benchmark report | Historical local benchmark; results depend on hardware and measurement protocol |
| Dashboard explanations and controls | Frontend source/tests; latest chat verification | Four frontend tests and production build previously passed; full visual browser and live-stack review still pending |

### Baseline measurement retained for comparison

Task: binary normal-versus-attack classification on the official UNSW-NB15
test file, **82,332 records**. The official training file provides training and
validation partitions. Dataset hashes and confusion matrices are in the report.

| Metric | Recorded Random Forest test result |
|---|---:|
| Accuracy | 89.7889% (89.79% rounded) |
| Macro F1 | 89.46% |
| Attack recall | 97.65% |
| False-positive rate | 19.85% |
| ROC-AUC | 98.43% |

Confusion matrix `[[TN, FP], [FN, TP]]`:
`[[29657, 7343], [1064, 44268]]`.
Correct classifications: **73,925 / 82,332**.
Validation accuracy **95.48%** is a separate measurement and must not replace
test accuracy. An individual API attack probability is not model accuracy.
Access to promoted metadata was denied during the current audit, so this check
did not independently establish the currently deployed model's hash.

## 2026-10-01: Publication goal and related-work review

**Decision:** Aim for a strong submission to a reputable peer-reviewed venue,
with an explicit contribution, reproducible experiments, and honest limitations.
Acceptance and superiority over existing work are goals, not guaranteed results.

Closely related work found through publisher and preprint searches:

- [ML-driven adaptive PQC selection in cloud microservices, 2026](https://jidmis.org/index.php/jidmis/article/view/3224): its risk forecasts service-performance/SLA conditions; our prototype uses network attack probability and application constraints.
- [Policy-governed PQC migration for legacy microservices, 2026](https://arxiv.org/abs/2609.14286): focuses on sidecar migration and rollback; our implemented flow selects and executes protection for individual application requests.

**Interpretation:** The broad combination of AI, adaptive policies,
microservices, and PQC already exists. No exact duplicate was established in
this search, but absence of a found duplicate is not proof of uniqueness.
Attack-risk- and sensitivity-aware selection with measured execution overhead
is a candidate contribution requiring comparison and ablation evidence.

The following reported IDS figures were verified against primary publications:

| Source | UNSW-NB15 accuracy reported | Difference from our rounded baseline |
|---|---:|---:|
| [BLOEO feature selection, 2024](https://www.nature.com/articles/s41598-024-67488-7) | 97.60% | 7.81 percentage points above ours |
| [Self-attention explainable IDS, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12618664/) | 97.90% | 8.11 points above ours |
| [SAGEConv-GNN + Transformer, 2026](https://www.mdpi.com/2079-9292/15/8/1737) | 98.41% | 8.62 points above ours |

These differences are arithmetic comparisons of reported numbers. Dataset
partitions, label tasks, preprocessing and sample sizes may differ. They do
not establish a controlled ranking of the methods or overall system security.
Our project has not demonstrated higher accuracy than these papers.

## 2026-10-01: Iterative improvement plan

**Accepted method:** Freeze the study -> validate data -> manage features inside
training folds -> analyse validation errors -> bounded model optimization ->
validation-only threshold/calibration tuning -> repeated checks -> freeze the
recipe -> final evaluation -> controlled integration and rollback evidence.

**Priority:** Reduce false alarms without a substantial loss in attack recall.
Report accuracy, macro F1, recall, FPR, latency and variation together. Retain
unsuccessful experiments and explain trade-offs. Never alter labels or select
settings using the official test metrics.

**Planned candidates:** tuned Random Forest, Extra Trees, and a CPU-feasible
gradient boosting model. These are proposals; no new candidate has been trained
or measured during this discussion.

**Next implementation requirement:** Introduce a validation-only optimization
runner with a separate final-evaluation step. The current baseline runner
evaluates fitted models on the test file and must not be reused as an iterative
test-driven tuning loop. Prior test results are already known; disclose reuse
and add independent generalization evidence where possible.

**Deferred work:** Controlled bot/request-flood tests, final hosting feasibility,
and comparable publication experiments. Cryptographic mode changes alone do
not demonstrate protection against request floods.

## 2026-10-01: Repeated confirmation and frozen XGBoost evaluation

- Status: measured; rejected for promotion.
- Repeated validation: seeds 42, 123 and 2026 all passed calibration gates.
  Selected thresholds were 0.575, 0.575 and 0.585; median frozen threshold was
  0.575. Candidate macro-F1 was 0.9521, 0.9538 and 0.9509 respectively.
- Frozen official test: accuracy 0.8917, macro-F1 0.8879, attack recall 0.9768,
  ROC-AUC 0.9847 and FPR 0.2125 (TN 29,137; FP 7,863; FN 1,052; TP 44,280).
- Historical RF comparison: accuracy 0.8979, macro-F1 0.8946, attack recall
  0.9765, ROC-AUC 0.9843 and FPR 0.1985. XGBoost did not improve the balanced
  deployment objective and was not promoted.
- Evidence: `ml/artifacts/xgboost-repeated-seed-confirmation-v1.json` and
  `ml/artifacts/xgboost-frozen-final-evaluation-v1.json`. The evaluated model is
  retained locally under `ml/models/evaluated/`; the promoted RF is unchanged.
- Limitation: the official test file has historical project exposure. Do not
  use this outcome for further tuning or call it wholly unseen. Future model
  optimization must remain training/validation-only and use separate external
  evidence for a new generalization claim.

## Template for each future entry

## 2026-10-01: Validation-only optimization runner prepared

- Status: implemented; not executed; no new model training or measurement.
- Parent evidence: historical RF validation results in
  `ml/artifacts/baseline-results.json`; baseline files were not changed.
- Change: added `ml/training/validation_sweep.py` with four bounded RF
  configurations, fixed stratified seed-42 split, and predeclared comparison
  gates. Runner reads only the official training CSV and writes a separate
  dated validation artifact if successfully run.
- Guardrails: official test CSV is not loaded, scored, or used for selection;
  no candidate is promoted by this runner.
- Verification: Python syntax compilation and `git diff --check` passed.
  Actual execution was blocked because Windows denied launching the configured
  Python 3.14 interpreter; available Python 3.12 is incompatible with the
  environment's CPython 3.14 NumPy binaries. Therefore there are no new metrics.
- Next: restore a working compatible Python environment, run the validation
  comparison, retain all outcomes, and implement a separately frozen final
  evaluation step before any promotion.

## 2026-10-01: First validation sweep attempt

- Status: trained and measured on validation; report serialization failed, so
  the machine-readable artifact was not written. Results below are transcribed
  from the user's PowerShell output and should be replaced/confirmed by a clean
  successful rerun.
- Dataset/split: official UNSW-NB15 training CSV only; seed 42; 140,272 fit
  rows and 35,069 validation rows; held-out test CSV was not loaded.
- Candidates (validation macro-F1 / attack recall / FPR / accuracy / fit sec):
  RF reference 0.948402 / 0.959571 / 0.055446 / 0.954775 / 47.5;
  shallower RF 0.938771 / 0.944614 / 0.051518 / 0.945850 / 23.9;
  deeper leaf-4 RF 0.947088 / 0.957183 / 0.054196 / 0.953549 / 41.4;
  unweighted RF 0.951975 / 0.981189 / 0.088929 / 0.958796 / 36.7.
- Interpretation: the unweighted RF had the best macro-F1 and recall, but its
  FPR exceeded the predeclared maximum of 0.065446; it is not eligible. The
  other candidates did not exceed baseline macro-F1. No model is promoted.
- Failure and repair: JSON serialization rejected NumPy's boolean type for the
  gate flag after all fits completed. The flag is now converted to a native
  Python boolean. The corrected script passed syntax validation, but this
  session could not relaunch the local Python executable; rerun from the user's
  normal PowerShell to save the artifact and confirm the transcribed metrics.

## 2026-10-01: Strict-results audit and next XGBoost sweep

- Status: prior artifacts verified; next experiment implemented but not yet run.
- Verified strict official-test results: balanced RF accuracy 0.8979 remains
  stronger than unweighted RF 0.8661, XGBoost 0.8565, and XGBoost without TTL
  features 0.8532. The combined random-split result of 0.9539 is a protocol
  demonstration, not an official held-out test result or promoted model.
- Change: added `ml/training/validation_xgboost_sweep.py` with four bounded,
  CPU-feasible candidates, two worker threads, a fixed seed-42 validation split,
  dataset hashing, full validation metrics, and predeclared eligibility gates.
- Guardrail: the new runner opens only the official training CSV. It neither
  loads the official test CSV nor promotes a model. An eligible model is saved
  only as a validation candidate for subsequent repeated-seed confirmation.
- Execution status: pending on AWS or another permitted Python environment.
  Do not disable endpoint protection or firewall controls to run it.

## 2026-10-01: Threshold-calibration experiment prepared

- Status: implemented and measured; validation candidate only.
- Motivation: `xgb_depth8_regularized` reached validation accuracy 0.9593,
  macro-F1 0.9528 and attack recall 0.9770, but its FPR of 0.0783 exceeded the
  predeclared 0.0604 ceiling. It was not promoted or evaluated on official test.
- Method: split only the official training CSV into 70% fit, 15% calibration
  and 15% untouched validation partitions. Select the threshold on calibration
  under fixed FPR and attack-recall constraints, then evaluate it once on the
  untouched validation partition.
- Comparison: train the balanced Random Forest reference on the identical fit
  rows and require the calibrated candidate to beat its validation macro-F1.
- Measured calibration selection: threshold 0.575, accuracy 0.9591,
  macro-F1 0.9530, attack recall 0.9678 and FPR 0.0595.
- Untouched validation result at threshold 0.575: accuracy 0.9583,
  macro-F1 0.9521, attack recall 0.9667, ROC-AUC 0.9939 and FPR 0.0598
  (TN 7,898; FP 502; FN 596; TP 17,306).
- Same-split RF reference: accuracy 0.9550, macro-F1 0.9486, attack recall
  0.9604 and FPR 0.0564. The candidate improves accuracy, macro-F1 and recall
  while adding about 0.33 percentage points FPR, remaining below the fixed
  6.04% ceiling.
- Runtime: XGBoost fit 10.7 seconds; Random Forest reference 33.9 seconds.
- Evidence: `ml/artifacts/xgboost-threshold-calibration-v1.json`; local
  candidate bundle `ml/models/candidates/xgboost-threshold-calibration-v1.joblib`.
- Guardrail: official test CSV remains unopened; passing creates only a local
  validation-candidate bundle containing the fitted pipeline and threshold.

- Date/time and run/change ID:
- Question or hypothesis:
- Status: proposed / implemented / measured / reproduced / rejected:
- Previous baseline and parent run:
- What changed and why:
- Dataset/source, license, hashes, split and feature schema:
- Model/preprocessing/threshold settings, seeds and code revision:
- Test command or reproducible procedure and environment:
- Measured results, repeat variability and evidence artifact paths:
- Failures, negative results, resource cost and limitations:
- Interpretation and claim supported:
- Next action and reason to keep/reject/promote:

For architecture or UI changes, mark model/dataset fields not applicable.
Keep raw data, credentials, tokens and protected payloads out of this log.
Link safe reports and versioned configurations. Record a commit or model hash
only after it has actually been verified.

## 2026-10-19 — CICIoT2023 first pilot (measured, no promotion)

- Run IDs: `ciciot2023-pilot-v1`, `ciciot2023-pilot-validation-v1`.
- Audit: 309 CSVs, 46,776,700 rows, 39 numeric predictors, 34 labels. This local
  release derives labels from attack filenames. Every source checksum is saved.
- Quality: 1,449 missing cells and 1,037 infinite cells; preparation excluded
  1,040 unique invalid rows. Conflicting exact model-input vectors were excluded
  from the bounded pilot. All 34 labels remain present in each partition.
- Frozen partition sizes: 230,242 train; 40,354 calibration; 54,597 validation;
  54,552 reserved test. Whole source files are held out where there are enough
  files; sparse labels use contiguous ranges. Capture independence is unproven.
- Binary RF: validation accuracy 0.888840, macro-F1 0.857713, recall 0.869214,
  false-positive rate 0.041441, fit time 16.93 seconds.
- Binary XGBoost: validation accuracy 0.909043, macro-F1 0.874760, recall
  0.917707, false-positive rate 0.121738, fit time 4.83 seconds.
- Eight-group XGBoost: validation accuracy 0.775574, macro-F1 0.707496;
  fit time 15.38 seconds. BruteForce/Web-based/Recon remain weaknesses.
- No calibration threshold met the predeclared recall >=95% and FPR <=5%
  requirements. No candidate was deployed and the reserved test was not opened.
- Seed 20261019; source/partition hashes, parameters, environment and the
  training-script hash are recorded in the local evidence JSON files.
- Six data preparation/validation tests passed. Candidate binaries and raw
  partitions remain Git-ignored. See `ciciot2023-pilot-results.md` and
  `ciciot2023-study-plan.md` for complete interpretation and next hypothesis.

## 2026-10-19 — Family weighting and enforcement safeguards

- Run: `ciciot2023-family-refinement-v1`. Four predefined recipes were selected
  and calibrated only inside the frozen training partition. Plan and code hash
  saved before fitting. Outer calibration, validation and reserved test stayed
  unopened because no internally eligible recipe met recall >=95% and FPR <=5%.
- Best internal diagnostic: deeper family-weighted XGBoost, 89.84% accuracy,
  87.87% macro-F1, 87.96% attack recall, 60.04% weak-family recall and 4.83% FPR.
  Weak-family recall improved from 56.57%, but failed the promotion requirements.
  No repeated-seed confirmation was triggered and no model was deployed.
- Implemented independent gateway token buckets and HTTP 429/Retry-After
  enforcement. Identity uses the peer address; bucket memory is bounded.
- Business Service now rejects HIGH-risk classical downgrades, inconsistent
  policy mode/profile pairs, mismatched correlation IDs and invalid scores.
  Valid-but-unacceptable decisions retain failed-execution audit evidence.
- Full Maven build passed; targeted final Java reports total 49 passing tests.
  Real local HTTP tests verify gateway blocking and H2-backed authentication.
  Python suite: 10 passed. MySQL-backed deployment and live network feature
  extraction remain unmeasured in this iteration.
- Reports: `ciciot2023-family-refinement-results.md` and
  `../security-enforcement-progress.md`. Raw data and protected credentials are
  excluded from tracked evidence.

## 2026-10-19 — Capacity comparison and repeated-split checks

- Run: `ciciot2023-capacity-study-v1`; nine model fits, three recipes, seeds
  42/123/2026, four threads. End-to-end duration 122.88 seconds.
- Only frozen training data used, internally split 70/15/15 by subtype.
  Thresholds selected on calibration. Outer calibration, validation and reserved
  test were not opened. Repeats share data and are not independent external tests.
- Mean reference accuracy 89.855%, macro-F1 87.875%, attack recall 88.068%,
  weak-family recall 60.353%, FPR 5.070%.
- Higher-capacity XGBoost: 90.035%, 88.072%, 88.294%, 60.926%, 5.022%
  respectively. Weak-family recall improved 0.573 percentage points, but
  all-seed recall/FPR gates failed. Extra Trees was inferior. No deployment change.
- 21 Python tests passed. Full parameters, environment, hashes, confusion
  matrices, subtype recall and timings are tracked in
  `evidence/ciciot2023-capacity-study-v1.json`; interpretation and limitations
  are in `ciciot2023-capacity-study.md`.
- Next hypothesis: improve representative difficult-attack/benign coverage and
  actual application signals, not unlimited tuning of this development sample.

## 2026-10-19 — Difficult-example mining and controlled HTTP collection

- Training-only run `ciciot2023-difficult-examples-v1`: three seeds; three-fold
  out-of-fold error mining inside fitting; double weights for errors; separate
  calibration/internal validation. No new raw rows, outer partitions untouched.
- Fifteen fits completed in 79.38 seconds. Mean accuracy declined from 90.035%
  to 89.830%, weak-family recall from 60.926% to 60.059%, FPR increased from
  5.022% to 5.077%. Rejected; no deployment change or 99% claim.
- Real local Auth Service with ephemeral H2: 22 HTTP observations collected in
  3.19 seconds; registration/login/authenticated access succeeded; all 15
  wrong-password/missing-token/invalid-token probes returned 401. Outbound
  monitoring publisher stubbed. No gateway, MySQL, PCAP or AI detection measured.
- Outcomes verify scoped controls, not model accuracy. Harness intent and
  post-response measurements are kept separate from model inputs. No passwords,
  tokens, response bodies or user identifiers retained in tracked observations.
- Python tests: 33 passed. Opt-in real-HTTP Java collection and ordinary auth
  test run passed. Reproduction wrapper stops its isolated test server on exit.
- Full protocol, limitations and next collection requirements are in
  `difficult-examples-and-local-traffic.md`; two tracked evidence JSON files
  preserve the measured negative result and lab observations.

## 2026-10-19 — Session-separated HTTP detector baseline

- New project-specific dataset, not a merged CICIoT/UNSW dataset: 1,056 actual
  HTTP requests to isolated Auth Service/H2 across 60 fresh accounts/sessions.
  Collection took 59.37 seconds; setup requests 120, study observations 936.
  Normal mistakes and legitimate bursts are explicit benign-intent controls.
- Chronological phases: train 36 sessions/557 requests, calibration 12/185,
  final test 12/194. Group CV keeps each session intact. No session identifiers,
  scenarios, labels or current response outcomes are model predictors.
- Nine client-harness pre-request features capture route/header context and
  strictly earlier completed-request/failure history. Server-side identity and
  feature collection/inference integration remains future work.
- Compared two predefined candidates on grouped training CV; selected Random
  Forest; calibrated threshold ~0.55. Froze model/code/data hashes, then ran the
  one-shot final evaluator. No retuning after final-test exposure.
- Final controlled-lab accuracy 97.938%, macro-F1 97.937%, suspicious-intent
  recall 95.876%, confusion matrix [[97,0],[4,93]]. History-rule accuracy 88.660%.
  These are NOT production, CICIoT improvement or prevented-attack percentages.
- Session-cluster intervals expose uncertainty: recall 93.44–98.48%. Zero
  observed FPs on 97 benign requests/six sessions does not prove zero real FPR.
- Automatic responses remain disabled and no candidate was promoted. Existing
  deployed UNSW model hash is unchanged. CICIoT reserved test remains unopened.
- Python suite 45 passed; full Maven reactor 49 passed/two opt-in tests skipped;
  explicit session collection test passed separately. Session test server stopped.
- Full evidence: `evidence/microservice-sessions-v1.json`; protocol, limitations
  and reproduction: `microservice-session-study-v1.md`. Next: trusted shadow-mode
  gateway instrumentation and independent later-run/client validation before
  any production automatic-response integration.

## 2026-10-19 — Gateway passive observation, no automatic enforcement

- Added a default-disabled auth-route observer with causal peer history,
  bounded memory/background queue and a 10 MiB output cap. Tokens, bodies, raw
  IPs and user-supplied identity headers are not stored. Incomplete/async/error
  responses are dropped rather than falsely labelled with a final status.
- Added offline scoring of completed snapshots with the unchanged frozen
  HTTP-lab model. It validates the model hash and feature schema, rejects bad
  data/overwrites and never enables an enforcement action or reports accuracy.
- Real gateway/test-downstream fixture responses: 401/401/401/429/200. Forged
  forwarding/session headers did not bypass the rate limiter or reset histories.
  An allowed fixture could receive a would-alert without being blocked.
- First successful snapshot: five observations/four would-alerts; independent
  wrapper repeat: five/three. This is plumbing/identity-shift evidence, not an
  accuracy benchmark. Per-peer gateway histories differ from per-account
  training; no deployment promotion or 97.94%-transfer claim is supported.
- Initial test-only route override failed due to missing ID/URI; corrected and
  rerun with a fresh output file. Failed evidence was not overwritten.
- Python: 51 tests passed. Gateway: 18 passed. The reproduction wrapper ran
  capture and passive scoring end to end. Full-project regression is checked
  separately before handoff. Existing promoted models remain unchanged.
- Protocol, privacy limits, configuration and remaining real routed-client
  validation: `gateway-shadow-mode.md`; snapshots/scores:
  `evidence/gateway-shadow-v1.json`. No MySQL or external hosts were used.
- Final full Maven reactor passed: 57 passing/two opt-in skipped, zero errors
  or failures. Existing promoted model binary hash was independently rechecked.

## 2026-10-19 — Real routed peer-holdout dataset and release rejection

- Actual Gateway-to-Auth/H2 collection: 1,056 HTTP requests, 60 accounts/sessions,
  seven actual bound loopback transport peers; 62.17 seconds. Joined 936 labelled
  observations to server-generated shadow IDs; replaced client features with
  gateway pre-request features. Three/two/two peers are disjoint across splits.
- Leave-one-training-peer-out model selection picked logistic; development
  calibration recall 32.58% at FPR 4.17% was ineligible. Frozen one-shot final
  test: 64.43% accuracy, 30.93% recall, 2.06% FPR, [[95,2],[67,30]]. Rejected.
- Same held-out requests, unchanged per-account RF: 58.25% accuracy, 96.91%
  recall, 80.41% FPR. This contradicts any claim that the old 97.94% transfers.
- A bounded training-only partial-AUC selection study compared four recipes;
  RF won, but development calibration recall was only 37.08% at 4.17% FPR.
  No old final-test access, no new holdout consumed, no promotion.
- Outcome audit: all 471 controlled suspicious requests returned 401; benign
  intent yielded 435 expected 200s and 30 expected user-mistake 401s. This is
  authentication evidence, not AI accuracy or universal prevention.
- Independent real routed controls: 19 requests, 12 concurrent valid reads all
  200 with correct principal; missing/malformed tokens and wrong passwords 401;
  exhausted test bucket 429/Retry-After despite forged forwarding headers.
- Python suite 59 passed. Full Maven reactor 57 passed/five opt-in skipped;
  routed collection and control tests passed explicitly. Initial route-property
  startup failure was repaired; failed artifacts preserved, fresh directory used.
- Evidence: `evidence/routed-http-study-v1.json`; interpretation:
  `routed-http-study-v1.md`; paper preparation: `paper-evidence-readiness.md`.
  No automatic AI responses, no existing deployment changes, no paper drafted.
- Weekly usage guard: initial tool reading 23% used/77% remaining; checked
  between batches and kept below the 30%-used ceiling. Readings are account-wide
  and coarse; no precise 7-percentage-point consumption guarantee was made.
- Final checkpoint in this batch: 25% used/75% remaining. Preserved more than
  the requested 70% reserve; stopped further model-search work after the failed
  gates rather than consuming the remaining allowance on an exposed benchmark.

## 2026-10-19 — Rich context representation and large fresh-test gain

- Predeclared hypothesis: add causal route/credential-context history without
  removing aggregate peer/churn evidence. Twenty-four numeric inputs; no current
  outcome, token bytes/digests, identity or label inputs. Random per-process
  HMAC context keys stay in bounded gateway memory and are never logged.
- New collection: 1,478 actual Gateway-to-Auth/H2 requests in 88.11 seconds;
  1,318 labelled rows, 80 sessions, seven actual loopback peers. Original six
  scenarios plus legitimate token refresh and rotated same-format corrupt JWTs.
- Train 774 rows/48 sessions/three peers; calibration 268/16/two; fresh final
  276/16/two. Groups disjoint. Same three-model grouped-CV search budget for rich
  and base features, calibration separate, freeze before one final evaluation.
- Rich RF: final accuracy 97.101%, macro-F1 97.094%, recall 94.074%, FPR 0/141,
  [[141,0],[8,127]]. Matched nine-feature pipeline: 61.232% accuracy/31.852%
  recall/10.638% FPR. Gains +35.870 accuracy and +62.222 recall points on the
  same fresh test. Old fixed peer reference: 60.507% accuracy/23.704% recall.
- Predeclared large-gain target passed; strict 95% final recall gate failed.
  No promotion or automatic response enabled. Results remain lab-only, not new
  CICIoT/UNSW metrics or literature-superiority claims. Both pipelines selected
  different algorithms: no fixed-estimator causal attribution is claimed.
- All four suspicious scenario types had two misses; zero benign test alerts
  does not establish zero real FPR. Two-peer uncertainty is weak and descriptive.
- Python 65 passed; full Java reactor 60 passed/five opt-in skipped; real rich
  routed collection passed explicitly. Reproduction wrapper and complete frozen
  evidence are in `rich-context-http-v1.md` and `evidence/rich-context-http-v1.json`.

## 2026-10-20 — Public SocialNetwork dataset intake

- Verified Zenodo record 10655126, release date 2024-02-13, CC BY 4.0;
  June 2023 timestamps observed in validation. Downloaded subset is not the
  entire three-application 900-hour dataset.
- All three complete download MD5 checksums match publisher values. Inspected
  all four validation tar inventories (46 headers each), six explicit normal
  experiment annotations, and eight syscall lines through bounded nested ZIP
  reading. No full extraction, test trace access or training yet.
- Validation plain workloads cannot establish attack recall. Locust task names
  contain `attack` even in normal runs; never use this as ground truth.
- Added bounded read-only inspector and three tests; full ML suite 68 passed.
  Separate syscall/time-window model preparation is next. Existing promoted
  model and unrelated frontend changes are untouched. Detailed provenance and
  protocol: `socialnetwork-dataset-intake-v1.md`.

## 2026-10-20 — Bounded public syscall reference training

- Completed training tar metadata inventory (27 headers). Preserved command
  and scaling interval exclusions; training normality/contamination remains
  incompletely established. Attack traces remain unopened.
- Built streaming first-entry ZIP/deflate prefix reader with 500k-event/128MiB
  caps, 29 identity-free syscall window features and annotation timezone tests.
- Trained fixed 128-tree Isolation Forest reference baseline, no model search.
  Parsed 1.5 million events, retained 2,977 training-reference windows.
- Corrected pre-annotation timing contamination in normal evaluation; retained
  original preliminary v1. Corrected v2 calibration: 109/2,191 alarms (4.975%);
  separate normal recording: 53/2,244 (2.362%). No attack accuracy/recall claim.
- Full ML suite 75 passed; promoted model checksum unchanged. Candidate remains
  experimental, offline, non-enforcing. Runtime 7.38s excluding intake scans.
  Evidence: `socialnetwork-reference-pilot-v1.md` and matching evidence JSON.
  Next: attack interval/container annotation verification before frozen scoring.

## 2026-10-20 — Frozen public syscall exposure evaluation

- Verified four attack metadata inventories; handled seconds/nanoseconds
  explicitly and joined exact pod names/intervals with matching annotations.
- Frozen model scored all eight scenario5/plain_workload/collection1 CVEs,
  both worker traces; all sixteen reached annotation end within scan caps.
  8/8 cases had an alert; observed overlap windows 20/26 flagged (76.92%),
  fully contained 8/11 (72.73%). This is NOT 100% accuracy or exploit-success
  verification. No models or thresholds changed after seeing attack results.
- Added control protocol before viewing exposure scores/outcomes: same-pod
  windows 60–10s before injection. 7/276 alarms (2.54%), not a proof of clean
  hosts. Preserve domain-shift/within-recording correlation limitations.
- Exposure/control jobs completed in 75.60s/78.38s; full suite 79 passed.
  Audited plan/model/code hashes, coverage, labels and threshold decisions.
  Promoted model unchanged, no enforcement. Unscored scenarios1/3/7 and
  collection2 remain available for genuinely frozen future evaluation.
  Details/evidence: `socialnetwork-exposure-evaluation-v1.md` and evidence JSON.

## 2026-10-20 — Expanded reference coverage, negative result

- Fixed-recipe expansion across both workers/trace segments:2m events,
  14,700 reference windows versus2,977; no complete eight-day coverage claim.
  Same calibration/check rows and threshold rule;58.45s preparation/fit.
- Replay-verified302-row exposed-development cache reproduces every prior
  frozen score within1e-12. Labels/identifiers excluded from input features.
- Expanded exposure alerts18/26 (69.23%) versus20/26; pre-injection alarms
  70/276 (25.36%) versus7/276; separate June-normal92/2,244 versus53/2,244.
  Both candidates still alert in8/8 cases, hiding the window/control failures.
- Rejected replacement; no selection/promotion/enforcement, no final test
  consumed, no threshold search. Existing promoted model hash unchanged.
  Full ML suite81 passed. Preserve original and failed candidates as evidence.
  Next investigate workload distributions/service-role conditioning, not blindly
  add more training. Report: `socialnetwork-reference-expansion-v1.md`.

## 2026-10-20 — Role conditioning and grouped supervised development

- Collector-observed service-role map covers cached groups without exposing
  replica identity as a feature. Nginx is453/14,700 training rows versusall302
  development rows; descriptive marginal feature shift observed. Cause unproven.
- Fixed normal profiles for13/25 roles;12 without calibration abstain.
  Normal-check49/2,244 alarms; exposure9/26; controls12/276;7/8 cases alerted.
  Rejected. Missing roles cannot be counted as benign/covered.
- Three fixed supervised recipes, leave-one-CVE-recording-group-out8 folds,
  threshold0.5. Logistic TP20/FN6/FP2/TN274; RF18/8/1/275; XGB17/9/0/276.
  All fail95% exposure recall gate; no selected model or final-test consumption.
- Full ML suite88 passed, promoted model unchanged. Plans, negative results,
  folds and role-support limits documented in
  `socialnetwork-role-and-supervised-study-v1.md` and matching evidence JSON.
  Next: richer syscall representation and additional recording-level examples,
  not blindly longer runs or weaker gates.

## 2026-10-20 — Richer syscall representation, matched negative result

- Added269-feature schema: unchanged29 base plus finer entry frequencies,
  selected syscall counts and within-thread transitions. Arguments/IDs excluded;
  transitions bounded by thread/container/window. No raw-data extraction.
- Reconstructed exactly302 existing development windows; all old feature values
  and labels identical. Same three recipes/eight grouped folds/fixed0.5 threshold.
  Base metrics reproduce previous study exactly.
- Rich logistic TP19/FN7/FP11/TN265; RF18/8/3/273; XGB17/9/0/276.
  No improvement or95% recall gate pass. No selected model or final-test access.
  Full suite90 passed, promoted model unchanged; negative evidence retained in
  `socialnetwork-rich-features-v1.md` and matching evidence JSON.
- Next prioritize additional recording-level development examples rather than
  more model complexity on the same26 positive windows.

## 2026-10-20 — Additional development recordings and concentrated misses

- Predeclared all scenario5/collection2 as development before trace decoding;
  protocol/code committedc6c2b9b before model scores. Other scenarios unscored.
  Preserved302 old rows, added255;557 total/51 exposure/506 controls/16 records.
  Both workers scanned for every new case; annotation-time containment checked.
- Same29/269-feature comparisons, three recipes, threshold0.5; both records of
  each CVE held out together in8 folds. Base logistic TP40/FN11/FP3/TN503
  (78.43% exposure hits,0.593% controls), macro-F10.91867. All candidates still
  fail95% recall; no selected/promoted model or independent-test consumption.
- Nine of11 logistic misses belong to CVE-2022-0492. Kept the difficult group;
  do not exclude it to inflate metrics. Exposure windows have selected syscall
  activity, but labels do not certify malicious action/attack success each second.
- Full suite93 passed, promoted model unchanged. Results documented in
  `socialnetwork-development-expansion-v1.md` and corresponding evidence JSON.
  Next hypothesis: causal multi-window behaviour, never future events/labels.

## 2026-10-20 — Budget guard and pending temporal hypothesis

- Verified weekly usage6% used after a0%-used reset checkpoint; user allowance
  is seven percentage points. Stopped before starting another training batch
  to avoid overrunning coarse account-wide usage readings. Renewed budget
  approval is needed for further experiments; no reset credit used.
- Saved `socialnetwork-temporal-protocol-pending-v1.md`. No temporal training
  has run. Important methodological guard: filtered development rows omit
  pre-injection/unlabeled history, so reconstruct continuous raw context before
  temporal features; do not fabricate zero histories from missing cache rows.
- Goal remains incomplete:95% development recall and independent validation
  are not achieved. Existing88/90/93-test study evidence and negative results
  remain preserved; no candidate promotion or enforcement change.

## 2026-10-20 — CICIoT2023 bounded study closed with final negative gates

- User prioritized finishing CICIoT testing before more microservice training.
  Froze saved RF/XGB/eight-category bundles, manifests, code and thresholds
  before loading the54,552-row reserved test. Exclusive marker prevents reruns.
- RF accuracy88.510%, recall86.506%, FPR4.383%; XGB90.396%,91.399%,13.158%.
  Neither passes95% recall/5% FPR, so no winner/promotion/enforcement change.
  Eight-category accuracy80.140%, macro-F10.73903. All negative results retained.
- Bounded training/calibration/development/final-test study complete, NOT all
  46.8m-row training or production readiness. Test is now exposed: no future
  tuning on it. Full suite95 passed; final artifact/hash/CM checks verified.
  Evidence and handoff: `ciciot2023-final-results.md` and tracked summary JSON.

## 2026-10-20 — Authorized causal history experiment, gates still failed

- User removed percentage restriction. Rebuilt70s continuous contexts from32
  development traces, constructed history before label selection and preserved
  all557 original rows/269 feature values/labels plus canonical training order.
-305 features, same recipes/eight CVE-group folds/0.5 threshold. Temporal
  logistic TP39/FN12/FP20/TN486; RF36/15/0/506; XGB36/15/1/505. Base/rich
  metrics reproduce previous study. No selected temporal model or final test.
- Separate posthoc explicit frontend execve/execveat guard: ML OR guard
  TP41/FN10/FP3/TN503. Only one additional window; not a pure-ML improvement
  or a production blocking policy. Gates still failed, no promotion/enforcement.
- Full suite100 passed; model checksum unchanged; unrelated UI edits preserved.
  `socialnetwork-temporal-study-v1.md` documents causality tests, negative results
  and labeling/observability review needed before another model search.

## 2026-10-20 — Project-local source and completion audit

- Copied all three SocialNetwork ZIPs and publisher README into the canonical
  project-local raw folder. Publisher MD5 and source/destination SHA-256 match;
  Downloads originals preserved, no bulk extraction, raw data stays Git-ignored.
- Added safe import/inspection entry points and path tests. Historical plans
  retain their source paths. No new model training or accuracy claim from copying.
- Verification: ML 102 passed; frontend eight passed and production build passed;
  Java 65 tests total, five skipped, zero failures/errors. Live routed/MySQL and
  browser acceptance are NOT proven by those checks.
- Added `docs/completion-status.md` to retain full PRD scope and distinguish
  achieved checks from remaining live, model, deployment and publication gates.

## 2026-10-20 — Frozen-prediction observability audit

- Reused unchanged grouped OOF predictions and all 557 original observations;
  verified hashes/order and annotation overlap without opening raw archives.
- Same40/51 exposure hits,3/506 control alarms. At least one exposure alert in
  15/16 recordings is a separate posthoc diagnostic, not a replacement gate.
  Nine misses are CVE-2022-0492; one entire recording is undetected. Full-second
  misses and absent execution syscalls show that boundary trimming/exec guards
  alone do not solve it. Labels and difficult observations are unchanged.
- Added exclusive-output auditor and three tests; full suite105 passed. No
  training, promotion, enforcement or independent-test consumption. See
  `socialnetwork-observability-audit-v1.md` for interpretation and next boundary.
- MySQL listens locally but root.env and required runtime variables are absent.
  Requested local secret setup without asking user to disclose passwords.

## 2026-10-20 — Actual-service MySQL and responsive dashboard verification

- User saved DB_PASSWORD locally; verified direct SQL and all seven services
  with temporary in-memory development keys. No secrets were printed/committed.
- Added bounded loopback launcher/live verifier and process-ownership stop
  helper.21 checks passed, including all three verified crypto modes, SQL rows,
  wrong/tampered/anonymous rejection, downgrade rejection and real audit delivery.
- Preserved partial failed-run evidence. Fixed gateway no-instance exceptions
  that surfaced as500 instead of controlled503; four tests cover handling.
  Found startup event loss from missing publisher discovery cache: still open,
  not concealed by the successful steady-state flow. Durable outbox is next.
- Actual browser login, phone390 layout/no document overflow, PQC selection,
  related-event filtering, JSON export and sign-out verified. Stopped the owned
  Monitoring process to prove partial failure: events became stale while the
  execution retrieval remained current. Existing data is retained with times.
- Dashboard fixes distinguish selected/rejected modes from verified execution,
  exclude failed selections from protection shares, preserve per-source export
  provenance and bound API requests to15seconds. Existing design work preserved.
- Final checks:18 frontend tests/build passed;110 ML+inference tests passed;
  Java69 total/five skipped/zero failures/errors. Test processes and preview
  stopped, MySQL untouched. No model retraining/promotion or accuracy gain.
- Evidence, exact measured latency and limitations: `docs/live-verification.md`.

## 2026-10-20 — Durable audit delivery and real restart/outage acceptance

- Replaced best-effort Auth/Business publishing with service-owned MySQL outboxes
  through a shared library. Registration and terminal execution/event writes are
  atomic; persistence failure prevents successful acknowledgement. Retries use
  stable event IDs, row locks, capped backoff and retained dead letters/metrics.
- Collector acknowledges identical retries and rejects changed content for the
  same ID without overwrite. Canonical time comparison uses DB microseconds.
- Transaction, backoff, reconstruction, dead-record and concurrent-claim tests
  pass. Additional actual HTTP conflict handling was required after a negative
  live run; logs/results retained, not counted as a fully passing outage test.
- Final real MySQL run092e9e53c4884c44aa5bb1f6229cd892:21 normal live checks
  pass; Monitoring stopped, pending event retained through an actual Auth process
  restart, Monitoring recovered, one stored event, identical retry200/conflict409.
- Java81 total/76passed/five skipped; Python110passed; frontend18passed/build
  passed. Owned processes cleaned up, MySQL untouched. Promoted model unchanged;
  reliability work is NOT a model-accuracy improvement or exactly-once claim.
- ADR0003 supersedes the historical best-effort ADR0001. Full evidence and limits
  are in `audit-outage-recovery-v1.md` and its tracked summary JSON.
- Final receipt hardening adds six actual HTTP tests:200/201 must contain the
  matching event ID;202/redirect/wrong-ID/401 cannot mark delivery. Full reactor
  now87 total/82passed/five skipped. Final live run1889a28b9c9e4a44823036bb9d304f0a
  repeats all21 normal checks and actual outage/restart/idempotency checks with
  the tightened protocol. Prior passing092e... checkpoint remains preserved.

## 2026-10-20 — Targeted context audit and fixed syscall-error ablation

- Audited only four known development worker traces around CVE-2022-0492,
  8,714,386 prefix events. Collection1 has12execve/one mount entry during the
  annotated interval; collection2 has none on either worker. Target pod remains
  observed. A separatev2 checks the unlabelled10s onset gap, also without these
  calls. No exploit-success conclusion or relabeling follows from absence.
- Other containers have cgroup text mentions in pre-control context, so generic
  substring presence is not treated as an attack signature. Raw arguments are
  not saved; no independent scenario is decoded or scored.
- Protocol/code1465988 and runtime freeze9d18e1f precede scoring. Add50 generic
  leading syscall-return error features to29base inputs; all557 original rows,
  labels, order and base values match. Fixed recipes/.5 threshold/eight CVE
  folds reproduce every prior baseline. No parameter search is launched.
- Logistic alarms3to2 but exposure hits40to39; macro-F1 .918669to.917064.
  RF/XGB unchanged. All gates fail; select none, retain negative results, do not
  promote or alter enforcement. Promoted UNSW checksum remains unchanged.
- Read-only collision audit:three cross-label vector groups/22rows/three positive
  rows with identical inputs in both representations. No deletion/majority labels.
- Full Python120passed. Results, limitations, hashes and reproducible code are
  recorded in `socialnetwork-errors-results-v1.md` and its tracked evidence JSON.

## 2026-10-20 — Bounded gateway burst acceptance

- Froze protocol/verifier in a0927ad before running twelve loopback logins from
  one bound peer with rotating forwarded-IP headers. Four verifier tests passed.
- Existing 21 API/MySQL checks passed. Burst took 0.169 seconds: ten 401 then
  two 429; positive Retry-After, no-store and correlation were preserved.
- Exactly ten failed-login events appeared in both producer outbox and Monitoring.
  The two rate-limited calls did not reach Auth. Test records were retained.
- Runner stopped owned services; zero project test listeners remained. No model
  change or ML/DDoS accuracy claim. Sustained/distributed load, token recovery
  and durable rejection-event auditing remain separate acceptance work.
- See gateway-burst-results-v1.md for artifact path, fingerprint and limitations.

## 2026-10-20 — Fix cross-user record visibility

- Found global latest-record queries available to every authenticated user.
  Applied signed-identity repository scope for ordinary users; exact ROLE_ADMIN
  retains global access. No public role-promotion route was added.
- Actual HTTP/H2 tests reject header/query attempts to widen access, isolate
  unattributed events and verify signed operator access. Affected Maven reactor
  passed39 tests; frontend18 tests/build and live-verifier four tests passed.
- Actual MySQL run passed29 API checks, including attempted registration role
  escalation and two-user scopes. Gateway burst acceptance passed again.
- Dashboard labels personal/global role scope and latest100 record limits.
  Artifacts and limits: record-visibility-results-v1.md. No model change.

## 2026-10-20 — Shared HTTP input boundaries

- Added shared http-security module for Gateway/Auth/Business/Monitoring/Policy;
  bounded correlation IDs, body size including chunked body-bearing requests,
  rejected unsupported encodings, and preserved accepted bytes downstream.
- Capped login identity length and checked BCrypt passwords by UTF-8 byte length;
  sanitized malformed/invalid Auth responses without exposing rejected values.
- Full Java reactor100 total:95 passed/five skipped/no failures. Eleven new
  unit/HTTP boundary tests are included. Local Maven installation succeeded.
- Actual MySQL run38 checks plus bot and outage/restart recovery passed. Four
  live-verifier unit tests passed. Owned processes stopped. No model changed.
- Results and limitations: http-boundary-results-v1.md; design/STS module import:
  ADR0005. This does not establish comprehensive schema or network protection.

## 2026-10-20 — Controlled durable-audit recovery operations

- Added administrator-only producer summaries and DEAD-event dry-run/replay.
  Applied replay logs signed actor, reason, prior attempts/error and operation
  UUID atomically with the state change. Payload/UUID/time remain unchanged.
- Initial HTTP test exposed primitive apply-field parsing; nullable/default
  preview and authorization-before-parsing corrected it. Failure logs retained.
- Added oldest pending event-age metric; actual Prometheus exports verified.
  This is not queue residence time or proof of delivered alerts.
- Root Java107 total/102 passed/five skipped. Live44 API checks plus bounded
  burst and outage/restart/controlled replay passed; four verifier tests passed.
- Only a newly generated synthetic outage event was marked DEAD for MySQL replay;
  natural retry exhaustion is not claimed. Original UUID delivered after restore.
- Owned services stopped. No model/frontend change or deletion. Results and
  limitations: outbox-operations-results-v1.md; operator procedure: ADR0006.

## 2026-10-20 — Audit alert rules and actual rule-engine probe

- Added four production rules: retained DEAD events, old positive pending queues,
  unavailable producer scrape, and missing/invalid required metrics. Both scrape
  configs load the shared file; Compose mounts it. No external receiver chosen.
- Checksummed official pinned tools; both configs and10 scenarios/22 assertions
  passed promtool. Corrected unsupported NaN shorthand before protocol commit.
- Frozen f0fe6a7 before real loopback engine execution. Synthetic exporter drove
  inactive→pending→firing→inactive with unchanged hold rule. Runtime67.95s,
  owned process stopped and both probe ports clear. This is not attack detection.
- Added repeatable validation script and CI job; remote CI/Docker deployment and
  external notification delivery are not claimed. No model or frontend changed.
- Evidence/limitations: audit-alert-results-v1.md. Operator explanation/runbook:
  docs/monitoring-operations.md. Asked user to select the final alert destination.

## 2026-10-20 — Dashboard + email choice and real alert receipt UI

- User selected dashboard + email; sender/provider/recipient pending. Added real
  read-only admin dashboard sources, honest unknown/stale states and cancellation.
- Added bounded administrator-only Prometheus reader and exact Gateway GET route;
  no internal ingestion exposure. Frontend26 tests/build passed; full Java109
  total/104 passed/five skipped, then Gateway30/28 passed/two skipped after routing fix.
- Initial live startup exposed a readiness race; included real-model AI health
  in the existing deadline. Another run exposed the missing nested GET route.
  Both failures retained; routing-test list-binding correction retained too.
- Final44 API/MySQL checks and burst passed. Real engine/API trace through
  Gateway preserved inactive/pending/firing/recovery. No mocked production data.
- Actual ordinary-user browser sign-in, admin-access denial and logout checked;
  narrow DOM did not overflow. Screenshot capture failed; pixel/admin-browser
  review not claimed. Owned services/probe/preview stopped; MySQL untouched.
- Results/limits: dashboard-alert-results-v1.md. No ML change or email delivery.

##2026-10-20 Optional email transport

- User selected dashboard + email. Added private SMTP configuration validation,
  separate password-file rendering, required TLS, restricted runtime output and
  an optional unverified Compose deployment candidate. No account details read.
- Froze protocol in73dfb01 and rule-chain extension inb586df7 before live runs.
- Real Alertmanager→fixed loopback SMTP firing/retry/duplicate/recovery passed
  in10.09s. Actual production-rule Prometheus→Alertmanager→loopback SMTP passed
  in77.05s with unchanged one-minute hold. Ten verifier/config tests passed.
- No real mail, provider TLS/authentication or deployment permission claim;
  all owned test listeners stopped. Results/hashes:email-alert-results-v1.md.
  Existing promoted model and negative experiments unchanged.

##2026-10-20 Dashboard keyboard acceptance checkpoint

- Fixed scroll-only navigation by moving keyboard focus to labelled destinations;
  added skip link, username/required validation focus, table/list relationships,
  filter announcements and safe invalid-event timestamps. Implementation6f86755.
- All31 frontend tests and production build passed, including five new
  keyboard/semantic tests. Actual browser sign-in focus/tab order/empty-form
  validation checked. No credentials entered or backend services started.
- Screenshot capture unavailable; no administrator visual or full WCAG pass
  claimed. Mobile header semantics preserved in CSS, actual mobile assistive
  technology review remains. Owned preview/tab stopped. See
  dashboard-keyboard-results-v1.md. Sites local-only workflow; no publication.

## 2026-10-20 Session and denied-source cache boundaries

- Main event/execution refresh previously retained403 data as if it were an
  ordinary outage and waited for both requests before401 handling. Added prompt
  denied-source clearing including export/receipt state,immediate401 logout,
  cancellation and guards against late old-session callbacks. Login now checks
  response token structure and ignores completion after unmount.
- All43 frontend tests/build passed,including12 new bounded fixture cases.
  Existing outage-staleness behavior retained. No backend,model,MySQL or real
  browser revocation run; server-side JWT/role revocation remains separate.
- ADR0008 records behavior,verification and limits. Sites local-only workflow;
  no publication or live processes needed. Existing README/PRD edits preserved.

## 2026-10-20 Isolated MySQL recovery rehearsal

- Read only four live audit table structures; created fresh source/restore
  fixture schemas with six synthetic records. Native mysqldump/restore used;
  real users and application databases untouched. Protocol3396908.
- Initial restore had matching rows/DDL but the Windows CRLF queue-state
  assertion failed. Retained the failure; corrected text handling in ac29072.
  A fresh v2 pair passed all nine checks in1.57s, including corruption rejection,
  restored stable-event uniqueness and data equivalence after duplicate failure.
- Four guard tests/all14 live-verifier unit tests pass. Four tiny fixture schemas
  and ignored SQL/evidence retained; no server started or existing data deleted.
  Full application/encrypted/off-host/point-in-time recovery remains open.
- See database-recovery-results-v1.md and database-recovery.md for hashes,
  exact scope, reproducibility and operational limitations.

## 2026-10-20 Matched complete-envelope performance

- Froze protocol/source09c59e1 before executing actual factory/provider fresh
  keygen,seal,open,equality/wipe work for equal4KiB payloads in all three modes.
  Five forks each,five warm-up/ten measurement iterations each; GC profiler and
  bounded512MiB heap. No AI/policy/HTTP/database time included.
- Run passed in236.78s. Means CLASSICAL8.057ms,HYBRID6.685ms,PQC5.309ms;
  raw component totals4238–4240/8553/8521bytes. Classical fork variation retained.
  No generic PQC speed/security or adaptive-system superiority claim supported.
- Host power/thermal/background load not isolated; fixed parameter order and
  no wire/request-tail measurements. Kept raw JSON/logs,JAR/input hashes and
  machine-readable summary. All17 verifier/config tests and new Java benchmark
  round-trip/unknown-mode tests pass. Full root Java regression:112 total,
  107 passed,five skipped,zero failures/errors across47 fresh suite reports.
  Initial optional timestamp aggregation failed freshness validation; retained
  and superseded by fail-fast java-regression-fresh.json,not a test failure.
- See matched-envelope-results-v1.md and protocol for exact evidence and limits.

## 2026-10-20 Recovered live adaptive matrix and independent audit check

- Matrix/protocol8307423 was frozen before actual stack execution. Earlier
  attempt597d6a had no completed receipt. Later dc8caad0 receipts recovered after
  tool interruption show44 base checks and32 frozen scenarios passed; no extra
  rerun after recovery. All owned services were absent/ports free when checked.
- Actual model/Policy/Business/MySQL produced24 verified envelopes and eight422
  fail-closed outcomes. Independent read-only MySQL joins confirmed32 execution,
  decision and event identities,versions,payload fingerprints and outcomes.
- Observed2/24 successful crypto executions above configured selection value:
  both0ms cases executed in3/4ms. Field is a heuristic selector,not a hard SLA.
  All flows used one MEDIUM-score demonstration input; no ML accuracy claim.
- All21 verifier/config tests pass. Kept receipts,logs and synthetic audit rows;
  no credentials/full envelopes exported or existing data deleted. Results and
  hashes:adaptive-matrix-results-v1.md. Wider acceptance remains open.

## 2026-10-20 Bounded AI/policy dependency failures

- Added explicit2s connect/5s read-inactivity waits to both critical HTTP clients.
  Actual accepted-but-silent socket tests pass near5s. Initial assertion expected
  a narrower Spring wrapper; preserved its failure XML and now require the real
  SocketTimeoutException root cause. Frozen live source/protocol6b7495a.
- Full root package:114 total/109 passed/five skipped,zero failures/errors,
  49 fresh suites. All21 live-verifier/config tests pass.
- Actual44-check live suite plus AI-down/restart and Policy-down/restart passed.
  Both outages returned502 with failed audits/no executed crypto; both recoveries
  produced verified PQC. Direct post-run counts matched2 failed/2 successful
  executions,2 policy decisions and4 matching monitoring outcomes.
- Owned process trees now stop with an explicit cleanup receipt; verified no
  project listeners/processes remain. MySQL/unrelated apps left alone,synthetic
  audit rows retained. No model/accuracy change or whole-request SLA claim.
- See dependency-failure-results-v1.md for measurements,hashes and remaining gaps.

## 2026-10-23 Full-length manuscript and reviewed export

- Revised existing open `paper/main.tex` in place; no replacement project/tab
  and no alternate PDF compilation. Added research questions/gap,all11 retained
  sources,explicit contracts/threat model,all later syscall ablations,paired
  HTTP results,matched-envelope findings,uncertainty and reproducibility.
- Checked six remaining PDFs against library hashes; corrected unchanged P05
  copy's year to final March2022 SP800-204C. Scoped review recorded separately;
  no systematic novelty search or independent literature reproduction claimed.
- Final source compiles. Source preflight verifies168-word abstract,16 refs,
  all11 retained citations,12 tables,4 figures,resolved labels and arithmetic.
- User-exported document(4).pdf has13 A4 pages; every page rendered/inspected.
  Fixed crossing architecture arrow,figure width,Unicode Times font selection,
  reference spacing and repetitive summaries that caused a near-empty page.
  Reviewed PDF copied into `paper/output/AI-PQC-research-paper-reviewed-v2.pdf`.
- Source/PDF hashes,reviewed-page record and remaining submission requirements
  are in `paper/pdf-review-2026-10-23.md`. No model retraining/test reopening,
  promotion,enforcement or server change. Promoted checksum unchanged.
- Author/guide finalization,venue adaptation,legacy template comparison and
  actual institutional similarity report remain. No acceptance/score guarantee.
