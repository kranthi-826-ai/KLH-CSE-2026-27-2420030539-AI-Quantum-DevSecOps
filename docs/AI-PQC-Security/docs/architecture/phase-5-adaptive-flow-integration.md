# Adaptive Security Flow Integration

The Business Service now exposes `POST /api/v1/business/adaptive-secure-data`.
An authenticated request supplies an application payload, the exact UNSW-NB15
network feature schema, data sensitivity, compatibility capabilities, and a
latency constraint.

The flow is:

1. The Business Service calls the Adaptive Policy Engine.
2. The policy engine calls the AI Security Service and records its decision.
3. The Business Service maps the returned algorithm profile to the crypto-agility layer.
4. It creates a signed encrypted envelope and verifies a round trip before returning it.
5. MySQL stores an execution audit in `pqc_business_db.crypto_executions`.
6. The Monitoring Service receives the successful API access event.

The execution audit never stores plaintext, private keys, shared secrets, or
ciphertext. It stores a SHA-256 payload fingerprint, model and policy versions,
risk and crypto selections, latency measurements, verification outcome, and a
bounded error description. The current server-generated ephemeral recipient
keys make this endpoint an integration and measurement proof. Production client
delivery requires the planned certificate and key-management boundary.
