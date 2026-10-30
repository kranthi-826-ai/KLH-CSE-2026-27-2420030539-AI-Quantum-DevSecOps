# CICIoT2023 Supporting Study Plan

## Role in this project

CICIoT2023 is a supporting network-threat dataset, not the complete adaptive
PQC system dataset. It covers transferable threats including DDoS, DoS,
reconnaissance, brute force, spoofing, Mirai, and malicious web traffic. Our
project contribution begins after detection: risk scoring, policy selection,
classical/hybrid/PQC execution, enforcement, and auditable monitoring.

## Frozen study sequence

1. Acquire the official extracted CSV features and record provenance.
2. Validate schema, labels, missing values, non-finite values, counts, and hashes.
3. Audit duplicates and capture-group leakage before defining a split.
4. Freeze binary and multiclass tasks, metrics, seeds, search budget, and gates.
5. Establish simple baselines before tuning advanced candidates.
6. Select using training-only validation and evaluate the untouched test once.
7. Report accuracy, macro-F1, per-class recall, false-positive rate, ROC-AUC,
   PR-AUC, confusion matrices, inference latency, and uncertainty.
8. Keep these results separate from the 2024 microservice-runtime study.

## Research-integrity constraints

- Do not directly merge CICIoT2023, UNSW-NB15, or microservice system-call rows.
- Do not describe laboratory benchmark accuracy as production accuracy.
- Do not optimize against the untouched test split.
- Preserve unsuccessful experiments and disclose all test-set exposure.
- Cite the official paper using DOI `10.3390/s23135941`.

## Advancement gate

Training begins only after the validation artifact confirms the downloaded
source, schema, labels, hashes, and a defensible split strategy.

## First executed protocol: ciciot2023-pilot-v1 (2026-10-19)

Audited local intake: 309 files, 46,776,700 observations, 39 numeric features,
and 34 labels. Label identity is encoded in per-attack filenames, rather than a
label column. The observed corpus contains 1,098,191 benign observations and
45,678,509 attack observations. SHA-256 hashes are recorded per file. The audit
found 1,449 missing cells and 1,037 infinite cells; these are cell counts and
must not be reported as counts of unique invalid rows.

### Partition and sample rules frozen before training

- Seed: 20261019.
- For labels with four or more source files, order files by the SHA-256 of
  seed plus filename. Reserve one file each for test, validation and calibration;
  remaining files supply training observations.
- For labels with fewer files, use contiguous 60/10/15/15 percent row ranges in
  each file for train/calibration/validation/test respectively. These share a
  source capture and cannot establish unseen-capture generalization.
- Cap each attack subtype at 6,000 train, 1,000 calibration, 1,500 validation,
  and 1,500 test observations. Benign caps are 60,000/12,000/12,000/12,000.
- Sampling uses deterministic random priorities within each label/partition.
- Exclude rows with missing or non-finite numeric features. Model input is
  float32. Detect exact duplicate/conflicting model-input vectors in the pilot
  using feature hashes. Remove ambiguous vectors and keep nonconflicting shared
  vectors in only one partition, with test then validation then calibration then
  training priority. The raw files are preserved.
- Save source allocation, feature list, per-label counts, output hashes and
  exclusions before model fitting. All source checksums are rechecked on intake.

### Predeclared pilot models and selection

Binary baselines: majority predictor, balanced Random Forest (160 trees,
maximum depth 20, minimum leaf size 2), and XGBoost (220 trees, maximum depth 6,
learning rate 0.07). XGBoost uses minimum child weight 4, subsample and feature
sampling 0.85, L1 penalty 0.05 and L2 penalty 2. Four workers bound CPU use.

For each model, calibration chooses a threshold from 0.10 to 0.90 in 0.01
increments to maximize macro-F1 subject to false-positive rate at most 5% and
attack recall at least 95%. If none qualifies, retain threshold 0.5 and mark
the candidate ineligible. Evaluate each fixed candidate once on validation.

A separate XGBoost baseline predicts eight broad categories: Benign, BruteForce,
DDoS, DoS, Mirai, Recon, Spoofing and Web-based. It uses 160 trees, depth 6,
learning rate 0.07, minimum child weight 4, subsample/column sample 0.85 and L2
penalty 2. Report all category recalls and macro-F1. Binary detection alone does
not demonstrate attack-family identification.

### What these results can support

These are pilot validation results on a capped sample. Class prevalence differs
from the full corpus. Whole source files may themselves be fragments of the same
original capture, and source-file holdout cannot prove independent captures.
Duplicate removal covers the pilot, not a complete corpus duplicate census.
The frozen test files stay unopened by the model-selection script. Candidate
models are saved separately and are not automatically deployed.

## Study closure2026-10-20

The bounded pilot's final reserved-test evaluation is complete under
`ml/training/evaluate_frozen_ciciot2023.py`. Both saved binary baselines fail
the security gates; none is promoted. See `ciciot2023-final-results.md` for
final metrics and limitations. The test is now exposed and cannot be reused
as untouched evaluation for later optimization. This does not claim full-corpus
training or production acceptance.
