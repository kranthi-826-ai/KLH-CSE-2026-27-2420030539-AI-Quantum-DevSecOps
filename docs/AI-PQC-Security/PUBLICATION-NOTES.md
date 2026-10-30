# AI-PQC Security project snapshot

**AI-Driven Adaptive Quantum-Resilient Security Framework for Secure Microservice Architectures**

Added to this academic repository on 30 October 2026. Existing course files under the parent docs directory are preserved unchanged. This directory is a source/documentation snapshot, not a nested Git repository or a ready-to-run deployment image.

## Entry points

- [Project requirements and scope](docs/PRD.md)
- [Backend services](backend/)
- [Web dashboard](frontend/web-dashboard/)
- [AI and adaptive policy services](platform/)
- [Training and evaluation instructions](ml/README.md)
- [Research manuscript source](docs/research/paper/main.tex)
- [Reviewed 14-page paper](docs/research/paper/output/AI-PQC-research-paper-reviewed-v3.pdf)
- [Paper export review](docs/research/paper/pdf-review-v3-2026-10-29.md)
- [Team guide](docs/team/AI-PQC-Security-Team-Guide.docx)
- [Tests](tests/)

## Running and reproducibility

Use this directory as the working directory for the project's relative paths. Read the relevant service, database and ML setup documentation before starting the stack. Supply local secrets privately using the example configuration files; never commit actual passwords or keys. Model artifacts and raw datasets are intentionally absent and must be obtained/prepared under the documented protocol before inference/training can run. Generated dependencies, build products, experiment state and temporary downloads are also excluded.

Nested .github/workflows files are retained as original project source. GitHub will not automatically run workflows from this nested location; moving/adapting them into this academic repository's root .github/workflows directory is separate work.

The snapshot retains historical development notes. Some older README/phase descriptions predate later implementation; use the latest requirements, research results, receipts and paper review for current evidence boundaries. A passing local round trip is not universal attack prevention or production-wide quantum security. Similarity checks and venue-specific acceptance are not claimed.
