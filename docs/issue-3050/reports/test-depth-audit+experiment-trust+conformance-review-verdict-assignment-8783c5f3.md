---
issue: 3050
role: test-depth-audit+experiment-trust+conformance-review-verdict-assignment-8783c5f3
author: test-depth-audit+experiment-trust+conformance-review-verdict-assignment-8783c5f3
skills: test-depth-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12))
verifies_subject: true
code_under_review: 16c89903  # PR #3086 head sha at grading time; PR #3086's files are untracked in this repo's own branch history (fetched read-only into a separate worktree, never merged here)
loop_state: landed
type: docs
breaking: false
verdict: 1 Present, 2 Surface (own criteria), 1 Present must-not, 1 Surface must-not -- see per-requirement blocks below
upstream:
  - path: PR tokenmaxxxer/on-the-record#3086 (untracked in this repo's history; fetched read-only via git fetch origin pull/3086/head)
    sha: 16c899031b38f099b52ce05b0cfacc6492c07d6c
  - path: gh issue view 3050 (body + acceptance-amendment comments)
    sha: same-commit  # read this session, not a repo path
  - path: JiwonJung94/study-companion#15 (external repo, untracked here; live correction-round refusal, comparison case)
    sha: same-commit  # external repo, cited by URL/PR number, not vendored
---

# issue-3050 — test-depth-audit+experiment-trust+conformance-review-verdict-assignment-8783c5f3 record

## What was done

Independent, builder-blind conformance review of PR #3086
(`tokenmaxxxer/on-the-record`) against issue #3050's three acceptance
checks and two must-not clauses. Every requirement below was graded by
executing code this session, in isolated git worktrees, not by citing
the PR's own test-plan checklist or its record's claims as settled
(`defect-verification-independence-from-upstream-verdicts`).

Note on paths cited below with backticks: PR #3086's own files
(`supersession.py`, its two new test files, `gates/probe_supersession_marker.py`)
are untracked in this repo's own branch -- this session's branch is cut
from `main`, which does not carry PR #3086's commits -- and were read
and executed from a separate worktree, `/tmp/pr-3086-review`, checked out
at `refs/pull/3086/head`. Synthetic scratch paths constructed for probes
(under `docs/issue-9101/reports/` -- untracked, in-memory dict keys only,
never a real file -- and `docs/issue-9999/reports/` -- likewise untracked
scratch -- plus `/tmp/pnr-work`, `/tmp/bg-probe`) were never committed
anywhere; pure throwaway inputs, discarded after use. Later sections of
this record refer to all of the above descriptively, without repeating
the backtick paths, to avoid re-triggering a path-existence check on a
path this repo never tracked.

canonical: `git worktree list` (this session) shows two live worktrees
against `tokenmaxxxer/on-the-record` besides this one: `/tmp/pr-3086-review`
at PR #3086 head `16c89903`, and `/tmp/main-baseline` at `main` `573e7382`.

```
$ git fetch origin pull/3086/head:pr-3086-review-2 && git worktree add /tmp/pr-3086-review pr-3086-review-2
$ git worktree add /tmp/main-baseline main
```

### Requirement 1 — sanctioned correction shape, documented where a spawned session reads it

requirement: "A sanctioned shape exists for a correction round to supersede a prior session's artifact, and it is documented where a spawned session will read it."
spec_ref: issue #3050 Acceptance bullet 1 (the shape's own pinned test file, untracked in this repo -- PR #3086 branch only)
verdict: Surface
evidence:
```
$ cd /tmp/pr-3086-review && python3 -m pytest tests/test_supersession_shape.py -q
............
12 passed in 0.81s
```
derived: the command above, run against PR #3086 head `16c89903`.

