# Phase 3 Baseline Results

Experiment date: 2026-09-27

These results establish the project's first reproducible baseline. They are not
evidence that the project exceeds a published paper because the papers may use
different samples, splits, preprocessing, and label definitions.

## Dataset verification

| Split | Rows | Normal | Attack | Columns | Duplicate rows | SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| Official training | 175,341 | 56,000 | 119,341 | 45 | 0 | `bec7dd5ec88dc2a0ccc7a07879d338395ed7421750f675fd0339e07dfe0648fa` |
| Official testing | 82,332 | 37,000 | 45,332 | 45 | 0 | `734fe6642edf758f7c94d7d9149426b49d202fe8e7bf0bef47392489c3c0a559` |

The official training file was divided into 80% training and 20% stratified
validation data using seed 42. The official test file remained separate from
fitting and model selection.

## Results

| Model | Validation accuracy | Validation macro F1 | Test accuracy | Test macro F1 | Test attack recall | Test false-positive rate | Test ROC-AUC | Test latency per sample |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 93.23% | 92.22% | 83.53% | 82.92% | 92.94% | 28.01% | 95.56% | 0.0028 ms |
| Random Forest | 95.48% | **94.84%** | 89.79% | **89.46%** | **97.65%** | **19.85%** | **98.43%** | 0.0074 ms |

Validation selected Random Forest as the current candidate. Its additional
latency is small in this local batch measurement, while its held-out macro F1,
attack recall, false-positive rate, and ROC-AUC are all better than the baseline.

## Confusion matrices

Matrix order is `[[TN, FP], [FN, TP]]`.

| Model | Validation | Official test |
|---|---|---|
| Logistic Regression | `[[10007, 1193], [1180, 22689]]` | `[[26638, 10362], [3200, 42132]]` |
| Random Forest | `[[10579, 621], [965, 22904]]` | `[[29657, 7343], [1064, 44268]]` |

## Environment

- Python 3.14.6
- pandas 3.0.6
- scikit-learn 1.9.1
- joblib 1.6.0
- MLflow 3.16.1 using a local SQLite tracking database

Generated JSON results, MLflow state, datasets, and model binaries remain local
and Git-ignored. The tracked evidence contains metrics and dataset hashes but no
raw records or sensitive information.

## Interpretation and next experiment

The validation-to-test reduction and 19.85% test false-positive rate show that
generalization remains the main weakness. The next experiment should therefore
test leakage-safe feature selection, threshold calibration using validation data
only, and an additional class-balanced tree/boosting candidate under the same
split. We should not move the current candidate into a policy engine as a final
model yet.
