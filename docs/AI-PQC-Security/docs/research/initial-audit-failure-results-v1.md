# Initial audit write failure results

Date:2026-10-20. Frozen source/protocol:a139be0.
See initial-audit-failure-protocol-v1.md for the required behavior and limits.

## Reproduction and change

All three new before-tests failed. The initial STARTED save sat outside the
guarded try/catch/finally,so an exception bypassed the existing failed-audit
attempt,failed-flow metrics and byte-array cleanup boundary. The original error
was thrown without policy evaluation,but recovery/telemetry were incomplete.
Retained the three-failure XML/log before changing the code.

Moved the initial save into the existing guard,without moving policy or crypto
ahead of it. No retry loop or weaker security mode was added. The existing
single sanitized failure-audit attempt and cause-preservation behavior now apply
to initial-save failures as well as later operation failures. The finally block
also covers this path;immutable request strings and all memory copies are not
claimed erased or verified by the tests.

## Controlled Spring/H2 cases

The writer is a Spring spy with controlled RuntimeExceptions at its save boundary;
fallback success invokes the real writer/repository/outbox code. These are not
actual MySQL/disk outage or commit-ack ambiguity experiments.

| Case | Verified behavior |
|---|---|
| Initial save throws,fallback recovers | Original exception returned;no policy interaction;one sanitized FAILED/unverified row with no decision/mode/crypto latency and one durable FAILURE event;failed metric increments once;lost-audit counter unchanged |
| Both saves throw distinct exceptions | Original error retained,secondary suppressed;no policy interaction;no persisted row/event;failed metric once and lost-audit counter once |
| Both saves reuse the same exception | Original error retained without self-suppression;no policy interaction;no persisted row/event;same failure/lost-audit counts |

All three cases pass. A storage failure cannot be converted into an encrypted
success. If neither write commits,the process-local metric is not a fabricated
durable audit record or an event that can later be queried from MySQL.

## Regression and cleanup

- Full root Maven package passed179 tests across54 fresh suites:174 passed,
  five skipped,zero failures/errors. Current XML timestamps/hashes were checked.
- Actual local44-check API/MySQL baseline passed on the rebuilt services.
  This verifies normal workflows,not an injected live initial-save MySQL fault.
- Frontend unchanged;prior100-test/build evidence remains applicable. No model
  training,promotion or detection-accuracy measurement occurred.
- Owned test services stopped;cleanup reached the end and OS verification found
  no project listeners. MySQL/unrelated apps and historical rows left unchanged.

## Evidence

Directory:ml/artifacts/live-stack-38bb6b22b7184af8818ea2914d31cf95/.

| Receipt | SHA-256 |
|---|---|
| verification.json |c2fc11e5941d5eda9d9b5509861fe7f6cabb0fd88506c79e64499035265d7129|
| java-regression.json |bdca7f58624cdc6d6dbf4d1f1c84ceff4fd0fb1df9b8b4dd39a4cf6f86fc478b|
| cleanup.json |476b8da71eee6a7ebd3170c35a738bb1cca512a94df31daf1fca1beb7eb437bf|

Other retained artifacts under ml/artifacts:initial-audit-before-v1.log,
initial-audit-before-v1/InitialAuditFailureTests.xml
(8bf1bfb17555e48bbaf79b806d093a0830cc34e7627462d0a7eb6978a6c8568a),
initial-audit-after-v1.log,and initial-audit-package-v1.log/json. The final fresh
InitialAuditFailureTests XML hash is
8c90645990360eac33e377d4e087ce2e178b90709c654e5ac09f3dd582f1b1ae.

Actual DB/disk outages,commit ambiguity,crash recovery,durable alternate storage,
metric alert wiring and complete zeroization remain separate. No claim of
universal audit availability or complete project/security acceptance is made.
