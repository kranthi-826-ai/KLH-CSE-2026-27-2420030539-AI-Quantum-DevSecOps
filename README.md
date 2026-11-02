# AI Enabled DevSecOps Framework for Adaptive Quantum Resilient Software Systems

## Project overview

This project is a working research prototype that connects AI-assisted threat-risk estimation, adaptive cryptographic policies and auditable security execution in a distributed microservice application. It provides a dashboard through which users can demonstrate protected requests, understand why a protection mode was selected, and inspect recorded outcomes.

In simple terms: **authenticate the user, estimate risk, choose an acceptable cryptographic profile, execute protection, verify the result and record the evidence.**

The framework supports research into quantum-resilient software migration. It is not a claim of perfect security, a replacement for all cybersecurity controls, or a production-certified product.

## Team

| Member | Role |
| --- | --- |
| Yellanki Kranthi Giri Venkata Chary | Student |
| Morampudi Girish Venkat Sai | Student |
| Alla Sai Harsha | Student |
| Billa Venkateshewara Laxmana | Student |
| Velthuru Vinisha | Project Guide |

Department of Computer Science and Engineering, Koneru Lakshmaiah Education Foundation, Bowrampet, Hyderabad-500043, Telangana, India.

## Problem addressed

Distributed applications expose multiple APIs and depend on communication between services. Security requirements vary with the estimated threat, sensitivity of the data, compatibility of the application and performance constraints. Meanwhile, quantum computing threatens established public-key cryptographic techniques.

This project investigates an integrated approach rather than using the same cryptographic profile for every request. Importantly, selecting stronger cryptography does not itself stop DDoS, brute-force attempts or malicious application behavior. Authentication, authorization, traffic controls and operational defenses remain necessary.

## What the application is

- A web dashboard for users and project demonstrations.
- API-connected services that perform authentication, business operations, risk assessment, policy decisions and monitoring.
- Reusable cryptographic libraries that execute classical, hybrid and post-quantum profiles.
- MySQL audit storage and containerized operational monitoring.

It is not a browser extension, antivirus application or universal shield automatically protecting every application on the laptop. Other applications would need an explicit, authenticated integration with the framework.

## Architecture and component responsibilities

| Component | Responsibility | Default local port |
| --- | --- | --- |
| React dashboard | Displays decisions, executions, security events and outcomes | 8088 in Docker |
| API Gateway | Public API entry point and request routing | 8080 |
| Auth Service | Registration, BCrypt password hashing and JWT login | 8081 |
| Business Service | Protected operations and adaptive crypto execution | 8082 |
| Security Monitoring Service | Receives and exposes persisted security events | 8083 |
| AI Security Service | Model inference and network-risk estimation | 8090 |
| Adaptive Policy Engine | Combines risk and constraints into a versioned decision | 8091 |
| Eureka Discovery Server | Service registration and discovery | 8761 |
| MySQL | Service-owned users, decisions, executions and audit events | 3307 in Docker |
| Prometheus | Collects configured operational metrics | 9090 |
| Grafana | Operational metric visualization | 3000 |

Crypto-agility modules are Java libraries, not additional standalone microservices. The frontend development server may use a different port from the Docker deployment.

## End-to-end workflow

```text
User -> Dashboard -> API Gateway
                         |
                         +-> Auth Service -> JWT
                         |
                         +-> Business Service: validate protected request
                                  |
                                  +-> Policy Engine -> AI risk inference
                                  |        |
                                  |        +-> Sensitivity + capabilities + latency hint
                                  |                 |
                                  |                 +-> Versioned mode decision
                                  |
                                  +-> Execution safety check
                                           |
                                  +--------+---------+
                                  |                  |
                              Accept              Refuse unsafe
                                  |                downgrade
                              Crypto library         |
                                  |                  |
                              Round-trip verification
                                  |                  |
                                  +--------+---------+
                                           |
                                  MySQL audit + security events
                                           |
                                      Dashboard
```

1. A user registers and signs in; successful login returns a signed JWT.
2. The user submits an authenticated adaptive business request containing a payload and compatible network features.
3. The AI service estimates network risk using the retained model.
4. The policy service combines this estimate with data sensitivity, supported crypto modes and a latency hint.
5. The Business Service checks whether execution is acceptable. An unsafe high-risk classical downgrade is refused.
6. For an accepted decision, the crypto library protects the payload and verifies a local round trip.
7. The system persists execution identifiers, selected profile, versions, timing and outcome; security events support traceability.
8. The dashboard exposes the result and decision explanation.