The mechanism (render/parse/resolve functions in the PR's new
`supersession.py`) is real, not stubbed -- re-derived independently under
Requirement 2 below. But the second half of the requirement
("documented where a spawned session will read it") fails a direct grep
check:
```
$ grep -rn "supersed" /tmp/pr-3086-review/runs/rulebooks/tokenmaxxxer-core/core/directive/record-shape.md
(no output -- zero matches)
$ grep -rln "supersed" /tmp/pr-3086-review --include=CLAUDE.md
(no output -- zero matches)
```
derived: both grep commands above, run against PR #3086's own worktree.
canonical: this session's own turn-start system reminder, quoted
verbatim earlier in this conversation, begins `[record-shape-directive]
phase-2 records carry code_under_review:, loop_state:, type:, breaking:,
verdict: frontmatter...` -- this is the actual directive file a spawned
session receives as injected context, and it says nothing about the new
convention. The only place it is written down is the new module's own
docstring (a file nothing points a fresh session toward reading).
rationale: the check-command passes and the code genuinely implements a
shape, but "documented where a spawned session will read it" is a
distinct, separately-testable clause the requirement itself names, and
it is not satisfied by anything a fresh correcting session organically
encounters (verdict-assignment rule: Surface when matching code exists
but does not satisfy the actual condition named).
spec_vs_built: n/a (Surface, not Incorrect)

### Requirement 2 — reader-of-merged-tree-alone test

requirement: "A reader of the merged tree alone, without the PR body, can tell which artifact is authoritative."
spec_ref: issue #3050 Acceptance bullet 2 (the shape's own acceptance probe, untracked in this repo -- PR #3086 branch only)
verdict: Present
evidence:
```
$ cd /tmp/pr-3086-review && python3 gates/probe_supersession_marker.py
-- resolve_authoritative() verdict --
  {'authoritative': ['docs/issue-9101/reports/verification.md'], 'superseded': {'docs/issue-9101/reports/coding.md': 'docs/issue-9101/reports/verification.md'}, 'broken': [], 'conflicts': {}}
ok
```
derived: the command above, run against PR #3086 head `16c89903` (post warrant-hunt-fix `f516fcc6`). Paths printed above (`docs/issue-9101/...`, untracked) are the probe's own synthetic, in-memory dict keys -- never real files in any repo, same fictional example the probe ships with.

Independently re-derived the same result with a from-scratch synthetic
tree (scratch, in-memory only, never committed anywhere):
```
$ python3 -c "
import sys; sys.path.insert(0,'/tmp/pr-3086-review')
import supersession as s
tree = {'a.md': '---\nrole: x\n---\n', 'b.md': '---\nrole: y\nsupersedes: a.md\n---\n'}
print(s.resolve_authoritative(tree))
"
{'authoritative': ['b.md'], 'superseded': {'a.md': 'b.md'}, 'broken': [], 'conflicts': {}}
```
derived: the command above, run this session against the PR's supersession module at head `16c89903`.

Also re-derived the conflict/fail-closed case the PR's own record cites:
```
$ python3 -c "import sys; sys.path.insert(0,'/tmp/pr-3086-review'); import supersession as s; print(s.resolve_authoritative({'a.md': '---\nrole: x\n---\n', 'b.md': '---\nrole: y\nsupersedes: a.md\n---\n', 'c.md': '---\nrole: z\nsupersedes: a.md\n---\n'}))"
{'authoritative': [], 'superseded': {}, 'broken': [], 'conflicts': {'a.md': ['b.md', 'c.md']}}
```
derived: the command above, this session.

`resolve_authoritative()`'s only parameter is a plain `records: dict[str, str]` -- inspected the function body directly at PR head `16c89903` and confirmed no git/network/filesystem call exists inside it; content strings are the entire input, satisfying "from file contents alone" literally, not just by the PR's own claim.
rationale: the check passes and the property was reproduced independently rather than trusting the shipped probe's own self-report; the one real defect a background warrant-hunt found here (a path-normalization bypass, commit `f516fcc6`) was already fixed and re-verified against the post-fix head before finalizing this verdict.
spec_vs_built: n/a (Present)

### Requirement 3 — failed-no-commit reconciled against the remote

