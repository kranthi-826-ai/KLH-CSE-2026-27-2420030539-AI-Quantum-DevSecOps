# Local API/MySQL repeat verification — 2026-10-20

After the user saved the Git-ignored root `.env`, ran
`scripts/verify-local-stack.ps1 -VerifyOutage` without printing the password.
Missing development keys were generated in process memory by the runner.

Evidence directory: `ml/artifacts/live-stack-1f312f14f137426cbfdcdeeaedce7aab/`.

- All 21 existing live API/database assertions passed, including authentication,
  tampered-token rejection, verified Classical/Hybrid/PQC envelopes, execution
  persistence, audit retrieval and rejection of the prohibited downgrade.
- Monitoring was actually stopped, and the pending event survived an Auth
  process restart. Restoring Monitoring delivered the event.
- Identical event retry returned 200; conflicting content under the same ID
  returned 409. Exactly one row remained for this event ID.
- The runner exited successfully and stopped only its owned service processes.
  Test records were retained; no tokens/passwords were saved in JSON evidence.

Event ID: `91f71f66-d654-45c1-9abe-a2ea0fbdc231`.

SHA-256 evidence fingerprints:

- `verification.json`:
  `253b57bb0b8c27684ccb8184bd8f51e667ee350deb8d94aaa85e70d11c517901`
- `outage-verification.json`:
  `9c27317ecb0ac7e3da08898c4af465f09e0ff43b504bd4b170c5a9a0bde0efc4`

This repeats the scoped reliability experiment in
[audit-outage-recovery-v1.md](audit-outage-recovery-v1.md). It is not a model
training run, improved accuracy claim, bot/load test, frontend browser test or
production-security certification. Those acceptance areas remain separate.
