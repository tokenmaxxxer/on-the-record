---
issue: 2978
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: 34b954737fa232add2f36a83502f86ae4b35791d
loop_state: landed
type: code
breaking: true
verdict: fail
upstream:
  - path: gates/spawn_on_pr.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
  - path: gates/closure_sweep.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
---

# issue-2978 — independent-verification-1 record

## What was done

Independently verified PR #3012 (branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`, head
`34b954737fa232add2f36a83502f86ae4b35791d`), issue #2978's fix for two
watchdog checks (`spawn_on_pr.missing_verification()`,
`closure_sweep.find_violations()`) that reported an ordinary state as a
violation.

canonical: `gh pr view 3012 --json title,body,headRefName,state,commits`
output fetched this turn (state: OPEN, head:
`34b954737fa232add2f36a83502f86ae4b35791d`).

Fetched the PR head into an isolated `git worktree`
(`git fetch origin pull/3012/head:pr-3012-check-iv1 && git worktree add
/tmp/pr3012-iv1 pr-3012-check-iv1`) and re-ran all four issue-#2978
acceptance checks myself inside it, without citing PR #3012's own or
any other prior review's pasted results as evidence:

- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
  ```
  1 passed in 0.97s
  ```
- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
  ```
  1 passed in 0.88s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
  ```
  1 passed in 0.89s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
  ```
  1 passed in 0.93s
  ```
- acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py -q` (PR's own claimed regression check) — result:
  ```
  33 passed in 0.87s
  ```

canonical: `gates/spawn_on_pr.py` lines 183-221 (`subject_deliverable_record()`
docstring and body) and lines 356-476 (`missing_verification()`), read in
full this turn inside `/tmp/pr3012-iv1` — audited directly against the
issue's must-not list (no age/window/issue-number distinction; genuine
anomaly must keep reporting).

Beyond the four acceptance checks, independently reproduced a defect in
the spawn-on-pr half by constructing a case not covered by the PR's own
tests, run this turn inside `/tmp/pr3012-iv1`:

```
board = {"issue-50001": {"implementation": {"author": "carol"},
                          "conformance-review": {"author": "dave"}}}
```

- `subject_deliverable_record(board["issue-50001"])` — result: `(None, {})`
- `verification_deficit(board["issue-50001"])` — result: `2`
- `spawn_on_pr.missing_verification(root, issue_states={50001: "OPEN"},
  pr_index={})` with `spawn.board` mocked to return the above and
  `_watchdog_note_unmappable_subject_branch` mocked to return `True` —
  result: `{}`; `print` call list: `[]`; marker `called`: `False`.

derived: this is exactly the ambiguous "2+ non-verifying records" case
`subject_deliverable_record()`'s own docstring names (lines 194-209) as
structurally distinct from "no deliverable landed" — both collapse to
the same `(None, {})` return, but only one of them means "no PR ever
existed." The fix's own comment at lines 466-467 ("Once a deliverable
record HAS landed (`_slug` is not `None`), its PR necessarily existed")
states a converse that is false for the ambiguous case: a deliverable
demonstrably DID land (that's why 2 non-verifying records exist), yet
`_slug is None` there too, so line 474's `if _slug is None: continue`
silently drops what should be a genuine unmappable-branch report — the
exact #2379-class anomaly the issue's must-not requires to keep
reporting.

Confirmed this precondition is live, not contrived — scanned the real
board checked out in the worktree, run this turn:

```python
board = spawn_on_pr.spawn.board(Path("."))
ambiguous = [s for s, sb in board.items()
             if len([1 for _, fm in sb.items()
                     if fm.get("verifies_subject") != "true"]) > 1]
len(board), len(ambiguous)
```

derived: result `(700, 146)` — 146/700 = 20.9% of currently-tracked
subjects (e.g. `issue-1160`, `issue-1163`, `issue-1165`, `issue-1174`,
`issue-1199`, `issue-1202`, `issue-1490`, `issue-1510`) sit in the
ambiguous shape under which this fix would suppress a genuine
unmappable-branch report, for any such subject whose issue is OPEN and
whose branch later becomes genuinely unmappable.

Separately audited the closure-sweep half (`_pr_is_record_only()`,
`gates/closure_sweep.py:86-102`) and confirmed it is sound: it reuses
`check_runner.pr_diff_paths()` / `check_runner.touches_implementation_paths()`
verbatim rather than a new branch-name/issue-age heuristic —

canonical: `git log -p --follow -S"def touches_implementation_paths" --
gates/check_runner.py`, run this turn inside `/tmp/pr3012-iv1` — shows
the function introduced in commit `7961f712` (issue #2974, PR #2994),
predating PR #3012 by several commits.
derived: `git diff 005a3ec6 f0d8c2eb --stat`, run this turn, output:
```
 gates/closure_sweep.py                             |  39 +++++
 gates/spawn_on_pr.py                               |  16 ++
 test/test_watchdog_heartbeat_noise.py              |  20 ++-
 ...est_watchdog_normal_state_not_violation_2978.py | 167 +++++++++++++++++++++
 4 files changed, 239 insertions(+), 3 deletions(-)
