---
status: proposed
files:
  - gates/need_detector.py
  - gates/test_need_detector.py
  - gates/quality_bar.py
  - gates/test_quality_bar.py
  - spawn.py
  - roles/specs/brand-design.spec.json
  - roles/specs/content-design.spec.json
  - roles/specs/market-analysis.spec.json
  - docs/specs/role-spec-template.schema.json
  - docs/issue-1160/reports/implementation/survey.md
  - docs/issue-1160/reports/implementation/scout-brief.md
  - docs/issue-1160/proposals/step3-machinery.md
  - docs/issue-1160/reports/implementation.md
---

## Request

execution-observation's FAIL on issue #1160 step 3
(docs/issue-1160/reports/execution-observation.md) found that
`need_detector`, `mission_deliverables`, and `verified_by` are
declarative-only: no evaluator reads `need_detector`, nothing prints an
advisory line from it, and nothing feeds `mission_deliverables`/
`verified_by` into a bar-verdict check. Build the missing machinery: (1)
a need-detector evaluator, advisory-first, that reads the three pilot
specs' `need_detector` predicates against a target repo's file tree;
(2) an advisory print surface the orchestrator's existing board-reading
path can consume, alongside `roles-due`, never auto-spawning; (3) a
bar-verdict linkage function that feeds `mission_deliverables`/
`verified_by` into `gates/quality_bar.py`'s existing anti-circular
`classify`, reused rather than reinvented. Hermetic tests: WITH-need
fixture fires, WITHOUT-need fixture silent, verdict-linkage
anti-circular. State what remains for the next observation pass.

## Constraints

