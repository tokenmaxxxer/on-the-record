---
issue: 3050
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
loop_state: done
upstream:
  - path: docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md
    sha: 16c899031b38f099b52ce05b0cfacc6492c07d6c
  - path: supersession.py
    sha: 16c899031b38f099b52ce05b0cfacc6492c07d6c
  - path: board.py
    sha: 16c899031b38f099b52ce05b0cfacc6492c07d6c
  - path: spawn.py
    sha: 16c899031b38f099b52ce05b0cfacc6492c07d6c
---

# issue-3050 — independent-verification-1 record

## What was done

Independent verification of PR #3086 (branch `issue-3050/implementation-
blueprint+silent-failure-audit+test-derivation-150a8ac4`, head
`16c899031b38f099b52ce05b0cfacc6492c07d6c`), the deliverable for issue
#3050. Verified by fetching the PR branch into a separate git worktree
(not this session's own tree) and executing the PR's real code against
self-constructed inputs, not by citing the PR's own test-plan prose. The
two new test files and the new gate probe the PR adds are untracked on
this session's own branch (new, unmerged files that exist only on PR
#3086's branch); all commands below that touch them ran inside the
`/tmp/pr3086-review` worktree, not this branch's own tree.

canonical: `gh pr view 3086 --json number,title,body,headRefName,baseRefName,commits,files,url,state` — result:
```
state: OPEN, mergedAt: null (via gh pr list --search 3050)
head: 16c899031b38f099b52ce05b0cfacc6492c07d6c
commits: 5
files changed: 10
```

derived, worktree setup: `bash -c "git fetch origin pull/3086/head:pr-3086-review && git worktree add /tmp/pr3086-review pr-3086-review"` — result: worktree created at `/tmp/pr3086-review`, HEAD `16c899031b38f099b52ce05b0cfacc6492c07d6c`. All checks below ran inside that worktree, never against this session's own branch.

**Acceptance check 1** (untracked on this branch — new file added by PR #3086, run in `/tmp/pr3086-review`):
```
$ python3 -m pytest tests/test_supersession_shape.py -q
............                                                             [100%]
12 passed in 0.79s
```

**Acceptance check 2** (untracked on this branch — new file added by PR #3086, run in `/tmp/pr3086-review`):
```
$ python3 gates/probe_supersession_marker.py
-- shape decision --
  Two artifacts, not one: the correcting session can only ever write its
  own record, never the one it corrects. 'Exactly one artifact survives'
  was rejected on that ground alone, before any content design question.
ok
```
exit 0.

**Acceptance check 3** (untracked on this branch — new file added by PR #3086, run in `/tmp/pr3086-review`):
```
$ python3 -m pytest tests/test_failed_no_commit_reconcile.py -q
.................                                                        [100%]
17 passed in 0.82s
```

All three literal `check:` commands from the issue's acceptance section
pass on PR #3086's head. The graded findings below go past the literal
checks into the two must-not clauses and the "documented where a spawned
session will read it" half of Requirement 1, which the literal checks
don't test.

### Requirement 1 (sanctioned supersession shape) — Present, with a documentation gap

canonical: `16c899031b38f099b52ce05b0cfacc6492c07d6c:supersession.py` (read in full, 147 lines, in `/tmp/pr3086-review`) — `render_supersedes_field()` / `parse_supersedes()` / `resolve_authoritative()` implement the shape the issue asks for: a correcting session writes only its own record (board-gate's write-set isolation denies every write shape into a peer session's record) and marks a `supersedes: <path>  # <reason>` frontmatter line; `resolve_authoritative()` reads only record content (no git, no PR body, no issue comment) and fails closed on a dangling target (`broken`) and on two records both claiming to supersede the same original (`conflicts`) — the "second correction, third copy" shape named in issue comment `issuecomment-5503338925`.

derived (see acceptance check 2 above): the probe builds a synthetic
two-artifact tree and asserts merged-tree-only resolution, `ok`, exit 0.
PR body claims it also fails against `main` (module absent there); this
specific re-run against `main` was not independently repeated in this
session.

