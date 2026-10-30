# CICIoT2023 bounded study: final reserved-test results

Completed2026-10-20. Training, calibration, development experiments and the
single reserved-test evaluation of the saved pilot baselines are now complete.
This closes the predeclared BOUNDED PILOT, not full-corpus training or production
acceptance. The309-file/46,776,700-row corpus was audited, but the models were
trained on230,242 prepared rows, not all46.8million observations.

## Frozen evaluation

Original split: train230,242; calibration40,354; validation54,597; test54,552.
Test contains12,000 benign and42,552 attack observations. Feature count39.
Split/cleaning limits remain those in `ciciot2023-study-plan.md`: capped
sampling, source-file holdout or contiguous ranges for labels with few files,
pilot duplicate/conflict exclusion. Capture independence is not established.

Saved original RF, XGBoost and eight-category XGBoost bundles were frozen by
SHA-256, feature schema, manifest, evaluation/helper-code hashes and thresholds
BEFORE test loading. All binary thresholds remain0.5. No fitting, threshold
search or candidate selection used test outcomes. A persistent exclusive
test-started marker prevents reruns/overwrite, including after failed attempts.
Original validation eligibility remains false; final scoring cannot override it.
Later rejected internal capacity/family/hard-example studies remain documented
negative development evidence, not additional final-test candidate searches.

| Binary model | Test accuracy | Macro-F1 | Attack recall | False-positive rate | Confusion matrix TN/FP/FN/TP |
|---|---:|---:|---:|---:|---|
| RF |88.510% |0.85350 |86.506% |4.383% |11,474 /526 /5,742 /36,810 |
| XGBoost |90.396% |0.86801 |91.399% |13.158% |10,421 /1,579 /3,660 /38,892 |

Neither meets both95% attack recall and5% false positives. Neither is promoted
or automatically deployed. Accuracy alone hides the unacceptable misses or
false alarms. Always predicting attack would itself score78.0026% on this
sample while flagging every benign observation; the full raw corpus has a
different, even more attack-heavy prevalence.

Selected XGBoost binary subtype recalls: DictionaryBruteForce81.84%,
Recon-PortScan63.57%, SqlInjection66.75%, XSS84.03%, CommandInjection91.09%.
These are detection recalls, not correct subtype identification. Several
flooding types reach100% in this sample, which does not establish universal
flood detection or real-world robustness.

The separate eight-category classifier achieved80.140% accuracy and0.73903
macro-F1. Category recalls: Benign95.58%, BruteForce45.33%, DDoS93.90%,
DoS66.14%, Mirai99.42%, Recon41.93%, Spoofing79.19%, Web-based41.94%.
Its full confusion matrix and classification report are in the local result.

## Honest closure and transition

The experiment is complete; the security target was NOT achieved. This is a
valid negative result, not permission to change thresholds after test exposure
or claim99%. Do not compare directly with papers using different data splits,
feature sets or class prevalence. Previously reported90.90% is validation;
90.40% here is the final bounded-test accuracy for saved XGBoost.

The test is now exposed. Any future CICIoT optimization requires a new protocol
and genuinely independent final data rather than repeated tuning on this test.
The existing promoted UNSW model remains unchanged. CICIoT features must not be
concatenated blindly with microservice syscall/HTTP datasets. Next dataset work
can resume from the separately recorded2024 SocialNetwork development studies
and pending causal-history plan, subject to the user's usage budget.

## Evidence and reproduction

Evaluator: `ml/training/evaluate_frozen_ciciot2023.py`, separate `freeze` and
`evaluate` modes. Frozen plan, one-shot marker and complete results:
`ml/artifacts/ciciot2023-frozen-final-v1/` (Git-ignored). Tracked summary:
`docs/research/evidence/ciciot2023-frozen-final-v1.json`. Original validation
artifacts are unchanged. Full ML suite95 passed, including repeat-evaluation
refusal checks. Checksum/CM/threshold audit independently verified final output.
Recorded final inference/report runtime1.55s excludes earlier training/intake.
Dataset attribution: Neto et al., Sensors2023, DOI10.3390/s23135941, with the
existing bibliography entry in `dataset-references.bib`.
