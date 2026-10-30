# Gateway burst acceptance result — 2026-10-20

Protocol and verifier were committed as `a0927ad` before execution. Run:
`scripts/verify-local-stack.ps1 -VerifyBot`.

Evidence: `ml/artifacts/live-stack-5e41f77492ce49b1a3045d1a5e4f0b8a/`.
The existing 21 live API/MySQL checks passed before the burst.
SHA-256 of `gateway-burst-verification.json`:
`f6e6ef085942f866b465bc15e62d4ad166d5cbf154aa518230553ad16dcbb36a`.

| Assertion | Observed |
|---|---|
| Hard request cap | 12 local synthetic logins |
| First ten requests | 401, invalid synthetic credentials |
| Requests eleven and twelve | 429, before Auth handling |
| Rotating Forwarded/X-Forwarded-For | No bypass with the same connected peer |
| Both rate-limit responses | Retry-After: 6, Cache-Control: no-store, matching correlation |
| Burst time | 0.169 seconds, below the six-second refill interval |
| Auth outbox / Monitoring rows | 10 / 10 for the unique synthetic username |
| Burst verifier total time | 2.3284 seconds, including persistence checks |
| Cleanup | Owned service processes stopped; MySQL left running |

Four verifier unit tests passed, including rejection of a bypass response,
missing response safety headers and a burst exceeding the refill interval.
No model was trained or promoted. Raw response bodies and credentials were not
saved. Synthetic failed-login audit records remain for reproducibility.

This proves the measured single-instance local burst control, not distributed
bot attribution, sustained high-load throughput, upstream DDoS mitigation or ML
detection accuracy. Rate-limit rejections themselves are not durable audit
events yet; the stored rows represent the ten admitted failed authentications.
The test does not exercise token recovery or shared state across gateway nodes.
