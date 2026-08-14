# Conformance review — issue-326 stranded push/PR relay

## Upstream / basis

Requirement list: issue #326's own `## Acceptance` section (bullets 1-4,
reproduced below) plus the approved phase-1 proposal
`docs/issue-326/proposals/ensure-pushed-stranded-comment.md`. Reviewed
artifact: PR #348 into `main`.

canonical: `gh pr view 348 --json files,mergedAt,mergeCommit` (run this
turn) — mergedAt `2026-08-07T08:53:21Z`, mergeCommit `327f647d`, files
`spawn.py`, `test_spawn.py`,
`docs/issue-326/proposals/ensure-pushed-stranded-comment.md`,
`docs/issue-326/reports/implementation.md`,
`docs/issue-326/reports/implementation/survey.md`.

`docs/issue-326/reports/implementation.md` records four post-merge
rebase rounds of the implementation branch against `origin/main`; this
review reads the current state of `spawn.py`/`test_spawn.py` on this
branch (`issue-326/conformance-review`, based on current `main`) directly
rather than the PR diff in isolation, so any rebase drift is caught.

## What was done

Artifact-only re-read of `_post_stranded_push_comment` (`spawn.py:3404-3427`)
and its two call sites inside `ensure_pushed()` (`spawn.py:6127-6128`
push-failure branch, `spawn.py:6156-6157` pr-create-failure branch)
against the issue's four acceptance bullets and the approved proposal's
"What will be built"/"How you'll know it worked" sections. Ran the
acceptance test class directly as evidence:

canonical: `python3 -m pytest tests/test_spawn.py -k "stranded or PostCrashComment" -v` (run this turn, full output below)

```
$ python3 -m pytest tests/test_spawn.py -k "stranded or PostCrashComment" -v
tests/test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_posts_comment_on_pr_create_failure PASSED
tests/test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_posts_comment_on_push_failure PASSED
tests/test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_stranded_comment_is_idempotent PASSED
tests/test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_stranded_comment_posts_when_comments_unreadable PASSED
tests/test_spawn.py::PostCrashComment::test_post_failure_is_logged_not_silent PASSED
tests/test_spawn.py::PostCrashComment::test_posts_when_marker_absent PASSED
tests/test_spawn.py::PostCrashComment::test_skips_when_marker_already_present PASSED

7 passed
```

One verdict rendered per acceptance bullet below.

## Verdicts

**A1 — A session whose `git push` fails posts one idempotent comment on
its issue, and a repeated attempt against the same stranded state does
not double-comment: Present.** `ensure_pushed()`'s push branch
(`spawn.py:6123-6129`) calls `_post_stranded_push_comment(..., "push-failed",
r.stderr.strip())` immediately after a non-zero `git push` return code,
before returning `{"status": "push-rejected", ...}`.
`_post_stranded_push_comment` (`spawn.py:3407-3427`) reads
`_issue_comments(root, issue)` and skips posting if a comment already
contains the exact marker `[on-the-record] stranded-relay: {branch}:push-failed`.
Shown by `test_ensure_pushed_posts_comment_on_push_failure` (one comment
call on first failure) and `test_ensure_pushed_stranded_comment_is_idempotent`
(zero comment calls across two `ensure_pushed()` calls when the marker is
already present) in the run above.

**A2 — A session whose `gh pr create` fails does the same: Present.**
`ensure_pushed()`'s PR-create branch (`spawn.py:6145-6158`) calls
`_post_stranded_push_comment(..., "pr-create-failed", c.stderr.strip())`
on a non-zero `gh pr create` return code, using the same idempotent
marker mechanism with `reason="pr-create-failed"` (a distinct key from
A1's `push-failed`, so the two failure modes on the same branch each get
their own marker and both can surface independently, per the proposal's
step 1). Shown by `test_ensure_pushed_posts_comment_on_pr_create_failure`
in the run above.

**A3 — The comment names what was stranded and where the commits are, so
the work is recoverable rather than merely reported lost: Present.** The
comment body built in `_post_stranded_push_comment` (`spawn.py:3421-3425`)
includes `branch: {branch}`, `reason: {reason}`, `detail: {detail[:200]}`
(the captured stderr), and an explicit sentence naming the role and
asking to resume ("retry the push/PR creation from the host") or close
with a stated reason. Both `test_ensure_pushed_posts_comment_on_push_failure`
and `test_ensure_pushed_posts_comment_on_pr_create_failure` assert the
branch name and reason string appear in the posted body
(`self.assertIn(br, body)`, `self.assertIn("push-failed"/"pr-create-failed",
body)`) in the run above.

**A4 — Interrupted work reaches the operator as a question — resume or
close — rather than as silence: Present, as the issue's own named
mechanical stand-in.** The issue's Acceptance section itself marks the
conversational half of this bullet `unverifiable` ("whether the operator
is actually asked is a property of the orchestrator's conversational
turn... the mechanical stand-in is the durable issue comment above").
The comment body's closing sentence is phrased as exactly that stand-in:
"resume it (retry the push/PR creation from the host), or close the issue
with a stated reason. Needs human intervention." — a durable, on-issue
question, not a log line. No code path in `ensure_pushed()` or
`_post_stranded_push_comment` auto-resumes or auto-closes the issue,
matching the proposal's "Out of scope" section (automated resume/close
explicitly excluded).

## Additional coverage beyond the approved proposal

The proposal's step 3 named three tests; the current tree carries a
fourth, `test_ensure_pushed_stranded_comment_posts_when_comments_unreadable`
(`tests/test_spawn.py`, lines 5993-6026), added per the issue #432
tuple-shape regression mirror — when `_issue_comments()` returns
`ok=False`, `_post_stranded_push_comment` posts anyway rather than
silently skipping under an unconfirmed marker-present read. This is
additive robustness, not a divergence from any acceptance bullet or
proposal step: it leaves A1's idempotency guarantee scoped to the
verified-readable case, which `test_ensure_pushed_stranded_comment_is_idempotent`
still covers in the run above, and it matches `_post_crash_comment`'s
existing fail-open-to-posting behavior on a read failure.

## Rebase history reviewed

`docs/issue-326/reports/implementation.md` narrates four post-merge
rebase rounds of the implementation branch onto advancing `origin/main`,
each re-running the `stranded`-keyed test selection. No conflict-resolution
note in that record touches `_post_stranded_push_comment` or its call
sites' own logic — the two real conflicts it describes (an
insertion-point collision with #325's `_post_stall_comment`;
`ensure_pushed()`'s bare-`return` vs. structured-dict collision with
#301 B2) both resolve by keeping both independent changes side by side,
not by altering this issue's own logic.

canonical: `spawn.py:3404-3427,6092-6159` read directly this turn.

Re-reading the current `spawn.py` state directly (rather than trusting
the implementation record alone) shows both call sites still fire before
their respective `return` statements, and the marker format is unchanged
from the proposal's step 1.

## Why

Per-requirement fidelity verdicts, artifact-only, per the
conformance-review role's rulebook (never a holistic quality read, never
a fix).

## What did not work

None.

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

None. All four acceptance bullets (A1-A4) verify Present against the
current `spawn.py`/`test_spawn.py` state, with the fourth bullet's
conversational half satisfied via the issue's own named mechanical
stand-in (the durable comment), consistent with how the issue itself
scoped that bullet as unverifiable beyond that stand-in.

## Next steps

None — no findings to route. The proposal's explicitly out-of-scope item
(a process dying before `ensure_pushed()` is ever invoked, so no code
path exists to post anything) stays open and undelivered, as named in
the proposal itself; it is not part of issue #326's acceptance and is
not a conformance gap of this delivered scope.
