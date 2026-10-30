# UNSW-NB15 Data Acquisition

Use only the official UNSW-NB15 source linked from:

<https://research.unsw.edu.au/projects/unsw-nb15-dataset>

The university page documents academic-use permission, required citations,
features, attack families, and the official predefined split. Download these
exact files and place them locally as follows:

```text
ml/data/raw/unsw-nb15/
|-- UNSW_NB15_training-set.csv
`-- UNSW_NB15_testing-set.csv
```

Expected counts from the official page:

- training: 175,341 rows
- testing: 82,332 rows

Do not rename training as testing, merge the files before evaluation, or upload
the dataset to Git. Run `validate_unsw_nb15.py` immediately after download; its
SHA-256 output becomes the provenance record for the exact files used.

## CICIoT2023 acquisition

Use only the official Canadian Institute for Cybersecurity page:

<https://www.unb.ca/cic/datasets/iotdataset-2023.html>

For the first ML study, download the extracted-feature `CSV` directory rather
than the much larger PCAP collection. Place its files under:

```text
ml/data/raw/ciciot2023/CSV/*.csv
```

The official download requires the CIC statistical-information form. Never put
personal form information, credentials, or raw dataset files in Git.

After downloading, run:

```powershell
.\ml\.venv\Scripts\python.exe .\ml\data\validate_ciciot2023.py
```

The validator streams the files, checks schema and labels, records missing and
non-finite values and SHA-256 hashes, and saves local evidence under
`ml/artifacts/`. It does not create a random row split; we will freeze the split
only after auditing the source-file organization to reduce capture leakage.

The observed 309-file release uses 39 numeric features and attack-specific
filenames. Its labels are recovered using an explicit taxonomy; unknown names
fail validation. Labeled CSV files are also supported by the validator.

Pilot preparation and baseline training:

```powershell
.\ml\.venv\Scripts\python.exe .\ml\data\prepare_ciciot2023_pilot.py
.\ml\.venv\Scripts\python.exe .\ml\training\train_ciciot2023_pilot.py
```

These scripts refuse to overwrite existing frozen evidence. Pilot preparation
streams the corpus, samples bounded per-label partitions, removes non-finite
rows and exact duplicate/conflicting feature vectors within the pilot, and saves
the split manifest. Training opens train, calibration and validation only.
See `docs/research/ciciot2023-study-plan.md` for interpretation limits.

## 2024 SocialNetwork microservice syscall release

The downloaded SocialNetwork subset is stored separately from network-flow
datasets. Its syscall observations are not interchangeable with CICIoT2023 or
UNSW-NB15 features. Release identity and interpretation are documented in the
research library; recordings and publication year are different dates.

```text
ml/data/raw/microservice-ids-2024/socialnetwork/
|-- SocialNetwork-training-data.zip
|-- SocialNetwork-validation-data.zip
|-- SocialNetwork-attack-data.zip
`-- README.md
```

To copy the four publisher files from Downloads without deleting originals:

```powershell
.\scripts\import-socialnetwork-dataset.ps1
.\scripts\inspect-socialnetwork-local.ps1
```

The importer validates publisher MD5 checksums, compares source/destination
SHA-256 values, refuses conflicting existing files, and creates a unique import
manifest in `ml/artifacts/`. Raw files stay compressed and Git-ignored. Do not
extract the entire nested release blindly. The inspector inventories archives
and decodes bounded validation prefixes; it does not score held-out attacks.
Use `-OutputManifest` for a new inspection record rather than overwriting one.

Historical experiments retain their original source paths and hashes. Moving
the source location is not a new training experiment or an accuracy improvement.
Preserve scenario/recording/CVE separation, exposure-label limitations, and all
failed results. See `docs/research/socialnetwork-temporal-study-v1.md` before
further experiments. Independent attack scenarios must not be used for tuning.
