# Research Paper Library Manifest

The local paper library is stored in `docs/research/papers/`. PDF files are intentionally excluded from Git to avoid repository bloat and accidental redistribution. This manifest is the tracked source index. SHA-256 hashes identify the exact local copies used by the project.

| ID | Phase | Local filename | Year | SHA-256 |
|---|---|---|---:|---|
| P01 | Adaptive policy | `01-adaptive-encryption-risk-based-selection-2026.pdf` | 2026 | `9703A874BAB9D134D19F76758D577594822036AB1E66AFDDA5653B0077DFA5C8` |
| P02 | AI intrusion detection | `02-sageconv-gnn-transformer-ids-2026.pdf` | 2026 | `E65DC26DCD88B48DB0CD1D394A928E81483F94457A4F6C5B0ACEC468377351A6` |
| P03 | Microservice IDS and dataset | `03-microservice-ids-benchmark-dataset-2024.pdf` | 2024 | `36C65C0A72E5290C12738492D8F6C1760BBB16A0C534DAE1EB15B5DC260407BC` |
| P04 | Authenticated PQC communication | `04-authenticated-ml-kem-ml-dsa-session-protocol-2026.pdf` | 2026 | `CF19B684456D157CDCCB968522E03D31B232EE0D5757092E12F35FEAB82CEDF1` |
| P05 | DevSecOps and service mesh | `05-nist-devsecops-microservices-service-mesh.pdf` | 2022 | `1B5F3E1E4FC8C782A1E55795898048B5991BB71D067F417BAD41D8378C03FB25` |
| P06 | API Gateway and microservice security | `06-api-gateway-microservices-security-2024.pdf` | 2024 | `0E646847E887F9F8D9FBAEA4918F081362739FEE30ED4ACCBCC7A3904922723C` |
| P07 | ML-KEM standard | `07-nist-fips-203-ml-kem.pdf` | 2024 | `19846B626E6F8F625AF08A70B9046687419C866523FFE7C144D7A0BF69F4E786` |
| P08 | Quantum-resilient enterprise architecture | `08-quantum-resilient-enterprise-cloud-2025.pdf` | 2025 | `4EDE901B54180350C88D17A428F01A4010BDD872F57CEC4A2C284D39E481B861` |
| P09 | IDS feature selection | `09-feature-selection-network-ids-2024.pdf` | 2024 | `05EDEF461D4688B4D14C6961828CE896BF74D77CE3622BEBFF7159537065C4E9` |
| P10 | Explainable AI intrusion detection | `10-explainable-self-attention-ids-2025.pdf` | 2025 | `5BECD23911BF4EB07249760072365CC943B50886D54667036BFA7E429772634B` |
| P11 | Enterprise-cloud PQC migration | `11-pqc-readiness-enterprise-cloud-2026.pdf` | 2026 | `6E58A6D6741E694709E512ACA38D13CBCE86536FFBFF07FEEEF0423FB2C0AD34` |

## Dataset decisions

October 23 source review: P05's unchanged retained PDF is final NIST SP
800-204C, March 2022, not the previously indexed 2021 year. The filename and
SHA-256 are unchanged. See `literature-review-2026-10-23.md` for the remaining
six source reviews and all-eleven manuscript coverage.

- Primary ML benchmark: official predefined `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` partitions.
- Microservice-specific benchmark: evaluate the dataset associated with P03 after its license, schema, size, and download source are verified.
- System-specific evaluation: project-generated authentication, API, authorization, and monitoring events remain a separate versioned dataset.
- Optional external generalization test: TON_IoT, only after the primary experiment is reproducible.

Raw datasets, transformed datasets, trained model binaries, and local research PDFs must not be committed.
