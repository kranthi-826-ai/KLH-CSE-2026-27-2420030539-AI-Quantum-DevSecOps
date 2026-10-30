# Durable audit outbox

Imported by Auth and Business through `AuditOutboxConfiguration`. The queue uses
each service's configured DataSource and transaction manager; no additional
always-running service is introduced. See `docs/decisions/0003-durable-audit-outbox.md`.

Configuration:

| Property | Default | Purpose |
|---|---:|---|
| monitoring.outbox.interval-ms |2000| Delay between worker flushes |
| monitoring.outbox.max-attempts |20| Attempts before retained DEAD state; valid1–100 |
| monitoring.outbox.dispatch-enabled |true| Tests can disable dispatch without disabling durable enqueue |

Workers keep credentials in runtime configuration, not event payloads. A failed
attempt stores only a fixed error code. PENDING and DEAD gauges require operational
alerts; delivered/dead rows are not automatically deleted. This is a bounded
worker, not a claim of bounded lifetime database storage.

Producer `enqueue` uses the caller's transaction when present, otherwise a
single committed insert. Use a transactional service boundary to atomically
persist application state and its event. Do not catch and ignore enqueue errors.
`ExecutionAuditWriter` and transactional registration demonstrate these boundaries.

Build/test from the root Maven reactor with `-pl platform/audit-outbox -am test`.
The tests use H2 MySQL mode; actual MySQL/outage verification is a separate gate.
