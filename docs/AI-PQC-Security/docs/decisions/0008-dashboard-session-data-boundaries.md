# ADR0008 — Dashboard data after permission loss and session changes

Date:2026-10-20. Scope:main dashboard event/execution snapshots and login lifecycle.

## Issue

The operational-alert component already discarded privileged data on403.
The main evidence loader instead handled403 like503:previous records remained
visible and exportable as stale. Its batch waited for both requests before
handling401, allowing a slow peer to delay logout. Requests were not cancelled
on unmount, so a late old-session401 could call the App logout callback after a
new login. Login also trusted any successful response's token property.

## Decision

- Create a cancellation controller for each evidence refresh. Abort prior work
  before replacement; abort on dashboard unmount/token change. Ignore results
  from aborted requests even if a transport/mock does not honor cancellation.
- Handle401 as soon as either source rejects:abort the refresh and logout.
  Do not wait for the other source's request timeout.
- Handle403 immediately per source:clear its records and loaded flag, clear its
  previous successful timestamp, mark it forbidden, and remove derived selected
  execution/correlation state when execution access is denied. A slow peer must
  not postpone cache removal. Do not clear unrelated, still-authorized evidence.
- Keep ordinary outage behavior distinct:503/network failure can retain a
  previous snapshot, explicitly stale. A later403 is not a stale-cache fallback.
- Derive global latest-retrieval time/export eligibility from remaining source
  receipts. A denied source must not keep an otherwise empty export enabled.
  Export the forbidden source's empty array, false loaded flag and forbidden
  receipt, never its old records or the session token.
- Key the dashboard by session token so a replacement token cannot inherit a
  previous principal's component data. Login requests are cancellable; late
  responses after unmount cannot save a token. Accept only a bounded nonempty
  three-part base64url-shaped token before starting a session. This is structural
  validation, **not** signature/issuer/authorization validation; those remain
  the server's responsibility.

## Evidence and limits

All43 frontend tests and the production build passed. Twelve new cases in
`SessionBoundary.test.jsx` cover partial denial/export while a peer remains
unresolved,both-source denial,immediate401,logout cancellation,late old-session
401 after a new login,late login completion,and seven malformed token responses.
Existing stale-outage behavior,keyboard and operational-alert tests still pass.

These are component/network-fixture proofs,not a newly performed real-browser
permission-revocation or MySQL integration run. No server-side role-revocation
mechanism or JWT invalidation was added. The backend must actually reject access
before the client can observe it; offline copies and already downloaded exports
cannot be recalled. A user who legitimately retrieved data can retain it outside
the dashboard. No claim of DRM or complete confidentiality follows from this fix.
No live servers,external recipients,credentials or model artifacts were touched.
