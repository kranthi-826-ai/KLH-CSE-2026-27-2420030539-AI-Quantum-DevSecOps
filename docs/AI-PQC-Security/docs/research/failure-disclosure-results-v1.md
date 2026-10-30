# Failure disclosure verification results

Date:2026-10-20. Frozen implementation/live verifier/protocol:6be230e.
See failure-disclosure-protocol-v1.md for requirements and explicit limits.

## Changes and reproduction

The Business Service previously copied exception.getMessage() into failed
execution records and returned raw GeneralSecurityException/argument messages
through its public error advice. Five original tests failed using synthetic
private markers,internal-looking URLs and response-body text. No real secret
was used. The original five-failure XML is retained.

Known policy validation/denial failures now carry typed fixed reasons; generic
dependency,provider and argument failures map to fixed public messages. The
same disclosure mapping is used for new failed audit writes and public advice.
No regex/substring scrub is trusted to recognize safe arbitrary exceptions.

The execution-read DTO separately allowlists reviewed fixed stored reasons;
unreviewed legacy details become a generic failure message. Historical database
rows are not mutated. A legacy H2 fixture retained its synthetic private string
in storage while the actual authenticated HTTP read response omitted it.

## Tests

- Full root package exited zero:174 tests across52 fresh suites,169 passed,
  five skipped,zero failures/errors. Fresh report timestamps and XML hashes were
  checked. All26 live-verifier/config tests pass.
- New disclosure tests:19 unit/service invocations,including all13 typed reasons,
  exception causes,new failed-audit writes,legacy redaction and lookalike strings.
- Five real-HTTP/H2 tests verify dependency502,crypto/argument422,reviewed HIGH-risk
  denial wording and a database-backed legacy read. Service failure responses are
  controlled test injections; they are not real attacks or model evaluations.
- First targeted HTTP run had39/40 passing:the argument-error assertion wrongly
  required the word failed although the reviewed message says invalid. Retained
  that XML; replaced it with an exact expected-message assertion for each category.
  Sensitive-marker absence and HTTP status assertions were not removed.
- An initial optional PowerShell summary reused a typed XML variable and produced
  invalid zero totals. The original java-regression.json is retained as invalid;
  use java-regression-v2.json,which independently recounts52 fresh suites and
  explicitly identifies the superseded report. Maven's successful exit is separate.

## Actual local dependency phases

The rebuilt actual stack passed44 baseline checks,then all four owned phases:

| Phase | HTTP | Verified persistence/read behavior |
|---|---:|---|
| AI stopped |502|FAILED execution,no crypto/decision;generic reason in MySQL and signed-user read;matching FAILURE event|
| Real AI restarted |200|Verified PQC;SUCCESS execution/event;null failure reason in MySQL/read|
| Policy stopped,AI still UP |502|FAILED execution,no crypto/decision;generic reason in MySQL and signed-user read;matching FAILURE event|
| Real Policy restarted |200|Verified PQC;SUCCESS execution/event;null failure reason in MySQL/read|

Phase receipts passed11,8,12 and8 checks respectively. They use the real model,
crypto,MySQL and production application clients,not mocked healthy dependencies.
The existing fixed4KiB restricted request and ephemeral signing keys were used.
No full envelope,token or password was saved in phase receipts.

## Evidence

Run:ml/artifacts/live-stack-2a394869117344e49e432f2d0d262231/.

| Receipt | SHA-256 |
|---|---|
| verification.json |0880becea49918a8f280a4281d03ddc7bf0a833f77c8d33b156ec64069e21a73|
| dependency-ai-down.json |dc11f26ebcd30a87f8df255f63e1f2f358541da5ba215ab69e6fe04e532a0d52|
| dependency-ai-recovered.json |5067fca09cd2be197cf45e57e8340b4f24e377aaaa88b319228a11e1b6a67c6d|
| dependency-policy-down.json |7bb6b2a3404f6f4793eaff0ee08fd7e1cee0f5d768eaa5a578ba64bb83a76dfd|
| dependency-policy-recovered.json |5db044f6bea14bd61547441e4da9e9d41a1eb3db2e36db1768bbe3886249590a|
| java-regression-v2.json |a29ea8b3b2d691e0ac802a801b17442173839b12d5ff08a04580186e2ae0a085|
| cleanup.json |c5866955cb46580fe9049f56ba9244858aace35c28b3bd014c3b46f87fa08144|

Additional local artifacts:failure-disclosure-before-v1/FailureDisclosureTests.xml
(ccbf59b3bdfb2adee91348526a8e9f4a9699e610662660e4188b1b9d7b66525d),
failure-disclosure-http-first-v1/FailureDisclosureHttpTests.xml
(2713cc80d1a9dee26d8a25bf0bbcf5c1a0a13f12789b05e6640cd16d8ef326b0),
failure-disclosure-package-v1.log and its timestamp/exit receipt.

All owned service trees stopped;cleanup reached the end and an OS check found
no project listeners. MySQL/unrelated apps and historical rows were untouched.
No frontend/model changes,training,promotion or accuracy improvement occurred.

## Remaining limits

Legacy database strings still require an explicit retention/privacy decision;
redaction at the API is not retroactive storage sanitization. Other metadata,
logs,backups,services,error categories and arbitrary runtime/error conditions
were not globally sanitized by this change. Broader persistence-after-crypto
failure semantics,operator authorization/revocation,trusted telemetry,load and
deployment acceptance remain open. Passing these checks is not privacy/security
certification or proof that no disclosure path exists elsewhere.
