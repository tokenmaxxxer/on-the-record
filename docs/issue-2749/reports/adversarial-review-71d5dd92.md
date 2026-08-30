---
issue: 2749
role: adversarial-review-71d5dd92
author: adversarial-review-71d5dd92
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2844's own deliverable
code_under_review: roster.py:_session_looks_real, spawn.py:self_update_pull_cli, watchdog.py:watchdog_freshness_check, on-the-record/hooks/self-update.sh
type: verification
breaking: false
verdict: pass-with-disclosed-scope — both round-1 blocking findings independently reproduce as addressed (recycled-pid wedge closed in both directions; watchdog.py route confirmed still open, `Part of #2749` trailer is the correct shape); one residual pid-reuse gap found by this round's own probing that the PR's record already discloses as an open finding rather than hiding it (see Open findings)
loop_state: landed
upstream:
  - path: docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md
    sha: 66526212ebfd571400a180c7f4fbf152f8760afd
  - path: docs/issue-2749/reports/adversarial-review-28904fd2.md
    sha: 37549eea3fe4f096f836ddbf026a9d9a754b0fde
  - path: spawn.py
    sha: 66526212ebfd571400a180c7f4fbf152f8760afd
  - path: roster.py
    sha: 66526212ebfd571400a180c7f4fbf152f8760afd
  - path: watchdog.py
    sha: 66526212ebfd571400a180c7f4fbf152f8760afd
---

# issue-2749 — adversarial-review-71d5dd92 record

## What was done

Independent, structurally separate verification of PR #2844 (issue #2749
round 2), which supersedes the closed PR #2823 and carries that PR's work
plus three fixes made in response to round 1's independent review (PR
#2831). This session had no access to the builder's record while
re-deriving; every claim below is checked from scratch against a fresh
`git worktree` (`/tmp/wt2844`, PR tip
`66526212ebfd571400a180c7f4fbf152f8760afd`) and a baseline worktree of
`origin/main` (`/tmp/wt_main`), both removed after use.

canonical: `gh pr view 2844 --repo tokenmaxxxer/on-the-record` — result:
state OPEN, head `issue-2749/silent-failure-audit-e9b54ddf`, base `main`,
+1044/-11.

