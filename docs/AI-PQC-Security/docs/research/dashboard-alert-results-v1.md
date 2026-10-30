# Dashboard operational-alert integration — 2026-10-20

Implementation: `0f428bd`; exact-route/readiness correction: `ed695bb`. User
selected dashboard + email; recipient/provider and local email settings remain
pending. No email was configured, sent or verified.

## Implemented and tested

- Read-only Operational alerts section loads only after an explicit click.
  Prometheus pending/firing receipts and two producer outbox observations stay
  separate, with per-source retrieval/stale/unavailable states. Invalid shapes
  are unknown, not zero.403 clears privileged cached data;401 clears/signs out;
  unmount/session changes cancel pending requests. No fake email/replay controls.
- Monitoring exposes a bounded, administrator-only reader for the four known
  audit rules, selecting safe response fields. It rejects malformed/oversized
  upstream bodies and returns503/state unknown rather than healthy empty data.
- Exact Gateway GET route is added without widening event ingestion or unrelated
  subpaths. Compose uses its Prometheus service URL; native default remains9090.
- Frontend26 tests and production build passed. Eight new tests cover actual
  receipt rendering, expansion, partial failure/staleness, unknown initial data,
  permission/session loss, response validation and cancellation.
- Full Java reactor109 total:104 passed/five skipped. After the exact-route fix,
  the affected Gateway reactor was rerun:30 Gateway tests,28 passed/two skipped,
  including one new production-config route test. These are not claimed as a
  second full-root110-test run.
- Final real services/MySQL run passed44 checks and the bounded gateway burst.
- Real Prometheus probe through Gateway→Monitoring API preserved actual states:

| State | Direct engine observation(s) | Monitoring receipt through Gateway(s) |
|---|---:|---:|
|inactive|5.83|5.94|
|pending|12.18|12.21|
|firing|71.87|71.91|
|inactive after recovery|74.00|74.04|

Normal-user403 and stopped-source503/unknown were verified through Gateway.
The exporter metrics were synthetic and labelled as such, not real failed audit
events or detected attacks. All owned probe/service/preview processes stopped;
no project test ports remained. MySQL and unrelated applications were untouched.

## Actual browser check and limits

Using the local existing test account, sign-in loaded real personal records.
The navigation and Load operational alerts control produced administrator-access
required, without showing global source data. Sign-out returned to empty login
fields; the temporary test tab closed and viewport override reset. Narrow DOM
measurements were window433px, document scroll width416px, panel≈386.32px: no
horizontal overflow in that observed layout. This is not an exact390px claim.
Screenshot capture failed twice; no screenshot/pixel-perfect review is claimed.
Administrator firing/stale UI variants have automated rendering coverage, not
a real administrator browser-session claim. Broader visual/keyboard review stays
on the completion checklist. Sites' local-only workflow kept this work unpublished.

## Failures retained and corrected

1. `live-stack-5222b286caa44c409d49541db13ab9ca`: launcher checked AI health once
   before readiness and stopped its owned processes on refusal. AI now participates
   in the existing150-second readiness loop; UP still requires the real model.
2. `live-stack-237c5a3a1ce249c8a87006b974d9496b` passed44/burst checks but failed
   the new end-to-end route assertion. Gateway previously forwarded only exact
   events path. This was a route gap, not evidence of an authorization bypass.
3. The initial routing-test harness failed Spring's indexed-list binding when
   overriding only route3. It now loads all actual production route definitions
   and changes only the target URI. Rerun verifies exact GET forwarding and
   non-forwarding of POST/internal/unrelated paths. Logs retained.

## Local evidence

- Successful stack: `ml/artifacts/live-stack-acea1e4c45ea4b5a91c38413efc70652/`.
- Real engine/API: `ml/artifacts/alerts-3eeb8367f1c8445694f4adeaf7dbed25/`.
- Preview process/logs: `ml/artifacts/ui-alerts-842a7440ab7f4453a66d76df01358a06/`;
  screenshot unavailable, not fabricated.
- Maven logs: `dashboard-alert-reactor-20261020.log`,
  `dashboard-alert-gateway-regression-20261020.log`, and initial/rerun route logs
  under `ml/artifacts/`. No passwords/JWTs saved in JSON evidence.

SHA-256 fingerprints:

- Stack `verification.json`:
  `18c99ae200455784037ab3ff50ad8ed13685e5d09738ad769171785b6e46a2f3`
- Real-engine/API `verification.json`:
  `2cb3b6c84ca603e3172e139a18ebfb3030eea763ebda8a64655045f08fc35df5`

No model training/promotion or accuracy improvement. No production deployment,
external notification delivery, full browser visual verification or project
completion is claimed. Operational email setup remains a separate required step.