```
`gates/check_runner.py` is absent from this list — confirms it is only
imported by PR #3012's diff, not redefined or reimplemented.

## Why

Treated this as an independent verification rather than a rubber-stamp
of the PR's own pasted test-plan output: re-derived every acceptance
check from a freshly fetched worktree, and looked for at least one
case beyond the PR's own fixtures on the half of the fix
(`subject_deliverable_record()`'s collapsed return value) whose own
docstring flagged a second code path collapsing to the same sentinel.

canonical: the reproduction transcript in `## What was done` above
(`subject_deliverable_record()` → `(None, {})`, `missing_verification()`
→ `{}`/no print/no marker call), all produced this turn inside
`/tmp/pr3012-iv1` — that is where the defect in `## Open findings`
below was located, on a case the PR's own acceptance test 2 does not
construct (it only covers the single-record, non-ambiguous "no PR yet"
case).

## What did not work

None.

## Upstream basis

PR #3012, branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`:
- `f0d8c2e` — the code fix (`gates/spawn_on_pr.py`, `gates/closure_sweep.py`,
  `test/test_watchdog_heartbeat_noise.py`, and one new test file)
- `eb05833` — PR #3012's own record
- `34b9547` — PR #3012's own deviation log (PR head)

## Open findings

canonical: the reproduction transcript and board scan in `## What was
done` above, all produced this turn inside `/tmp/pr3012-iv1`.

1. **spawn-on-pr's no-PR-yet discriminator over-suppresses on ambiguous
   legacy subjects.** `gates/spawn_on_pr.py:474` (`if _slug is None:
   continue`) conflates "zero non-verifying records" (genuinely no
   deliverable yet — the case this PR fixes) with "more than one
   non-verifying record" (ambiguous; `subject_deliverable_record()`
   already documents this second case at lines 198-209 and deliberately
   refuses to guess which one is the deliverable). In the ambiguous
   case a deliverable demonstrably did land, so an unmappable branch for
   it is a genuine anomaly that must still print per the issue's
   must-not — instead it is silently swallowed.
   derived: reproduced directly in `## What was done` above
   (`missing_verification()` → `{}`, no print, no marker call); board
   scan there shows this precondition on 146/700 subjects (146/700 =
   20.9%) of the live board's currently-tracked subjects, not
   theoretical.

   Resolution path: distinguish "zero non-verifying records" from
   "ambiguous, 2+ non-verifying records" directly inside
   `missing_verification()` (e.g. check the candidate count rather than
   reusing `subject_deliverable_record()`'s already-collapsed `(None,
   {})`), plus a new acceptance case constructing the ambiguous
   multi-record board shape. Not fixed in this record — this session's
   task is independent verification, not remediation.

2. closure-sweep half: no open finding. Sound reuse of issue #2974's
   existing diff-content signal — derived: `git log -p --follow
   -S"def touches_implementation_paths" -- gates/check_runner.py` and
   `git diff 005a3ec6 f0d8c2eb --stat`, both cited with output in
   `## What was done` above, confirm the function predates PR #3012 and
   is only imported, not a new heuristic.

## Next steps

acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` (and
the three sibling `-k` runs for `spawn_on_pr_genuinely_missing_branch`,
`closure_sweep_record_after_merge`, `closure_sweep_genuine_violation`)
— result:
```
1 passed in 0.97s
1 passed in 0.88s
1 passed in 0.89s
1 passed in 0.93s
```
(full individual transcripts already given in `## What was done`.)

All four issue-#2978 acceptance checks succeed as written against PR
#3012's head. This record's own `verdict: fail` frontmatter is driven
by finding 1 above, a gap those four checks do not exercise (they only
cover the single-record, non-ambiguous case) — not by any acceptance
check failing. `loop_state: landed` marks this verification round as
concluded, with the finding routed to a coding session per `## Open
findings` above; no further action from this record itself.

Route open finding 1 above to a coding session against issue #2978 (or
a follow-up issue) before the spawn-on-pr half can be considered to
satisfy its must-not requirement.

skill-verdict: work-in-english — applied: invoked; wrote this record, all commit messages, and all in-session commands/comments in English per the policy
skill-verdict: defect-verification-severity-band-assignment — applied: invoked; banded the spawn-on-pr finding as **degrading** (criterion: degrades core functionality without halting the system — the watchdog keeps running and my own review was not blocked, but a required violation report is silently dropped for 20.9% of live subjects, derived above), not blocking (nothing halts) and not cosmetic (it is a required-signal miss, not a polish gap); this band is held independent of the finding's narrow-precondition framing (rule 7) and of the otherwise-clean closure-sweep half (rule 6)
skill-verdict: verify-finding-record — not-applicable: this session's assigned record area is `docs/issue-2978/reports/independent-verification-1.md` (this file); `docs/issue-2978/reports/defect-verification.md` (untracked path — this skill's own target, not created by this session) is where that skill writes exclusively, which this task does not use
skill-verdict: observability-phase-trace — not-applicable: this task audits a landed fix via independent verification, not a phase-2 implementation record's signal set against a phase-1 methodology
skill-verdict: issue-retrospective-timeline-comprehensibility-and-subtraction-rules — not-applicable: this record is a single verification round with its own frontmatter/verdict, not a records-only cross-skill retrospective spanning the subject issue
skill-verdict: market-analysis-mece-proposal — not-applicable: this session reviews already-delivered code (phase-2), not a phase-1 proposal's section structure
other mounted skills: not triggered
