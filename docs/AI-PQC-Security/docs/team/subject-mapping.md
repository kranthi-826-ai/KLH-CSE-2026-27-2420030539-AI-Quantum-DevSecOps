# Academic subject mapping

Verified27 October2026 from user-supplied handouts,first three PDF pages,
including course titles,syllabus and course outcomes. Title pages visually
inspected. SOA expansion is directly confirmed by the user.

| Subject | Exact course title | Course code |
|---|---|---|
| IAS | Information Assurance and Security |24CS3105|
| SOA | Service Oriented Architecture |Not supplied|
| ASE | Adaptive Software Engineering |24CI3201|
| CACD | Cryptanalysis and Cyber Defence |24CSB3101|

These supersede earlier assistant guesses. ASE is NOT Advanced Software
Engineering. CACD is NOT Cloud Architecture and Cloud Deployment.

## IAS

- CO1 symmetric encryption: AES-256-GCM protects the payload.
- CO3 integrity/authentication: payload fingerprints,signature generation and
  verification,authenticated encryption. Exact deployed algorithms differ
  from some examples in the syllabus; do not claim every listed algorithm.
- CO4 intrusion detection/access protection: trained network risk inference,
  JWT/role checks,security-event monitoring and bounded authentication throttling.
- Keys/signatures currently support local envelope round trips,not independently
  authenticated remote recipients or a complete firewall/security certification.

## SOA

Auth,Business,AI Security,Adaptive Policy and Monitoring services expose defined
APIs. API Gateway routes requests; Eureka supports discovery. Responsibility
separation,contracts and service interaction demonstrate SOA through microservices.
Discovery does not establish trust,and integration does not prove plug-and-play
compatibility with every external application.

## ASE

- CO1: documented requirements and phased iterative engineering; formal Scrum
  ceremonies/Jira usage are not established merely by incremental development.
- CO2: Git,build/test scripts and configured GitHub Actions workflow; configuration
  is not evidence of a current successful hosted CI or production deployment.
- CO3: request/decision validation,secret configuration,access checks,fail-closed
  behavior,security tests and Prometheus operational monitoring.
- CO4: separate data preparation/training/evaluation,MLflow tracking,model/schema
  hashes,inference service and controlled candidate promotion/rejection.
- CO5: team guide and suggested presentation responsibilities support collaboration;
  do not claim completed peer reviews without records.
- Docker/cloud/DevOps topics belong here in these handouts,not under CACD.
  Public cloud production acceptance remains incomplete. Do not claim SageMaker,
  Azure ML,Vertex AI,DVC,Trivy or other syllabus tools solely because listed.

## CACD

- CO1/CO2: practical AES-GCM encryption/decryption and block-cipher-mode concepts;
  not implementation of every historical cipher in the syllabus.
- CO3: X25519 key agreement and classical signatures,extended with ML-KEM/X-Wing
  and ML-DSA for PQC research.
- CO4/CO5: hashes,authenticated encryption,signature checks and local envelopes.
- Existing tamper-rejection tests,unknown-profile rejection and HIGH/classical
  refusal evaluate defensive behavior. They do not constitute new cryptanalysis
  of AES,successful cipher breaking,or verified quantum-attack resistance.
- Controlled invalid-login/traffic research is not a completed Nmap/Metasploit/
  Wireshark/Burp/SQL-injection/XSS/MITM assessment. Such lab work needs its own
  explicit scope and evidence; no antivirus/security disabling is required.

## Sources

- IAS: `C:/Users/ykran/Downloads/ias.pdf`,pp1–3.
- CACD: `C:/Users/ykran/Desktop/CACD/co1/Handout CACD Final.pdf`,pp1–3.
- ASE: `C:/Users/ykran/Downloads/ase.pdf`,pp1–3.
- Local extraction/checksums: `ml/artifacts/course-handouts-2026-10-27/`.
- Implementation spot-check: policy rules,crypto profile factory/tests,business
  request/response contracts,`.github/workflows/ci.yml`,ML promotion scripts.
- No source handout,application runtime,research result or open paper was edited.
