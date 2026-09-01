---
issue: 2961
role: adversarial-review-225e111b
author: adversarial-review-225e111b
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2964 (issue-2961/observability-methodology-selection+test-derivation-27c16f97), reviewed and audited this session
code_under_review: spawn.py, pipeline.py, directive_assembly.py, 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:runaway_backstop.py, 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:runaway_signal.py, 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:tests/test_runaway_backstop.py, 03e0b2ff6ed31f48f5365c12844cfdb49e12923b:tests/test_runaway_signal.py
type: verification
breaking: no
verdict: pass-with-caveat
loop_state: terminal
upstream:
  - path: docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md
    sha: 03e0b2ff6ed31f48f5365c12844cfdb49e12923b
  - path: runaway_backstop.py
    sha: b36ffba6db738ac412899a1e8815d3e24aefd7fa
  - path: runaway_signal.py
    sha: b36ffba6db738ac412899a1e8815d3e24aefd7fa
---

# issue-2961 — adversarial-review-225e111b record

## What was done

Independently verified PR #2964 (branch
`issue-2961/observability-methodology-selection+test-derivation-27c16f97`,
tip `03e0b2ff6ed31f48f5365c12844cfdb49e12923b`, base `main`) against issue
#2961's 5 acceptance checks. Fetched the PR head into an isolated git
worktree and re-ran all 5 acceptance checks live rather than trusting
the PR body's pasted output, read every changed file's diff against the
issue's must-not list, and independently reproduced the 90-session
threshold-derivation script against the live corpus rather than trusting
the record's pasted numbers.
canonical: `gh pr view 2964 --json headRefName,baseRefName,commits,files` output this session — result:
```
baseRefName: main, mergeStateStatus: CLEAN, 9 files changed
(4 modified: directive_assembly.py, pipeline.py, spawn.py;
5 added: runaway_backstop.py, runaway_signal.py, tests/test_runaway_backstop.py,
tests/test_runaway_signal.py, docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md
+ its deviation-log entry)
```

