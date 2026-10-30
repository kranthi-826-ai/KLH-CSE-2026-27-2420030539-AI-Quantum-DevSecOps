# Microservice-specific HTTP detector: controlled session study v1

Date: 2026-10-19. Status: lab candidate evaluated once; not promoted or connected
to automatic responses. This is a separate model and dataset from CICIoT2023
and UNSW-NB15; their deployed models and reserved datasets were not changed.

## What was actually collected

The real Auth Service ran on an ephemeral loopback port with an explicitly
isolated H2 database. Its controller, password hashing, JWT checks and HTTP
responses were real. Only outbound monitoring publication was stubbed. The
collector made **1,056 actual HTTP requests** in 59.37 seconds: 120 account
registration/login setup requests and 936 measured study requests across
60 fresh accounts/sessions. No MySQL password, external targets or disabled
security settings were needed. No passwords, usernames, bearer tokens or
response bodies were retained in the dataset.

Six harness scenarios were interleaved in each collection phase:

- Normal use, including valid login and protected identity reads.
- Normal mistakes: occasional wrong passwords and one missing credential,
  all labelled benign intent rather than labelling every HTTP 401 as an attack.
- Legitimate authenticated bursts, also benign intent.
- Repeated wrong-password probes against the harness's own test account.
- Invalid-token bursts and missing-token bursts.

All requests returned the scenario's expected status or the collection would
abort without a complete manifest. These are low-volume controlled probes and
bursts, not successful exploits or a realistic distributed DDoS workload.

## Features and leakage controls

Nine predictors are frozen **before** each request: whether it is login or an
identity read, bearer-header presence (not validity), whether history exists,
previous completed request counts over 1/5 seconds, previous 401 and failed-login
counts over 5 seconds, and elapsed time since the previous request started.
Only strictly earlier completed responses update historical failure counters.

Scenario, target, session/account identity, sequence, partition, the current
response status and the current duration are excluded from model inputs.
Unit tests check that adding a response cannot change an existing feature
snapshot, future responses cannot contribute, history expires, separate
histories do not mix, and outcome fields cannot enter the predictor schema.

These features are calculated in the **client harness**, using the known test
account to keep histories separate. A trusted server-side identity/counter
adapter is still needed for real deployment. Do not use attacker-controlled
session headers as identity, assume this schema equals CIC network-flow inputs,
or populate missing network features with invented values.

## Selection, calibration and one-time test

Collection order reserves later phases, with disjoint accounts/session IDs:

| Partition | Sessions | Measured requests | Purpose |
|---|---:|---:|---|
| Training | 36 | 557 | Three-fold stratified **group** CV and final fitting |
| Calibration | 12 | 185 | Threshold selection only |
| Final test | 12 | 194 | One frozen evaluation on later sessions |

Two predefined candidates were compared: standardized logistic regression and
a 128-tree Random Forest, maximum depth 6, minimum leaf size 3, balanced weights.
Grouped training CV selected Random Forest (mean macro-F1 97.31%, versus
94.25% logistic regression). No account/session crossed a CV or dataset boundary.

The calibration threshold was frozen at approximately **0.55**, with 95.51%
suspicious-intent recall and 2.08% FPR. Model, code, feature module and data
checksums were recorded before opening the final test. The evaluator refuses
overwriting results or repeating an attempted final evaluation. No test-result
tuning or retraining followed this evaluation.

## Measured final results

On 194 held-out requests from 12 later sessions (97 benign-intent and 97
suspicious-intent requests):

| Detector | Accuracy | Macro-F1 | Suspicious-intent recall | Observed FPR |
|---|---:|---:|---:|---:|
| Always normal | 50.00% | 33.33% | 0.00% | 0/97 |
| Predeclared history rule | 88.66% | 88.51% | 77.32% | 0/97 |
| Frozen Random Forest | **97.94%** | **97.94%** | **95.88%** | **0/97** |

The history rule alerts after three previous failed logins or four previous
401 responses in five seconds. The model's confusion matrix is
`[[97, 0], [4, 93]]`: four suspicious-intent requests were missed. Alert rates
were 100% for credential guessing, 92.59% for invalid-token bursts and 94.59%
for missing-token bursts. None of the normal-use, normal-mistake or legitimate
burst test requests caused a model alert.

