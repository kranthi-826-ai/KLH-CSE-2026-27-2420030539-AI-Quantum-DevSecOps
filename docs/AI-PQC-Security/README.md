# AI-PQC Security

**AI-Driven Adaptive Post-Quantum Cryptographic Security Framework for Distributed Applications**

This repository is organized for phased development. We are starting with the SOA microservices foundation; AI analysis, adaptive policies, post-quantum cryptography, Docker/Kubernetes deployment, and ML training will be added incrementally.

The project scope, approved architecture, research rules, roadmap, and definition of done are fixed in the [Product Requirements Document](docs/PRD.md). All new work must remain aligned with that document.

## Project structure

```text
AI-PQC-Security/
|-- backend/                 Spring Boot microservices
|   |-- discovery-server/
|   |-- api-gateway/
|   |-- auth-service/
|   |-- business-service/
|   `-- security-monitoring-service/
|-- frontend/                Client applications
|   `-- web-dashboard/       React dashboard (later)
|-- platform/                Adaptive AI and cryptographic-security modules
|   |-- ai-security-service/ Python UNSW-NB15 model inference API
|   |-- adaptive-policy-engine/ Java risk-to-crypto policy service
|   `-- crypto-agility/      Classical, hybrid, and PQC execution libraries
|-- ml/                      Data, training, evaluation, and model artifacts
|-- infrastructure/          Database, Docker, Kubernetes, and monitoring
|-- tests/                   Integration, end-to-end, and performance tests
|-- docs/                    Architecture, API, research, and decisions
`-- scripts/                 Setup, test, and demonstration scripts
```

## Technology direction

- Java 21, Spring Boot, Spring Cloud, Maven
- React dashboard (later)
- Python ML inference service (later)
- Docker Desktop, then Kubernetes (later)
- Bruno for API testing
- Free and open-source tools only

## Local environment variables

Configure these variables in each applicable STS run configuration. Do not commit their real values.

| Variable | Used by | Purpose |
|---|---|---|
| `DB_PASSWORD` | Auth, business, and monitoring services | Local MySQL password |
| `JWT_SECRET` | Auth, business, and monitoring services | Shared JWT signing/validation secret containing at least 32 characters |
| `MONITORING_API_KEY` | Auth, business, monitoring, AI, and policy services | Authenticates internal service APIs |
| `AI_SECURITY_SERVICE_URL` | Adaptive policy engine | AI inference service URL; defaults to `http://localhost:8090` |

## Implemented authentication flow

- User registration with BCrypt password hashing
- User login through the API Gateway
- Signed JWT access tokens containing username and role
- Stateless JWT validation for protected endpoints
- JSON `401 Unauthorized` responses for missing or invalid tokens
- Protected `GET /api/v1/auth/me` endpoint
- Unit tests for valid, invalid-signature, and expired JWTs

See [Auth Service API](docs/api/auth-service.md) for request examples.

## Implemented security-event flow

- Gateway-generated or client-preserved `X-Correlation-ID`
- JWT-protected Business Service endpoint
- Versioned normalized security-event contracts
- Authentication success/failure and business API access events
- Service-to-service event ingestion protected by an internal API key
- MySQL-backed event audit history
- JWT-protected event query API

See [Phase 2 APIs](docs/api/phase-2-security-events.md) for the end-to-end flow.

## Phase 3 research pipeline

The research matrix, controlled experiment protocol, official UNSW-NB15 data
validation, baseline training, evaluation evidence, and local MLflow tracking
are now scaffolded. Start with [the ML pipeline guide](ml/README.md). Accuracy
claims will be added only after the official dataset is validated and experiments
are executed.

## Phase 4 adaptive-security foundation

- The Python AI service loads the promoted UNSW-NB15 model and returns attack
  probability, risk level, explanation, and a hash-derived model version.
- The Java adaptive policy engine combines AI risk with data sensitivity,
  client compatibility, and latency constraints.
- Versioned deterministic rules select classical, hybrid, or post-quantum
  profiles and store the complete input, fallback reason, model version, and
  policy version in MySQL for research reproducibility.
- Internal prediction and policy APIs require `X-Internal-API-Key`.

The policy output is a decision and audit record whose profile name maps to the
Phase 5 execution library. See [Phase 4 APIs](docs/api/phase-4-risk-policy.md).

## Phase 5 cryptographic agility

The reusable Java crypto layer implements executable classical, hybrid, and
post-quantum profiles with authenticated secure envelopes and JMH benchmarks.
It uses Java 21 cryptography plus maintained Bouncy Castle implementations of
NIST ML-KEM-768 and ML-DSA-65. See the
[Phase 5 architecture](docs/architecture/phase-5-crypto-agility.md).

The authenticated Business Service now connects the complete execution path:
AI risk inference, adaptive policy selection, selected crypto execution,
round-trip verification, and a privacy-preserving MySQL execution audit. A
ready-to-run `Adaptive Secure Data` request is included in the Bruno collection.
See the [integration design](docs/architecture/phase-5-adaptive-flow-integration.md).

## Import into Spring Tools for Eclipse
`
## Phase 6 dashboard foundation

The React security dashboard in `frontend/web-dashboard` uses the authenticated
gateway APIs to display recent security events and adaptive crypto executions,
including AI risk, selected protection mode, verification outcome, and latency.
JWTs are kept in session storage and the development server proxies API calls to
the gateway without exposing internal service API keys.

Run `npm install` once and `npm run dev` from the dashboard directory after the
backend services are running.

Import the repository root with **File → Import → Maven → Existing Maven Projects**. The Spring projects are located under `backend/`. STS automatically creates its own local `.project`, `.classpath`, and `.settings` files; do not copy or commit those files.

After pulling file changes, use **Refresh** and **Maven → Update Project** in STS.