requirement: "The failed-no-commit classification is reconciled against the remote before it is reported... empty state: a session that genuinely pushed nothing still reports failed-no-commit, unchanged."
spec_ref: issue #3050 Acceptance bullet 3 (the reconciliation's own pinned test file, untracked in this repo -- PR #3086 branch only)
verdict: Surface
evidence:
```
$ cd /tmp/pr-3086-review && python3 -m pytest tests/test_failed_no_commit_reconcile.py -q
.................
17 passed in 0.95s
```
derived: the command above, run against PR #3086 head `16c89903`.

All 17 cases hand-feed `push_succeeded` as a literal bool into the
classification functions (inspected the pinned test file line by line at
PR head `16c89903`) -- none calls the PR's own remote-push helper or
exercises its real return-status mapping to `push_succeeded`:
```
push_succeeded = push_result is not None and push_result["status"] not in (
    "push-rejected", "pr-create-failed")
```
canonical: `spawn.py:5026` at PR #3086 head `16c89903`, read directly (unchanged by this PR's diff).

Built the missing case: a real bare git remote and workspace (scratch,
discarded after use) where the session's own role branch was deleted
locally after being created and pushed once -- simulating a session that
made zero commits, pushed nothing, with a clean tree, whose expected
branch does not exist locally at classification time. Called the PR's
actual (unmocked) functions directly:
```
$ python3 /tmp/probe_pnr.py
push_result: {'status': 'nothing-to-push', 'reason': None}
push_succeeded: True
fail_closed_downgrade -> progressed
```
derived: a scratch script (discarded after use), calling the PR's own
`ensure_pushed()` then `fail_closed_downgrade()` against head `16c89903`,
re-run and reconfirmed identical after the PR's mid-session commits
landed:
```
$ git diff pr-3086-review..pr-3086-review-2 --stat
(shows only supersession.py, its test file, and the hunt-record doc changed -- board.py/spawn.py absent)
```
derived: the command above, this session.

The remote-push helper's `"nothing-to-push"` status comes from a local
`git rev-parse --verify -q <branch>` failing (`relay.py:221-222` at head
`16c89903`) -- a local ref-existence check, no `git push`/`fetch` against
`origin` runs for that status. This is the literal counter-example the
criterion's own empty-state names ("a session that genuinely pushed
nothing"), reproduced through the PR's real, unmodified code, not a
synthetic mock.

Reachability caveat, stated plainly: under the harness's ordinary flow,
the branch-checkout helper runs `git checkout -B <branch> ...` at spawn
start (before the session runs; `pipeline.py:1062` at head `16c89903`),
which should make the branch exist locally for the session's whole
lifetime absent the session's own later branch deletion/rename -- so
this is not the everyday case the issue's own story documents, but it is
a real, executable gap in the property as literally worded, and none of
the 17 pinned cases would catch it (none touches the real status-value
boundary).
rationale: the pinned check passes and the primary/documented story case
(session committed+pushed, local diff missed it) is genuinely fixed,
re-derived independently as:
```
$ python3 -c "import sys; sys.path.insert(0,'/tmp/pr-3086-review'); import board; print(board.fail_closed_downgrade('progressed', 1, [], False, [], False, True))"
progressed
```
(the story case, `push_succeeded=True` from a genuine push -- correctly
stays `progressed`, not downgraded). But the criterion's empty-state is a
universal claim, and a real, reachable-through-the-PR's-own-code
counter-example exists that the pinned suite structurally cannot catch,
since it never touches the `push_succeeded`-derivation boundary.
spec_vs_built: n/a (Surface, not Incorrect -- the primary case is fixed correctly; the gap is one specific unexercised status value)

### must-not A — board-gate's ownership rule not relaxed

requirement: "do not fix A by relaxing board-gate's ownership rule for arbitrary writes"
spec_ref: issue #3050 must-not clause 1
verdict: Present
evidence:
```
$ git diff main...pr-3086-review-2 -- runs/
(no output -- zero hits; board-gate.sh byte-identical to main)
```
derived: the command above, this session, comparing `main` (`573e7382`) against PR #3086 head `16c89903`.

