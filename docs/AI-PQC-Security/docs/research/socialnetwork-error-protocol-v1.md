# Generic syscall-error ablation protocol

Declared2026-10-20 before feature-cache preparation/model scoring. Development
only; this is not an independent test or a plan to relabel the hard recording.

The targeted context audit found process execution/mount activity in the first
CVE-2022-0492 recording but no such entry calls on either observed worker during
the second recording's annotated interval. Keep all original labels and misses.
An interval annotation does not establish successful exploitation in every second.
Do not use CVE-specific strings or post-interval data to fabricate positive features.

Hypothesis: generic reported syscall errors may describe failed or stressed
operations that the29 base features do not distinguish. Add50 features: total
reported negative results, fraction of exits with a reported error, normalized
frequencies for16 predeclared numeric error codes, and32 hashed syscall/error-pair
frequencies. Only the leading `res=`/`fd=` field on exit records is eligible;
payload/command text is never interpreted as a return code or stored as input.
This does not claim to parse every possible kernel error representation.

Preserve all557 original development observations, their order, labels and29
base feature values. Reconstruct only the same16 scenario5/plain_workload
development recordings, both workers. Raw context uses the existing bounded
streaming helper; selected features use the current completed one-second window
only. No future context, IDs, timestamps, role/CVE strings or arguments enter ML.

Compare29-feature matched baselines to79-feature augmented inputs using the
same three fixed recipes: balanced logistic C0.5, RF128/depth4/leaf2, XGBoost128/
depth2/learning-rate0.05/min-child3/lambda4. Preserve the exact fixed seed and
sample order. Eight leave-one-CVE-out folds hold both recordings together;
threshold0.5 is fixed. Baseline results must reproduce the temporal study's
saved base metrics before any new result is accepted.

Eligibility remains >=95% exposure recall, <=5% matched-control alarms and
macro-F1 no worse than the earlier base-logistic reference. Selected-control
class balance is artificial, so no headline accuracy is reported. If no candidate
passes, select none, retain the negative result and do not alter enforcement or
the promoted network model. A passing development candidate still needs a new,
frozen independent protocol and separate inference schema before any promotion.
No independent scenario or exposed CICIoT final test is opened by this study.

Code: `socialnetwork_error_features.py`, `prepare_socialnetwork_errors.py`,
`study_socialnetwork_errors.py`. Output paths are exclusive; plans/hashes are
written before fitting, and this protocol/code is committed before scoring.
