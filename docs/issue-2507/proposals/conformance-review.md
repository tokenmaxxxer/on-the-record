---
status: proposed
files:
  - docs/issue-2507/reports/conformance-review.md
---

## Request

Issue #2507 conformance review (board condition per role spec,
`roles/specs/conformance-review.spec.json`): commit `ad7a3d02` landed the
phase-2 delivery on `issue-2507/implementation` (a task-composed
skill-mount path replacing `spawn.py`'s use of the fixed `_ROLE_SKILLS`
table, plus an implementation record re-scoping the other 7 of the
issue's 8 deferred-remainder items), PR #2532 is open, and no
conformance-review record exists yet for that sha — see
`docs/issue-2507/reports/conformance-review/survey.md` for the full
derivation and canonical citations. This role's phase-2 job is a
per-requirement verdict (Present|Surface|Absent|Incorrect|Unverifiable)
against issue #2507's own `## Acceptance` text — never a holistic quality
judgment, never a fix, and never a rubber stamp of PR #2532's own
self-assessment (which already hedges two of its three completion-bar
legs in its own body).

## Constraints

- The filled record lands only after human Approve (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- This role's `write_scope` is
  `docs/issue-2507/reports/conformance-review.md` only
  (`roles/specs/conformance-review.spec.json`) — it never edits
  `spawn.py`, `skills.py`, `pipeline.py`, `roles/`, or the implementation
  role's own record.
- Verdicts must be re-derived by this role directly against `ad7a3d02`
  (independent spawns for R2/R2b/R2d, independent multi-spawn
  `bootstrap_timing` collection for R3/R3b/R3c, independent greps for
  R4/R4b/R4c), not taken from `docs/issue-2507/reports/implementation.md`'s
  own self-reported numbers at face value — finding-record skill
  checklist item: the verdict comes from looking at the artifact, not
  from the builder's account of their own intent. This matters concretely
  here: PR #2532's own body already hedges its `bootstrap_timing` box as
  unchecked ("could not be safely obtained this session... spawning
  another risks branch/workspace collision") — a constraint that does not
  apply to this role's own, separate session/workspace, so phase 2 has no
  excuse to carry that gap forward unmeasured.
- Issue #2507's `## Acceptance` text names 4 `check:` bullets, split in
  the survey into R1.1-R1.8 (the 8-item deferred-remainder list) plus
  R2-R2d/R3-R3c/R4-R4c (12 further single-obligation items). The survey's
  "Notable surface for phase 2" item (the `spawn.py` cross-family-dispatch
  condition widening found this session, undisclosed in PR #2532's own
  body) is inside the R1.3/R2 set and gets checked as part of those
  verdicts, not treated as a separate finding outside the acceptance text.
- The approval-gate's own Bash-hook over-block on `docs/issue-<n>/
  reports/*.md` paths (reproduced live twice this session, see the
  survey's "Board / approval state" section) is recorded as a candidate
  Open Finding for a different issue/role, not folded into any R1-R4
  verdict — it is unrelated to issue #2507's own subject matter.

## Rationale

Considered trusting `docs/issue-2507/reports/implementation.md`'s own
pasted evidence (the "Live direct calls into
`_cross_family_skill_matches_with_consult`... across 3 task shapes" claim
and the unchecked `bootstrap_timing` box) as sufficient on its own,
without independent re-runs — rejected: this role's own live PreToolUse
denial this session (quoted in the survey's "Board / approval state"
section) already shows this session cannot read that record at all before
Approve, so the only way to check R2/R2b/R2d and R3/R3b/R3c today is
direct, independent re-execution against `ad7a3d02` — which this survey
already scoped (R2/R2b/R2d: run the same production matching function
this role calls itself, on two task shapes of this role's own choosing,
not copied from the PR body; R3/R3b/R3c: this role's session sits in a
different workspace than `issue-2507/implementation`, so it does not
inherit that session's own stated branch/workspace-collision obstacle,
and can obtain the >=5-spawn measurement PR #2532 itself could not). The
finding-record skill's own rule against builder self-report as evidence
applies for exactly the same reason it did on issues #2409 and #2211 —
this role's own conformance-review record is the direct precedent for
method here, not a different case needing a different approach.

Considered treating R1.1-R1.8 as satisfied by the mere presence of
re-scoping prose in the implementation record, without independently
re-deriving each item's current call-site state — rejected: this
session's own `git diff` reads (already executed, see the survey's
"Facts gathered" section) show 5 of the 8 items (`roles/` itself,
`spawn.py`'s `ROLES` tuple, `gates/gates.py`, `gates/roles_due.py`, the
three named hooks, `consult.py`/`pipeline.py`/`board.py`) received *zero*
code changes in `ad7a3d02` — meaning R1's own acceptance text ("removed
or explicitly re-scoped with a stated reason") turns entirely on whether
the record's stated reasons for those five untouched items hold up under
independent Analysis of their current call sites, not on trusting that a
reason was merely written down. A verdict rendered from the record's
prose alone, without that independent check, would satisfy R1 only in
form, not substance — exactly the gap this role exists to catch.

Considered a stratified/sampled review of every `roles/`/`CLAUDE_ROLE`
grep hit rather than a full-vs-summary split — resolved in the survey's
own "Sampling scope" section: the survivor population is large (170
`roles/` line-hits, 60+ `CLAUDE_ROLE`-referencing files outside `docs/`,
plus ~46 rulebook-skeleton-asset files under `docs/issue-167/`/
`docs/issue-170/`), too large to name every line individually without
the record itself becoming unreadable, but the live-enforcement stratum
(`gates/`, `on-the-record/hooks/`, the core spawn/consult/pipeline/board
files) is exactly the stratum where a stale reference would resolve at
runtime and break a session — the sampling-derivation skill's rule 5
case for exempting the highest-impact tier from sampling, while the
lower-impact rulebook-skeleton-asset and test-fixture strata get a
class-level summary instead of per-file enumeration.

## What will be done

Phase 2, once approved, renders one verdict per requirement (R1.1-R1.8,
R1-empty-state, R1-must-not, R2-R2d, R3-R3c, R4-R4c as listed in the
survey) against `ad7a3d02`, using the verification method already
assigned per requirement in the survey's "Verification method per
requirement" section: Inspection plus independent Analysis for R1.1-R1.8
(checking whether the record's stated reason for each untouched item
matches this role's own independent read of its current call sites, not
accepting "re-scoped" at face value); Demonstration for R2/R2b/R2d
(independently invoking `ad7a3d02`'s own production skill-matching path
on at least two task shapes chosen by this role, quoting the resolved
skill list from the actual output); Inspection plus Analysis for R2c (no
new fixed role-keyed table introduced under a different name);
Demonstration for R3/R3b/R3c (>=5 real spawns off `ad7a3d02`,
`bootstrap_timing` totals extracted and compared against a pre-change
baseline located from the historical session logs the survey already
found — 201 logs carrying `bootstrap_timing` entries — the record states
plainly whether overhead grew); and Inspection for R4/R4b/R4c using the
survey's Stratum A (full enumeration) / Stratum B (class summary) split,
with Analysis of whether any Stratum A survivor could resolve to a
now-deleted path. Each verdict carries a file:line/command-output
evidence citation per the traceability-and-evidence skill. The record's
frontmatter (`subject`/`test`/`result`/`assertedBy`, per
`roles/specs/conformance-review.spec.json`'s EARL-aligned required
fields) will be filled with `result` recomputed as the worst-case across
the cited verdicts. The `spawn.py` cross-family-dispatch condition
widening found this session (undisclosed in PR #2532's own body) will be
checked as part of R1.3/R2's own verdicts, named explicitly either way.

## Out of scope

- Editing `spawn.py`, `skills.py`, `pipeline.py`, `roles/`, or the
  implementation role's own record, even if a verdict below Present is
  rendered — this role reports, it does not fix.
- Filing a follow-up issue for the approval-gate's Bash-command
  path-matching over-block this session reproduced — outside this role's
  `write_scope`; phase 2 will name it as an Open Finding for a human/
  different role to act on.
- Re-litigating issue #2507's own design (whether task-composed matching
  was the right replacement for a fixed role→skill table, vs. some other
  mechanism) — phase 2 checks conformance to what the issue asked for,
  not whether the issue asked for the right thing.
- Independently re-deriving issue #2289's own original 8-item list
  derivation (the "Deferred remainder" section of
  `docs/issue-2289/reports/implementation.md` issue #2507 explicitly
  states it carried the list from, unread this session) — issue #2507's
  own body already treats that list as given; phase 2 checks whether
  `ad7a3d02` resolved or re-scoped each of the 8 items as issue #2507
  states them, not whether issue #2289's own derivation of the 8 was
  itself correct.
- Reviewing PR #2532's own mergeability, CI status, or review comments —
  this role's subject is the commit's conformance to the issue text, not
  the PR's process state.

## How you'll know it worked

`docs/issue-2507/reports/conformance-review.md` carries requirement
blocks for R1.1-R1.8 (plus R1-empty-state/R1-must-not) and R2-R2d/
R3-R3c/R4-R4c, each with `requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`, every verdict backed by a citation this role re-derived
against `ad7a3d02` (including an independently run >=5-spawn
`bootstrap_timing` measurement compared against a real pre-change
baseline, and independently run skill-mount demonstrations on two
distinct task shapes with the resolved skill list quoted verbatim from
the output — not copied from PR #2532's own body); the frontmatter
`result` field matches the worst-case of those verdicts; the survey's
"Notable surface" item (the approval-gate's own over-block) is recorded
as an Open Finding with a resolution path; `loop_state` reaches
`reported` (this role's terminal state per its spec). Caveat, matching
the issue-2409/issue-2211 precedent: `result`-vs-verdicts agreement is
not gate-checked today
(`roles/specs/conformance-review.spec.json`'s own
`recomputation.checked_by` is `"TBD"`) — this stays manual discipline in
phase 2, not something an existing gate refuses if violated.
