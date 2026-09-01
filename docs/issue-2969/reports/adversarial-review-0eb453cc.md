---
issue: 2969
role: adversarial-review-0eb453cc
author: adversarial-review-0eb453cc
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
loop_state: landed
type: fix
breaking: false
verdict: pass
upstream:
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  - path: lifecycle.py
    sha: 46864b697e40dab9d19a16d8e1296a0a4eab8f8d
  - path: docs/issue-2969/reports/silent-failure-audit-daadb0ad.md  # untracked on this branch -- lives on branch issue-2969/silent-failure-audit-daadb0ad (PR #3005), read via git show
    sha: fb309f65f29e0ff6593ca9532ccec24cba06c9bb
---

# issue-2969 — adversarial-review-0eb453cc record

skill-verdict: adversarial-review — applied: invoked; this record is a structurally independent re-verification of PR #2990's fix round — own isolated `git worktree` at the exact fix commit, own re-run of all four acceptance checks and the touched test file, own reading of the caller chain in `spawn.py`/`lifecycle.py` to adjudicate PR #3005's ungated-path argument line by line, rather than accepting PR #3005's or the record's claimed output.

## What was done

Independently re-verified issue #2969's deliverable (PR #2990, branch `issue-2969/silent-failure-audit+test-derivation-bb5cc534`) after its fix round, against the two `verdict: fail` findings that two earlier independent verifications (PR #2999, PR #3000) raised, and that PR #3005 / commit `46864b69` claim to resolve. Did not trust that claim; re-derived both from the code and my own command runs.

canonical: `gh pr view 2990 --json headRefOid -q .headRefOid` — result: `46864b697e40dab9d19a16d8e1296a0a4eab8f8d` — PR #2990's head is exactly the fix commit under review.

### Finding 1 (regression) — confirmed fixed

canonical: `git show 46864b69 -- on-the-record/monitors/poll_heartbeat_delta.py` (full diff read this session).

The stale `state_token == "HEALTHY"` comparison is replaced with a prefix match, and the changed-check now compares the full new state name instead of a hardcoded `"HEALTHY"`:

