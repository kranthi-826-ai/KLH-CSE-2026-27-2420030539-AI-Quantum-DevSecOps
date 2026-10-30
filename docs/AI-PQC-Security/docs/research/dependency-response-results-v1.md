# Dependency response validation results

Date: 2026-10-20. Frozen implementation and contract: `d17924f`.
See `dependency-response-contract-v1.md` for requirements and limits.

## Completed checks

- Full root `mvn -q package` exited zero: 150 tests across 50 suites,
  145 passed, five skipped, zero failures/errors. The skipped tests are not
  claimed as passing. Per-suite XML hashes/timestamps are retained in the run.
- 26 AI HTTP-fixture invocations passed: seven omitted fields, four invalid
  scores, five contradictory/invalid metadata cases, four malformed/empty
  response shapes and six valid score boundaries.
- Business service suite passed 16 invocations, including eight new invalid
  decisions and two actual HTTP omitted/null-score cases. Invalid decisions
  leave failed, unverified audits with no selected decision/mode or crypto work.
- All 21 live-verifier/configuration unit tests passed.
- Rebuilt actual services passed the 44-check baseline and existing frozen
  32-case adaptive matrix using the unchanged real RF model and native MySQL.
  There were 24 verified envelopes and eight HIGH/CLASSICAL fallback denials.
- An independent read-only MySQL postcheck joined all 32 execution IDs,
  decisions and monitoring events: 24 verified, eight denied, all 32 consistent
  in correlation, outcome, versions and payload fingerprint.
- The runner stopped its seven owned process trees; a subsequent OS listener
  check found no listeners on project ports. MySQL and unrelated apps were not
  stopped. Synthetic test users and audit records remain as test evidence.

## Retained evidence

Directory: `ml/artifacts/live-stack-ba7c6693b9054773b26afd8805bc4bef/`.

| Receipt | SHA-256 |
|---|---|
| verification.json | 6ede57da83d4b028156ab4b623791893b840f5095a33fc6206e4685f3d9ea572 |
| adaptive-matrix.json | 64bea2e5ad9ddb438bc48a1ff8499684d94610107f71769cc31d85fb76d5b043 |
| java-regression.json | 071baa6df460dc6204a71411f154de5ce9d703848d8cafd93f299e2303bde445 |

The directory also contains `adaptive-audits-recheck.json`, process/cleanup
receipts and local service logs. It is ignored runtime evidence, not a public
dataset. No credentials or full crypto envelopes were saved in the receipts.

## Claim limits

Negative-response fixtures prove rejection of the enumerated contract defects,
not behavior against every malformed response or a compromised authenticated
dependency. Healthy live verification uses one MEDIUM model-input flow with
sensitivity/capability variations; it is not LOW/HIGH input-model coverage,
load acceptance, public deployment, or an ML accuracy improvement. Client-supplied
features remain demonstration inputs. No new model was trained or promoted.
