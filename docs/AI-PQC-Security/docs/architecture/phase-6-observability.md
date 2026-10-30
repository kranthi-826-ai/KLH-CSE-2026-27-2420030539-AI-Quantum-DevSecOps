# Phase 6 Observability

## Purpose

The local observability stack measures availability, HTTP traffic, JVM resource
usage, AI inference traffic, and adaptive cryptographic outcomes without placing
credentials or protected payloads in metrics.

## Metrics

- Every Java service exposes Spring Boot health and Prometheus metrics.
- The AI Security Service exposes request count, latency, and risk-result counts.
- The Business Service records adaptive execution outcomes by risk and selected
  mode, plus an end-to-end execution-duration histogram.
- Usernames, JWTs, API keys, request payloads, ciphertext, and correlation IDs
  are intentionally excluded from metric labels to prevent sensitive leakage and
  unbounded label cardinality.

Prometheus uses separate target files for the two supported execution modes.
`prometheus.yml` discovers the full Compose stack by service name, while
`prometheus-local.yml` scrapes services launched from STS through
`host.docker.internal`. Grafana is provisioned with a read-only datasource and
the **AI-PQC Adaptive Security Overview** dashboard.

## Local operation

1. Set a strong `GRAFANA_ADMIN_PASSWORD` in the local `.env` file.
2. Start the application services.
3. Set `PROMETHEUS_CONFIG=./infrastructure/monitoring/prometheus-local.yml` in
   `.env`, then run `docker compose up -d`.
4. Open Prometheus at `http://localhost:9090` and Grafana at
   `http://localhost:3000`.
5. Stop the monitoring stack with `docker compose down` when finished.

Only `health`, `info`, and `prometheus` actuator endpoints are exposed. These
endpoints are not routed through the public API Gateway. Production deployment
must additionally restrict them using the Kubernetes network policy and TLS.
