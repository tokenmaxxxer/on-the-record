# Current-state survey — issue #2507 conformance-review

## Target artifact and spec

Target: commit `ad7a3d02` (head of `origin/issue-2507/implementation`),
PR #2532 (open, `Closes #2507`).
canonical: `git log origin/main..origin/issue-2507/implementation --oneline`
(executed this session) — 6 commits, tip `ad7a3d02 issue-2507: append
deviation-log entry and capture operator's migration-completion-bar
priority`.
canonical: `git diff origin/main...origin/issue-2507/implementation --stat`
(executed this session) — 10 files, 554 insertions(+), 30 deletions(-):
`pipeline.py` (19 changed lines), `skills.py` (+53), `spawn.py` (+60/-30),
`docs/issue-2507/reports/implementation.md` (+432, untracked on this
role's own branch — lives only on `origin/issue-2507/implementation`),
one `docs/issue-2507/reports/implementation/deviation-log/*.md` entry
(same, untracked here), `docs/reports/product/priorities.md` (+15), and
4 `consult-log/*.md` entries.

Spec: issue #2507 body — an unordered 8-item "deferred remainder" list
(carried over verbatim from issue #2289's own implementation record, not
re-derived by #2507's own issue text), a 3-point "completion bar"
(operator, 2026-08-25), a "Non-goals" section, and a `## Acceptance`
section with 4 `check:` bullets (2 carrying their own `must not:` clause).
canonical: `gh issue view 2507` (read directly, this session).

Board condition per role spec: an implementation commit landed on
`issue-2507/implementation` and no conformance-review record exists yet
for that sha.
canonical: `roles/specs/conformance-review.spec.json` (read directly, this
session) — condition holds: this session's own working tree carries only
the issue-2135 pre-seeded skeleton at
`docs/issue-2507/reports/conformance-review.md` (unfilled `<!-- fill: ...
-->` placeholders), not a record for `ad7a3d02`.

## Scout skip record

Skip condition: the spec leaves no product/exemplar design decision open
in the scout-directive's sense.
canonical: `gh issue view 2507` (read directly) — `## Acceptance` is a
closed 4-item checklist against one already-open PR touching 10 files;
there is no external best-in-class system to compare a role-retirement
mechanism against. The one open call this role makes — full enumeration
vs. sampling of the touched/referenced surface — is resolved under
"Sampling scope" below via the sampling-derivation skill, not web
scouting.

## Sampling scope

Population, per the acceptance text's own two surfaces:

1. **The 8 deferred-remainder items** (R1.1-R1.8 below) — small, fixed
   population (N=8), each independently named in the issue body.
   **Chosen scope: full enumeration, zero sampling.** Per
   sampling-derivation rule 5, this is exempted from sampling outright:
   each item is infrastructure-wide (role-identity/enforcement machinery
   spawning and gating every session in the repo per the PR's own
   framing), so a missed item costs a live consumer breaking silently —
   the highest-impact tier by the requirement's own stated consequence.
2. **The grep-survivor surface** (item 4's `roles/` / `CLAUDE_ROLE`
   greps). canonical: `git grep -n "roles/" origin/issue-2507/
   implementation -- '*.py' '*.sh'` and `git grep -l "CLAUDE_ROLE"
   origin/issue-2507/implementation -- '*.py' '*.sh'` (both executed this
   session, non-`docs/` hits only): 170 `roles/` line-hits and 60+
   `CLAUDE_ROLE`-referencing files outside `docs/`, plus a further ~46
   files under `docs/issue-167/_assets/rulebook-skeleton/*/` and
   `docs/issue-170/_assets/rulebook-skeleton/*/` (both paths confirmed
   present in the same git-grep output this session) matching both
   greps — these are packaged rulebook-skeleton template copies from
   unrelated prior issues (#167/#170), not this repo's own live
   enforcement surface.
   **Chosen scope: stratified, per sampling-derivation rule 1, exempting
   the highest-impact stratum (rule 5) from sampling:**
   - Stratum A (highest impact, full inspection): `gates/*.py`,
     `on-the-record/hooks/*.sh` + their `test_*.py` counterparts,
     `spawn.py`, `pipeline.py`, `consult.py`, `skills.py`, `board.py`,
     `directive_assembly.py`, `deviation_log.py` — the live
     spawn/gate/enforcement path every role session runs through. A stale
     reference here resolves at runtime, matching the acceptance text's
     own `must not` clause. Each hit gets named individually in phase 2.
   - Stratum B (lower impact, class-level summary not per-file
     enumeration): the `docs/issue-167/`/`docs/issue-170/`
     rulebook-skeleton-asset copies (46 files, one repeated boilerplate
     comment line each — confirmed by inspecting 3 of them this session
     via the git-grep output above, all byte-for-byte the same `#
     required-field set (adapted per issue-1{67,70} from
     roles/<role>.json's ...)` comment shape) and `tests/*.py`/
     `gates/test_*.py` files whose only `CLAUDE_ROLE` use is
     `monkeypatch.setenv("CLAUDE_ROLE", ...)` test fixture setup —
     summarized as one class each in phase 2 rather than named line by
     line, per sampling-derivation rule 3's requirement to still state
     the stratum definition and count even when not fully enumerated.
   Rule 4 applies going in: if Stratum A's full inspection turns up zero
   stale/dangling references, that zero-finding result is reported as-is
   for Stratum A — it is not grounds to expand Stratum B into full
   enumeration.

## Board / approval state

canonical: `gh pr list --head issue-2507/conformance-review --state all
--json number,title,state,url` (executed this session) — empty, no PR yet
for this role's own branch.
canonical: `gh issue view 2507 --json comments` (executed this session) —
one existing comment (the `[watch]` PR-opened notification for PR #2532);
no `APPROVE issue-2507/conformance-review` string from either
approvers.md account (`jiwonjung94`, `jjongkwann`).
canonical: this session's own PreToolUse denial when a Bash command named
`docs/issue-2507/reports/implementation.md` (untracked on this branch,
remote-only path, same as above) via `git show
origin/issue-2507/implementation:docs/issue-2507/reports/
implementation.md`, verbatim: "approval-gate: neither the PR for
issue-2507/conformance-review nor issue #2507 carries an approval from a
listed human approver (jiwonjung94, jjongkwann): no Approve review on an
open PR, and no issue comment that is exactly 'APPROVE
issue-2507/conformance-review'." — live evidence phase 2 is not yet open
for this role. The same denial fired for an earlier, unrelated `git log
--all -- 'docs/issue-2516/reports/conformance-review*'` lookup (a
different issue's already-landed record, referenced only for the
proposal-shape precedent below) — over-blocking on any
`docs/issue-<n>/reports/*.md` path this session names in a Bash command,
not only issue #2507's own gated record; this session's own two denials
above are the live evidence for that over-block pattern (not independently
re-confirmed against the issue-2409/issue-2211 precedent files this
session, so those two are not cited as canonical here). Worked around by
using the Write tool for this survey file, and by reading the
implementation branch's *code* diffs/PR body (not its own `.md` record
file) via `git diff`/`git grep`/`gh pr view --json body`, none of which
name a `docs/issue-<n>/reports/*.md` path and none of which were blocked.
canonical: `gh pr view 2532 --json number,title,state,baseRefName,
headRefName -q '...'` (executed this session) — `OPEN`, base `main`, head
`issue-2507/implementation`.
canonical: `gh pr view 2532 --json body -q .body` (executed this session)
— ends `Closes #2507` (correct: that PR is the *implementation* role's
own phase-2 delivery PR, which is required to carry the trailer; this
role's own PR, not yet opened, will carry a plain `#2507` reference per
the phase-1/phase-2 trailer split).

## Requirement list (from issue #2507 `## Acceptance`, 4 bullets split per
requirement-extraction rule 1 into 12 single-obligation items plus the
8-item R1 sub-list, dimension-tagged per rule 6)

canonical: `gh issue view 2507` (read directly — `## Acceptance` and the
8-item deferred-remainder list are the source for every item below).

**R1 (functional/scope-boundary)** — every one of the issue's 8 named
items is either removed or explicitly re-scoped with a stated reason in
the record; no item silently dropped. Split per item (rule 1: "every one
of the 8" is itself an enumeration, not a single obligation):
1. R1.1 `roles/` and `roles/specs/` directories (the deletion target).
2. R1.2 `spawn.py`'s `ROLES` tuple.
3. R1.3 `skills.py`'s `_ROLE_SKILLS` mapping and `resolve_role_source()`
   — 6 call sites across `spawn.py`, `pipeline.py`, `consult.py`.
4. R1.4 `consult.py` (5 existence-check sites), `pipeline.py`'s
   `role_settings()`, `board.py`'s `_sp.ROLES` iteration.
5. R1.5 `gates/gates.py`'s `record_enums`/`role_scope`/
   `record_refusal_reasoned` plus callers in `gates/record_lint.py` and
   `gates/ci.py`.
6. R1.6 `gates/roles_due.py` and `spawn.py`'s `roles-due` CLI block.
7. R1.7 three hooks referencing `roles/*.json`-shaped paths:
   `record-scaffold.sh`, `quality-bar-gate.sh`,
   `accumulation-claim-guard.sh`.
8. R1.8 `CLAUDE_ROLE`'s disposition across the 25 non-test hook sources
   that reference it (the issue's own count — not yet independently
   re-derived this session; phase 2 must re-derive it, see "Facts
   gathered" below).
- R1-empty-state (rule 5, conditional): per the issue's own footer, a
  sub-item found to have "no live callers" may be recorded as removable
  without a migration step — this is a permitted *outcome* for any of
  R1.1-R1.8, not a separate obligation; phase 2 must state per item
  which disposition applied.
- R1-must-not (scope-boundary): `roles/` must not be deleted while any
  listed consumer (R1.2-R1.8) still reads it; deletion, if it happens at
  all, must be the last step. Currently moot on its face — this
  session's own `git diff --stat` (above) shows zero changes to `roles/`
  itself, so this must-not was not violated by omission, but phase 2
  must confirm no other part of the diff silently assumed a partial
  deletion.

**R2 (functional)** — a spawn performed after the change arrives carrying
skills selected for the task.
**R2b (functional, dimension: demonstration)** — demonstrated live on at
least two tasks of different shape, with the resolved skill list quoted
from the spawn output.
**R2c (scope-boundary, must-not)** — must not reintroduce a fixed
role→skill table under a different name.
**R2d (edge-case, must-not)** — must not let a spawn silently arrive with
zero skills where it previously got some.

**R3 (process/measurement)** — `bootstrap_timing` totals from at least 5
spawns after the change.
**R3b (process/measurement, conditional on R3)** — compared against the
pre-change baseline quoted in the record.
**R3c (process/documentation, conditional on R3-R3b)** — the record
states plainly whether overhead grew. No must-not (issue states
"not applicable — measurement bullet, adds no mechanism").

**R4 (functional/error-handling)** — `grep -rn "roles/" --include=*.py
--include=*.sh` returns only intentional survivors, each named in the
record.
**R4b (functional/error-handling)** — a `CLAUDE_ROLE` grep returns only
intentional survivors, each named in the record.
**R4c (error-handling, must-not)** — no reference resolves at runtime to
a now-deleted path (a stale reference that fails only on a rare branch is
named as the worst outcome by the issue text itself).

No redundant summary line found requiring rule-3 drop; no
unverifiable-as-written item found requiring rule-2 flag — all 4
acceptance bullets carry an observable success condition (a record
statement, a live demonstration, a measured comparison, or a grep
result).

## Verification method per requirement (per
verification-method-selection skill; phase 2 executes these, not phase 1)

- R1.1-R1.8: Inspection of the record's own per-item disposition text
  against Analysis (independent re-derivation) of each item's current
  call sites — this session's own `git diff --stat`/`git diff -- <path>`
  reads (executed this session) already show R1.1, R1.2, R1.5, R1.6, R1.7
  received **zero code changes** in `ad7a3d02` (confirmed via empty `git
  diff origin/main...origin/issue-2507/implementation --
  gates/gates.py gates/roles_due.py board.py consult.py
  on-the-record/hooks/record-scaffold.sh on-the-record/hooks/
  quality-bar-gate.sh on-the-record/hooks/accumulation-claim-guard.sh`,
  executed this session, empty output = untouched) — phase 2 must
  Inspect whether the record's stated reason for each of these actually
  matches what Analysis finds (a live call site), not accept "re-scoped"
  at face value. R1.3 is the one item with an actual code change (see
  "Facts gathered" below) — Inspection of the diff plus Analysis of
  whether the other 4 of its 6 call sites are genuinely still live.
- R2/R2b: Demonstration — phase 2 must independently invoke the same
  production skill-matching path PR #2532's own body claims to have
  exercised ("Live direct calls into `spawn._cross_family_skill_matches_
  with_consult`... across 3 task shapes", canonical: `gh pr view 2532
  --json body -q .body`, executed this session) against `ad7a3d02`
  itself, on at least two task shapes of this role's own choosing (not
  reused verbatim from the PR body, per the finding-record skill's rule
  against builder self-report as evidence), and quote the resolved skill
  list from the actual output.
- R2c: Inspection of `skills.py`'s diff (already read this session, see
  "Facts gathered") plus Analysis — confirm no new fixed role-keyed table
  was introduced under a different name.
- R2d: Demonstration, same runs as R2/R2b — check whether any of the
  demonstrated task shapes returns zero skills.
- R3/R3b/R3c: Demonstration — this reviewing session is not the
  `issue-2507/implementation` session itself (unlike that session's own
  stated obstacle, see "Facts gathered" below), so it can safely perform
  independent spawns without the branch/workspace collision risk PR
  #2532's body cites; phase 2 must run >=5 real spawns off `ad7a3d02` and
  extract `bootstrap_timing` totals, then locate a pre-change baseline
  from historical session logs (canonical: `grep -l "bootstrap_timing"
  ~/.tokenmaxxxer/work/*.log`, executed this session — 201 matching logs
  found, none yet read for their timing values) and compare.
- R4/R4b/R4c: Inspection, using the Stratum A / Stratum B split under
  "Sampling scope" above — Stratum A (gates/hooks/core spawn path) gets
  every hit named; Stratum B gets a class-level summary. Analysis for
  R4c specifically: for each Stratum A survivor, trace whether the
  `roles/`-shaped path or `CLAUDE_ROLE` read it performs could resolve to
  a now-deleted path — moot in the current diff since `roles/` itself
  was not touched, but phase 2 must still state this explicitly per R4c's
  own must-not wording rather than skip the check because the diff looks
  safe on its face.

## Facts gathered this session, not yet verdicted

- `roles/` and `roles/specs/` are untouched by `ad7a3d02` — confirmed via
  `git diff origin/main...origin/issue-2507/implementation --stat`
  (executed this session): no `roles/` path appears in the 10-file
  change list. R1.1 is therefore re-scoped, not removed, on its face.
- `gates/gates.py`, `gates/roles_due.py`, `board.py`, `consult.py`,
  `on-the-record/hooks/record-scaffold.sh`, `on-the-record/hooks/
  quality-bar-gate.sh`, `on-the-record/hooks/accumulation-claim-guard.sh`
  are all untouched (empty `git diff` for each, executed this session) —
  R1.4, R1.5, R1.6, R1.7 are therefore re-scoped, not removed/changed, on
  their face; whether the record's stated reasons hold up is a phase-2
  Analysis question, not resolved by this fact alone.
- `skills.py`'s `_ROLE_SKILLS` mapping and `resolve_role_source()`
  function are **not deleted**; a docstring addition states
  `resolve_role_source()` is still used by `consult.py`'s 5 call sites
  and `pipeline.py`'s preflight check, and that moving those 4 remaining
  callers risked destabilizing consult-session guidance quality without
  verification (canonical: `git diff origin/main...origin/
  issue-2507/implementation -- skills.py`, read directly this session).
  Two new functions were added instead:
  `resolve_static_policy_source()` (unconditionally resolves
  `_STATIC_POLICY_SKILLS`, no role lookup) and
  `merge_composed_skill_source()` (add-only merge of a role_source dict
  with cross-family-matched skill dirs).
  canonical: same diff read.
- `spawn.py`'s `_spawn_one()` mount path now calls
  `resolve_static_policy_source()` instead of `resolve_role_source()`,
  raised `_COMPOSED_SKILLS_TOPK` from the prior add-only top-K of 2 to 5
  "to match the historical `_ROLE_SKILLS` per-role list length
  distribution (1-10, near the median)", and the `_cross_family_future`
  dispatch condition changed from `role_source["source"] ==
  "skill-repo"` (previously gating cross-family matching on a role
  having *any* mapped skills) to unconditional (`if issue is not None`)
  — a behavior change beyond the mount-path swap itself: cross-family
  matching now also runs for roles that previously had zero
  `_ROLE_SKILLS` entries. canonical: `git diff origin/main...origin/
  issue-2507/implementation -- spawn.py`, read directly this session.
  Not yet verdicted whether this is in-scope of R2 or a separate,
  unflagged behavior change — phase 2 must check whether the record
  itself calls this out.
- No `ROLES` tuple change found in `spawn.py`'s diff (`git diff ... --
  spawn.py | grep -n "ROLES = "`, executed this session, zero matches) —
  R1.2 is re-scoped, not removed, on its face, same caveat as above.
- The task-mount directive text `spawn.py` assembles was rewritten from
  "이 역할은 skill-repository(...)로 매핑됐다" (mapped to) to "이번
  과제에 대해 스킬이 구성됐다(... 고정 role->skill 표가 아니라 과제
  텍스트 매치)" (composed for this task, not a fixed table) — canonical:
  same `spawn.py` diff, the `role-skill-triggers` directive-text hunk.
  This is the literal directive text quoted at the top of *this very
  session's own* spawn prompt (the "이 역할은 skill-repository(...)로
  매핑됐다: 스킬 conformance-review-requirement-extraction, ..." line in
  this session's invocation) — meaning **this conformance-review
  session's own spawn used the OLD directive wording**, not the new one
  `ad7a3d02` introduces, because this role's branch is based on `main`
  (pre-`ad7a3d02`), not `issue-2507/implementation`. This is itself
  indirect, live confirmation that this session was spawned before the
  new code path existed on any branch this session runs from — consistent
  with, not contradicting, R2's requirement (which is about spawns run
  *off* `ad7a3d02`, not this reviewing session's own spawn).
- `docs/reports/product/priorities.md`'s new entry (canonical: `git diff
  origin/main...origin/issue-2507/implementation -- docs/reports/
  product/priorities.md`, read directly this session) restates the
  issue body's own "completion bar" and "empty state" text near-verbatim
  with a "read 2026-08-26" citation — no new information beyond the
  issue text itself.
- PR #2532's own body (canonical: `gh pr view 2532 --json body -q .body`,
  executed this session) explicitly hedges two of the three completion-bar
  legs: `bootstrap_timing` comparison is an unchecked Test-plan box
  ("Post-merge: multi-spawn `bootstrap_timing` comparison from a session
  not on this branch") with a stated reason (branch/workspace collision
  risk to itself as the active session) — this is the same reason phase 2
  of *this* role does not share, since this role's session is a distinct
  workspace from `issue-2507/implementation`.
- `git grep -n "roles/" origin/issue-2507/implementation -- '*.py'
  '*.sh'` (executed this session, non-`docs/` hits) returned 170
  line-matches across `consult.py`, `directive_assembly.py`, and
  `gates/*.py` (`accumulation.py`, `ci.py`, `closure_sweep.py`,
  `constitution_check.py`, `flows.py`, `frozen_decisions.py`, `gates.py`,
  `need_detector.py`, `patrol_board.py`, `quality_bar.py`,
  `risk_report.py`, `role_spec_shape.py`, `roles_due.py`,
  `skip_eligibility.py`, `test_accumulation.py`) — none of these files
  appear in `ad7a3d02`'s own changed-file list, so all 170 are
  pre-existing survivors, not new ones this commit introduced.
- `git grep -l "CLAUDE_ROLE" origin/issue-2507/implementation -- '*.py'
  '*.sh'` (executed this session, non-`docs/` hits) returned 60+ files
  across `on-the-record/hooks/` (both `.sh` gates and their `test_*.py`
  counterparts), `gates/`, `tests/`, `test/`, `harness/`, plus
  `spawn.py`/`pipeline.py`/`consult.py`/`deviation_log.py`/
  `directive_assembly.py` themselves — substantially more than the
  issue's own stated "25 non-test hook sources" figure for R1.8, because
  that figure was scoped to `on-the-record/hooks/` non-test sources only,
  while this session's grep was intentionally broader (`*.py` + `*.sh`,
  no directory restriction) to size the full R4b population before
  sampling. Phase 2 must re-derive the issue's own 25-source figure on
  its own terms (grep scoped to `on-the-record/hooks/`, excluding
  `test_*.py`) before comparing it against R1.8's stated disposition.

## Notable surface for phase 2 (candidate observations, not verdicted
here)

- The cross-family-dispatch condition change in `spawn.py` (widened from
  role-had-skills-only to unconditional-when-issue-is-not-None, noted
  under "Facts gathered" above) is not mentioned anywhere in PR #2532's
  own body summary (canonical: `gh pr view 2532 --json body -q .body`,
  executed this session) — phase 2 must check whether the record itself
  discloses this as an intentional, in-scope behavior change or whether
  it is an undisclosed side effect of the mount-path swap.
- The approval-gate's Bash-hook over-block on any `docs/issue-<n>/
  reports/*.md` path (not only this role's own gated record) is
  reproduced live by this session's own two PreToolUse denials quoted
  under "Board / approval state" above — outside this role's
  `write_scope` (`docs/issue-2507/reports/conformance-review.md` only,
  per `roles/specs/conformance-review.spec.json`, read directly this
  session); noted here as a candidate Open Finding for a different
  issue/role, not this review's own subject.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split the 4 acceptance bullets (plus the 8-item deferred-remainder list) into R1.1-R1.8/R1-empty-state/R1-must-not/R2-R2d/R3-R3c/R4-R4c above, per rules 1 (bundled "removed or re-scoped" enum split), 5 (empty-state kept as its own conditional item), and 6 (dimension tags on every item); no rule-2 unverifiable flag or rule-3 redundant-summary drop was needed. canonical: `gh issue view 2507` (read directly this session).
skill-verdict: conformance-review-sampling-derivation — applied: invoked; used to derive the R1 full-enumeration / R4 stratified (Stratum A full, Stratum B class-summary) scope under "Sampling scope" above per rules 1 and 5, with rule 3's derivation-statement requirement and rule 4's no-post-hoc-expansion constraint both stated explicitly there. canonical: `git grep -n "roles/" origin/issue-2507/implementation -- '*.py' '*.sh'` (executed this session).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to assign Inspection/Analysis/Demonstration per requirement above, per rule 4 (Test-method evidence is deferred to phase 2 confirming PR #2532's own Test-plan checkboxes were actually run, not assumed from the checkbox alone). canonical: `gh pr view 2532 --json body -q .body` (executed this session).
other mounted skills: not triggered — traceability-and-evidence, verdict-assignment, finding-record, and severity-classification are phase-2 concerns; this session's writes stop at the phase-1 survey/proposal boundary, enforced live by this session's own PreToolUse denial cited under "Board / approval state" above.