**Round-1 finding 1 (recycled-pid wedge) — CONFIRMED FIXED, both
directions independently reproduced live.** `roster.py` gained
`_session_looks_real(pid, work)` (identity-confirms via
`/proc/<pid>/cwd` against the roster entry's recorded `work`, falling
back to bare-alive when `/proc`/`work` is unavailable — same pattern as
the pre-existing `_watcher_looks_real()`), and
`spawn.py:self_update_pull_cli()`'s `live_roster` computation now calls
it instead of bare `roster._alive()`. This session wrote its own
reproduction script (not the PR's test file) exercising both directions
against scratch git fixtures:

- Case A — a roster entry whose `work` is the checkout but whose `pid`
  belongs to an unrelated live process with a different `cwd` (what pid
  reuse looks like from the roster's point of view):
  `derived: python3 indep_check.py` (Case A) — result:
  ```
  rc=0 pull-check='pull=ok'
  HEAD advanced: True
  ```
  the pull is no longer blocked.
- Case B — the direction that matters more: a genuinely live session,
  same `pid`, `cwd` matching the registered `work`:
  `derived: python3 indep_check.py` (Case B) — result:
  ```
  self-update 거부: 살아있는 세션이 있다고 판단함(신원 확인 포함) —
    roster      issue-2749/implementation  pid 417432  work /tmp/tmpsydv1fir/checkout
  rc=1 pull-check='pull=refused:1-live-sessions'
  HEAD advanced: False
  ```
  a genuinely live session still blocks the pull, and the refusal names
  the exact pid and workspace it believes is live so a human can check
  the claim by hand (`readlink /proc/417432/cwd`).

The fix did not create a false-negative in the opposite direction: a
live session is not misclassified as dead.

**Round-1 finding 2 (reflog-signature mismatch / `watchdog.py` route) —
CONFIRMED STILL OPEN, not closed by this delivery, and the PR's own
trailer correctly reflects that.** The task framing for this round
stated "watchdog.py is now touched" — checked and found **false as a
code claim**: `derived: git diff origin/main...HEAD -- watchdog.py` (PR
worktree) — result: 0 lines changed. `watchdog.py` is only *referenced
in prose* inside the delivery's own record (canonical: PR #2844 branch,
path `docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
`66526212ebfd571400a180c7f4fbf152f8760afd` — untracked in this session's
own branch), not edited. This session independently reproduced, live,
that the route is in fact still open at the code level, with a session
genuinely registered as live in the roster:

`derived:` a standalone script (this session's own, not the PR's test
suite) that clones a scratch origin/checkout pair, registers a
`sleep`-backed process in the roster with `work` == the checkout (an
identity `_session_looks_real()` would accept as genuinely live),
advances the scratch origin, then calls
`watchdog.watchdog_freshness_check(startup_head, cwd=checkout)` directly
— result:
```
watchdog_freshness_check -> False '[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 (시작=80fae30e400c 현재=59f437c84a98) — 재기동 필요'
reflog:
 59f437c HEAD@{0}: merge origin/HEAD: Fast-forward
80fae30 HEAD@{1}: clone: from /tmp/tmptstbvz4a/origin.git
```
The function takes no roster/liveness argument at all, so the registered
live session has zero effect on its outcome. The merge executes
unconditionally and reproduces the exact founding reflog string (`merge
origin/HEAD: Fast-forward`) the issue was filed on. `spawn.py
self-update`'s new gate is irrelevant to this path —
`watchdog_freshness_check()` never calls it.

`derived: gh api repos/tokenmaxxxer/on-the-record/pulls/2844 --jq
'.body'` — result: `Part of #2749.` (plus the auto-generated relay
preamble) — not `Closes`/`Fixes`/`Resolves`, not `Advances`. Per
`hook-contract.md`'s `pr-preflight.sh` note, `Part of #<n>` is one of
the two accepted non-closing forms for a deliberate partial delivery,
and the watchdog reproduction directly above confirms it is the correct
choice here — the issue's founding symptom still reproduces through
`watchdog.py`, so landing `Closes` would have been the exact
silent-failure shape #2749 exists to remove.

**Round-1 finding 3 (nothing invokes `spawn.py self-update`; `.pull-check`
written but never read) — CONFIRMED STILL TRUE, and the record's claim
about it is backed by intention, not mechanism.** Re-ran the same greps
this round: `derived: grep -n '"self-update"' spawn.py` — result: only
the CLI dispatch line (`if a.role == "self-update": return
self_update_pull_cli()`), no other caller anywhere in the tree.
`derived: grep -rn "pull-check" *.py on-the-record/hooks/*.sh` — result:
only `self-update.sh`'s own writer and
`self_update_pull_cli()`'s `_pull_check_write()` touch the file; nothing
reads it back (not `spawn.py ps`, not watchdog health output, not any
other CLI path). canonical: PR #2844 branch,
`docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
`66526212ebfd571400a180c7f4fbf152f8760afd` (untracked in this session's
own branch), section "Why the staleness-ceiling question (item 3) is
answered here, not fixed," states this plainly: the checkout's staleness
ceiling moved from "at most one `SessionStart` firing" to "unbounded
until a human or the orchestrator remembers to run `spawn.py
self-update`," and that this is an accepted, disclosed trade — not a fix
— logged as an open finding with a named resolution path
(scheduled/event-driven trigger, or surfacing `.pull-check` in `spawn.py
ps`), deliberately deferred pending weighing against #910 finding #4 and
#2670. This session's own probing (the two `grep` commands above, re-run
independently rather than trusted from the record) confirms the claim:
**the checkout advances today only by a human typing `spawn.py
self-update`; nothing schedules or surfaces it.** That is an honest
disclosure, not a hidden gap — but it is intention, not a mechanism, and
any future round that wants to close #2749 needs to either build that
mechanism or argue explicitly that manual-only is the final answer.

**Residual finding this round located, not raised by the task framing:**
the same recycled-pid wedge round 1 found in the roster path also has a
live, independently-reproduced path through
`roster._claim_only_live_sessions()`, which `self_update_pull_cli()`
also consults and which still uses bare `_alive()` (`roster.py:128`) —
not `_session_looks_real()`. Reproduced live: a stale `.spawn-claim` file
naming a pid the OS has recycled to an unrelated live process wedges
`self_update_pull_cli()` exactly like the fixed roster-path bug used to:

`derived:` a standalone script (this session's own) registering only a
`.spawn-claim` file (no roster entry) with a recycled pid, then calling
`spawn.self_update_pull_cli()` — result:
```
self-update 거부: 살아있는 세션이 있다고 판단함(신원 확인 포함) —
  claim-only  pid 425070  work: /tmp/tmpn0pnj57w/checkout
rc: 1 HEAD advanced: False
```
This is **not a hidden defect** — canonical: PR #2844 branch,
`docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
`66526212ebfd571400a180c7f4fbf152f8760afd` (untracked in this session's
own branch)'s own Open findings section names this exact function and
line (`roster.py:93-133`, bare `_alive()` at `roster.py:128`) as a known,
narrower residual gap, with the reasoning for why it was left (a
`cwd`-based identity check doesn't work for the fork-wrapper pid a claim
file records — its `cwd` is the orchestrator's own `cwd` at spawn time,
not the workspace). This session's own reproduction directly above
confirms that reasoning holds and that the gap is real and
live-reproducible — matching, not contradicting, the record's own
disclosure.

**Four standing invariants, independently re-derived:**

- **No new role axis.** `derived: git show origin/main:spawn.py | grep -c
  "a\.role"` — result: `52` (matches the task framing's stated
  pre-existing-convention baseline). `derived: grep -c "a\.role"
  spawn.py` (PR worktree) — result: `53` — exactly the one new `if
  a.role == "self-update":` dispatch line (`derived: 53 - 52 = 1`), the
  same convention as the other 52 pre-existing `a.role ==` dispatch
  lines. No code elsewhere in the diff reintroduces a role/skill axis;
  the only other "axis" hits in the PR diff are inside the record's own
  prose (grepped and confirmed non-code).
- **No new bug — failing-test-name SETS.** `derived: python3 -m pytest -q`
  in both worktrees, `FAILED` lines sorted and diffed — origin/main:
  `16 failed, 572 passed, 3 xfailed`; PR tip: `16 failed, 580 passed, 3
  xfailed`. `derived: diff /tmp/main_failed.txt /tmp/pr_failed.txt` —
  result: no output (byte-identical 16-name sets). The +8 passed matches
  8 new test cases added on the PR branch (untracked in this session's
  own branch): `derived: python3 -m pytest
  test/test_self_update_pull_gate.py
  test/test_self_update_working_tree_untouched.py -q` (PR worktree) —
  result: `8 passed`.
- **No overhead increase, on the hook's own path.** `derived: time ( for i
  in $(seq 1 10); do bash on-the-record/hooks/self-update.sh; done )` in
  a copy of each worktree, warmed once first — origin/main: `real
  0m5.437s`; PR tip: `real 0m5.453s` (≈0.3% delta, within run-to-run
  noise, not a directional increase).
- **Monitor/watch machinery unbroken and not quieter.** `derived: python3
  -m pytest -q test/test_watchdog_heartbeat_noise.py
  test/test_ps_live_reliability.py test/test_roster_skill_field.py` —
  result: `18 passed`. `derived: grep -n "roster_ps\|_watcher_looks_real"`
  against the PR diff — result: `_watcher_looks_real()` and `roster_ps()`
  are not touched by any hunk; only a new, adjacent
  `_session_looks_real()` function was added next to them. No output
  path was removed or narrowed.

**Live before/after of the hook's own behavior** (issue acceptance
criterion 2 — "start a session, merge a hook change, and show what the
session observes — before and after the fix"): against a scratch
checkout one commit behind a scratch origin, `bash
on-the-record/hooks/self-update.sh` on the fixed hook
(`TOKENMAXXXER_CHECKOUT` pointed at the scratch checkout) —
`derived: git rev-parse HEAD` before and after — result:
```
before=32f263ac2a5bd28fdfbe8dd48c08bf762674bb78 after=32f263ac2a5bd28fdfbe8dd48c08bf762674bb78 unchanged=yes
pull-check: pull=deferred:1-behind-origin
```
HEAD unchanged, `.pull-check` records the deferred state. On
`origin/main`'s hook (still `git pull --ff-only` unconditionally,
`derived: sed -n '37,47p' on-the-record/hooks/self-update.sh` on the
main worktree — result: `pull_err="$(git -C "$CHECKOUT" pull -q --ff-only
2>&1)"` at line 42), the same scenario advances HEAD immediately — this
is the exact behavior issue #2749 was filed against. **Staleness still
fails loudly, not silently** (acceptance criterion 3): the fixed hook
always writes `.pull-check`'s state to disk
(`pull=deferred:<n>-behind-origin` here), visible to any subsequent
inspection, rather than silently proceeding on stale code or silently
discarding the outcome.

