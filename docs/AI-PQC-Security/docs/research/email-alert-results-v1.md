# Optional email transport: bounded local evidence

Date:2026-10-20. User selected dashboard + email. No model was retrained or
promoted. No real SMTP credentials were read and no external mail was sent.

Frozen implementation commits:73dfb01(config/direct transport),
b586df7(real rule-chain integration). Existing user README/PRD edits were not
staged. Runtime binaries and artifacts remain ignored; this report preserves
their evidence identifiers and limitations.

## Tool and protocol

Official Alertmanager0.34.1 Windows amd64 archive publisher SHA256:
`69624d6ce3674dbcf8cefc5a93d7028d00bbd5e0196a8384907f51593a495fef`.
Download checksum verified before extraction. Existing checksummed
Prometheus3.7.3 used for the integrated run; no Docker daemon started.
Local sink accepts only fixed example.test sender/recipient envelopes and
cannot relay. It rejects the first DATA message451, then accepts retries.
SMTP TLS is disabled only in the synthetic loopback fixture; the production
renderer requires TLS and a separate password file with normal certificate checks.

## Measurements

| Check | Observed result |
|---|---|
| Direct real Alertmanager→local SMTP | Passed in10.09s; one firing and one resolved mail accepted; one temporary failure retried |
| Three identical active alert submissions | No additional immediate firing mail during the5s observation; not a long-duration repeat/HA guarantee |
| Real production rule→Prometheus→Alertmanager→local SMTP | Passed in77.05s; firing and recovery receipts; one temporary failure retried |
| Unchanged1-minute rule hold | Inactive0.54s,pending6.57s,firing66.27s,recovered75.28s relative to child start |
| Configuration/live-verifier unit tests |10 passed, including6 email-specific tests |
| Optional Compose syntax |Validated with tracked example values; no daemon, provider or container-permission proof |
| Cleanup |Owned processes stopped; no listeners on19090/19091/19093/19094 afterward |

The synthetic integration keeps DEAD active8s after firing to allow mail retry.
Its Alertmanager grouping intervals1s/2s accelerate **transport testing only**;
production30s/5m/4h grouping/repeat and Prometheus rule holds are unchanged.

## Evidence

Under ignored `ml/artifacts/`:

- `email-transport-v1/verification.json`, SHA256
  `9d6ebdb8ae5df0f3927acb64828eea20762d8e3e4bb0660464af1d67ec52959d`.
- `email-rule-chain-v1/verification.json`, SHA256
  `126c3f169a3d050325c75730d14813838948992af2c9f2596ea868b46ebc655a`.
- `email-rule-chain-v1-engine/verification.json`, SHA256
  `d020316526d1dbf226625ba63c75bd2f2deb09d5c21e57ff5fbaecd04451698e`.

## Not established

Provider TLS/authentication, sender-domain configuration, real inbox delivery,
acknowledgement, production grouping/repeat timing, deployment secret mounts,
cross-host permissions, distributed availability or delivery guarantees remain
unverified. The optional Compose candidate requires a reviewed readable secret
mount for its non-root container before deployment; host files are0600, not
world-readable. Sender/provider/recipient details remain pending.

No detection-accuracy or cryptographic-security improvement follows from adding
notifications. Existing failed model gates and all other project requirements
remain open. Official configuration reference:
[Alertmanager](https://prometheus.io/docs/alerting/latest/configuration/).
