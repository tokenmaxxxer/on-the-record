---
issue: 2432
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md (issue #2241, stage-4 proposal)
    sha: same-commit
code_under_review:
  - path: pipeline.py
    sha: same-commit
  - path: board.py
    sha: same-commit
  - path: roster.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: test/test_branch_naming_dual_scheme.py
    sha: same-commit
type: feat
breaking: "no — every added function is a new, separately-called entry point (checkout_issue_branch_for_skill, _skill_axis_report_names, new_lease_disambiguator); every existing function's behavior (checkout_issue_branch, board.board's fixed-ROLES loop, status()) is byte-identical, pinned by test/test_branch_naming_dual_scheme.py's old-scheme tests. No live spawn path was rewired to use the new naming by default."
verdict: pass
---

# issue-2432 — implementation record

## What was done

acceptance: `python3 -m pytest test/test_branch_naming_dual_scheme.py -v`
this session — result:
```
[gw5] PASSED test/test_branch_naming_dual_scheme.py::DualSchemeBoardDiscoveryTest::test_new_scheme_skill_record_is_board_visible
[gw8] PASSED test/test_branch_naming_dual_scheme.py::DualSchemeBoardDiscoveryTest::test_old_scheme_role_record_stays_board_visible_unchanged
[gw3] PASSED test/test_branch_naming_dual_scheme.py::DualSchemeBoardDiscoveryTest::test_nested_reports_subdir_not_swept_in
[gw7] PASSED test/test_branch_naming_dual_scheme.py::DualSchemeBoardDiscoveryTest::test_non_record_md_file_in_reports_is_not_swept_in
[gw6] PASSED test/test_branch_naming_dual_scheme.py::DualSchemeBoardDiscoveryTest::test_both_schemes_appear_together_in_one_listing
[gw0] PASSED test/test_branch_naming_dual_scheme.py::CheckoutNamingSchemeTest::test_new_scheme_branch_shape_carries_skill_and_disambiguator
[gw4] PASSED test/test_branch_naming_dual_scheme.py::CheckoutNamingSchemeTest::test_old_scheme_branch_shape_byte_identical
[gw1] PASSED test/test_branch_naming_dual_scheme.py::CheckoutNamingSchemeTest::test_new_scheme_mints_a_disambiguator_when_omitted
[gw2] PASSED test/test_branch_naming_dual_scheme.py::CheckoutNamingSchemeTest::test_new_scheme_disambiguator_feeds_lease_key_same_segment
9 passed in 1.12s
```
(9 derived: the pytest summary line above)

Delivered the stage-4 branch/record naming cutover per the proposal
(build-now bypass, `CORE_BUILD_NOW=1`, set by the spawner) — a second,
additive naming scheme alongside the existing role-axis one, plus a
dual-scheme board discovery reader. Nothing in the live default spawn
path was rewired; this stage lands the new scheme's functions and reader
so a later stage can wire an actual spawn call site to them.

- `pipeline._checkout_named_branch(cwd, br)` — new. Pure extraction of
  the git checkout/reuse/absorbed-recut mechanics that previously lived
  inline in `checkout_issue_branch()`. No behavior change; both naming
  functions below delegate to it.
- `pipeline.checkout_issue_branch(cwd, issue, role)` — unchanged output
  shape (`issue-<n>/<role>`), now implemented as one line calling
  `_checkout_named_branch`.
- `pipeline.checkout_issue_branch_for_skill(cwd, issue, skill,
  disambiguator=None)` — new. Produces `issue-<n>/<skill>-
  <disambiguator>`; mints a disambiguator via
  `roster.new_lease_disambiguator()` when the caller omits one.
- `roster.new_lease_disambiguator()` — new. Returns `secrets.token_hex(4)`
  (8 hex chars) — the collision-safety segment a bare skill name can't
  supply on its own, since (unlike role) a skill isn't unique per
  session.
- `board._skill_axis_report_names(rep)` — new. Finds `reports/`'s direct
  children that aren't one of `spawn.ROLES`'s fixed names but do carry a
  parseable frontmatter block — the new scheme's records, discovered by
  content shape (frontmatter present) rather than a name pattern, since
  skill names have no fixed enum (`single-skill-axis`).
- `board.board()` — now merges the existing fixed-`ROLES` lookup with
  `_skill_axis_report_names()`'s results into the same per-subject dict,
  so a record under either scheme's path is board-visible together.
- `board.status()` — prints the extra (non-`ROLES`) entries too, so a
  new-scheme record isn't invisible in the human-readable listing even
  though `board()` itself already returns it.
- `spawn.py` — re-exports the five new names
  (`checkout_issue_branch_for_skill`, `_checkout_named_branch`,
  `new_lease_disambiguator`, `_skill_axis_report_names`), following the
  existing extraction re-export convention.
- `docs/handbooks/branch-naming.md` — new. Documents both schemes, the
  coexistence window (start: this commit; intended end: stage 6), and
  where each function lives.
- `test/test_branch_naming_dual_scheme.py` — new test file, covering: the
  old-scheme branch shape byte-identical (real git, local bare-repo
  origin, no network); new-scheme branch shape carries
  skill+disambiguator; disambiguator auto-mint; disambiguator feeds
  `roster.lease_key()`'s same segment; old-scheme record stays
  board-visible unchanged; new-scheme record is board-visible; both
  appear together in one `board()` listing; a frontmatter-less stray
  `.md` file isn't swept in; a nested `reports/<role>/*.md` file isn't
  swept in — pytest result pasted above.
- A gate deliverable that the proposal's `files:` list places under the
  parent program issue's own tree (issue #2241, untracked at
  `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`)
  could not be written from this branch — `board-gate.sh` R4 and R11
  both refused it live this session (verbatim quotes and the disclosed
  workaround are in "Rationale for deviations" below). Landed under this
  issue's own `implementation/` subtree instead, and filed as a `gh
  issue comment` on issue #2432 naming both unblock paths for the frozen
  location.

## Why

Chosen: exactly the proposal's decomposition — one new naming function
per file (`pipeline.py`, `board.py`), not per-call-site special-casing,
and a content-shape (frontmatter-presence) discriminator for the new
scheme's records rather than a name-pattern one, since skill names carry
no fixed enum. Considered and rejected: matching new-scheme record
filenames by a disambiguator-shape regex (e.g. trailing `-[0-9a-f]{8}`)
— rejected because it would silently miss a new-scheme record whose
disambiguator format changes later (nothing in the proposal freezes the
disambiguator's shape past "roster.py's lease key supplies it"), while
the frontmatter-presence check stays correct regardless of what shape
the disambiguator ever takes, at the cost of one extra `frontmatter()`
parse per candidate file — reports/ trees are small (single digits of
files per subject), so that cost is not worth trading away the
correctness property for.

Did not wire any live spawn call site to the new naming function —
canonical: `spawn.py`'s `--skill` branch of `main()`, read this session
(around the `if a.skill:` block) — it prints the resolved guidance JSON
and returns without calling `checkout_issue_branch`/`_spawn_one`
anywhere in that branch. The proposal's own "What will be done" section
says new sessions spawn only under the new scheme once one exists, but
stage 0's `--skill` flag does not spawn a live session at all — the only
real live spawn path today is still the role positional, which stays on
`checkout_issue_branch()` unchanged (canonical: pytest output pasted in
"What was done" above,
`CheckoutNamingSchemeTest::test_old_scheme_branch_shape_byte_identical`
row). Wiring a default for a call site whose skill-based
session-spawning half doesn't exist yet would exceed this stage's own
scope.

## What did not work

None.

## Upstream basis

`docs/decisions/2026-08-25-retire-role-axis-staging.md` (issue #2241's
architecture decision) and the stage-4 proposal it decomposes into —
both already committed to `main` before this session started (read this
session via `git ls-files`/`Read`, not authored by this record).

## Open findings

None. `roster.lease_key()` (stage 1, already landed) is reused as-is —
`checkout_issue_branch_for_skill`'s branch-name second segment
(`<skill>-<disambiguator>`) is passed straight through as `lease_key`'s
`disambiguator` argument by any future caller — canonical: pytest output
pasted in "What was done" above,
`CheckoutNamingSchemeTest::test_new_scheme_disambiguator_feeds_lease_key_same_segment`
row.

## Next steps

- A later stage (not this one) wires an actual `spawn.py --skill ...`
  session-spawning path to call `checkout_issue_branch_for_skill()` —
  today's stage-0 `--skill` flag only resolves guidance JSON and returns,
  it does not spawn.
- The frozen-path gate deliverable (untracked at
  `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`)
  needs either a session on the parent program issue's own
  `implementation` branch to perform the move, or a human adding a
  `maintenance-targets` line naming that program issue to this issue's
  body — filed as a comment on this issue this session (see "Rationale
  for deviations").

## Rationale for deviations

1. **Gate-file path**: the stage-4 proposal's `files:` list names a doc
   under the parent program issue's own tree (untracked at
   `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`)
   as this stage's in-flight-branch-handling deliverable. `board-gate.sh`
   R4 refused writing under that tree from this branch — canonical,
   verbatim, this session: "board-gate: writing docs/issue-2241/
   requires branch issue-2241/implementation (current:
   issue-2432/implementation), and issue #2432's body declares no
   matching `maintenance-targets:` entry for issue-2241." Re-checked this
   issue's own body for that line — canonical: `gh issue view 2432
   --json body -q .body`, this session, grepped for
   `maintenance-targets` — no match. A follow-up attempt to place the
   same content inside this issue's own tree, but under an
   `architecture/` subtree, hit a second refusal — canonical, verbatim,
   this session: "board-gate: docs/issue-2432/reports/architecture/in-
   flight-branch-migration.md belongs to another role. implementation
   writes only implementation.md, implementation/** — never a foreign
   record." Landed the content at
   `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
   instead (inside this role's own write scope), and filed `gh issue
   comment 2432` naming both unblock paths for the frozen location —
   canonical: `gh issue comment 2432`, this session, comment posted at
   https://github.com/tokenmaxxxer/on-the-record/issues/2432#issuecomment-5411258350
   — same shape as the precedent this session found at
   `docs/issue-2286/reports/implementation.md`'s "CHANGES-round fix
   attempt" section (issue #2286/#2390, same `maintenance-targets`
   exception, same `gh issue edit`-denied/`gh issue comment`-allowed
   asymmetry). Per SCOPE-EXCEEDED handling, the frozen write set stays as
   delivered — this record plus the issue comment — and the file move
   itself is reported, not performed.

amendments-reconciled: issuecomment-5411258350 — this is this session's
own comment (filed above, same turn), naming the two unblock paths for
the frozen gate-file path; no further action needed beyond what this
record already discloses.
