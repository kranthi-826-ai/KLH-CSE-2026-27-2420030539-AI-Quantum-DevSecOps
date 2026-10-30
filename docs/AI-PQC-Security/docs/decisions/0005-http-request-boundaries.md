# ADR 0005 — Shared JSON API request boundaries

Date: 2026-10-20. Scope: Gateway, Auth, Business, Monitoring and Policy Servlet
services. The Python inference service remains an internal dependency with its
own schema; Eureka management endpoints are not part of this filter.

## Decision

Introduce `platform/http-security`, auto-configured through its classpath
dependency. It registers one earliest-order filter for `/api/v1/*` on each of
the five services; this protects direct service calls as well as the gateway.
The gateway-specific correlation filter is replaced by this shared boundary.

- Missing/blank correlation IDs generate UUIDs. A single supplied nonblank ID
  must be 1–80 ASCII characters, begin alphanumeric and otherwise contain only
  alphanumeric, dot, underscore, colon or hyphen. Reject duplicate/invalid
  values with400 and a fresh UUID; never echo rejected input.
- Limit request bodies to262144 bytes, rejecting larger declared lengths before
  reading. Body-bearing methods are read through a bounded MAX+1 byte buffer,
  also rejecting oversized unknown-length/chunked input with413. Accepted body
  bytes remain available to downstream JSON parsing/proxying.
- Nonidentity Content-Encoding is unsupported and returns415, rather than
  letting compressed input bypass byte accounting. Error responses are no-store.
- Login identities are capped at50 characters, consistent with registration.
  Registration/login passwords must not exceed BCrypt's72 UTF-8-byte limit.
  This is a byte check, not merely a character count. Invalid authentication
  JSON/DTOs receive a generic400 without rejected values or passwords.

The body limit permits JSON escaping overhead around the existing65536-character
payload cap; unusually heavily escaped payloads can still hit the lower byte
boundary. This is intentional and should be stated to clients.

## Verification and operations

Shared unit tests cover bounded replay, exact byte/ID boundaries, missing IDs,
duplicates, unsafe characters, chunked/unknown lengths and unsupported encoding.
Real Gateway HTTP tests verify chunked and fixed-size413 responses before the
handler. Real Auth HTTP tests cover malformed JSON, long credentials, multibyte
password rejection and an accepted72-byte password. Live MySQL verification
also probes direct-service filter registration, not just a mocked gateway.

STS: import `platform/http-security/pom.xml` as an Existing Maven Project, then
update all Maven projects. The root reactor includes the module. Do not copy
library files into each service or disable security to resolve dependencies.

## Limits

This is blocking Servlet ingress, not a slow-client timeout, connection limit,
aggregate memory budget, reverse proxy, tenant quota or network-level flood
defence. Management endpoints are unchanged. Streaming/nonblocking request-body
APIs and compressed request bodies are not supported by this wrapper. Direct
service ports still require protected production ingress. Parser nesting/type
constraints, trusted telemetry, operational alerts, TLS and other PRD security
requirements remain separate acceptance gates.
