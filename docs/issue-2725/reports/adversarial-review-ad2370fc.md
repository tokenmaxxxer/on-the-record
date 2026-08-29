---
issue: 2725
role: adversarial-review-ad2370fc
author: adversarial-review-ad2370fc
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2725/reports/architecture-coupling-classification+adversarial-review-b98326e0.md
    sha: b5ca6c0c3c7eb410d5ee36c50f5e45a957f65aa3
  - path: board.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
  - path: gates/flows.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
  - path: test/test_board_front_skill.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
---

# issue-2725 — adversarial-review-ad2370fc record

## What was done

Independently verified PR #2738 (`issue-2725: fix 3-way partial-tie gap
in board.py front-record tie-break`, head
`b5ca6c0c3c7eb410d5ee36c50f5e45a957f65aa3`, `Closes #2725`, state OPEN —
canonical: `gh pr view 2738 --json title,body,state,headRefOid,files`).
This PR supersedes the closed PR #2735, whose defect (a 3-way
partial-tie in the tie-break guard could return an arbitrary winner with
`ok=True`) was found by `docs/issue-2725/reports/independent-verification-2.md`
(merged to main). Per the task's instruction, this record does not
re-verify #2735's claims — only #2738's new claims — using a disposable
`git worktree` fetched from the PR's own head, never this session's
tracked tree. PR #2738 adds one new test file, untracked on this
session's own branch (it exists only on that PR's branch) — it is not
cited by backtick path anywhere below except once, annotated, in the
Upstream basis section.

**Setup.** canonical: `git fetch origin a366617aa7ea5b8a10cbeaafbd419064b2cedf77`
(PR #2735's head) into `/tmp/pr2735check` (the "OLD guard"), and
`git fetch origin pull/2738/head:pr-2738-check` into `/tmp/pr2738check`
(the "NEW guard"). Confirmed `/tmp/pr2735check/board.py`'s `_front_skill`
still has the buggy line `if len(candidates) < 2 or len({sha for _, sha
in candidates}) == 1: return None, False` (read directly, board.py:632).

**Claim 1 — the new regression test fails on the old guard, passes on
the new one.** Copied PR #2738's new test file (read from the PR
worktree) verbatim into the `/tmp/pr2735check` worktree (leaving
`board.py` untouched there) and ran only the new test:
```
$ cd /tmp/pr2735check && python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q
FAILED test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide
AssertionError: Tuples differ: ('b', True) != (None, False)
1 failed in 0.91s
```
Then ran the identical test against the PR's own worktree:
```
$ cd /tmp/pr2738check && python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q
1 passed in 0.85s
$ python3 -m pytest test/test_board_front_skill.py -q
8 passed in 0.85s
```
derived: the test fails on the exact guard it targets and passes on the
fixed one — asymmetric result, not a test that would pass on both
(which would pin nothing).

**Claim 2 — an ambiguous case the new test does not cover, checked for a
silent guess.** The new test only exercises a 3-candidate, 2-way tied
subset (`b`/`c` tie, `d` later). Wrote three scenarios that test does not
construct and ran them against the PR's `board._front_skill` directly
(`/tmp/verify_extra_scenarios.py`, a disposable script, executed inside
the PR worktree, writes only to `tempfile.TemporaryDirectory` scratch
repos):
```
$ cd /tmp/pr2738check && python3 /tmp/verify_extra_scenarios.py
A: 3-way tie block of 4: front=None ok=False
B: unique earliest, tie for 2nd (should resolve to a,True): front='a' ok=True
C: 5 candidates, tie at min among 2, 3 later distinct: front=None ok=False
```
Scenario A (three of four candidates tie for earliest, not two) and
scenario C (five candidates, two tie for earliest, three later and
distinct) both correctly report `ok=False` rather than guessing.
Scenario B (only a later position ties; the earliest is unique) correctly
still resolves — confirming the fix is not merely more conservative
across the board, it specifically targets ambiguity at the *winning*
position. Ran the same script against the OLD guard for contrast:
```
$ cd /tmp/pr2735check && python3 verify_extra_scenarios.py
A: 3-way tie block of 4: front='a' ok=True
B: unique earliest, tie for 2nd (should resolve to a,True): front='a' ok=True
C: 5 candidates, tie at min among 2, 3 later distinct: front='a' ok=True
```
The old guard guesses in every ambiguous shape tried (A and C), not only
the specific 3-candidate shape the new test encodes — the fix generalizes
rather than patching the one reported case. Read the new guard's logic
(`board.py`, `/tmp/pr2738check`, the `candidates.sort(...)` block
followed by `if order.get(candidates[0][1], len(order)) ==
order.get(candidates[1][1], len(order))`): since `candidates` is sorted
ascending by commit-order index, any tie for the minimum places the tied
elements at positions 0 and 1, so comparing those two positions detects
a tie for the *minimum* regardless of how many total candidates exist or
how many share that minimum — this is why scenarios A and C (different
tie sizes, different total candidate counts) both resolved correctly
without a corresponding dedicated test for each shape. No case was found
where the new guard silently guesses.

