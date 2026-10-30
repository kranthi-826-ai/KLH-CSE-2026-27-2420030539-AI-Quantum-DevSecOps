# Phase 7 DevSecOps Gates

Every push and pull request to `main` runs independent, least-privilege jobs:

- the complete Java 21 Maven reactor;
- Python dependency auditing plus AI-service API and model tests;
- React tests, production build, and high-severity npm audit;
- full-history secret scanning with Gitleaks;
- high/critical dependency, secret, and configuration scanning with Trivy.

Dependabot checks Maven, npm, pip, and GitHub Actions weekly. Updates remain pull
requests so test evidence is reviewed before promotion. CI receives read-only
repository permissions and no application/database secrets because all tests use
isolated H2 databases or mocks.

Security gates are intentionally fail-closed. A detected secret or unfixed
high/critical issue blocks the workflow and must be reviewed rather than silently
ignored.

The Java service POMs pin patched Jackson, Tomcat, and FreeMarker maintenance
versions because the initial scan found fixed 2026 advisories in the versions
managed by Spring Boot 4.1.1. The Maven cache is populated before Trivy runs so
the gate does not depend on repeated Maven Central metadata requests.
