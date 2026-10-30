# Live adaptive scenario and audit results

Date: 2026-10-20. Frozen matrix/protocol commit: `8307423`.
The completed receipt was recovered after an interrupted tool response. Its
actual saved evidence, not the earlier incomplete status message, establishes
the result below. No extra rerun was needed after recovering it.

## Outcome

All16 frozen scenarios, repeated twice, passed in7.76 seconds after readiness
and the ordinary44-check live suite. The ordinary suite also passed separately.

- 24 successful verified envelopes:6 CLASSICAL,12 HYBRID,6 PQC.
- Eight HTTP422 fail-closed requests: HIGH effective risk with only a CLASSICAL
  fallback available. No successful execution or encrypted payload returned.
-32 distinct execution audits,32 matching policy decisions and32 corresponding
  Monitoring events. Event outcomes were24 SUCCESS and8 FAILURE.
- A separate **read-only post-run MySQL join** matched the receipt's execution,
  decision and correlation IDs; model/policy versions; payload SHA256 values;
  effective risk/modes; and execution/event outcomes for every case.

The test used actual loopback Gateway/Auth/AI/Policy/Business/Monitoring/Eureka
services, the unchanged promoted model and actual MySQL. No mock inference,
limiter disablement or real attack traffic was used. Credentials and full
envelopes were not included in the evidence receipts.

## Scenario coverage

All requests use the same4096-byte synthetic payload and Bruno network-flow
features. The model score remained0.5690423129295029 (MEDIUM input risk).
Sensitivity changes effective policy risk, not the model's prediction.

| Case family | Selection threshold | Observed contract |
|---|---|---|
| MEDIUM PUBLIC/INTERNAL with hybrid support |8 or100ms|HYBRID executes |
| MEDIUM below hybrid threshold or with no hybrid support |0,7 or100ms|CLASSICAL executes |
| CONFIDENTIAL elevates MEDIUM; RESTRICTED forces HIGH |15 or100ms with PQC support|PQC executes |
| HIGH with hybrid fallback |8,14 or100ms|HYBRID executes |
| HIGH below all available thresholds or incompatible |7,14 or100ms|CLASSICAL selection is recorded but Business refuses execution with422 |

The exact16 cases and expected results remain in the frozen Python manifest;
this table groups cases and is not an exhaustive policy truth table. LOW/HIGH
input-risk model flows and the full feature space were not evaluated here.

## Latency limitation actually observed

Client wall times ranged92.741–160.526ms across the32 sequential calls. This
small functional run followed other startup/verification requests; it is not
a cold-start, load, request-p95 or static-versus-adaptive performance benchmark.
Recorded server crypto times are integer milliseconds and have a different
measurement boundary from the client wall clock and JMH study.

Both `medium_zero_threshold` repetitions executed successfully while measured
crypto time was3ms and4ms despite a configured threshold of0ms. Thus **2/24**
successful executions exceeded their configured selection value. This confirms
the current `maxCryptoLatencyMillis` field is a heuristic selection input, not
a hard runtime deadline/SLA. No latency guarantee should be claimed. Failed
execution rows' default component-time values are not measurements of failed
policy-call duration.

## Recovered and interrupted attempts

- `live-stack-597d6a4864614daa8356b7cbf4ece1ad` has startup logs but no completed
  matrix/base receipt. Its tool handle and recorded processes were missing and
  project ports free when checked. Retained as unverified/interrupted, not passed.
- `live-stack-dc8caad0dd144e859740243a2d68b45f` contains both passing receipts.
  The interrupted tool call did not imply the underlying run failed. Later
  inspection recovered the completed results; no duplicate run was started.
  All recorded service processes were absent and all seven project ports had
  no listeners during the recovery check. MySQL and unrelated apps were untouched.

## Evidence identifiers

Under ignored `ml/artifacts/live-stack-dc8caad0dd144e859740243a2d68b45f/`:

- `verification.json` SHA256:
  `0dd2cfb93f06c7a8ed2d79cd7814eeaec12e9c00fa6c0c89d40ee70339e46e86`.
- `adaptive-matrix.json` SHA256:
  `e79fdf59993589e66cd866d7803ccb1061d07de6ce3c541acfdb1dad4ea291b4`.
- `adaptive-audits-recheck.json` SHA256:
  `b931650e3c8bcbfccfdee14bbac75a59390db71cb1277310816fe8da854dba70`.
- Frozen case manifest SHA256:
  `a620cb3948d97d6eca10841f926bb92d1783576c793aa9ea9500762e5fc97d82`.
- Flow feature fixture SHA256:
  `db9faa348894620d38adc0174ca1abd9629a545000eb6eceb07ace001abcc398`.
- Promoted model SHA256:
  `c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.

All21 live-verifier/config unit tests passed, including two manifest and two
post-check receipt tests. Java/frontend production source was unchanged, so
their full suites were not rerun in this checkpoint. Synthetic users and audit
records remain for traceability; no deletion was performed.

Reproduce with [the frozen protocol](adaptive-matrix-protocol-v1.md). After
services stop, run `tests/live/recheck_adaptive_audits.py` on the unique completed
artifact directory for an independent read-only database check. It rejects
incomplete, duplicate, mismatched and unsafe identity receipts and refuses to
overwrite an existing post-check result.

## Claim boundaries

This establishes the measured deterministic scenario contract and durable
record traceability, not improved model accuracy, real bot/attack detection,
server-trusted sensitivity/telemetry, full policy coverage, universal security,
hard latency bounds, production transport security or paper novelty. Full
adaptive-versus-static API comparison, broader failure/load/browser/deployment
acceptance and the other project requirements remain open.