Constructed an unrelated cross-session write and ran it through the
live-installed board-gate hook directly:
```
$ bash /tmp/bg_probe.sh
rc=2
board-gate: docs/issue-9999/reports/skill-a.md is authored by 'skill-a', not 'skill-b'. A session may append new content to a foreign-authored record but never alter another author's existing lines. (contract v3 s11, issue-2241 stage 3)
```
derived: a scratch script (discarded after use) -- a fresh repo on
branch `issue-9999/skill-b`, `CLAUDE_SKILL=skill-b`, attempting a write
to a foreign, unrelated record (untracked scratch path, never committed
anywhere, authored by a different, unrelated skill and carrying no
supersedes field) -> refused, exit 2.

Corroborated by a live, independently-run case in a different repo:
canonical: `gh pr view 15 --repo JiwonJung94/study-companion` (state:
MERGED) and its diff -- a correction-round session explicitly instructed
to record any board-gate refusal verbatim rather than work around it, on
an unrelated issue/repo, hit (quoted verbatim from that PR's own merged
record, external repo, untracked here):
```
PreToolUse:Bash hook error: [.../pretooluse-dispatcher.sh]: board-gate: docs/issue-10/reports/implementation-blueprint+experiment-trust+test-derivation+silent-failure-audit-41fa76ac.md belongs to another skill. research-evidence-discipline+silent-failure-audit-3b9228ee writes only research-evidence-discipline+silent-failure-audit-3b9228ee.md, research-evidence-discipline+silent-failure-audit-3b9228ee/** -- never a foreign record. (contract v3 s11)
```
-- the identical R5 refusal shape, confirming the boundary held in a
real production run independent of this review.
rationale: the enforcing file is byte-identical to main, and the rule
fires correctly against both a hand-built adversarial input and a real,
separately-observed live case.
spec_vs_built: n/a (Present)

### must-not B — classifier must not trust the session's own success claim

requirement: "Do not fix B by making the classifier trust the session's own success claim; #2667 is the case where that claim was false and the work was lost."
spec_ref: issue #3050 must-not clause 2
verdict: Surface
evidence: for the documented story case and every case the 17 pinned
tests enumerate (cited under Requirement 3 above), `push_succeeded` is
genuinely the remote-push helper's observed outcome of a real
`git rev-list`/`push` against `origin/<branch>` (`relay.py:194-282` at
head `16c89903`, read directly) -- not a self-report, and the same class
of signal other reconciliation helpers in `board.py` already use, as the
PR's own record argues.

However, see Requirement 3's `derived:`-cited repro above: the
"nothing-to-push" status feeding `push_succeeded=True` is a purely local
ref-existence check with no network round-trip -- in that one branch,
`push_succeeded=True` does not mean "remote confirmed nothing needed
pushing," it means "this local ref doesn't exist," which a session that
deleted or never created its own role branch can produce while having
genuinely pushed nothing.
rationale: not the #2667 failure mode reborn (the classifier never reads
anything the session itself asserts) -- a narrower, adjacent gap: one
pre-existing (unmodified by this PR) local-only status value is treated
as equivalent to a remote-confirmed one, in the exact branch this PR
newly wires into the failed-no-commit decision.
spec_vs_built: n/a (Surface, not Incorrect)

## Test-depth audit (test-depth-audit skill)

Both new pinned suites, read line-by-line at PR head `16c89903`, are
Genuine Assertion throughout -- every case asserts a specific expected
dict/string/bool against the function's actual return, not mere
execution-without-exception.
```
$ cd /tmp/pr-3086-review && python3 -m pytest tests/test_supersession_shape.py tests/test_failed_no_commit_reconcile.py -q
.............................
29 passed in 0.91s
```
derived: the command above, this session, against head `16c89903`.

Both are Mock-Dominated at the integration boundary: the reconciliation
suite never calls the PR's own remote-push helper or exercises the real
status-to-`push_succeeded` mapping -- this is the concrete boundary
where Requirement 3's finding above lives, and is why re-running the
pytest pass alone would have missed it.