The current demonstration accepts supplied network features. This is not equivalent to automatically collecting trustworthy live network telemetry from every request.

## Inputs and outputs

| Input | Meaning |
| --- | --- |
| JWT | Authenticates the requesting user |
| Data payload | Content used in the cryptographic demonstration |
| Network features | Model-compatible measurements used for risk estimation |
| Data sensitivity | PUBLIC, INTERNAL, CONFIDENTIAL or RESTRICTED |
| Capability flags | Whether hybrid and PQC modes are supported |
| Maximum crypto latency hint | Policy selection constraint; not a guaranteed execution deadline |

Outputs include risk score and level, decision and execution identifiers, selected mode, algorithm profile, policy/model versions, encrypted-envelope fields, verification outcome and execution timing. A refusal is an unsuccessful protection attempt, not an executed secure mode.

## Cryptographic profiles

| Mode | Key establishment | Payload protection | Digital signature |
| --- | --- | --- | --- |
| Classical | X25519 | AES-256-GCM | ECDSA P-256 |
| Hybrid | X-Wing: X25519 combined with ML-KEM-768 | AES-256-GCM | ML-DSA-65 |
| Post-quantum | ML-KEM-768 | AES-256-GCM | ML-DSA-65 |

AES-256-GCM is common because it performs efficient authenticated payload encryption. The modes change key establishment and signature mechanisms. ML-KEM is a key-encapsulation mechanism, not a bulk-payload encryption algorithm.

These are local cryptographic execution and round-trip demonstrations. They do not establish authenticated end-to-end PQC transport between remote services or production-grade key management.

## How adaptive selection works

The current deterministic policy version is `1.1.0`:

- PUBLIC and INTERNAL retain the estimated risk level.
- CONFIDENTIAL elevates risk by one level; RESTRICTED forces HIGH risk.
- LOW effective risk selects classical protection.
- MEDIUM selects hybrid when supported and the latency hint is at least 8 ms; otherwise it selects classical.
- HIGH prefers PQC when supported and the hint is at least 15 ms, then hybrid when supported and the hint is at least 8 ms.
- If HIGH risk cannot satisfy either option, the policy records a classical fallback, but the Business Service refuses that unsafe downgrade instead of executing it.

These thresholds are policy eligibility hints, not measured algorithm runtimes or service-level guarantees. The AI estimates risk; explicit policy and enforcement logic decide what is permitted.

## AI, datasets and evaluation

The retained deployed network-risk model is a Random Forest. Training and evaluation work also investigates XGBoost candidates, difficult attack classes and false alarms.

| Dataset | Research purpose |
| --- | --- |
| UNSW-NB15 (2015) | Existing network-feature pipeline and retained inference model |
| CICIoT2023 | Additional network-attack experiments, including difficult attack families |
| 2024 microservice dataset / SocialNetwork data | Microservice-specific experiments and generalization investigation |

These sources have different feature schemas and experimental protocols. They must not be described as one jointly trained deployed model without a verified compatible pipeline. A dataset's age or published accuracy does not establish the accuracy of this application.

Evaluate accuracy, precision, attack recall, macro-F1 and false-positive rate together. Keep calibration/validation separate from final testing, retain rejected candidates and document split boundaries. Do not claim 99% accuracy, unseen-attack guarantees or superiority over papers using incomparable test conditions.

## Database design

MySQL uses separate service schemas:

| Schema | Main responsibility |
| --- | --- |
| `pqc_auth_db` | Registered identities and password hashes |
| `pqc_policy_db` | Versioned adaptive decisions and their audit context |
| `pqc_business_db` | Cryptographic execution records and timings |
| `pqc_monitoring_db` | Normalized security-event history |

Correlation, decision and execution identifiers connect evidence across service boundaries. Passwords must be hashed, credentials must stay outside Git, and raw sensitive payloads should not be treated as ordinary audit data.

## DevSecOps practices

- Version-controlled implementation and reproducible configuration examples.
- Unit, integration, API and database-backed verification.
- Docker Compose service deployment and bounded local resource settings.
- JWT validation and internal-service API authentication.
- Prometheus/Grafana operational monitoring and security-event audit history.
- Recorded ML experiments, model versions and promotion gates.

These practices support DevSecOps; they do not prove a fully automated hosted delivery pipeline, vulnerability-free dependencies or automatic production retraining.

## API demonstration

