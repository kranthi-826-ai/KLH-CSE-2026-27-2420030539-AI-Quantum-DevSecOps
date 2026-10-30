# Adaptive audit alert live propagation

Date October21,2026. Probe source revision bb3191a; packaged application source
31edbe6. Command: `scripts/verify-local-stack.ps1 -VerifyAuditAlerts`.

The actual local stack passed44 API/MySQL baseline checks, then ran a native
Prometheus3.7.3 instance with the checked-in production rules. A loopback exporter
emitted synthetic audit-write-failure metrics; its instance label explicitly
identifies a synthetic Business target on8082 so the production scope applies.
No genuine Business metrics or database outcomes were falsified or modified.

Prometheus and the actual Gateway/Monitoring administrator API both observed:

| State | Prometheus elapsed seconds | Monitoring API elapsed seconds |
|---|---:|---:|
| inactive |5.72|5.77|
| pending |11.96|11.99|
| firing |27.63|27.65|
| inactive after simulated counter reset |29.73|29.76|

The measured firing follows the unchanged15second hold. These are one-run
elapsed observations, not latency guarantees. Counter reset emulates a process
reset; it is not proof of recovery or durable incident resolution. Ordinary-user
access was403 before reading the alert engine, and administrator retrieval with
the engine stopped was503/unknown instead of an empty healthy list.

Evidence:

- Stack baseline and cleanup:
  `ml/artifacts/live-stack-81d6242faedb4674881335602655e155/`.
- Engine/API state trace, generated configuration and native logs:
  `ml/artifacts/adaptive-audit-alerts-01bacdd749684e2a92eae08494db7e6a/`.
- Live-verifier/config unit suite:26tests passed.

Engine receipt reports passed=true,synthetic_metrics_only=true,
counter_reset_simulated=true,database_fault_injected=false,
external_notification_configured=false and owned_process_stopped=true.
Stack cleanup confirms all seven owned services stopped. OS listener checks
found none on8761,8080–8083,8090,8091,19090or19091; MySQL was not stopped.

A follow-up direct Business metrics read was attempted after automatic cleanup
had completed and received connection refusal. It did not establish actual
Business counter exposition and was not retried by restarting the stack. No
successful direct-metric receipt is claimed. Existing production-counter Java
tests, rule tests and this synthetic engine path remain distinct evidence.

This closes the measured engine-to-API propagation gap for the positive counter
alert only. Missing-counter live propagation, real storage fault injection,
browser rendering, durable incident persistence and external email delivery
remain separate requirements. No ML model, threshold or security setting changed.