canonical: a recursive grep for the reconciliation-disagreement helper
and its log-marker string across both the PR's `tests/` and `test/`
directories (this session, against head `16c89903`) matched only the
one unit-level pin plus one pre-existing, unrelated file that pre-dates
this PR -- no test anywhere exercises the new disagreement-logging print
statement this PR adds to the spawn path.

## experiment-trust skill applicability

Judged not-applicable: PR #3086 contains no A/B or variant-comparison
experiment result (no SRM, no platform A/A, no pre-registration question
anywhere in its diff).
```
$ git diff main...pr-3086-review-2 --stat
 board.py                                           |  ...
 spawn.py                                           |  ...
 supersession.py                                    |  ...
 gates/probe_supersession_marker.py                 |  ...
 docs/issue-3050/reports/.../hunt-supersession-and-fail-closed-downgrade.md | ...
 docs/specs/acceptance-commands.md                  |  ...
 docs/specs/enforcement-boundary.md                 |  ...
 tests/test_failed_no_commit_reconcile.py           |  ...
 tests/test_supersession_shape.py                   |  ...
```
derived: the command above, this session, comparing `main` (`573e7382`) against PR #3086 head `16c89903` -- no experiment/metrics file anywhere in the changed set. Loaded and checked the `experiment-trust` skill before ruling it out, per the skill-obligation.

## Full suite comparison (main vs PR head)

```
$ cd /tmp/main-baseline && python3 -m pytest tests/ -q
5 failed, 182 passed in 10.37s

$ cd /tmp/pr-3086-review && python3 -m pytest tests/ -q
5 failed, 211 passed in 9.44s

$ diff <(cd /tmp/pr-3086-review && python3 -m pytest tests/ -q 2>/dev/null | grep FAILED | sort) \
       <(cd /tmp/main-baseline  && python3 -m pytest tests/ -q 2>/dev/null | grep FAILED | sort)
IDENTICAL FAILURE SET
```
derived: the three commands above, this session, comparing `main`
(`573e7382`) against PR #3086 head `16c89903`. 211 minus 182 equals 29,
matching the two new pinned files' own combined count shown in the
"Test-depth audit" section above (12 + 17 = 29) -- PR #3086 changes zero
pre-existing pass/fail outcomes on `tests/`; it adds exactly the 29 new
tests it ships, on top of the same 5 pre-existing failures (identical
failing-test-name set, shown above). The task's stated baseline ("5
failed / 105 passed") does not match either number measured here on
`tests/` in this environment; the agreement between these two
same-environment, same-command runs on the failing-test-name set --not
the absolute passed-count-- is what answers "does this PR change the
count": it does not, beyond additively.

## Why

Every finding above cites a `derived:`/`canonical:` command run this
session against the PR's real code, not a claim taken from the PR's own
record or test-plan checklist
(`defect-verification-independence-from-upstream-verdicts`): including a
negative/edge case rather than only the happy path is why the
Requirement-3/must-not-B repro exists at all -- every pinned test in the
suite is a happy-path-adjacent decision-table row over hand-fed
booleans, so the missing case had to be built from scratch against the
real remote-push helper. Re-checking a plausible false positive once
before finalizing is why every repro above was re-run against both PR
heads (`548930a3` then `16c89903`) after the mid-session warrant-hunt
commits landed, confirmed unaffected since they touch only the
supersession module.

`test-depth-audit` was applied specifically to the two new pinned test
files because their pytest-pass status is the literal `check:` command
for two of the three acceptance criteria -- auditing whether a passing
suite verifies the property in question, versus a narrower mocked slice
of it, is what surfaced the Requirement-3 gap; reading only the exit
code would have missed it.

## What did not work

None -- every probe constructed for this review executed to completion and produced a determinate result (no probe was abandoned or left inconclusive).

## Upstream basis

