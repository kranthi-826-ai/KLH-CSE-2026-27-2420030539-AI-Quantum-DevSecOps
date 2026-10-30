# ADR 0001: Synchronous Security Event Ingestion for Phase 2

## Status

Accepted for Phase 2.

Superseded on2026-10-20 by [ADR0003](0003-durable-audit-outbox.md) after live
testing exposed event loss during discovery/startup outages. The text below
records the historical Phase2 decision, not the current delivery guarantee.

## Context

The system needs normalized authentication and API security events before the AI and adaptive-policy phases. Introducing Kafka at the same time would increase local memory use and make event-contract debugging harder.

## Decision

Auth and Business publish normalized events to the Monitoring Service using a service-discovered Spring `RestClient`. The internal endpoint requires a shared API key and is not exposed by the API Gateway. Publishers fail open for the user request and log a warning if Monitoring is temporarily unavailable.

## Consequences

- The event schema and persistence flow can be tested immediately.
- The project remains lightweight on a 16 GB development laptop.
- Event delivery is best-effort and not durable while Monitoring is unavailable.
- A later infrastructure phase may add Kafka using the same versioned event contract.
