# Exported paper review October21

User confirmed export. The two recent Downloads files `document.pdf` and
`document (1).pdf` are byte-identical. The latter was inspected completely:
four rendered pages,body text,tables,equations,author block and references.
PDF SHA256:53525d4a19878924bc55d7a0a70c0e1a2e5f5ef839b7af5d1f4f664fd4edb69a.
Evidence/rendered pages and preserved export are in
`ml/artifacts/paper-pdf-review-v1/`; user originals were not changed.

## Findings and source changes

- The exported paper uses Letter dimensions. The supplied Word format declares
  A4(595.30by841.90points),Times New Roman and18point body-column spacing.
  Source now requests A4,Times-compatible mathptmx and explicit margins/spacing
  derived from template XML. Exact font/layout fidelity remains unverified.
- Visible prose contained missing spaces:seed42,with39,remain0.5,detects40/51,
  receives403 and similar joins. Source corrections separate these tokens and
  clarify HTTP status wording without changing measured results.
- Page4contains only references10/11. Source now enables bibliography balancing;
  a fresh export must establish whether the almost-empty last page improves.
  Do not claim a new page count before reviewing the new PDF.
- First-reference numbering skipped ahead because the standards appeared later
  in the text. The introduction now cites the two standards alongside the
  cryptographic scope,so initial citation order matches bibliography numbering.
- The old table floats appear before their local discussion. Placement remains
  a review item for the next export rather than a claim of exact template fidelity.

The revised source compiled successfully with the desktop editor's compiler.
Source preflight passes,168-word abstract and eleven defined references; receipt
`ml/artifacts/paper-preflight-f86ba5133653480b9e81e42836ce37ac/verification.json`.
No revised PDF has yet been exported or visually checked. The earlier four-page
review does not validate a changed source or prove Word-template agreement.

Only paper exports were found. No PDF export of the supplied Word template or
legacy DOC sample was identified. The legacy sample is confirmed OLE binary DOC,
not a renamed DOCX. Template geometry/font inspection used its actual DOCX XML;
it is not a substitute for rendered comparison. No native Word/LibreOffice or
browser-security bypass was attempted. No plagiarism report is established.
