# issue-1518 current-state survey

## Write surfaces

- `gates/` — plugin-side gate/logic modules with paired `test_*.py` files
  in the same directory (e.g. `gates/repo_scope.py` +
  `gates/test_finding_shape.py`, `gates/findings_due.py`). No existing
  module parses a target-repo file convention; `gates/finding_shape.py`
  and `gates/findings_due.py` reference `target_repo` only as a
  frontmatter field, not a file this plugin reads out of a target repo's
  checkout.
- `tests/` — this repo's own suite (pytest, tiered via `pytest.ini`
  markers, not a file convention — see below).
- `on-the-record/hooks/` — deployed hook surface; `hooks.json` wires
  `UserPromptSubmit`/`PreToolUse`/etc. entries to shell scripts under
  this directory. Directive-only hooks (observe, no gate) follow one
  consistent shape: `trap` fail-open boilerplate, an `ORCHESTRATE_OFF`
  kill switch, optional `CLAUDE_ROLE` gating, then a `cat <<'TXT' ...
  TXT` heredoc emitted to stdout as the directive text (e.g.
  `on-the-record/hooks/role-deviation-directive.sh`). Each such directive
  ships a paired `test_<name>.py` that runs the script via subprocess and
  asserts marker strings appear in stdout (e.g.
  `on-the-record/hooks/test_role_deviation_directive.py`).
- `docs/handbooks/operations.md` — already carries the reference
  instance this issue's req 1 names: a "Pre-merge regression policy —
  tier required per change class (issue #1490)" table (lines
  ~1193-1211) plus the `pytest.ini` `-m "not slow"` / `-m slow` tiering
  convention (lines ~1150-1172). That is a **pytest-marker** convention
  local to this repo, not a file a target repo declares — issue #1518
  req 1 explicitly asks for a *file-convention* (`.on-the-record/
  test-tiers.json` in the target repo), because target repos are not
  this plugin's own repo and cannot carry `roles/*.json` entries or
  `pytest.ini` markers this plugin controls. The file convention is the
  generalization; #1490's marker table is the one instance it must stay
  compatible with (fast tier <=300s budget, `slow` tier keyed to a named
  change class — "spawn-lifecycle code").
- `on-the-record/hooks/record-tiering-directive.sh` /
  `record-tiering-guard.sh` — same literal word "tiering" but an
  unrelated, already-reverted feature (record **section** tiering for
  `## What did not work`, issue #745/#760, PR #1509 kill verdict). No
  collision with test-tiering; naming overlap only.
- `roles/execution-observation.json`, `roles/conformance-review.json` —
  the verification roles req 2 names as contract consumers. Neither
  currently references a tier contract or a target-repo test command;
  consumption is new.
- `gates/repo_scope.py` establishes the existing "target repo" vocabulary
  (a role's clone is scoped to one target repo's checkout; claims about
  capability/contract absence must name which repo). This is the
  established precedent for "a target repo" as a distinct checkout this
  plugin operates against, which req 1's file convention builds on.

## Gap this issue closes

No file convention, parser, or directive currently exists for a
target-repo-declared test-tier contract. `docs/handbooks/operations.md`'s
existing tier table is this-repo-only and pytest-marker-based; it is the
reference *shape* (fast default <=300s / slow keyed to change class), not
a reusable artifact other repos can adopt without also adopting this
repo's `pytest.ini`/`conftest.py` setup.

## #1493 merge point (req 5)

Issue #1493's own check-run artifact (its title names it as the
check-run writer) has no per-issue docs tree on this branch yet —
checked: `find docs/issue-1493 -maxdepth 0` returns nothing here. The
merge point named in this issue's proposal is therefore forward-looking:
the contract fields this issue defines (`fast`/`slow`/`budget_seconds`/
`trigger_change_classes`, plus the tier-selection and measured-cost
output shape `no_contract_gap()` returns) are the fields #1493's future
check-run artifact should reuse verbatim for its own tier+result record,
rather than inventing a second convention — recorded here so #1493's own
phase-1 survey has something concrete to consult.

## Skip conditions

Neither scout-directive skip condition applies (this is not a pure
bugfix and the spec leaves the exact schema to phase-1 design per the
issue's own text: "exact name/schema is phase-1") — scouting ran.
Category: infrastructure/process convention, not a product-facing
surface: scout swept for comparable multi-repo test-tiering conventions
(GitHub Actions `paths:`-triggered job matrices, Bazel/Pants
`target_compatible_with` tagging, `pytest.mark` conventions) rather than
product exemplars. Finding: the "fast default budget + slow triggered by
changed-path pattern" shape is the same shape CI systems converge on
(path-filtered job triggers); no external source materially changed the
schema already specified by the issue text and #1490's landed instance,
so no separate scout-brief.md was produced — the issue text plus
#1490's landed table (cited above) fully pins the schema, satisfying the
"spec leaves no design decision open" skip condition for the *scout
sweep* specifically (the phase-1 schema-naming decision itself was still
open and is resolved in the proposal, not skipped).
