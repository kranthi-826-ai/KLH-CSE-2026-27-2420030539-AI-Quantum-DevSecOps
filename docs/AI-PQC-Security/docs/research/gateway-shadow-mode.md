# Passive gateway observation and experimental scoring

Date: 2026-10-19. Implemented and tested; disabled by default. No model was
promoted, retrained, connected to policy, or allowed to change traffic decisions.

## Scope and flow

For synchronous `POST /api/v1/auth/login` and `GET /api/v1/auth/me` only:

1. The observer snapshots nine pre-request features, before the rate limiter.
2. Existing authentication/routing/rate-limit behavior runs unchanged.
3. A completed response updates historical counters for subsequent requests.
4. A bounded background queue writes a secret-free JSONL observation.
5. A **separate offline command** scores a completed file snapshot with the
   frozen HTTP-lab candidate. Scores are not sent back to the gateway.

This is capture plus offline shadow scoring, not a live inference/enforcement
service. Business, registration, health and unsupported routes are not scored
by this feature contract. Async/incomplete/exceptional responses are dropped
with a metric rather than inventing their final status.

The features follow the HTTP-lab contract: route indicators, bearer presence
(never the token or validity), completed request counts over 1/5 seconds,
earlier 401 and failed-login counts over 5 seconds, history presence and elapsed
time since the previous completed request's start. Current response outcome
is audit metadata, never a scoring input.

## Safety and privacy boundaries

- Histories use the servlet connection peer, not caller-provided session IDs
  or `X-Forwarded-For`. Spoofed forwarding/session headers were tested. Any
  future trusted-proxy/forward-header configuration needs its own identity audit.
- No request body is read. Passwords, bearer values, raw IP addresses, user
  names and caller correlation/session headers are not written. Peer IDs are
  random, local to an observer's in-memory lifetime, and not raw addresses.
- Defaults: at most 1,024 peers, 128 history events per peer, 256 queued records,
  five-second event windows and 60-second idle-peer eviction. Counter truncation
  at the event bound can underestimate high-volume history; this is not a
  production-calibrated traffic detector.
- Each output file stops at a conservative 10 MiB cap. No rotation or silent
  overwriting occurs. An explicit **new** filename is required when enabling.
- Request threads do not perform file I/O or wait for inference. Queue overflow,
  history-capacity exhaustion and stopped/failed writers drop observations, not
  requests. Shutdown flushing is best effort, with a bounded wait.
- Authentication and rate limiting still enforce their own decisions. This
  observer never replaces those controls or upgrades an alert into a block.

Metrics include `gateway_shadow_recorded_total`, `gateway_shadow_dropped_total`,
`gateway_shadow_history_capacity_dropped_total`, `gateway_shadow_incomplete_dropped_total`,
`gateway_shadow_writer_failures_total`, and `gateway_shadow_file_limit_total`.
Check these alongside assessments; missing records are not evidence of safe
traffic. New-file/open/configuration errors fail an explicitly enabled observer
at application startup; runtime telemetry drops do not reject requests.

## Verified experiment and interpretation

The real gateway HTTP test uses **test-only downstream handler fixtures**,
not a real routed Auth Service. It issued four login probes followed by an
identity-read probe, and observed statuses **401, 401, 401, 429, 200**. The 429
kept Retry-After. Forged forwarding/session headers did not reset peer identity.
Five observations were flushed without request bodies, tokens or IP addresses.

Offline scoring of the first successful snapshot produced four would-alerts;
the wrapper's independent repeat produced three. Timing-sensitive scores can
vary. These counts are **not attack-detection accuracy**, and no labels were
inferred from the response codes. In particular, the final allowed fixture was
also flagged in the first run: an alert did not alter its HTTP 200 response.

The model was trained with per-account harness histories, whereas the gateway
observes per-peer histories. Shared/NAT/proxy clients, sequential users and
concurrent traffic can therefore shift features and transfer prior failures
between users. This is a measured integration boundary, not proof that the
97.94% controlled HTTP-lab accuracy transfers to a gateway. Keep enforcement
disabled. Next, collect labelled **real Gateway-to-Auth-Service** sessions,
including shared peers and legitimate concurrent clients; align identity and
feature generation before training a new version and testing separate runs.

No CICIoT/UNSW reserved evaluation was opened or modified. Existing model
promotion is unchanged. No MySQL database or production service was needed.

## Reproduction and configuration

Run `./scripts/test-gateway-shadow.ps1` from PowerShell. This executes the real
gateway test with a unique output file, then offline scoring; it does not run
production services or enable shadow capture globally. The wrapper was executed
successfully end to end. It requires the prior frozen HTTP-lab study under
`ml/models/candidates/microservice-sessions-v1` (or `-ModelStudyPath`).

For an intentional local gateway run, configure:

- `GATEWAY_SHADOW_ENABLED=true`
- `GATEWAY_SHADOW_OUTPUT` to an absolute, new JSONL file under the project's
  ignored `ml/artifacts` directory. Reusing an existing file refuses startup.
- Optional `GATEWAY_SHADOW_MAX_PEERS` (1–4096) and
  `GATEWAY_SHADOW_MAX_EVENTS_PER_PEER` (1–512).

Disable again with `GATEWAY_SHADOW_ENABLED=false`. Stop/flush the producer before
scoring its snapshot with `ml/training/score_gateway_shadow.py`; the scorer
rejects malformed, duplicate-ID, non-finite, unknown-feature or over-10-MiB
input, changed model hashes, and existing output files. No new public scoring
endpoint or automatic response API was introduced.

## Evidence and tests

- `docs/research/evidence/gateway-shadow-v1.json`: the successful initial
  snapshot, repeat snapshot and their passive scores, with model/source hashes.
- Initial test setup failed because a route-list override lacked its required
  ID/URI. The test configuration was repaired; the empty failed artifact was
  preserved, and success used a fresh filename. No false success was reported.
- Python suite: 51 passed in 5.01 seconds. Tests prove outcome changes cannot
  change a score when pre-request features stay the same; invalid data and model
  tampering are rejected; scoring never reports accuracy or enables responses.
- Gateway tests: 18 passed, covering default-disabled beans, causal history,
  expiry/capacity/concurrent-completion behavior, preserved original exceptions,
  closed-writer telemetry drops, no overwrite, real HTTP 429 and unchanged 200.
- The file cap is an explicit writer invariant; disk-failure/high-load durability
  and independent production-client validation remain future operational tests.
- Final full Maven reactor: 57 tests passed, two opt-in collection tests skipped,
  zero failures/errors. Promoted model bytes still match the prior SHA-256.
