# Remaining retained literature and manuscript coverage

The October 21 review covers P01/P02/P03/P04/P06. This supplement directly
inspects the remaining six retained PDFs. All six SHA-256 values match
`papers-manifest.md`. Extraction remains local/Git-ignored under
`ml/artifacts/literature-supplement-2026-10-23/`; source PDFs are unchanged.
This is passage-level review, not independent reproduction or a systematic
review of all prior systems.

| ID | Inspected passages | Verified use / caution |
|---|---|---|
| P05 | PDF cover/title pages 1–2, abstract p4, introduction/code-type/lifecycle discussion pp11–14 | R. Chandramouli, final SP 800-204C, March 2022, DOI10.6028/NIST.SP.800-204C. Corrected manifest year from2021. Five code types motivate separating policy/observability/application validation; no conformance or C-ATO claim. |
| P07 | Title, abstract and announcement pp1–4 | FIPS203, published August13,2024; three ML-KEM parameter sets. Normative primitive specification, not detector performance or application/module certification. |
| P08 | Repository cover/title pp1–2 and architecture/method discussion p6 | M.V.Inakollu, Acta Sci.26(3),2025, DOI10.22178/acta.26.3.44, USF repository item161. Used as migration/crypto-agility context, not validation of its enterprise-analysis claims or predictions of quantum dates. |
| P09 | Abstract p1, method pp7–8, results/Table4 p11 | Z.Asghari Varzaneh/S.Hosseini, Scientific Reports14:18696,2024, DOI10.1038/s41598-024-67488-7. KNN k5, random ten-folds,20 optimization runs;97.6% UNSW accuracy and10.8 mean selected inputs. Different from official predefined binary split; no project superiority claim. |
| P10 | Abstract p1, representation/split p8, model p9, explanation/hyperparameters pp10–11; example explanation passages pp14–16 | K.P.Sharma et al., Scientific Reports15:39937,2025, DOI10.1038/s41598-025-23750-0. Reported99.3% BoT-IoT/99.6% N-BaIoT/97.9% UNSW. Random70/15/15 splits and different task/representations. Author-reported abstract figures only; do not treat explanation examples or printed table captions as independently reconciled experimental evidence. |
| P11 | Abstract/introduction pp1–2, planning estimator/results pp8–9 | A.Gupta/S.Mittal, Cybersecurity9:147,2026, DOI10.1186/s42400-026-00579-2. Exposure-risk planning under timeline assumptions; not classification accuracy, observed attack rates or a new cipher. |

The manuscript bibliography now contains16 entries. All11 retained sources
are cited in prose and mapped in TableI; remaining references are SP800-204A,
FIPS204, UNSW/CIC original data papers and the Zenodo microservice data record.
No numerical subtraction ranks our official test against a differently split
published model. No reproduced figures or copied source prose are used.

The 2024 microservice evidence review also includes the already completed
269-input expansion,305-input causal temporal study and exploratory execution
guard—not just the79-input generic-error study. Their negative outcomes are
retained. Further tuning on those same development windows is not justified
as an independent accuracy improvement. Independent scenarios remain unopened;
no model, training data or enforcement behavior changed in this paper revision.
