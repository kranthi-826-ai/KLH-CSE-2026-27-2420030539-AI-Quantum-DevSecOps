# Difficult examples and local application traffic

Date: 2026-10-19. Two separate experiments; neither changes the deployed model.

## CICIoT2023: difficult-example mining

Run `ciciot2023-difficult-examples-v1` uses the frozen training partition only.
For each seed 42/123/2026, fit/calibration/internal-validation are stratified by
subtype, 70/15/15. Inside fitting, three-fold out-of-fold predictions identify
misclassified examples at threshold 0.5. Each example is scored by a model that
did not fit it. Their existing weights are doubled, without replicating rows.
No outer calibration, outer validation or reserved test is opened.

The base recipe is the prior higher-capacity XGBoost. Nine miner fits and six
paired evaluation fits completed in 79.38 seconds. Thresholds are chosen only
on the calibration partition. The plan, seeds, hashes, parameters and quality
gates were frozen before fitting. We did not add new raw examples in this run.

Mean internal-validation results:

| Recipe | Accuracy | Macro-F1 | Attack recall | Weak-family recall | FPR |
|---|---:|---:|---:|---:|---:|
| Paired reference | 90.035% | 88.072% | 88.294% | 60.926% | 5.022% |
| Difficult-example weighted | 89.830% | 87.848% | 88.037% | 60.059% | 5.077% |

The mining recipe performed worse. It failed recall >=95% and FPR <=5%
requirements and was rejected. No model was saved or deployed. These results
support collecting more representative examples rather than repeatedly
amplifying errors on the same capped sample. Error mining can amplify noisy or
ambiguous labels; this result alone does not establish the cause.

Per-subtype counts and error fractions are in the tracked evidence JSON. They
are calculated only within training and can guide the next collection, but
are not estimates of generalization. Repeated random splits share rows and
are not independent external evaluations.

For example, seed-42 mining flagged 14,531 of 161,169 fitting examples. At
the mining threshold (0.5), the highest relevant subtype error fractions were
Recon-OSScan 39.23%, VulnerabilityScan 28.41%, Recon-PingSweep 26.53%, SQL
injection 22.51%, port scans 21.34% and dictionary brute force 20.92%. Benign
examples had a 17.17% error fraction. These are **OOF mining diagnostics**, not
validation FPR/recall, and prioritize both benign diversity and difficult attacks.

## Actual HTTP measurements, controlled local lab

`LabTrafficCollectionTests` starts the real authentication application on an
ephemeral port with the existing test H2 database. Only the outbound monitoring
publisher is stubbed. The Python collector sends real HTTP requests; the test
server shuts down when the Maven test process exits. No MySQL credentials,
production users, external hosts or security-setting changes are needed.

The first collection measured 22 requests in 3.19 seconds, excluding application
startup. All expected outcomes were observed:

| Controlled scenario | Requests | Observed HTTP status |
|---|---:|---|
| Setup registration | 1 | 201 |
| Correct login | 1 | 200 |
| Authenticated access | 5 | 200 |
| Wrong-password probes | 5 | 401 |
| Missing-token probes | 5 | 401 |
| Invalid-token probes | 5 | 401 |

Labels are **harness intent**, not inferred from HTTP status. A wrong password
can also be a legitimate user mistake. These probes are not successful exploits
or a realistic brute-force workload. This dataset is too small and artificial
for training or claiming model accuracy. Twenty-two expected responses do not
mean 100% AI accuracy or universal security.

Recorded: route, method, scenario, expected/observed status, monotonic offset and
measured duration. Passwords, tokens, response bodies, usernames and personal
identifiers are not retained in the observations. The collector disables proxy
use and redirects, accepts only explicit IPv4 loopback URLs with a port, uses
timeouts and refuses to overwrite existing artifacts.

Reproduce from PowerShell with `./scripts/collect-microservice-lab.ps1`.
It writes a unique JSON under the ignored `ml/artifacts` directory. Use this
isolated-test wrapper, not the collector against an existing user database.

## Boundaries and next data work

- These HTTP observations are **not** CICIoT2023's 39 network features or
  UNSW-NB15 features. Do not map them to those schemas with invented zeros.
- Response status, latency and outcome are post-response evidence. They cannot
  be input to a model deciding the same request before it executes. Historical
  response rates may be valid only with strictly earlier time windows.
- No PCAP extractor, gateway-to-business flow, policy/crypto decision or MySQL
  persistence was evaluated in this collection. Those require separate runs.
- Next collection must include independent sessions/time windows, normal user
  mistakes and legitimate bursts as well as controlled attack intent. Keep all
  windows from a session/capture in one partition. Collect representative
  pre-decision features and hold out later sessions before fitting.
- Additional CICIoT raw rows need a versioned sampling and duplicate-exclusion
  plan before training. Do not simply append held-out source data to training;
  existing capture independence remains unproven. The reserved pilot test is
  still unopened and must not be used to pick the next recipe.

## Evidence and verification

- `ml/training/mine_ciciot2023_difficult.py` and its ignored plan/result artifacts.
- `docs/research/evidence/ciciot2023-difficult-examples-v1.json` (tracked results).
- `docs/research/evidence/microservice-http-lab-v1.json` (tracked observations).
- `ml/data/collect_microservice_lab.py` and opt-in `LabTrafficCollectionTests`.
- Python suite: 33 passed in 5.08 seconds. Opt-in Java collection: 1 passed.
- The ordinary auth-module/reactor test run also passed; collection is skipped
  unless explicitly enabled, so normal tests do not create traffic artifacts.
