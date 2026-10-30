# Phase 7 Container Architecture

The application profile in `docker-compose.yml` runs the complete distributed
security system on one Docker network:

1. MySQL initializes independent auth, business, monitoring, and policy schemas.
2. Eureka provides service discovery to the gateway and Java services.
3. The gateway is the only public backend entry point.
4. The AI service loads the locally promoted model through a read-only bind mount.
5. The policy engine calls AI inference, and the business service executes the
   selected classical, hybrid, or PQC profile.
6. Nginx serves the React build and proxies `/api` to the gateway.
7. Prometheus and Grafana observe the full flow without receiving application
   credentials or protected payloads.

Java and Python application images run as non-root users. Multi-stage builds
exclude compilers, source code, local datasets, model artifacts, and credentials
from runtime images. The model remains a separately promoted research artifact,
which allows retraining and rollback without rebuilding application code.

## Verified local flow

The complete profile was built and started on Docker Desktop. All five Eureka
clients registered, all seven Compose Prometheus targets were healthy, and the
repository Bruno suite passed all seven requests. The test created one user,
five normalized events, one adaptive policy decision, and one verified crypto
execution in the isolated container databases. Containers were stopped after
validation; the named database volume was retained for inspection.

Use `docker compose --profile app down -v` only when the isolated test data is
no longer needed, because `-v` permanently removes the Compose database volume.
