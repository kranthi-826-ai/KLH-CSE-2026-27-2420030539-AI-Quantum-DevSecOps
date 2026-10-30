# Dashboard keyboard and semantics acceptance checkpoint

Date:2026-10-20. Implementation:6f86755. This is a partial PRD Section6.1
acceptance result, not a WCAG conformance or full dashboard-completion claim.
No backend, model, saved security record or account permission was changed.

## Observed issue and change

Previously sidebar fragments and inspect/related-event actions scrolled the
page without reliably moving keyboard focus. Execution records were visually
columnar divs without table relationships; mobile column headings were removed
from the accessibility tree. Invalid event dates could show `Invalid Date`.

- Section navigation now moves focus to labelled, programmatically focusable
  destinations. Hash navigation updates the selected sidebar location; modified
  link clicks preserve normal browser behavior. No scrolling animation added.
- A visible-on-focus skip link bypasses sidebar navigation. Sign-in focuses the
  username field, requires both credentials and bounds usernames to50 characters.
  Logout returns to that field. Error text is associated with both credentials.
- Execution rows expose five column headers/cells, including uniquely named
  inspect actions. On narrow screens the header is visually clipped rather than
  removed from assistive technology. Security events expose list relationships.
- Filtering announces result counts without forcing focus away from inputs.
  Invalid/missing event dates now read `Time unavailable`.

## Automated evidence

All31 frontend tests in6files and the production build passed after the final
implementation commit. Five new keyboard/semantic tests cover:

1. Initial username focus, Tab order and empty-form rejection without fetch.
2. Skip link and Enter activation of every sidebar section with focus/current URL.
3. Browser fragment navigation synchronizing destination focus/current location.
4. Inspect/related-event focus, five-column table/cell relationships, event-list
   structure and honest invalid-time handling.
5. Filter count announcements and keyboard logout/session-token removal.

Tests use synthetic API fixtures, not actual authenticated browser evidence.
Reproduce with `npm test` and `npm run build` in `frontend/web-dashboard`.
Production output:CSS `index-mPitTqtg.css`,JS `index-C4UlWGgK.js`.

## Real browser check and limits

The actual local Vite page opened in a temporary in-app browser tab. The browser
accessibility observations confirmed initial Username focus, Tab→Password,
Tab→Sign in securely, then Enter on an empty form showing the browser's
`Please fill out this field` prompt and returning focus to Username.
No credentials were entered, no authenticated session was opened, and no
backend or MySQL test servers were started for this checkpoint.

Screenshot capture returned `Unable to capture screenshot`. No screenshot was
saved or fabricated. This check does not establish authenticated administrator
visual quality, pixel contrast, all responsive widths, screen-reader behavior,
zoom/reflow or every interaction. Those remain acceptance work. The mobile
column-header rule is implemented and unit semantics are checked, but its actual
mobile assistive-technology rendering is not yet independently verified.

The temporary tab was closed and owned Vite process stopped. Port5174 had no
listener afterward. Existing MySQL and unrelated applications were untouched.
The Sites local-only skill guided checkout-based verification with no publishing;
computer-use guidance constrained the browser checks to observed UI state.
