# ADR 0007 — Read-only dashboard alert receipts and email direction

Date: 2026-10-20. User selected dashboard + email. Recipient/sending provider and
local SMTP credentials are still pending; no email has been sent or verified.

## Dashboard source contract

Add an explicit-load Operational alerts section. It requests three independent
administrator-only sources: actual Prometheus alert states through Monitoring,
and Auth/Business outbox observations. No privileged source is fetched merely
by opening the ordinary dashboard. No browser-selected upstream URL is accepted.

`GET /api/v1/events/operations/alerts` requires signed ROLE_ADMIN before querying
Prometheus. Monitoring uses a configured server-side Prometheus base URL, bounded
connect/read timeouts, a1MiB response limit and at most1000 source rows. The
receipt includes only the four known audit rules' safe label/annotation fields,
pending/firing state, source and retrieval time. Unknown rules are not forwarded.
Gateway adds only the exact GET alert path; it does not broaden the existing
events read route or expose the internal ingestion path. An actual HTTP routing
test loads production route definitions and replaces only the test target URI.
Unavailable, malformed or oversized source responses produce503/state unknown,
not a successful empty alert list. No arbitrary upstream labels/body/errors leak.

Outbox snapshots are observations, not proof that Prometheus has fired. Their
scrape intervals and hold conditions remain distinct from API retrieval time.
The UI preserves per-source successful snapshots after ordinary refresh failure
but marks them stale. Initial failure is unknown, not zero. Permission loss
clears retained privileged data;401 clears it and signs out. Pending requests are
aborted on unmount/session change. No synthetic production alerts or nonfunctional
email/replay buttons are added. Recovery stays an explicit administrator API.

## Verification plan

Frontend tests cover explicit loading, real receipt rendering, metadata expansion,
partial failures/staleness, initial unknown state, permission/session changes,
invalid response shapes and cancellation. Real HTTP tests cover authorization,
safe field selection and malformed/oversized source responses. Optional live
`-VerifyAlertEngine` points Monitoring at an owned loopback Prometheus probe and
checks actual pending/firing/recovery receipts through Gateway, not mock states.
Synthetic probe metrics remain explicitly labelled test-only.

## Deployment and email boundary

Default native Prometheus URL: `http://127.0.0.1:9090`; Compose uses
`http://prometheus:9090`. This is runtime configuration, not a caller-supplied
query parameter. Protect source/management ports and use appropriate deployment
TLS/access controls. The UI currently marks email setup and delivery as pending.
Do not imply that choosing the email channel configured it or delivered an alert.
Recipient/provider/credentials, transport, retries/deduplication and verified
delivery/acknowledgement remain work. Secrets belong in ignored local configuration,
never React bundles, Git, screenshots or chat.
