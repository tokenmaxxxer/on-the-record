---
issue: 2908
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: 1008fe49:on-the-record/hooks/self-update.sh, 1008fe49:on-the-record/hooks/poll-rearm.sh, 1008fe49:on-the-record/hooks/pretooluse_dispatcher.py, 1008fe49:on-the-record/hooks/decision-queue-stopgate.sh, 1008fe49:on-the-record/hooks/impact-guard.sh, 1008fe49:on-the-record/hooks/merge-allow-gate.sh, 1008fe49:on-the-record/hooks/plan-order-guard.sh, 1008fe49:on-the-record/hooks/quality-bar-gate.sh, 1008fe49:on-the-record/hooks/spawn-allow-gate.sh, 1008fe49:test/test_self_update_working_tree_untouched.py, 1008fe49:test/test_engine_checkout_resolve_muster_retired.py
type: verification-record
breaking: false
verdict: claims-confirmed-no-regressions-two-open-findings-carried-forward
loop_state: landed
upstream:
  - path: PR #2910 (issue-2908/silent-failure-audit-ef3215b3)
    sha: 1008fe494b1e78fa8b8eb71162a616386dfbb942
  - path: 1008fe49:docs/issue-2908/reports/silent-failure-audit-ef3215b3.md
    sha: 1008fe494b1e78fa8b8eb71162a616386dfbb942
skill-verdict: work-in-english — applied: invoked; loaded the SKILL.md via the Skill tool before writing this record. This record, all commands, and the PR text are in English; only the final chat summary to the user is in Korean.
other mounted skills: not triggered — this is a single-PR read-and-reproduce audit (checkout a branch, re-run cited tests, verify cited greps and diffs), not a multi-module build; freelunch's fan-out threshold (width >= 2 units, ~100+ lines each) did not apply, so the whole unit was delegated to one freelunch:freelunch-worker (foreground, per contract v3 s22 in this headless session) instead of run inline; no other mounted skill's trigger matched.
---

# issue-2908 — independent-verification-2 record

## What was done

canonical: `gh issue view 2908` (full body, acceptance criteria, non-goals) and `gh pr view 2910 --json body,commits,files,additions,deletions,mergeable` — read before checking out the branch.

Fetched PR #2910 (`issue-2908/silent-failure-audit-ef3215b3`, tip `1008fe49`) into the working tree as `pr-2910-review` and delegated a full independent re-check of every claim in the subject's own record (`1008fe49:docs/issue-2908/reports/silent-failure-audit-ef3215b3.md`) to one freelunch worker, run in the foreground and consumed in this same turn. The worker checked out the branch itself and reproduced each check from scratch rather than trusting the record's prose.

### Claims checked against the actual diff and live command output

