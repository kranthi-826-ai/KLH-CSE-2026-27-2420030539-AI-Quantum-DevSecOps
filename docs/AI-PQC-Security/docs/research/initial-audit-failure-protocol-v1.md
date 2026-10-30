# Initial audit write failure boundary

Date:2026-10-20. Freeze source before the normal live regression.

The initial STARTED write must be inside the operation's guarded failure/finally
boundary. If it throws,do not evaluate policy or execute crypto. Attempt one
sanitized FAILED audit/event transaction,then throw the original failure even
if that transaction succeeds. Never fabricate an encrypted success response.

If the failure write also throws,preserve the primary error and suppress a
distinct secondary error. Do not self-suppress the same exception instance.
Record one failed/unselected/unknown metric and increment the process-local
failure-audit-error metric only when the failure audit could not be saved.
When neither save commits,there is no durable execution/event to claim.

Three Spring/H2 tests inject initial-save exceptions through a writer spy:
fallback recovers,fallback continues failing,and the same exception is reused.
Verify no policy-client interaction,stored row/event facts,metrics and causes.
These controlled writer failures are not actual MySQL/disk outages. The byte
array finally block now covers the initial-save failure path;this is not a
guarantee that immutable request strings or every memory copy is erased.

Run full root packaging and the actual local44-check baseline to ensure normal
flows still work. Retain before/after test evidence and stop only owned services.
Distributed failure recovery,commit ambiguity,crashes and metric durability/
alerts remain separate requirements. No training or model improvement is claimed.
