# Phase 2 Business and Security Event APIs

All client-facing requests use the API Gateway at `http://localhost:8080`.

## Runtime requirements

Start services in this order:

1. Discovery Server
2. Security Monitoring Service
3. Auth Service
4. Business Service
5. API Gateway

Use identical `JWT_SECRET` values for Auth, Business, and Monitoring. Use identical `MONITORING_API_KEY` values for Auth, Business, and Monitoring. The three database-backed services also require `DB_PASSWORD`.

## Protected business endpoint

`GET /api/v1/business/secure-data`

```text
Authorization: Bearer <login-token>
```

A successful response includes the authenticated username, role, and gateway correlation ID. The Business Service publishes an `API_ACCESS_GRANTED` event. Missing or invalid JWTs receive `401 Unauthorized` and produce an `API_ACCESS_DENIED` event when Monitoring is available.

## Security event query

`GET /api/v1/events`

```text
Authorization: Bearer <login-token>
```

Returns the latest 100 events in descending timestamp order. Events include type, outcome, source service, username, correlation ID, request metadata, source IP, and detail.

## Internal ingestion

`POST /api/v1/events/internal` is not routed through the API Gateway. Auth and Business call it directly through Eureka/LoadBalancer and provide `X-Internal-API-Key`. The Monitoring Service rejects a missing or incorrect key.

## Event types

- `USER_REGISTERED`
- `REGISTRATION_REJECTED`
- `LOGIN_SUCCEEDED`
- `LOGIN_FAILED`
- `API_ACCESS_GRANTED`
- `API_ACCESS_DENIED`

Kafka is intentionally deferred. Phase 2 uses synchronous service-discovered HTTP ingestion to keep local resource usage low and establish the event contract before asynchronous infrastructure is introduced.