Second half of Requirement 1 — "it is documented where a spawned session
will read it" — is not satisfied:

derived:
```
$ cd /tmp/pr3086-review && grep -in supersed docs/handbooks/record-contract.md docs/handbooks/record-authoring.md; echo EXIT:$?
EXIT:1
```
No match in either handbook — the two files that already document every
other record frontmatter field a spawned session populates:
```
$ grep -n "^## " docs/handbooks/record-contract.md
## Issue-scoped lease
## Author identity
## Record-kind
## What stays additive
```

derived:
```
$ cd /tmp/pr3086-review && grep -rl 'supersession\|resolve_authoritative\|render_supersedes_field\|parse_supersedes' --include='*.py' . | wc -l
7
```
Reading each of the 7 matches confirms only the new module and its own
dedicated test/probe files reference the `supersedes:` convention by
name; the rest are pre-existing, unrelated uses of the generic English
word "supersession" in this codebase's attempt-halt logic (`roster.py`'s
halt-clearing comments, two pre-existing `test/test_spawn_attempt_*.py`
files) that predate this PR and have nothing to do with record artifacts.
No spawn-time prompt, directive, or record-authoring code path references
the new `supersedes:` field.

derived:
```
$ cd /tmp/pr3086-review && grep -c supersed docs/specs/acceptance-commands.md docs/specs/enforcement-boundary.md
docs/specs/acceptance-commands.md:1
docs/specs/enforcement-boundary.md:1
```
Both matches are `gates/ci.py`-registration table rows (which script maps
to which `check:` command), not authoring guidance aimed at a correcting
session.

A spawned correcting session would discover the `supersedes:` convention
only by independently finding the new module's own docstring — this is a
Surface finding against Requirement 1's second clause, not a Present.

canonical: `gh pr view 3100 --json body` — result: PR #3100 (branch `issue-3050/test-depth-audit+experiment-trust+conformance-review-verdict-assignment-8783c5f3`, `Advances #3050`, independent builder-blind verification of the same PR #3086, filed concurrently on a different branch) reaches the same conclusion independently: "Surface — sanctioned-shape documentation location (Requirement 1: the `supersedes:` convention is undocumented anywhere a spawned session actually reads)" — corroborating this session's own finding above, which was reached via this session's own greps before reading PR #3100's body.

### Must-not A (do not relax board-gate's ownership rule) — Present

derived:
```
$ cd /tmp/pr3086-review && git fetch origin main && git diff origin/main...HEAD --stat
 board.py                                           |  29 +++
 docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md | 281 +++++++++++++++++++++
 docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4/2026-09-02-hunt-supersession-and-fail-closed-downgrade.md | 66 +++++
 docs/specs/acceptance-commands.md                  |   4 +
 docs/specs/enforcement-boundary.md                 |   1 +
 gates/probe_supersession_marker.py                 | 126 +++++++++
 spawn.py                                           |  17 ++
 supersession.py                                    | 147 +++++++++++
 tests/test_failed_no_commit_reconcile.py           | 148 +++++++++++
 tests/test_supersession_shape.py                   | 142 +++++++++++
 10 files changed, 961 insertions(+)
```

The board-gate hook that enforces write-set isolation is a harness-side
enforcement point, not a file tracked in this repo's own git history:

derived:
```
$ cd /tmp/pr3086-review && git ls-files | grep -i board-gate
docs/issue-1245/proposals/2026-08-13-monitor-attachment-board-gate.md
docs/issue-1827/proposals/board-gate-citation-gate-carrier-aware.md
docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
docs/issue-2286/reports/implementation/board-gate-r5-migration.md
docs/issue-651/proposals/2026-08-10-board-gate-resolved-write-targets.md
```
Only unrelated proposal/report docs — no hook script tracked in this
repo. That hook does not appear anywhere in the PR's changed-files list
above — the fix does not touch the ownership boundary at all, consistent
with the new module's own docstring stance that it "does not try to
relax that boundary."

