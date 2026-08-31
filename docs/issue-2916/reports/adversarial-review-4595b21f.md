---
issue: 2916
role: adversarial-review-4595b21f
author: adversarial-review-4595b21f
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: PR #2918 (github.com/tokenmaxxxer/on-the-record/pull/2918)
    sha: 64af2be1650c0dc310cc3352d270548a59edbec3
  - path: 64af2be1650c0dc310cc3352d270548a59edbec3:docs/issue-2916/reports/refactoring-legacy-seam-selection+observability-explorability-b3797400.md
    sha: 64af2be1650c0dc310cc3352d270548a59edbec3
---

# issue-2916 — adversarial-review-4595b21f record

skill-verdict: adversarial-review — applied: invoked; loaded via Skill tool before verifying (Skill tool call, this session). canonical: this session's own tool-call transcript (Skill invocation of `adversarial-review`). Used the skill's blind-evaluator posture as the standing frame, but the concrete method per attack point was construction/reproduction against primary sources rather than open-ended critique, since every claim below is a checkable pass/fail, not a style judgment.

## What was done

Independently verified all five claims (a)-(e) in PR #2918 plus the four
standing invariants named in the task, against primary sources only.
canonical: `gh pr diff 2918` output (the diff itself), two real git
worktrees checked out this session (`/tmp/wt-2918-head` at PR head
`64af2be1` / fix commit `7b2f2de0`, `/tmp/wt-2918-main` at `origin/main`
`85d9f61d`) — derived: `git worktree add --detach /tmp/wt-2918-head 64af2be1...` and `git worktree add --detach /tmp/wt-2918-main origin/main`, both executed this session, `git -C /tmp/wt-2918-head log -1 --oneline` / `git -C /tmp/wt-2918-main log -1 --oneline` confirming the two SHAs above. I did not read the builder's own record
(`64af2be1650c0dc310cc3352d270548a59edbec3:docs/issue-2916/reports/refactoring-legacy-seam-selection+observability-explorability-b3797400.md`)
until after independently re-deriving every checkable number below, per
the task's "do not read the PR's record as your source of truth"
instruction.

