# Bounded concurrent adaptive request protocol

Frozen before execution, 2026-10-20. This is a local consistency/resilience
check, not a maximum-capacity benchmark, ML evaluation or public attack test.

- Use rebuilt real local services, the unchanged promoted RF model with SHA-256
  `c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`,
  native MySQL and the tracked Bruno flow feature fixture. No mocked inference.
- Run the existing 44-check baseline first. Register/login one fresh account
  for this experiment; no stored tokens or secrets in receipts.
- Submit six batches, four clients per batch, with a barrier and rotated
  submission order. Every batch has PUBLIC/CLASSICAL, PUBLIC/HYBRID,
  RESTRICTED/PQC and incompatible RESTRICTED/CLASSICAL denial. All requests
  share the same 4096-byte synthetic payload and 100ms selection hint.
- Expect six requests per case: 18 verified envelopes, six HTTP422 denials,
  no HTTP429/5xx. For every batch require observed overlapping client request
  intervals. This does not prove parallel server execution.
- Verify successful response correlation, risk, profile, model version,
  cryptographic round-trip, 4112-byte ciphertext and 12-byte nonce. Denials
  must not return an envelope or record cryptographic work.
- After HTTP completion, allow up to20 seconds for all24 monitoring records.
  Query actual MySQL and require exactly one execution, policy decision and
  matching outcome/event per correlation. Compare owner, identities, model/
  policy versions, risk/score, selected mode, sensitivity, payload hash and
  successful response identities. Preserve synthetic rows; do not delete data.
- Submit no new batch after90 seconds. Each HTTP operation uses the existing
  20-second socket timeout and SQL subprocesses have10-second limits. These
  are not hard whole-operation limits against slow-drip peers. Retain partial
  results on failure; do not tune or silently retry failed scenarios.
- Use a new exclusive JSON receipt in the owned run directory. The stack runner
  stops only its own service trees in finally. Leave MySQL/unrelated apps alone.

Interpretation: client-observed timings include HTTP, policy, inference, crypto,
database and scheduling. Report the exact low-concurrency workload, all failures
and host conditions; do not extrapolate to production throughput or tail SLAs.
One MEDIUM input-flow fixture does not establish general attack detection,
cross-tenant isolation or LOW/HIGH input-model coverage. One run is not a
statistically powered performance comparison.
