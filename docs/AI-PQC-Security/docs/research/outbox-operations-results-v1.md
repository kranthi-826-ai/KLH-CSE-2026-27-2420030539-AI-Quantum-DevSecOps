# Controlled outbox operations — 2026-10-20

Implementation/protocol commit before live execution: `5e9f420`.
Design and safe operator procedure: ADR0006.

## Executed evidence

- Full Java reactor:107 total,102 passed, five opt-in tests skipped, zero
  failures/errors. Six new H2 tests cover retained permanent failure, preview,
  identity/payload/time preservation, ineligible/missing state, atomic rollback,
  concurrent replay, event-age semantics and invalid operation inputs.
- One new real HTTP test covers anonymous401, user403 before body parsing,
  administrator summary/preview/apply, malformed UUID400, and repeat replay409.
- The initial HTTP run failed because an omitted primitive apply field produced
  a parse400, not the required dry-run default. Apply is now nullable and only
  explicit true mutates; path-level admin authorization also precedes parsing.
  Initial/rerun logs are retained, not presented as an initially passing test.
- Actual local stack/MySQL:44 checks passed, including both producers' signed
  administrator-only summaries and live Prometheus metric export.
- Controlled replay changed only the newly created outage fixture to DEAD.
  A user received403; omitted apply preview left the row DEAD with zero logs;
  explicit administrator apply created one operation; repeat apply returned409.
- Monitoring was still unavailable during replay. Normal bounded delivery
  retries resumed; restoring Monitoring delivered the original event UUID.
  Identical receiver retry200 and conflicting content409 retained exactly one row.
- The bounded gateway burst still passed. Four live-verifier unit tests passed.
- Owned test services stopped; no project test listeners remained. MySQL retained.

Local evidence directory:
`ml/artifacts/live-stack-3954c10522cf4526a7c47af8515c32dc/`.
Event UUID: `ac1501e1-bccc-47e5-8a5b-3252a9d30ba3`.
Replay operation UUID: `d0006ce4-950b-4ea5-8050-ad9268dc30c5`.
Reactor log: `ml/artifacts/outbox-operations-reactor-20261020.log`.
Initial/rerun HTTP logs: `ml/artifacts/outbox-operations-http-20261020.log` and
`ml/artifacts/outbox-operations-http-rerun-20261020.log`.

SHA-256 evidence fingerprints:

- `verification.json`:
  `1b4fa9baddfcd025a9399b61e8c035b6bfccfd913fa1ffafd8c6d14af16d5528`
- `outage-replay-verification.json`:
  `801ae63791ddaa8de8cbe3446dce2685dbc2390902d6b4957a18ad9ff13228ca`
- `outage-verification.json`:
  `40c501c69a86768f58814278c7938824c510bcd87bc499a5b710fbd4f1fb1efd`

No model changes, frontend changes, password/token evidence or automatic deletion.
The MySQL DEAD transition was a deliberately simulated fixture, not a claim of
natural retry exhaustion. Natural permanent-rejection handling is tested in H2.

## Remaining limits

Metrics are exported, but deployed alert/notification delivery is not verified.
Docker was stopped and was not started. Oldest pending event age is not queue
residence time and depends on source timestamps. Operator provisioning/revocation,
archive/restore/retention automation, monitoring uptime, production migrations,
least-privilege access and broader fault/load acceptance remain requirements.
This is local reliability/authorization evidence, not ML accuracy or universal
security. Replay preserves the receiver's existing conflict-rejection behaviour.
