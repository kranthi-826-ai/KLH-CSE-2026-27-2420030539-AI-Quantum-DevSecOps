# Real routed HTTP study: frozen evaluation and deployment rejection

Date: 2026-10-19. This completes the current routed dataset experiment, not
production AI certification. All candidates remain unpromoted; automatic AI
responses are disabled. No final-test tuning or repeated final evaluation occurred.

## Why this experiment was necessary

The earlier isolated-account HTTP model scored 97.94% on its own small test.
Gateway shadow work then exposed a different identity boundary: gateway history
is shared by a transport peer, while the earlier generator reset history per
account. This experiment tests that mismatch with **real Gateway-to-Auth-Service
routing**, not downstream handler fixtures.

## Data collection and labels

Two actual Spring applications ran on ephemeral loopback ports. Auth used a
dedicated H2 database; only outbound monitoring publication was stubbed. The
Gateway used a real HTTP route to it. Seven distinct bound loopback source
addresses produced seven actual connection peers, not spoofed identity headers.
This is a controlled single-host lab, not seven independent physical networks.

The collector made 1,056 HTTP requests in 62.17 seconds: 120 setup registrations/
logins and 936 labelled study requests across 60 fresh accounts/sessions.
Scenarios were normal use, normal mistakes, legitimate bursts, credential
guessing, invalid-token bursts and missing-token bursts. Labels come from
harness intent, not response outcomes. Normal mistakes remain benign-intent
even when authentication correctly rejects an individual wrong credential.

The lab gateway limits were raised to 5,000 tokens to isolate detection from
blocking during collection. A separate real routed controls test verifies
limiting with a deliberately smaller bucket; collection results must not be
misrepresented as a default-limit stress test or a DDoS benchmark.

For the isolated labelled lab only, the gateway returns a server-generated
observation UUID. Preparation joins that UUID to the gateway's pre-request
snapshot. It replaces provisional client features rather than mixing schemas.
IDs are never trusted as history identity. The optional response header is off
by default; no request-body values, token values or raw source IPs are stored
in the model records. The gateway log contains 996 observations: 936 study
requests plus 60 setup logins. Setup observations are not labelled as attacks.

Preparation verified unique IDs, client/server outcome agreement, exact feature
keys and source hashes. It refuses missing/reused joins, identity changes within
a session, overlapping transport peers, and output overwrites.

## Peer holdout and model selection

| Partition | Sessions | Rows | Distinct transport peers |
|---|---:|---:|---:|
| Train | 36 | 557 | 3 |
| Calibration | 12 | 185 | 2 |
| Final test | 12 | 194 | 2 |

Peers, not just accounts, are disjoint across partitions. Requests within each
peer retain real causal history across successive accounts. Only nine
pre-request route/header/history features are used; current status, latency,
scenario, target, session/peer IDs and partition are not predictors.

The plan was saved before fitting. Standardized logistic regression and the
predefined Random Forest were compared with leave-one-transport-peer-out CV
on the three training peers. Mean CV macro-F1 selected logistic regression.
Calibration selected a threshold of approximately 0.925, attempting to keep
FPR <=5%. Calibration recall was only 32.58%, so it was explicitly ineligible.
Model, code, dependencies and data were then frozen for **one diagnostic final
evaluation**, never for deployment approval.

## Frozen final results, same 194 held-out requests

| Detector | Accuracy | Macro-F1 | Suspicious-intent recall | FPR |
|---|---:|---:|---:|---:|
| Earlier per-account RF, unchanged | 58.25% | 50.91% | 96.91% | 80.41% |
| Predeclared peer-history rule | 57.22% | 50.16% | 94.85% | 80.41% |
| Peer-trained logistic, calibrated for low FPR | 64.43% | 59.94% | 30.93% | 2.06% |

The calibrated candidate's confusion matrix is `[[95,2],[67,30]]`. It missed
67 of 97 suspicious-intent requests. At this threshold it detected none of the
credential-guessing or invalid-token scenarios and 81.08% of missing-token
requests. It failed the recall >=95% / FPR <=5% gates and was rejected.

