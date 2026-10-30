# Adaptive audit persistence monitoring

Date: October21,2026. This change connects the existing Business Service
`adaptive_security_failure_audit_errors_total` counter to reviewed monitoring
rules and the administrator-only operational alert API/dashboard.

## Semantics

`AdaptiveAuditWriteFailure` is critical after a positive counter is observed
for15seconds. It catches a positive first scrape as well as later increments;
using only a rate/increase would miss an error before the first observation.
The incident remains firing while the observed process-lifetime count is
positive. It is not an event ledger or evidence of successful encryption.
An operator must reconcile request, execution and outbox records and storage
health. Restarting clears the in-memory counter, not the underlying incident.
There is no automatic reset/acknowledgment endpoint or silent downgrade.

`AdaptiveAuditMetricUnavailable` warns after1minute when the Business Service
scrape succeeds but its required counter is missing, negative or NaN. Matching
uses job and instance so a same-address unrelated exporter cannot hide missing
telemetry. Unavailable service scrapes remain covered by AuditProducerUnavailable.
Targets are restricted to the configured local/Compose Java job names and8082.

Both alert names are explicitly accepted by the monitoring API and dashboard
schema. Existing authentication/administrator checks and stale/unavailable
source handling remain unchanged. Email delivery still requires separately
configured and verified provider settings; adding a rule is not inbox proof.

## Verification

Pinned Prometheus3.7.3 promtool validates both checked-in configurations and all
15 rule scenarios, including five new scenarios: first-positive hold/reset,
observed zero, missing counter despite another job's same-instance metric,
NaN and unrelated targets. Evidence:
`ml/artifacts/monitoring-rules-a8d4baa4612049099a78f65e2feb064d/`.

OperationalAlertHttpTests:three passed,zero failures/errors/skips. A loopback
HTTP fixture verifies both new alert names reach an administrator, ordinary
users are rejected before upstream access, and malformed upstream states
remain unavailable. It is not a real Prometheus/persistence-fault chain.

Frontend104tests and production build pass. Two new component cases render
the reviewed alert summaries/states and validate both names. Evidence:
`ml/artifacts/audit-alert-ui-tests-v2.json`. No browser visual test was obtained.

Full root `mvn -q package` also completed with exit0. All54 fresh Surefire
reports total180 tests:175 passed,five skipped,zero failures/errors. XML paths,
timestamps and hashes are retained in
`ml/artifacts/audit-alert-java-regression-v1.json`; package output is retained
in `audit-alert-package-v1.log`. No project listener remained on5174,8761,
8080–8083,8090 or8091 after verification. Skipped tests are not passing tests.

The first test attempts are retained:promtool rejected unsupported NaNx20
fixture shorthand; explicit NaN values corrected the fixture. Two UI assertions
incorrectly expected internal rule identifiers in the presentation, which
intentionally shows human-readable summaries; assertions now verify summaries,
states and schema acceptance. These were test-definition errors, not masked
production failures. The first Maven command was rejected by PowerShell's
unquoted dotted property; quoted properties executed the targeted test.

Limitations: no fresh actual database failure was injected; no live engine to
dashboard/email propagation of these particular alerts is established. A crash
before scrape can lose the counter; a restart or scrape disappearance can end
its visible alert without proving durable incident resolution. Durable alternate
audit storage, process-independent incident tracking and broader acceptance
remain open. No model training or detection-accuracy change occurred.

Subsequent scoped update: `adaptive-audit-alert-live-results-v1.md` verifies the
positive-counter production-rule engine through the actual administrator API
using synthetic metrics. This supersedes the earlier absence of engine/API
propagation evidence only; browser,email and genuine storage-fault boundaries
above remain unchanged.
