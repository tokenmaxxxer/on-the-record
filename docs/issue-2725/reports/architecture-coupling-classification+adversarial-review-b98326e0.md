---
issue: 2725
role: architecture-coupling-classification+adversarial-review-b98326e0
author: architecture-coupling-classification+adversarial-review-b98326e0
skills: architecture-coupling-classification (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: fix
breaking: true
verdict: pass — the guard is rewritten to check whether the earliest commit position is uniquely held after sorting, not whether the whole candidate set collapses to one sha; the 3-way partial-tie failure mode from PR #2735's CHANGES review no longer reproduces
upstream:
  - path: board.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: gates/flows.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: test/test_board_front_skill.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
---

# issue-2725 — architecture-coupling-classification+adversarial-review-b98326e0 record

## What was done

This record revises PR #2735 (`board.py`'s `_front_skill` closed-set
fallback replacement, code at `e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2`)
in response to the CHANGES review on that PR — canonical: `gh pr view
2735 --json comments` (review comment body). The review cited a
confirmed defect found by independent verification 2 (branch
`issue-2725/independent-verification-2`, untracked on this branch —
its record lives only on that unmerged branch, read via `git show
origin/issue-2725/independent-verification-2:docs/issue-2725/reports/independent-verification-2.md`,
not present on disk here); independent verification 1 found nothing.

**The defect.** `_front_skill`'s tie-break guard was:
```python
if len(candidates) < 2 or len({sha for _, sha in candidates}) == 1:
    return None, False
```
This only fires when *every* candidate shares one commit. With 3+
rootless records where a *subset* ties for the earliest introducing
commit and a later, untied candidate also exists, the guard never fires
— the whole set is not one sha — so the sort still ran and returned an
arbitrary winner among the tied pair with `ok=True`, the exact
silently-plausible-answer shape issue #2725's must-not clause forbids.

**Reproduced before fixing, on the unfixed PR #2735 code
(`e36c3ac5`)** — three rootless records `b`, `c`, `d`; `b` and `c` added
in the same commit (genuine tie for earliest), `d` added later in its own
commit:
```
$ python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q
AssertionError: Tuples differ: ('b', True) != (None, False)
```
matches independent verification 2's own reproduction exactly (`front,ok:
b True`).

**The fix** (`board.py`, `_front_skill`): after sorting candidates by
commit-log position, check whether the winning (minimum) position is
uniquely held — not whether the whole candidate set collapsed to one
sha:
```python
candidates.sort(key=lambda rc: order.get(rc[1], len(order)))
if order.get(candidates[0][1], len(order)) == order.get(candidates[1][1], len(order)):
    return None, False
