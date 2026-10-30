# Workload diagnosis, service profiles and supervised development study

Date: 2026-10-20. All experiments here use exposed development data, not a new
final test. No candidate met the declared recall/control gates. No deployment,
automatic blocking or model promotion changed.

## Diagnosis and service-role mapping

Read collector container names to map cached group hashes to service roles:
the Kubernetes container-name field, not replica suffix, pod ID, attack label,
scenario or client-supplied metadata. Exact group coverage is required; fail
rather than guess roles for missing groups. Original cached numerical features
are retained. Roles route to normal profiles, not numerical identity features.

Expanded training contains25 roles. Only453/14,700 rows (3.082%) are nginx-thrift,
while all302 development observations are that role. The13 roles in the
available calibration prefix have normal profiles;12 other training roles
lack calibration support. Unknown/unsupported roles must abstain, not be
silently called benign. The measured normal-check prefix contains only the
13 calibrated roles, so100% coverage there does not prove all25 are covered.

Nginx training/calibration marginal feature distributions differ: descriptive
two-sample KS statistics are0.484 for syscall_bin_3,0.428 for unique_threads,
and0.393 for category_bin_0. Median one-second event counts are232 in training,
294 in calibration and268 in the November pre-injection controls. These are
correlated window observations: no significance, independence or causal
explanation is claimed. The data support distribution-shift investigation,
not proof that role imbalance alone caused the earlier regression.

## Fixed service-role profile experiment

One128-tree Isolation Forest per eligible role, same seed20261020 and maximum
256 samples per tree, with minimum100 reference and30 calibration rows.
Scikit-learn clips max_samples to training size for smaller eligible roles;
the observed warnings are expected, not failed training. Per-role threshold is
the next float above the normal calibration95th percentile. No attack fitting
or threshold search. Missing profiles explicitly abstain.

- Separate normal check:49/2,244 alarms (2.184%), no abstentions in this prefix.
- Exposed attack windows:9/26 flagged (34.615%).
- Pre-injection controls:12/276 alarms (4.348%).
- Cases with any alert:7/8. Development gates failed; reject as a replacement.

## Fixed supervised search with grouped validation

Use the302 replay-verified exposed development rows,29 numerical features,
26 exposure labels and276 pre-injection controls. Exposure is an annotation
label, not proof of successful exploitation. No class rebalancing by synthetic
rows and no random window split. Leave one entire CVE recording group out in
each of eight folds; all its positive and control windows stay together.
Case/group/role/window identifiers are not model features.

Three recipes frozen before scores: balanced scaled logistic regression C0.5;
balanced RF128/depth4/leaf2; XGBoost128/depth2/rate0.05/min_child3/lambda4.
Threshold fixed at0.5, no threshold search or final-test access. Classifier
probabilities are not asserted to be calibrated confidence estimates.

| Grouped out-of-fold model | Exposure windows detected | Control alarms | Macro-F1 |
|---|---:|---:|---:|
| Logistic regression |20/26 (76.92%) |2/276 (0.725%) |0.90947 |
| Random Forest |18/26 (69.23%) |1/276 (0.362%) |0.89195 |
| XGBoost |17/26 (65.38%) |0/276 observed |0.88733 |

None reached95% exposure-window recall with control alarms at most5%; no
winner fitted or saved for independent evaluation. Zero observed XGBoost
control alarms do not prove zero real false-positive risk. The improved
control numbers do not justify hiding the misses. Eight groups and26 positive
windows are small; no paper-superiority claim, general accuracy or precision
estimate for a real deployment's class prevalence is supported.

## Evidence and next experiment boundary

Ignored outputs: `ml/data/processed/socialnetwork-roles-v1/`,
`ml/models/candidates/socialnetwork-role-profiles-v1/`, and
`ml/models/candidates/socialnetwork-supervised-v1/`. Plans, grouped fold results,
model hashes (profiles only), support counts and thresholds are preserved.
Scripts reject existing output directories. Full ML suite:88 passed.
Promoted UNSW checksum unchanged. Original and rejected models remain available.

The compact hashed-frequency representation and sample diversity need further
investigation. Next predeclare richer entry/exit syscall features and additional
recording-level development coverage. Independent scenarios and reserved
collections must stay untouched until a new recipe is frozen. Do not lower
gates or repeatedly tune against the same final results to manufacture99%.
