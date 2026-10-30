# Phase 3 Random Forest Threshold Calibration Results

## Purpose

Evaluate whether an unweighted Random Forest with a threshold selected on
training-only calibration data can improve the currently promoted balanced
Random Forest without increasing false alarms or reducing attack detection.

## Protocol

- Dataset: official UNSW-NB15 predefined training/test files.
- Features excluded: `id`, `attack_cat`, and `label`.
- Selection: three independent 70/15/15 fit/calibration/validation splits from
  the official training file only, using seeds 42, 123, and 2026.
- Threshold constraints: false-positive rate at most 6.0446%; attack recall at
  least 95.4571%; Macro-F1 above the same-split reference.
- Frozen choice: the median calibrated threshold, 0.600.
- Final evaluation: one recorded run on the official test file after the model
  and threshold were frozen.

## Training-only confirmation

| Seed | Threshold | Validation accuracy | Macro-F1 | Attack recall | FPR |
|---:|---:|---:|---:|---:|---:|
| 42 | 0.595 | 95.65% | 95.02% | 96.37% | 5.89% |
| 123 | 0.600 | 95.70% | 95.08% | 96.45% | 5.90% |
| 2026 | 0.610 | 95.66% | 95.04% | 96.12% | 5.33% |

The candidate passed all predeclared validation gates in each split.

## Frozen official-test result

| Model | Accuracy | Macro-F1 | Attack recall | FPR | Decision |
|---|---:|---:|---:|---:|---|
| Promoted balanced Random Forest | 89.79% | 89.46% | 97.65% | 19.85% | Keep |
| Unweighted RF, threshold 0.600 | 89.58% | 89.24% | 97.38% | 19.98% | Reject |

Although threshold calibration improved validation behaviour, it did not
generalize beyond the promoted model on the official test set. The evaluated
artifact is retained for reproducibility and must not be promoted.

## Evidence

- `ml/artifacts/random-forest-unweighted-threshold-calibration-v1-seed42.json`
- `ml/artifacts/random-forest-unweighted-threshold-calibration-v1-seed123.json`
- `ml/artifacts/random-forest-unweighted-threshold-calibration-v1-seed2026.json`
- `ml/artifacts/random-forest-unweighted-repeated-seed-confirmation-v1.json`
- `ml/artifacts/random-forest-unweighted-frozen-final-evaluation-v1.json`
