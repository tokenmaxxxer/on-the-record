---
issue: 2915
role: adversarial-review-fa319c5b
author: adversarial-review-fa319c5b
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2934 round 3's own deliverable
loop_state: landed
upstream:
  - path: PR #2934 (head sha 422ec2b18f571b5acbf7b812124212801a65656e)
    sha: 422ec2b18f571b5acbf7b812124212801a65656e
  - path: docs/issue-2915/reports/adversarial-review-708b12ce.md
    sha: same-commit
---

# issue-2915 — adversarial-review-fa319c5b record

## What was done

Independent verification of PR #2934 (round 3 of issue #2915, "withdraw
false dead-Monitor detection-latency bound claim"), responding to round
2's independent review (`docs/issue-2915/reports/adversarial-review-708b12ce.md`,
landed via PR #2931). canonical: `gh pr view 2931` — result: `state:
MERGED`, this turn; `gh pr view 2934` — result: `state: OPEN`, this
turn. Re-derived every claim from primary sources, not round 3's own
record — canonical: `git worktree add /tmp/pr2934wt pr2934-head` and
`git worktree add /tmp/mainwt2 origin/main`, both run this turn, plus
`git fetch origin pull/2934/head:pr2934-head`, giving an independent
checkout of the PR head (`422ec2b18f571b5acbf7b812124212801a65656e`) to
read, diff, and execute code from directly.

skill-verdict: adversarial-review — applied: invoked; loaded the skill
via the Skill tool this turn and followed its blind/independent-evaluator
posture — this session is structurally independent of the round-3
builder session by construction (fresh context, spawned solely to
review), re-derived every claim below from primary sources (the diff,
worktree checkouts, and live script execution) rather than trusting
round 3's own record, per the skill's core mechanism.
other configured skills: implementation-audit — not-applicable: this
task handed direct attack points to check, not a builder-extracted
falsifiable-claims list to classify Present/Surface/Absent/
Incorrect/Unverifiable against a spec; no two-session claim-extraction
handoff was set up for this round, so the audit's specific claim-tracing
protocol does not fit this review shape.

### Verified true (no defect)

- **Code is byte-identical to round 2** — derived: `git diff
  93e674941e6fe291fe745f12a38028f7a31d77d9 pr2934-head --
  on-the-record/monitors/poll_heartbeat_delta.py
  on-the-record/monitors/poll-heartbeat.sh
  on-the-record/monitors/test_poll_heartbeat.py`, this turn — empty
  output on all three files. `93e67494...` is round 2's own head
  (PR #2917), already independently verified against `origin/main` in
  `docs/issue-2915/reports/adversarial-review-708b12ce.md`. Confirms the
  PR body's "no code changed in this round" claim directly, not by
  reading the claim. `directive.sh` and `stop-poll-rearm.sh` (the
  pre-existing staleness-check hooks) are likewise untouched — derived:
  `git diff 46779718d2435a8749d7c736e86d3f54a5dc30d5 pr2934-head --
  on-the-record/hooks/directive.sh
  on-the-record/hooks/stop-poll-rearm.sh`, this turn — empty output.
- **PR's actual file-level diff scope matches `gh pr diff`'s reported
  scope, not the noisy result of naively diffing against current
  `origin/main`'s tip** — derived: `git diff origin/main pr2934-head
  --stat`, this turn, result: spuriously shows large deletions across 24
  files, including unrelated issue-2920 files (`skills.py`,
  `test/test_consult_skill_resolution_2920.py`, etc), because
  `origin/main` had 3 issue-2920 commits land after this PR's merge-base
  — canonical: `git log --oneline -5` this turn shows `25fbd379`,
  `a7334fd3`, `16e6bc56` (all `issue-2920: ...`) on current `origin/main`
  — base drift, not this PR's own change. Using the actual merge-base
  instead: derived: `git merge-base origin/main pr2934-head` → result:
  `46779718d2435a8749d7c736e86d3f54a5dc30d5` (round 2's own review-merge
  commit); derived: `git diff --stat 46779718... pr2934-head`, this
  turn, result: `10 files changed, 1314 insertions(+), 16 deletions(-)`
  — matches `gh pr view 2934`'s reported `additions: 1314 deletions: 16`
  exactly, and the file list matches `gh pr diff 2934 --name-only`
  exactly (handbook, three monitor files, and six new docs/issue-2915
  report/hunt files). Ruled out as a non-issue after checking, not left
  as an open question.
- **Test count unchanged** — derived: `cd /tmp/pr2934wt && python3 -m
  pytest on-the-record/monitors/test_poll_heartbeat.py -q`, this turn,
  result: `35 passed` — matches round 2's own count exactly, consistent
  with zero code change.
- **The deep "Issue #2915" handbook section is a genuine, well-reasoned
  withdrawal, not a rewording** — canonical:
  `docs/handbooks/monitor-liveness.md` (PR head, read in full this
  turn), diffed precisely against round 2's own head — derived: `git
  diff 93e674941e6fe291fe745f12a38028f7a31d77d9 pr2934-head --
  docs/handbooks/monitor-liveness.md`, this turn, result: one hunk,
  entirely replacing round 2's "**Worst-case detection latency for a
  dead Monitor ... is now bounded at ~1800s ...**" paragraph and its
  "What remains unbounded" paragraph with new prose that (a) explicitly
  names round 2's claim as wrong and states why (a dead tick loop cannot
  emit one more line to announce its own death), (b) re-confirms live
  that no consumer reads the tag or alerts on its absence, (c)
  constructs and reports a literal kill scenario, (d) explicitly
  reconciles with the adjacent "Structural limit: full-idle death cannot
  self-heal" section (confirmed unmodified by this same diff — that
  section sits above the diff's insertion point and appears verbatim,
  unchanged, in both `origin/main`'s and the PR head's copy), and (e)
  states plainly what the beacon is now for ("an aliveness/observability
  improvement, not a dead-Monitor detection-latency bound"). This is the
  shape the round-2 review's own resolution path asked for.
- **Dead-monitor construction independently reproduced** — derived: my
  own from-scratch script (`/tmp/verify_r3_dead_monitor.py`, not round
  3's `/tmp/issue2915r3/dead_monitor_scenario.py`), this turn: ran the
  real, unmodified `poll_heartbeat_delta.py` for a 1h warm-up (31 ticks
  at 120s spacing, healthy roster), then stopped invoking it entirely —
  by construction nothing can emit past that point, since the only thing
  capable of printing is the script itself and it is never called again.
  This structurally confirms (not merely re-reads) round 3's own
  +1h/+3h/+24h/+388min claim: elapsed wall-clock from actual death to
  surfaced-to-orchestrator remains bounded only by whenever an unrelated
  turn next arrives — unbounded if none does. Matches round 1's original
  finding and is not a new regression introduced by round 2 or round 3.
- **1800s boundary and 1920s jitter figure, independently reconstructed**
  — derived: `/tmp/verify_r3_boundary.py`, this turn: unchanging-content
  ticks at t=1799 emit nothing, t=1800 emits
  `[monitor-heartbeat] issue-500/implementation: HEALTHY ...` — exact
  boundary confirmed. With irregular tick spacing (133s), worst gap
  measured `1862s` (bound + slack, consistent with the ">= 1800,
  first-tick-past-bound" mechanic). Separately checked: with perfectly
  clock-regular 120s ticks (both aligned-from-0 and offset-start), the
  gap lands at exactly `1800s`, not `1920s` — the extra up-to-one-tick
  slack the handbook cites is a worst-case bound for irregular/jittered
  real timing, not something that fires on every cycle; the handbook's
  own phrasing ("worst case is ... up to one tick interval") is
  consistent with this, not overstated.
- **1920s correction landed everywhere the old flat-1800s *detection*
  claim appeared, except one place (see Finding 1)** — derived: `grep
  -rn "detection.latency\|detection latency" --include="*.py"
  --include="*.sh" --include="*.md" /tmp/pr2934wt`, this turn: every hit
  is either the corrected framing (`monitor-liveness.md:305`, "not a
  dead-Monitor detection-latency bound") or a quoted/historical
  restatement of round 2's now-withdrawn sentence, explicitly marked as
  withdrawn (`monitor-liveness.md:235`). The `1800s` occurrences in
  `on-the-record/monitors/test_poll_heartbeat.py` and
  `poll_heartbeat_delta.py` itself describe the code's literal `>= 1800`
  constant (correctly unchanged — that IS the threshold), not a
  detection-latency claim, so they correctly do not say `1920s`.
- **No watch-family or suppression-logic regression** — inherited from
  round 2's own independently-verified findings (byte-identical code, per
  above): `ALWAYS_RE`-matching lines still make the new branch
  structurally unreachable whenever an anomaly is present, the
  `to_emit`/else split is untouched, and no retired role axis reappears
  anywhere in this diff — derived: `gh pr diff 2934 --name-only`, this
  turn, result: only `docs/handbooks/monitor-liveness.md`, three
  `on-the-record/monitors/*` files, and new `docs/issue-2915/reports/*`
  / `docs/reports/*` files — no role-resolution or skill-mounting code
  touched.

### Finding 1 (MAJOR) — the withdrawal is incomplete: one earlier paragraph in the same handbook file still asserts the exact claim round 3 elsewhere calls wrong

canonical: `docs/handbooks/monitor-liveness.md:44-53` (PR head,
`/tmp/pr2934wt`, read this turn), in the "Staleness threshold and the
re-arm directive" section — near the very top of the document, well
before the deep "Issue #2915" subsection round 3 rewrote:

```
**These numbers bound how fast this turn-driven check flags a stale
stamp once invoked (measured: ~29ms, issue #2915), not how often the
check gets invoked.** See "Structural limit" below — this turn-driven
check's own invocation, during a genuinely healthy, quiet stretch, is not
bounded by anything in this repo. A separate, independent mechanism
(`poll_heartbeat_delta.py`'s own 1800s-bound beacon, issue #2915 round 2)
bounds detection for a non-empty tracked roster specifically, without
touching this check.
```

This is precisely the claim round 3's own big edit, ~150 lines further
down in the same file, explicitly withdraws and calls a category error —
canonical: `docs/handbooks/monitor-liveness.md:235-238` (PR head): "Round
2's claim here was wrong and is withdrawn ... That sentence measured the
wrong quantity" (verified above in "Verified true"). derived: `git diff
93e674941e6fe291fe745f12a38028f7a31d77d9 pr2934-head --
docs/handbooks/monitor-liveness.md`, this turn — the diff has exactly
one hunk, starting at the deep "Issue #2915" subsection
(`@@ -230,18 +230,90 @@`); the "Staleness threshold" paragraph quoted
above is outside that hunk, confirming it is byte-identical to round 2's
version — independently re-confirmed: derived: `git show
93e674941e6fe291fe745f12a38028f7a31d77d9:docs/handbooks/monitor-liveness.md
| sed -n '44,53p'` this turn, result: the same text verbatim. Round 3
re-checked and rewrote the deep section but did not sweep the rest of
the file for the same claim — a targeted grep would have caught it:
derived: `grep -n "bounds detection\|bound.*detection\|detection.*bound"
docs/handbooks/monitor-liveness.md` (PR head), this turn, result: 3
matching lines total — line 53 (the uncorrected claim), plus lines 283
and 305 (both correctly rewritten); derived: same grep command re-run
this turn, 1 of those 3 hits (line 53) is still the stale, unwithdrawn
version.

This directly fails the central check this round exists to answer: a
reader who starts at the top of the document — where the 360s/180s
thresholds are first introduced, the section most readers would consult
first for "what do these numbers bound" — encounters, immediately after
them, an unambiguous assertion that a separate mechanism "bounds
detection ... for a non-empty tracked roster," with no hedge, no forward
reference to a correction, and no indication it is stale. They would
have to already know to keep reading ~150 more lines into "Structural
limit" and the "Issue #2915" subsection to learn this sentence is wrong.
The PR does not merely leave an overclaim standing by omission; it
creates a new internal contradiction inside the same file between this
early paragraph and its own later correction — the identical shape of
defect round 2 was faulted for (two sections in the same file reaching
opposite conclusions about the same failure mode, unreconciled), now
reproduced at smaller scale between two parts of round 3's own edit.

Resolution path: apply the same correction already written for the deep
section to this paragraph — replace "bounds detection for a non-empty
tracked roster specifically" with language matching the corrected
framing ("bounds silence-while-alive for a non-empty tracked roster
specifically, not detection of the Monitor's own death"), or delete the
forward-pointing sentence and let the reader reach the fuller correction
below via the existing "See 'Structural limit' below" pointer already in
this same paragraph.

## Why

The task named five attack points. (1) The central question — genuine
rescoping vs. rewording that leaves an overclaim standing — resolves to
**mostly genuine, with one incomplete spot**: the deep section round 3
rewrote is a real, well-evidenced withdrawal (canonical:
`docs/handbooks/monitor-liveness.md:230-320`, verified above,
independently reconstructed, not just re-read), but Finding 1 shows the
sweep for the old claim did not cover the whole file, so the answer to
"would a reader come away believing dead-Monitor detection is bounded"
is: not if they read the deep section, but possibly yes if they stop at
the paragraph that introduces the numbers in the first place. (2) What
the beacon is now for: it has no repo-code consumer (independently
re-confirmed, `grep -rn "monitor-heartbeat" ...` above, matching round 2's
and round 3's own enumeration exactly) — but it is not necessarily pure
unconsumed noise either. The handbook's corrected section grounds a
real, hedged (`"likely does restore"`, not asserted as certain) claim in
independent, previously-merged evidence — canonical:
`docs/issue-2906/reports/adversarial-review-30a89443.md:196-198,208-211`
(read directly this turn, not taken on round 3's word) — that non-empty
Monitor stdout forces a platform-level task-notification/turn while the
Monitor is alive, a mechanism outside this repo's own code (the
harness's Monitor-tool plumbing) that this review cannot execute-verify
directly but which is honestly hedged rather than overclaimed. That is
a real, if modest and appropriately-qualified, answer to "what earns
it" — not a bare assertion. (3) The 1920s correction landed everywhere
the detection-latency claim itself appears, confirmed by grep above
(canonical: `docs/handbooks/monitor-liveness.md`, grep results cited in
"Verified true"), with the sole exception being Finding 1. (4) The
beacon's boundary/jitter behavior, independently reconstructed this turn
from the byte-identical code (not trusted from either round 2's or round
3's own numbers), matches both rounds' figures exactly, including the
nuance that clock-regular ticks land the gap at exactly 1800s, and only
irregular timing produces the "up to one tick interval" slack the
handbook correctly hedges as a worst case rather than a typical value.
(5) No watch-family signal, anomaly line, or suppression condition
changed — inherited from round 2's own already-verified byte-identical
code; no retired role axis reappears anywhere in this PR's touched-file
list (canonical: `gh pr diff 2934 --name-only`, cited above). A dead
Monitor is not less detectable after this round than before it — the
true, unbounded-during-full-idle answer is unchanged across all three
rounds; round 3 only changes what the *handbook claims* about that
answer, and Finding 1 is the one place that claim is still wrong.

## What did not work

None — every independent reconstruction in this review (boundary
timing, jitter, dead-monitor kill scenario, code-identity diffing, the
merge-base correction for the base-drift diff scare) ran to a clean,
reproducible result on scripts written for this review
(`/tmp/verify_r3_boundary.py`, `/tmp/verify_r3_dead_monitor.py`),
independent of both round 2's and round 3's own harnesses.

## Upstream basis

- PR #2934 (round 3), head sha `422ec2b18f571b5acbf7b812124212801a65656e`
  — canonical: `gh pr view 2934`, `gh pr diff 2934`, this turn, plus a
  `git worktree add` checkout at `/tmp/pr2934wt`, this turn.
- `origin/main` — `git worktree add` checkout at `/tmp/mainwt2`, this
  turn; merge-base with the PR head resolved to
  `46779718d2435a8749d7c736e86d3f54a5dc30d5` (round 2's own review-merge
  commit) via `git merge-base`, used for the correct file-scope diff
  after the naive `origin/main` diff proved to include unrelated
  issue-2920 base drift (verified above).
- PR #2917 round 2 head, sha
  `93e674941e6fe291fe745f12a38028f7a31d77d9` — used as the precise
  round-2-vs-round-3 diff baseline (already fetched in this checkout
  from the prior round's review).
- `docs/issue-2915/reports/adversarial-review-708b12ce.md` (round 2's
  independent review) — canonical: `gh pr view 2931` this turn, result:
  `state: MERGED` — read for what round 3 claims to respond to; not
  treated as authoritative for round 3's own claims, per this task's
  instruction.
- `docs/issue-2906/reports/adversarial-review-30a89443.md` — cited by
  the handbook (and re-cited here) as independent, pre-existing evidence
  for the stdout-forces-a-turn mechanism; read directly, not taken on
  round 3's word.

## Open findings

- **Finding 1 (MAJOR)**: `docs/handbooks/monitor-liveness.md:50-53`
  still states the withdrawn "bounds detection ... for a non-empty
  tracked roster specifically" claim, unreconciled with the corrected
  section ~150 lines below in the same file. Resolution path: apply the
  same correction to this paragraph (state it bounds silence-while-alive,
  not detection of death) or delete the sentence and rely on the
  existing "See 'Structural limit' below" pointer already present in the
  same paragraph.
- No other open findings; verified-true items above require no
  follow-up.

## Next steps

None from this record — per role scope, this session evaluates PR #2934
and does not fix it. `loop_state: landed`.
