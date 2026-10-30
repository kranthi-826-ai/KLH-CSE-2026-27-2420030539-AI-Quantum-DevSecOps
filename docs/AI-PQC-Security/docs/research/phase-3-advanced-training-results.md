# Phase 3 Advanced Training Results

Experiment date: 2026-10-19

## Objective

Improve the binary UNSW-NB15 detector while preserving research integrity.
All candidate selection, feature selection, weighting, and threshold calibration
used the official training file only. The official test file was evaluated only
after a recipe passed repeated validation and was frozen.

## Diagnostic result

The balanced Random Forest validation errors were concentrated in two attack
families:

| Attack family | Validation samples | Missed attacks | Miss rate |
|---|---:|---:|---:|
| Fuzzers | 3,674 | 874 | 23.79% |
| Analysis | 422 | 45 | 10.66% |
| Exploits | 6,583 | 41 | 0.62% |

Normal FTP and `INT`-state flows had elevated validation false-positive rates.
TTL, load, rate, duration, byte-count, timing, and connection-count features
were among the most important Random Forest inputs. This supports the conclusion
that distribution shift, rather than insufficient training accuracy, is the
main limitation.

## Validation-only experiments

| Experiment | Best validation accuracy | Macro-F1 | Attack recall | FPR | Decision |
|---|---:|---:|---:|---:|---|
| Extra Trees | 94.41% | 93.50% | 96.90% | 10.88% | Reject |
| Regularized XGBoost tuning | 95.87% | 95.26% | 96.77% | 6.05% | Reject: missed strict FPR gate |
| XGBoost with 60 selected features | 95.70% | 95.08% | 96.41% | 5.80% | Confirm across seeds |
| Family-weighted XGBoost | 95.79% | 95.18% | 96.40% | 5.52% | Confirm across seeds |
| Histogram Gradient Boosting | **96.05%** | **95.47%** | **96.88%** | **5.73%** | Confirm across seeds |

The two confirmed candidates passed the predeclared validation gates for seeds
42, 123, and 2026. Feature selection was fitted inside each pipeline. Attack
family labels were used only to compute fit-sample weights and were excluded
from inference features.

## Frozen official-test evaluations

| Frozen model | Accuracy | Macro-F1 | Attack recall | FPR | ROC-AUC | Decision |
|---|---:|---:|---:|---:|---:|---|
| Promoted balanced Random Forest | **89.79%** | **89.46%** | **97.65%** | **19.85%** | 98.43% | Keep |
| XGBoost, 60 selected features, threshold 0.580 | 89.20% | 88.82% | 97.71% | 21.23% | **98.48%** | Reject |
| Family-weighted XGBoost, threshold 0.665 | 89.34% | 88.99% | 97.39% | 20.52% | 98.38% | Reject |
| Histogram Gradient Boosting, threshold 0.585 | 88.76% | 88.35% | 97.74% | 22.24% | 98.46% | Reject |

Neither frozen candidate beat the promoted model on all gates. The promoted
balanced Random Forest therefore remains unchanged.

## Research conclusion

The experiments improved training-only validation results but did not overcome
the official train/test distribution shift. A defensible 99% claim is not
supported by the current evidence. Repeated tuning against the known test file
would create test-set overfitting and is prohibited.

The next valid research step is to obtain and validate an independent
microservice-security dataset, or collect a versioned project-specific flow
dataset, then use it for domain adaptation and external generalization evidence.
That dataset must remain separate from UNSW-NB15 and must have documented
provenance, license, schema, collection conditions, and an untouched test split.

## Training-only ensemble follow-up

A fixed probability ensemble (90% XGBoost and 10% balanced Random Forest, with
threshold 0.565) passed the predeclared recall and false-positive gates on three
independent training-only splits. Validation accuracy ranged from 95.81% to
96.01%, macro-F1 from 95.19% to 95.42%, attack recall from 96.63% to 96.96%,
and false-positive rate from 5.90% to 6.00%.

This is the strongest stable training-only candidate so far. It is intentionally
not evaluated on the official test partition in this iteration because that
partition has already been used for several historical model comparisons.
Repeatedly testing new candidates against it would bias the research result.

## Machine-readable evidence

- `ml/artifacts/random-forest-validation-error-analysis-v1.json`
- `ml/artifacts/extra-trees-validation-sweep-v1.json`
- `ml/artifacts/xgboost-tuning-validation-sweep-v1.json`
- `ml/artifacts/xgboost-feature-selection-validation-v1.json`
- `ml/artifacts/xgboost-select60-repeated-seed-confirmation-v1.json`
- `ml/artifacts/xgboost-select60-frozen-final-evaluation-v1.json`
- `ml/artifacts/xgboost-attack-family-weighting-validation-v1.json`
- `ml/artifacts/xgboost-family-weighted-repeated-seed-confirmation-v1.json`
- `ml/artifacts/xgboost-family-weighted-frozen-final-evaluation-v1.json`
- `ml/artifacts/hist-gradient-boosting-validation-sweep-v1.json`
- `ml/artifacts/hist-gradient-boosting-repeated-seed-confirmation-v1.json`
- `ml/artifacts/hist-gradient-boosting-frozen-final-evaluation-v1.json`
- `ml/artifacts/rf-xgboost-ensemble-validation-v1.json`
- `ml/artifacts/rf-xgboost-ensemble-repeated-seed-confirmation-v1.json`
