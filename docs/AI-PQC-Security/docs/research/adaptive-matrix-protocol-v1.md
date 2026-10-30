# Frozen live adaptive scenario protocol

Freeze before running. This is functional scenario/audit evidence, not a model
accuracy benchmark or a static-versus-adaptive performance claim.

The frozen16-case manifest is in `tests/live/verify_adaptive_matrix.py`.
Each case runs twice sequentially using the same4096-byte synthetic payload
and the tracked Bruno flow features. The current promoted model hash is pinned;
this demonstration flow must produce MEDIUM input risk. No dataset test labels
or test-set tuning are involved. A changed model requires a reviewed new protocol.

Cases cover PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED sensitivity, PQC/hybrid/both/
neither compatibility, and selection thresholds0/7/8/14/15/100ms. Expectations
are frozen from policy1.1.0 and the Business Service high-risk downgrade guard:
24 successful cryptographic round trips and eight422 fail-closed outcomes.
The same model score must persist across cases; sensitivity changes effective
policy risk, not model predictions. This set does not cover LOW/HIGH input-risk
flows or every possible feature/input combination.

Every case checks the actual Gateway response, direct MySQL execution and policy
audits, model/policy versions and stable IDs. Successful envelopes must have a
verified round trip and expected ciphertext/nonce sizes; denials must not return
an encrypted payload or a successful execution. All32 correlations and expected
24SUCCESS/eightFAILURE events must reach the actual Monitoring database.

The runner creates a new synthetic test user with an in-memory password/token.
No credentials or full envelopes are persisted in receipts. Existing records
are not deleted. It makes32 sequential adaptive calls plus registration/login,
uses a90-second scenario deadline, and records client wall time and saved crypto
time without inventing request-tail statistics. It neither disables the gateway
limiter nor substitutes mock inference. The parent owns and stops all seven
temporary loopback services, leaving existing MySQL and unrelated apps alone.

Run `scripts/verify-local-stack.ps1 -VerifyPolicyMatrix` after packaging current
JARs. This also runs the ordinary live API/database checks. Keep failures in their
unique artifact directories; never change expectations just to produce a pass.

The configured maxCryptoLatencyMillis is a policy **selection threshold**, not
a hard execution deadline. Count successful operations whose measured crypto
time exceeds it and report that limitation. Client-supplied flow features and
sensitivity remain demonstration inputs, not trusted live attack telemetry or
server-authoritative data classification. Mode selection alone cannot block
bots, prove detection accuracy, guarantee latency or establish production security.
