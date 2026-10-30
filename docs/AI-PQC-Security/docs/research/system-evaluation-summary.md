# System Evaluation Summary

This document is the evidence index for the research demonstration. It links
each project claim to a repeatable test or measured result and prevents the
paper from treating implemented features as experimentally proven outcomes.

The [research journal](research-journal.md) records ongoing decisions,
experiments, limitations and the evidence needed to prepare the paper.

## Evaluated evidence

| Research question | Current evidence | Result | Remaining publication work |
|---|---|---|---|
| Can the system detect risky network flows? | Official UNSW-NB15 predefined split | Random Forest test macro F1 89.46%, attack recall 97.65%, ROC-AUC 98.43%, FPR 19.85% | Reduce false positives and compare candidates under the identical split |
| Can risk drive an auditable protection decision? | Policy unit/integration tests and MySQL decision records | Deterministic classical, hybrid, and PQC selection with model/policy versions and fallback reasons | Add scenario-distribution and decision-latency statistics |
| Can the selected profiles execute real standardized PQC? | Java correctness/tamper tests and JMH | ML-KEM-768, ML-DSA-65, hybrid X-Wing, X25519, and AES-GCM execute successfully | Repeat longer controlled benchmark runs and report artifact sizes |
| Does the distributed flow work end to end? | Isolated Docker Compose plus Bruno collection | 7/7 API scenarios passed; registration, login, JWT, risk, policy, crypto, audit, and denial paths verified | Repeat runs and export machine-readable test evidence for the paper |
| Is operational evidence observable? | Prometheus target checks, Grafana provisioning, MySQL audit queries | All seven configured Prometheus targets reported UP in the verified Compose run | Collect a timed demonstration trace and dashboard screenshots |
| Is deployment reproducible? | Maven/pytest/frontend CI, Compose, and rendered Kubernetes resources | Fourteen-module Maven reactor, Python tests, React tests/build, container E2E, and 27 Kubernetes resources validated | Run Kubernetes E2E when local cluster resources are available |

## Measured baselines

Latest resilience checkpoint (2026-10-20): explicit dependency connection/read
waits and real silent-peer timeout tests pass. Isolated AI/Policy process outages
returned502 with no crypto success; real restarts restored verified PQC and
matching MySQL/Monitoring records. Full root114 total/109 passed/five skipped;
44 ordinary live checks also passed. No whole-request/availability SLA follows.
See [dependency failure results](dependency-failure-results-v1.md).

Latest live adaptive checkpoint (2026-10-20):44 ordinary live checks plus32
frozen sensitivity/compatibility/threshold scenarios passed,with24 verified
envelopes,eight required422 denials and independently joined MySQL decision/
execution/event audits. Two zero-threshold requests executed in3/4ms,so selection
thresholds are not runtime SLAs. This is not model accuracy or a static-versus-
adaptive performance comparison. See [live scenario evidence](adaptive-matrix-results-v1.md).

Latest crypto checkpoint (2026-10-20): the matched complete-envelope run now
reports fresh-key seal/open work across all three actual profiles with five
forks and50 measurement iterations per mode. Means were8.057ms CLASSICAL,
6.685ms HYBRID and5.309ms PQC, with allocation, fork variation and raw component
sizes retained. These are not full API/adaptive speedups or a security ranking.
See [matched-envelope results and limits](matched-envelope-results-v1.md).
The older primitive-only numbers below remain historical, not directly
comparable complete-envelope workloads.

### Intrusion model

| Metric | Current held-out result |
|---|---:|
| Accuracy | 89.79% |
| Macro F1 | 89.46% |
| Attack recall | 97.65% |
| False-positive rate | 19.85% |
| ROC-AUC | 98.43% |

The complete dataset hashes, split rules, confusion matrices, and environment
are in [Phase 3 baseline results](phase-3-baseline-results.md).

A calibrated XGBoost candidate passed three repeated validation splits but did
not beat the Random Forest on the frozen official-test evaluation: 89.17%
accuracy, 88.79% macro F1, 97.68% attack recall and 21.25% FPR. It was rejected;
see [Phase 3 XGBoost calibration results](phase-3-xgboost-calibration-results.md).

### Cryptographic execution

| Operation | Local average time |
|---|---:|
| AES-256-GCM encrypt, 4 KiB | 3.043 us |
| ML-KEM-768 encapsulation | 34.539 us |
| Hybrid X-Wing encapsulation | 105.702 us |
| X25519 encapsulation | 210.821 us |
| ML-DSA-65 sign, 4 KiB | 692.220 us |

The protocol and interpretation limits are in the
[Phase 5 benchmark report](phase-5-crypto-benchmark-results.md).

## Demonstration sequence

1. Start the complete stack and confirm service discovery and health.
2. Register and log in through the gateway to obtain a JWT.
3. Prove that an unauthenticated protected request is denied.
4. Submit a network flow and confidential payload to the adaptive endpoint.
5. Show AI risk, policy explanation, selected cryptographic mode, verification,
   and component latency in the response.
6. Show the matching decision, execution, and security-event records in MySQL.
7. Show the same correlation ID and outcome in the dashboard and monitoring
   views.
8. Run the Bruno collection and retain its machine-readable result artifact.

## Claim boundaries

- The project is a research prototype, not a certified production security product.
- Model results are comparable only under the documented dataset and split.
- Local cryptographic timings are hardware- and protocol-dependent.
- Passing functional and vulnerability checks does not prove absence of defects.
- The project integrates standardized primitives; it does not invent a new cipher.
- Accuracy improvement will be claimed only after a validation-selected, frozen
  candidate beats the recorded baseline under the documented official test
  protocol and passes every promotion gate. Prior baseline test metrics are
  already known; disclose test-set reuse and keep it out of tuning decisions.
