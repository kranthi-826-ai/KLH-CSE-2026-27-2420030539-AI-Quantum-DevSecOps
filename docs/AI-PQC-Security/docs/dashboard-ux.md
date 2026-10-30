# Dashboard content and verification

The dashboard is the explanation and audit surface for adaptive security.
It uses authenticated API responses from `/api/v1/events` and
`/api/v1/business/executions`. It represents the returned records rather than
lifetime system totals. The executions API currently returns up to 100 records.

## Contents

1. Snapshot overview: observed events, failed/denied outcomes, execution count,
   verified round trips, and mean recorded execution time.
2. Protection distribution: recorded Classical, Hybrid, and PQC selections.
3. Service activity: services represented in audit evidence, without claiming
   current health from historical activity.
4. Decision journey: request, model score, effective policy risk, selected
   cryptographic profile, policy/model version, reason, and verification.
5. Timing breakdown: policy-service call, cryptographic work, and other recorded
   work. This is not claimed to measure full end-to-end response latency.
6. Searchable executions with an inspect action.
7. Searchable audit events with outcome and correlation filters.
8. Evidence export: JSON with snapshot time, source availability, execution
   records, and audit events. No session token is included.
9. Recorded activity chart: successful and other event outcomes across sixteen
   intervals spanning the returned timestamped events. Events without valid
   timestamps are excluded from the chart but retained in snapshot totals.
10. Protection intelligence: latest recorded decision, risk, model score,
    policy version, and a link to the full decision explanation.

## Console design

The dashboard and sign-in screen share a dark operations-console design with
emerald accents, restrained borders, compact numerical typography, and separate
colors for successful, denied, and failed outcomes. The workspace card identifies
the development environment. Cards and tables adapt to desktop and phone widths;
decorative animation remains disabled.

## Meaning of displayed results

- The model score is a prediction for a submitted flow, not evaluation accuracy
  or proof that an attack occurred.
- Effective policy risk can depend on sensitivity and compatibility as well as
  the model score. The saved policy reason explains each selection.
- A verified round trip is a seal/open check, not a production security audit.
- Encryption and request blocking are separate controls. Selecting PQC does not
  itself stop flooding, injection, or credential attacks.
- Dataset benchmark results need a versioned evidence API before they can become
  dashboard statistics. CICIoT2023 bounded final evaluation is recorded separately
  in `docs/research/ciciot2023-final-results.md`; its failed gates are not live
  dashboard accuracy or grounds for promoting another model.

## Interaction and layout

Navigation links target real sections and show the selected navigation item.
Filters, refresh, execution selection, related-event inspection, sign-out, and
evidence download have implemented actions. No decorative animations were added.
Mobile views retain decision details and audit fields. Keyboard focus remains
visible. Printing removes navigation and action controls.

If one evidence API fails, records from the other remain visible. The page
shows a partial-evidence warning. A 401 response clears the session and returns
to sign-in. Missing API data is displayed as unavailable rather than zero.

## Verification on 2026-10-19

- Production Vite build passed.
- Eight React interaction tests cover telemetry, partial API failure and exported
  JSON contents without the session token.
- Browser review of populated desktop and mobile layouts used clearly labeled
  synthetic fixtures. Those temporary fixture files were removed afterward.
- Mobile execution selection updated the displayed policy mode and risk.
- Local screenshots are stored under `ml/artifacts/ui-review/` and are UI
  verification evidence only, not research experiment results.
- Real authenticated backend-to-database testing was not performed in this UI
  iteration; it requires the project services to be running.

## Open the dashboard

Serve the frontend with Vite or the Docker/nginx deployment. Opening index.html
directly as a local file does not serve the JavaScript application correctly.
The development proxy forwards `/api` requests to the gateway on port 8080.

## Live verification and reliability updates — 2026-10-20

See `docs/live-verification.md` for21 actual API/MySQL checks and browser review
at phone width390. Freshness is recorded per source, retained records are marked
stale after failure, and export schema2 preserves both source times/statuses.
The top retrieval time is explicitly the latest source retrieval, not proof
that every record was refreshed. Requests time out after15seconds with retry.

Protection shares now include only successful, verified executions. Rejected or
unverified policy selections remain inspectable but do not count as protection
executed. Latest-policy cards explicitly distinguish selection from execution,
and failed execution details show the recorded rejection.18 frontend tests and
the production build pass. This does not close every accessibility/security or
production-deployment requirement.
