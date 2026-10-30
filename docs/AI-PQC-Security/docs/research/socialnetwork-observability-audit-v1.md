# Development exposure-label and observability audit

2026-10-20. Posthoc diagnostic of unchanged grouped out-of-fold base-logistic
predictions, not another trained model or independent evaluation. The auditor
checks frozen manifests, row order, study plan and binary predictions; every
positive annotation must overlap its one-second window. It does not open raw
archives, remove difficult rows, relabel observations or change thresholds.

## Findings

- Same 40/51 exposure hits and 3/506 matched-control alarms as before.
- Alerts in at least one exposure window in 15/16 observed recordings. This
  does not replace failed window-level recall, nor establish 93.75% accuracy.
- CVE-2022-0492 accounts for nine of eleven missed windows. Collection 1 has
  two hits in six exposure windows; collection 2 has zero hits in five windows.
- The nine missed windows for that CVE have zero observed current or prior-five-
  second execve/execveat counts. Several overlap a full second, so excluding
  only boundary windows would not solve the problem. Other syscall activity
  is present; absence of process execution does not mean absence of attack.
- The two remaining misses are CVE-2017-16939 (collection 1, 982.62 ms overlap)
  and CVE-2017-7308 (collection 1, 88.79 ms overlap). Both recordings have other
  detected exposure windows. All missed observations are retained.

The script also reports first alerted window-close time relative to annotation
start. This is a feature-availability delay calculated from saved windows, not
measured online inference/transport latency. For CVE-2022-0492 collection 1 it
is 5842.43 ms; collection 2 has no detected window, so delay is null, not zero.

## Interpretation and next experiment boundary

An annotation describes injection/exposure, not confirmed exploit success in
every second. Selected same-pod pre-injection controls are not a representative
production false-positive denominator. Both recording and window diagnostics
remain development-only and correlated. Do not select a different denominator
or drop the difficult CVE to produce a higher headline score.

Before more feature search, inspect the publisher's attack logs and permitted
development-only runtime context for this CVE, retaining all original labels.
Declare any added post-injection observation horizon and benign controls before
scoring it. Compare matched baselines and keep independent scenarios reserved.
No new detector is eligible for promotion based on this audit.

## Reproduction

```powershell
.\ml\.venv\Scripts\python.exe ml/training/audit_socialnetwork_observability.py ml/data/processed/socialnetwork-temporal-development-v1 ml/data/processed/socialnetwork-expanded-development-v1/windows.json ml/models/candidates/socialnetwork-temporal-supervised-v1/report.json ml/artifacts/socialnetwork-observability-audit-v1.json
```

Output creation is exclusive; an existing result is never overwritten. Full
local report SHA-256:
`5bf76e6cbb58e356cdf5e97a4ede580e2b69de6dd8e7dfc90bf469f583eecffa`.
Tests cover distinct recording/window counts, missed-detection null delay,
boundary overlap, row alignment, duplicate observations and invalid labels.
Full ML suite: 105 passed. Promoted UNSW model checksum remains
`c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.
