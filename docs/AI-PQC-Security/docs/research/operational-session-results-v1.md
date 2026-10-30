# Operational-panel session/access boundaries

Date: 2026-10-20. Baseline source:05fabca. This change is frontend session
hardening,not a model experiment or new live backend/admin-browser acceptance.

## Defect and implementation

The operational panel previously waited for Promise.allSettled across all three
privileged sources before reacting to401/403. A retained privileged snapshot
could therefore remain visible while another source was slow. Main-dashboard
source revocation was already handled separately; that did not cover this panel.

The per-source catch now handles the first current-request401/403 immediately:
abort remaining peers,clear all retained operational snapshots and release the
loading state.401 invokes sign-out;403 locks the privileged panel while personal
records remain available. Aborted/obsolete responses cannot apply later results.
A completed old request cannot clear the new request's controller reference.
Ordinary source failures still use the existing explicit stale/unknown behavior.

## Reproduction and regression evidence

Initial four new controlled-timing component tests:one passed,three failed
against the unchanged implementation. Specifically,immediate403 clearing,
immediate401 sign-out and retry after403 were delayed by unresolved peers.
The existing old-session replacement guard passed and was not removed.

The first fixed-code targeted run passed10/12 tests. Its two remaining failures
were over-broad test assertions requiring the already-completed denial request's
own fetch signal to be aborted. api-client detaches that completed request's
external cancellation listener in finally. Corrected assertions require both
still-pending peer signals to be aborted and verify exactly six fetch calls;
data clearing,immediate handling and no-repopulation assertions were retained.
Both failing reports remain available; neither was overwritten or called passing.

Expanded coverage now includes seven new tests:

- Immediate403 clearing while two peers ignore cancellation.
- Immediate401 sign-out and peer cancellation without waiting for either peer.
- Old-session401 and403 ignored after token replacement and a successful new load.
- Fresh load after403 cannot be overwritten by old successes.
- Complete App-level401 removes session/table and focuses sign-in.
- Complete App-level403 retains personal dashboard access while clearing the
  privileged view,including late ignored peer completions.

Final full frontend suite:51 tests passed,zero failed/pending; production Vite
build passed. The prior44 tests remain passing. No backend/model code changed,
no training/promotion occurred and no project servers were started this turn.

## Retained local receipts

| Artifact under ml/artifacts | SHA-256 |
|---|---|
| operational-session-before-v1.json |d142684c380620a1b6b11131e48a7e0d54353c1ad4c239cad1e7a0c43672a7a6|
| operational-session-after-v1.json |7d64dec844f32f290bb87b8b6b1821a64b5adf405e3851024ab371e1913b9f19|
| operational-session-after-v2.json |3a1a2a250b7e90a3320c49f3b3a2a410c16bb1e517062b4ee320d0ef862f3a62|
| frontend-operational-session-full-v1.json |2fd8c3722540419396df63ab472ef60fd54241611b2d5ccf3e89744ddd8baf8e|

Tests use synthetic data and controlled mocked HTTP completion timing,including
peers deliberately ignoring abort. They prove these component/App transitions,
not a real-browser permission revocation race or administrator visual review.
Production server authorization remains authoritative. No universal race-free,
complete security or WCAG conformance claim is made.
