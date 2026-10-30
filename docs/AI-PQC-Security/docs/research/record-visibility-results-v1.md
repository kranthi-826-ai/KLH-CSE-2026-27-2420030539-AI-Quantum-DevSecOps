# Record visibility verification — 2026-10-20

## Problem and implementation

Source inspection found that every authenticated account could retrieve the
latest global audit/execution rows. ADR 0004 now scopes ordinary-user repository
queries to the verified JWT subject before ordering/limiting. Only exact signed
ROLE_ADMIN authority receives the global latest-100 view. Unattributed events
are not included in personal views. Public registration remains ROLE_USER-only.

The dashboard now describes access-scoped snapshots and the per-source 100-row
limit rather than labelling these counts as complete system metrics. The Sites
local-only workflow was used; no website was published. This bounded text change
has automated rendering coverage, not a new responsive browser-review claim.

## Evidence

- Two actual HTTP/H2 permission tests passed: two users' isolation, empty third
  identity, anonymous rejection, ignored username/role query parameters and
  forged headers, signed administrator view, and unattributed event isolation.
- Affected services and their Maven dependency reactor: 39 tests, no failures,
  errors or skips. This count is not a rerun of every unrelated Java module.
- Frontend: all 18 tests passed, production build succeeded.
- Live verifier unit tests: four passed.
- Live MySQL run: all 29 API/database checks passed, including the original 21,
  personal-record scopes, attempted admin registration, second-user login,
  cross-user query resistance and short-lived signed operator view fixtures.
- The bounded gateway burst also passed after the permission changes: ten 401,
  then two 429; exactly ten failed-login events persisted in both stores.
- All test-owned servers stopped; zero project test listeners remained.

Local artifacts:
`ml/artifacts/live-stack-c9214773c1914651a5335e5ee98c3b03/`.
Maven transcript: `ml/artifacts/record-visibility-maven-20261020.log`.
No passwords or JWTs were saved in JSON evidence. Test records were retained.

SHA-256 fingerprints:

- `verification.json`:
  `cd700fe0a9ada28f0b9a6064da05da8d57a9ecdfa11b0e85c212b5c99d55cdb1`
- `gateway-burst-verification.json`:
  `2f90ecbca769d48b7f432abb481c83eeddc894731287c2af3fd7d064d36accad`

This is an authorization fix, not an ML-accuracy gain or comprehensive security
certification. Operator provisioning, token revocation, tenant-level permissions,
ingress/TLS and least-privilege database credentials remain separate work.