These are different findings from 97.94% on the isolated-account benchmark.
Do not present that older score as gateway accuracy. The unchanged RF's high
recall here is accompanied by an unacceptable 80.41% benign alert rate.
Two-peer bootstrap intervals are retained in the evidence for transparency,
but cannot establish reliable real-world population uncertainty.

## Bounded follow-up, without touching the final test

A new development-only plan compared logistic, RF and two bounded XGBoost
recipes. Selection used mean standardized partial ROC-AUC at FPR <=5% on
training-peer CV, rather than default-threshold macro-F1. Only training and the
previously exposed **development calibration** partition were loaded.
The follow-up was initiated after reviewing the original failed evaluation;
it is post-test method development, not an independently confirmed improvement.

Mean partial-AUC scores: logistic 0.63740; RF 0.72819; XGB depth 3 0.69160;
XGB depth 5 0.65812. Selected RF calibration recall was 37.08% at 4.17% FPR.
This also failed. No fresh holdout was consumed and no new final-test score was
reported. The old final test was not reused to select a recipe or threshold.

## Independent controls remain effective for these bounded probes

An audit of the collected outcomes found:

- 471 suspicious-intent study requests: all returned HTTP 401.
- 465 benign-intent study requests: 435 HTTP 200 and 30 expected HTTP 401 user
  mistakes. These rejections do not make the whole session malicious.

This verifies authentication outcomes for the specified invalid-credential
scenarios, **not 100% AI accuracy or universal attack prevention**.

A separate real Gateway-to-Auth/H2 test issued 19 requests. Twelve simultaneous
authenticated identity reads all returned HTTP 200 and the correct principal.
Missing and malformed tokens returned 401. Two wrong-password attempts returned
401; a subsequent attempt hit HTTP 429 with Retry-After despite changed
X-Forwarded-For values. Its test auth bucket had capacity 4, not the normal
default of 10. AI responses were disabled. No handler fixtures were used.

## Interpretation and release decision

The evidence demonstrates an identity/granularity and feature-information
problem, not that larger models automatically solve detection. A boolean
bearer-header indicator cannot itself prove token authenticity. Shared-peer
failure history can spill across legitimate users, and low-FPR calibration
can suppress useful recall. These are plausible explanations consistent with
the measured failure; this single small experiment is not a causal proof.

Do not enable automatic AI denial, publish a 99% claim, combine these scores
with CICIoT/UNSW, or tune against the exposed final test. Preserve independent
authentication, rate controls and policy downgrade protections. A new version
would need better justified identity/features and independently collected
holdouts before release. This is an explicit deployment rejection, not a claim
that the whole project is finished or that production security is certified.

## Reproduction, evidence and limitations

- `scripts/run-routed-study.ps1` orchestrates fresh uniquely named collection,
  real routed concurrency/control checks, preparation, training/freeze and final
  evaluation. Its component commands were executed for this report; the new
  consolidated wrapper was syntax-checked, not used to replace the recorded run.
- `scripts/run-routed-gateway-child.ps1` launches only the explicitly selected
  opt-in gateway lab test while its parent holds the real Auth Service open.
- `ml/data/prepare_routed_sessions.py`, `ml/training/study_routed_sessions.py`,
  and `ml/training/refine_routed_operating_point.py` preserve separate data,
  selection, calibration and evaluation responsibilities.
- Tracked packet: `docs/research/evidence/routed-http-study-v1.json` contains
  manifest, frozen model selection, final negative result, development-only
  refinement and real-service controls. Raw data/model binaries stay ignored.
- Initial routed startup failed due to a list-property priority mismatch. All
  route fields were moved to the same dynamic source; failed artifacts were
  preserved and successful collection used a fresh directory.
- Python: 59 tests passed. Full Java reactor: 57 passed, five opt-in lab tests
  skipped by default; routed collection and real control tests passed explicitly.
- Only one machine, generator and collection run; sequential training traffic,
  seven local peers and two final peers. The separate concurrency check is not
  a load benchmark. No successful exploitation, external-client distribution,
  live MySQL, PCAP collection or PQC execution was measured in this dataset.

The final budget checkpoint reported 25% weekly usage (75% remaining), versus
23% used initially. This account-wide, coarse reading stays above the user's
70%-remaining reserve; it is not an exact attribution of cost to this run.
