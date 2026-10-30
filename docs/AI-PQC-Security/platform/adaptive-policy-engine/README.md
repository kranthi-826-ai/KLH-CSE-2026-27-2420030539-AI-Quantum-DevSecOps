# Adaptive Policy Engine

Internal Spring Boot service that converts a versioned AI risk assessment and
application constraints into an explainable cryptographic policy decision.

Policy version `1.1.0`:

- low effective risk: classical
- medium effective risk: hybrid when compatible and within latency budget
- high effective risk: PQC when compatible and within latency budget
- confidential/restricted data elevates the effective risk
- every compatibility or performance fallback is explicitly recorded

All decision endpoints require `X-Internal-API-Key`, using the existing
`MONITORING_API_KEY` environment variable. Decisions are persisted to the local
MySQL schema `pqc_policy_db`.