skill-verdict: adversarial-review — applied: invoked; this whole session
follows the protocol as the structurally independent evaluator of PR
#2844 — re-derived every claim from raw commands against fresh
worktrees/scratch git fixtures rather than restating the subject
record's own citations, and specifically hunted for a failure in the
opposite direction (a genuinely live session misread as dead) alongside
the fix being verified.
skill-verdict: work-in-english — applied: invoked; this record, all
scratch reproduction scripts, and PR/commit text are in English; the
final summary to the user is in Korean per the user's own language.

## Why

Round 2's task was to check whether round 1's three findings actually
landed, and whether each fix created a failure in the opposite
direction. canonical: the commands under "What was done" above show the
approach taken was to never trust the delivering record's own
citations — every command was re-run from scratch in this session, most
against newly written scratch git fixtures rather than reusing the PR's
own test file verbatim (the two `indep_check.py` cases and the three
standalone `watchdog_freshness_check`/claim-only-path scripts were
authored fresh by this session, not copied). Where this session's
independent reproduction agreed with the delivering record's own claims
— derived: all three round-1 findings and all four standing invariants
documented under "What was done" above — that is reported as confirmed,
not merely repeated. Where this session found something the delivering
record's Open findings section already named — canonical: PR #2844
branch, `docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
`66526212ebfd571400a180c7f4fbf152f8760afd` (untracked in this session's
own branch), its Open findings entry for
`roster._claim_only_live_sessions()` — that is reported as an
independently-verified confirmation of an existing disclosure, not a new
hidden defect: a review that reports every disclosed gap as if newly
discovered would misrepresent how honest the underlying record already
was.

## What did not work

None.

## Upstream basis

- PR #2844 branch, `docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`
  (untracked in this session's own branch), sha
  `66526212ebfd571400a180c7f4fbf152f8760afd` — PR #2844's own delivery
  record, the subject of this verification.
- `docs/issue-2749/reports/adversarial-review-28904fd2.md` (round-1
  independent verification, PR #2831, sha
  `37549eea3fe4f096f836ddbf026a9d9a754b0fde`) — source of the three
  findings this round checks the resolution of.
- `spawn.py`, `roster.py`, `watchdog.py` (sha
  `66526212ebfd571400a180c7f4fbf152f8760afd`, the PR tip this session
  checked out into `/tmp/wt2844`) — independently exercised, not read
  only.

## Open findings

- **`roster._claim_only_live_sessions()` still uses bare `_alive()`
  (`roster.py:128`)**, so a recycled claim-file pid can still wedge
  `self_update_pull_cli()` indefinitely via the claim-only path, even
  though the roster-path version of the same bug is fixed.
  `derived:` this session's own standalone script (registers a
  `.spawn-claim` file with a recycled pid, no roster entry, then calls
  `spawn.self_update_pull_cli()`) — result:
  ```
  self-update 거부: 살아있는 세션이 있다고 판단함(신원 확인 포함) —
    claim-only  pid 425070  work: /tmp/tmpn0pnj57w/checkout
  rc: 1 HEAD advanced: False
  ```
  canonical: PR #2844 branch,
  `docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
  `66526212ebfd571400a180c7f4fbf152f8760afd` (untracked in this session's
  own branch) already discloses this as a known, narrower residual with
  a stated reason it was left (the fork-wrapper pid a claim file records
  has no workspace-matching `cwd` to check against) — this review's own
  reproduction above confirms that reasoning holds rather than finding a
  hole in it. Resolution path unchanged from the delivering record: a
  wedge-safe identity signal for the fork-wrapper pid specifically, not
  designed yet.