| Method | Gateway path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Register a user |
| POST | `/api/v1/auth/login` | Obtain a JWT |
| GET | `/api/v1/auth/me` | Confirm authenticated identity |
| GET | `/api/v1/business/secure-data` | Demonstrate protected access |
| POST | `/api/v1/business/adaptive-secure-data` | Execute the adaptive-security flow |
| GET | `/api/v1/events` | Inspect authorized security-event history |

Protected endpoints require appropriate credentials. Use the Bruno collection under `tests/e2e/bruno/` for existing request examples; never place real passwords or JWTs in presentation slides.

## Existing verification evidence

The recorded local Docker run dated **30 October 2026** started 11 containers and passed 44 API/MySQL checks. Additional checks recorded successful demonstration executions for all three modes, frontend-proxied authentication, Grafana database health and seven healthy Prometheus targets.

Evidence files:

- [API and database receipt](ml/artifacts/docker-runtime-20261030/verification.json)
- [Frontend proxy and monitoring receipt](ml/artifacts/docker-runtime-20261030/web-monitoring.json)
- [Runtime instructions and caveats](docs/docker-local-runtime.md)

These are historical functional receipts, not a statement that services are currently running or a measure of ML accuracy. That run did not establish interactive browser visual validation. Five npm dependency advisories remained for separate review; external email delivery was unconfigured/unverified.

## Run the existing local Docker setup

Prerequisites: Docker Desktop running, prepared local private runtime files, built images and the required retained model artifact. This command is for the existing laptop setup, not a fresh-clone installer:

```powershell
cd C:\Users\ykran\Desktop\AI-PQC-Security
docker compose -p ai-pqc-security --env-file .runtime/docker-stack.env -f docker-compose.yml -f .runtime/docker-local.override.yml --profile app up -d --no-build
```

Open the dashboard at <http://127.0.0.1:8088/> after services are ready. Private demo credentials, if generated, are in `.runtime/docker-login.json`; do not share that file.

Stop the stack without deleting database volumes:

```powershell
docker compose -p ai-pqc-security --env-file .runtime/docker-stack.env -f docker-compose.yml -f .runtime/docker-local.override.yml --profile app stop
```

Do not use `down -v` for routine stopping. The development run uses a separate named MySQL volume and preserves the earlier database volume; see the runtime guide before changing database configuration.

## Output screenshots for the presentation

Folder: `output/gamma-fullscreen/`

| Screenshot | What to explain |
| --- | --- |
| `01-secure-login.jpg` | Authentication entry point |
| `02-live-dashboard-overview.jpg` | Main security dashboard |
| `03-crypto-executions.jpg` | Recorded execution outcomes |
| `04-pqc-decision-journey.jpg` | PQC selection and explanation |
| `05-hybrid-decision-journey.jpg` | Hybrid selection and explanation |
| `06-classical-decision-journey.jpg` | Classical selection and explanation |
| `07-unsafe-downgrade-rejected.jpg` | Refusal of an unsafe downgrade |
| `08-security-event-timeline.jpg` | Traceable security events |

[Full-screen screenshot ZIP](output/AI-PQC-Fullscreen-Screenshots.zip). These are recorded demonstration images, not evidence that a new run occurred today. Crop only irrelevant surroundings, keep results readable and remove credentials before external sharing.

## Repository organization

```text
backend/         Gateway, discovery, authentication, business and monitoring
frontend/        React web dashboard
platform/        AI inference, policy engine and crypto-agility libraries
ml/              Dataset preparation, training, evaluation and experiment evidence
infrastructure/  Database initialization, containers and monitoring configuration
tests/           Automated and manual API/integration checks
scripts/         Setup, verification and demonstration helpers
docs/            Architecture, API guides, research and team documentation
output/          Presentation screenshots and generated deliverables
```

## Recommended presentation demonstration

1. Explain the problem and architecture before opening the dashboard.
2. Sign in and show the authenticated identity.
3. Run prepared classical, hybrid and PQC cases; explain the policy inputs rather than promising a particular mode for every attack name.
4. Show a successful verification and its matching MySQL record.
5. Show an unauthorized request and an unsafe downgrade being refused.
6. Show security events and explain correlation-based traceability.
7. End with measured evidence, limitations and next steps.

## Remaining research and engineering work

Improve difficult-attack detection while reducing false positives; validate trustworthy live microservice telemetry; perform controlled authorized bot/traffic tests; strengthen service identity and key lifecycle management; complete email-alert validation; review dependency advisories; and evaluate deployment scalability and cost.

**Presentation summary:** This project demonstrates how AI-assisted risk estimates can inform constrained cryptographic decisions, with explicit enforcement and auditable execution in a containerized microservice application.
