# Audit database recovery rehearsal

This is an isolated, synthetic recovery test, not a production backup service.
It checks real MySQL dump/restore behavior against current audit table structures
without copying real user records or overwriting application databases.

## Run safely

Keep `DB_PASSWORD` in the Git-ignored root `.env`; never put it in a command,
chat or committed file. The existing local MySQL 9.7 tools must be installed.
From the repository root run:

```powershell
.\ml\.venv\Scripts\python.exe -m unittest discover -s tests/live -p test_database_recovery_guards.py
.\ml\.venv\Scripts\python.exe tests/live/verify_database_recovery.py --output-directory ml/artifacts/NEW_UNIQUE_RECOVERY_RUN
```

The output directory must be a new immediate child of `ml/artifacts/`.
The runner reads only table definitions from the fixed live audit allowlist:

| Structure source | Table |
|---|---|
| pqc_auth_db | audit_outbox, audit_outbox_replay_log |
| pqc_monitoring_db | security_events |
| pqc_business_db | crypto_executions |

It creates two fresh `pqc_recovery_<32-hex-run-id>_source/restored` schemas.
No `IF NOT EXISTS` reuse, live row reads, user/account changes, live dump or
restore target is allowed by the rehearsal. Foreign-key/definer schemas are
unsupported and fail closed pending review. Plain InnoDB table structures are
cloned; all six records are labelled synthetic fixtures, not model predictions
or actual cryptographic executions.

The dump uses one transaction and disables added DROP/locking statements,
triggers and GTID state changes. The restore target is freshly created and
verified empty. A SHA256 checksum is checked before import; a deliberately
modified in-memory copy must be rejected without being imported. Then all
table definitions, deterministic data-only exports, counts, queue states,
occurrence precision and restored stable-event uniqueness are checked.
Credential environment and raw MySQL errors are not printed or saved; only a
sanitized numeric duplicate-error check is used. This uses the existing local
root account for the test, not a demonstrated least-privilege backup account.

## Retained evidence and cleanup

`verification.json` records schema names, checks, timing and checksums. The
ignored `synthetic-audit-backup.sql` contains fixture data only. Evidence and
test schemas remain after success or failure for inspection. No automatic
deletion is performed, no existing server is stopped and no background server
is started. Repeated runs create more fixtures; review the exact schema names
before authorizing a separate cleanup. Never substitute a wildcard or an
application schema in a DROP command.

## Remaining recovery requirements

This small test does **not** establish a full application restore, disaster
recovery or availability guarantee. Production work still needs a reviewed
backup/restore operator role; encrypted storage and independent key management;
off-host copies; scheduling, retention and restore monitoring; all application
tables and associated model/configuration provenance; application-level
post-restore acceptance; cross-service point-in-time consistency; and recovery
under actual disk/host failures. A checksum detects this measured corruption;
it does not authenticate a backup against someone who can replace both file and
manifest. No live backup deletion or restore is authorized by this runbook.

Measured results and retained failed attempt:
[audit recovery results](research/database-recovery-results-v1.md).
