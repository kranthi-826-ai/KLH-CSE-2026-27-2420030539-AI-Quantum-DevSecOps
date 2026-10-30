# Matched rich-syscall feature study: no replacement selected

Date: 2026-10-20. Exposed-development experiment only. Hypothesis: the compact
hashed syscall representation loses detail needed to distinguish short CVE
exposure windows from legitimate workload. This study did not establish a
benefit from the specific richer representation tested.

## Representation and matched data

Original29 features unchanged. Add128 entry-syscall frequency bins,16 entry
category bins,32 explicit entry counts for selected process/namespace/mount/
permission/socket syscalls, and64 within-thread syscall-transition frequency
bins. Total269 features. The explicit calls are hypotheses about useful
behaviour, not rules asserting every execve/mount/etc. is malicious.

Only syscall entry events enter the additional counts/transitions. Thread
IDs are temporary grouping keys; transitions cannot cross threads, containers
or time windows. No raw syscall arguments, addresses, paths, credentials,
thread/container IDs, timestamps or attack labels enter model features.
State is scoped to the bounded context slices, not whole raw recordings.

Re-extracted exactly the same302 observed development windows from the same
eight scenario5/plain_workload/collection1 cases, both worker traces. Every
original base-feature value and label is checked against the cached baseline;
no rows were added, dropped or relabeled to improve scores. Raw traces remain
compressed in Downloads; only derived local ignored JSON data is persisted.

## Frozen comparison

Three identical small recipes for both feature sets: scaled balanced logistic
C0.5; balanced RF128/depth4/leaf2; XGB128/depth2/rate0.05/min_child3/lambda4.
Threshold0.5 fixed before scores. Leave one whole CVE recording group out in
each of eight folds. No random window mixing, threshold search or final-test
access. RF's sqrt feature subsampling naturally changes with input dimension;
this is a matched pipeline-budget comparison, not a fixed-dimensional causal
feature-effect experiment.

| Model | Base exposure hits /26 | Rich exposure hits /26 | Base control alarms /276 | Rich control alarms /276 |
|---|---:|---:|---:|---:|
| Logistic |20 (76.92%) |19 (73.08%) |2 (0.725%) |11 (3.986%) |
| RF |18 (69.23%) |18 (69.23%) |1 (0.362%) |3 (1.087%) |
| XGBoost |17 (65.38%) |17 (65.38%) |0 observed |0 observed |

Base out-of-fold metrics reproduce the previous supervised study exactly.
Rich macro-F1: logistic0.82286, RF0.87310, XGB0.88733. All six pipelines fail
the95% exposure-recall gate, so no winner/model file is selected for independent
evaluation. Zero observed control alarms are not proof of zero real FPR.

A descriptive exact-vector audit found275 unique rich vectors and no exact
feature-vector contradictions between positive/control labels. This does not
validate the exposure labels, prove generalizability or demonstrate that99%
is attainable. Only26 positive windows from eight correlated recordings are
available here; additional detail can increase variance rather than useful
cross-recording signal. Cause is not established by this experiment.

## Evidence and next step

Code: `ml/data/socialnetwork_rich_syscalls.py`,
`ml/data/prepare_socialnetwork_rich.py`,
`ml/training/study_socialnetwork_rich.py`. Ignored outputs:
`ml/data/processed/socialnetwork-rich-development-v1/` and
`ml/models/candidates/socialnetwork-rich-supervised-v1/`. Plans, feature
definitions, fingerprints, matched-row checks and all fold results retained.
Full ML suite90 passed; promoted model unchanged; no enforcement enabled.

Next: predeclare additional recording-level development examples before
looking at their outcomes, while preserving independent scenarios for a final
frozen test. Do not repeatedly extend model complexity or lower gates using
these same26 positive examples to manufacture a target percentage.