```python
            if state_token is not None and state_token.startswith(HEALTHY_STATE_PREFIX):
                pm = POLL_REPORT_STATE_RE.match(prev_line) if prev_line else None
                prev_state = pm.group(1) if pm else None
                changed = prev_state != state_token or (
```
(`on-the-record/monitors/poll_heartbeat_delta.py`, post-fix, lines matching commit `46864b69`'s diff hunk)

This restores issue #2906's per-tick suppression for repeats of the same `HEALTHY-*` substate, while treating a `HEALTHY-CONFIRMED`↔`HEALTHY-UNCONFIRMED` transition as a real, notify-worthy change (`prev_state != state_token` now compares the real names, not a bare `"HEALTHY"`).

Checked the fixture specifically, since a fixture that still fakes the state was named as the reason the regression escaped in the first place:

canonical: `git show 46864b69 -- on-the-record/monitors/test_poll_heartbeat.py` (full diff read this session).

```python
    entry = {"pid": os.getpid(), "work": None, "log": None,
              "start_time": watchdog._proc_start_time(os.getpid())}
    health = watchdog.diagnose_health("issue-500/implementation", entry, anomalies=[])
    return health["state"]
```
(`on-the-record/monitors/test_poll_heartbeat.py:466-469`, `_healthy_state_token()`, post-fix)

`_healthy_report()` now interpolates `{_healthy_state_token()}` instead of the literal `"HEALTHY"` — the fixture derives its state from the real `diagnose_health()`, not a hardcoded double. A future rename of the `HEALTHY-*` state now breaks this fixture loudly instead of staying silently pinned to a stale name.

Ran the acceptance checks myself in a fresh worktree at `46864b69`, not reusing any claimed output — derived: `git worktree add /tmp/verify-2969-46864b69 46864b69 && cd /tmp/verify-2969-46864b69` then:
```
$ python3 -m pytest tests/ -k health_verdict_confirmed_vs_unconfirmed -q
6 passed in 0.91s
$ python3 -m pytest tests/ -k liveness_pid_reuse -q
6 passed in 0.89s
$ python3 -m pytest tests/ -k flapping_verdict -q
7 passed in 0.91s
$ python3 -m pytest tests/ -k destructive_action_requires_consecutive -q
4 passed in 0.91s
$ python3 on-the-record/monitors/test_poll_heartbeat.py
37/37 passed
```

Read the specific regression test to confirm it is a genuine assertion, not execution-only — canonical: `on-the-record/monitors/test_poll_heartbeat.py:492-517`, `t_healthy_poll_report_with_drifting_detail_suppresses_after_first_tick`, read this session (worktree at `46864b69`):
```python
        r1 = _run_tick(checkout, home, _healthy_report(0))
        assert r1.returncode == 0, r1.stderr
        assert "[poll-report] issue-500/implementation: HEALTHY" in r1.stdout, r1.stdout

        for i in range(1, 6):
            r = _run_tick(checkout, home, _healthy_report(i))
            assert r.returncode == 0, r.stderr
            assert r.stdout.strip() == "", (
```
Tick 1 asserts the real `[poll-report]` line is emitted; ticks 2-6 (only the drifting last-tool-activity clause changes) assert `stdout` is empty — this drives the actual `poll_heartbeat_delta.py` script end-to-end via `_run_tick`, not a mock of the comparison.

### Finding 2 (false completeness claim) — argument adjudicated, sound

PR #2990's delivery record claimed `_auto_respawn_check()` is "the only place a watchdog verdict automatically triggers a destructive action." PR #3005 does not gate `lifecycle._self_trigger_respawn()`'s call into `_respawn_or_cap()`; it argues the gate would be unnecessary and harmful there on three grounds. Checked each against the code directly, not against the record's prose.

**Ground 1**: "only called after `_spawn_one()` confirmed process exit via `proc.wait()`."

canonical: `git show 46864b69:spawn.py` lines 4905-4906 and 5079-5081, read this session in the fix-commit worktree.
```python
        rc = proc.wait()
        roster_remove(roster_key)
```
(`spawn.py:4905-4906`)
```python
        _self_trigger_respawn(outcome, roster_key, cwd, issue, skill,
                              str(log_path), session_start_ts, single_phase)
        os._exit(rc if isinstance(rc, int) else 0)
```
(`spawn.py:5079-5081`)

Both snippets are inside the same `_spawn_one()` invocation; `proc.wait()` and `roster_remove()` (lines 4905-4906) execute strictly before `_self_trigger_respawn()` (line 5079) is ever called. Ground 1 is true as written: there is no inferred-liveness read on this path (no pid-presence or log-growth heuristic) — the exit is a direct syscall return.

**Ground 2**: "a second confirmation is structurally impossible because `roster_remove()` already deleted the entry."

Same citation as Ground 1 (`spawn.py:4905-4906` precedes `spawn.py:5079`) establishes `roster_remove()` runs before `_self_trigger_respawn()` can be reached. Compared against the gated sibling path's counter mechanism — canonical: `lifecycle.py:519-527`, read this session (worktree at `46864b69`):
```python
    confirm_prior = state.get(key, {})
    if verdict != "crashed":
        if confirm_prior.get("crash_confirms"):
            state[key] = {**confirm_prior, "crash_confirms": 0}
            _sp._respawn_state_save(state)
        return
    crash_confirms = confirm_prior.get("crash_confirms", 0) + 1
```
(`lifecycle.py:519-526`, `_auto_respawn_check`)

That counter depends on the roster entry staying visible to a later `roster_watchdog()` tick so `verdict` can be re-read against the same `key`. Since `roster_remove()` already deleted the entry before `_self_trigger_respawn()` runs (Ground 1's citation), no later tick can ever look up this `key` again to supply a second observation — the counter could never reach `RESPAWN_CONSECUTIVE_CONFIRMATIONS`. Ground 2 is true as written.

**Ground 3**: "other safeguards (attempt-cap, claim lock) already bound this path."

canonical: `lifecycle.py:444-455`, read this session (worktree at `46864b69`):
```python
    if total_attempts >= _sp.RESPAWN_ABSOLUTE_MAX:
        _sp._post_crash_comment(root, issue, key, work, log, trigger, absolute=True)
        return
    if attempts >= _sp.RESPAWN_MAX_ATTEMPTS:
        _sp._post_crash_comment(root, issue, key, work, log, trigger)
        return
    claim_path = Path(str(work) + f".respawn-claim-{session_start_ts}")
    try:
        fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return
```
(`lifecycle.py:444-454`, `_respawn_or_cap`, shared by both the watchdog-crashed path and this self-trigger path)

`RESPAWN_MAX_ATTEMPTS`/`RESPAWN_ABSOLUTE_MAX` caps and an atomic per-session claim lock (`O_CREAT | O_EXCL`) both run before `_respawn_or_cap()` ever calls `_spawn_one()` again. Ground 3 is true as written.

**Overarching question** (does the ungated path still leave a way for a live session to be killed on a single observation): no. `RESPAWN_CONSECUTIVE_CONFIRMATIONS` exists specifically to protect against a watchdog tick *inferring* death from an external, potentially-flaky signal — the incident the issue names (two live sessions killed by trusting one such verdict). `_self_trigger_respawn()` has no such inference to protect against, per Ground 1's citation: by the time it runs, the process's own exit has already been witnessed directly and synchronously (`proc.wait()`), not guessed at from a later, separate snapshot. Respawning here does not kill a live session — the session this `key` names has already, unambiguously, ended (same citation); the action is starting a new one for abandoned work, bounded by Ground 3's caps and claim lock. This is a materially different risk shape from the watchdog-verdict path the issue is about. The three grounds check out individually against the code's actual execution order (not just the docstring's prose about it), so the conclusion built on them is sound engineering judgment, not rationalization for skipping the work.

Confirmed the fix commit changes only comments here, no logic — canonical: `git show 46864b69 -- lifecycle.py`, read this session: every added line in that hunk falls inside the `_self_trigger_respawn()` docstring (a `"""..."""` block); the first executable line after the docstring, `if outcome not in _sp._ABANDONED_WORK_OUTCOMES:`, is unchanged — consistent with the record's framing as a completeness-claim correction, not a code defect.

Also cross-checked PR #3005's own record rather than just reading and trusting it — canonical: `git show origin/issue-2969/silent-failure-audit-daadb0ad:docs/issue-2969/reports/silent-failure-audit-daadb0ad.md`, read this session. It states both findings resolved with the same file:line citations independently re-derived above, its own re-run acceptance/regression evidence, and that PR #2990 (not PR #3005) carries the fix commit — matches `gh pr view 2990 --json headRefOid` cited above.

## Why

derived: `git show 46864b69:spawn.py` (lines 4905-4906, 5079-5081) and `git show 46864b69 -- on-the-record/monitors/poll_heartbeat_delta.py on-the-record/monitors/test_poll_heartbeat.py lifecycle.py` — both re-read this session, same sources cited under "What was done" above.

Re-verification approach: reproduce from primary sources (the actual commit diff, the actual caller chain, my own fresh worktree test runs) rather than reading PR #2999/#3000/#3005's prose and accepting their conclusions. Finding 1 required checking the fixture specifically because a self-hardcoding fixture was named as the root cause of the original miss — checking only "do tests pass" would have repeated exactly that miss if the fixture fix were cosmetic rather than a real switch to the live `diagnose_health()`. Finding 2 required tracing the actual line order in `spawn.py` (not just reading the docstring's claim about it) because the argument's soundness depends entirely on `proc.wait()` and `roster_remove()` genuinely preceding `_self_trigger_respawn()` in execution order, not just in prose.

## What did not work

None.

## Upstream basis

canonical: `gh pr view 2990 --json headRefOid -q .headRefOid` — result: `46864b697e40dab9d19a16d8e1296a0a4eab8f8d`; `gh pr view 2999 --json state,title`, `gh pr view 3000 --json state,title` — both read this session (see "What was done" above for citations of their content).

- `docs/issue-2969/reports/silent-failure-audit-daadb0ad.md` — untracked on this branch; lives on branch `issue-2969/silent-failure-audit-daadb0ad` (PR #3005) at commit `fb309f65f29e0ff6593ca9532ccec24cba06c9bb`, read via `git show origin/issue-2969/silent-failure-audit-daadb0ad:docs/issue-2969/reports/silent-failure-audit-daadb0ad.md` — the fix-round record whose two finding-resolutions this record independently re-derives and confirms.
- commit `46864b697e40dab9d19a16d8e1296a0a4eab8f8d` (PR #2990's head) — the actual code and test changes verified.
- PR #2999 (`issue-2969/adversarial-review-4b49fcf9`) and PR #3000 (`issue-2969/adversarial-review-07fbd75c`) — the two prior independent verifications whose `verdict: fail` findings this record checks were actually resolved, not just claimed resolved.

## Open findings

canonical: all four acceptance checks and the full `test_poll_heartbeat.py` suite re-run this session at commit `46864b69` (see "What was done" → Finding 1 for the exact commands and output).

None. Both findings from PR #2999/#3000 are independently confirmed resolved: finding 1 by a code fix verified this session to actually restore suppression (regression test read line-by-line, not just executed) plus a fixture verified to derive its state from the real `diagnose_health()` (not re-hardcoded); finding 2 by an ungated-path argument whose three factual grounds each check out against the code's actual execution order (cited above with file:line and matching code fences), and whose overarching safety conclusion (no live session can be killed on a single observation via this path) holds under adversarial reading.

## Next steps

None — loop_state: landed.
