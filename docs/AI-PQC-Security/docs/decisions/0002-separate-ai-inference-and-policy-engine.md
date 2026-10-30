# ADR 0002: Separate AI inference from adaptive policy decisions

## Status

Accepted

## Decision

Run inference in a Python FastAPI service and deterministic policy rules in a
Java Spring Boot service. Persist each decision with the model version, policy
version, constraints, selected mode, and reason. Keep both APIs internal.

## Rationale

- Python loads the exact scikit-learn training artifact without conversion.
- Policy rules remain testable and auditable independently of the model.
- Model changes do not silently alter cryptographic policy semantics.
- Either model or policy version can later be rolled back independently.
- UNSW flows remain separate from project authentication and API events.

## Consequences

- Network evaluation depends on AI service availability.
- A direct decision endpoint supports controlled fallback and isolated testing.
- Phase 5 must implement and benchmark profiles before real crypto execution.
