# Post-crypto audit completion results

Date:2026-10-20. Frozen implementation/live protocol:38ce71d.
See post-crypto-audit-protocol-v1.md for the state table and verification scope.

## Reproduction and corrected semantics

Actual crypto verification can pass before a later audit transaction fails.
The earlier frontend contract incorrectly rejected every FAILED/verified=true
record. The new App regression initially failed against that contract;the other
four snapshot-boundary tests passed. We corrected this assumption rather than
erase genuine crypto evidence or count a failed request as successful protection.

The initial two Spring/H2 tests also failed. One already demonstrated the
correct FAILED/verified=true persisted state but exposed inaccurate unselected/
unknown failure metric labels. The other showed that a second failure while
saving FAILED replaced the original exception and left no failure-audit metric.
Original XML/logs are retained;only synthetic errors were injected.

## Backend behavior now verified

Tests use real Spring transaction proxies,H2/JPA/JDBC,outbox code and actual
CLASSICAL seal/open/equality. The policy response is mocked and outbox enqueue
throws controlled exceptions;this is not a live MySQL/disk fault experiment.

1. Completion enqueue throws once,then recovers. The success transaction rolls
   back;the fallback commits one FAILED execution retaining true verification,
   decision and mode,together with one PENDING API_ACCESS_DENIED/FAILURE event.
   The operation throws and returns no envelope. Failed-flow metrics retain
   the known CLASSICAL/LOW labels;no success metric is produced.
2. Completion enqueue and failure enqueue both throw. Both transactions roll
   back,leaving the earlier STARTED row without durable crypto completion and
   no outbox event. The original exception is rethrown with the secondary failure
   suppressed. Exactly one failed-flow increment and one failure-audit-error
   increment occur. The response is not successful and no envelope is returned.

The dedicated failure-audit counter is initialized at startup. It is in-memory
telemetry,not durable storage or a configured alert guarantee. A STARTED stored
record cannot tell an operator that cryptography definitely never ran;it tells
them no completion result was durably recorded. Failure recovery/ambiguity needs
separate operational handling and is not fabricated as a successful audit.

## Frontend behavior

Well-formed FAILED/verified=true records load normally. The table and decision
journey say Crypto verified · flow failed,with neutral rather than verified-
success styling. The spotlight and failure note distinguish a passed check from
a successful request. Known crypto timings remain visible with a failed-flow
warning. Failed flows remain excluded from successful protection shares and
successful-flow averages. Missing profile/timing wording now says recorded,
instead of claiming cryptography definitely did not execute.

STARTED/verified=true still fails validation. Boolean/type/identity/profile,
malformed-record and other prior validation checks remain. The old FAILED/true
rejection test was replaced by STARTED/true rejection plus explicit acceptance
and whole-App exclusion/label assertions for the newly established valid state.

Full frontend100 tests passed and production build passed. The first fixed-code
full run had99/100 passing because one existing no-data test expected the old
wording No completed timing for this execution. Updated that assertion to the
more accurate recorded wording;all data/verification assertions remain. Its
one-failure report is retained,not overwritten.

## Full and actual-service regressions

- Full root Maven package succeeded:176 tests across53 fresh suites,171 passed,
  five skipped,zero failures/errors. Fresh XML timestamps/hashes retained.
- Actual local baseline44 checks and all32 adaptive matrix cases passed on the
  rebuilt services:24 verified envelopes and eight expected denials. These are
  ordinary real-model/MySQL requests,not the post-crypto injected storage faults.
- Independent read-only MySQL joins verified32 executions,32 decisions,32 outcome
  events,24 verified/eight denied and32 consistent identity/version/outcome joins.
- Owned services stopped;OS check found no project listeners. MySQL and unrelated
  apps left alone;synthetic audit rows retained. No model training or promotion.

## Evidence

Live directory:ml/artifacts/live-stack-9b8a71128149451b87966dd228211af1/.

| Receipt | SHA-256 |
|---|---|
| verification.json |814c594c8b9849851455c7f0472a484b8b59ecb2f9cb0653df9686824762b9d2|
| adaptive-matrix.json |5c6b9b46f5534fc5b1323477abc36b75c3ebe0704894e11ca172fbce6b01b9f5|
| adaptive-audits-recheck.json |8d4760adb434cff6990de9db50548ed7d70ac8e4fdac9ce23e67fd3e0db71551|
| java-regression.json |a25955180342309d0b9450938707cf7b61c0fdafb5a46b119d86d8fc89f2b4b8|
| cleanup.json |16d21731d57587f115cbaed1cc41002a95e13b8f7fac039aaaa205c910a8c354|

Other artifacts under ml/artifacts:

| Receipt | SHA-256 |
|---|---|
| post-crypto-java-before-v1/PostCryptoAuditFailureTests.xml |a4182eadd4c0a228e4da32cc4660be5211d4a01b8e7e38ef0a60fadf18dd9665|
| post-crypto-frontend-before-v1.json |b1b6db0fad452034f3cfaf22dbdfb0567cf94611e7791c2ef2ca232b7de1dce6|
| post-crypto-frontend-after-v1.json |e53c2fadd0cbf7d47b0e3ccd9d78de6c99420b7203432fb957bf0f0250d7e4cd|
| post-crypto-frontend-after-v2.json |d98c7839c0ccc3ee8cd18f00147a3ca489c5d636c4510de17cc0ad1fb9045038|

Targeted Java logs and full-package log/timestamp/exit receipt are also retained.

## Remaining limitations

Initial STARTED-write failure handling,real MySQL/disk/commit-ack ambiguity,
process crashes,metric persistence/alert wiring and actual browser display of
the injected post-crypto state remain unverified. If the store is unavailable,
this implementation cannot guarantee a durable failed record. No claim of
complete fault tolerance,zeroization,successful response delivery or improved
intrusion-detection accuracy follows from these tests.
