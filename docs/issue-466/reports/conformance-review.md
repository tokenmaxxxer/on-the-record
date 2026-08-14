# Conformance review of PR #470's decision-queue Stop-hook + respawn branch fix (issue-466)

kind: record
loop_state: verdict-issued
upstream: docs/issue-466/proposals/2026-08-08-decision-queue-stophook-and-respawn-branch-fix.md
code_under_review:
- on-the-record/hooks/decision-queue-stopgate.sh
- on-the-record/hooks/hooks.json
- on-the-record/hooks/test_decision_queue_stopgate.py
- spawn.py (checkout_issue_branch / _recut_absorbed_branch)
- tests/test_spawn.py

## What was done

canonical: docs/issue-466/proposals/2026-08-08-decision-queue-stophook-and-respawn-branch-fix.md
"How you'll know it worked" section, read this session — re-ran every
acceptance check from #466's proposal live against the current tree
(not against the historical PR #470 diff alone, since later issues
#719/#732/#784/#1021/#1032 touched the same functions) to render a
per-acceptance-line verdict.

## Why

#466's acceptance text names two concrete checks (Stop-hook wired +
passing, `test_spawn.py` red-green pair passing) and this issue's own
comment thread records an "APPROVE issue-466/implementation" but no
conformance record exists yet for the landed PR #470 — this record
closes that gap per the spawn-on-pr trigger.

## Per-acceptance verdicts

### #466 accept line 1 — Stop-hook fires with aged decision-queue items and stays silent without them — Present

```
$ python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q
17 passed in 1.84s
```
derived: `pytest on-the-record/hooks/test_decision_queue_stopgate.py -q`,
run this session — covers the three age tiers plus the
empty-queue/kill-switch clean-exit cases.

canonical: on-the-record/hooks/hooks.json `Stop` array, read this
session — `decision-queue-stopgate.sh` is present as an entry
alongside `stop-gate.sh`/`role-test-claim-guard.sh`.

derived: `grep -n "ORCHESTRATE_OFF\|CLAUDE_ROLE" on-the-record/hooks/decision-queue-stopgate.sh`, run this session:
```
16:# Kill switches: ORCHESTRATE_OFF=1, CLAUDE_ROLE set (spawned role session).
26:case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
78:role = os.environ.get("CLAUDE_ROLE", "")
```
canonical: same grep, this session — both kill switches named in the
proposal's Constraints are wired.

### #466 accept line 2 — Respawn onto an already-absorbed stale branch is detected and handled loudly — Present

canonical: spawn.py:6054-6089 `checkout_issue_branch()`, read this
session — the local-branch-exists path calls
`_recut_absorbed_branch()` (spawn.py:5942) instead of unconditionally
reusing the local ref; that helper checks `base..br` ahead-count and,
on 0-ahead, deletes and recuts the branch with a stderr line, matching
the proposal's "loud by construction" design choice.

```
$ python3 -m pytest tests/test_spawn.py -q -k "test_checkout_starts_fresh_on_stale_branch_merged_into_base or test_checkout_starts_fresh_on_general_stale_zero_ahead_branch"
2 passed, 501 deselected in 0.45s
```
derived: `pytest tests/test_spawn.py -k test_checkout_starts_fresh_on_stale_branch_merged_into_base|test_checkout_starts_fresh_on_general_stale_zero_ahead_branch`,
run this session — these two are the proposal's item 5 shapes: the
issue-441 fully-absorbed shape
(`test_checkout_starts_fresh_on_stale_branch_merged_into_base`) and the
general stale-branch shape from the #428 survey's issue-999 fixture
(`test_checkout_starts_fresh_on_general_stale_zero_ahead_branch`), both
defined in tests/test_spawn.py.

Note: the file moved from root `test_spawn.py` to `tests/test_spawn.py`
between #470's landing and this review (unrelated later reorg); this
does not affect the acceptance verdict since the same test bodies run
green at their current path.

## Summary table

derived: the two `pytest` runs cited above (accept line 1's
`on-the-record/hooks/test_decision_queue_stopgate.py -q` and accept
line 2's `tests/test_spawn.py -k
test_checkout_starts_fresh_on_stale_branch_merged_into_base|test_checkout_starts_fresh_on_general_stale_zero_ahead_branch`),
run this session — source for both rows below.

| # | #466 acceptance line | Verdict |
|---|---|---|
| 1 | Stop-hook wired into hooks.json, tests green, silent when queue clean | Present |
| 2 | Respawn onto an already-absorbed stale branch detected + handled loudly, test_spawn.py red-green pair | Present |

## Open findings

canonical: the two per-acceptance-verdict sections above, this session
— no open finding. The mechanism was later extended by issues #719
(remote-stale distinction), #732 (original recut), #784 (mid-run
recheck), and #1021/#1032 (Stop-hook re-block bounding/isolation)
without breaking #466's original contract.

## Next steps

None — this closes issue-466's spawn-on-pr conformance-review
obligation; no corrective issue is warranted.

## Resolution path

N/A — no open finding to resolve.

Proposal: docs/issue-466/proposals/2026-08-08-decision-queue-stophook-and-respawn-branch-fix.md
