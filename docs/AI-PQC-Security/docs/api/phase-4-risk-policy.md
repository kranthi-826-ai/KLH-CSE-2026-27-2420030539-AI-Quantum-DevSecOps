# Phase 4 Risk and Policy APIs

Phase 4 adds two internal services. They are intentionally not routed through
the public API Gateway because inference and policy creation are
service-to-service operations.

## AI Security Service (`localhost:8090`)

- `GET /api/v1/ai/model` returns readiness, model identity, hash-derived
  version, and required feature count.
- `POST /api/v1/ai/predict` accepts the complete UNSW-NB15 network-flow feature
  object plus `correlation_id` and `source_service`.
- Missing or unknown model features receive `422 Unprocessable Entity`.
- Prediction requests require `X-Internal-API-Key` with the configured
  `MONITORING_API_KEY`; health and model metadata are readiness endpoints.

## Adaptive Policy Engine (`localhost:8091`)

All endpoints require `X-Internal-API-Key` with the configured
`MONITORING_API_KEY` value.

### Direct policy decision

`POST /api/v1/policies/decisions`

```json
{
  "riskLevel": "HIGH",
  "riskScore": 0.83,
  "dataSensitivity": "CONFIDENTIAL",
  "hybridSupported": true,
  "pqcSupported": true,
  "maxCryptoLatencyMillis": 25,
  "sourceService": "business-service",
  "correlationId": "request-correlation-id",
  "modelVersion": "model-hash",
  "riskExplanation": "Model probability and threshold explanation"
}
```

### End-to-end network evaluation

`POST /api/v1/policies/decisions/evaluate-network` accepts the complete network
feature object plus sensitivity and compatibility constraints. The policy
engine calls the AI service, applies policy `1.1.0`, stores the decision, and
returns the selected profile and reason. Its audit record includes the risk
explanation, sensitivity, compatibility flags, latency constraint, model
version, and policy version.

### Audit history

`GET /api/v1/policies/decisions` returns the latest 100 persisted decisions.

## Current boundary

The model makes real predictions only for UNSW-compatible network flows.
Authentication/API events have a different schema and are not falsely sent to
this model. The Phase 5 crypto-agility library now maps each selected profile
to executable providers; application-service wiring remains an integration step.
