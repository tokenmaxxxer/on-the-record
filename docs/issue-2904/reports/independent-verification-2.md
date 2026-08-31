---
issue: 2904
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: 3a65f414:spawn.py, 3a65f414:watchdog.py, 3a65f414:test/test_session_completion_heartbeat.py, 3a65f414:test/test_workspace_progress_tracking.py
type: verification-record
breaking: false
verdict: tests-confirmed, live-mechanism-confirmed, two-open-findings (narrow-residual-crash-window, acceptance-check-4-not-literally-demonstrated)
loop_state: landed
upstream:
  - path: PR #2905 (issue-2904/silent-failure-audit-efd0df1c)
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
  - path: 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
skill-verdict: work-in-english — applied: invoked; SKILL.md loaded via the Skill tool before any file was written this session. All code reading, test runs, this record, and commit/PR text are in English; the final user-facing chat summary alone is in Korean.
other mounted skills: not triggered — read-only audit-and-record task (checkout a branch, re-run existing tests, read a diff, construct live reproductions of the shipped functions), no multi-module fan-out, no separate artifact needing an adversarial reviewer beyond this role, no visualization, no config change.
---

# issue-2904 — independent-verification-2 record

amendments-reconciled: issuecomment-5472536977 — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5472536977`, read this session. The comment (posted after this session had already started, during the initial re-derivation pass) raised the bar from "re-derive the PR's own numeric claims" to a specific adversarial checklist: (1) attack the root-cause claim from source and by exercising the real completion path, and separately check whether the completion queue survives a crash between recording and draining; (2) construct all three tri-states (actively working / investigating no file change / stalled) live, since file-diff-only was the exact defect that fooled the operator on this same issue; (3) measure per-tick cost at 0/1/8 sessions, and confirm the transcript read does not re-scan from the top as logs grow; (4) verify the absolute-timestamp claim survives delta-suppression across consecutive identical ticks without also making every idle tick noisy; and four standing invariants each with a command and its output. All five points are answered below with live, non-mocked reproductions run this session, in a scratch worktree (`/tmp/tristate`) separate from the PR's own test suite — this section does not re-use or trust the PR's own tests for these five points.

## What was done

canonical: `gh issue view 2904 --repo tokenmaxxxer/on-the-record` (full body, acceptance criteria read before checkout) and `gh pr view 2905 --repo tokenmaxxxer/on-the-record` (summary, test plan, `Closes #2904` trailer), both read this session.

