---
issue: 2894
role: silent-failure-audit-dd4cce49
author: silent-failure-audit-dd4cce49
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: done
upstream:
  - path: docs/issue-2894/reports/adversarial-review-3fb40e3e.md
    sha: 8a2ee6768bc3dc7a3d5f68d05c26e4d0e5e1eb1e
  - path: roster.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: gates/gh_rest.py
    sha: same-commit
  - path: test/test_spawn_attempt_staleness.py
    sha: same-commit
---

# issue-2894 — silent-failure-audit-dd4cce49 record

canonical: `spawn.py:1494-1510` pre-fix, `6bf67b9836df94fb85a9452abca53e5da28d3b1d:spawn.py:1508` (read this session via `git show 6bf67b98:spawn.py`) — the exact-match `== "CLOSED"` comparison this record fixes.

skill-verdict: silent-failure-audit — applied: invoked; used the skill's
error-handling-path lens on `_attempt_issue_closed()`'s own re-check call
against the pre-fix source cited directly above — the exact-match
`== "CLOSED"` comparison against a GraphQL answer of `"MERGED"` was a
silently-absorbed failure mode (no exception, no non-zero exit, just a
comparison that could never be true for that input shape), the same
defect class the skill exists to catch.
skill-verdict: work-in-english — applied: invoked; record, commit
messages, and PR title/body are in English per the policy, with only this
final user-facing summary in Korean.

## What was done

Round 2 on PR #2896 (branch `issue-2894/silent-failure-audit-0c41a52b`,
commit `6bf67b9836df94fb85a9452abca53e5da28d3b1d`, cherry-picked onto this
branch as `31ca23c6`), after independent adversarial verification
(`docs/issue-2894/reports/adversarial-review-3fb40e3e.md`, PR #2897,
merged) found PR #2896's central acceptance criterion only half held
against the real repo: the four-halt before/after count was live-measured
at 4 -> 2, not 4 -> 0, plus two structural findings on the same call.
This round fixes all three, all inside `_attempt_issue_closed()`
(`spawn.py:1465-1520`) and its one new call site into
`gates/gh_rest.py`.

**1. The state-comparison defect (the only one that changed the
acceptance number).** derived: `gh issue view 614 --json state -q
.state` (run this session) — result: `MERGED`. derived: `gh api
repos/tokenmaxxxer/on-the-record/issues/614 --jq '{pull_request,state}'`
(run this session) — result:

```
{"pull_request":{"diff_url":"https://github.com/tokenmaxxxer/on-the-record/pull/614.diff","html_url":"https://github.com/tokenmaxxxer/on-the-record/pull/614","merged_at":"2026-08-10T04:38:49Z","patch_url":"https://github.com/tokenmaxxxer/on-the-record/pull/614.patch","url":"https://api.github.com/repos/tokenmaxxxer/on-the-record/pulls/614"},"state":"closed"}
```

Two of the four issue-#2894 halt numbers (614, 489) are numbers of
merged pull requests, not closed issues. The pre-round-2 code called
`gh issue view --json state` (GraphQL), which reports a PR-backed number
as `"MERGED"`, and compared it with `r.stdout.strip().upper() ==
"CLOSED"` — an exact match that structurally can never be true for
`"MERGED"`. The field that differs: GraphQL's `state` enum has three
values (`OPEN`/`CLOSED`/`MERGED`) for issue-or-PR nodes, while the REST
Issues API (`gh api repos/{o}/{r}/issues/{n}`) has only two
(`open`/`closed`) — REST folds "merged" into "closed" because a merged PR
*is* closed.

Fix: `spawn._attempt_issue_closed()` (`spawn.py:1508-1516`) no longer
calls `subprocess.run(["gh", "issue", "view", ...])` directly. It now
calls the new `gates.gh_rest.fetch_issue_state(root, issue,
timeout=_GH_STATE_RECHECK_TIMEOUT_SEC)` (`gates/gh_rest.py:63-75`), which
wraps the existing `_api_json(repo, f"issues/{issue}")` REST helper and
returns the lower-cased `state` field, and compares with `state ==
"closed"` instead of the old upper-case exact match against a
GraphQL-only value.

