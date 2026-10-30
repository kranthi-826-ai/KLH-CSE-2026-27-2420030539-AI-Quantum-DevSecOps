# Post-crypto audit completion semantics

Date:2026-10-20. Freeze source before the normal live regression.
Crypto verification and whole-request completion are distinct facts.

| Situation | Returned result | Durable execution/event evidence |
|---|---|---|
| Crypto and completion transaction succeed | Verified envelope | SUCCESS,true verification;success event |
| Crypto succeeds,completion transaction fails,failure transaction succeeds | Exception,no envelope | FAILED,true verification retained;failure event |
| Crypto succeeds,both completion and failure transactions fail | Original exception,no envelope | Prior STARTED row remains;crypto result unknown in storage;no invented event |

For the last two cases,record exactly one failed-flow metric with known mode/
risk when available. When the failure audit itself cannot be committed,increment
adaptive_security_failure_audit_errors_total and retain the secondary exception
as suppressed context rather than replace the original failure. This metric is
process-local evidence,not a durable recovery queue or proof after a restart.

The dashboard must accept a well-formed FAILED/verified record,display crypto
verified but flow failed,and exclude it from successful protection shares and
successful-flow timing averages. Do not erase a real passed check to manufacture
an unverified record. Conversely,STARTED without durable completion must say no
profile/timing recorded,not that cryptography definitely never ran.

Tests use real Spring transactions,H2 persistence,outbox code and actual crypto,
with controlled exceptions injected at outbox enqueue. Check rollback,committed
outcome/event,original/suppressed causes,no returned envelope and metrics.
This is not an actual MySQL/disk outage at the crypto-completion instant.

Run full root packaging and frontend tests/build. Then run the existing actual
44-check baseline and32-case matrix unchanged in scenario content,confirm normal
verified requests/denials and matching MySQL audits still work. Stop owned service
trees afterward. No model training or accuracy measurement is part of this work.

Initial STARTED-write failures,concurrent DB ambiguity/crash recovery,memory
zeroization guarantees,metric alert wiring,live browser display of this injected
state and real MySQL/disk-failure acceptance remain separate requirements.