Dispatched 5 parallel verification agents via Workflow (run id
`wf_2fdd2f77-f5c`; canonical: this session's own Workflow tool-call
result and its `w4bbytplm` task-completion notification, both landing in
this session's transcript), each constructing its own evidence rather
than re-reading the builder's claims:

### 1. TTL-consumer enumeration (claim b)

Bounded the population as `git ls-files '*.py'` in both worktrees.
derived: `git ls-files '*.py' | wc -l` in each worktree — result: 202
files on main, 203 on head; derived: `diff <(cd wt-main && git ls-files
'*.py'|sort) <(cd wt-head && git ls-files '*.py'|sort)` — result: exactly
one line differs (`7b2f2de0:test/test_spawn_attempt_halt_report_cadence.py`,
head-only, new in commit `7b2f2de0`). Then grepped that exact
tracked-file list for `ledger_check_and_stamp(` in both trees: derived:
`git ls-files '*.py' | xargs grep -n "ledger_check_and_stamp("` in each
worktree — result: 9 real call sites plus 2 comment-only mentions,
identical in both trees except the one modified call
(`roster.py:720`→`753-754`, the halt-report site). `plumbing.py`,
`spawn.py`, `watchdog.py` are byte-identical between the two worktrees:
derived: `diff /tmp/wt-2918-main/watchdog.py /tmp/wt-2918-head/watchdog.py`,
same for `spawn.py`, `plumbing.py` — result: empty output on all three
(no diff). `RECONCILE_LEDGER_TTL_SEC = 15*60` (plumbing.py:266) and
`SPAWN_ATTEMPTS_RETENTION_SEC = 7*24*3600` (spawn.py:1639) are therefore
byte-identical in both trees by construction of that empty diff.

I then independently re-checked (own tool calls, not the fan-out agent's
report) the 2 call sites the fan-out found beyond the 6 the builder's own
record names (`roster.py:787` `approval-wait-surfaced:{key}:{ts}`,
`watchdog.py:516` `session-resume:{session_id}`):
```
roster.py:817-819 (head, canonical: `sed -n '780,825p' roster.py` in /tmp/wt-2918-head, executed this session):
    if _sp.ledger_check_and_stamp(f"approval-wait-surfaced:{key}:{ts}",
                                   now=now,
                                   ttl=_sp.APPROVAL_WAIT_LEDGER_TTL_SEC):
watchdog.py:516-517 (head, canonical: `sed -n '505,522p' watchdog.py` in /tmp/wt-2918-head, executed this session):
    return _sp.ledger_check_and_stamp(
        f"session-resume:{session_id}", now=now, ttl=_sp.SESSION_RESUME_CLAIM_TTL_SEC)
```
Both already pass an explicit `ttl=` of their own
(`APPROVAL_WAIT_LEDGER_TTL_SEC`, `SESSION_RESUME_CLAIM_TTL_SEC`) — neither
relies on the default `RECONCILE_LEDGER_TTL_SEC`, so both were correctly
out of scope for "call sites that rely on the default ttl and would be
affected by widening it," which is the exact population the builder's
record enumerated. Verdict: claim (b) confirmed — no other dedup channel
is affected.

### 2. Arithmetic bound (claim d), by construction

A fan-out agent wrote a fresh script (`/tmp/my_verify_b.py`, its own new
file, not the PR's test), with one hand-written unresolved halted
`spawn-attempt` entry, driving `roster.spawn_attempt_sweep` across the
full 7-day retention window at multiple tick granularities (15-min, 1s,
60s, 3617s, 100000s). acceptance: `python3 /tmp/my_verify_b.py` — result:
```
exactly 8 spawn_attempt_halt_reported emissions in every tick schedule tested,
landing at attempt_ts + {0, 86400, 172800, 259200, 345600, 432000, 518400, 604800}
```
Boundary check at 1-second resolution around the retention edge (ledger
primed to 6 prior reports): no report at `+604798`s/`+604799`s, the 8th
(final) report fires exactly at `+604800`s, the entry is pruned within
that same call, nothing at `+604801`s onward — no off-by-one at either
end. Verdict: claim (d) confirmed by construction (8 = 604800 // 86400 +
1), not by reading the derivation in the PR.

### 3. Full-suite reproduction by name (test-plan claim)

Ran the real suite on both worktrees (not `git stash`). acceptance:
`cd /tmp/wt-2918-head && python3 -m pytest test/ -q` — result:
```
15 failed, 513 passed, 3 xfailed in 31.81s
```
— exact match to the PR's claimed head count. acceptance: `cd
/tmp/wt-2918-main && python3 -m pytest test/ -q` — result:
```
15 failed, 508 passed, 3 xfailed in 31.54s
```
derived: `comm -23 head_failed_names.txt main_failed_names.txt` and
`comm -13` (both directions) on the sorted `FAILED` lines from the two
runs above — result: both empty; `comm -12` (intersection) — result: all
15 names present in both, i.e. the two 15-failure sets are byte-identical
by name, not merely equal in count. The 513-508=5 passed-count delta is
accounted for by `7b2f2de0:test/test_spawn_attempt_halt_report_cadence.py`
(new-on-head, absent-on-main): derived: `python3 -m pytest
test/test_spawn_attempt_halt_report_cadence.py -v` on head — result: 5
tests, all PASSED, none of the 5 names appear in either FAILED list.
Verdict: test-plan claim confirmed — this specifically rules out the
"two different 15-failure sets producing the same count" failure mode
the task named.

### 4. Both boundaries, constructed live

Resolves-and-prunes (#2511 path): a fan-out agent built an unresolved
halt, swept once, then cleared the blocking condition and swept again,
running the identical script on both worktrees. acceptance: the boundary-1
script on head — result:
```
SWEEP 1 (unresolved): count=1, one "[spawn-attempt] ... spawn halted pre-workspace" line
SWEEP 2 (resolves): count=0, one "halt RESOLVED" line, raw spawn-attempts.jsonl empty immediately after
SWEEP 3: count=0
```
acceptance: `diff` of the boundary-1 output between main and head after
normalizing incidental tmp-dir paths — result: exit 0 (byte-identical) —
this path is genuinely untouched by the PR, not merely claimed untouched.

Never-resolves, first report unchanged (claim e): identical
`attempt_id`/`ts`/`reason`, one sweep at an identical fixed `now` on both
worktrees, captured `print()` output and the `ledger_write` payload.
acceptance: `diff -u b2_main.txt b2_head.txt; md5sum b2_main.txt
b2_head.txt` — result: diff exit 0, identical md5sums
(`93a811f87656853a4836ec9671e5c4e5` both) between main and head. Verdict:
claim (e) confirmed byte-for-byte.

### 5. Standing invariants — all four confirmed

(i) retired role-axis: derived: `git diff 85d9f61d..HEAD -- roster.py
test/test_spawn_attempt_halt_report_cadence.py | grep -inE 'role'` on
head — result: zero matches; derived: `python3 gates/retirement_count.py`
run on both worktrees — result: `roster.py` role-token count unchanged
(16 on main, 16 on head) — no retired-role-axis revival in any form.
(ii) no new bugs: canonical: `sed -n '600,780p' roster.py` on head,
read this session (via the fan-out agent) — `dedup_ttl` is assigned
unconditionally at the top of every loop iteration (`roster.py:686`,
before the outcome-branch split), so it cannot leak a stale value across
`attempt_id`s or start uninitialized on any path. (iii) no overhead
increase: canonical: `diff` of the "no outcome recorded" (#2413) branch
of `spawn_attempt_sweep` between the two worktrees — byte-identical; the
only additions in the diff are two O(1) assignments and passing an
already-computed local as an explicit kwarg — no new I/O, no new loop
nesting. (iv) no monitor/watch breakage: derived: `grep -rln
'spawn_attempt_halt_reported\|spawn_attempt_sweep\|ledger_check_and_stamp'
on-the-record/` on head worktree — result: zero hits inside
`on-the-record/monitors/`; `watchdog.py` only consumes
`spawn_attempt_sweep`'s integer return value (`anomaly_count += ...`),
unaffected by the diff.

## Why

Verified from primary sources rather than the builder's record, per the
task's instruction: a same-session self-review of an arithmetic claim
tends to confirm the author's own derivation by re-reading it, not by
independently re-deriving it — this is the exact failure mode
adversarial review exists to break. canonical: the adversarial-review
skill's "core mechanism" section (Skill tool output, loaded this
session, see skill-verdict line above). Each attack point was therefore
given its own fresh script/worktree rather than re-running or re-reading
the PR's own test suite, so a shared bug in both the fix and its test
could not silently reproduce in both runs. canonical: this session's
Workflow launch (run id `wf_2fdd2f77-f5c`, see "What was done" above) —
5-way parallel fan-out, freelunch STEP-1 tally stated at this record's
opening turn: 5 independent search angles, no non-freezable coupling,
each needing real digging, frozen contract of two worktree paths. I then
did the synthesis and the one loose-thread follow-up (the
`roster.py:787`/`watchdog.py:516` call-site check) myself — synthesis
and judgment are the reviewer's own, not delegable.

## Upstream basis

PR #2918, fix commit `7b2f2de0` (canonical: `git log --oneline -5` in
`/tmp/wt-2918-head`, this session), record-adding commit `64af2be1`
(frontmatter `upstream[0].sha`). Its own record at
`64af2be1650c0dc310cc3352d270548a59edbec3:docs/issue-2916/reports/refactoring-legacy-seam-selection+observability-explorability-b3797400.md`
(not present in this branch's worktree — it lands only on the PR-2918
branch, hence the commit-pinned citation rather than a bare repo path)
was read only after independent re-derivation, specifically to check
whether the builder's own stated enumeration/derivation matched what was
found independently (see "Open findings").

## Open findings

None requiring follow-up. One methodology note, not a code defect: the
builder's record enumerates 6 "call sites that rely on the default ttl"
when rejecting the widen-the-shared-TTL alternative. My independent
enumeration (bounded via `git ls-files`, see "What was done" §1) found 9
real call sites total — 2 more than the builder's list. I checked both by
hand (see §1 code excerpt above): both already pass their own explicit
`ttl=` and were therefore correctly excluded from the builder's stated
population ("sites that rely on the default"). derived: net effect zero
— claim (b) still holds (9 total sites, 2 outside the builder's stated
scope but correctly excluded, 7 matching the builder's own 6 plus the
1 changed site = builder's enumeration was accurate for what it claimed
to cover). Flagging only because the task explicitly asked how the
enumeration was bounded.

## Bottom line

All five PR claims (a)-(e) and all four standing invariants — see the 5
numbered subsections under "What was done" above, each with its own
acceptance/derived tag and executed command — are confirmed by
independent construction; no functional defects found. Per-unit raw
command output and full agent transcripts are preserved in this
session's Workflow journal (canonical: `wf_2fdd2f77-f5c` journal, this
session's own run) — nothing above was taken at the builder's word
without a from-scratch reproduction.

## Next steps

None — `loop_state: landed`. This is a review-only deliverable; per the
task, findings are reported here and no code changes are made to PR
#2918.
