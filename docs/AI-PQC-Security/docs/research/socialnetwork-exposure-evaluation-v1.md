# Frozen SocialNetwork exposure pilot and matched controls

Date: 2026-10-20. Model is the unchanged `socialnetwork-reference-v2` Isolation
Forest. This is a bounded, offline public microservice syscall experiment,
not a deployed attack blocker, full-dataset benchmark or new UNSW/CICIoT score.

## Annotation audit and scope

All four attack tar metadata inventories completed (622 headers each in
scenarios3/5/7; 607 in scenario1), without decoding attack trace ZIPs at that
stage. Metadata includes CVE injection intervals and affected pod names.
Scenario1 contains epoch seconds, while other inspected annotations use epoch
nanoseconds. Explicit parsing accepts these two units only and refuses to
guess milliseconds. `dates.txt` must agree with the matching experiment
annotation. Stale unrelated `commands.txt` timestamps are not attack labels.

Before trace scoring, a local immutable plan fixed: all eight CVEs in
scenario5/plain_workload/collection1, both worker-node first trace ZIPs,
unchanged model hash, unchanged 29-feature implementation and calibrated
threshold 0.5524111151667888. No fit or threshold search occurs in evaluation.
All sixteen traces reached the annotated attack end within the 20-million-event
and 2-GiB decoded-byte caps. Features retain only a few seconds around injection;
the earlier trace is streamed and discarded. No attack code was executed.

Affected pod membership is exact Kubernetes pod matching, not substring
matching. A positive exposure window overlaps the annotation interval and
belongs to that pod. Fully contained windows are also reported separately.
These are exposure labels: annotation does not independently prove successful
exploitation or that each syscall inside the interval is malicious.

The matched-control addendum was written while exposure scoring was running,
before viewing scores or aggregate outcomes. It uses the same pod in the same
recording between 60 and 10 seconds before injection, with CMDs: 0, discarding
boundary/incomplete windows. These are pre-injection controls, not forensic
proof of a clean host. The model/threshold remain fixed. Other pods/times are
not automatically assigned benign labels.

## Results

| CVE | Overlap windows flagged / observed | Pre-injection control alarms / observed |
|---|---:|---:|
| CVE-2016-5195 | 3 / 3 | 2 / 36 |
| CVE-2016-9793 | 3 / 3 | 0 / 38 |
| CVE-2017-1000112 | 2 / 2 | 0 / 36 |
| CVE-2017-16939 | 2 / 3 | 1 / 37 |
| CVE-2017-16995 | 3 / 3 | 0 / 30 |
| CVE-2017-7308 | 2 / 3 | 2 / 34 |
| CVE-2019-5736 | 3 / 3 | 1 / 29 |
| CVE-2022-0492 | 2 / 6 | 1 / 36 |
| Total | 20 / 26 (76.92%) | 7 / 276 (2.54%) |

- At least one alert occurred in each of eight observed injection cases (8/8).
  This is case-level alert coverage, **not 100% accuracy**.
- Fully contained exposure windows: 8/11 flagged (72.73%); three misses.
- Overlap windows: six misses, four in CVE-2022-0492. Boundary-window inclusion
  changes the unit and result; both definitions are preserved, not cherry-picked.
- Sparse seconds with no observed syscalls do not produce feature rows. These
  denominators count observed scored windows, not every wall-clock second.
- Separate earlier June normal recording: 53/2,244 alarms (2.362%). The matched
  November pre-injection check helps expose domain shift but does not establish
  broad cross-domain robustness. Controls generated seven false alerts here.
- Exposure scan 75.60s; separate controls 78.38s, excluding metadata intake.

Eight cases/one workload scenario/one collection cannot support claims of
general real-world recall, production readiness, latest-attack coverage or
superiority over another research paper. Legacy CVE injection behaviour is
not equivalent to modern DDoS, brute-force or malicious API requests. Window
observations within a recording are correlated, not independent trials.
No synthetic combined accuracy is reported for the arbitrarily sampled
positive/control ratio. No model promotion or enforcement was enabled.

## Evidence and remaining work

Local ignored outputs:

- `ml/models/candidates/socialnetwork-exposure-evaluation-v1/`: plan, append-only
  progress observations and one-shot result.
- `ml/models/candidates/socialnetwork-pre-injection-control-v1/`: separate plan,
  progress and result.
- `ml/artifacts/socialnetwork-attack-metadata-v1.json`: annotation inventory.

Reproduction scripts: `ml/training/evaluate_socialnetwork_attacks.py` and
`ml/training/evaluate_socialnetwork_controls.py`, each taking source directory,
frozen candidate directory, metadata JSON and a NEW output directory. Refuse
to overwrite results. Preserve original outputs; reruns are not fresh tests.

Audited model/code/protocol/plan hashes, threshold agreement, matching case
lists, both-worker coverage through attack end, scored alert decisions and
strictly pre-attack control windows. Full ML suite: 79 passed. Promoted UNSW
model checksum remains unchanged.

This scenario5/collection1 set is now exposed and can only be development
evidence for future candidates. Attack traces in scenarios1/3/7 and all second
collections remain unscored. Further work: broader representative training,
recording-level development confirmation and a frozen independent evaluation
before any deployment decision. Prior successful and negative studies remain.