- Advisory-only (issue #1160 requirement 2): the detector never spawns
  a role session itself — it only prints a line an orchestrator's
  existing board-reading step can act on, same shape as `roles-due`'s
  existing advisory output.
- Reuse, not reinvent, `quality_bar.classify`'s anti-circularity
  (account-resolved, never `CLAUDE_ROLE`-resolved) — scout-brief's
  "adopt" list.
- Hermetic: no fixture repos on disk outside pytest's own `tmp_path`,
  no network, no shelling out — `test_quality_bar.py`'s existing
  pure-function/in-memory-dict convention (scout-brief item 3).
- No new dependency: hand-rolled predicate matching
  (`fnmatch`/`pathlib`), the same constraint `role_spec_shape.py`
  already states for itself.
- `write_scope`/`design-tokens` style glob evaluation must run against
  an arbitrary **target repo root**, not just this repo — the whole
  point is evaluating a *different* project's file tree, so the
  evaluator takes a `root: Path` argument, mirroring `roles_due.py`'s
  own `root` parameter.

## Rationale

Considered parsing `need_detector.condition`'s existing free-form prose
directly (regex/keyword heuristics over the English sentence) instead
of adding a structured sibling shape. Rejected: `gates/roles_due.py`'s
own module docstring states the deliberate house rule this repo already
follows — "No LLM re-reading `board_condition` as prose here —
determinism and auditability" — and a hand-rolled prose parser is
exactly the fragile, non-auditable middle ground that rule warns
against: it would silently drift out of sync with the prose wording
(e.g. rewording "no design-tokens/*.json file exists" would break a
regex without failing any test that pins the *predicate*, only tests
that happen to pin the exact string). Instead, each spec's
`need_detector` gets a small structured sibling next to the existing
prose `condition` (which stays as the human-readable contract, exactly
how `board_condition` prose already coexists with `use_when.trigger`'s
structured fields on other specs) — `present_patterns` (glob list,
"has this kind of file") and `absent_patterns` (glob list, "and none of
these exist") — mechanically evaluated, deterministic, and immune to
prose rewording.

Considered building the bar-verdict linkage as a wholly new function in
a new module instead of extending `gates/quality_bar.py`. Rejected: the
existing `bar_scoped_roles(pr_files, role_path_patterns)` already
establishes exactly the shape needed —
`mission_deliverables[].artifact` values are glob-shaped path strings,
so mapping them into `bar_scoped_roles`'s existing glob-matching input
is direct reuse, not a new pattern; the anti-circularity comparison
(`classify`'s `record_author_account != producer_account`) is already
correct for "verified_by role differs from the producing role" and
needs no change, only a caller that resolves `verified_by`'s named role
to an account the same way existing callers already resolve
`CLAUDE_ROLE`-adjacent accounts (per `quality_bar.py`'s own docstring
constraint on callers).

## What will be done

1. `gates/need_detector.py` (new, mirrors `roles_due.py`'s shape):
   - `load_need_detector_specs(root)` → `{role: spec}` for every
     `roles/specs/*.spec.json` carrying a non-empty
     `use_when.need_detector`.
   - `needs_due(target_root: Path) -> list[dict]`: for each loaded spec,
     evaluates `present_patterns`/`absent_patterns` (glob, via
     `pathlib.Path.rglob`-based matching, same `fnmatch` primitive
     `roles_due.py` already uses) against `target_root`'s actual file
     tree; a role is "due" iff at least one `present_patterns` glob
     matches AND no `absent_patterns` glob matches — the same
     present-AND-absent shape all three pilot specs' prose already
     describes. Returns `{"role", "reason"}` dicts, pure classifier, no
     side effects.
   - `format_report(due)` → advisory text lines, same shape as
     `roles_due.format_report`, prefixed `[needs-due]` (not
     `[roles-due]`) to keep the two advisory streams visually
     distinct.
2. Sibling structured fields added to each pilot spec's existing
   `use_when.need_detector` (prose `condition` untouched, kept as the
   documented contract):
   - brand-design: `present_patterns: ["**/*.tsx","**/*.jsx","**/*.vue","**/*.svelte"]`,
     `absent_patterns: ["design-tokens/*.json"]`.
   - content-design: `present_patterns` covering the same UI-source
     globs (content-design's condition already keys off UI source
     text), `absent_patterns: ["docs/**/content-design/style-guide.md"]`.
   - market-analysis: `present_patterns` covering
     `docs/issue-*/reports/product-discovery.md` /
     `docs/issue-*/reports/pricing*.md` (the "a product-discovery or
     pricing record exists" half of its prose condition),
     `absent_patterns: ["docs/issue-*/reports/market-analysis.md"]`.
3. `docs/specs/role-spec-template.schema.json`: document the new
   `present_patterns`/`absent_patterns` array-of-string shape under
   `use_when.need_detector` (documentation only — `role_spec_shape.py`
   is not extended to enforce it in this write set; the shape-check
   extension is out of scope, named below).
4. `spawn.py`: a `needs-due` subcommand mirroring the existing
   `roles-due` subcommand (same `argparse` wiring pattern, calls
   `need_detector.needs_due` + `format_report`, prints, never spawns).
5. `gates/quality_bar.py`: add `mission_bar_scoped(target_files,
   mission_deliverable_patterns)` (thin wrapper reusing
   `bar_scoped_roles`'s exact glob-matching body against
   `mission_deliverables[].artifact` globs instead of `write_scope`
   globs) and `verified_by_account(spec, resolve_account_fn)` (resolves
   the `verified_by` spec string, e.g. `"ux-engineering — ..."`, to just
   the leading role token before the first ` — `, so callers can pass it
   into the existing `classify(...)`'s `record_author_account` slot).
   No change to `classify` itself — it is called, not modified in
   behavior.
6. Tests: `gates/test_need_detector.py` (in-memory `tmp_path` fixture
   trees built by pytest itself, not shelled `/tmp` scratch dirs) —
   WITH-need fixture (has `*.tsx`, no `design-tokens/*.json`) fires;
   WITHOUT-need fixture (has `design-tokens/*.json`) stays silent.
   `gates/test_quality_bar.py` gains cases for `mission_bar_scoped` and
   `verified_by_account`, plus one anti-circular case: a role's own
   account passed as both `verified_by`'s resolved account and the
   producer account returns `BAR_NOT_MET` with the same "same account"
   reason `classify` already gives — proving the linkage doesn't bypass
   the existing anti-circularity, only feeds it.
7. Record what remains for the next observation pass in this record's
   own body: leg 1 (detector fires/stays silent) becomes mechanically
   exercisable via `needs-due` on a real target repo; leg 2 (a role
   actually wakes and lands a deliverable) and leg 3 (a different role
   records the bar verdict) still require a human or orchestrator to
   act on the advisory line and then run the existing PR/role flow —
   this build makes the signal real, it does not remove the human
   step the advisory-first constraint (issue #1160 requirement 2)
   deliberately keeps in place.

## Out of scope

- Auto-spawning a role session when the detector fires (explicitly
  ruled out by the advisory-first false-positive-bound constraint).
- Extending `role_spec_shape.py` to mechanically validate the new
  `present_patterns`/`absent_patterns` shape (documentation in the
  template schema only this round — a shape-check extension is a
  separate, smaller follow-up).
- Running the live pilot itself (legs 2-3, which need a real target
  repo and a human/orchestrator decision) — that is
  execution-observation's next pass, not this build's.
- The remaining ten cause-a dormant roles from #1129 — still pilot-scoped
  to the same three specs per #1160's own scope line.

## How you'll know it worked

`python3 -m pytest gates/test_need_detector.py gates/test_quality_bar.py gates/spec_schema_five_activities_test.py gates/test_role_spec_shape.py -q`
exits 0, including: a WITH-need fixture (tmp_path tree with `*.tsx`, no
`design-tokens/*.json`) returning a non-empty `needs_due()` result for
`brand-design`; a WITHOUT-need fixture (same tree plus
`design-tokens/colors.json`) returning an empty result; and a
`mission_bar_scoped`/`verified_by_account`-fed `classify()` call
returning `BAR_NOT_MET` (anti-circular reason) when the resolved
`verified_by` account equals the producer account, and `BAR_MET` when
it differs and the verdict is `bar-met`.

## Accumulation

This touches the repeated `roles/specs/*.spec.json` file set (three
files this round: brand-design, content-design, market-analysis). If N
more pilot roles are added later, each gets the same
`present_patterns`/`absent_patterns` sibling fields under its own
`use_when.need_detector` — the evaluator (`need_detector.py`) already
generalizes over every spec carrying that key via
`load_need_detector_specs`, so no evaluator code changes per new role,
only a new spec-file entry (the same shape `roles_due.py` already
scales to N specs with `use_when.trigger`, per this session's survey of
that file). The one place that would need to change with N is
`docs/specs/role-spec-template.schema.json`'s documentation, and only
if the sibling shape itself changed — adding more roles using the
existing shape needs no schema-doc edit.

## What did not work

None.