**Claim 3 — the old closed-set fallback is fully gone, not relocated.**
```
$ cd /tmp/pr2738check && grep -n "for r in (" board.py
exit=1  (no match)
$ grep -rn "PRODUCT_DISCOVERY\|TECHNICAL_FEASIBILITY\|RETIRED_SKILLS\|FALLBACK_SKILLS" --include="*.py" .
(no output)
```
`grep -rn "product-discovery\|technical-feasibility"` across the worktree
turns up only: the two retired names inside `_front_skill`'s and
`_record_add_commit`'s own docstrings (narrating the history, not
executable), unrelated pre-existing hits in `gates/gates.py`,
`gates/delegation_metrics.py`, `test/test_board_ownership_report.py`,
`test/test_convention_equivalence.py` (a different function,
`role == "technical-feasibility"`, not `_front_skill`'s fallback), and
`.claude-plugin/marketplace.json` (unrelated plugin package names). No
constant, config file, or per-entry file holds the two names as a
membership list.

**Claim 4 — `gates/flows.py`'s call site behaves as the record says, and
leaving `ok=False` undistinguished there is harmless.**
```
$ diff /tmp/pr2735check/gates/flows.py /tmp/pr2738check/gates/flows.py
(no output — byte-identical)
```
PR #2738's record states this call site was "left unchanged" from PR
#2735 (which independent verification 1 already reviewed and judged
sound); the byte-identical diff confirms that claim directly rather than
by re-trusting the record's prose. Read the call site
(`gates/flows.py:419-431`): `front, _front_ok = spawn._front_skill(...)`
is computed once per subject; the loop only ever compares `front ==
skill`. When `front is None` — true both when `ok=True` (no front
record) and `ok=False` (cannot decide) — the comparison never matches
any skill name, so `stage_source` stays `None` in both cases; there is no
code path where `_front_ok`'s value changes what `stage_source` becomes.
Traced `stage_source` forward: it feeds `_stage_for(stage_source,
issue_state)` (`gates/flows.py:442`), which lands in
`flows_out.append({"stage": ..., "stage_derived": ..., ...})` — consumed
only by `flows()` (`gates/flows.py:528`), which either JSON-dumps the
payload or prints a `flows: N건` / `issue-N: stage` display line
(`gates/flows.py:539-541`). Grepped for other callers of
`flows_payload`: none found. This is a read-only reporting/dashboard
path with no gate or approval decision downstream — confirms the "only
drives a dashboard label" claim, not merely repeats it. Also confirmed
`board.py`'s `approve_scope` (the actual gate that writes the
scope-approval commit) is untouched by this PR relative to #2735:
```
$ diff <(sed -n '/^def approve_scope/,/^def /p' /tmp/pr2735check/board.py) <(sed -n '/^def approve_scope/,/^def /p' /tmp/pr2738check/board.py)
(no output — identical)
```

**Claim 5 — full test suite, failing sets compared as sets of names, not
counts, against `origin/main`.**
```
$ cd /tmp/pr2738check && python3 -m pytest test/ -q
15 failed, 403 passed, 6 xfailed in 2.48s
$ cd /tmp/mainwt (origin/main, f4db9600 + the two verification merges) && python3 -m pytest test/ -q
15 failed, 395 passed, 6 xfailed in 2.59s
$ diff <(sort failed_main.txt) <(sort failed_pr2738.txt)
(no output — IDENTICAL SETS)
```
Both runs produced the exact same 15 `FAILED` test IDs (compared with
`diff` on sorted `FAILED ...` lines, not just the numeric `15`); the
`403 - 395 = 8` delta matches the 8 tests PR #2738 adds in its new test
file exactly. No regression.

