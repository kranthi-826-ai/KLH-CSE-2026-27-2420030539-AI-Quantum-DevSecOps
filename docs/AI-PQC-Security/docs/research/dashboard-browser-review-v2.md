# Authenticated dashboard browser review

Date: 2026-10-20. Application backend: d17924f packaged binaries. Frontend:
dabb12b baseline plus the empty-search guidance change recorded with this report.
This is a bounded real-browser review, not complete UI/accessibility acceptance.

## Actual workflow and observations

- Started the real loopback stack; existing44 API/MySQL baseline checks passed.
  Started the current Vite dashboard on127.0.0.1:5174. No mock API responses.
- Created one fresh normal-user fixture and three actual adaptive requests:
  PUBLIC/HYBRID success, RESTRICTED/PQC success and incompatible RESTRICTED
  denial. Registration/login and the three outcomes were checked before UI use.
- Signed in through the visible form using that fixture account. Dashboard
  showed three execution records,two completed verified round trips and one
  failed execution. Protection shares excluded the denied CLASSICAL selection.
  The denial view explicitly said selection was not proof of executed protection.
- At1280px desktop,390px mobile and320px narrow mobile widths, inspected DOM
  document width and observed no horizontal document overflow. Narrow execution
  rows retained mobile labels. Saved screenshots include real data/states.
- Required empty sign-in fields blocked submission and focused username.
  Dashboard section navigation focused its labelled target. Keyboard Enter
  activated decision navigation; Inspect selected the correct real execution;
  Related events showed its one matching correlation; clearing restored six
  snapshot events. Correlation linkage is not claimed as proof of causality.
- Searching executions for an absent term showed0 of3. Found misleading helper
  text asking for new traffic instead of clearing a search. Changed execution
  and event empty-filter guidance; genuine no-record states retain appropriate
  data-generation instructions. Browser reload verified the new message.
- A normal-user Operational Alerts load showed Administrator access required,
  not a fabricated healthy/empty privileged snapshot. Admin access was not granted
  and no admin fixture or permission change was used for this browser review.
- Download evidence JSON created a real file. Read-back confirmed schemaVersion2,
  three executions,six events and only the fixture owner,with source retrieval
  metadata. Copy retained in the run; browser's downloaded file remains untouched.
- Keyboard sign-out returned focus to username and removed the authenticated
  table. The temporary viewport override was reset.

## Regression and retained evidence

Frontend44 tests passed across seven files; production Vite build passed.
One new event-filter recovery test was added; the existing execution-filter
test now asserts the corrected hint. No backend/model change or retraining.

Artifacts: `ml/artifacts/live-stack-cc1be2352fbd471a9003d19bcc32a71e/`:
`verification.json`, `desktop-overview.jpg`, `desktop-decision.jpg`,
`mobile-signin.jpg`, `mobile-decision.jpg`, `authenticated-dom.txt`,
`browser-evidence-export.json`, `processes.json`, `ui-cleanup.json`, service logs.
DOM/screenshots/export contain synthetic fixture identities and real saved
outcomes,not customer data. They are ignored local evidence,not bundled UI data.

All seven owned backend/AI trees were stopped after review; the owned Vite
session was interrupted. OS check found no project listeners including5174.
MySQL and unrelated applications were left running. Fixture users/audits remain.
An initial cleanup comparison safely refused because PowerShell parsed recorded
timestamps as DateTime rather than strings; actual executable paths and matching
UTC start instants were inspected before termination. No process identity check
was bypassed and no unrelated process was terminated.

## Still not proven

No full WCAG conformance,screen-reader/contrast audit,administrator visual review,
permission-loss browser race injection,all-device coverage,real provider email,
production hosting or trustworthy live traffic ingestion is claimed. Automated
permission/session tests remain distinct from these real normal-user observations.
The UI is an evidence viewer; it does not itself establish service health,
calibrated attack probability,full-history totals or universal attack prevention.
