# Phase 3 XGBoost Calibration Results

Experiment date: 2026-10-01

## Method

The selected depth-8 XGBoost configuration was evaluated without using the
official test file during model or threshold selection. Three independent
seeded repetitions divided only the official training file into 70% fitting,
15% threshold calibration and 15% validation partitions. Each run trained the
same balanced Random Forest reference on identical fitting rows.

The fixed gates were false-positive rate at or below 6.04%, attack recall at or
above 95.46%, and macro-F1 above the same-split Random Forest. Thresholds were
selected by calibration macro-F1 only among settings satisfying the first two
constraints.

## Repeated validation

| Seed | Threshold | XGBoost macro F1 | Attack recall | FPR | RF macro F1 | Pass |
|---:|---:|---:|---:|---:|---:|---|
| 42 | 0.575 | 95.21% | 96.67% | 5.98% | 94.86% | Yes |
| 123 | 0.575 | 95.38% | 96.87% | 5.93% | 95.00% | Yes |
| 2026 | 0.585 | 95.09% | 96.40% | 5.75% | 94.97% | Yes |

All repetitions passed. The median selected threshold, 0.575, was frozen before
the final run. Exact per-seed metrics and variability are stored locally in
`ml/artifacts/xgboost-repeated-seed-confirmation-v1.json`.

## Frozen official-test evaluation

The frozen configuration was fitted on all 175,341 official training rows and
evaluated once at threshold 0.575 on the 82,332-row official test file.

| Model | Accuracy | Macro F1 | Attack recall | FPR | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Existing balanced Random Forest | **89.79%** | **89.46%** | 97.65% | **19.85%** | 98.43% |
| Frozen calibrated XGBoost | 89.17% | 88.79% | **97.68%** | 21.25% | **98.47%** |

The XGBoost candidate increased attack recall by about 0.03 percentage points
and ROC-AUC by about 0.05 points, but reduced accuracy and macro-F1 and increased
false positives. It is rejected for promotion. The existing balanced Random
Forest remains the promoted model.

## Interpretation and limitation

The large validation-to-test shift remains the primary research problem. The
result is useful negative evidence: threshold calibration improved validation
trade-offs but did not resolve generalization to the official test distribution.
No further candidate should be selected using these test outcomes.

The repository contains historical experiments on the same official test file,
so this result must not be described as evaluation on a dataset entirely unknown
to the broader project. Future optimization remains training/validation-only;
stronger claims require a separately sourced external generalization dataset or
a prospectively collected microservice workload.
