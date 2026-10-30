# Audit delivery alerts and operator response

These alerts concern delivery of audit records, not AI threat classification.
They neither prove an attack nor change the selected cryptographic mode.

## Rules

| Alert | Condition and hold | Operator response |
|---|---|---|
| AuditOutboxDeadEvents | At least one retained DEAD row for one minute | Inspect recent DEAD metadata, correct the delivery cause, preview and explicitly replay a specific event |
| AuditOutboxOldPendingEvents | Pending count positive and event age above120s, continuously for two minutes | Inspect receiver/discovery/credentials and source clocks; do not interpret age as queue residence time |
| AuditProducerUnavailable | Expected Auth/Business scrape fails for one minute | Restore service/scrape connectivity; missing metrics are not a healthy empty queue |
| AuditOutboxMetricsUnavailable | Producer scrape works but pending/dead/age metrics are missing or invalid for one minute | Check exporter registration and database access; do not clear the alarm by hiding a metric |

Producer scrape selectors match this repository's local/Compose job names and
ports8081/8082. Adapt and retest them when deployment names/ports change. Rules
separate application/instance identities and clear after their conditions resolve.
Transient conditions shorter than the hold times do not become firing alerts.
Total real detection delay also includes scrape/evaluation intervals.

## Configuration and validation

Both `prometheus.yml` and `prometheus-local.yml` load `audit-alerts.yml` relative
to the configuration directory. Compose mounts the same tracked rule file next
to its configuration. No other application container needs the rules file.

The monitored producers expose real gauges, verified by the live API runner.
Use `promtool check config` on both configurations and `promtool test rules` on
`infrastructure/monitoring/audit-alerts.test.yml`. The CI job uses the pinned
Prometheus3.7.3 image already present in Compose. A local Windows helper
`scripts/prepare-prometheus-tools.ps1` downloads that exact official release,
checks the publisher SHA-256, and extracts tools under ignored artifacts.
This is a reproducibility pin, not a claim that it is the newest secure release.
Review dependencies before any production deployment.
After preparation, `scripts/verify-monitoring-rules.ps1` runs both configuration
checks and rule scenarios and retains logs/input fingerprints in a unique ignored
artifact directory. It starts no server. The separate real-engine probe remains
explicit and bounded.

Test cases cover healthy queues, held/transient DEAD conditions, resolution,
pending-age hold/recovery, empty pending counts, producer scrape outages, absent
and NaN metrics, unrelated targets, and cross-producer label isolation.

An optional bounded loopback test runs actual Prometheus with the unchanged rule
file and synthetic exporter metrics. It records inactive→pending→firing→inactive
and then stops its own server. It does not use real user audit events, start
Docker, or configure/send external notifications.

## Recovery and retention

Signed administrators can inspect `/api/v1/auth/audit-outbox` and
`/api/v1/business/audit-outbox`, including at most20 DEAD-event metadata entries.
Follow ADR0006 for a dry-run and explicit replay. Ordinary users cannot read or
operate those endpoints. Never change event payload/UUID to bypass a receiver
conflict. A pending retry or delivered event cannot be replayed as DEAD.

No retention deletion is automatic. Keep failed events/replay logs, investigate,
and verify backups and restores before proposing separately authorized cleanup.

The isolated [audit recovery rehearsal](database-recovery.md) now verifies
synthetic MySQL dump/restore against current audit table structures. It does not
back up live users or establish full application/disaster recovery. Existing
retention and deployment backup requirements remain open.

## Notification boundary

Rules become visible in a running Prometheus Alerts view. This repository does
not yet have a verified real-provider email/chat destination.
Rule testing and local firing/resolution do not prove an operator was notified.
External destination, credentials, delivery/acknowledgement and outage testing
must be explicitly configured and verified before claiming notification coverage.
The user chose dashboard + email. The dashboard now has an explicit-load,
administrator-only Operational alerts view; email sender/provider and recipient
configuration remain pending. The view separates actual Prometheus states from
outbox observations and marks failed/retained sources unknown/stale.
Production ingress/TLS and metrics access controls also remain requirements.

An optional secret-file SMTP configuration and bounded real Alertmanager tests
now exist. Local synthetic firing/retry/recovery delivery and the real
Prometheus→Alertmanager→loopback SMTP chain passed. This is not real-provider
TLS/authentication/inbox evidence. See [email setup and deployment boundaries](email-alerts.md)
and [retained transport results](research/email-alert-results-v1.md).

Primary reference: [Prometheus rule unit testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/).
