# ADR 0006 — Explicit outbox operations and retained replay evidence

Date: 2026-10-20. Producers: Auth and Business. No automatic deletion or replay.

## Operations contract

Signed ROLE_ADMIN sessions may access `/api/v1/auth/audit-outbox` and
`/api/v1/business/audit-outbox`. Other authenticated users receive403 before
request-body parsing; anonymous callers receive401. Controller checks remain
as defence in depth. The shared internal publisher key does not grant access.

GET returns pending/dead/delivered counts, the oldest pending **event age**, and
at most20 recent DEAD-event metadata entries. No event body, credentials or user
payload is returned. Event age uses occurrence time, not enqueue time; clocks
and backdated events affect it. Future ages are clamped to zero.

POST `<producer-path>/replay` accepts `eventId`, one of the fixed `reason` codes,
and optional `apply`. Missing/null/false means a nonmutating preview. Explicit
true permits only DEAD→PENDING. PENDING/DELIVERED returns409; unknown UUID404;
invalid inputs400. Response headers prohibit caching. Allowed reasons:

- RESTORED_DEPENDENCY
- CORRECTED_CONFIGURATION
- VERIFIED_RECEIVER_STATE

An applied operation locks the row and atomically inserts an append-only replay
log (operation/event UUIDs, signed actor, reason, time, prior attempts/error),
then resets retry state. Event UUID, payload and original occurrence time remain
unchanged. Five-second transaction timeout bounds database lock waits. Concurrent
or repeated attempts do not create duplicate operations while the event is no
longer DEAD. A future new DEAD cycle can be deliberately replayed and logged.

## Monitoring and retention

Existing `audit_outbox_records{status="PENDING"|"DEAD"}` gauges are retained.
New `audit_outbox_oldest_pending_event_age_seconds` is exported by both producers.
These metrics alone do not send alerts. Prometheus/notification rule deployment
and delivery testing remain acceptance work; Docker was stopped during this
implementation and was not started to claim alert coverage.

Never purge PENDING/DEAD rows or replay logs to hide a backlog. Investigate the
receiver/key/discovery/conflict first, preview a specific event, and apply once
only after the cause is corrected. A409 receiver conflict is not permission to
overwrite the receiver's record. If delivery cannot be restored, retain the event
and document the incident. Production retention requires an agreed duration,
verified backup/export and restore procedure before any separately authorized
deletion; this implementation intentionally performs none.

## Verification boundaries

H2 tests exercise permanent failure, preview, replay identity, invalid state,
rollback and concurrent attempts. Actual HTTP tests cover authorization and
malformed requests. Optional local `-VerifyOutage -VerifyReplay` changes only
the newly generated outage fixture's row to DEAD, then exercises the HTTP replay
and recovers its original UUID after Monitoring returns. That fixture transition
is simulated, not observed natural retry exhaustion. Read the result report for
executed evidence. Operator provisioning/revocation, incident notification,
durable archive automation and deployment hardening remain separate work.
