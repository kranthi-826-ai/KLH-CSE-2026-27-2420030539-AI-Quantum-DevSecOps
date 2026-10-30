# Audit alert rule and real-engine verification — 2026-10-20

Protocol/rules/probe commit before execution: `f0fe6a7`.
Operator meanings and limits: `docs/monitoring-operations.md`.

## Verified outcomes

- The official Prometheus3.7.3 Windows archive matched the publisher's SHA-256:
  `a775b4718910cacfa5c80e97c39c4666818640afef59bc0c0d96b5398cc84531`.
  This matches the repository's existing version pin, not a latest/security claim.
- Promtool accepted both scrape configurations and their shared four-rule file.
- All10 scenario groups /22 alert assertions passed. They cover healthy state,
  hold timing, transient suppression, recovery, missing/NaN metrics, unrelated
  scrape targets and correct producer-label joins.
- The initial NaNx10 test-value shorthand was rejected by this tool version;
  explicit NaN samples passed before the protocol commit. No rule logic was
  weakened to pass a failing functional assertion.
- A real loopback Prometheus process used the unchanged rule file and synthetic
  exporter, recording these observed alert states:

| Elapsed seconds | State |
|---|---|
|0.63|inactive|
|6.69|pending|
|66.57|firing|
|67.60|inactive after recovery|

The bounded process finished in67.95s. Its own process stopped, and neither test
port19090/19091 remained listening. This probe used1s scrape/evaluation intervals;
the tracked deployment configurations use15s. The production one-minute hold
rule was not shortened. Polling observations are not exact activation timestamps.

## Evidence

Real-engine directory: `ml/artifacts/alerts-4947165d48be413fa4331074a5cb27a3/`.
SHA-256 of `verification.json`:
`98ffae8086be52e9a8b7a0d124732e006a7f4c827fba5c7a577b6dbdb8850b25`.

Repeatable wrapper run:
`ml/artifacts/monitoring-rules-17ac6cb147924c3bbe0d6cb05bd6fe99/` includes version,
configuration and test logs plus input-file fingerprints.
The new GitHub workflow job is configured but not remotely executed here.
Compose mounts the tracked rule file; Docker remained stopped and no container
deployment is claimed. Tool binaries/archive are ignored local artifacts.

## Explicit limits

The runtime exporter was synthetic; no attack traffic or real failed audit row
was created. Previous live tests separately proved actual producer metric exports.
No model/frontend code changed and no accuracy improvement is claimed. No email,
chat/webhook or external Alertmanager destination was configured or notified.
Rule validation and local firing/resolution do not prove deployed notification
delivery or that the entire monitored system is healthy. Deployment reachability,
operator destination, delivery/acknowledgement, access controls and retention
remain separate acceptance work.

Method reference: [Prometheus rule unit testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/).
