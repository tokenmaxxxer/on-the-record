---
issue: 3050
role: implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0
author: implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 74b261e9 (issue-3050/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4, PR #3086; supersedes this record's own earlier citation of 80ff89f8, its immediate parent)
type: implementation-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md
    sha: 861895f39fc6edaa949e481818f973fc89fa604d
  - path: docs/issue-3050/reports/independent-verification-1.md
    sha: 0d912bf863dc02b46c11f0e0d31b8e50cbf37e4a
  - path: gh issue view 3050 --repo tokenmaxxxer/on-the-record (repair-round spawning comment)
    sha: same-commit
---

# issue-3050 — implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0 record

## What was done

Repair round on PR #3086 (held, not landed), fixing the three gaps both
independent verifications (PR #3101, PR #3108) found. This session's own
`CLAUDE_SKILL` identity is `...-6eac66c0`, a different session from the
one that opened PR #3086 (`...-150a8ac4`), so `board-gate.sh` refuses
this session any write under `docs/issue-3050/` other than this session's
own record path (reproduced live -- see "Why" below). The code fix
therefore landed as commit `80ff89f8`, pushed directly onto PR #3086's
own branch (continuing that PR), while this record documents the repair
round from this session's own, separately-owned path.

The fix touches `spawn.py` (`_push_succeeded()`) and `tests/
test_failed_no_commit_reconcile.py` -- both untracked on this branch,
existing only on PR #3086's own branch `issue-3050/implementation-
blueprint+silent-failure-audit+test-derivation-150a8ac4`, referenced by
their bare paths for the rest of this record without repeating that
annotation each time.

**1. Must-not B fix (blocking).** `spawn.py`'s `push_succeeded`
derivation treated `ensure_pushed()`'s `"nothing-to-push"` status -- the
session's role branch never existed locally, i.e. zero commits were ever
made -- as a successful push, so `fail_closed_downgrade()` kept the
session's self-reported `progressed` outcome instead of downgrading to
`failed-no-commit`. That is must-not B's forbidden shape exactly: the
classifier trusting a session's own success claim, the condition issue
#2667 recorded as the case where the claim was false and the work was
silently lost.

canonical: `gh pr view 3108 --json body` (this session's own read) --
PR #3108 reproduced the pre-fix defect independently against PR #3086's
own `board.py`/`relay.py` before this repair round started.

canonical: `80ff89f8:spawn.py` (`_push_succeeded()`, new):
```python
def _push_succeeded(push_result: dict | None) -> bool:
    return push_result is not None and push_result["status"] not in (
        "push-rejected", "pr-create-failed", "nothing-to-push")
```
`_spawn_one()`'s inline derivation now calls this function.

derived: `grep -n "push_succeeded" board.py spawn.py` (run on PR #3086's
branch before this fix, then again after) -- the only other use of
`push_succeeded` is `board.py`'s `fail_closed_downgrade()` `silent-failure`
branch, `if new_commit and push_succeeded`, which requires `new_commit`
first; `new_commit` cannot be `True` while the role branch never existed
locally, so that branch was not a second instance of the same bug either
before or after this fix.

**2. Test gap (the bug's real cause).** PR #3086's own test file
hand-supplied `push_succeeded` as a literal `True`/`False` to
`board.fail_closed_downgrade()` in every case -- the property was never
exercised by the code that computes it.

derived: added `PushSucceededDerivationLiveTest` to that test file and
ran `python3 -m pytest tests/test_failed_no_commit_reconcile.py::PushSucceededDerivationLiveTest -q`
(PR #3086 branch, that path untracked on this branch as noted above) --
result: `2 passed in 0.9s`. Both cases call the real
`spawn.ensure_pushed()` against a scratch bare-origin + clone: one where
the role branch is never created (reproducing `"nothing-to-push"` for
real), one where a commit is made, pushed, and a PR opened through a fake
`gh` shim (reproducing `"pr-opened"` for real) -- then the real
`spawn._push_succeeded()`, then `board.fail_closed_downgrade()`. Neither
case hand-types a `push_succeeded` boolean.

derived: reverted `_push_succeeded()`'s exclusion tuple to the pre-fix
form (dropping `"nothing-to-push"`) and re-ran the same command --
`test_zero_commits_role_branch_never_created_reconciles_to_failed_no_commit`
failed (`AssertionError: True is not false`); restored the fix and re-ran
the full test file -- result: `19 passed in 0.99s` (17 pre-existing + 2
new). Confirms the new test would have caught the shipped bug.

**3. Documentation gap.** `supersession.py`'s `supersedes:` convention
(landed by PR #3086) was referenced only in spec-registration bookkeeping
(`docs/specs/enforcement-boundary.md`, `docs/specs/acceptance-commands.md`)
-- nowhere a spawned correcting session actually reads.

canonical: `gh pr view 3108 --json body` (this session's own read) -- PR
#3108's own finding: "Neither `docs/handbooks/record-contract.md` nor
`record-authoring.md` mentions it."

derived: added a "Supersession" section to `docs/handbooks/record-
contract.md` (the shape, the frontmatter line, `resolve_authoritative()`'s
reader contract, and the whole-artifact-only limit -- see "Partial
supersession" below) and a "Correcting a prior session's record" section
to `docs/handbooks/record-authoring.md` pointing to it; both committed in
`80ff89f8`.

## Why

**Deviation -- this record could not land on PR #3086's own branch.**
Attempted (`Edit`) to update PR #3086's own record directly while checked
out on `issue-3050/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4`.

derived: attempted `Edit` write to `docs/issue-3050/reports/
implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md`
(untracked on this branch -- exists only on that other branch) while
checked out there -- result: refused by the `board-gate.sh` PreToolUse
hook:
```
board-gate: writing docs/issue-3050/ requires branch issue-3050/implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0 (current: issue-3050/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4)
board-gate: expected: make .on-the-record/role.json and the current branch name agree on the same issue-<n>/<role>, or remove the stale sidecar.
```
derived: re-checked out this session's own branch
(`issue-3050/implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0`)
and re-attempted a `Bash rm` of an unrelated `docs/issue-3050/` path --
same refusal, same required branch named both times, independent of
which git branch was actually checked out. Confirms `CLAUDE_SKILL`
(fixed in this session's own environment, `printenv CLAUDE_SKILL` --
`implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0`),
not git branch state, is what `board-gate.sh` consults -- the exact root
cause the issue's own second comment names: ownership resolves from the
writing session's own project root, not the path being written; no `cd`,
no branch checkout reaches a foreign record. Non-`docs/issue-3050/` paths
(`spawn.py`, the test file, `docs/handbooks/*`) were not gated this way
and landed directly on PR #3086's branch as commit `80ff89f8`; only the
record itself required this session's own path. Reported here rather than
worked around, per the role-handoff contract's scope-exceeded rule.

**Partial supersession -- decision, not a patch (issue #3050's third,
non-blocking ask).**

canonical: `gh pr view 3101 --json body` (this session's own read) -- PR
#3101's finding: study-companion PR #15 is a section-level correction
inside a larger, mostly-correct foreign record, and `supersedes:` only
supports whole-artifact replacement; applying it there would mark the
entire record non-authoritative.

Decision: **whole-artifact replacement stays the limit of `supersedes:`;
it is not extended to sections in this repair round.**

canonical: `80ff89f8:supersession.py` (untracked on this branch, exists
only on PR #3086's branch) -- `resolve_authoritative()`'s safety property
(a reader with only the merged tree can tell what is authoritative) is
built entirely on `path -> content` lookups; a section inside a record
has no equivalent stable, git-tracked identity the way a file path does
-- headings can be renamed, split, or reordered by the record's own
author in a later revision the correcting session never sees. A
`supersedes: <path>#<heading>`-shaped field would need drift detection
(does a later edit still correspond to the section the correction named)
that the current flat path-graph resolver does not have, and this repair
round did not scope time to design and test that soundly. Naively reusing
whole-file `supersedes:` semantics for a partial correction is worse than
leaving it unhandled: it would mark an entire, mostly-correct record
non-authoritative to express a single-section fix -- the exact failure
this issue's second report warns `supersedes:` exists to prevent,
reproduced against `supersedes:` itself.

**What a section-level correction should do instead, today:** do not set
`supersedes:` on the foreign record. Land the correction as an ordinary
record with no `supersedes:` field -- what study-companion PR #15's
correcting session already did -- and state the exact section and
corrected text in the record's own body, so a human reconciling the
target record next has ready-to-apply text sitting in a merged, citable
record rather than scattered across a PR body or issue comment. This
record does the same thing one level up: it does not mark PR #3086's own
record `supersedes:`-superseded either (that record is not wrong, only
incomplete now that this repair lands on top of it), so it stands as an
ordinary, non-superseding companion record instead, referenced via
`upstream:` above -- the shape this decision recommends, exercised on
this repository's own record rather than only prescribed for the next
session that hits it. A future stage could add a genuinely section-scoped
marker once a stable section-identity contract exists; not attempted
here.

## What did not work

The direct-edit attempt on PR #3086's own record, described above under
"Why" -- refused by `board-gate.sh`, not a design or code defect; the
resolution was writing this session's own record instead of retrying
against the same path.

## Upstream basis

canonical: `gh pr view 3108 --json body,mergedAt` (this session's own
read) -- merged as `0d912bf8` into `main`.

- `docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md`
  (sha `861895f`, untracked on this branch -- exists only on PR #3086's
  branch) -- PR #3086's own record, describing the shape and fix this
  repair round corrects and extends.
- `docs/issue-3050/reports/independent-verification-1.md` (sha
  `0d912bf8`, on `main`) -- the confirmed-and-reproduced must-not B
  finding and the documentation-gap finding this repair round fixes.
- `gh pr view 3101` (this session's own read) -- the second independent
  verification naming the partial-supersession gap.
- `gh issue view 3050 --repo tokenmaxxxer/on-the-record` (this session's
  own read) -- issue body, root-cause comments, and the "Both
  verifications land" comment that spawned this repair round.

## Open findings

None outstanding for this repair round's own scope -- the
partial-supersession gap is a recorded, deliberate limit (see "Why"), not
an open finding needing its own resolution path.

derived: `python3 -m pytest tests/ -q` (PR #3086 branch, commit
`80ff89f8`) -- result:
```
5 failed, 213 passed
```
The failures are in `tests/test_respawn_deliverable_gate.py`
(every case of `AutoRespawnConsultsDeliverableGateTest`) plus
`tests/test_spawn_gate_wiring.py`'s `HooksJsonWiringIsAdditive` class's
pre-existing-commands regression check -- the same names PR #3086's own
record lists as pre-existing and unrelated to
`board.py`/`spawn.py`/`supersession.py`, and the same file the
repair-round spawning task names as PR #3089's to fix, not this repair's.
derived: `python3 -m pytest test/ -q -m "not slow"` (same) -- result:
```
15 failed, 546 passed, 3 xfailed
```
Failing files are `test/test_convention_equivalence.py`,
`test/test_local_dependency_env.py`,
`test/test_spawn_cross_family_skill_selection.py`,
`test/test_spawn_artifact_skill_pairing.py`, and
`test/test_spawn_skill_judge_haiku_timeout_overlap.py` -- same failing
files PR #3086's own record's baseline lists; none touch
`board.py`/`spawn.py`/`supersession.py`.

## Acceptance verification

- supersession-shape acceptance check for issue #3050 — checked: tests/test_supersession_shape.py — result: pass: derived: `python3 -m pytest tests/test_supersession_shape.py -q` (PR #3086 branch, commit 80ff89f8) -- 12 passed in 0.82s
- supersession-marker-probe acceptance check for issue #3050 — checked: gates/probe_supersession_marker.py — result: pass: derived: `python3 gates/probe_supersession_marker.py` (same) -- ok, exit 0
- failed-no-commit-reconciliation acceptance check for issue #3050 — checked: tests/test_failed_no_commit_reconcile.py — result: pass: derived: `python3 -m pytest tests/test_failed_no_commit_reconcile.py -q` (same) -- 19 passed in 0.99s

## Next steps

canonical: this record's own `loop_state: landed` frontmatter field, set
in this same commit -- terminal for this record kind, no further phase
from this session. PR opened per the build-now bypass (`CORE_BUILD_NOW=1`)
carrying only this record; the code fix is commit `80ff89f8`, already
pushed to PR #3086's own branch and not part of this PR's diff. A human
still needs to merge PR #3086 for this issue's acceptance checks to run
against `main`; this PR alone does not close #3050.

skill-verdict: implementation-blueprint — applied: invoked; ran
`prep.py classify --surface backend --external no --logic crud
--asynchronous no --single-file` for the `_push_succeeded()` extraction
(one pure function, one call site, added to an already-large existing
module) -- result: `VETO: single file, single concern, no callers ->
no-structure`, "just write it correctly ... flat is fine". Confirms the
extraction as a bare module-level function (no class, no interface, no
archetype ceremony) was the right call, not an accidental
under-structuring; earlier drafting of this record had instead described
it as "backend/domain-rich" without running the tool, corrected here
after the actual invocation.
skill-verdict: silent-failure-audit — applied: invoked; ran the audit's
Step 1-3 against `spawn._push_succeeded()`/`board.fail_closed_downgrade()`
for the same defect class the fix closes (a status silently falling
through as success). Found `relay.py::ensure_pushed()`'s
`"issue-closed-stale-branch"` return (a 7th possible status) is not in
`_push_succeeded()`'s exclusion tuple, before or after this fix.

derived: `grep -n '"nothing-to-push"\|"push-rejected"\|"pr-create-failed"\|"issue-closed-stale-branch"' spawn.py relay.py`
(PR #3086 branch) -- confirms the tuple names three statuses, not that
fourth one.

derived: `grep -n "CLOSED => never respawn" lifecycle.py` (PR #3086
branch) -- `lifecycle.py:428` refuses to *respawn* when the subject issue
is `CLOSED`, independent of `push_succeeded`. First-pass trace-forward
concluded that made this Unreachable and left it unfixed; a subsequently
dispatched background warrant-hunter (before-landing hunt on this repair
round's own fix) corrected that -- the respawn guard does not touch the
classification itself: `fail_closed_downgrade()` still returned
`progressed` for a round with no new commit and no real delivery,
independent of whether anything respawns on it, which is must-not B's
actual shape. Fixed in a second commit, `74b261e9`: added
`"issue-closed-stale-branch"` to `_push_succeeded()`'s exclusion tuple.

derived: `python3 -m pytest tests/test_failed_no_commit_reconcile.py -q`
(PR #3086 branch, commit `74b261e9`) -- `20 passed`, including the new
`test_closed_issue_stale_branch_reconciles_to_failed_no_commit` (real
`ensure_pushed()`/`_push_succeeded()`, `spawn._subject_issue_state`
stubbed to `CLOSED`).
skill-verdict: test-derivation — applied: invoked; routed the
requirement ("`push_succeeded` must reflect `ensure_pushed()`'s real
7-valued status, not a hand-supplied boolean") to equivalence
partitioning over that status domain -- High risk (A: this is must-not
B, a silently-lost-work-shaped failure). Partition list: 7 named
statuses partition into 2 outcome classes (success:
`pushed`/`pr-opened`/`pr-already-open`/`issue-closed-stale-branch`;
failure: `nothing-to-push`/`push-rejected`/`pr-create-failed`).
`PushSucceededDerivationLiveTest`'s two cases exercise one partition from
each outcome class (`nothing-to-push` -- the must-not B defect itself;
`pr-opened` -- a regression pin) through real git operations, not a
synthetic status string, per the repair round's explicit instruction
that a test setting the flag directly does not close the gap. EP
coverage against the full 7-partition list (2 of 7 = 29%, derived: count
the two named cases against the seven-status list cited above) by direct
real-path derivation; the other 5 are not separately exercised through
`ensure_pushed()` in this repair round -- named exclusion, not a silent
gap: `push-rejected`/`pr-create-failed` were already covered at the
boolean level by the pre-existing hand-typed test suite (`board`-level,
not `ensure_pushed()`-level), and constructing real git/gh fixtures for
`pushed`/`pr-already-open`/`issue-closed-stale-branch` was judged out of
this repair round's named scope (the one confirmed defect was
`nothing-to-push`).
