# Detection and enforcement progress — 2026-10-19

The framework has distinct detection, enforcement, and cryptographic functions.
An attack score selects neither a reliable firewall rule nor a production-ready
blocking threshold without separate validation.

## Implemented request-rate enforcement

The gateway now has per-peer token buckets for `/api/v1/**`:

| Bucket | Burst capacity | Refill period |
|---|---:|---:|
| All API requests | 120 | 60 seconds |
| Login and registration, combined | 10 | 60 seconds |

These are configurable initial development settings, not measured production
capacity recommendations. A token bucket permits bursts; it is not a fixed
maximum number of requests in every rolling minute. Exhausted buckets return
HTTP 429 with `Retry-After` and `Cache-Control: no-store`, before forwarding.
Rejected requests retain the gateway correlation response header.

Client identity uses the connected peer address, not user-controlled forwarding
headers. When deployed behind a reverse proxy, peer-address behavior and shared
NAT users require an explicitly designed ingress/trusted-proxy configuration.
The default limits apply to the gateway process, not directly to each backend
port. Network policy/ingress must prevent backend bypass in a deployment.

Each limiter stores at most 10,000 peer buckets. When full, it reclaims idle
entries; if capacity is still unavailable, it returns HTTP 503 instead of growing
memory without bound. Counters distinguish rate-limit rejection from client-map
capacity exhaustion. These counters are visible through gateway monitoring;
rate-limit rejections are not yet persisted as security-event rows in MySQL.

Environment overrides:

- `RATE_LIMIT_API_CAPACITY`, `RATE_LIMIT_API_PERIOD_SECONDS`
- `RATE_LIMIT_AUTH_CAPACITY`, `RATE_LIMIT_AUTH_PERIOD_SECONDS`
- `RATE_LIMIT_MAX_CLIENTS`

The limiter is local to one instance. Multiple replicas need shared or edge
enforcement. It does not provide upstream network DDoS protection, distributed
credential-stuffing prevention, account-level lockout, or web-payload inspection.

## Enforced cryptographic minimum

Business Service checks that each returned policy decision has a nonempty ID,
the expected correlation ID, a finite score in [0,1], a known effective risk,
and an algorithm profile matching its selected mode.

The policy engine may still record compatibility fallback reasons, but Business
Service now refuses to execute a HIGH-risk CLASSICAL fallback. HIGH-risk
operations require the configured PQC or hybrid profile; otherwise they fail
before encryption with a controlled HTTP 422 response. This is intentional
stricter behavior for clients whose budget or capabilities previously allowed
a classical downgrade. LOW/MEDIUM selection semantics are unchanged.

The execution audit retains a structurally valid decision and rejection reason
when minimum protection is unavailable. Invalid decision identities/scores are
not recorded as successful cryptographic results. Dependency failure remains
a failed operation and cannot generate a successful protection response.

This enforcement does not classify high-risk data as malicious. Confidentiality
requirements can elevate risk for legitimate requests as well.

## Tests and remaining evidence

Tests exercise token refill, per-peer separation, spoofed forwarding headers,
bounded client memory, concurrent bursts, and management-path exclusion. A real
local HTTP test sends a three-request burst to a test-only gateway handler with
capacity two and verifies that only two requests reach the handler.

Business-service tests cover a verified hybrid round trip, high-risk downgrade
rejection with audit evidence, profile mismatch, correlation mismatch, invalid
score rejection, and dependency failure. Existing tests cover JWT identity,
invalid signatures and expiry, internal API keys, key establishment, signatures,
and altered envelope context/metadata rejection.

Verification completed: the full Maven reactor passed, followed by targeted
gateway, business and authentication runs after the HTTP tests were added.
The latest module reports total 49 Java tests with zero failures/errors; the
Python suite has 10 passing tests. The HTTP authentication test exercised
registration, bcrypt storage, duplicate registration, wrong-password rejection,
valid login, authenticated identity, and missing/invalid/expired JWT rejection
against an isolated H2 database. Only its outbound event publisher was stubbed.
Full MySQL-backed live deployment and packet-to-
feature microservice evaluation remain separate work. The 39 CICIoT2023 fields
must be extracted consistently before a trained model can score live traffic;
API request counts are not interchangeable with those network features.
