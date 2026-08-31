---
issue: 2906
role: adversarial-review-30a89443
author: adversarial-review-30a89443
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2913 (issue-2906/silent-failure-audit-c7e19e1e, commits 290141e9, 5624bcb0)
loop_state: landed
type: verification
breaking: false
verdict: mechanism-correct-measurement-overstated-liveness-gap-undisclosed
upstream:
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: 290141e9fec95d8187e5a8a3ad7cc10954e4ccaa
  - path: docs/issue-2906/reports/silent-failure-audit-c7e19e1e.md (untracked on this branch; lives only on PR branch issue-2906/silent-failure-audit-c7e19e1e, same commit as the fix; read via `git worktree add /tmp/pr2913-review pr-2913`)
    sha: 290141e9fec95d8187e5a8a3ad7cc10954e4ccaa
---

# issue-2906 — adversarial-review-30a89443 record

## What was done

Independently re-derived every checkable claim in PR #2913 (branch
`issue-2906/silent-failure-audit-c7e19e1e`, commits 290141e9 + 5624bcb0)
against a `git worktree add` checkout of the PR head and a separate
worktree of `origin/main` (`e516a433`/`109e38c5` lineage), not by reading
the PR's own record and restating it. canonical: `gh pr view 2913
--json title,body,commits,files` (fetched this turn) plus a direct
`git worktree add /tmp/pr2913-review pr-2913` checkout of the PR head,
read file-by-file below.

**1. Mechanism, read at the comparison layer** — canonical:
`on-the-record/monitors/poll_heartbeat_delta.py` diff (lines 43-63,
185-197 of the PR's patch, `git diff main...pr-2913 -- on-the-record/
monitors/poll_heartbeat_delta.py`, this turn). For a `poll-report:`
keyed line, when the current state token is `HEALTHY`,
`POLL_REPORT_ACTIVITY_STRIP_RE` strips only the trailing `; 마지막
도구 호출: ...` / `; 도구 호출 (로그|기록) 없음` clause from both sides
before comparing; every other state token falls to the pre-existing
`changed = prev_line != line` full-line compare, untouched. Traced the
HEALTHY detail's construction in `watchdog.py:501-505` (`f"{workspace_
summary}; {activity_summary}"`) — the strip regex is anchored at `$`
and only removes the trailing activity clause, so `workspace_summary`
(the #2904 dirty-file/record-started summary) always survives into the
compared string. Matches the PR's claim.

**2. Boundary and all four live transitions, constructed myself** — not
reading the PR's own tests first. Wrote a standalone driver
(`/tmp/pr2913-review/scratch_verify.py`, scratch, not committed) that
feeds hand-built `[poll-report]` lines through the PR's actual
`poll_heartbeat_delta.py` and asserts emit/suppress per tick. All 10
constructed scenarios matched expectation exactly — derived:
`python3 scratch_verify.py`, this turn:
```
[OK] A1 first tick HEALTHY (baseline, first_tick forces emit)
[OK] A2/A3 HEALTHY->HEALTHY, only tool/ts changed (suppressed)
[OK] B HEALTHY->HEALTHY but workspace file-set changed (notified)
[OK] B2 HEALTHY->HEALTHY same file-set again (suppressed)
[OK] C HEALTHY->STALLED (notified)
[OK] D STALLED->STALLED unchanged, ALWAYS_RE forces emit every tick (notified)
[OK] E STALLED->HEALTHY recovery (notified); E2 next HEALTHY tick (suppressed)
[OK] F HEALTHY->DEAD-ERRORED (notified); F2 DEAD-ERRORED->DEAD-ERRORED unchanged (suppressed, pre-existing behavior)
[OK] G ->COMPLETED (notified); G2 COMPLETED->COMPLETED unchanged, ALWAYS_RE forces emit (notified)
```
Ran the PR's own test suite against the PR worktree — derived:
`python3 on-the-record/monitors/test_poll_heartbeat.py`, this turn,
result: `33/33 passed` (reproduced independently, not copied from the
PR's record).

**Anomaly-tag enumeration**: `watchdog.py`'s `diagnose_health()` states
are `HEALTHY, STALLED, STALLED-HEARTBEAT-ONLY, STALLED-FLAT-PROGRESS,
DEADLOCKED`, plus dead-entry labels `DEAD-REMOTE-STATE-UNKNOWN,
DEAD-UNRECOVERED-COMMITS, DEAD-ERRORED, COMPLETED` (watchdog.py:445-505,
1834-1875, read directly). Of these, only `HEALTHY` enters the new
branch; every other state (including the three `DEAD-*` labels that
`ALWAYS_RE` does *not* match by substring) falls through to the
unmodified `else` branch. Every other watchdog tag this issue named —
`[resume]`, `[orphaned]`, `[watchdog-crash]`, `[reconcile-poll-
disagreement]` (the #2874 disagreement line), `[checkpoint]` — is keyed
and compared by a completely different code path (`TAG_RE`/
`FIXED_TAG_RE`, not the new `poll-report:` branch) and is provably
untouched by this diff by construction, not by re-testing each one.

**3. Retirement gate / pytest / overhead invariants, re-run myself, not
trusted from the PR body**:
- derived: `python3 gates/retirement_count.py | wc -l` on both worktrees,
  this turn — result: `1136` both trees; `diff` between the two runs'
  full output is pure line-number drift from the 116 lines this PR
  inserted earlier in `test_poll_heartbeat.py` (identical match
  *content*, confirmed by inspecting the diff hunks — every changed line
  pair is byte-identical text at a shifted line number).
- derived: `python3 -m pytest . -q` on both worktrees, this turn —
  result: `17 failed, 691 passed, 3 xfailed` (PR) vs `17 failed, 688
  passed, 3 xfailed` (main); `diff <(grep '^FAILED' pr.txt | sort)
  <(grep '^FAILED' main.txt | sort)` — result: empty, identical
  failing-test name sets, +3 new passing tests on the PR, reproduced
  independently of the PR's own pasted numbers.
- derived: 100 timed invocations of `poll_heartbeat_delta.py` on the PR
  worktree, this turn — result: `21.72 ms/tick` — same order of
  magnitude as the PR's claimed 22.18ms/tick (dominated by Python
  interpreter startup, not the two added regexes); no measurable
  regression.

**4. The measurement (87.8% / 2493), re-derived independently from the
same live transcript** (`~/.claude/projects/-home-jwjung-tokenmaxxxer/
93c239f8-561b-41f5-b69c-ae9e757b7939.jsonl` — canonical: `ls -la` +
`wc -l` on that path, this turn — result: 101,570,820 bytes / 68,479
lines; the file is still growing, since this is the live orchestrator's
own ongoing session; the PR's snapshot was 68,279 lines). Parsed
independently (a fresh Python script, not the PR's) over every
`queue-operation`/`enqueue` record's `<event>` body — derived: python
script counting `<event>`-bearing task-notifications, this turn, result:
2510 (vs the PR's 2493 — consistent with ~200 lines of transcript
growth since their snapshot). Applying the PR's *own* stated anomaly
regex verbatim reproduces their shape closely — derived: same script
with the PR's exact regex from its record, this turn, result: `301
anomaly-bearing (12.0%), 2209 routine (88.0%)` (vs their 87.8%) — the
classification code itself is reproducible and not fabricated.

**The counting method has a real gap the PR does not disclose.**
Cross-tabulating "routine" against whether the `<event>` body is
actually watchdog-shaped content at all (vs. some *other*
Monitor-tracked background command's output relayed through the
identical `<task-notification>` wrapper) — derived: python script,
`watchdog_body_re` (poll-report/watchdog/board-sweep/patrol-poll/etc
markers) vs `<summary>` text, this turn, result:
```
total event-bearing: 2510
non-watchdog, routine:  451  (18.0%)
watchdog, anomaly:      301  (12.0%)
watchdog, routine:     1758  (70.0%)
```
found 451 of 2510 event-bearing notifications (18.0%) are not
poll-heartbeat.sh watchdog ticks — they are other ad-hoc Monitor
watches the orchestrator itself set up (a spawn-session status poll
re-announcing "PS: RUNNING ... N분" every minute for `issue-284`,
pytest-tier-wait relays, a "noop" ping, "pause to let audit agents
finish" — sampled directly from the transcript, this turn). All of
these are counted as "routine, no actionable content" in the PR's
classification (none matches its anomaly regex), inflating the 87.8%
headline with noise this PR's fix cannot touch (it only edits
`poll-report:`-keyed comparisons).

**More significant**: of the 2209 routine-classified notifications, 601
(27.2% of the routine bucket) — derived: python script matching
`\[spawn-attempt\].*spawn halted` against the routine bucket's body
text, this turn, result: `601 / 2209 = 27.2%` — contain a
`[spawn-attempt] ... spawn halted pre-workspace: ...` line, e.g. "no
outcome recorded 4010s after spawn attempt (pid 3801531) — process
likely died before it could report why", or "unable to write file ...
장치에 남은 공간이 없음" (disk full), or workspace/origin-mismatch
errors (sampled directly from the transcript, this turn). These are
exactly the "spawn halts" category this review was told to check
reaches the orchestrator — and they do reach it (this PR doesn't
suppress them; `[spawn-attempt]` is in neither `TAG_RE` nor
`ALWAYS_RE`, checked directly in the diff above, so it's on the
pre-existing generic-hash-key full-line compare, unaffected by this
diff either way) — but the PR's own "actionable" classifier does not
recognize `[spawn-attempt]`/"spawn halted" as an anomaly marker (its
regex, quoted in section 4 above, has no such term), so a repeated
disk-full or died-silently spawn failure counts toward "87.8% ...
carried no actionable content." A quarter of the bucket the PR calls
noise is arguably a distinct, real operational signal the classifier
simply doesn't have a marker for — the 87.8% figure is real as counted,
but "no actionable content" is a looser judgment call than the headline
number implies, and the PR's own "Open findings" section (which does
disclose that board-sweep/accumulation-trend dominate the *remaining*
noise this fix doesn't touch) never mentions spawn-halt content or the
non-heartbeat Monitor notifications at all.

The narrower number the PR's own record *does* disclose — derived:
`docs/issue-2906/reports/silent-failure-audit-c7e19e1e.md` (untracked
on this branch, PR branch only), "Open findings" first bullet, read
this turn, states 377/2189 = 17.2% of routine notifications carry a
`[poll-report]` HEALTHY line (i.e. the actual addressable surface of
this specific fix) — reproduces independently at 392/2209 = 17.7% —
derived: python script matching `\[poll-report\] ... HEALTHY` against
the current routine bucket, this turn, result: `392 / 2209 = 17.7%`,
consistent given transcript growth. That disclosed, narrower framing is
accurate; the undisclosed one (the 87.8% headline conflating unrelated
Monitor watches and spawn-halt content with true watchdog noise) is
not.

**5. Monitor liveness — the finding this PR turns on.** canonical:
`docs/handbooks/monitor-liveness.md` (PR-branch worktree, read in full,
this turn — cited by the PR's own record as upstream basis). It
documents, pre-existing and unmodified by this PR, a section titled
"Structural limit: full-idle death cannot self-heal": `directive.sh`
and `stop-poll-rearm.sh` are **turn-driven** — they only run
`_monitor_liveness_check_and_notify()` when a UserPromptSubmit or Stop
event fires. "If the Monitor dies during a fully idle stretch (no user
turn arriving at all, and no Monitor left to tick), nothing in this
repo observes that death ... until the next turn actually happens."
Confirmed live in `on-the-record/monitors/poll-heartbeat.sh:256-258`
(read directly, this turn): `printf` only runs `if [ -n
"${diff_output}" ]` — a fully-suppressed tick produces zero stdout, so
no Monitor task-notification fires for that tick at all (not merely a
quiet notification; no notification).

The PR's record demonstrates the staleness-check *function* is correct
when invoked (simulated a 400s-stale stamp, got `[MONITOR-DEAD]`
correctly — canonical: `docs/issue-2906/reports/silent-failure-audit-
c7e19e1e.md` (untracked on this branch, PR branch only) "Monitor-
liveness check" paragraph, read this turn). It does not address whether
the function gets invoked often enough post-fix. Before this fix, the
bug being fixed was — as an unintended side effect — also the mechanism
keeping the orchestrator receiving a turn roughly every ~120s during
any period when at least one roster entry was alive and HEALTHY (since
the activity clause changed on nearly every tick, nearly every tick
emitted, nearly every tick forced a turn, and each turn re-ran the
turn-driven staleness check for free). Measured across the reference
transcript, an alive roster entry appears to have been true for the
overwhelming majority of the 8-day window — canonical: section 4's own
re-derivation above (88% routine, 12% anomaly, near-continuous
notification traffic) — that is precisely why 87.8% of wakes were
"routine" rather than "nothing happening at all." This fix removes that
forced ~120s cadence specifically during the periods it targets
(healthy, stable, nothing to act on) — which are, by the PR's own
numbers, the common case. The documented "structural limit" (full-idle
death is invisible until the next turn) does not change in kind, but
its *practical exposure window* widens substantially, because the
accidental near-continuous turn cadence that used to bound it in
practice is exactly what this fix removes. The PR's record neither
measures nor acknowledges this trade — it reads `docs/handbooks/
monitor-liveness.md`'s structural-limit section (cited as upstream
basis) without connecting it back to what its own fix does to that
limit's practical bound. If the monitor dies during a stretch this fix
now keeps quiet, the honest answer to "how long until something
notices" is: not the stated 360s bound (`directive.sh`'s default; note
`stop-poll-rearm.sh` defaults to 180s and the handbook itself says
180s/"3x the 60s poll interval", but the actual poll interval is 120s —
three different numbers for the same threshold across two hook files
and their own doc, checked directly by reading all three, a
pre-existing drift this PR did not create but also did not have reason
to touch) — it is unbounded, until some *other* unrelated turn-driver
fires. That is exactly the "nothing until the next state change" case
this review was told to name plainly if true, and it is true.

**6. `.orchestrate-hook-fires/unknown.log`** — established as a
pre-existing repo-hygiene defect, not caused by or related to this PR's
diff (which never touches `hook_fires.py`/`hook-fires.sh` — checked via
`git diff main...pr-2913 --stat`, this turn, file list confirmed above
does not include either path). The whole `.orchestrate-hook-fires/`
directory is declared in `.gitignore` (line 29, read directly) —
specifically because `hook_fires.py`'s own docstring (read directly)
says it is a per-session, per-workspace ephemeral artifact — yet
`git ls-files` on this checkout shows 27 shard files already committed
to history despite the ignore rule, including
`.orchestrate-hook-fires/unknown.log` itself — derived: `git log
--oneline -- .orchestrate-hook-fires/unknown.log`, this turn, result:
first committed at `96513f8c` ("issue-2348: shard hook-fires and
deviation-log per session", 2026-08-25). Because it is already tracked,
`.gitignore` cannot protect it from further modification: every hook
firing (`directive.sh`/`stop-gate.sh`/`stop-poll-rearm.sh`) whose stdin
JSON payload lacks a resolvable `session_id` appends a line to this
*specific*, shared, already-tracked file (`_hook_fires_shard_id()`
returns the fixed literal `"unknown"` for that case, read directly) —
derived: `git show HEAD:.orchestrate-hook-fires/unknown.log | wc -l`,
this turn, result: `612` lines already, spanning dates through
2026-08-28, from many different sessions all landing in the same
tracked file. This is not a harmless one-off artifact: it is a
standing, currently-active dirty-tree trap for any session on this
branch lineage whose hooks ever hit the missing-session_id fallback,
and the correct fix is `git rm --cached` on the 27 already-committed
shard paths (never re-adding them, since the `.gitignore` rule is
already correct) — out of scope for PR #2913 itself but real, and not
something this review should let pass as "probably fine."

## Why

Adversarial review of a change that intentionally makes a signal
quieter demands verifying the mechanism (does it suppress only what it
claims to), the boundary (does every other signal still get through),
and — because "quieter" is exactly the failure mode that doesn't
announce itself — the second-order effect on the one thing this issue
was explicitly forbidden to trade away (monitor liveness). canonical:
the full re-derivation in "What was done" above, sections 1-6, all
executed this turn against the PR worktree, the main worktree, and the
live orchestrator transcript — re-deriving every number from the same
raw sources the PR used (its own diff, its own worktree, the same live
transcript) rather than restating its record was the only way to find
the two things its own record didn't surface: that ~18-27% of what it
counts as "noise" isn't watchdog noise at all or is arguably real
signal (spawn halts) misclassified, and that its own cited liveness
doc's "structural limit" section, read carefully against what this fix
removes, names the exact risk this review was asked to confirm or
refute.

## What did not work

None — every check in this review ran to a conclusion on the first
attempt; no approach was tried and abandoned.

## Upstream basis

- PR #2913, branch `issue-2906/silent-failure-audit-c7e19e1e`, commits
  `290141e9fec95d8187e5a8a3ad7cc10954e4ccaa` (fix) and
  `5624bcb0a3ad86ac834ea31927a36d52ff9b6e745` (deviation-log entry) —
  the subject of this verification.
- `docs/issue-2906/reports/silent-failure-audit-c7e19e1e.md` (untracked
  on this branch; lives only on PR branch
  `issue-2906/silent-failure-audit-c7e19e1e`, same commit as the fix;
  read via `git worktree add /tmp/pr2913-review pr-2913`) — the PR's
  own record; read in full, not restated, independently re-derived per
  section above.
- `on-the-record/monitors/poll_heartbeat_delta.py`,
  `on-the-record/monitors/test_poll_heartbeat.py`, `watchdog.py`,
  `on-the-record/hooks/directive.sh`, `on-the-record/hooks/
  stop-poll-rearm.sh`, `on-the-record/monitors/poll-heartbeat.sh`,
  `docs/handbooks/monitor-liveness.md`, `hook_fires.py` — all read
  directly from a `git worktree add` checkout of the PR head (and a
  parallel `origin/main` worktree for the differential checks), not
  from the PR's descriptions of them.
- Orchestrator transcript `~/.claude/projects/-home-jwjung-tokenmaxxxer/
  93c239f8-561b-41f5-b69c-ae9e757b7939.jsonl` (external, read-only,
  101,570,820 bytes / 68,479 lines at time of this review) — parsed
  independently with my own script, not the PR's.

## Open findings

- **The 87.8%/2493 headline conflates three distinct populations**:
  true `[poll-report]` HEALTHY noise this fix addresses (~17.7% of the
  routine bucket, reproduced above), other watchdog-tag noise this fix
  deliberately leaves alone and the PR *does* disclose (board-sweep,
  accumulation-trend), and two undisclosed populations — non-heartbeat
  Monitor watches (18.0% of all event-bearing notifications) and
  `[spawn-attempt]`/"spawn halted" content misclassified as
  non-actionable (27.2% of the routine bucket) — canonical: section 4
  of "What was done" above, all counts derived this turn from the live
  transcript. Resolution path: none required to land this PR (the code
  fix is correctly scoped and doesn't claim to fix the undisclosed
  populations), but the PR body/record's headline framing overstates
  what the fix addresses; a follow-up should either narrow the reported
  percentage to the watchdog-specific denominator or add
  `[spawn-attempt]`/"spawn halted" to the classifier's anomaly
  vocabulary before citing this measurement again.
- **Monitor-liveness detection bound widens in practice, undisclosed**:
  the documented 360s (or 180s, depending on which hook file) staleness
  bound assumes `_monitor_liveness_check_and_notify()` gets invoked on
  a cadence close to the poll interval; before this fix, the very bug
  being fixed provided that cadence for free during any period with a
  live, healthy roster entry (the common case, per this PR's own
  numbers) — canonical: section 5 of "What was done" above. After this
  fix, during exactly that common case, nothing forces a turn, so
  nothing invokes the staleness check, until some unrelated event does.
  This is the highest-severity finding in this review — resolution
  path: not a revert (the suppression mechanism itself is correct and
  the noise problem is real), but a follow-up issue should either (a)
  give `poll-heartbeat.sh` its own independent, content-independent
  liveness ping on a fixed interval (e.g., a low-frequency always-emit
  "monitor alive" line, orthogonal to the delta-suppression this PR
  correctly narrows), or (b) explicitly accept and document the widened
  exposure window as a deliberate trade against #1497/#2182's
  388-minute incident, rather than leaving it unmeasured and
  unmentioned.
- **`.orchestrate-hook-fires/unknown.log` and 26 other shard files are
  committed despite `.gitignore`**: pre-existing (issue #2348), not
  caused by PR #2913 — canonical: section 6 of "What was done" above.
  Resolution path: a small, separate follow-up — `git rm --cached` the
  27 already-tracked `.orchestrate-hook-fires/*` paths; no code change
  needed since the ignore rule is already correct, only the historical
  commit needs undoing.
- **Threshold drift across `directive.sh` (360s default),
  `stop-poll-rearm.sh` (180s default), and `docs/handbooks/
  monitor-liveness.md` (documents 180s / "3x the 60s poll interval",
  but the actual poll interval is 120s)**: pre-existing, noticed
  incidentally while verifying finding 2 above (canonical: section 5 of
  "What was done"), not caused by this PR. Resolution path: a
  documentation/consistency follow-up, low priority.

## Next steps

None — `loop_state: landed`. This record's findings are complete —
canonical: `python3 -m pytest . -q` and `python3 gates/
retirement_count.py`, both re-run this turn against both worktrees per
section 3 of "What was done", plus the transcript re-derivation in
section 4, all executed live this turn, not read from the PR's own
claims. No code was changed by this review (PR #2913 was not modified,
per the adversarial-review skill's structural-independence contract —
evaluate, do not fix).

skill-verdict: adversarial-review — applied: invoked; called via the
Skill tool this turn — canonical: Skill tool call this turn returned the
full SKILL.md body (structurally independent evaluation, no shared
context with the builder, evidence-per-finding requirement). Deviation
logged (see this session's deviation-log entry): the review itself was
already carried out and committed in the protocol's shape before this
call happened. The protocol as read matches the work done above: every
checkable claim in PR #2913 was re-derived from primary sources (diff,
worktree checkouts, live transcript, cited handbook doc) rather than
read and restated from the builder's own record, and the four required
live transitions plus the boundary enumeration were constructed before
consulting the PR's own test file.
skill-verdict: work-in-english — applied: invoked; called via the Skill
tool this turn — canonical: Skill tool call this turn returned the full
SKILL.md body (English for repo-bound exhaust, Korean for the final
user-facing summary). Deviation logged, same entry as above. The rule as
read matches the work done above: this record and all intermediate
scratch scripts are in English, and the final chat summary to the user
is Korean.
other mounted skills: not triggered
