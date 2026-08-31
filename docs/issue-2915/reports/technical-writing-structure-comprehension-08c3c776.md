---
issue: 2915
role: technical-writing-structure-comprehension-08c3c776
author: technical-writing-structure-comprehension-08c3c776
skills: technical-writing-structure-comprehension (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2915/reports/adversarial-review-fa319c5b.md
    sha: 0209daf7d1a75d8fe7df15fc350fe9bcfe2e967b
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
---

# issue-2915 — technical-writing-structure-comprehension-08c3c776 record

## What was done

Round 5 on issue #2915: rebases the fix from PR #2946 (round 4,
`issue-2915/technical-writing-structure-comprehension+diagnose-first-676b7bd2`,
still `OPEN`/`CONFLICTING` against `main` at the time of this session —
canonical: `gh pr view 2946 --json state,mergeable` — result:
`{"state":"OPEN","mergeable":"CONFLICTING"}`) onto current `main`
(`97fd8c2641ec784d46ab92f55c7adcfaa7065e82`, "round 3 — withdraw false
dead-Monitor detection-latency bound claim", PR #2934) and lands it from
a fresh branch/PR, per this round's spawning instructions not to reuse
#2946's branch.

This session's branch (`issue-2915/technical-writing-structure-comprehension-08c3c776`)
was already at `origin/main` HEAD when the session started — derived:
`git merge-base HEAD origin/main` and `git log --oneline -1 origin/main`
both resolve to `97fd8c26`. So there was no branch-level rebase to run
mechanically; the work was to apply round 4's *semantic* fix directly to
the current file, which already differs from the pre-round-4 file #2946
was authored against (round 3, PR #2934, rewrote the same "Staleness
threshold and the re-arm directive" paragraph in the interim, adding the
`directive.sh`=360s / `stop-poll-rearm.sh`=180s distinction and the
`watchdog.POLL_INTERVAL_SEC` attribution that #2946's diff still shows as
the old, pre-round-3 180s-only text).

**Reconciliation, not duplication.** Comparing #2946's diff
(`gh pr diff 2946`) against current `main`'s paragraph
(`docs/handbooks/monitor-liveness.md:35-55`) line by line:

- The 360s/180s split, the `watchdog.POLL_INTERVAL_SEC`=60s attribution,
  and the "NOT `poll-heartbeat.sh`'s own 120s tick-loop sleep" distinction
  were already correct on `main` (landed by round 3) — re-verified
  against the code rather than carried forward on trust: `grep -n
  'MONITOR_LIVENESS_STALE_SECONDS' on-the-record/hooks/directive.sh
  on-the-record/hooks/stop-poll-rearm.sh` — result:
  `stop-poll-rearm.sh:56: ...:-180}` and `directive.sh:211: ...:-360}`;
  `grep -n 'sleep' on-the-record/monitors/poll-heartbeat.sh` — result:
  `sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"`; `grep -n
  'POLL_INTERVAL_SEC' watchdog.py spawn.py` — result: `watchdog.py:67:
  POLL_INTERVAL_SEC = 60`, `spawn.py:196: POLL_INTERVAL_SEC =
  watchdog.POLL_INTERVAL_SEC` (spawn.py re-exports watchdog's constant,
  confirming the handbook's "the unrelated `spawn.py poll-due()` TTL
  gate" phrasing is accurate — it's the same 60s value under a second
  name). Nothing to re-fix here; not duplicated.
- What was still stale on `main`: the paragraph's last two sentences
  claimed `poll_heartbeat_delta.py`'s 1800s-bound beacon "bounds
  detection for a non-empty tracked roster specifically, without
  touching this check" — the exact dead-Monitor detection-latency bound
  claim round 3's own deep "Issue #2915" section (~90 lines below,
  `docs/handbooks/monitor-liveness.md:292-307` on `main`) explicitly
  withdrew ("an aliveness/observability improvement, not a dead-Monitor
  detection-latency bound"). This is the one substantive edit #2946 made
  and the one this session ports forward.

**The edit applied** (`docs/handbooks/monitor-liveness.md:47-55`):
replaced the withdrawn-claim sentence with three statements, each
checked against the code before being asserted rather than copied
forward from #2946's diff on trust:

1. The 360s/180s numbers bound how fast the turn-driven check flags a
   stale stamp once invoked (measured ~29ms, established in round 1 and
   unchanged since — no code in `directive.sh`/`stop-poll-rearm.sh` has
   been touched by any round of this issue) — and *not* how often the
   check is invoked, nor how quickly an actually dead Monitor's death
   reaches the orchestrator. (#2946's version stated the first two but
   not the third explicitly; added it here per this round's brief.)
2. During a genuinely healthy, quiet stretch, nothing in this repo
   bounds that invocation — forward-referencing "Structural limit"
   rather than restating its argument.
3. `poll_heartbeat_delta.py`'s 1800s beacon does not close that gap
   either, because a dead tick loop cannot emit the beacon that would
   announce its own absence — checked against
   `on-the-record/monitors/poll_heartbeat_delta.py:218` (`if now -
   last_emit_epoch >= 1800:`) and its surrounding comments (lines
   218-273): the beacon line is only ever appended by code running
   inside the same tick loop being checked for liveness; nothing else in
   the file emits it.

## Why

Same rationale as #2946: the paragraph at
`docs/handbooks/monitor-liveness.md:35-55` is the reader's first
encounter with the 360s/180s numbers, and until this edit it asserted —
in the same file, ~90 lines above the section that withdrew it — a bound
on dead-Monitor detection latency that round 3 had already shown does
not exist. A handbook that states one position early and the opposite
position later, without a forward reference tying them together, forces
the reader to notice the contradiction unaided. Forward-referencing
"Structural limit" instead of re-arguing the case here keeps the
paragraph short and avoids a second, potentially-diverging copy of the
same argument.

Applied `technical-writing-structure-comprehension` (loaded via the
Skill tool this session — canonical: its SKILL.md body, procedure steps
1-8 and rules 1-10) to the replacement text: split the original run-on
sentence ("...specifically, without touching this check.") into short,
single-clause sentences targeting the skill's 15-20-word guidance, kept
the bolded caveat sentence pair together since they carry the one
measured number the rest of the paragraph depends on, and deleted no
content the reader needs — the added clause about death reaching the
orchestrator is new information this round's brief required, not
padding.

skill-verdict: technical-writing-structure-comprehension — applied: invoked; restructured `docs/handbooks/monitor-liveness.md:47-55` per the canonical SKILL.md procedure cited above, splitting the withdrawn-claim sentence into shorter single-clause sentences while preserving the bolded caveat and adding a forward reference instead of duplicating the deep section's argument.

other mounted skills: not triggered (work-in-english governs language
only, no separate invocation needed beyond writing this record and its
commit/PR in English).

## What did not work

None. There was no branch-level git conflict to resolve mechanically
(this session's branch started at `origin/main` HEAD, unlike #2946's
branch which was cut before round 3 landed) — the "conflict" named in
this round's brief was resolved by applying #2946's semantic fix
directly to the current file rather than by a literal `git rebase`
invocation.

## Upstream basis

- `docs/issue-2915/reports/adversarial-review-fa319c5b.md`
  (`0209daf7d1a75d8fe7df15fc350fe9bcfe2e967b`) — the independent review of
  round 3 that found the stale paragraph #2946 (and this round) fixes.
- `docs/handbooks/monitor-liveness.md` (`same-commit`) — the file edited
  here.
- PR #2946 (`issue-2915/technical-writing-structure-comprehension+diagnose-first-676b7bd2`,
  still open/conflicting) — canonical: `gh pr diff 2946` — supplied the
  semantic fix ported forward; not merged, so not citable by sha.

## Verification: no detection-bound claim remains

Re-ran #2946's own check against the post-edit file, plus the same wider
superset it used, bounded to this one file (the paragraph this round
touches, plus every other paragraph in the same file — the search is not
scoped to a section, so it covers the population #2946 itself checked):

- derived: `grep -n "bounds detection\|bound.*detection\|detection.*bound" docs/handbooks/monitor-liveness.md`
  — result: 2 hits, both inside round 3's deep "Issue #2915" section:
  line 285 ("a true bound on actual-death detection needs an OS-level
  scheduled-execution primitive" — states no such bound exists in-repo)
  and line 307 ("...an aliveness/observability improvement, not a
  dead-Monitor detection-latency bound" — explicit denial). Neither
  asserts a bound exists.
- derived: `grep -c -i "bound\|detect\|beacon\|infer\|absence\|surfac" docs/handbooks/monitor-liveness.md`
  — result: 52 matching lines total, spanning the edited paragraph
  (lines 47-55, the corrected text) and the pre-existing "Structural
  limit" / "Issue #2915" sections (lines 120-338); read every hit's
  surrounding line and confirmed none states or implies a code-enforced
  dead-Monitor detection-latency bound — all either describe the
  turn-driven check's own ~29ms flag-latency (a different, narrower
  claim this round preserves), or explicitly state the absence of a
  bound (`unbounded`, `not... a detection-latency bound`, `a true bound
  ... needs an OS-level ... primitive`).

## Open findings

None.

## Next steps

None — this record and its PR are the terminal delivery for round 5.