**2. GraphQL quota reintroduction (adversarial-review-3fb40e3e finding
3).** derived: `python3 -m pytest test/test_spawn_attempt_staleness.py -q
-k test_uses_rest_not_graphql` (new test, run this session) — the new
test asserts the only `gh` subprocess invocation observed is `["gh",
"api", "repos/.../issues/<n>", ...]`, never `["gh", "issue", "view",
...]`. Routing through `gates/gh_rest.py` fixes this as a side effect of
fix 1 — `fetch_issue_state()` is built on the same `_api_json()` REST
helper that the two sibling class-recheck paths already use
(`gates/requirement_linkage.py:62`, `gates/acceptance_gate.py:174`, both
call `gh_rest.fetch_issue_body()`).

**3. Missing timeout (adversarial-review-3fb40e3e finding 2).** derived:
`grep -n "timeout=10" gates/gh_budget.py` (run this session) — result:
`gates/gh_budget.py:37: capture_output=True, text=True, timeout=10)`.
Added `timeout=` to the `gh`/`git` subprocess calls this call path
reaches: `gates/gh_rest.py`'s `owner_repo()` and `_api_json()` both
gained an optional `timeout: float | None = None` parameter (default
`None`, preserving every existing caller's untimed behavior — additive,
not a behavior change for `fetch_issue_body`/`fetch_issue`/
`fetch_pr_body`/etc.), threaded through to their `subprocess.run(...,
timeout=timeout)` calls, with `subprocess.TimeoutExpired` added to the
existing `except OSError` fail-closed branches. `_attempt_issue_closed()`
passes a concrete `_GH_STATE_RECHECK_TIMEOUT_SEC = 10` (`spawn.py:1460`),
matching the `gh_budget.py:37` convention quoted above — the only other
`gh api ...`-calling site in this codebase that already carries a
timeout.

**Test harness fix.** derived: `git diff origin/main..HEAD --
test/test_spawn_attempt_staleness.py` (run this session) — PR #2896's
own tests mocked `spawn.subprocess.run` to return a hand-built
`"CLOSED\n"`/`"OPEN\n"` string, a shape only the old GraphQL call ever
produced, so the harness could not have exposed the "MERGED" gap by
construction. The file now: adds `_mixed_gh_run()` (module-level helper,
next to `_git_repo()`), which routes `git remote get-url origin` through
the real `subprocess.run` and only fakes the `gh api ...` leg, with a
real `repos/{owner}/{repo}/issues/{n}`-shaped JSON payload as the
response body instead of a bare status string; adds
`test_closed_pull_request_number_is_cleared` and
`test_unknown_class_halt_on_merged_pr_number_stops_replaying`, both
constructing the exact JSON shape the real REST endpoint returns for a
merged PR number (`{"state": "closed", "pull_request": {"merged_at":
...}}`, matching the live `gh api .../issues/614` output quoted above);
adds `test_uses_rest_not_graphql`; updates every other
`AttemptIssueClosedTest`/`SpawnAttemptSweepIssueClosedTest` case to the
new mixed-run shape and gives `_git_repo()` a real `origin` remote.

derived: `python3 -m pytest test/test_spawn_attempt_staleness.py -q`
(run this session) — result: `52 passed` (49 from PR #2896 + 3 new:
`test_closed_pull_request_number_is_cleared`,
`test_unknown_class_halt_on_merged_pr_number_stops_replaying`,
`test_uses_rest_not_graphql`).

**Acceptance criterion 2, re-run live against the real repo, real `gh`
binary** (a scratch `spawn-attempts.jsonl` with the issue's own four
halt shapes, `cwd` pointed at a scratch repo with `origin
https://github.com/tokenmaxxxer/on-the-record.git`, driven through
`roster.spawn_attempt_sweep()` directly — same method
adversarial-review-3fb40e3e used to find the gap). derived: `python3 -c
"..."` harness invoking `roster.spawn_attempt_sweep()`, run this session
— result:

