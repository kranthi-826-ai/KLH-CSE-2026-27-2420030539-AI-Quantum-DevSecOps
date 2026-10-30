# Local full-stack verification — 2026-10-20

The local MySQL password was supplied through the Git-ignored root `.env`.
It was not printed, placed in command arguments, exported or committed. Missing
JWT/internal-service keys were generated for this run only and inherited by the
child services. Services bound to loopback, not the public network.

## Reproduce

Build current JARs with Maven first, then run:

```powershell
.\scripts\verify-local-stack.ps1
```

This checks free project ports, starts seven bounded-memory processes, waits
for listener/model readiness and routed event delivery, runs the live checks,
and stops only the processes it started. MySQL remains running. Raw logs and
exclusive verification JSON go into a unique ignored `ml/artifacts/live-stack-*`
directory. No Docker or security-setting changes are needed.

`-KeepRunning` retains a successfully verified stack for browser review. On
failure it still cleans up. Stop a retained run using its exact printed folder:

```powershell
.\scripts\stop-local-stack.ps1 -RunDirectory '<exact run directory>'
```

The stop helper checks directory scope, known service names, process start time
and command line before stopping anything. It refuses reused/unrelated PIDs.

## Measured live result

Successful run: `live-stack-0b5a76f2877d453dadb47dc4acdcbeae`.
Verification JSON SHA-256:
`7424542516489e7f576f03c50cd878bf3821ba71e2678a71d91e25875daa0c3e`.
All 21 checks passed: direct SQL connectivity; anonymous business/events rejection;
gateway registration/login; wrong password and tampered JWT rejection; identity;
real event delivery; all three crypto profiles and direct SQL execution rows;
high-risk classical downgrade rejection; dashboard execution/event APIs; SQL
event records; BCrypt storage; policy internal-key enforcement.

| Executed mode | Policy call ms | Crypto ms | Recorded total ms | Observed HTTP ms |
|---|---:|---:|---:|---:|
| PQC |281|48|411|546.571|
| Hybrid |80|41|127|161.399|
| Classical |82|9|98|146.893|

These are three demonstration requests, not a performance benchmark, capacity
claim or ML test. All use the existing promoted UNSW model and a Bruno fixture;
no new model was trained or promoted. Test accounts/rows from the runs remain
for audit evidence, including partial failed runs; original records were not
deleted. Reports do not store tokens or passwords.

## Browser verification against real services

Signed in using the existing local demonstration account. The page retrieved
real events and executions. At phone width390, document width375 did not exceed
the viewport; navigation intentionally scrolls horizontally. Selecting the PQC
execution changed the decision journey and displayed the actual profile,
versions and verification. Related-event filtering returned its correlated
event. JSON download included per-source provenance and no token property.

Stopped only this run's Monitoring process, then refreshed: event records were
marked stale with their original retrieval time, while executions received a
new successful retrieval time. Sign-out returned to login. All seven owned
backend processes and the owned Vite preview were subsequently stopped; MySQL
was left running. Local screenshots (not benchmark results):

- `ml/artifacts/ui-review-20261020/mobile-live-decision.png`
- `ml/artifacts/ui-review-20261020/mobile-live-stale-source.png`

The UI now excludes failed/unverified selections from protection shares,
labels policy-selected modes separately from executed protection, and shows
the execution rejection reason. API calls have a15-second deadline and permit
retry rather than remaining indefinitely busy. Frontend18 tests/build pass;
ML plus inference110 tests pass. Java regression results are recorded in the
completion checklist after the reactor finishes.

## Failures retained and remaining gaps

1. Early no-instance exceptions escaped functional gateway routing as generic
   500 responses. `DependencyFailureFilter` now maps discovery/transport
   unavailability to503, preserving correlation and avoiding internal detail
   leakage; four new tests cover expected and unrelated/committed errors.
2. MySQL BIT output required explicit unsigned casting in the test comparison.
   This was a verifier representation error, not missing execution persistence.
3. Early audit events were dropped while publisher discovery caches lacked
   Monitoring. The successful flow waits for observed event delivery, but this
   did NOT fix durable delivery during startup/outages in this initial run.
   This gap was subsequently addressed and tested by ADR0003 and
   `docs/research/audit-outage-recovery-v1.md`; preserve the initial failure as
   historical evidence rather than treating this earlier run as an outage test.
4. Root DB access, ddl-auto update and plain local HTTP are development settings,
   not a hardened deployment. Least-privilege credentials, migrations, TLS/
   ingress and production secret handling remain acceptance work.
5. Model quality, independent microservice evaluation, broader system load,
   free-hosting feasibility and the final paper are not completed by these checks.
   A subsequent bounded gateway burst passed separately; see
   `docs/research/gateway-burst-results-v1.md` for its narrow scope and limitations.
