# Dashboard snapshot integrity boundary

Correction after post-crypto persistence testing:the original constraint below
that FAILED records cannot retain true verification was too strong. A real
Spring/H2 rollback test demonstrated a passed crypto check followed by a failed
completion transaction. Current code accepts that well-formed state,labels the
flow failed and excludes it from successful protection shares. STARTED/verified
remains invalid;strict boolean/type/identity checks are unchanged. See
post-crypto-audit-protocol-v1.md and post-crypto-audit-results-v1.md. The earlier
test results below describe the earlier contract,not this corrected assumption.

Date: 2026-10-20. Baseline8db4e78 accepted any array as a retrieved source,
without validating records. This change protects rendering and display/evidence
semantics; it does not authenticate records or improve intrusion detection.

## Reproduced defects

Both new before-tests failed. A null security-event element could crash the
dashboard during rendering. A non-boolean verification value such as the string
`"false"` could be treated as truthy in the overview verified count,even though
other protection-share code required a literal true. Reports were inconsistent.
The original failure receipt is retained,not overwritten.

## Current contract

`snapshot-contract.js` checks each source before state/freshness acceptance:

- Array of at most100 records,matching the actual Top100 API repository methods;
  non-null object records,unique bounded nonblank record identifiers.
- Explicit known event/execution fields only. Unreviewed extra fields are not
  accepted into a snapshot/export,including accidental credential-like fields.
- Event outcomes/required text and optional display text must have expected
  types/bounds. Missing or unparseable timestamp strings remain supported and
  render as Time unavailable rather than fabricated timestamps.
- Execution outcomes,boolean verification,finite numeric score in[0,1] and
  nonnegative safe-integer timings are required. Successful timing components
  cannot individually exceed recorded total. Numeric strings are not coerced.
- Decision-bearing records require a reviewed risk/mode; a supplied algorithm
  profile must match its mode. No-decision STARTED/FAILED records remain valid
  when unverified without selected risk/mode. Successful records require a
  decision; FAILED/STARTED records cannot claim a verified round trip.
- Optional absent provenance/profile text can still be represented as unavailable;
  this is not a claim that every displayed record has complete provenance.

A malformed source is rejected as a whole. It is not filtered into a smaller
apparently successful snapshot,which would silently change denominators. On a
first failure it is unavailable; after prior success the last valid snapshot
remains explicitly stale with its previous retrieval timestamp. Exports contain
that validated retained snapshot and provenance,not malformed new rows. If both
initial sources fail,no evidence export is enabled.401/403 clearing remains
distinct from ordinary malformed-source handling.

## Verification

- Final full frontend suite99 passed,zero failures; production build passed.
- Added44 contract-validation invocations and four App-level tests covering null
  records,string flags,stale retention/export and both-initial-sources failure.
- Boundary tests include primitives,nested/wrong-type fields,unknown profile,
  invalid scores/timings,duplicate IDs,mixed-invalid lists,101-row overflow,
  unreviewed secret-like fields,and valid empty/started/failed/success states.
- Checked the saved real browser export from the prior actual-service review:
  all three executions and six events satisfy the new contract. This is a
  persisted-real-data compatibility check,not a fresh live service/browser run.
- No backend/model changes,no training/promotion and no project servers started.

## Retained receipts

All paths below are under ignored `ml/artifacts/`.

| Artifact | SHA-256 |
|---|---|
| snapshot-boundary-before-v1.json |3ec99e931e015f9c8fbc2602421b84160cb8a2b030d91a09c8e0279cf29d607d|
| snapshot-boundary-after-v1.json |7e3806ba689f7af73c62a8add02e031fa794d5bfe93100be129d286a6d255bf0|
| snapshot-contract-full-v1.json |69ececbf8617948fcf545ba7f2020300b2a45b0a431c0a45ddf80ca6a3591502|
| snapshot-contract-full-v2.json |db11033c22f67a9a107a88ec398fa9e61ee3a9f2d71c258c9f77e8f6eb7a4347|
| live-stack-cc1be2352fbd471a9003d19bcc32a71e/browser-evidence-export.json |c606ff6f02e86aab1f500e304e161f36aaacd3d9df3303a0bce739bd2a7b8e37|

Source-schema changes require reviewing/updating this contract rather than
silently accepting new fields. This boundary does not prove absence of every
rendering failure,record authenticity,privacy correctness,all-model semantics,
complete accessibility,or production security. The protected existing backend
APIs and trusted telemetry requirements remain separate.
