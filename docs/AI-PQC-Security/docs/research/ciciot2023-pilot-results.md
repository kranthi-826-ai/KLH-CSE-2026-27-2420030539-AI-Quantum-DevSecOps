# CICIoT2023 first pilot results

Experiment date: 2026-10-19. Status: measured validation baselines; none promoted.

Update2026-10-20: the separate one-shot reserved-test evaluation is complete.
See `ciciot2023-final-results.md`. The figures below remain the original
validation results, not final-test scores. The reserved test is now exposed.

## Data and protocol

The local download was audited in full: 309 attack-specific CSV files,
46,776,700 rows, 39 numeric predictors, 33 attack subtypes and benign traffic.
SHA-256 checksums were recorded for every source. The label is derived from an
explicit filename taxonomy and is never included among the predictors.

There are 1,098,191 benign and 45,678,509 attack observations. An always-attack
predictor would achieve about 97.65% accuracy at this raw class prevalence, while
falsely flagging every benign observation. Headline accuracy therefore cannot
establish detector quality.

The audit found 1,449 missing cells and 1,037 infinite cells. Pilot preparation
excluded 1,040 unique rows with invalid numeric features. Random priorities cap
the sample per label; these results are not estimates for the complete corpus.

Source-file holdout is used for labels with at least four files; other labels
use disjoint contiguous row ranges. Source fragments may share an original
capture, so this does not prove generalization to independently collected data.
The full frozen rules appear in `ciciot2023-study-plan.md`.

Exact float32 feature hashes identify duplicate/conflicting inputs within the
bounded pilot. There were 1,123 ambiguous feature vectors associated with more
than one subtype; they were excluded. Remaining identical vectors are retained
in only one split. The pilot has zero shared feature hashes between splits;
this is not a full-corpus duplicate audit or a claim of capture independence.

| Partition | Rows | Benign | Labels represented |
|---|---:|---:|---:|
| Train | 230,242 | 59,955 | 34 |
| Calibration | 40,354 | 11,992 | 34 |
| Validation | 54,597 | 11,993 | 34 |
| Reserved test | 54,552 | 12,000 | 34 |

Reserved-test counts come from preparation metadata. The training script opens
train, calibration and validation only and never evaluates the reserved test.

## Binary validation

| Model | Accuracy | Macro-F1 | Attack recall | False-positive rate | ROC-AUC | Fit time |
|---|---:|---:|---:|---:|---:|---:|
| Majority predictor | 78.03% | 43.83% | 100.00% | 100.00% | 0.5000 | 0.11 s |
| Balanced Random Forest | 88.88% | 85.77% | 86.92% | 4.14% | 0.9682 | 16.93 s |
| XGBoost | 90.90% | 87.48% | 91.77% | 12.17% | 0.9682 | 4.83 s |

No calibration threshold from the predeclared 0.10-0.90 grid met both the 5%
false-positive ceiling and 95% attack-recall floor. Therefore, all binary models
are reported at the default 0.5 threshold and remain ineligible for promotion.

Per-attack binary recall measures whether an attack is flagged at all. It does
not mean the model correctly identifies its attack type.

| Attack subtype | RF binary recall | XGBoost binary recall | Validation support |
|---|---:|---:|---:|
| DDoS SYN flood | 100.00% | 100.00% | 1,452 |
| Dictionary brute force | 48.13% | 79.04% | 1,498 |
| Reconnaissance port scan | 56.74% | 71.23% | 1,491 |
| Command injection | 91.17% | 93.44% | 793 |
| SQL injection | 42.19% | 63.91% | 787 |
| XSS | 65.68% | 84.75% | 577 |

## Eight-category validation

A separate XGBoost classifier predicts the broad attack category. Accuracy was
77.56%, macro-F1 70.75%, and fit time 15.38 seconds.

| Category | Recall | F1 | Support |
|---|---:|---:|---:|
| Benign | 96.16% | 78.89% | 11,993 |
| BruteForce | 27.84% | 41.66% | 1,498 |
| DDoS | 88.17% | 86.58% | 17,742 |
| DoS | 52.94% | 56.09% | 5,844 |
| Mirai | 99.89% | 99.90% | 4,498 |
| Recon | 48.59% | 60.95% | 6,324 |
| Spoofing | 81.04% | 88.26% | 2,991 |
| Web-based | 45.00% | 53.68% | 3,707 |

## Interpretation and next experiment

The pipeline learns useful network patterns, but brute force, web attacks and
reconnaissance remain weaknesses. Raising overall accuracy alone would conceal
these missed attacks. The next controlled study should investigate family-aware
weighting and specialist detection using a fresh internal training subdivision,
calibrate thresholds on calibration only, and confirm a fixed recipe across
seeds before any reserved-test evaluation.

These results are not directly comparable with UNSW-NB15 or published CICIoT2023
results using different features, samples, labels or splits. They do not establish
microservice deployment performance or the quality of cryptographic policy
selection. Those require their own runtime and end-to-end experiments.

## Evidence and reproducibility

- Scripts: `ml/data/validate_ciciot2023.py`, `ciciot2023_common.py`,
  `prepare_ciciot2023_pilot.py`, `ml/training/train_ciciot2023_pilot.py`.
- Full audit: `ml/artifacts/ciciot2023-dataset-validation.json`.
- Frozen split manifest: `ml/data/processed/ciciot2023-pilot-v1/manifest.json`.
- Model results: `ml/artifacts/ciciot2023-pilot-validation-v1.json`.
- Candidate bundles: `ml/models/candidates/ciciot2023-pilot-v1/`.
- Seed: 20261019; parameters, environment and training-script hash are in JSON.
- Six dataset preparation tests passed. Source checksums are revalidated before
  preparation; partition checksums are validated before model fitting.
- Raw data, processed partitions and binaries remain local and Git-ignored.
- Dataset citation: Neto et al., Sensors 2023, DOI `10.3390/s23135941`;
  the BibTeX entry is in `dataset-references.bib`.
