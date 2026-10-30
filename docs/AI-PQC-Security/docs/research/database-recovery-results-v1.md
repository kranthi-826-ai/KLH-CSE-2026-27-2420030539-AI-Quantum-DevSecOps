# Isolated MySQL audit recovery results

Date: 2026-10-20. Protocol commit: `3396908`; Windows text-comparison correction:
`ac29072`. No production data, model, API behavior or account permission changed.

## Scope and outcome

The current table definitions for Auth outbox/replay, Monitoring events and
Business executions were read with SHOW CREATE only. Two fresh fixture schemas
were created for each run. Source schemas contained six synthetic rows across
four tables; no real rows were copied. Native MySQL/mysqldump 9.7.1 performed the
actual backup and restore. This is not a four-database application restore.

Final run passed nine checks in **1.57 seconds**:

1. Newly created restore target is empty.
2. Modified backup fails checksum validation before any import.
3. Deterministic data-only dumps of source and restored fixtures are identical.
4. All four table definitions are identical immediately after restore.
5. Counts match: outbox3, replay1, event1, execution1.
6. PENDING, DEAD and DELIVERED states survive restoration.
7. Nanosecond occurrence component123456789 survives restoration.
8. Duplicate stable Monitoring event identity returns MySQL1062 after restore.
9. Failed duplicate insertion does not change the data rows.

The duplicate-insert test is not a claim that auto-increment counters never
advance on a failed insert. Timing includes this small local fixture only and
cannot be extrapolated to production RTO, throughput or real-user scale.

## Retained failed run

`database-recovery-v1` restored schema and row content successfully but failed
the queue-state comparison because Windows CLI output used CRLF rather than LF.
The comparison now uses `splitlines()` without changing the database or fixtures.
The failed result and schemas remain. A new run/schema pair was used for v2;
the failure was not overwritten or relabelled passing.

## Evidence identifiers

All under ignored `ml/artifacts/`:

- Failed `database-recovery-v1/verification.json`: SHA256
  `ec4b5b1c33d78a61b2b4ac5013593922acae484f3b0d944024fb07d4087475ad`.
- Passed `database-recovery-v2/verification.json`: SHA256
  `8e574c9656cf1e5dc0e37f38282064800f07d45564aa45a3558a910d872c0da2`.
- Passed synthetic SQL backup (6254 bytes): SHA256
  `9effd4312082c8cb767edc302a9731a3edc8655005f7b13f94e10d2fb19fd4d5`.
- Source/restored data-only dump SHA256
  `a29b3ccaef0df06f523e22e394f97c4cd8bff17615b336cc62690bb19d5b16cf`.

Four guard tests passed; all14 local live-verifier/configuration unit tests
passed. No Java or frontend source changed, so those suites were not rerun in
this checkpoint. Four test schemas total remain from the two runs; their exact
names are in the corresponding receipts. No deletion or background server start
was performed. Existing MySQL was left running.

## Limits

No full user/policy database dump, encrypted/off-host backup, restore into an
application deployment, cross-service transaction snapshot, point-in-time
recovery, sustained concurrent-write test, retention deletion or disk-loss test
was performed. Those requirements remain open. Read the
[recovery runbook](../database-recovery.md) before reproducing the fixture test.
