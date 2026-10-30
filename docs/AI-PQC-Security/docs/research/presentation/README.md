# Project execution review presentation

Latest revision: `output/AI-PQC-review-v2.pptx` includes the confirmed first
author Yellanki Kranthi Giri Venkata Chary and email on its title slide. Full
department/institution/address details appear in title-slide speaker notes and
the IEEE paper author block. Other authors/guide await user confirmation.
V2finalizer checks pass. The changed cover was visually inspected; renders of
slides2–12 are byte-identical to the previously inspected version. V2SHA256:
`eaccc5a20d0b1e3b6606c773b64376a8a5e0e42af7298dd7515d87227b3e1e83`.
V2receipt/previews:
`ml/artifacts/review-presentation-v2-2cbf240a-a731-4b11-bcec-594bba544d85/`.
The builder accepts REVIEW_DECK_REVISION (for example v3) and creates a fresh
private build directory, preserving earlier final files and validation evidence.

## Original preparation version

Deliverable: `output/AI-PQC-review-v1.pptx`,12editable slides,16:9.
Prepared October21,2026 for the project review. Author/college/guide details
remain unconfirmed and are omitted rather than invented. This is a reviewed
preparation version, not evidence that all project requirements are complete.

Contents: system purpose,seven services,adaptive request sequence,crypto profile
table,model score versus policy risk,dataset separation,held-out network results,
application-specific experiments,persistence failure semantics,verification
evidence and demonstration/remaining work. Six tables remain native editable
objects. Source citations and qualifying explanations are in speaker notes.

Every slide was rendered and individually visually inspected at1280x720.
Finalizer checks passed:12slides,sixrequired native tables,no package/layout
findings,Arial font policy and first-party round-trip import. Final SHA256:
`154a3ec8b6bd53d482ab46e5db78f3291b976507c028da82690888c33722a511`.
Evidence/previews: `ml/artifacts/review-presentation-v3/validation.json` and
`slide-01.png` through `slide-12.png`. The deck was not opened in native PowerPoint;
render/import checks do not prove native application behavior or accessibility.

Initial build1 retained the tool's Aptos default because the source used an
unsupported fontFamily property. Build2 corrected theme/typeface but failed
import validation because a required runtime module environment path was absent.
Build3 sets that inherited runtime path and passes all gates. Failed candidates
and logs remain in ignored local artifacts; only the validated deck is delivered.

Builder: `scripts/build-review-presentation.mjs`, using bundled artifact-tool.
Set REVIEW_RUNTIME_MODULES, REVIEW_RUNTIME_PYTHON and REVIEW_PRESENTATION_SKILL
from `load_workspace_dependencies` and the installed presentation skill, then run
with that bundled Node executable from project root. The builder refuses to
overwrite its final file; use a new revision/output filename for subsequent edits.
Do not substitute project Node dependencies or install presentation packages.

The presentation intentionally retains rejected model results and distinguishes
software checks from classification accuracy. It does not promise99%accuracy,
zero false alarms,production PQC transport,publication acceptance or a similarity
score. The paper and real plagiarism report remain separate deliverables.