- **`watchdog.py:watchdog_freshness_check()` still unconditionally
  advances the checkout** every tick with no live-session gate.
  `derived:` this session's own standalone script (registers a
  `sleep`-backed process in the roster with `work` == the checkout,
  advances the scratch origin, calls
  `watchdog.watchdog_freshness_check(startup_head, cwd=checkout)`
  directly) — result:
  ```
  watchdog_freshness_check -> False '[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 (시작=80fae30e400c 현재=59f437c84a98) — 재기동 필요'
  reflog:
   59f437c HEAD@{0}: merge origin/HEAD: Fast-forward
   80fae30 HEAD@{1}: clone: from /tmp/tmptstbvz4a/origin.git
  ```
  this is the exact reflog string #2749's founding evidence cites,
  produced with a genuinely-live session registered and ignored.
  Resolution path unchanged from the delivering record: a follow-up
  under #2749 that re-derives the watchdog's staleness signal from the
  fetched origin ref instead of a merged local HEAD, before `Closes
  #2749` can be used.
- **Nothing schedules or surfaces `spawn.py self-update`/`.pull-check`.**
  `derived: grep -n '"self-update"' spawn.py` — result: only the CLI
  dispatch line, no other caller. `derived: grep -rn "pull-check" *.py
  on-the-record/hooks/*.sh` — result: only the writer sites, nothing
  reads it back. canonical: PR #2844 branch,
  `docs/issue-2749/reports/silent-failure-audit-e9b54ddf.md`, sha
  `66526212ebfd571400a180c7f4fbf152f8760afd` (untracked in this session's
  own branch) states this is an accepted trade for now, not a fix —
  logged here so a future round doesn't have to re-derive that the gap
  is real.

## Next steps

None from this session — `loop_state: landed`. This is a verification
round; the three open findings above are handed off, not owed by this
session.