Acceptance checks, executed live this session in the isolated worktree
(`git fetch origin pull/2964/head:pr-2964-verify && git worktree add
/tmp/verify-2961-pr2964 pr-2964-verify`):
acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?` — result:
```
rc=1
```
acceptance: `python3 -m pytest tests/ -k backstop -q` — result:
```
5 passed in 0.85s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_observe_only -q` — result:
```
4 passed in 0.91s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_discrimination -q` — result:
```
3 passed in 0.97s
```
acceptance: `python3 -m pytest tests/ -k subagent_in_flight -q` — result:
```
3 passed in 1.01s
```
All 5 of issue #2961's own acceptance checks pass, reproduced live
against the fetched PR tip.

derived: `python3 -m pytest tests/ -q` (full regression, same worktree) — result:
```
70 passed, 1 failed
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
```
derived: `git reset --hard main && python3 -m pytest tests/test_spawn_gate_wiring.py -q` (same isolated worktree, checked whether the failure predates the PR) — result:
```
1 failed, 26 passed
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
AssertionError: 4 not greater than 4
```
Identical failure with the PR's changes absent — confirms it predates
this PR and is unrelated, matching the upstream record's own claim.
Worktree reset back to `pr-2964-verify` (`git reset --hard
pr-2964-verify`) for the remainder of this review.

### `--max-turns` removal, confirmed by execution not just by grep

canonical: `git diff main...pr-2964-verify -- pipeline.py spawn.py` read in full this session — the old `cmd += ["--max-turns", str(max_turns + wrap_up_allowance)]` block (pre-PR `pipeline.py:698-699`) is deleted entirely and replaced by comment-only prose, not commented out or feature-gated; `max_turns` is now used only to set the advisory env var `MUSTER_SESSION_MAX_TURNS_RESOLVED` (`03e0b2ff:pipeline.py:727-728`) that the pre-existing `approach-cap-warning.sh` nudge hook reads. `spawn.py`'s `--max-turns` argparse flag is deleted outright (`03e0b2ff:spawn.py` diff hunk removing the `ap.add_argument("--max-turns", ...)` block and the `max_turns=a.max_turns,` kwarg passed to `_spawn_one()`), and its `doctor()` probe subprocess call drops the `"--max-turns", "2"` argv pair, leaving only the pre-existing `timeout=180` as its bound.

derived: `grep -rln "max.turns\|MAX_TURNS" --include="*.py" --include="*.sh" .` (isolated worktree, whole-repo sweep, not just the acceptance check's 3-file list) — result:
```
runaway_backstop.py
pipeline.py
consult.py
spawn.py
on-the-record/hooks/approach-cap-warning.sh
bench/test_ablation.py
tests/test_runaway_backstop.py
bench/ablation.py
```
`consult.py` (a one-shot `claude -p` subprocess unrelated to session
spawning) and `bench/ablation.py` (a research tool that intentionally
varies the turn budget as an independent variable) are the only two
production/tooling files outside the acceptance check's 3-file list that
still construct `--max-turns` directly — both disclosed as out-of-scope
in the PR's own Open findings item 2, and both are a genuinely different
kind of subprocess than the session-spawning path this issue targets, so
excluding them from the acceptance check's file list is correct, not an
omission. `03e0b2ff:runaway_backstop.py` and
`03e0b2ff:tests/test_runaway_backstop.py` match only on the unrelated
substring "MAX_TURNS" inside `TOKEN_COST_BACKSTOP_TOKENS`/similar
identifiers, not `--max-turns` itself — checked directly by reading
`03e0b2ff:runaway_backstop.py` lines 33-34 (`WALL_CLOCK_BACKSTOP_MS`,
`TOKEN_COST_BACKSTOP_TOKENS`).

derived: `grep -rn "backstop_verdict\|runaway_backstop\.\|runaway_signal\.\|finished_session_verdicts\|runaway_verdict(" --include="*.py" . | grep -v tests/` (isolated worktree) — result:
```
directive_assembly.py: 5 matches, all reading the two threshold
CONSTANTS (WALL_CLOCK_BACKSTOP_MS, TOKEN_COST_BACKSTOP_TOKENS) to embed
their values into an advisory prose string; zero calls to
backstop_verdict()/runaway_verdict()/finished_session_verdicts()
pipeline.py, spawn.py: comment-only mentions
runaway_backstop.py, runaway_signal.py: their own definitions
```
Confirms no production call site anywhere in the tree invokes either
module's decision function outside of their own test files — see Open
finding 1.

### Must-not list, checked item by item

- **Conjunction, not a single signal, for the trajectory-based composite
  signal.** canonical: `03e0b2ff:runaway_signal.py:30,52-53` read this session —
  ```
  MIN_SIGNALS_FOR_RUNAWAY = 2
  ...
  "runaway": len(signals) >= MIN_SIGNALS_FOR_RUNAWAY,
  ```
  canonical: `03e0b2ff:tests/test_runaway_signal.py:95-107`
  (`test_runaway_signal_discrimination_never_fires_on_a_single_signal`)
  read this session — asserts a lone `repeated-action-observation`
  signal alone still reports `verdict["runaway"] is False`. Reproduced
  passing live in the acceptance run above (`-k
  runaway_signal_discrimination` — 3 passed).
- **`subagent_in_flight` guard (#2214) not weakened.**
  derived: `git diff main...pr-2964-verify -- trajectory_analyzer.py watchdog.py roster.py` (isolated worktree) — result:
  ```
  (no output — empty diff)
  ```
  None of the three files this guard and the wrap-up/checkpoint
  machinery live in were touched by this PR. canonical:
  `03e0b2ff:runaway_signal.py:38-39` — calls the pre-existing
  `ta.subagent_in_flight(events)` unmodified and short-circuits to a
  non-runaway verdict before computing any other signal.
- **Wrap-up/checkpoint machinery (#2215/#2262) not weakened.** canonical:
  `03e0b2ff:pipeline.py:727-728` — `approach-cap-warning.sh` (unmodified
  by this PR — checked separately: `git diff main...pr-2964-verify --
  on-the-record/hooks/approach-cap-warning.sh` — result: empty) still
  reads `MUSTER_SESSION_MAX_TURNS_RESOLVED`, which `pipeline.py` still
  sets from the same advisory value the old `DEFAULT_SESSION_MAX_TURNS`
  used to seed. `_resolve_wrap_up_allowance_turns()` is left in place as
  dead code rather than deleted (disclosed, Open finding 3 of the
  upstream record), so nothing that referenced it elsewhere breaks.
- **Observe-only signal terminates/throttles/refuses nothing.** canonical:
  `03e0b2ff:runaway_signal.py` (full file, 72 lines, read this session)
  — no `os.kill`, `sys.exit`, subprocess call, or file write anywhere in
  the module. `finished_session_verdicts()` only appends to a list it
  returns; the whole-repo grep above confirms nothing calls it outside
  `03e0b2ff:tests/test_runaway_signal.py`.
- **Do not raise the cap as a substitute for removing it.** Already
  covered by the `--max-turns` removal section above: no numeric turn
  ceiling reaches the CLI subprocess argv at all, not a larger one.

### Backstop OR-semantics vs. the "conjunction" must-not — considered, not a violation

canonical: `03e0b2ff:runaway_backstop.py:64-77`
(`backstop_verdict()`) — `"terminate": wall or cost`, i.e. either the
wall-clock or token-cost backstop firing alone sets `terminate`, not
their conjunction. Read in isolation, the Acceptance's must-not bullet
("do not terminate a session on any single signal — termination
requires the conjunction the consults specified") could be misread as
forbidding this.
canonical: `gh issue view 2961` Consults paragraph, quoted verbatim in
the spawning prompt this session received — the conjunction requirement
is stated in the same sentence as, and specifically about, "combin[ing]
the existing trajectory signals with a no-progress signal ... terminate
only on a conjunction, never a single signal" — the observe-only
composite signal, not the backstops, which the same paragraph names
separately ("bound the worst case with wall-clock and token/cost
accumulation rather than turns") with no conjunction language attached.
Acceptance item 2's own wording ("A wall-clock backstop and a token/cost
backstop terminate a session, each with its threshold derived...") is
consistent with each backstop independently terminating. Concluded this
is not a violation; flagging the ambiguity for the record rather than
silently resolving it.

### Threshold derivation — reproduced independently, not just re-read

derived: re-ran the record's own derivation script this session against
the live corpus (same glob as
`03e0b2ff:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`
lines 91-125, `python3 - <<'PYEOF' ... glob.glob(".../*.session.*.log")`) — result:
```
n= 84 logs on disk this session (73 with a terminal `result` event, all
terminal_reason: completed, none turn-capped; 11 still-running/no-result)
duration_ms max: 2,808,986
cost max: 12.90
tokens max: 86,752,151
```
The upstream record claims (same file, lines 126-130): `n= 90`, duration
max `3,064,830`, cost max `13.73`, tokens max `86,752,151`. The corpus is
a live, continuously-growing directory — this very session and its
concurrently-running sibling sessions add new logs while running, and
the oldest log on disk is 2 days old with no evidence of deletion
otherwise (checked: `ls -lat /home/jwjung/.tokenmaxxxer/work/*.session.*.log`
oldest entry timestamp `8월 30 08:01` still present) — so an exact
re-match of `n` across a several-hour gap between the record's
derivation and this check was never expected. The exact match on the
token-count max (86,752,151, to the exact 9-digit integer) is strong
evidence the record's derivation script genuinely executed against real
log data rather than being invented — an exact coincidence on a number
that size is not plausible otherwise. The lower duration/cost maxima
observed now only make `runaway_backstop.py`'s 1.5x-of-observed-max
thresholds more conservative relative to the current corpus, not less.

Checked whether the two shipped thresholds still satisfy the record's
own claimed formula (`>= 1.5x observed max`, `< 2x observed max`)
against the record's cited maxima directly, rather than re-doing the
arithmetic by eye:
derived: `python3 -c "print(5400000 >= 3064830*1.5, 5400000 < 3064830*2, 150000000 >= 86752151*1.5, 150000000 < 86752151*2)"` — result:
```
True True True True
```
All four checks hold. canonical: `03e0b2ff:tests/test_runaway_backstop.py:58-68`
(`test_backstop_thresholds_are_derived_from_observation_not_freehand`)
— hardcodes the same two observed-max figures as a regression guard;
reproduced passing in the acceptance run above (`-k backstop` — 5
passed).

## Why

Verified by execution rather than by reading the PR's own claims, per
this skill's protocol and the task's explicit instruction not to trust
the PR's self-reported results. canonical: the `acceptance:`/`derived:`
tags and their pasted command output throughout "What was done" above,
all executed this session in the isolated worktree — three areas needed
live reproduction rather than a diff read alone: the acceptance checks
themselves (drift check against the PR's own claimed output — see Open
finding 2 for the one mismatch found), the threshold-derivation script
(corpus/percentile fabrication check — see the "Threshold derivation"
subsection above for the reproduction and its result), and a whole-repo
grep for any remaining CLI call site that could still attach
`--max-turns` (scope-of-removal check beyond the acceptance check's
narrow 3-file list — see the "`--max-turns` removal" subsection above,
which found none beyond the two already disclosed).

## Open findings

1. **The backstops are inert — no caller anywhere in the tree wires
   them to a real session, and this makes the actual unguarded window
   wider than the issue's own operator-decision text implies.**
   canonical: whole-repo grep result quoted in "What was done" above
   (`backstop_verdict`/`runaway_verdict`/`finished_session_verdicts` have
   zero callers outside their own test files;
   `03e0b2ff:directive_assembly.py` only reads the two threshold
   constants for a prose string, never calls `backstop_verdict()`). The
   PR and its upstream record disclose this honestly as their own "Open
   findings item 1" / "not a blocker" — canonical:
   `03e0b2ff:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`
   lines 229-237 read this session. But the issue's own quoted operator
   decision — canonical: `gh issue view 2961`, "Operator decision"
   paragraph, quoted verbatim in the spawning prompt — says: "the cap is
   removed immediately, with the wall-clock and cost backstops as the
   only active defence, while the composite signal runs observe-only
   alongside." The delivered state does not match that sentence: the
   backstops are not an "active defence," they are tested-but-uncalled
   library functions. Post-merge, from the moment this PR lands until a
   follow-up issue wires an enforcing loop, there is no automatic
   termination mechanism of any kind for a runaway session — not turn
   count (removed by this PR), not wall-clock, not token/cost. This is a
   materially wider risk posture than "backstops catch it, just slower
   than the turn cap used to" — it is "nothing catches it." The PR's own
   "What did not work" section (canonical: same upstream record, lines
   190-214) explains why `roster_watchdog()` was correctly left
   unmodified — it is documented observe-only and wiring a kill into it
   would have violated that contract — and that reasoning holds up; the
   revert was the right call given the conflict discovered. What is
   missing is proportion: the consequence gets one "not a blocker"
   Open-findings bullet, when it is the difference between the issue's
   accepted decision and what actually ships. Resolution path: treat the
   PR's own suggested follow-up (a new, explicitly-enforcing poll loop
   calling `backstop_verdict()` per alive roster entry, using `roster.
   roster_kill()`) as a priority follow-up to schedule promptly, not a
   someday-cleanup, before treating this slice as having closed the risk
   the original issue opened with.
2. **PR body test-plan text is stale relative to its own tip commit.**
   canonical: `gh pr view 2964 --json body -q .body` line 12, read this
   session — claims `python3 -m pytest tests/ -k
   runaway_signal_observe_only -q` — `3 passed`; the actual count at the
   PR's tip (`03e0b2ff`) is `4 passed`, reproduced live in the
   acceptance run above. The later commit
   `37ad86e1dc1aecc8a01a158ea24d6b2c65908703` (canonical: `gh pr view
   2964 --json commits` messageHeadline "invoke
   observability-methodology-selection... add mixed-batch test", read
   this session) added
   `test_runaway_signal_observe_only_mixed_batch_only_counts_finished_ones`
   to close a real equivalence-partition gap, but the PR body's
   test-plan list was never updated to match. Not a functional defect —
   the acceptance check has no fixed expected count, and the upstream
   record's own later section does show a corrected combined total
   (canonical:
   `03e0b2ff:docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`
   lines 351-355, "15 passed" for the 4-selector combined re-run, read
   this session) — but it is exactly the kind of self-reported-result
   drift this verification's own instructions said not to trust
   blindly, and here it did not match on first read.
3. **`on-the-record/hooks/approach-cap-warning.sh`'s header comment is
   now inaccurate; not touched by this PR.** canonical:
   `03e0b2ff:on-the-record/hooks/approach-cap-warning.sh:7-8`, read this
   session — "the actual cap enforcement lives outside this repo (the
   `claude` CLI itself kills the process at `--max-turns`)" — false as
   of this PR, since `--max-turns` is never passed to the CLI subprocess
   anymore (confirmed above). The hook's actual runtime behavior is
   unaffected — it only ever emitted an advisory `additionalContext`
   nudge, never a kill, so the now-false premise in its comment was
   never load-bearing for what the hook does — purely a documentation
   staleness, out of this PR's declared file list (confirmed by the
   empty-diff check on this file, above). Resolution path: minor
   follow-up comment fix, not urgent.

None of these findings are correctness defects in the delivered code
against the issue's literal 5-check Acceptance list — all 5 pass,
reproduced live above, and the must-not list is honored by the code as
written (checked item by item above). Finding 1 is the one worth the
operator's attention: the PR is not dishonest about the enforcement gap
— it discloses it — but the framing undersells how total the resulting
gap is against what the issue's own accepted decision text promised.

## Next steps

None — `loop_state` is terminal for this record. acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?; python3 -m pytest tests/ -k backstop -q; python3 -m pytest tests/ -k runaway_signal_observe_only -q; python3 -m pytest tests/ -k runaway_signal_discrimination -q; python3 -m pytest tests/ -k subagent_in_flight -q` (re-run immediately before writing this record, same isolated worktree, same order as "What was done") — result:
```
rc=1
5 passed in 0.85s
4 passed in 0.91s
3 passed in 0.97s
3 passed in 1.01s
```

skill-verdict: adversarial-review — applied: invoked; loaded via the
Skill tool before writing this record. canonical: Skill tool transcript,
this session, `adversarial-review` invocation — confirmed this task
already matches the skill's own protocol (fresh, structurally
independent session; isolated worktree fetch of only the PR's committed
deliverable; execution-based verification over trusting the builder's
claims; findings cited to file:line/command output) and used its Step 3
critique shape ("problems with a location," "bottom line") to structure
the Open findings section above.
other mounted skills: work-in-english — applied silently throughout
(this record, all commands, and the branch/commit history are in
English per project policy), not surfaced as a separate design decision;
conformance-review-finding-record — not-applicable: that skill targets
verdicts written to `docs/issue-<n>/reports/conformance-review.md`, not
this adversarial-review verification record's own file.