1. **Skew visibility** — `on-the-record/hooks/self-update.sh`'s new `printf '[self-update] engine checkout %s commits behind origin/main...'` line sits inside the branch that fires only when `behind_err != "0"`; the `pull=ok` (matched) branch has no new output. CONFIRMED by direct read of the diff.
2. **Automatic self-update dispatch, no new unconditional pull** — `on-the-record/hooks/poll-rearm.sh`'s new `nohup python3 "${checkout}/spawn.py" self-update ... & disown` sits inside the existing `if [ "$due_rc" -eq 0 ]` gate, directly beside the pre-existing watchdog `nohup` launch — same TTL gate, same detach pattern, no new cadence. `spawn.py`'s `self_update_pull_cli()` (the #2749 CLI this now calls automatically) is pre-existing code that refuses when live sessions are detected. CONFIRMED.
3. **`muster` retired from all 9 resolve implementations** — derived: `grep -rn "tokenmaxxxer/muster" on-the-record/` — result: no output (rc=1). The diff removes the candidate from the 8 shell files plus `pretooluse_dispatcher.py`; the only remaining string match anywhere in the repo is prose inside the new test file's own name/docstring, outside `on-the-record/`. CONFIRMED.
4. **New/extended test files pass** — derived: `python3 -m pytest test/test_self_update_working_tree_untouched.py test/test_engine_checkout_resolve_muster_retired.py -q` on `1008fe49` — result: `5 passed in 0.94s`. Matches the PR body's own count. CONFIRMED.
5. **Pre-existing pull-gate test still green** — derived: `python3 -m pytest test/test_self_update_pull_gate.py -q` on `1008fe49` — result: `5 passed in 0.91s`. CONFIRMED.
6. **No regression in the full suite** — derived: `python3 -m pytest . -q` on `1008fe49` — result: `17 failed, 667 passed, 3 xfailed`; the same command on `origin/main` (via `git worktree add /tmp/main-check origin/main`) — result: `17 failed, 686 passed, 3 xfailed`. Diffing the sorted `FAILED ...` lines from both runs is empty — the 17 failing test names are identical on both sides. The passed-count delta (667 vs 686) is base-branch drift — `origin/main`'s tip carries two unrelated test files (`test_session_completion_heartbeat.py`, `test_workspace_progress_tracking.py`) that post-date this PR's merge-base — not a regression this PR introduced or a count the subject's record miscounted; the identical-failure-set claim itself holds exactly. CONFIRMED, with this base-drift caveat added since the subject's record did not mention it.
7. **Hardcoded `${CLAUDE_PLUGIN_ROOT}/..` call sites, cited as the reason a full payload-move is out of scope** — read directly: `on-the-record/commands/consult.md:10` contains `` `ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` ``; `on-the-record/hooks/absorbed-branch-recut-guard.sh:55` contains `spawn_py="${CLAUDE_PLUGIN_ROOT:-}/../spawn.py"`. Both exact. CONFIRMED.
8. **Self-clone failures silently absorbed, pre-existing, not introduced by this PR** — derived: `git diff origin/main...1008fe49 -- on-the-record/hooks/pretooluse_dispatcher.py` — result: the only hunk touching the resolve-order list removes the `muster` candidate tuple; the surrounding `try: ... except Exception: pass` around the self-clone `subprocess.run(["git", "clone", ...])` at `1008fe49:on-the-record/hooks/pretooluse_dispatcher.py:156` is untouched by the diff. Same check on the shell files (`self-update.sh`, `poll-rearm.sh`, `merge-allow-gate.sh`, `decision-queue-stopgate.sh`, `impact-guard.sh`, `plan-order-guard.sh`): each diff only removes the adjacent `muster` fallback line, never the `git clone -q ... "$own" 2>/dev/null` line itself. CONFIRMED as pre-existing, not this PR's own defect.
9. **No new `role`/`roles` token in this diff** — `gates/retirement_count.py` has zero diff (untouched). derived: `git diff origin/main...1008fe49 | grep -iE '^\+.*\brole'` — result: 2 hits, both inside the new `docs/issue-2908/reports/silent-failure-audit-ef3215b3.md` (a `role:` frontmatter key and a prose sentence quoting "role/roles axis") — documentation, not the retired code axis `retirement_count.py` checks for. CONFIRMED.
10. **No unconditional `git pull` added anywhere in the executable diff** — derived: `git diff origin/main...1008fe49 | grep -iE '^\+.*git pull'` — result: 1 hit, prose inside the same markdown report file, not a shell command. The only new invocation added to any hook is the already-gated `spawn.py self-update` CLI call (claim 2). CONFIRMED — satisfies the issue's own non-goal ("no unconditional `git pull` under running sessions").

### Not re-reproduced

The subject record's one-time live claims against the real machine state — the actual `~/.claude/tokenmaxxxer/muster` clone's rev-list count before/after its rename, and the live-session refusal demonstrated against that session's own roster entry — were not independently re-run here (re-running them would mean mutating the same real path a second time, or fabricating a new live-session claim to refuse against). canonical: `1008fe49:spawn.py` — the `self_update_pull_cli()` function this refusal exercises is present in the diff's tree with none of its own lines changed by this PR; derived: `python3 -m pytest test/test_self_update_pull_gate.py -q` on `1008fe49` — result: `5 passed in 0.91s` (claim 5), the existing automated coverage of that same refusal path. Flagged here as unverified-by-reproduction rather than silently treated as confirmed.

## Why

Contract v3 headless/single-shot rule (s22) required consuming the delegated worker's result within this same turn rather than dispatching it to the background — the freelunch directive's default background dispatch does not apply here, so the worker ran in the foreground. The verification itself re-ran every claim's underlying command from scratch (fresh checkout, fresh pytest invocations, fresh greps) rather than re-stating the subject's own record, per this role's purpose: an independent check is only worth landing if it could have caught a wrong or unreproducible claim, not if it just echoes what the subject already asserted.

## What did not work

None.

## Upstream basis

PR #2910 (`issue-2908/silent-failure-audit-ef3215b3`, tip `1008fe494b1e78fa8b8eb71162a616386dfbb942`) is the deliverable under review; `sha: same-commit` does not apply here since none of the reviewed code lands in this record's own commit — all cited paths carry the real PR tip sha per contract §1.

## Open findings

1. **Full payload-move for the engine remains genuinely open** (carried forward from the subject's own record, not newly discovered here): the two `${CLAUDE_PLUGIN_ROOT}/..`-shaped call sites (claim 7 above) and the two divergent `gates/` trees mean folding the 17 root modules into `on-the-record/` is a real migration, unverified end-to-end against an actual `/plugins update` installer run. Resolution path unchanged from the subject's record: a follow-up that rewrites both call sites, reconciles the `gates/` trees, and is verified against a real installer run.
2. **Self-clone failures are silently absorbed** (carried forward): derived: `git diff origin/main...1008fe49 -- on-the-record/hooks/pretooluse_dispatcher.py on-the-record/hooks/self-update.sh on-the-record/hooks/poll-rearm.sh` — result: the `except Exception: pass` / `2>/dev/null` around every self-clone attempt (claim 8 above) is confirmed unchanged by this diff across all checked files, giving no diagnostic on clone failure (network down, disk full, permission error). Pre-existing, not introduced by this PR; the subject's record already logged this as an open finding rather than fixing it, matching the codebase's stated fail-open design intent. No new resolution path beyond what the subject already proposed.
3. **New here**: the full-suite before/after comparison's passed-count delta (667 vs 686, claim 6 above) is base-branch drift from two test files added to `origin/main` after this PR's merge-base, not a count either side miscounted — worth naming explicitly since a future reader diffing raw pytest summary lines without this note could mistake the delta for missing test coverage. No action needed; the identical-failing-name-set claim this delta could have obscured was checked directly, not inferred from the counts.

## Next steps

None — loop_state is terminal (`landed`). All three open findings above are handoffs, not in-progress work on this record.
