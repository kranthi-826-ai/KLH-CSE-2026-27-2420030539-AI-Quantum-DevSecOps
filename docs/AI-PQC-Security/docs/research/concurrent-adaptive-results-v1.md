# Bounded concurrent adaptive results

Date: 2026-10-20. Frozen verifier/protocol commit: `be576d9`.
Application binaries came from the successful root package for `d17924f`;
no production Java/model changes were made for this experiment.

## Observed outcomes

The existing actual-service baseline passed44 checks. The subsequent concurrent
experiment passed all24 requests: six batches of four, with rotated submission
order. Every batch had four overlapping client HTTP intervals. There were six
CLASSICAL, six HYBRID and six PQC verified envelopes, and six expected HTTP422
HIGH-risk/incompatible-capability denials. No unexpected429 or5xx occurred.

Direct MySQL reads verified exactly24 executions,24 policy decisions and24
monitoring outcomes, uniquely bound by correlation/decision/execution identity.
Owner, mode, risk, model/policy version and payload hash matched each expected
request. Successful response identities matched their own database records.
All six denied executions were unverified with zero recorded crypto latency.

Whole verifier duration was6.55s, including registration/login, batch scheduling,
HTTP work, asynchronous event delivery waits and direct database queries. It is
not the duration of a single request or a maximum-throughput measurement.

| Case | Requests | Actual HTTP | Observed client HTTP range ms |
|---|---:|---:|---:|
| PUBLIC / CLASSICAL |6|200|263.275–303.056|
| PUBLIC / HYBRID |6|200|262.204–321.690|
| RESTRICTED / PQC |6|200|261.696–325.259|
| RESTRICTED / unsupported quantum-resilient mode |6|422|259.455–328.405|

These ranges are individual client-observed times, not confidence intervals,
isolated crypto timings or stable tail percentiles. No previous run is treated
as a matched sequential baseline. A small scheduling/runtime difference between
these cases is not a performance ranking of cryptographic security modes.

## Host and cleanup

Non-isolated Windows laptop: i7-13650HX,14 cores/20 logical processors, about
16GiB visible RAM. During startup the host snapshot showed5% CPU load and
2,128,420KiB free physical memory. Power/thermal state and unrelated background
tasks were not controlled. Java services used the runner's64–512MiB heap bounds.

The runner stopped its seven owned process trees. Subsequent OS checks found
zero owned handles and zero listeners on project ports8080–8083,8090,8091,8761.
MySQL/unrelated applications were left alone; synthetic users/audits retained.

## Evidence and verifier checks

Directory: `ml/artifacts/live-stack-faab948382ec4864a639e9cf3efdc968/`.

| Receipt | SHA-256 |
|---|---|
| concurrent-adaptive.json |21131c610e09646a38b62e9e60860b891699a85dea8004e7644da8b2cf99257f|
| verification.json |50be36565abdfd8466cbd014c8585d3a6044880142bb2bf20f14bc072f540a2a|
| cleanup.json |346bb03e15297634242d529a84e937e0d1d9f7d1a42ed0d428390e1901b78c1f|

The directory also retains host/process snapshots and local logs. Receipts do
not contain credentials or full crypto envelopes. All25 live-verifier/config
unit tests pass, including the four new concurrent-verifier test methods;
negative subcases detect missing/duplicate/crossed identities, wrong owner,
version, payload, denied crypto work, event outcome and response identity.

## Remaining limits

This is a four-client local correctness check with one user and one real MEDIUM
model-input feature flow. It does not prove cross-tenant isolation, parallel
server execution, distributed rate limiting, sustained throughput, saturation
recovery, production availability, or detection accuracy. No model was trained
or promoted. Broader workload/failure coverage and frontend/operator/deployment
acceptance remain open. See `concurrent-adaptive-protocol-v1.md`.
