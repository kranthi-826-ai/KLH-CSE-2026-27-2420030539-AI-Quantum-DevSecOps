# Compiled dashboard live/HTTP-fault acceptance

Date:2026-10-20. Frontend contract/source:c88aaa6. Test-only proxy/guard source:
64b2274. Backend binaries unchanged from the successful d17924f root package.
This review tests the built production assets,not the Vite development module.

## Healthy actual-service path

Started the actual loopback AI/Java/MySQL stack;44 baseline live checks passed.
Served current dist through Vite preview on127.0.0.1:5174 and signed in through
the real gateway with the earlier synthetic normal-user review account.
The validated dashboard loaded its three existing execution records,two verified
successes and one denied selection. A fresh export contained three executions
and six events for that account,with source freshness metadata. Displayed
execution rows were previously generated real fixtures,not new model trials.
Login events appear asynchronously and later snapshots contain more events.

Observed script URL:/assets/index-gcSXsW2G.js. Local built file SHA-256:
473b3fdd6030c26d8e2dd490b562e676e354d7c826734ae4b74a0cba3967c2aa.

## Test-only HTTP fault path

`tests/live/dashboard_fault_proxy.py` serves the same compiled dist at loopback
5175. Login and the two read sources are forwarded to the actual gateway.
Only an upstream200 for a reviewed read source can have its body deliberately
replaced by[null]. Gateway rejection codes are not replaced. This fixture is
never part of production deployment and does not grant administrator access.

Sequence with a separate browser-origin session:

1. Healthy mode:real gateway login and validated snapshot;three executions and
   seven events retrieved. No mock prediction or fabricated healthy record.
2. malformed-events:browser Refresh rejected the corrupted event body. Prior
   events became explicitly stale with their original retrieval time; executions
   refreshed independently. Error named the unexpected Security events response.
3. Real downloaded stale export:seven validated old events and three current
   executions;events freshness stale,runs freshness current. No null row included.
4. malformed-both:both prior snapshots became stale,without blanking/crashing
   the page or quietly accepting smaller data arrays.
5. Reload under malformed-both:with no in-memory saved snapshot,both sources
   became unavailable,execution count0 of0 and export disabled. No fabricated
   successful empty retrieval or verified count was enabled.
6. Anonymous read while malformed-both was active returned the actual gateway
   HTTP401 rather than an injected authorized list. Guard unit tests separately
   reject mutation for401/403/429/5xx and unreviewed paths/modes.
7. Healthy mode restored:Refresh recovered both sources,three executions,
   eight actual events,two verified protections and enabled export. Saved DOM
   and screenshot show the recovered data. No training/accuracy change occurred.

Twenty-six live-verifier/config unit tests passed,including the proxy guard test.
The frontend99-test/build result from c88aaa6 remains applicable;no production
frontend or backend code was changed for this acceptance exercise.

## Evidence and cleanup

Run:`ml/artifacts/live-stack-4b5e8ca3fac34ec9a464132a86357a53/`.
Saved DOM snapshots cover healthy,events-stale,both-stale,both-unavailable and
recovery states. Actual healthy/stale JSON downloads,screenshots,service logs,
owned-process records and cleanup are retained. Browser download originals were
left untouched. Both browser sessions signed out and viewport override reset.

| Receipt | SHA-256 |
|---|---|
| verification.json |76269aae58183998e998d23d7e7d76545f9580f6e8f90822ef94e0cf80a06b19|
| browser-contract-receipts.json |bd6d43151ffe15114565425a79d21645f648beaf07bb4d7b0e03d2a3a7e1dfa5|
| recovered-desktop.jpg |53c9cb963ae09e4a71717ef5bf14aa4a7a38a8cf0e4dc0ad9b76b69b82f2cabc|

The receipts manifest contains per-artifact hashes; saved-state/export assertions
were checked after capture. It does not convert injected responses into actual
backend failures. Runtime evidence is local/ignored and contains synthetic audit
identities,not customer data or saved credentials.

Stopped all seven owned AI/backend process trees,preview and test-only proxy;
OS check found zero project listeners on5174,5175,8080–8083,8090,8091,8761.
MySQL/unrelated applications stayed running. Synthetic users/audits remain.

## Limits and reproduction

Build dashboard,start isolated stack with KeepRunning,serve dist via preview,
and perform healthy sign-in/export first. For fault review,create an artifact-run
control file with mode healthy,start the test-only proxy with --control,then
change the explicit modes in the sequence above and use browser Refresh/Reload.
Never deploy this proxy. Review the fixed loopback ports before starting and
stop only recorded owned processes afterward.

The negative cases are real-browser/real-HTTP tests with deliberately replaced
authorized read bodies. They are not spontaneous production faults,malicious
traffic,admin permission revocation,load tests or detection accuracy results.
Operator provisioning/revocation,administrator visual review,real-browser
session-expiry races,full accessibility and hardened deployment remain open.