return candidates[0][0], True
```
This subsumes the old all-same-sha check (if every candidate shares one
commit, the top two also share that commit's position) while additionally
catching the partial-tie case the old guard missed.

**Re-verified after fixing:**
```
$ python3 -m pytest test/test_board_front_skill.py -q
8 passed in 0.85s
$ python3 -m pytest test/ -q
15 failed, 403 passed, 6 xfailed in 3.00s
```
The 15 failures are pre-existing and unrelated — derived: ran
`python3 -m pytest test/ -q` on this tree with `board.py`,
`gates/flows.py`, and `test/test_board_front_skill.py` stashed back to
`origin/main`'s state, then again with those three files restored, then
`sort`ed both runs' `FAILED` lines and `diff`'d them — output
`IDENTICAL FAILURE SET`, both lists 15 lines, no line differs.

**Added the 3-way case to `test/test_board_front_skill.py`**
(`test_three_way_partial_tie_for_earliest_reports_cannot_decide`) — the
existing 7-test suite only constructed 2-candidate scenarios (a single
tie, or a single non-tied pair), so passing it could not have proven this
failure mode absent; it now can.

**Issue's three acceptance checks, re-run against the fixed code:**
- `grep -n 'for r in (' board.py` — no match (exit 1), same as before
  this round's fix; the hardcoded-name-list removal was never in
  question, only the tie-break's completeness.
- Two-rootless-record and three-rootless-partial-tie subjects
  constructed directly (see reproduction above and the new test) — both
  callers receive `(None, False)` for the unresolvable case and a
  concrete `(name, True)` only when the winner is uniquely earliest.
- `approve_scope` (`board.py`) and `gates/flows.py`'s comparison: both
  already exercised by the existing
  `ApproveScopeFrontRecordMessageTest` cases, re-run above as part of the
  8-test pass — unaffected by this round's change, since the guard
  rewrite changes only which inputs are treated as ambiguous, not the
  shape of what `approve_scope`/`flows.py` do with `(front, ok)`.

**`gates/flows.py`'s call site — explicitly assessed, not silently
left.** Independent verification 1 read `gates/flows.py:416-424` in full
and judged it sound: `ok=False` and `ok=True, front=None` are
deliberately left un-distinguished at that call site because it only
drives a dashboard `stage_source` label, not a gate decision — the code
comment at `gates/flows.py:420-423` states this explicitly (checked:
`sed -n '415,430p' gates/flows.py` in this tree — result: the comment is
present verbatim). This round changes nothing there; noting it here so a
reader does not have to wonder whether the CHANGES review's silence on
`flows.py` meant it was missed. It was read and judged sound, not
skipped.

## Why

The reviewer's diagnosis is correct: "whether all candidates share one
commit" and "whether the minimum position is uniquely held after
sorting" are different predicates, and only the second one is what the
issue's must-not clause actually needs. Checking `candidates[0]` against
`candidates[1]` after the sort (rather than re-deriving a `len(set(...))
== 1` count over the whole list before sorting) is the minimal change
that closes the gap: it is exactly the comparison the sort already
produces, at no extra cost, and it strictly subsumes the case the old
guard handled (all-same-sha implies the top two share a position too).

## What did not work

None.

## Upstream basis

See frontmatter `upstream:`. The design (rootless-candidate ranking by
introducing-commit order, `(front, ok)` return shape, both call-site
rewrites) is unchanged from PR #2735's own code at `e36c3ac5`; this round
only tightens the tie-break guard and adds the regression test. The
finding being fixed is independent verification 2's Open finding 1
(untracked on this branch, cited by branch + path above, not by
frontmatter `upstream:` since it is not present on disk here).

## Open findings

None — the 3-way partial-tie case now reports `(None, False)`, matching
the issue's must-not clause; the 15 pre-existing test failures are
unrelated to this issue (identical set before/after, derived above).
Independent verification 2's finding 2 (minor, non-blocking: one `git
log` subprocess per rootless candidate plus one whole-history `git log`
call) was explicitly noted as non-blocking by that verification and is
not addressed by this round.

## Next steps

None — `loop_state: landed`.

## Skill verdicts

skill-verdict: architecture-coupling-classification — not-applicable: this round is a targeted correctness fix to an already-classified coupling site (the coupling classification itself, from the original delivery, is unchanged); no new coupling relationship was introduced or reclassified.
skill-verdict: adversarial-review — applied: invoked; reading the CHANGES review and independent verification 2's finding as an adversarial account rather than assuming the prior session's own record was complete, and independently re-deriving the before/after result rather than re-pasting the verification's output.
derived: `python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q` re-run this turn against the unfixed code — result: `AssertionError: Tuples differ: ('b', True) != (None, False)` (quoted in full in "What was done").
other mounted skills: not triggered — no chart/visualization surface (dataviz), no settings.json change (update-config), no keybinding change (keybindings-help), no separate code-review/simplify invocation requested, no Claude/Anthropic-API surface (claude-api), no app-launch requested (run), no new CLAUDE.md requested (init), no separate security-review requested. work-in-english: guidance-only per the spawn prompt; not invoked via the Skill tool, but this record and all repository-bound work were already written in English.