**Aside — branch staleness, not a defect.** PR #2738's branch
(`976896e1f600fdad906e4d6a6f3abe3af4097fb5`) is cut from `f4db9600`, two
commits behind current `origin/main` (missing the two
independent-verification merges, `d5651f22` and `3800b553`). A two-dot
`git diff main..HEAD` misleadingly shows those two files as deletions; a
correct three-dot `git diff main...HEAD` shows the PR only touches
`board.py`, `gates/flows.py`, one new test file, and its own two new
record files — matching `gh pr view`'s own `files` list. `git merge
--no-commit --no-ff origin/main` inside the PR worktree auto-merged
cleanly with no conflicts. Not a blocker; noted for the record only.

## Why

The prior round's defect survived one full verification pass
(independent-verification-1) because its test suite only exercised the
2-candidate tie shape its author had thought of; a full 3-candidate
partial tie went uncovered. Repeating that same method here — re-running
only the cases PR #2738's own new test constructs — would repeat the
miss in the same way, just one layer later. The highest-value
independent checks were therefore: (a) prove the new test actually
discriminates old-vs-new rather than passing regardless (a common way an
after-the-fact regression test looks convincing but pins nothing), and
(b) construct additional tie shapes (different tie-block sizes, more
total candidates, a tie at a *non-winning* position) that the new test
does not itself cover, to check whether the general algorithm — not just
the one reported input — closes the gap.

## What did not work

None. derived: re-ran `python3 -m pytest` inside `/tmp/pr2738check`
against the PR's new test file (the same execution cited under Claim 1)
— result: `8 passed in 0.85s` — every independent reproduction in this
record (old-guard fail / new-guard pass, the three additional tie
shapes under Claim 2, the closed-set grep under Claim 3, the `flows.py`
byte-diff under Claim 4, and the two full-suite runs under Claim 5)
converged on PR #2738's claims on the first correctly-scoped attempt,
with no divergence requiring a second attempt or a different approach.

## Upstream basis

`board.py` and `gates/flows.py` at PR #2738's actual head content, plus
its new test file, `test/test_board_front_skill.py` (untracked on this
session's own branch — exists only on PR #2738's branch), verified via
`/tmp/pr2738check`, a worktree fetched from `pull/2738/head`, landing at
local commit `976896e1f600fdad906e4d6a6f3abe3af4097fb5 issue-2725: fix
3-way partial-tie gap in board.py front-record tie-break`; the PR's
visible head SHA is `b5ca6c0c3c7eb410d5ee36c50f5e45a957f65aa3`, one
commit later, adding only a deviation-log entry — `git diff 976896e1
b5ca6c0c` touches no code file. canonical: `gh pr view 2738 --json
headRefOid,files`. The subject's own record for this PR,
`docs/issue-2725/reports/architecture-coupling-classification+adversarial-review-b98326e0.md`
(untracked on this session's own branch — exists only on PR #2738's
branch), was read in full via the same worktree, and its narrative
matches every independently-reproduced result above; its own citations
(the defect quote, the `verdict: pass` line) were not taken on faith but
checked against the live diff and test runs in this record.

## Open findings

None. All five of the task's specific verification points reproduced
independently with results matching PR #2738's claims, and the
additional adversarial scenarios beyond the new test's own coverage
(three-way tie block, five-candidate partial tie, tie-at-non-winning-
position) did not surface a silent-guess case the fix misses.

## Next steps

None for this verification. PR #2738 is ready to land on its own
technical merits; this record does not itself land it.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked, though only after
the review work below was already written — a deviation, logged at
`docs/issue-2725/reports/adversarial-review-ad2370fc/deviation-log/20260829T160017321207-8ca844d18bc81d8a.md`.
canonical: this turn's own Skill-tool result for `adversarial-review` —
its procedure states a session structurally separate from the builder
already satisfies the skill's core mechanism, which this session was
(evaluating PR #2738, a different session's deliverable) — matching the
"receive only the deliverable, incentivized to find everything wrong"
posture this record independently applied by re-deriving PR #2738's
specific claims from a fresh worktree rather than re-trusting the
subject record's prose or citations.
skill-verdict: work-in-english — not-applicable: not invoked via the
Skill tool this session; this record and all repository-bound work were
already written in English without needing the skill's guidance invoked
explicitly.
other mounted skills: not triggered (verify-finding-record and
defect-verification-independence-from-upstream-verdicts apply to
`docs/issue-<n>/reports/defect-verification.md`-style reproduction
records for a review requirement or qa defect report; this is an
adversarial-review verification record under the adversarial-review
skill's own report path instead).