### Requirement 3 / must-not B — Incorrect (confirmed, reproduced independently)

canonical: `16c899031b38f099b52ce05b0cfacc6492c07d6c:spawn.py` line 5026 (read in `/tmp/pr3086-review`) — the `push_succeeded` derivation:
```python
push_succeeded = push_result is not None and push_result["status"] not in (
    "push-rejected", "pr-create-failed")
```

canonical: `16c899031b38f099b52ce05b0cfacc6492c07d6c:relay.py` line 221 (read in `/tmp/pr3086-review`) — `ensure_pushed()`'s early return:
```python
if git("rev-parse", "--verify", "-q", br).returncode != 0:
    return {"status": "nothing-to-push", "reason": None}
```
This fires when the session's role branch does not exist locally at all
— the genuine "committed and pushed literally nothing" case.
`"nothing-to-push"` is not in `spawn.py`'s excluded-status set above, so
`push_succeeded` comes out `True` for that case — the opposite of what
the name promises.

derived, reproduced directly against the PR's own `board.py`, not a
rewritten or mocked copy:
```
$ cd /tmp/pr3086-review && python3 -c "
import board
push_result = {'status': 'nothing-to-push', 'reason': None}
push_succeeded = push_result is not None and push_result['status'] not in ('push-rejected', 'pr-create-failed')
print('push_succeeded:', push_succeeded)
print(board.fail_closed_downgrade('progressed', 1, [], False, [], False, push_succeeded))
"
push_succeeded: True
progressed
```
Expected `failed-no-commit` — both signals (no local commit, no remote
push) should agree on failure. Reproduced against the PR's own pinned
test for exactly this scenario, untracked on this branch, read in
`/tmp/pr3086-review`:
```
$ sed -n '59,64p' tests/test_failed_no_commit_reconcile.py
    def test_genuine_failure_no_commit_no_push_stays_failed(self):
        # Both signals agree on failure -- the fix must not paper over a
        # real failed-no-commit.
        self.assertEqual(
            board.fail_closed_downgrade("progressed", 1, [], False, [], False, False),
            "failed-no-commit")
```
derived:
```
$ cd /tmp/pr3086-review && grep -c 'push_succeeded=' tests/test_failed_no_commit_reconcile.py
0
```
Every call in that file passes `push_succeeded` positionally as a
hand-typed `True`/`False` literal argument to
`board.fail_closed_downgrade()` (confirmed by reading the file in full),
never derived from a simulated `ensure_pushed()` return value. So the gap
between the `board.py`-level fix and its actual `spawn.py` wiring is
untested by all 17 passing cases in acceptance check 3 above.

canonical: `gh pr view 3086 --json body` — result: the PR's own body
states must-not B as "do not... make the classifier trust the session's
own success claim; #2667 is the case where that claim was false and the
work was lost." In the reproduced case above, a session that made zero
commits and pushed nothing keeps whatever `outcome` it self-reported
(`"progressed"` in the repro) instead of being downgraded to
`failed-no-commit` — must-not B's exact forbidden shape.

canonical: `gh pr view 3100 --json body` — result: PR #3100 reports
reproducing the same defect via a live `ensure_pushed()` call against a
constructed genuinely-pushed-nothing session, rather than the class-level
repro used here; both routes land on the same root cause — the `status
not in (...)` exclusion tuple in `spawn.py`'s `push_succeeded` derivation
is missing `"nothing-to-push"`.

### Full suite comparison

derived:
```
$ cd /tmp/pr3086-review && python3 -m pytest tests/test_supersession_shape.py tests/test_failed_no_commit_reconcile.py -q
29 passed
```
(untracked on this branch — both new files added by PR #3086; 29 = 12 +
17, matching acceptance checks 1 and 3 above.)

canonical: `gh pr view 3086 --json body` — result: PR body claims a full
`tests/` run shows "5 pre-existing failures, verified identical against a
stashed clean-main baseline"; this session did not independently re-run
the full test suites end-to-end to confirm that count (not re-verified
here — the two acceptance-check test files above were run in full and
independently confirmed instead).

