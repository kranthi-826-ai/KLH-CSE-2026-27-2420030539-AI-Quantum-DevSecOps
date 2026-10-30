# SocialNetwork bounded reference pilot

Experiment date: 2026-10-20. This is a separate unsupervised syscall model,
not an improvement to the promoted UNSW model or to CICIoT/HTTP attack accuracy.

## Inputs and representation

The complete training tar metadata inventory finished: 27 headers, no read
budget exhaustion. Training has two worker nodes, each with two very large
trace ZIPs. Eight command intervals and six scaling intervals are recorded;
their expanded +/-1 second windows are excluded from reference features.
This does not prove the rest of training is completely free of contamination.

For a bounded initial baseline, use only the first node1 trace in training,
scenario5/collection1 validation for calibration and scenario3/collection1
validation for a separate normal check. Each prefix is capped at 500,000
events or 128 MiB decompressed, whichever comes first. Here all three reached
500,000 events with zero rejected lines, for 1.5 million parsed events total.
Only minutes of recording are represented; this is NOT full-dataset training.
Node2, later collections, other scenarios and attack traces are not evaluated.

Group by container and nonoverlapping one-second windows; omit global first
and last boundary windows. Fixed 29 features: event count, exit fraction,
negative-result fraction among syscall exits, unique syscall/thread counts,
16 stable hashed syscall frequency bins and 8 category frequency bins.
Absolute timestamp/container/thread values are not ML inputs. Arguments are
discarded after negative-result counting. Container hashes remain grouping
metadata, not features. Detection is after a window closes, not per-request
preauthorization. Hash collisions and application/workload differences remain
limitations. No learned vocabulary or feature selection uses held-out data.

## Timing correction and preserved preliminary run

The preliminary `socialnetwork-reference-v1` included trace windows before the
annotated experiment start. Those are not justified as ground-truth normal
solely by `Attack: NONE` in the later experiment annotation. Its preliminary
alarm fractions are not accepted normal FPR evidence.

The corrected `socialnetwork-reference-v2` parses Portuguese weekday/English
month date annotations, explicitly maps WEST to UTC+1, and includes only full
windows inside the annotated 30-minute normal runs. It discarded 1,184
calibration and 980 normal-check windows outside the annotated intervals.
This is a labeling/timing correction, not a model search or threshold tuning
against attack results. Both runs are retained locally without overwriting.

## Fixed baseline and results

Isolation Forest: 128 trees, max_samples=256, two CPU workers, seed 20261020.
Fit 2,977 reference windows. No candidate search. Threshold is the next float
above the calibration 95th percentile (higher quantile), fixed before the
separate normal check: 0.5524111151667888.

| Partition | Complete container-second windows | Alarms | Observed normal alarm fraction |
|---|---:|---:|---:|
| Annotated normal calibration | 2,191 | 109 | 4.975% |
| Separate annotated normal recording | 2,244 | 53 | 2.362% |

The recorded corrected preparation/fit/scoring run took 7.38 seconds, excluding
the earlier complete archive metadata/checksum scans and environment setup.
Windows from the same recording/container are correlated; these counts are
not independent trials or evidence of general real-world FPR. Low normal
alarms alone do not demonstrate that attacks can be detected. Accuracy,
attack recall, macro-F1 and superiority to research papers are NOT measured.

## Reproduction/evidence

Run `ml/training/train_socialnetwork_reference.py` with source Downloads folder,
a NEW candidate output directory, `--training-intake` pointing to
`ml/artifacts/socialnetwork-training-intake-v1.json` and `--validation-intake`
pointing to `ml/artifacts/socialnetwork-inspection-v3.json`. Existing output
directories are refused. Archive integrity was verified at intake; prefix
streaming does not independently verify full inner-ZIP CRCs.

Local v2 output: `ml/models/candidates/socialnetwork-reference-v2/`. Includes
model, report, provenance hashes and separate feature files. No raw trace or
model binary is committed. `socialnetwork-reference-pilot-v1.json` in the
tracked evidence folder records the corrected result and model/code hashes.
Full ML test suite: 75 passed. Promoted model SHA-256 remains
`c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.

Next incomplete step: inspect attack annotation metadata, define affected
containers/time intervals and frozen evaluation groups, and test this fixed
model without tuning on final outcomes. No enforcement or deployment change.
