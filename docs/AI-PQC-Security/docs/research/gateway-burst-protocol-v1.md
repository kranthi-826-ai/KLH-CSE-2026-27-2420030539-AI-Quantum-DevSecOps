# Bounded gateway burst protocol v1

Declare before execution: twelve sequential synthetic failed logins to literal
`127.0.0.1:8080` from bound loopback peer `127.0.0.44`. No configurable external
target, parallel flood, real account or real password. Every request rotates
untrusted `Forwarded` and `X-Forwarded-For` values from the documentation range.

Run `scripts/verify-local-stack.ps1 -VerifyBot`. Standard live checks precede
the burst and ensure routing is ready. Default authentication token bucket has
ten tokens, replenished over sixty seconds. The verifier allows 5.5 seconds to
send the burst and rejects durations at or above six seconds as inconclusive.
Expected statuses: ten 401 responses, then two 429 responses. Both 429 responses
must preserve correlation, specify positive Retry-After, and prohibit caching.

Direct MySQL checks require exactly ten LOGIN_FAILED producer-outbox rows for
the unique synthetic username and ten matching Monitoring rows within a bounded
30-second delivery wait. The two blocked calls must not enter Auth. Passwords
and response bodies are not stored; test audit records are retained. Evidence
uses exclusive file creation and retains failures. The runner stops its owned
processes by default, even on failure.

This validates one local gateway's burst control and resistance to forwarded-IP
spoofing, not distributed rate limiting, upstream DDoS resistance, ML detection,
PQC attack prevention, sustained throughput, recovery timing, or bot attribution.
Rate-limit rejections currently have gateway counters, not durable MySQL audit
events; the ten stored events are failed authentications, not blocked requests.
