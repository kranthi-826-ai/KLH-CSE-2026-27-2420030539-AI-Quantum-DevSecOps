# SocialNetwork public dataset intake v1

## Provenance verified 2026-10-20

Source: [Microservice Intrusion Detection Dataset](https://zenodo.org/records/10655126),
DOI 10.5281/zenodo.10655126, Jose Flora and Nuno Antunes. Zenodo API publication
date 2024-02-13; license `cc-by-4.0`. Credit the creators, DOI and license and
identify transformations when publishing derivatives. This intake is the
SocialNetwork subset, not all three applications or the whole 900-hour dataset.
The inspected validation event timestamps/annotations are from June 2023:
publication year does not mean recording year.

All three downloaded ZIPs were read completely for MD5 verification and match
the publisher checksums. MD5 here verifies download integrity, not security.

| Archive | Publisher and local MD5 |
|---|---|
| SocialNetwork-training-data.zip | 85363b48faf0473199daf4184a8164d7 |
| SocialNetwork-validation-data.zip | b3b09bf1c63a8630b71c5c286847ca95 |
| SocialNetwork-attack-data.zip | d6bda4b15a56eb5a60bde69003a3cd6a |

Archives remain in the user's Downloads directory. No copies or whole-dataset
extraction were made. Approximately 178.7 GiB free was available at intake.
The 23.70 GiB of ZIP contents includes compressed tar files, which themselves
contain ZIP-compressed traces. One 69 MiB inner ZIP alone expands to an
approximately 848 MiB trace. Do not assume 23.70 GiB is the final extraction size.

## Observed structure and schema

- Training ZIP: one `collection-1.tar.gz` (about 14.70 GiB).
- Validation ZIP: scenarios 1, 3, 5 and 7, each with two collections and two
  worker-node trace archives per collection. All four tar inventories completed
  within a 512 MiB decompressed-tar limit each (46 headers each).
- Validation paths say `plain_workload` and `NO_attack_data`; six inspected
  experiment annotations explicitly state `Attack: NONE`. Scenario 7 did not
  expose a matching `*experiment.txt` annotation in the small-text selection;
  do not infer its label solely from the scenario number or Locust task name.
- Attack ZIP: scenarios 1, 3, 5 and 7. Only outer archive metadata and file
  integrity have been inspected: attack trace contents remain unopened.
- Trace prefix inspected: scenario 5 / plain workload / collection 1 / node 1.
  Fields: nanosecond timestamp, container name, thread ID, direction, category,
  syscall name, variable arguments. Eight lines were sampled without extraction.
- Locust summary task names can contain `attack_socialnetwork_mixed` even in
  explicitly attack-free collections. Task names are NOT attack labels.

## Training protocol requirements (not yet fulfilled)

1. Inventory training collections and obtain their workload/annotation evidence.
2. Implement streaming trace parsing and bounded feature aggregation; distinguish
   syscall-entry/exit semantics. Do not feed raw container/thread identifiers,
   absolute timestamps, paths/scenario names or label-bearing arguments to ML.
3. Preserve original training versus validation collections. Split calibration
   from training by collection/time with window boundary purging; no random
   event-level mixing across recordings or overlapping windows.
4. Normal-only calibration can set a false-alarm threshold; it cannot select
   attack recall or produce meaningful attack accuracy. A one-class baseline is
   appropriate only after verifying training normality and coverage.
5. Review attack annotation metadata separately from trace features, including
   timestamp/timezone alignment and affected container scope. Freeze feature
   recipe/model/threshold before any designated final attack evaluation. If
   attack development is needed, predeclare collection-level development and
   final groups BEFORE inspecting outcomes; never tune on the final group.
6. Report held-out attack recall, normal false-positive rate, macro-F1 and
   confusion matrices with recording-level uncertainty; never report all-normal
   validation correctness as intrusion-detection accuracy.

This dataset requires a separate syscall model, not direct concatenation with
UNSW-NB15, CICIoT2023 or the 24-feature routed HTTP model. Combining evidence
at policy level needs a separately validated integration. Current intake trains
no model, changes no promoted model and enables no enforcement.

## Reproduction and local evidence

`ml/data/inspect_socialnetwork_archives.py` accepts source directory and a fresh
output JSON path. `--metadata` scans validation metadata only. It refuses an
existing output; does no extraction; caps decompressed reads; only probes a
bounded trace prefix. `ml/artifacts/socialnetwork-inspection-v3.json` contains
the local inventory, raw sample and small annotations and is Git-ignored.
Earlier v1/v2 inspections are preserved as preliminary evidence. No raw trace,
token, model or dataset archive is included in this document or Git.