```
BEFORE (fallback disabled to show the pre-fix baseline replay):
  issue-488, issue-489, issue-614, issue-645 all report live
  emitted live-halt lines: 4

AFTER (fix active, real gh, real issue/PR numbers):
  issue-488: halt RESOLVED (resolution=issue-closed)
  issue-489: halt RESOLVED (resolution=issue-closed)   <- merged-PR number
  issue-614: halt RESOLVED (resolution=issue-closed)   <- merged-PR number
  issue-645: halt RESOLVED (resolution=issue-closed)
  emitted live-halt lines: 0

FOLLOWING TICK: emitted live-halt lines: 0 (stays silent)
```

Before/after count for the four halts issue #2894 names: 4 -> 0,
including the two (614, 489) that stayed live after PR #2896's own fix.

**A genuinely new spawn failure still reports** (must-not guard,
re-run this session). derived: `python3 -c "..."` harness, continued,
same scratch ledger, this session — appended a fifth halt
(issue=2894, a real currently-open issue, skill `brandnew-eeeeeeee`,
reason `"skill brandnew not found"`, an unknown-class shape distinct from
the four resolved entries) — next `roster.spawn_attempt_sweep()` call
printed `issue-2894/brandnew-eeeeeeee: spawn halted pre-workspace ...:
skill brandnew not found`, emitted live-halt lines: 1. Unaffected by the
four already-resolved entries, consistent with
adversarial-review-3fb40e3e's own signal-loss finding (each spawn
attempt is its own independently-keyed `attempt_id` ledger entry).

**Overhead, re-measured after the change.** derived: `python3 -c "..."`
timing harness, single direct call to `spawn._attempt_issue_closed()`
against a still-open-shaped attempt, real `gh`, run this session —
result: `single call elapsed: 0.4271s`. adversarial-review-3fb40e3e
measured `0.4229s` pre-fix (one GraphQL round trip). Moving from GraphQL
to REST does not measurably change single-call latency (both are one
network round trip); the win is quota isolation (finding 2), not speed.
No overhead regression.

**Four standing invariants.** derived: `python3 gates/retirement_count.py`
(run this session, on this branch and again with the fix stashed out via
`git stash`/`git stash pop`) — result: `1136` matched lines both with and
without the fix — no new "role" occurrences, unchanged from
adversarial-review-3fb40e3e's own `1136`-vs-`1136` reading of PR #2896.
derived: `python3 -m pytest . -q` (run this session, on this branch and
in a worktree of `origin/main` at `8a2ee676`) — result: `17 failed, 662
passed, 3 xfailed` here vs `17 failed` on `origin/main`, identical
failing-name set (`diff` of the two sorted `FAILED`-line files: empty).
The overhead measurement is quoted directly above. The
monitor/watch-machinery invariant is this fix itself — the sweep still
prints `RESOLVED ... resolution=issue-closed` for every halt it clears
(not a silent drop) and still prints the full `spawn halted
pre-workspace ...` line, unchanged, for anything it does not clear
(`test_unknown_class_halt_on_open_issue_keeps_reporting`, still passing
per the 52-passed result quoted above).

## Why

derived: this session's own live `gh`/`pytest`/`roster.spawn_attempt_sweep()`
runs quoted under "What was done" above are the grounding for every
choice below, not PR #2896's or adversarial-review-3fb40e3e's own prose.

This round's own spawning instructions (citing adversarial-review-3fb40e3e)
directed fixing the state-comparison defect without enumerating strings,
since GitHub's set of terminal states for an issue-or-PR node is not
open-ended in a way that matters here — the fix does not add a third
string to compare against (`"MERGED"` alongside `"CLOSED"`); it switches
to the REST endpoint that never emits a third value in the first place,
so there is nothing left to enumerate. This is narrower than a
string-matching fix and closes the actual gap (a PR number is a number
that will never again show up as `"CLOSED"` from GraphQL, no matter how
long the wait) rather than special-casing the two values a small live
sample happened to produce.

