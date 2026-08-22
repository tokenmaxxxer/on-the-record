# design-bearing classifier corpus (issue #2012 phase 2)

Precision-first: the mechanical rows are real, already-landed issues in
this repo (verbatim excerpts). The classifier must score all four as
NOT design-bearing (overlap < `_DESIGN_BEARING_MIN_OVERLAP = 3`). The
design-bearing rows are three constructed fixtures (this repo has no
literal design-bearing issue of its own — survey.md, "No existing
design-bearing corpus") plus one real design-bearing exemplar fetched
from a consumer repo per the operator's phase-2 approval amendment.

## Mechanical rows (real, must classify NOT design-bearing)

### #1975 — "Watcher alive but event-silent: 92min of no watcher-log output..."

> Observed live 2026-08-22 during issue-1959: the poll-report flagged
> 'watcher-silent: 워처 pid 2119052 는 살아 있지만 92분째 로그 무응답' and
> prescribed --rearm, but --rearm refused... Requirement: --rearm (or a
> new flag) must be able to replace an alive-but-silent watcher when its
> event log has been quiet longer than a threshold while the session log
> grew.

Expected: 0 keyword matches (no storyboard/IA/flow-diagram/UI/UX/brand
vocabulary — this is a watcher-liveness bugfix).

### #1635 — "record_enums (gates.py) mis-flags valid bucketed loop_state values..."

> `gates/gates.py record_enums` (lines ~340-347) iterates record_fields
> and treats a role spec's BUCKETED loop_state dict... as a flat
> allow-list, so it checks `value not in <dict keys>` and flags a
> genuinely-valid terminal value like `handed-off` as an enum violation.

Expected: 0 keyword matches (a scanner logic bugfix).

### #1596 — "[patrol:test-authoring] record-lint-violation: docs/issue-831/reports/architecture.md"

> **Fingerprint:** e2e53e107f80989c27afab436d7d71b61b3872c977e5c95c8b4c0e2222691863
> **Rule / baseline ID:** judge:test-authoring / record-lint-violation
> ...
> Evidence: `[e2e-demo 2026-08-15] loop_state: done`
> **Proposed direction:** address the record-lint-violation finding at
> the flagged location per the judge:test-authoring rule that flagged it.

Expected: 2 keyword matches — `architecture` (from the referenced
report's filename segment, which still tokenizes to the bare word under
`_tokenize`'s alnum-split) and `demo` (from the evidence line's
`e2e-demo` token, which alnum-splits to `e2e` + `demo`). Both hits are
below the `>= 3` threshold, so the row still classifies NOT
design-bearing. This is the calibration-critical row: it is the
highest-scoring mechanical row in the corpus and is why the threshold
could not be set at `>= 1` or `>= 2`.

### #1742 — "spawn.py: additive --skills mount from skill-repository (skill-axis program phase 1)"

> Program context: dissolve the role/rulebook layer into a single skill
> axis... Operator hard constraint: convention adjustments must
> introduce ZERO bugs/conflicts — role-name remains the load-bearing
> identity string until every consumer reads the new fields... check:
> `test/test_spawn_skills_mount.py` (argv/env/workspace-layout
> assertions for both cases...)

Expected: 2 keyword matches — `identity` (from "load-bearing identity
string") and `layout` (from "workspace-layout assertions"). Also below
threshold, tied with #1596 as the second-highest-scoring mechanical row.

## Design-bearing fixtures (constructed, must classify design-bearing)

### Fixture A — landing-page build

> Build a landing page for the product: hero section, features grid,
> testimonials, and a footer. Needs a storyboard and information
> architecture pass before implementation — sketch the user flow from
> landing to signup, then a wireframe of each breakpoint (mobile/tablet/
> desktop) and an HTML demo for stakeholder review.

Expected matches: `storyboard`, `information`, `architecture`, `flow`,
`wireframe`, `html`, `demo`, `landing`, `page` — well above threshold.

### Fixture B — brand/SVG identity asset

> Design a new brand identity: logo mark, color palette, and an SVG icon
> system. Deliverable includes a visual design mockup and a UI style
> guide (typography, spacing, layout grid) for downstream teams to
> apply consistently across surfaces.

Expected matches: `brand`, `identity`, `visual`, `mockup`, `ui`,
`layout` — above threshold.

### Fixture C — k8s platform topology design

> Design the platform topology: a flow diagram of service boundaries and
> data paths, user scenarios for the three primary operator personas,
> and an information architecture for the ops dashboard UX before any
> manifests are written.

Expected matches: `flow`, `diagram`, `user`, `scenarios`, `information`,
`architecture`, `ux` — above threshold.

## Real design-bearing exemplar (consumer repo)

### tokenmaxxxer/tm-webfolio#1 — "ux-engineering + implementation: responsive landing page (hero, projects grid, contact) with a11y baseline"

> Build the landing page: semantic HTML (header/hero, projects grid of 6
> placeholder cards, contact footer), responsive at 360/768/1280 via CSS
> grid/flex (no framework, no build step), accessible baseline
> (landmarks, alt text, focus-visible, color contrast tokens), and a
> small vanilla-JS theme toggle persisting via localStorage.

Expected matches: `landing`, `html`, `page` — overlap 3, exactly at
threshold, still classified design-bearing (`>= 3`). Fetched live via
gh issue view 1 -R tokenmaxxxer/tm-webfolio --json body (2026-08-22) —
this is the operator's phase-2 amendment: at least one real
consumer-repo design-bearing exemplar in the corpus and its own test
row, since the classifier's actual consumers are consumer-repo issues,
not this repo's own tracker.

## Threshold calibration

`_DESIGN_BEARING_MIN_OVERLAP = 3`. The mechanical set tops out at
overlap 1 (#1596); the design-bearing set (3 fixtures + 1 real exemplar)
bottoms out at overlap 3 (the real exemplar). A threshold of 3 clears
the mechanical set at zero false positives (the precision-first bar)
while still catching every design-bearing row in this corpus, including
the real one at its lower bound.