## Why

Executing the real code (worktree checkout, direct `board.py` / `relay.py`
calls, the actual probe script) rather than re-reading the PR's own
test-plan prose is what surfaced the `push_succeeded` derivation gap
documented in Requirement 3 / must-not B above.

derived:
```
$ cd /tmp/pr3086-review && grep -c 'push_succeeded' tests/test_failed_no_commit_reconcile.py
9
```
(untracked on this branch) — every one of those 9 occurrences is a
hand-typed boolean literal passed straight into
`board.fail_closed_downgrade()`; none exercise `spawn.py`'s own
derivation of that boolean from `ensure_pushed()`'s real status strings,
which is exactly the path this session's own `python3 -c "..."` repro
(Requirement 3 section above) exercised instead and where the defect
actually lives. A citation-only review of the diff would have read the
`push_succeeded` derivation line and `relay.py`'s status vocabulary
separately and plausibly missed that `"nothing-to-push"` falls on the
wrong side of the exclusion tuple.

## What did not work

None — no write path was attempted against PR #3086's own branch or
record; board-gate's ownership boundary was not tested against, since
that is what must-not A itself forbids relaxing and this session had no
reason to attempt it.

## Upstream basis

`16c899031b38f099b52ce05b0cfacc6492c07d6c:docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md`
and the code changes in the same commit range
(`16c899031b38f099b52ce05b0cfacc6492c07d6c:supersession.py`,
`16c899031b38f099b52ce05b0cfacc6492c07d6c:board.py`,
`16c899031b38f099b52ce05b0cfacc6492c07d6c:spawn.py`,
`16c899031b38f099b52ce05b0cfacc6492c07d6c:relay.py`) — all read and
executed at PR #3086 head `16c899031b38f099b52ce05b0cfacc6492c07d6c`, in
a separate worktree, not this session's own tree.

## Open findings

canonical: `gh issue view 3050 --json state` — result: issue state OPEN,
so a correction round remains possible against the two findings below.

- **Requirement 1 documentation gap (Surface, evidence above).** The
  `supersedes:` convention should be added to
  `16c899031b38f099b52ce05b0cfacc6492c07d6c:docs/handbooks/record-contract.md`
  (which already documents every other record frontmatter field) so a
  spawned correcting session can discover it without independently
  finding the module's own docstring. Resolution path: a follow-up
  commit on PR #3086, or a new session against issue #3050.
- **`push_succeeded` misclassification (Incorrect, evidence above).** Add
  `"nothing-to-push"` to the excluded-status set in
  `16c899031b38f099b52ce05b0cfacc6492c07d6c:spawn.py` line 5026's
  `push_succeeded` derivation, or invert it to an explicit allow-list of
  statuses that confirm the remote actually holds this session's work,
  rather than a deny-list that silently admits any future `relay.py`
  status string by default. Add a test exercising `spawn.py`'s actual
  derivation against `ensure_pushed()`'s real return shape, not only
  `board.fail_closed_downgrade()` with a hand-supplied boolean.
  Resolution path: a correction round on issue #3050 — which, per this
  same issue's part A, cannot write into PR #3086's own record and would
  need the supersession shape this PR itself introduces (once the
  documentation gap above is closed) to land the correction visibly.
- Both findings corroborated independently by PR #3100 (`gh pr view 3100
  --json body`, concurrent builder-blind verification of the same PR),
  reached via different reproduction routes landing on the same root
  causes.

## Next steps

derived: acceptance checks 1-3 above (all executed and passing on PR
#3086 head `16c899031b38f099b52ce05b0cfacc6492c07d6c`) plus the must-not
A / must-not B checks above (A holds, B does not) together complete this
record's own verification scope. `loop_state: done`. No further action is
owed by this record; the two Open findings above belong to a future
correction round on issue #3050, not to this verification pass.
