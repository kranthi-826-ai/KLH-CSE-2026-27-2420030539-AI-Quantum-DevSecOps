# Phase 3 Literature Matrix

October 23 update: the remaining retained sources are reviewed in
`literature-review-2026-10-23.md`. The expanded manuscript cites all eleven
retained sources, plus five supporting standards/dataset records. P05 is the
final March 2022 SP 800-204C. Historical project-extension proposals below are
not claims that every proposed capability has been implemented.

October21review:see `literature-review-2026-10-21.md` for page-specific checks of
P01/P02/P03/P04/P06 and manuscript comparisons. The P01headline below describes
only27designed scenarios; its separate CSIC2010 held-out result is lower. Do not
present any row as a matched replication or use unreviewed historical rows as
newly verified evidence.

This matrix records what each source contributes to this project. Reported paper
results are **not** directly comparable unless the dataset, split, labels, and
preprocessing are identical. Our results will be entered only after the
reproducible experiment pipeline has run.

## Core research papers

| ID | Scope and method | Dataset / evaluation | Reported result | Limitation relevant to our work | How this project extends it |
|---|---|---|---|---|---|
| P01 (2026) | Risk-based dynamic encryption selection for web applications | Scenario-based experiments on three hardware platforms | The paper reports 100% decision accuracy for its best evaluated configuration | Rule/scenario accuracy is not network-intrusion accuracy; web framework rather than distributed Java services; no standardized PQC migration benchmark | Combine measured AI risk, compatibility, sensitivity, and latency in an auditable microservice policy engine |
| P02 (2026) | SAGEConv-GNN plus Transformer intrusion detector | UNSW-NB15 and CIC-IDS2017; up to about 100,000 flows; five random seeds | UNSW-NB15: accuracy 0.9841, macro precision 0.9684, macro recall 0.9818, macro F1 0.9749 | Subsampled graph construction and a different experimental protocol prevent direct comparison with the official full predefined split | Establish reproducible classical baselines on the official split, then evaluate a justified candidate under identical preprocessing |
| P03 (2024) | Benchmark, dataset, and IDS case studies for microservice applications | Dedicated microservice workload and attack benchmark | Multiple detectors/case studies; no single universal accuracy target | Dataset/license/schema portability must be verified before adoption; environment differs from our Spring system | Keep public network benchmarking separate from project-generated microservice events and later test cross-domain behavior |
| P09 (2024) | Binary Levy-opposition equilibrium optimization for feature selection | NSL-KDD, UNSW-NB15, CIC-IDS2017; KNN, random ten-fold evaluation and repeated optimization | UNSW-NB15: 97.6% accuracy and reported 100% precision with 10.8 features on average | Different protocol; average feature count is not a literal fractional input; no matched reproduction here | Compare representations under fixed independent evaluation rather than assuming superiority |
| P10 (2025) | Self-attention IDS with SHAP/LIME explanations | IoT datasets plus UNSW-NB15 generalization experiment | 97.9% accuracy on UNSW-NB15; 99.3% and 99.6% on the primary IoT datasets | Cross-dataset headline accuracy is not sufficient for our class imbalance and deployment questions | Add reproducible split control, per-class results, inference latency, and explanations used by policy decisions |
| P04 (2026) | Authenticated session protocol using ML-KEM and ML-DSA | Protocol implementation and cryptographic/performance analysis | Security and performance results rather than IDS classification accuracy | Does not provide AI-driven mode selection or a distributed application control plane | Use standardized PQC primitives behind a later crypto-agility interface selected by the policy engine |

## Architecture and standards sources

| ID | Contribution | Project use |
|---|---|---|
| P05 | NIST guidance for DevSecOps, microservices, and service mesh | Phase 7 security controls, deployment, and operational boundaries |
| P06 | API-gateway security patterns for microservices | Gateway enforcement, routing, authentication boundary, and request controls |
| P07 | NIST FIPS 203 specification for ML-KEM | Normative algorithm and parameter requirements for Phase 5; not an ML accuracy source |
| P08 | Enterprise/cloud quantum-resilient architecture and harvest-now-decrypt-later risk | Migration motivation and architecture requirements |
| P11 | Enterprise/cloud PQC readiness and migration positioning | Crypto inventory, staged migration, compatibility, and governance considerations |

## Comparison rule

The project does **not** promise to exceed a paper's percentage merely because
its reported number is lower. A valid improvement claim requires the same task,
dataset version, split, preprocessing, label definition, and metric calculation.
The primary comparable experiment will use the official UNSW-NB15 predefined
training and testing files. We will optimize on a validation partition created
only from the official training file and evaluate the held-out official test
file once per finalized candidate.

## Research questions

1. Which laptop-feasible model gives the best macro F1 and attack recall on the
   official UNSW-NB15 split without unacceptable false-positive rate or latency?
2. Does leakage-safe feature selection improve macro F1 or inference latency
   compared with the same model and split using all eligible features?
3. How well does the selected public-dataset model transfer to separately
   collected project microservice events?
4. Can an explainable risk score drive classical, hybrid, and PQC policy choices
   while keeping service latency and resource overhead measurable?

## Evidence status

- Values above are author-reported values extracted from the local PDFs.
- `docs/research/papers-manifest.md` identifies the exact local copies by hash.
- Our target is a measured, reproducible improvement over our own fair baseline;
  any paper-to-project superiority claim remains **pending experimental proof**.