Routing through `gates/gh_rest.py` rather than teaching
`_attempt_issue_closed()` to parse `"MERGED"` itself was chosen over
widening the old GraphQL call's comparison to `{"CLOSED", "MERGED"}`: the
widened-comparison approach would still leave the GraphQL-quota finding
unfixed (issue #1569's reason for `gh_rest.py` existing at all) and would
still need its own `timeout=` added from scratch, duplicating what
`gh_rest.py` already carries for its other four call sites. One change
closes both findings because they shared the same root call site.

The diagnostic stderr line the pre-round-2 code printed on a raw
exception (distinguishing "still open" from "recheck itself broke") is
not reproduced after the fix — `gh_rest._api_json()`'s fail-closed
`except (OSError, subprocess.TimeoutExpired): return None` swallows that
distinction the same way the two sibling call sites already accept
(`gates/requirement_linkage.py:62`, `gates/acceptance_gate.py:174` — a
`None` body from `gh_rest.fetch_issue_body()` is not separately logged).
Matching that established convention was judged more valuable than
keeping a dedicated diagnostic unique to this one call site, since "match
the siblings" was explicit in this round's own instructions and the
fail-safe behavior itself (still-live on any ambiguous case) is unchanged
and still covered by `test_gh_failure_is_conservative_not_cleared` and
`test_gh_exception_is_conservative_not_cleared` (both in the 52-passed
result above).

## What did not work

None.

## Upstream basis

derived: `gh pr diff 2896`, `git log --oneline -5`, and the live
`gh`/`pytest`/`roster.spawn_attempt_sweep()` commands quoted under "What
was done" above (all run this session) ground every citation below.

- `docs/issue-2894/reports/adversarial-review-3fb40e3e.md` (this repo,
  commit `8a2ee676`) — independent verification of PR #2896 that found
  the 4 -> 2 gap, the GraphQL-quota finding, and the missing-timeout
  finding this record fixes.
- PR #2896, commit `6bf67b9836df94fb85a9452abca53e5da28d3b1d`
  (cherry-picked onto this branch as `31ca23c6`) — the fallback this
  round fixes, not replaces.
- `gates/gh_rest.py` (this session, before and after this record's own
  edits) — REST helper convention, issue #1569.
- `gates/gh_budget.py:37` (read this session) — the `timeout=10`
  convention this fix's `_GH_STATE_RECHECK_TIMEOUT_SEC` matches.
- `gates/requirement_linkage.py:62`, `gates/acceptance_gate.py:174`
  (read this session) — the two sibling class-recheck call sites this
  fix now matches in REST-routing convention.

## Open findings

None — all three findings from adversarial-review-3fb40e3e (the state
mismatch, the GraphQL quota reintroduction, the missing timeout) are
fixed in this round, verified live against the real repo and real `gh`
binary above. The 17 pre-existing, environment-dependent test failures
(unrelated to this change, identical set on `origin/main`) are not
findings of this record.

## Next steps

derived: `gh pr create --title "issue-2894: round-2 fix -- REST state
check resolves the merged-PR gap PR #2896 left at 4->2" --body-file
/tmp/pr2894-round2-body.md --base main --head
issue-2894/silent-failure-audit-dd4cce49` (run this session) — result:
`https://github.com/tokenmaxxxer/on-the-record/pull/2902`. derived: `gh
pr comment 2896 --body ...` (run this session) — result:
`https://github.com/tokenmaxxxer/on-the-record/pull/2896#issuecomment-5469366491`
— PR #2896 could not be closed directly from this session (`gh-guard`
refused: "closing a PR is the human's acceptance/refusal — a skill
session only opens PRs and pushes to its own issue branch", two-account
model, contract v3 s8), so it is left open with a comment pointing to
#2902 for a human to close. `loop_state: done` — no further action
expected from this record itself; #2902 is the delivery.
