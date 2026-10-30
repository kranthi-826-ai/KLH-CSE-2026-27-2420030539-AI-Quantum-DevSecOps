# Adaptive failure disclosure boundary

Date:2026-10-20. Freeze implementation/verifier before the live dependency run.

Requirements:

- New failed execution audits must not persist arbitrary exception messages,
  dependency URLs,response bodies,provider details or exception-cause text.
- Known policy denials/validation failures use typed reasons with fixed reviewed
  public messages. In particular,the HIGH/CLASSICAL denial must stay explainable
  and remain fail-closed. Do not select weaker crypto to avoid an error.
- Public advice for dependency/crypto/argument failures returns reviewed/generic
  reasons rather than exception.getMessage(). Existing502/422 status semantics
  remain unchanged. Do not infer safety by regex-scrubbing arbitrary strings.
- Execution read DTOs redact unreviewed legacy errorDetail values,while leaving
  stored historical evidence unchanged. New writes use safe reasons. Preserved
  raw legacy data remains a separate database/retention privacy concern.

Verification:

1. Retain original failing disclosure test XML using only synthetic private
   markers. Exercise new audit writes and public advice. Preserve test failures.
2. Exercise every typed reason plus causes/legacy redaction. Real HTTP tests
   verify response status/body and an actual H2-backed legacy read. The injected
   HTTP provider/service failures are controlled fixtures,not real attacks.
3. Run full root Maven package,retain suite counts/skips and current receipts.
4. Run the actual local44-check baseline,then existing owned AI-down/restart and
   Policy-down/restart phases. For each failure require generic502,a failed
   execution without crypto/decision,generic reason in actual MySQL and matching
   safe errorDetail through the signed-user execution read API. Recoveries must
   execute verified PQC and have null errorDetail. Require matching outcome events.
5. Stop only owned service trees and verify project ports absent. Leave MySQL,
   unrelated applications and historical records alone.

This boundary does not sanitize every policy metadata field,application log,
database backup,other service/error category or pre-existing stored audit string.
It is not a complete privacy certification,availability SLA or accuracy result.
