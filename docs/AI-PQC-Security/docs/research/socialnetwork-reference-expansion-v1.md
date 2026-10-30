# Reference expansion experiment: rejected replacement

Date: 2026-10-20. Hypothesis: broader normal-reference coverage across worker
nodes and recording segments would improve the fixed syscall anomaly model.
Result: **not supported on the exposed development set**. Preserve the prior
pilot; neither model is promoted to production or used for automatic blocking.

## Fixed training experiment

- Same 29 features, 128-tree Isolation Forest, max_samples=256, seed20261020,
  two CPU workers. Same calibration rule: next float above the normal
  calibration 95th percentile. No search over models/features/thresholds.
- Four 500,000-event prefixes, each capped at 128MiB decoded: both workers and
  both trace segments in the original training collection. Parsed 2 million
  events; 14,700 retained container-second windows, compared with 2,977 before.
- Trace contributions: node1/000 2,977; node1/001 4,325; node2/000 3,141;
  node2/001 4,257. Known command/scaling exclusions retained; no sampled window
  intersected an exclusion. This does not establish uncontaminated training.
- Sample windows span four short sections on June8/15 (UTC dates), not the
  complete eight-day recording. Timestamp overlap with the annotated normal
  evaluation intervals is forbidden. Not full-dataset training.
- Reused exactly the same 2,191 annotated calibration and 2,244 normal-check
  feature rows, with original file hash verification.
- Training/preparation/scoring duration: 58.45s, including streaming through
  intervening compressed trace members, without extracting them to disk.

## Matched development comparison

Created an ignored 302-row development cache containing the already exposed
scenario5/collection1 observations (26 exposure and 276 pre-injection control
windows). Reconstructed baseline scores agree to absolute tolerance1e-12 for
every window with the original separate exposure/control scans. No final test
was consumed to produce this cache. Group/case/window/labels are metadata and
not supplied as model features. Preparation reads the compressed traces once,
so subsequent development comparisons do not repeatedly decompress them.

| Metric on identical rows | Earlier pilot | Expanded reference |
|---|---:|---:|
| Training windows | 2,977 | 14,700 |
| Exposure-window alerts | 20/26 (76.92%) | 18/26 (69.23%) |
| Cases with any alert | 8/8 | 8/8 |
| Pre-injection control alarms | 7/276 (2.54%) | 70/276 (25.36%) |
| Separate June normal-check alarms | 53/2,244 (2.36%) | 92/2,244 (4.10%) |

Both fail the declared development window-alert gate of95%, even though each
alerts in every case. The expanded model also fails the5% control-alarm gate.
Case-level alert coverage alone hides these failures. The calibration
thresholds are0.5524111151667888 (earlier) and0.609893230246857 (expanded), each
derived mechanically from the same normal calibration rows, not attack tuning.

No manufactured accuracy is calculated from the arbitrary sampled class ratio.
This is development evidence, not an independent test or literature comparison.
The apparent workload/recording shift requires investigation; this experiment
does not prove its mechanism or show that adding data always hurts.

## Decision and evidence

No selected/promoted candidate. The better prior syscall pilot remains only
experimental; the actual promoted UNSW model hash is unchanged:
`c14839d71a11b46eb94abd2198b7ec4a72a794d092e97c2e564f0592ee1a3c39`.

Code:

- `ml/training/train_socialnetwork_expanded.py`: frozen-plan expansion.
- `ml/data/prepare_socialnetwork_development.py`: replay-verified cache.
- `ml/training/compare_socialnetwork_development.py`: fixed candidate scoring,
  separate metrics and explicit no-promotion decision.

Ignored outputs: `ml/models/candidates/socialnetwork-expanded-v1/`,
`ml/data/processed/socialnetwork-development-v1/`, and
`ml/models/candidates/socialnetwork-expansion-comparison-v1/`. All output
directories are exclusive; no previous artifacts were overwritten. Full ML
suite:81 passed. Future independent attack groups remain unscored.

Next: diagnose per-workload feature distributions and consider service-role
normal profiles before choosing another candidate. Recheck the unchanged
pipeline on independent groups only after development choices are frozen.
