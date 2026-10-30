# Audit outage/restart recovery experiment

Date2026-10-20. Scope: real local Auth, Business, Monitoring, Gateway, Eureka,
policy/inference services and MySQL. This is a reliability experiment, not ML
training, a novelty claim or proof of production readiness.

## Protocol

`scripts/verify-local-stack.ps1 -VerifyOutage` builds on the existing21 live
API/database checks. The verifier stops only its owned Monitoring process,
submits a failed login for a unique nonexistent account directly to Auth,
and confirms that a PENDING event was committed in the Auth database. The
orchestrator then kills and restarts its Auth process with the same database,
verifies that the same event remains PENDING, restarts Monitoring, and waits
for delivery. Finally it submits an identical event over HTTP and then changed
content under the same UUID. No password/token is written to evidence.

Synthetic failed authentication is intentional; it does not bypass auth or
attack a third-party system. Original application/test records are retained.
Only queue/collector changes are under test; the promoted model is unchanged.

## Final observed outcome

Final strict-receipt run: `ml/artifacts/live-stack-1889a28b9c9e4a44823036bb9d304f0a/`.
Earlier passing recovery run092e9e53c4884c44aa5bb1f6229cd892 is retained as a
checkpoint before the receiver-acknowledgement checks were tightened.

| Check | Observed |
|---|---|
| Existing complete API/MySQL verification |21 checks passed |
| Monitoring actually stopped | Unreachable during enqueue |
| Auth response for nonexistent account |401; event persisted locally |
| Auth process killed and restarted | Same event retained as PENDING |
| Monitoring restored | Event delivered and producer row marked DELIVERED |
| Identical HTTP retry |200; one stored event |
| Same UUID, changed content |409; original content retained |
| Cleanup | Owned processes stopped; MySQL left running |

Event UUID: `e7f03b21-99fa-4def-96e0-6ecba410ee4f`.
Local verification hashes:

- API/MySQL `verification.json`:
  `dd5ce70b321f746332b8b751822af09dec35b82f2a3a02921d4c5399f5ef97f2`
- `outage-verification.json`:
  `a45aa110e06e63005a1c986c39b9386500fa083f00d00ef25bcd6a9b948a7161`

Tracked summary: `docs/research/evidence/audit-outage-recovery-v1.json`.
Producer/collector transaction tests separately prove that a failed enqueue
rolls back user creation or a completed execution, and concurrent identical
collector submissions produce one row. H2 queue tests exercise preserved
UUID/time, rollback, backoff, retained DEAD records and concurrent row claims.
Six additional real HTTP receiver tests ensure that only200/201 with a matching
event ID acknowledge delivery.202, redirects, wrong-ID and401 responses remain
pending;409 remains retained DEAD. Final reactor87 tests total:82 passed, five
opt-in tests skipped, no failures/
errors. Python110 passed; frontend18 passed and production build succeeded.

## Failures retained and interpretation

The first outage run (`live-stack-91b2cd57706340849d1d7c3b9cf6f1fa`) retained the
event through restart and recovered delivery, but failed the conflicting-ID
HTTP status assertion. Service-level rejection worked; framework error
dispatch produced the wrong public status. An explicit409 handler and real
HTTP regression test were added before the final rerun. That earlier run is
not reported as a fully passing experiment. Its logs and prepared/restart
artifacts remain local. Future verifier failures receive a phase-specific
negative JSON rather than overwriting another run.

Delivery is at-least-once with idempotent storage, not a general exactly-once
distributed transaction. This test does not crash the OS/database, restore
backups, saturate a cluster, exhaust disk, or cover every crash timing. Pending
and dead gauges require alerts, controlled replay and a retention/storage policy.
No records are silently discarded after the retry cap. Production migrations,
least privilege, ingress/TLS, and security/load acceptance remain separate gates.
No change to intrusion-detection accuracy or promoted model is claimed.
