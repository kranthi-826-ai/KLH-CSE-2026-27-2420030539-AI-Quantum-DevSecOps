# AI/policy failure and recovery protocol

Freeze before the live outage experiment. This extends the adaptive scenario contract with
actual owned dependency process outages and separate accepted-but-silent socket
tests. It is not a complete fault-tolerance, DDoS or availability evaluation.

Business→Policy and Policy→AI clients now explicitly use2s connection and5s read
inactivity timeouts. These are per-I/O bounds, not a whole-request/SLA deadline
or protection against every slow-drip/connection-exhaustion pattern. Real silent
loopback-server Java tests must show SocketTimeoutException near the5s read
bound; Policy wraps its failure as502 rather than fabricating a prediction.

After normal44-check live verification, stop only the owned AI process tree and
confirm8090 has no listener. With an ephemeral signed ROLE_USER fixture, submit
the fixed4KiB restricted adaptive request. Require502,generic error,no envelope,
no successful verification,no policy decision,no selected/executed crypto,and
a FAILED execution plus matching Monitoring FAILURE event. The fixture bypasses
normal login issuance using this isolated run's temporary signing key; ordinary
login is already verified by the preceding suite. No token is saved.

Restart the owned AI with the same real promoted model and temporary internal
key; require UP and a fresh verified PQC execution with SUCCESS audit/event.
Then stop only owned Policy,confirm8091 is unreachable while AI remains UP,
repeat the failure checks,and restart Policy for another verified PQC recovery.
Each phase retains a unique receipt with correlation/IDs/counts/timing,not
credentials or encrypted payloads. The scripts use ordinary MySQL/HTTP services,
no mock inference,disabled protections or modified model.

Run `scripts/verify-local-stack.ps1 -VerifyDependencyFailures` after packaging the
current JARs. Parent readiness/restart checks are bounded; all owned process
trees stop on normal completion/error unless explicitly KeepRunning. Existing
MySQL and unrelated apps are not stopped. Synthetic rows remain for inspection.
Retain failures without overwriting. Database unavailability,partial network
partitions,slow-drip bodies,distributed recovery and full transport hardening
remain separate requirements.
