# HTTP request-boundary verification — 2026-10-20

## Change and scope

Implemented ADR0005: shared `platform/http-security` filtering in five Java API
services, replacing the gateway-only correlation filter. Added correlation-ID
character/length/duplicate checks, a262144-byte body cap for body-bearing methods,
bounded chunked-body reads, unsupported-encoding rejection, sanitized Auth400
responses and a72 UTF-8-byte password limit consistent with BCrypt.

This guards input boundaries; it is not proof of complete schema validation,
network-level flood protection, trusted telemetry or production readiness.
See ADR0005 for blocking/streaming, timeout and deployment limitations.

## Verification

- Full Maven reactor:100 tests total,95 passed, five opt-in tests skipped,
  zero failures/errors. The skips remain skips, not passing tests.
- Seven shared unit tests cover header/body boundaries and downstream replay.
- Two new real Gateway HTTP tests cover fixed/chunked oversized requests,
  duplicates, invalid IDs and preserved normal body bytes.
- Two new real Auth HTTP tests cover malformed JSON, long identities/passwords,
  multibyte byte limits and an accepted72-byte registration password.
- The new shared module and service artifacts installed into local Maven.
- Actual local stack/MySQL:38 checks passed, including invalid-ID rejection on
  each of the five direct-service ports, accepted80-character ID, oversized
  JSON/login rejection and sanitized multibyte-password rejection.
- The bounded bot test passed again: ten401 then two429, exactly ten persisted
  failed-login events, no forwarded-header bypass.
- Monitoring outage, Auth restart durability, restored delivery, identical retry
  acceptance and conflicting-ID rejection all passed again.
- Live-verifier unit tests: four passed. No model or frontend source changed.
- Owned test services stopped; zero project listeners remained. MySQL retained.

Evidence directory:
`ml/artifacts/live-stack-683470ceae7e495abd11789e16ba0239/`.
Maven logs: `ml/artifacts/http-boundary-maven-20261020.log` and
`ml/artifacts/http-boundary-install-20261020.log`.
Test audit records retained; JSON evidence contains no passwords/tokens.

SHA-256 fingerprints:

- `verification.json`:
  `6656e1d9d161ceca5d74122916d7e2c3d9b34bbc8f7f2bda1198284bc64c8237`
- `gateway-burst-verification.json`:
  `dd706aeb1b9a32c7151e5ad7de222acbbfdad17b5dfff32185fd2fd8774abdc2`
- `outage-verification.json`:
  `4c0430df74f94ad4b5c066e2f34eb760f92d3e46da62695505c92c345f1d4732`

## Interpretation

These are functional boundary/reliability observations, not improved threat
detection accuracy or a comprehensive adversarial assessment. JSON nested value
constraints, operational alerting/replay, least-privilege DB, protected ingress,
TLS, independent model evaluation, performance acceptance and final paper remain
separate requirements. For STS, import the new Maven module as described in
`docs/decisions/0005-http-request-boundaries.md`.