Five hundred session-cluster bootstrap replicates give conditional 95%
intervals of 96.28–99.49% accuracy and 93.44–98.48% suspicious-intent recall.
The recall interval extends below the 95% point-estimate target. Because no
benign false positives were observed, its empirical bootstrap interval is
degenerate at zero; **this does not prove zero population false alarms**.
Only six benign test sessions were available.

The point-estimate lab gates passed. This is **not production accuracy**, a
cross-dataset result, a new CICIoT accuracy score, or evidence of universal
attack protection. Labels mean harness intent; model accuracy is not the
percentage of attacks prevented. Authentication rejects these invalid requests
independently of model predictions. The automated response/deployment flags
remain false even after passing the lab gates.

## Limitations and the next boundary

All sessions came from one generator, application, host and collection run.
Disjoint accounts and later collection prevent session overlap but do not
prove independent real-world generalization. Setup traffic was not an input
to per-session histories, and scenario patterns can still provide artificial
shortcuts. More varied first-request login patterns, user mistakes, slow probes,
token expiry, retries, multiple clients and independent later-day runs are
needed before deployment decisions. Session resets and identity evasion need
specific evaluation; increasing encryption strength does not stop these probes.

This collection did not route through the Gateway or Business Service, extract
PCAP/system-call features, validate MySQL persistence, measure PQC execution, or
test unknown attack families. Existing real-HTTP gateway regression separately
verifies rate-limit rejection with HTTP 429 and Retry-After. It is not included
in these detector metrics. The immediate next integration boundary is a
trusted gateway-side **shadow-mode** collector, with no new automatic blocking,
followed by independently collected sessions and policy integration tests.

## Reproduction and evidence

- `ml/data/microservice_session_features.py`: causal feature contract.
- `ml/data/collect_microservice_sessions.py`: bounded loopback-only collector.
- `SessionTrafficCollectionTests`: explicit H2 test application; 1 passed,
  measured in 68.06 seconds including application startup and collection.
- `ml/training/train_microservice_sessions.py`: grouped selection and freeze.
- `ml/training/evaluate_microservice_sessions.py`: one-time frozen evaluation.
- `docs/research/evidence/microservice-sessions-v1.json`: tracked manifest,
  complete selection evidence, checksums, scenario metrics and final results.
- Local observations: `ml/data/processed/microservice-sessions-v1/` (ignored).
- Local candidate and frozen metadata: `ml/models/candidates/microservice-sessions-v1/`
  (ignored, not deployed).
- `scripts/run-microservice-study.ps1` reproduces the component sequence into a
  new uniquely named dataset/study without replacing evidence. The wrapper was
  syntax-checked; collection, training and evaluation components were executed
  individually for the recorded v1 run. New run timings and scores may differ.

Verification: 45 Python tests passed in 4.92 seconds. Full Maven reactor passed:
49 tests passed, with the two explicit collection tests skipped by default.
The session collection was enabled and passed separately. No test servers were
left running after the processes exited.

## Completion audit of this data-and-training phase

| Requested item | Authoritative evidence and result |
|---|---|
| Normal logins/access, user mistakes and legitimate bursts | Completed collector manifest and all 936 recorded study outcomes; six controlled scenarios covered |
| Repeated failed-login/token probes and excessive-request controls | Recorded probe sessions; independent gateway real-HTTP regression passed its 429/Retry-After check |
| Record frequency and earlier failures, without secrets | Exact nine-feature schema; strict temporal/history unit tests; stored-field audit found no credential/body fields |
| Fit and evaluate on separate sessions | 36/12/12 split; ID-overlap audit passed; grouped CV checks and one-shot frozen final evaluation |
| Check misses/false alarms before automatic responses | Final confusion matrix [[97,0],[4,93]]; no promotion and automatic-response flags remain false |

The final artifact audit verified tracked/local JSON equality, model and data
hashes, all 60 disjoint session IDs, all expected HTTP outcomes and the exact
secret-free stored schema. It did not repeat model inference or tune on test
data. The existing promoted model binary was independently hashed and still
matches `c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.

This completes the scoped controlled data/training/testing phase, not production
deployment, all-project completion or the independent real-world validation
described in the limitations above.
