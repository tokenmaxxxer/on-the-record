---
issue: 2961
role: adversarial-review-fb462020
author: adversarial-review-fb462020
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2964's deliverable (author: observability-methodology-selection+test-derivation-27c16f97) -- see docs/handbooks/observer-verification.md
loop_state: terminal
upstream:
  - path: docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md
    sha: 03e0b2ff6ed31f48f5365c12844cfdb49e12923b
---

# issue-2961 — adversarial-review-fb462020 record

## What was done

Independently verified PR #2964 (`issue-2961/observability-methodology-selection+test-derivation-27c16f97`,
head `03e0b2ff6ed31f48f5365c12844cfdb49e12923b`, base `main`) against
issue #2961's acceptance checks and "must not" list, without trusting the
PR's own claimed results — fetched the head commit into this repo
(`git fetch origin pull/2964/head`, commit object confirmed present) and
re-ran everything myself.
canonical: `gh pr view 2964 --json baseRefName,headRefOid,state` — result: `{"baseRefName":"main","headRefOid":"03e0b2ff6ed31f48f5365c12844cfdb49e12923b","state":"OPEN"}`

**Acceptance checks — re-run at the PR head, all pass as literally
specified:**
derived: acceptance checks re-executed against a worktree checked out at `03e0b2ff6ed31f48f5365c12844cfdb49e12923b` — result:
```
$ grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py
(no output, exit 1)

$ python3 -m pytest tests/ -k backstop -q
.....                                                                    [100%]
5 passed in 0.90s

$ python3 -m pytest tests/ -k runaway_signal_observe_only -q
....                                                                     [100%]
4 passed in 0.83s

$ python3 -m pytest tests/ -k runaway_signal_discrimination -q
...                                                                      [100%]
3 passed in 0.84s

$ python3 -m pytest tests/ -k subagent_in_flight -q
...                                                                      [100%]
3 passed in 0.85s
```
No SKIPPED lines in any run.

**`--max-turns` is genuinely removed from the production spawn path**,
not renamed or raised:
derived: `git show 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:pipeline.py | sed -n '680,690p'` — result:
```
    # Issue #2961: the CLI's own turn-count cap flag is never attached —
    # turn count no longer terminates a session (Acceptance: "No session
    # is terminated on turn count"). The resolved `max_turns` value below
    # still feeds the soft convergence nudge (env vars further down); it
    # no longer reaches the CLI's argv. The actual worst-case bound is
    # now `runaway_backstop.py`'s wall-clock/token backstops, enforced by
    # the watchdog poll loop, not by a flag on this subprocess.
```
`spawn.py`'s `doctor()` probe subprocess and its `--max-turns` CLI
argparse flag are both deleted (confirmed by the same-commit `git show`
of `spawn.py`, no `--max-turns` construction remains); `_spawn_one`'s
`max_turns` parameter has no CLI-driven caller left.
`DEFAULT_SESSION_MAX_TURNS = 200` was renamed to
`DEFAULT_SESSION_TURN_GUIDANCE = 200` (same value) but now only seeds
advisory env vars for the wrap-up hook, never CLI argv.
derived: `git grep -n "\-\-max-turns" 03e0b2ff6ed31f48f5365c12844cfdb49e12923b -- '*.py'` — result: only `consult.py:1567` (a 6-turn-capped utility probe, unrelated to session spawning) and `bench/ablation.py` (a turn-budget ablation benchmarking tool that intentionally varies turn count) — both outside the production spawn path (`spawn.py`/`pipeline.py`), and both disclosed as deliberately out-of-scope in the PR's own record's Open finding 2 (`03e0b2ff6ed31f48f5365c12844cfdb49e12923b:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`, "Open findings" §2).

**"Must not" list audit** (full diff read against merge-base `5c0cc59996816bb53a2a86047489b2b7c4e45a7a`, not just the 3 acceptance-check files):
- No termination on a single trajectory signal:
  derived: `git show 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:runaway_signal.py | sed -n '25,56p'` — result: `MIN_SIGNALS_FOR_RUNAWAY = 2`; `runaway_verdict()` sets `"runaway": len(signals) >= MIN_SIGNALS_FOR_RUNAWAY` over 5 possible signals. Satisfies. (`runaway_backstop.py`'s two backstops are each independently sufficient by explicit design — "either alone is sufficient", same file's module docstring — but see the caller-count finding below: this is moot in practice since nothing calls it.)
