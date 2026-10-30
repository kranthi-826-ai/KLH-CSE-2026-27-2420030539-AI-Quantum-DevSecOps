# CICIoT2023 capacity study v1

Date: 2026-10-19. Development experiment; not a deployed-model accuracy claim.

## Measured result

All nine fits completed in 122.88 seconds end to end. No candidate passed the
security gates on all three splits. The deployed UNSW model is unchanged.

The table reports arithmetic means across three internal validation splits:

| Recipe | Accuracy | Macro-F1 | Attack recall | Weak-family recall | FPR |
|---|---:|---:|---:|---:|---:|
| Previous deeper reference | 89.855% | 87.875% | 88.068% | 60.353% | 5.070% |
| Higher-capacity XGBoost | 90.035% | 88.072% | 88.294% | 60.926% | 5.022% |
| Extra Trees | 87.824% | 85.727% | 85.284% | 52.805% | 4.963% |

The larger XGBoost improved mean accuracy by 0.180 percentage points, macro-F1
by 0.197 points and weak-family recall by 0.573 points against the paired
reference. Its FPR varied from 4.614% to 5.448%; recall was only 88.130% to
88.420%, far below the 95% requirement. Therefore it is an incremental
development improvement, not a successful security-gate result. Extra Trees
did worse and is not recommended from this study.

These means must not be compared as a replacement for the earlier 90.90%
outer-validation pilot: the samples and threshold-selection protocol differ.
There is no new reserved-test result, cross-dataset result, 99% result or
live-microservice detection claim. The 21 Python tests passed in 5.13 seconds.

Next priority is representative benign and difficult-attack data, capture-level
validation where identifiers permit, and genuine application/runtime features.
This study does not justify simply increasing tree counts again. Any new data
version must get a separate manifest and evaluation plan rather than rewriting
the frozen pilot or using the reserved test to tune parameters.

## Question and protocol

Does increasing tree capacity or switching to Extra Trees improve detection of
BruteForce, Recon and Web-based attacks without exceeding a 5% false-positive
rate? The previous deeper family-weighted XGBoost is the paired reference.

The script freezes its recipe, environment, helper/script hashes and dataset
manifest hash before fitting. Nine fits cover three recipes and seeds 42, 123,
2026. Each uses only the frozen 230,242-row training partition, split 70/15/15
by attack subtype for fitting, threshold calibration and internal validation.
Each recipe uses the same split for a given seed. The earlier seed-42 result
has already been observed; this is further development, not an untouched test.

- Reference: XGBoost, 320 trees, maximum depth 8.
- Higher capacity: XGBoost, 500 trees, maximum depth 10.
- Alternative: Extra Trees, 240 trees, unrestricted depth, minimum leaf size 1.
- All use four worker threads and identical training weights: benign 2,
  weaker attack groups 3, remaining attacks 1.
- Only the 39 numeric predictors enter fitting; filenames, labels, hashes and
  metadata are excluded. Thresholds are selected on calibration, not validation.
- Calibration prioritizes recall >=95% within FPR <=5%, then macro-F1. A
  diagnostic fallback within the FPR budget is explicitly marked ineligible.
- All three validation splits must pass both security gates, and mean macro-F1
  must exceed the repeated reference, to qualify for future confirmation.

The outer calibration, outer validation and reserved test are never loaded by
this script. No model is automatically promoted. Repeated random splits share
observations and are sensitivity checks, not independent external datasets.
The capped pilot's attack prevalence and capture limitations still apply.

## Reproduction and evidence

Run `ml/.venv/Scripts/python.exe ml/training/compare_ciciot2023_capacity.py`
from the repository root. Existing evidence is never overwritten. The full
local artifacts are `ml/artifacts/ciciot2023-capacity-study-v1-plan.json` and
`ml/artifacts/ciciot2023-capacity-study-v1.json`; they contain per-subtype recall,
confusion matrices, timings, seeds, parameters and checksums.
The completed report is also tracked at
`docs/research/evidence/ciciot2023-capacity-study-v1.json` so aggregate research
evidence survives without committing datasets or model binaries.

Unit tests in `ml/tests/test_ciciot2023_capacity.py` check both gates, failed
calibration, deterministic seeds and worker/tree bounds. These test model-study
logic, not real-world cyberattack protection.
