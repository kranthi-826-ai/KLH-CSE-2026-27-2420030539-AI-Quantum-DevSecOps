# AI/policy dependency failure and recovery results

Date: 2026-10-20. Frozen live protocol/source: `6b7495a`.
The actual local stack passed44 baseline checks followed by all four owned
dependency outage/recovery phases. No mock inference or public deployment.

## Implementation and bounded silent-peer checks

Business→Policy and Policy→AI now explicitly use2-second connection and5-second
read-inactivity timeouts. Real Java socket fixtures accepted connections but
withheld responses; both clients reached a SocketTimeoutException cause instead
of returning a decision/prediction. Policy wrapped its failure as502.
Final full-build test durations were5.085s and5.069s, with a10s outer test bound.

The initial Business timeout test failed because it expected
ResourceAccessException while Spring wrapped response extraction in a broader
RestClientException. The actual underlying cause was a socket timeout. That
failure XML was retained; assertions now require the RestClientException family
and the actual deepest SocketTimeoutException, not just any error. No test wait
was shortened or security check removed to make it pass.

These settings are **not** a whole-request deadline or guarantee against
slow-drip bodies, aggregate load, thread exhaustion or every failure mode.

## Live measurements

| Phase | HTTP | Client wall time ms | Actual result |
|---|---:|---:|---|
| Owned AI stopped |502|120.190|FAILED execution; no selected crypto/decision/envelope; Monitoring FAILURE |
| Real AI restarted |200|198.784|Verified PQC envelope; SUCCESS execution/event |
| Owned Policy stopped, AI still UP |502|65.961|FAILED execution; no selected crypto/decision/envelope; Monitoring FAILURE |
| Real Policy restarted |200|289.801|Verified PQC envelope; SUCCESS execution/event |

The stopped-service cases first confirmed their actual TCP ports unreachable.
They test connection refusal, separately from the silent-peer Java tests above.
No manual cryptographic downgrade or fabricated risk prediction was allowed.
The gateway's client-facing dependency error was generic. Each phase directly
checked MySQL execution state/payload fingerprint and expected policy row count,
then waited for the matching Monitoring event. Failed requests had no policy
decision and no cryptographic work recorded. Recoveries used the actual model
and crypto implementation with a fixed4KiB restricted demonstration request.

A separate read-only post-run database count check confirmed two FAILED,
unverified executions; two SUCCESS,verified executions; two policy decisions;
and two FAILURE/two SUCCESS monitoring events across the four fresh correlation
IDs. These counts are not an independent re-execution of inference or crypto.

Authentication used an ephemeral signed ROLE_USER fixture with this isolated
run's temporary key, not a persisted administrator grant. Normal login/JWT
issuance was checked by the preceding44-check suite. No tokens, keys, passwords
or full encrypted payloads were included in phase receipts.

## Regression, ownership and evidence

Full `mvn -q package` passed:49 fresh suites,114 tests total,109 passed,five
skipped,no failures/errors. All21 live-verifier/config unit tests passed.
Frontend and ML source was unchanged and those suites were not rerun here.

Owned AI process trees (including the Windows venv child) are now stopped as
trees, not only launcher PIDs. The live runner retains process transitions and
an explicit final cleanup receipt. All seven current owned process handles were
stopped; a separate post-run OS check found no listeners on8080–8083,8090,8091,
8761 and no matching project Java/Python process. Existing MySQL and unrelated
applications were untouched. Synthetic audit rows remain; nothing was deleted.

Ignored run directory:
`ml/artifacts/live-stack-4610ce49ab334daebb7b9ee656fb8e02/`.

| Receipt | SHA256 |
|---|---|
| verification.json |eba1a116c1abaf704cf669a8dc8fea44079a2ca2c55c8af60d3e099105655a30|
| dependency-ai-down.json |bfbabcdb3ef51d3ce662d6550d2b779eadb21a78624818ef94b25ce318da214a|
| dependency-ai-recovered.json |c92c4a9ebe5c7a872c922d955b8546c4b1b3ab14604baa238588701ccbae6e6d|
| dependency-policy-down.json |1ea97f567dff11ec9a23a3d3518c557d3e6072a22db6afa526732884de096ab4|
| dependency-policy-recovered.json |d99738a1a17ee795783b4b90ea6eda0ccf55c19d25b9fc4da8ac94d491db1e3a|
| cleanup.json |21f602181c0fa967ccd11ac2063589a065995a18340f90c6bcc36b9045a7b1c8|
| dependency-process-transitions.json |e374c4fe8b869d53089f77f0ff3c05249fa578b206562f5180a14f3a09401a3c|
| java-regression.json |b49270438db84d4860452589ce2c4bbe6a6c355d76ab1f1f4b0c3996c9df12bd|

The retained initial assertion failure is under
`ml/artifacts/dependency-timeout-first-failure/` with XML SHA256
`5653ea6c9c6bd30167e248649127068d82d0bda79a02a71ba5c34956e67a7db8`.
The read-only count receipt `dependency-audit-postcheck.json` remains with the
run and references each phase receipt hash.

Reproduce using [the frozen protocol](dependency-failure-protocol-v1.md).

## Remaining limits

Only isolated AI and Policy outages/restarts and silent accepted sockets were
covered. Database outages, malformed dependency responses, network partitions,
slow-drip bodies, simultaneous failures, sustained load, distributed recovery,
hard request deadlines, operator credential lifecycle and production TLS remain
separate acceptance work. Local restart success does not establish an
availability SLA, model improvement, attack detection or production security.