- Turn cap not simply raised: same numeric value (200) confirmed by the rename shown above; its function changed from hard CLI ceiling to advisory-only env var, not raised. Satisfies.
- `subagent_in_flight` guard (#2214):
  derived: `git diff 5c0cc59996816bb53a2a86047489b2b7c4e45a7a..03e0b2ff6ed31f48f5365c12844cfdb49e12923b -- trajectory_analyzer.py` — result: empty (zero diff to the file the guard lives in). `runaway_signal.py:38-40` (`git show` above) calls `ta.subagent_in_flight(events)` as a hard short-circuit before computing any other signal. Satisfies.
- Wrap-up/checkpoint machinery (#2215/#2262):
  derived: `git diff 5c0cc59996816bb53a2a86047489b2b7c4e45a7a..03e0b2ff6ed31f48f5365c12844cfdb49e12923b -- checkpoint.py on-the-record/hooks/approach-cap-warning.sh` — result: empty (zero diff to both). Functionally satisfies — both still read the renamed `DEFAULT_SESSION_TURN_GUIDANCE`-derived env vars. Minor drift: `approach-cap-warning.sh`'s own header comment ("the `claude` CLI itself kills the process at `--max-turns`") is now stale/false post-PR and was not updated — not a functional weakening, but inaccurate documentation left in place.
- Observe-only signal terminates/throttles/refuses nothing:
  derived: `git show 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:runaway_signal.py | sed -n '1,24p'` — result: module docstring states "Never terminates, throttles, or refuses anything... Nothing in this module calls `os.kill`, raises, or has any other side effect." Full-file read confirms no process control, no lifecycle/roster imports. `git grep -n "runaway_verdict\|finished_session_verdicts" 03e0b2ff6ed31f48f5365c12844cfdb49e12923b -- '*.py'` shows callers only inside `runaway_signal.py` itself and `03e0b2ff6ed31f48f5365c12844cfdb49e12923b:tests/test_runaway_signal.py` (commit-pinned; not present on this session's own branch) — zero production callers, so it cannot enforce anything even indirectly. Satisfies.

## Why

The task required not trusting the PR's own claimed results. Re-running
the exact acceptance commands at the actual PR head, and independently
re-executing the record's own threshold-derivation script rather than
reading its pasted output as given, were the only ways to surface the
two findings below — neither is visible from the diff or record text
alone without re-running things.

## Upstream basis

canonical: `03e0b2ff6ed31f48f5365c12844cfdb49e12923b:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md` — PR #2964's own deliverable record (commit-pinned citation; not present in this session's working-tree branch, fetched via `git fetch origin pull/2964/head`). Its "Threshold derivation" subsection and "Open findings" item 1 are the two claims independently re-checked and disputed/confirmed below.

## Open findings

1. **The shipped result does not bound runaway sessions at all — and a
   landed code comment falsely claims it does.**
   derived: `git grep -n "backstop_verdict" 03e0b2ff6ed31f48f5365c12844cfdb49e12923b -- '*.py'` — result: only its own definition (`runaway_backstop.py:64`) and its own test file; zero production callers.
   derived: `git show 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:watchdog.py | grep -n "runaway\|backstop"` — result: no output (zero references in the 2,066-line file the PR's own `pipeline.py:687` comment names as the enforcement site — quoted in "What was done" above: "enforced by the watchdog poll loop"). That comment is false as landed: nothing enforces the backstop. The PR's own record is honest about the gap elsewhere — its "What did not work" section
   (`03e0b2ff6ed31f48f5365c12844cfdb49e12923b:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`)
   describes a `roster_watchdog()` enforcement-wiring attempt that was
   written, then deliberately reverted after finding `watchdog.py`'s own
   docstrings document it as pure-observation
   (`grep -n "observe-only" watchdog.py` cited in that same section,
   confirming the revert with a zero-diff `git diff --stat watchdog.py`
   check) — and "Open findings" item 1 of that same record states
   plainly: "No live enforcement caller exists yet." But the in-code
   comment at `pipeline.py:687` overstates the current state to any
   reader who trusts the code over the record. Net effect for a real
   session today: the 200-turn CLI cap (the previous hard worst-case
   bound) is gone (confirmed above), and nothing else in this repo
   automatically terminates a live runaway session — not turn count, not
   the backstop module (built, unit-tested, uncalled), not the watchdog
   (its only automatic action on a roster entry, `_auto_respawn_check()`,
   acts solely on entries whose `session_end_verdict()` already reads
   `crashed` — i.e. already-dead processes, never a still-running one).
   The only remaining stop is a manual operator `spawn.py kill`, or
   whatever exists entirely outside this repository (unverified from
   inside it). This directly undercuts the issue's stated goal ("bound
   runaways by cost and trajectory signal, not by counting turns") — the
   bounding half is inactive code at this head commit. This gap is a
   knowing, disclosed operator tradeoff per the PR record's own "Why"
   section (quoting the issue text's acceptance of "the resulting
   unguarded window because the failure this fixes is recurring now"),
   not a concealed one — but the false `pipeline.py:687` comment is not
   part of that disclosure and should be fixed or removed regardless of
   the wiring decision; the wiring itself the PR's own record already
   routes to a named follow-up issue.

2. **The threshold-derivation corpus is not reproducible, and the
   record's own rounding claim does not hold up arithmetically.**
   The record's "90-session corpus" is a glob
   (`$MUSTER_WORKSPACE_ROOT/*.session.*.log`) over a live, shared,
   actively-mutating scratch directory — not a versioned dataset,
   manifest, or list of named session IDs.
   derived: the record's own derivation script, re-executed verbatim by this session against the same glob path, moments after the PR's claimed run — result:
   ```
   n= 74
   duration_ms p50/p95/p99/max: 998882.0 1847623.1499999992 2446887.019999998 2808986
   cost p50/p95/p99/max: 2.7496885 7.943430659999996 11.42648789999999 12.902438399999998
   tokens p50/p95/p99/max: 13738195.5 44209574.64999997 79984849.51999997 86752151
   ```
   Not the claimed `n=90` (74 here; a second independent re-run by a
   delegated verification worker, run slightly earlier in the same
   session, got `n=73` with slightly different figures still) — with
   materially different `p50/p95/p99/max` for duration and cost (e.g.
   observed max duration 2,808,986ms here vs. the record's claimed
   3,064,830ms). Only the max-tokens figure (86,752,151) happened to
   survive across all three runs, which is incidental, not evidence of
   stability. The record presents `n=90` as a settled measurement
   without disclosing that the underlying directory is ephemeral and
   shared across unrelated concurrent sessions (this verification
   session's own logs were being written into that same directory while
   it ran). Separately, the record's stated rounding methodology is
   internally inconsistent:
   derived: `python3 -c "print(86752151*1.5); print(150_000_000 % 100_000_000)"` — result:
   ```
   130128226.5
   50000000
   ```
   The record claims 150,000,000 is "the first clean round-hundred-million
   figure above" 130,128,227. `150,000,000 % 100,000,000 == 50,000,000
   != 0`, so 150,000,000 is not a multiple of 100,000,000 at all — it is
   not a "round-hundred-million" figure by the plain meaning of that
   phrase (the first true one above 130,128,227 would be 200,000,000).
   Either the stated formula is wrong, or the shipped number was chosen
   by some other means and the formula written to rationalize it after
   the fact. This bears directly on the issue's own requirement that
   thresholds be "derived... not chosen freehand": as documented, the
   derivation is neither reproducible nor internally consistent, so the
   record does not currently substantiate the "derived from recorded
   observation" claim it makes for the number it shipped. (The
   wall-clock side is comparatively defensible: 4,597,245ms → 5,400,000ms
   [90min] is the first round multiple-of-30-minutes above that product,
   a plausible if unstated reading of "clean round-minute figure".)
   Resolution path: pin the corpus to a committed, immutable dataset (or
   explicitly caveat it as a non-reproducible snapshot), and correct
   either the stated rounding formula or the shipped token threshold so
   one actually follows from the other.

## Next steps

None — this record is terminal. Both open findings above are resolution
items for the PR itself (or its named follow-up issue), not further work
for this verification.

skill-verdict: adversarial-review — applied: invoked; used as the framing for treating PR #2964's own claimed acceptance results and derivation numbers as untrusted, re-deriving each independently (worktree re-run of all 5 acceptance checks, re-execution of the threshold-derivation script, direct git-show/grep citation of every "must not" list item) rather than reading the PR's report at face value
skill-verdict: work-in-english — applied: invoked; this record and all repo-facing content written in English, final summary to the user delivered in Korean