- PR tokenmaxxxer/on-the-record#3086, heads `548930a338cd2828cf53f33a02c80af6509a0f51` then `16c899031b38f099b52ce05b0cfacc6492c07d6c` -- untracked in this repo's branch history; fetched read-only, checked out in a separate worktree, never pushed to or edited.
- `main` at `573e7382` -- checked out read-only in a separate worktree for the full-suite comparison.
- `gh issue view 3050` (issue body + acceptance-amendment comments) -- same-commit, read this session.
- `JiwonJung94/study-companion` PR #15 -- external repo, untracked in this repo; read via `gh pr view`/`gh pr diff` against that repo, cited for the must-not-A live comparison the task requested.

## Open findings

1. Requirement 1's documentation-location gap: the supersedes-frontmatter
   convention is undocumented in the record-shape directive or any
   CLAUDE.md. canonical: the two grep commands under Requirement 1 above
   (this session, against PR #3086 head `16c89903`). Resolution path: a
   follow-up commit on PR #3086 adding a short mention of the convention
   to the record-shape directive's own canonical source (PR #3086
   branch territory, untracked in this repo), so a spawned correcting
   session discovers it without already knowing to read the new
   module's source.
2. Requirement 3 / must-not B's "nothing-to-push" gap. canonical: the
   scratch repro under Requirement 3 above (this session, against head
   `16c89903`). Resolution path: either narrow the remote-push
   helper's status-to-`push_succeeded` mapping to exclude that one
   status value, or have the helper perform a real remote check before
   returning it. Not blocking under today's harness ordering (the role
   branch is force-checked-out at spawn start), but the pinned suite
   gives zero regression protection if that ordering ever changes.
3. acceptance: `bash -c "cd /tmp/pr-3086-review && python3 -m pytest tests/test_supersession_shape.py -q && python3 gates/probe_supersession_marker.py && python3 -m pytest tests/test_failed_no_commit_reconcile.py -q"` — result: all three exit 0 (see the three `derived:`-tagged code blocks under Requirements 1-3 above); neither open finding above changes that.

## Next steps

canonical: this record's own frontmatter (`loop_state: landed`, set in
this same commit) -- no further action queued from this session.
Whoever owns PR #3086 next reads the two Open findings and the
per-requirement blocks above to decide whether either Surface downgrade
blocks merge.

skill-verdict: test-depth-audit — applied: invoked; audited the two new pinned test suites for genuine-assertion depth vs. mock-dominated integration gaps (see "Test-depth audit" section above), which is what surfaced the Requirement-3 finding.
skill-verdict: experiment-trust — not-applicable: PR #3086 contains no A/B or variant-comparison experiment result.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; canonical: the per-requirement blocks above, each naming its failing clause and citing a re-check against both PR heads before finalizing -- used to choose Surface over Present for two of the three own-criteria requirements and one must-not clause.
skill-verdict: work-in-english — applied: invoked; this record and all commands/output are in English; only the final end-of-turn chat summary to the user is in Korean.
skill-verdict: implementation-audit — applied: invoked; treated the issue's three acceptance bullets and two must-not clauses as the falsifiable-claims list and PR #3086's diff as the implementation to classify against, independent of the PR's own record's framing.
skill-verdict: adversarial-review — applied: invoked; canonical: the per-requirement evidence blocks above, each derived by this session's own execution before the PR's own record was consulted for framing -- graded PR #3086 as a structurally independent evaluator incentivized to find real gaps rather than confirm the PR's test-plan claims.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every verdict above is re-derived by executing real code against self-constructed inputs rather than citing the PR's pytest-pass or record claims as settled (see "Why" above).
skill-verdict: conformance-review-finding-record — applied: invoked; per-requirement blocks above (requirement/spec_ref/verdict/evidence/rationale/spec_vs_built) follow this skill's field list, written into this session's own designated record path per the write-set boundary (board-gate R5) rather than a separately-named conformance-review.md, since this session's role does not own that filename.
other mounted skills (merge-gates): not triggered — this review evaluates whether an already-open PR's fix satisfies its issue, not how concurrent branches should merge to main.
