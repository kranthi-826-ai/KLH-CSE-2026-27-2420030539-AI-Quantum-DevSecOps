# Two-recording development study

Date:2026-10-20. The expansion protocol was declared before collection2 trace
decoding and committed as `c6c2b9b` before grouped model scores were inspected.
All eight scenario5/plain_workload/collection2 cases were assigned DEVELOPMENT;
scenarios1/3/7 remain unscored for independent evaluation. No final test was
silently reassigned after seeing its performance.

## Prepared data and safeguards

Preserved the original302 rows exactly. Added255 rows from the second eight
recordings, yielding557 observed windows:51 annotated exposure and506
pre-injection controls,16 recordings/eight CVEs. All32 worker traces from the
two collections are represented in preparation (16 new scans); affected pods
were observed on node1, with no target-pod rows on node2. All new scans reached
their annotated attack ends under the existing bounded prefix budget.

All new annotation/CMDs:0 checks passed. A separate timezone audit verified
that selected attack/control intervals lie inside the annotated30-minute
experiment periods. Exact pod matching and seconds/nanoseconds normalization
are unchanged. Positive coverage is required for every case; missing coverage
fails preparation. No case/window was removed for being difficult to predict.
No raw dataset extraction, model promotion or enforcement change occurred.

Features remain original29 and richer269. Original rows retain identical
values/labels; new base values are computed by the unchanged original
aggregation function called through the rich wrapper. This is not a claim
that new rows were part of the earlier baseline replay experiment.

## Fixed grouped comparison

Same three recipes/threshold0.5 and eight leave-one-CVE-out folds. BOTH
recordings of a CVE are held out together. No neighboring recording of the
held-out CVE is used in that fold's training. No threshold search or additional
candidate tuning. Since training AND validation sets now contain additional
recordings, comparison with prior percentages is not a controlled same-test
improvement claim.

| Features/model | Exposure hits/51 | Pre-injection alarms/506 | Macro-F1 |
|---|---:|---:|---:|
| Base/logistic |40 (78.43%) |3 (0.593%) |0.91867 |
| Base/RF |36 (70.59%) |0 observed |0.90649 |
| Base/XGB |35 (68.63%) |0 observed |0.89919 |
| Rich/logistic |37 (72.55%) |14 (2.767%) |0.84891 |
| Rich/RF |36 (70.59%) |0 observed |0.90649 |
| Rich/XGB |36 (70.59%) |0 observed |0.90649 |

All six fail the95% exposure-recall gate. No winner/model is fitted for final
evaluation. Observed zero control alarms do not establish zero real risk.
No combined accuracy is reported from the arbitrary sampled positive/control
ratio. These are correlated small-sample development observations, not broad
microservice intrusion-detection benchmark results.

## Concentrated remaining error

For base/logistic,9 of11 misses occur in the held-out CVE-2022-0492 group:
2/11 windows detected there, versus38/40 for the remaining CVE groups. This
concentration is a diagnosis, not permission to exclude that CVE or report
only the easy cases. The other two misses are CVE-2017-16939 and CVE-2017-7308.

A descriptive feature audit shows that the11 CVE-2022-0492 exposure windows
do contain selected syscall events (including execve, clone and one mount),
but this does not prove every missed window individually contains an observable
malicious action. The annotation denotes exposure time, not exploit success.
Potential next hypothesis: causal short-term syscall history may retain
multi-window behaviour that independent one-second snapshots discard. Such
history must be computed before label selection, reset per recording, and
must not use future events, attack timestamps or labels as inputs.

## Reproducibility

Collector: `ml/data/expand_socialnetwork_development.py`; study:
`ml/training/study_socialnetwork_rich.py` with new data/output directories.
Ignored data: `ml/data/processed/socialnetwork-expanded-development-v1/`.
Ignored results: `ml/models/candidates/socialnetwork-expanded-supervised-v1/`.
Original outputs preserved, directories exclusive. Full ML suite93 passed;
promoted model SHA-256 remains unchanged. All plans/hashes/folds and difficult
cases are retained for the paper, including negative results.
