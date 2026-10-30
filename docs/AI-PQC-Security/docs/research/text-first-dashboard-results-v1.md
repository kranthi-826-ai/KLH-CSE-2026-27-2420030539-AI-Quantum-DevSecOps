# Text first dashboard regression

Date: October 21, 2026.

Removed redundant decorative icon components, marker boxes, spinner definitions,
and workspace avatar from dashboard chrome. Kept labelled controls, keyboard
navigation, meaningful charts, protection meters and numbered decision steps.
Removed the unused Lucide dependency from the package manifest and lockfile.
Added responsive text-first layout overrides and two component regression tests.
The retained migration script emits patches only; it does not write source files.

Verification: `npm test -- --reporter=json
--outputFile=../../ml/artifacts/quiet-ui-tests-v3.json` completed with 102 tests
passed, zero failed. `npm run build` completed successfully with Vite 8.3.1,
28 transformed modules. A later edit removed whitespace-only blank lines;
`git diff --check -- frontend/web-dashboard` passed.

The initial v1 regression report is retained: 26 failures exposed one remaining
Eye component reference after removing its import. That reference was removed;
v2 passed 102 tests. A remaining service marker was then removed to align its
two-child record with the new two-column grid; v3 passed all 102 tests and build.
Reports remain in ignored local `ml/artifacts/quiet-ui-tests-v*.json`.

These are mocked component and build checks, not fresh browser, live MySQL,
screen-reader or contrast certification. Responsive visual review and real-service
acceptance remain open. No accuracy, deployment or full-completion claim follows.
