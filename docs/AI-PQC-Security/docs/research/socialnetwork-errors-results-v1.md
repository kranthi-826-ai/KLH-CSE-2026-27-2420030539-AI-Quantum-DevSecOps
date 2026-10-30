# Generic syscall-error ablation and development observability

Date2026-10-20. This bounded experiment did not produce an eligible improved
model. The promoted network model and all enforcement settings are unchanged.

## Matched experiment

Protocol/code committed1465988, with runtime metadata committed9d18e1f before
model scoring. Same557 observations,51 exposure windows,506 selected controls,
16 recordings and eight CVE groups as the previous study. Both recordings of a
held-out CVE remain together. No independent scenario or CICIoT final test is read.

The29 base feature values and sample order reproduce exactly. Add50 generic
reported-error features for79 inputs. Only leading result/descriptor fields
on syscall exits are eligible; no paths, commands, CVE names, roles, timestamps,
identities or future activity enter the model. The same three fixed recipes,
seed20261020 and threshold0.5 are used. All three baseline metrics reproduce
the previous study. Runtime: NumPy2.5.3, scikit-learn1.9.1, XGBoost3.4.1,
joblib1.6.0; full Python version is in the frozen local plan.

| Model | Inputs | Exposure hits/51 | Control alarms/506 | Macro-F1 |
|---|---:|---:|---:|---:|
| Logistic baseline |29|40 (78.43%)|3 (0.593%)|0.918669|
| Logistic + errors |79|39 (76.47%)|2 (0.395%)|0.917064|
| RF baseline |29|36 (70.59%)|0 observed|0.906490|
| RF + errors |79|36 (70.59%)|0 observed|0.906490|
| XGBoost baseline |29|35 (68.63%)|0 observed|0.899195|
| XGBoost + errors |79|35 (68.63%)|0 observed|0.899195|

Logistic removes two earlier control alarms, adds one new control alarm and
loses one detected exposure window (CVE-2016-5195/collection2). It does not
resolve the hard CVE-2022-0492 recording. Lower alarms alone do not count as an
overall improvement. No candidate meets >=95% exposure recall, <=5% selected-
control alarms and macro-F1 at least the earlier base-logistic result. No winner
is fitted/saved or promoted. Zero observed alarms is not proof of zero risk.

These correlated, repeatedly used development observations and selected controls
do not support deployment-wide FPR, an independent generalization claim, or a
headline accuracy from the artificial class ratio. This is a development-informed
ablation, not an independently preregistered confirmatory result.

## Difficult-recording context audit

Audited bounded prefixes of only the four previously exposed worker traces for
CVE-2022-0492.8,714,386 prefix events were scanned. Raw arguments were not saved.
Observe50seconds of pre-control context, the annotated interval, and10seconds
afterward. A separately versioned diagnostic also includes the unlabelled ten
seconds just before injection. These extra periods were NOT labelled as attacks,
used in training or included in an accuracy calculation.

| Target-pod observation during annotated interval | Collection1 | Collection2 |
|---|---:|---:|
| Events |4155|1554|
| execve entry calls |12|0|
| mount entry calls |1|0|
| Argument mentions of cgroup |80|0|
| Argument mentions of release_agent |6|0|

The first recording's execve/mount entries are concentrated in the cached
window1701185306, late in its annotated interval. Earlier exposure windows
have none of those entries. The second recording has no observed execve/mount
entry on either worker during the annotated interval, the unlabelled pre-onset
gap or the audited post-context. The target pod is present in its trace.

This does NOT prove that exploitation failed or that labels should be changed.
Interval annotations do not certify malicious behaviour in each second; capture
loss and other observability limits are not ruled out. Furthermore other
containers have1394/1194 cgroup text mentions in the two pre-control intervals:
substring presence is not an attack label. No cgroup/path signature is added to ML.

## Exact-feature ambiguity

A read-only collision audit finds three cross-label feature groups containing
22 rows (three positive,19 control) for BOTH the29- and79-feature representations.
Identical vectors have different exposure labels. A deterministic classifier
using only these inputs cannot distinguish every row in those groups. This
does not prove that98% is impossible or that the underlying events are mislabeled.
No row is deleted, majority-relabeled or excluded from the unchanged metrics.
The audit rejects missing/nonnumeric/nonfinite inputs instead of silently
converting them to zero. The stricter rerun preserves exactly the same counts;
both local audit checkpoints remain available.

## Reproduction and evidence

- Context: `ml/data/audit_socialnetwork_cve_context.py`; use a fresh output folder,
  optionally `--include-onset-gap`. Outputs v1/v2 remain preserved.
- Features/cache: `socialnetwork_error_features.py`, `prepare_socialnetwork_errors.py`.
- Scoring: `ml/training/study_socialnetwork_errors.py`.
- Data quality: `ml/data/audit_socialnetwork_feature_collisions.py`.
- Local matched data: `ml/data/processed/socialnetwork-error-development-v1/`.
- Local study: `ml/models/candidates/socialnetwork-error-supervised-v1/`.
- Tracked summary: `docs/research/evidence/socialnetwork-errors-results-v1.json`.

Study plan SHA-256:
`146115d382b8996957505233496d14eb9d6b4c9b3c30ce11b6cb7e515f39f984`.
Study report SHA-256:
`bebaf2ee22df5aabebeae490b207094ef77b56aa8ca1ce352b5aaaf322bdff3c`.
The underlying archive hash matches the project-local import. Prefix decoding
does not verify each inner ZIP's CRC; it is not a full-trace integrity/capture audit.

Full Python suite120 passed (115 ML/data tests plus five inference-service tests).
Tests cover scope restrictions, unlabelled context boundaries, target separation,
result parsing, payload exclusion, future-prefix invariance, stable sample/feature
replay, container isolation and read-only collision counting. No project servers
were started. Do not launch more parameter sweeps merely to force98/99%; prioritize
trustworthy operational labels and additional observability before another study.
