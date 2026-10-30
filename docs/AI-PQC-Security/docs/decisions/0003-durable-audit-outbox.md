# ADR 0003: Durable audit outboxes with idempotent Monitoring ingestion

Date: 2026-10-20. Supersedes ADR0001's best-effort delivery policy.

## Why

Actual MySQL-backed testing showed events being dropped while a producer's
discovery cache lacked Monitoring. A successful user response did not guarantee
a saved audit event. Adding only a startup delay would not address outages or
producer crashes. The existing hardware/local scope does not require a broker.

## Decision

Auth and Business each own an `audit_outbox` table in their existing database.
The shared `platform/audit-outbox` library implements storage and dispatch, not
a shared cross-service database. Events have stable UUIDs and normalized fields;
passwords, tokens and protected business plaintext are not queue payloads.

- Registration and its event join one database transaction. Queue-storage failure
  rolls back user creation and yields a controlled503 response.
- Business terminal execution state and its event commit through one transactional
  writer, including failed operations. A STARTED row without terminal status can
  remain if the process crashes mid-operation; it is not a successful execution.
- Other audit-only paths synchronously enqueue their event before acknowledging
  the path. Monitoring HTTP delivery is asynchronous and is not a success prerequisite.
- A worker selects one due row using `FOR UPDATE SKIP LOCKED` in a transaction.
  It acknowledges only after a200/201 response containing the matching event ID;
  redirects,202 responses and wrong-ID receipts remain pending. Multiple workers
  skip locked rows. A worker crash rolls back its claim; it does not erase the row.
- Dispatch is at-least-once, not exactly-once. Monitoring's unique event UUID and
  content comparison make identical retries idempotent. Changed content for the
  same UUID returns409 and never overwrites the original event. Receiver times
  are normalized to microsecond database precision for a stable comparison.

## Bounds and operator responsibilities

Default scheduling delay2seconds; each flush processes at most10 records, stops
starting new work after a5-second budget, and bounds HTTP connect/read waits to
2seconds each. The last in-flight call can extend the flush beyond its budget.
Retry delays increase from2seconds to a60-second cap. After20 attempts the row
is retained as DEAD. Invalid/conflicting400/409/422 payloads dead-letter immediately.
401/403 are retried within the attempt budget so a corrected service key can recover.

`audit_outbox_records{status="PENDING"}` and `{status="DEAD"}` expose counts through
each producer's existing metrics. A DEAD row is a delivery failure, not success.
Operators must alert on dead/backlogged records, resolve the cause and use a
controlled replay procedure; this implementation does not silently auto-requeue
dead records or delete delivered evidence. Disk capacity, retention, alert routing,
least-privilege migration credentials and multi-replica performance remain
deployment responsibilities. No database or network outage can guarantee service
availability. Audit persistence failure deliberately prevents successful acknowledgement.

Schema creation is additive for the development MySQL/H2 workflow. A production
migration is still needed before removing DDL privileges. MySQL8+ is required for
the queue locking syntax. The brokerless design does not implement distributed
tracing, all-system tamper-proof logs or cross-database distributed transactions.

## Verification boundary

Tests cover rollback, preserved UUID/time, queue reconstruction, backoff, dead
records, concurrent claims, transactional producer writes, identical/concurrent
receiver retries, conflicting content and HTTP response semantics. Real process
restart/outage evidence is retained separately by `verify-local-stack.ps1 -VerifyOutage`.
These reliability tests are not model-accuracy results or a novel outbox algorithm.
