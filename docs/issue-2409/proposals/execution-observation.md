---
status: proposed
files:
  - docs/issue-2409/reports/execution-observation/survey.md
  - docs/issue-2409/proposals/execution-observation.md
  - docs/issue-2409/reports/execution-observation.md
---

# Proposal — issue #2409: execution-observation

Phase 1 only, per role-handoff contract v3 s19. No verdict language below —
outcome/result is named here as what phase 2 will check, not decided.

Skip condition stated per scout-directive / survey-order-directive: scouting
is skipped because the spec leaves no design decision open. canonical:
`roles/specs/execution-observation.spec.json`'s own `gate_c_status` field,
quoted in `docs/issue-2409/reports/execution-observation/survey.md`'s "Scout
skip record" section — the verdict method (worst-case recomputation over
cited results) and the record's own field shape (EARL 1.0
subject/test/result/assertedBy) are both fixed by that spec file, leaving
this round nothing to scout a comparable-system pattern against.

## Request

Fill the pre-existing skeleton at
`docs/issue-2409/reports/execution-observation.md` (issue #2135's
convention) with a verdict on the three commits landed on branch
`issue-2409/implementation` (PR #2416), against the six Acceptance bullets
issue #2409's own body states — instrumentation artifact regenerates,
exploratory-Bash mechanism, hook-refusal-contract mechanism,
redundant-read mechanism, honest before/after measurement, and no
verification/record/observer step removed.

## Constraints

- Write only `docs/issue-2409/reports/execution-observation.md` (this
  role's sole `write_scope` entry per
  `roles/specs/execution-observation.spec.json`) once phase 2 opens; the
  survey and this proposal are this round's only other writes.
- Never edit `directive_assembly.py`, `spawn.py`,
  `scripts/related_files.py`, `scripts/session_waste_metrics.py`, any
  test file, or the implementation role's own `docs/issue-2409/`
  subtree — those are read-only inputs, read via a separate git
  worktree checked out from `issue-2409/implementation` (PR #2416's
  head), kept out of this branch's own tree entirely.
- No fabricated result: the frontmatter `result` field is the worst
  case across every cited test entry (the spec's own recomputation
  rule), never a standalone summary asserted independently of what was
  actually re-run or read-verified this round.

## Rationale

**Chosen approach: independently re-execute the reproducible
Acceptance claims (the instrumentation artifact's regenerate command,
the exploratory-Bash lookup) from a fresh worktree, and independently
read-verify the wiring/diff claims (hook-contract always-on
materialization, the `code_scoped` gating, the additive-only
`directive_assembly.py` diff, the untouched `on-the-record/hooks/`
tree) against the actual PR #2416 diff — rather than trusting the
implementation record's own pasted transcripts.** This matches the role
spec's own framing of what makes this role's verdict non-discretionary:
`roles/specs/execution-observation.spec.json`'s `gate_c_status` states
the check holds because "two independent observers re-running the same
test set against the same commit sha produce the same worst-case
verdict" — re-running and re-reading the actual diff, not merely
re-reading the record's own prose about itself, is the reason the spec
gives for why this role's judgment reduces to mechanical aggregation
rather than an investigative finding. It also follows
`docs/issue-2393/reports/execution-observation.md`'s already-established
method for this exact lineage (independent worktree, fresh scratch
reproduction, direct source/diff read for non-executable claims).

**Rejected alternative: trust the phase-2 record's own pasted
command-output transcripts and source-code narrative without
independent re-execution or re-reading the diff directly** (the shape
`docs/issue-659/proposals/execution-observation.md`'s own Constraints
section chose for a prior issue — "never re-execute the observed
role's code"). Rejected here because issue #2409's own Acceptance
section explicitly requires "measured before/after," and a record
whose only evidence is a second-hand quote of the implementing role's
own claim about itself is not independently verifiable by a reader as
genuine — re-running the instrumentation artifact and the lookup
script, and re-reading the diff directly, this round, in a worktree
this role never wrote to, produces a citation this role can stand
behind as its own.

## What will be done

1. In a separate `git worktree` checked out from PR #2416's head (kept
   out of this branch's own tree), re-run
   `python3 scripts/session_waste_metrics.py --batch` (or the
   equivalent direct `batch_summary()` call) against the same 5 real
   session logs the implementation record names (issues
   2314/2331/2348/2382/2393), and independently re-run
   `python3 scripts/related_files.py <issue> --json` for the same 5
   issue numbers, comparing both outputs against the record's own
   pasted table row by row.
2. Read-verify (source read plus `git diff` against the parent commit)
   the hook-contract always-on materialization, the `code_scoped`
   gating wiring in `spawn.py`, and the additive-only nature of the
   `directive_assembly.py` diff; confirm `on-the-record/hooks/` and
   `hooks.json` are unchanged between the parent commit and PR #2416's
   head.
3. Re-run the targeted test suite the record names
   (`tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py
   tests/test_related_files.py tests/test_session_waste_metrics.py`)
   fresh, in the same worktree.
4. Fill `docs/issue-2409/reports/execution-observation.md` per the
   pre-existing skeleton's own five headings (delivered-work summary,
   why, upstream basis, open findings, next steps), with frontmatter
   `subject`/`test`/`result`/`assertedBy` resolving to the commit sha
   and commands actually re-run/re-read in steps 1-3, `result` set to
   the worst case across every cited entry, and `loop_state:
   handed-off` (this role's own terminal state per
   `roles/specs/execution-observation.spec.json`).
5. Report, as open findings with their own resolution path (not as
   blocking defects), anything this round observes outside the
   artifact's own correctness — for example any drift between a
   reproduced count and the record's pasted count, or anything this
   session's own live spawn environment reveals about whether PR
   #2416's mechanisms are actually reaching real spawned sessions yet.

## Out of scope

- Editing `directive_assembly.py`, `spawn.py`, any script or test file,
  or the implementation role's own `docs/issue-2409/` paths tracked on
  `issue-2409/implementation`.
- Filing a follow-up issue for any open finding — issues are
  user-authored only (contract v3); this role's record is the
  disclosure mechanism, not the filing mechanism.
- Performing the corpus-scale "after" re-measurement issue #2409's own
  Acceptance item 5 names as not yet done — spawning 5+ new real
  ~15-minute role sessions is outside this role's own `write_scope` and
  outside the safe blast radius the implementation record itself
  already declined for the same reason (real duplicate PRs against a
  shared repo).
- Judging whether PR #2416 should land on main — a human merge/close
  decision, outside this role's own `write_scope` and judgment.

## How you'll know it worked

The target record (`docs/issue-2409/reports/execution-observation.md`)
is committed on this branch with
`subject`/`test`/`result`/`assertedBy` frontmatter each resolving to a
real repo path, commit sha, or command actually re-run/re-read this
round; `loop_state: handed-off`; at least one non-untested,
non-cantTell test entry backed by a command re-executed in step 1 or 3
above (not merely read); and every open finding carrying its own
resolution path.