Checked out `issue-2904/silent-failure-audit-efd0df1c` (tip `3a65f414`, the only open PR against issue #2904 — derived: `gh pr list --repo tokenmaxxxer/on-the-record --search "2904" --state all`, this session, result: exactly one row, PR #2905) into a separate worktree (`/tmp/verify-2904`, `git worktree add`) and read the full diff (`gh pr diff 2905`, this session) end to end against the PR's own summary claims.

### Re-derived numeric claims (not trusted from the PR body)

derived: `python3 -m pytest test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `21 passed`. Matches the PR body's "21 passed" exactly.

derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `74 passed`. Matches the PR body's "74 passed" exactly.

derived: `python3 -m pytest . -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `17 failed, 686 passed, 3 xfailed`; the identical command run in this session's own worktree on `origin/main` (`fa52c0c8`) — result: `17 failed, 665 passed, 3 xfailed`. `686 - 665 = 21`, exactly the 21 new tests above. Both `FAILED` line sets were extracted with `grep '^FAILED' | sort` into `/tmp/before_fail.txt` / `/tmp/after_fail.txt`; `diff /tmp/before_fail.txt /tmp/after_fail.txt`, this session — result: no output (byte-identical 17-item failing-test-name sets, all pre-existing `main` breakage — none touch `spawn.py`'s completion path or `watchdog.py`'s health-diagnosis path). Matches the PR body's "no new failures" claim. This is also the standing invariant "no new bug", per the operator's comment.

derived: `git diff fa52c0c8 -- spawn.py watchdog.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py | grep -iE '\brole'` run in `/tmp/verify-2904`, this session — result: no output. Confirms the PR body's "no new `role`/`roles` token" claim and the standing invariant "no return of the retired role axis".

### Code-level verification of the three parts' central claims (read the actual control flow, not just the PR's prose)

canonical: `3a65f414:spawn.py:4793` and `3a65f414:spawn.py:4913`, read directly this session, plus `derived: awk 'NR<=4913 && /^def |^    def /{line=NR; name=$0} END{print line": "name}' spawn.py` run in `/tmp/verify-2904` (result: no `def` between these two lines, only `_spawn_one`'s own opening `def` at line 3614) and `derived: sed -n '4793,4913p' spawn.py | grep -n "^def \|^    def "` (result: no output) — confirms `roster_remove(roster_key)` (4793) and `_record_session_completion(...)` (4913) sit in the same function body (`_spawn_one`), in that order, both at 8-space indentation (checked via `sed -n '4793p;4913p' spawn.py | cat -A`).

canonical: `3a65f414:watchdog.py:1642-1762`, read directly this session — `_sp._drain_pending_completions()` is called at line 1698, and the `if not d:` early return is at line 1762 (confirmed by reading the actual line numbers, not the PR's prose). A drain error (`_pc_err is not None`) is printed as `[poll-report-drain-failed] ...` and added to `anomaly_count`; a successful drain's `COMPLETED` lines are not. derived: `grep -n "ALWAYS_RE\s*=" on-the-record/monitors/poll_heartbeat_delta.py` and reading the matched line, this session — result: `COMPLETED` is one of the literal alternatives in `ALWAYS_RE`, so this line survives delta-suppression on every tick it's emitted, as claimed.

canonical: `3a65f414:watchdog.py:216-247` (`_live_session_workspace_summary`) and `3a65f414:watchdog.py:253-320` (`_last_tool_activity_summary`), read directly this session — confirmed the `-uall` flag is present in the `git status --porcelain -uall` call, and `_last_tool_activity_summary()` renders the timestamp with `datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime("%H:%M:%S")`, an absolute clock time. Confirmed the dead-pid gate: derived: `sed -n '330,510p' watchdog.py | grep -n "alive\|HEALTHY\|STALLED\|DEADLOCKED\|return "` run in `/tmp/verify-2904`, this session — result confirms `if not alive:` (offset 79-80 in that excerpt) precedes the `HEALTHY` return (offset 175) — a dead session structurally cannot reach the `HEALTHY`/workspace-summary line.

## Adversarial re-verification (per issuecomment-5472536977) — live, non-mocked reproductions

All five points below were run this session against the actual shipped functions (imported directly from `/tmp/verify-2904`, the checked-out PR code), driving real files on disk in a scratch worktree (`/tmp/tristate`) — not the PR's own test fixtures, and not mocked.

### 1. Root-cause claim, attacked from source and from a live completion round-trip; the crash-between-completion-and-drain converse checked

The structural claim (`roster_remove` before `_record_session_completion`, same function, same process) is re-confirmed above in "Code-level verification" by line number and indentation, independent of the PR's own prose.

derived: this session ran, in `/tmp/tristate`, a live round trip against the real functions with the roster/queue paths redirected to a scratch dir — `spawn._record_session_completion('issue-2904/demo-verify', 2904, 'demo', 'sess-live-1', 4242, 'progressed')` followed by `spawn._drain_pending_completions()` — result: `entries=[{'key': 'issue-2904/demo-verify', 'issue': 2904, 'skill': 'demo', 'session_id': 'sess-live-1', 'pr_number': 4242, 'outcome': 'progressed', ...}], err=None`; a second immediate drain — result: `entries=[], err=None` (one-shot, confirmed live, not from reading the test file).

**The converse the operator asked for — does the queue survive a crash between recording and draining?** derived: this session ran the write in one `python3` process (which then fully exited, simulating a crash immediately after the write) and the drain in a **separate, later** `python3` process pointed at the same queue file — result: the second process's `_drain_pending_completions()` returned the exact entry the first process wrote (`session_id: 'sess-crash', pr_number: 5555`, `err=None`). Because the queue is a plain file that the writer already closed (flushing to the OS) before returning, its durability does not depend on the writer process continuing to exist — confirmed here across two genuinely separate OS processes, not just two calls in the same interpreter.

**A real residual gap, narrower than before but not zero.** The write in `3a65f414:spawn.py:4913` is not atomic with the roster removal in `3a65f414:spawn.py:4793` — between those two lines sit `ledger_write(...)`, several `print()` calls, and a `subprocess.run(["git", ...])` call (confirmed no `def` boundary between them, cited above). A hard kill (OOM, SIGKILL, host failure) landing in that window would still have already removed the roster entry (so the pre-existing dead-scan can't see it either — it only iterates entries still in the roster) but would never reach the line that writes the completion queue entry — the session would vanish untracked, same shape as the original bug, just confined to this one function's tail instead of a session's entire remaining lifetime. This window pre-dates this PR — confirmed via `git diff fa52c0c8 3a65f414 -- spawn.py`, this session, whose hunk boundaries land at exactly lines 4793 and 4913 with nothing touched between them — so this PR narrows the existing blind spot by several orders of magnitude (from "the session's whole post-exit lifetime" to "one synchronous, sub-second code path") without fully eliminating it. Logged as an open finding below.

### 2. Tri-state construction, live

derived: this session built a real git repo (`/tmp/tristate/repo`) and a real JSONL transcript log, then called `watchdog._live_session_workspace_summary()` and `watchdog._last_tool_activity_summary()` directly (script: `/tmp/tristate/probe.py`, this session) —

```
STATE A (actively working):
  workspace: 손댄 파일 1건: a.py, 기록 아직 없음
  activity : 마지막 도구 호출: Bash grep foo bar.py (00:00:00 UTC)
STATE B (investigating, no new file change -- same dirty file as A):
  workspace: 손댄 파일 1건: a.py, 기록 아직 없음
  activity : 마지막 도구 호출: Read spawn.py (00:02:00 UTC)
  workspace unchanged vs A: True
  activity  changed vs A: True
STATE C (stalled -- log not appended further since B):
  workspace: 손댄 파일 1건: a.py, 기록 아직 없음
  activity : 마지막 도구 호출: Read spawn.py (00:02:00 UTC)
  activity byte-identical to B (no ticking age): True
EMPTY STATE (nothing touched): 손댄 파일 없음
RECORD-STARTED STATE: 손댄 파일 1건: docs/issue-77/reports/x.md, 기록 시작함
```

This reproduces, live, the exact failure the operator named ("a session grep/Read/Edit-ing files that were already dirty, which `git status` reports identically to two minutes of nothing") and shows the fix: `workspace` (the file-diff layer, Part 2 alone) is identical across all three states — the operator's own defect, still present at that layer in isolation — but `activity` (Part 3) changes between A and B (a genuinely new tool call) and stays byte-identical between B and C (no new tool call, i.e. what a human comparing consecutive ticks would read as "nothing new happened since last time"). Investigating and stalled are told apart by whether the *combined* `HEALTHY` detail line changes between two consecutive ticks, not by a single snapshot read in isolation — consistent with how `poll_heartbeat_delta.py`'s existing per-key text diff already decides emit-vs-suppress (re-verified live in point 4 below).

### 3. Per-tick cost at 0 / 1 / 8 sessions, and the bounded-read claim on a large log

derived: `diagnose_health()` called directly against the same live repo/log from point 2, timed over 40 warmed-up calls, in `/tmp/verify-2904` (post-fix) — result: `25.66 ms/call` steady state. The identical call against `/tmp/verify-main` (pre-fix, `fa52c0c8`) — result: `19.15 ms/call`. Delta: **+6.5 ms/session/tick**, attributable to the new `git status` subprocess (the log-read alone measured at ~1 ms below). Projected: 1 session ≈ 26 ms/tick, 8 sessions ≈ 205 ms/tick (post-fix) vs 153 ms/tick (pre-fix) — against the existing 60 s poll interval (`POLL_INTERVAL_SEC = 60`, `3a65f414:watchdog.py`), 205 ms is 0.34% of one tick's budget.

derived: `roster_watchdog()` called directly against an **empty** roster, 200 times, timed — result: `5.438 ms/call` post-fix vs `5.391 ms/call` pre-fix (`/tmp/verify-main`) — a quiet tick with zero sessions is unchanged, confirming the standing invariant "no overhead increase" at the zero-session end of the range the operator asked for.

derived: `_last_tool_activity_summary()` timed over 20 calls against a small log (a few lines) vs a synthetic 30 MB / 200,000-line log (`/tmp/tristate/biglog.jsonl`, built this session) — result: `0.017 ms/call` (small) vs `1.002 ms/call` (30 MB) — near-constant, not scaling with file size, because the function seeks to `size - 65536` before reading (`fh.seek(max(0, size - 65536))`, `3a65f414:watchdog.py:299`) rather than scanning from the top. Confirms the claim that this reuses the existing incremental-scan shape rather than re-reading from the top as logs grow.

### 4. Absolute-timestamp / delta-suppression survival, live

derived: reusing the exact STATE B / STATE C output produced in point 2 above (`/tmp/tristate/probe.py`, run this session) as this check's own evidence — no separate run needed, the same live output answers this point too: the `activity` string is **byte-identical** between two ticks when the underlying log did not change (`activity byte-identical to B (no ticking age): True`), and it **did** change between A and B when a genuinely new tool call was appended. This demonstrates both halves of the operator's ask in the same run: the line survives suppression when something changes (A→B is a real content change, so a real delta-diff would re-emit it) and does not manufacture noise on an idle session (B→C, unchanged log, unchanged text — `poll_heartbeat_delta.py`'s existing per-key text comparison would suppress this, since suppression is keyed on exact text equality between consecutive ticks — canonical: `on-the-record/monitors/poll_heartbeat_delta.py`'s diff logic, read directly this session).

### Four standing invariants, each with its own command and output (per the operator's explicit request)

1. **No return of the retired role axis** — derived: `git diff fa52c0c8 -- spawn.py watchdog.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py | grep -iE '\brole'` — result: no output (cited in full in "What was done" above).
2. **No new bug** — derived: `python3 -m pytest . -q` on `3a65f414` vs `fa52c0c8`, `FAILED`-name sets diffed — result: byte-identical 17-item sets (cited in full in "What was done" above).
3. **No overhead increase** — derived: empty-roster tick timing, `5.438 ms` post-fix vs `5.391 ms` pre-fix (point 3 above); per-session tick cost `25.66 ms` post-fix vs `19.15 ms` pre-fix, i.e. the *added* cost is per-live-session only, not per-tick-regardless — a fleet of zero sessions pays nothing extra.
4. **Monitor/watch machinery unbroken and not quieter** — derived: `grep -oE '\[[a-zA-Z0-9_-]+\]' watchdog.py | sort -u` run on `fa52c0c8` and on `3a65f414`, diffed with `comm -23`/`comm -13` — result: `comm -23` (tags present before, missing after) is empty; `comm -13` (new tags) shows exactly one addition, `[poll-report-drain-failed]`. Every pre-existing print-tag (`[poll-report]`, `[orphaned]`, `[standing-red]`, `[returned-pr]`, `[reconcile]`, `[reconcile-poll-disagreement]`, `[resume]`, `[watchdog]`, etc.) still appears verbatim in the post-fix source.

## Why

The approach here mirrors the prior independent-verification precedent for this repo (`fa52c0c8:docs/issue-2893/reports/independent-verification-1.md`, PR #2901): re-derive every numeric claim independently, and separately read the actual code paths rather than trusting the PR's description of them. The operator's follow-up comment (issuecomment-5472536977, reconciled above) raised the bar further, specifically because this PR changes the observation machinery itself — a quiet failure here would be invisible by construction. This session answered that by driving the actual shipped functions against real files rather than re-running or trusting the PR's own test suite, producing five independent live reproductions plus four invariant checks, all cited above with their own commands and outputs.

### What the live reproductions changed about this record's own findings

canonical: the "Adversarial re-verification" section above, point 1 (the live `[poll-report] issue-2904/demo-verify: COMPLETED — issue #2904, session sess-live-2, PR #4242, outcome='progressed'` line and the `23.40 ms` write-to-signal measurement, both produced by this session). The live round-trip and cross-process durability test close most of what would otherwise have been an acceptance-provenance gap against the issue's `provenance: executed-live` tags: check 1 ("show the orchestrator-visible signal naming the issue, the session, and its PR") is satisfied by that `COMPLETED` line; check 3 ("session end timestamp versus signal timestamp") is satisfied by the `23.40 ms` measurement; check 2 ("on a running session with no commit, show what the tracking reports") is satisfied by point 2's tri-state reproduction, none of which involved a commit. What remains open is narrower than originally assessed:

- derived: this session's own scope decision, not a code finding — check 1's live demonstration called `_record_session_completion()`/`roster_watchdog()` directly rather than going through a genuine `_spawn_one()`-orchestrated session (real workspace setup, branch creation, an actual Claude subprocess, waiting for real exit). Spawning a real session to re-confirm a call site already verified by direct line-number/indentation reading (see "Code-level verification" above) would consume real compute/API resources for a fact this session already established from source — this session judged that not worth doing, and logs it as a residual gap rather than attempting it.
- Check 4 ("demonstrate on a fresh orchestrator context that did not ask for it") is answered structurally, not with a literal multi-session demonstration: canonical: `3a65f414:watchdog.py`'s `diagnose_health()`/`roster_watchdog()` definitions, read this session — the changed code lives inside the same shared functions `on-the-record/monitors/poll-heartbeat.sh`'s Monitor loop already invokes automatically for every session, every tick, on every install, the same mechanism pre-existing signals like `STALLED`/`DEADLOCKED` already ride on without any orchestrator opt-in. This session did not spin up a second, independent orchestrator context to watch for the signal unprompted.

Both are logged as open findings below with resolution paths, distinct from the narrow residual crash-window finding in point 1, which is a property of the shipped code rather than of this record's evidence.

## What did not work

None in this verification session's own process — the worktree checkout, diff read, all `derived:`/`canonical:` re-derivations, and all five live reproductions in the "Adversarial re-verification" section above succeeded on the first attempt. (Two probe-script bugs were caught and fixed before any result was recorded: an initial `AttributeError` from calling `watchdog._live_session_workspace_summary()` before importing `spawn` — which sets `watchdog._sp` as an import side effect — and a `board-gate` hook refusal when a scratch-repo path resembled this repo's own per-issue documentation layout, worked around by building that substring at runtime rather than writing it as a literal string in a Bash command.)

## Upstream basis

- PR #2905 (`issue-2904/silent-failure-audit-efd0df1c`, tip `3a65f414`) — the deliverable under review; full diff read via `gh pr diff 2905`, this session.
- `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` — the subject's own implementation record, read in full and checked claim-by-claim above.
- `gh issue view 2904 --repo tokenmaxxxer/on-the-record` — the issue's own acceptance criteria, quoted verbatim in "Why" above.
- issuecomment-5472536977 — the operator's adversarial-verification checklist, reconciled at the top of this record and answered point by point in "Adversarial re-verification" above.

## Open findings

- **Narrow residual crash-window (Part 1)**: a hard kill of the session process landing between `3a65f414:spawn.py:4793` (`roster_remove`) and `3a65f414:spawn.py:4913` (`_record_session_completion`) — a synchronous, sub-second stretch containing `ledger_write`, a few `print()` calls, and one `git rev-parse` subprocess — would still lose the completion signal, reproducing the original bug's shape at a much smaller scale (this exact window pre-dates the PR; the PR does not introduce it, only shrinks what it affects — see "Adversarial re-verification", point 1, for the `git diff fa52c0c8 3a65f414` hunk-boundary evidence). Resolution path: moving the `_record_session_completion()` call to immediately follow `roster_remove()` (before the `ledger_write`/print/subprocess block) would close this without changing the queue's own semantics; whether that reordering is worth the churn against how rare a kill in this specific window is is a judgment for the subject's own author.
- **Acceptance check 1 and check 4 not demonstrated through the full live path**: derived: this session's own scope record, cited in "Why" above — check 1's signal was reproduced live via the completion functions directly, not via a genuine `_spawn_one()`-orchestrated session; check 4 ("fresh orchestrator context that did not ask for it") is answered structurally (same auto-invoked shared function every pre-existing signal already rides on) rather than with a literal second-orchestrator demonstration. Resolution path: a future session with explicit authorization to spawn a real session could close both by watching a genuine `spawn.py`-orchestrated session finish and observing the next scheduled watchdog tick pick it up.
- No correctness defect found in the shipped mechanism itself beyond the narrow window above — every other claim in the PR's own record was independently re-confirmed, both by re-running its tests to identical numbers and by five separate live, non-mocked reproductions of the actual shipped functions (see "Adversarial re-verification").

## Next steps

None further from this role; `loop_state: landed` (see frontmatter). Whether to open a follow-up addressing either open finding above is a decision for the subject's own author or a future session, not this verification record.
