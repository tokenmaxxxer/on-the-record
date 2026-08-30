---
issue: 2749
role: adversarial-review-28904fd2
author: adversarial-review-28904fd2
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2823's deliverable
loop_state: landed
upstream:
  - path: docs/issue-2749/reports/silent-failure-audit-bbfffc81.md
    sha: a04cd4d298803d9060d0279fb361d0a00de2b094
  - path: on-the-record/hooks/self-update.sh
    sha: a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2
  - path: spawn.py
    sha: a4e0e6cbe58b2a9dea1ec77312b93f610c962ef2
---

# issue-2749 — adversarial-review-28904fd2 record

## What was done

Independently re-derived PR #2823's (`issue-2749/silent-failure-audit-bbfffc81`,
tip `e333add99cdd3aff5aa3fa186bd5b96020820738`, open against `main`) claims
against a fresh `git worktree` and scratch git fixtures — attacking the
refusal logic, the `.pull-check` state machine, the freshness question, and
the out-of-scope `watchdog.py` finding, rather than restating the subject
record's own numbers.

canonical: `gh pr view 2823 --json body` — this session's own live read;
`gh issue view 2749` — this session's own live read.

**Top finding — the reflog evidence the issue was filed on points at
`watchdog.py`, not at `self-update.sh`.** Issue #2749's Ask cites: `git
reflog` showing repeated `merge origin/HEAD: Fast-forward` entries while
sessions were running. `self-update.sh`'s old code (the mechanism this PR
fixes) ran `git pull -q --ff-only`, not `git merge ... origin/HEAD`.
`watchdog.py:1293-1298`'s still-unfixed `watchdog_freshness_check()` runs
`git fetch` then `git merge --ff-only --quiet origin/HEAD` on every tick it
hasn't already fetched, gated only on "already fetched this tick" — never on
whether any *other* session is live:

```
canonical: watchdog.py:1293-1298 (unmodified by this PR)
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
```

Reflog reproduces the exact message format each command actually produces:

```
derived: (scratch bare remote + clone, one commit behind) git pull -q
--ff-only; git reflog -1 — result:
  d51f74f HEAD@{0}: pull -q --ff-only: Fast-forward
derived: (same scratch setup, next commit behind) git fetch -q; git merge
--ff-only -q origin/HEAD; git reflog -1 — result:
  41655c5 HEAD@{0}: merge origin/HEAD: Fast-forward
```

`self-update.sh`'s old pull structurally cannot have produced the literal
`merge origin/HEAD: Fast-forward` reflog line the issue quotes as its
founding evidence — `watchdog.py`'s merge command is the only one of the
two mechanisms whose reflog signature matches. The PR's own "Open findings
#1" candidly identifies `watchdog_freshness_check()`'s unconditional
fetch+merge as unfixed and out of scope, but frames it as "plausibly a
second, independent contributor" — the reflog-message match found here is
stronger than that: a positive match for the mechanism the issue's own
evidence names, and a mismatch for the mechanism this PR closes. The hole
issue #2749 was filed to close is very plausibly still open, via a
different, undisclosed-strength route the PR's Open-findings section
already flags but does not fix. This does not mean the PR's fix is wrong
to make — `self-update.sh`'s unconditional pull was a real,
independently-confirmed hazard on its own (below) — but the PR should not
be read as having closed the specific hazard the issue's own reflog
evidence points at.

**Refusal logic (`self_update_pull_cli()`, `spawn.py:3273`), attacked live**
against five roster conditions (isolated fixture, `spawn._workspace_base()`
monkeypatched to an empty dir so this machine's own live sessions don't
leak into the test):

```
derived: scratch harness importing spawn.py, ROSTER pointed at each
fixture in turn, spawn._workspace_base() monkeypatched empty — result:
 missing roster (legit empty)        -> proceeds to git pull (correct)
 corrupt/unparsable roster           -> "pull=refused:roster-unreadable:<reason>", exit 2 (correct, strict)
 dead/stale pid entry                -> not counted live, proceeds (correct)
 recycled pid (unrelated live proc)  -> "pull=refused:1-live-sessions", exit 1 (see finding below)
 permission-denied roster            -> "pull=refused:roster-unreadable:<reason>", exit 2 (correct, strict)
```

Every ambiguous case (unreadable, unparsable, permission-denied, claim-scan
failure) answers in the strict/blocking direction, never the permissive
one — good, since a wrong permissive answer here is the worse failure mode
(pulling under a live session). But the recycled-pid case exposes a real
gap: `self_update_pull_cli()` reuses `roster._alive()` (bare
`os.kill(pid, 0)`), not `roster._watcher_looks_real()`, which exists in the
same file specifically to catch "pid is alive but reassigned to an
unrelated process":

```
canonical: roster.py:206-218
def _alive(pid: int) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
```

```
canonical: roster.py:175,188-189 (_watcher_looks_real, docstring cites
issue #488 for exactly the pid-reassignment hazard class)
def _watcher_looks_real(pid: int, issue: int | None,
                         skill: str | None = None) -> bool:
    if not _sp._alive(pid):
        return False
```

`_alive()` alone cannot tell a live session's own pid from an unrelated
process that happens to have been assigned the same number after the
session crashed without `roster_remove()` running. Traced the recovery
path:

```
canonical: watchdog.py:1670-1673
                    if not e.get("expects_pr") and issue_n is None:
                        # 관찰할 것이 없다(PR 도 안 기대하고 이슈도 없음) —
                        # 지금 바로 은퇴시킨다.
                        _sp.roster_remove(key)
```

`roster_remove()` only fires once a per-entry `dead_health` check (also
built on the `_alive()`-family liveness the code above gates on) confirms
the pid is dead — so a recycled pid fools the watchdog's own pruning the
same way, and the stale entry is never auto-removed. Net effect: a session
that crashes without cleanup, followed by pid reuse on this host before
anyone runs `spawn.py self-update`, wedges the checkout's advance path
indefinitely — the refusal message ("살아있는 세션이 있다 — roster ... pid
...") reads as a confirmed live session, not as "same pid number,
unconfirmed identity," so an operator reading it has no signal that the
block might be stale. `_watcher_looks_real()`'s cmdline check
(`"watch" not in parts`) is not directly reusable for a generic session pid
without generalizing it, so this is a real gap, not a simple call-site
swap — but it is a gap the same file already has the concept for and
doesn't apply here.

**`.pull-check` state machine — all four states reproduced live**, each
from an isolated scratch git remote/checkout pair, driving the actual
shipped `on-the-record/hooks/self-update.sh` (`git show
a4e0e6cb:on-the-record/hooks/self-update.sh`):

```
derived: (scratch remote+checkout) checkout current -> bash self-update.sh
  -> result: pull=ok
derived: (scratch remote+checkout, remote advanced 1 commit by a second
  clone+push) bash self-update.sh -> result: pull=deferred:1-behind-origin
  (git log -1 on the checkout confirms HEAD unchanged, still the old commit)
derived: (scratch checkout, git branch --unset-upstream) bash
  self-update.sh -> result: pull=unknown:fatal: 'trunk' 브랜치에 대해
  업스트림을 설정하지 않았습니다...
derived: (scratch checkout, git remote set-url origin <nonexistent path>)
  bash self-update.sh -> result: pull=failed:fetch:fatal: '...' does not
  appear to be a git repository...
```

All four distinguishable from each other and from `ok`; no path writes
`pull=ok` without having actually confirmed `rev-list --count HEAD..@{u}`
returned `0`, and no path silently drops a fetch or rev-list failure —
confirms the PR does not repeat #2792's success-flag-paired-with-absent-data
defect class.

One thing worth naming plainly, not a defect in this PR but relevant to how
"loud" the failure states really are:

```
canonical: lifecycle.py:709-713
_HARNESS_NOISE_BASENAMES = frozenset({
    ".pull-check", ".shallow-check", ".orchestrate-greeted",
    ".warrant-hunt.count", ".warrant-hunt.lock",
```

derived: `grep -rn "pull-check" --include=*.py --include=*.sh .` outside
`test/` — result: only the writer sites in `spawn.py`/`self-update.sh` and
this one noise-list entry; nothing else in the tree reads the file.
`.pull-check` is only ever consumed to keep it out of dirty-tree detection.
Nothing prints its content at session start, nothing in `spawn.py ps` or
any monitor surfaces `pull=deferred:N`/`unknown`/`failed` proactively. This
is unchanged from the pre-#2749 behavior (#910 already accepted a file
marker as the bar for "not silently dropped," not a proactive alert), so it
is not a regression this PR introduces — but it means "fails loudly" here
means "is inspectable if you go look," identical to before, not "surfaces
itself."

**Staleness question — what depended on per-firing freshness, and what
happens to it now:**

```
canonical: on-the-record/hooks/hooks.json SessionStart entry (matcher:
None; two commands: fail-open-wrapper.sh self-update.sh, fail-open-wrapper.sh
session-role-bind.sh)
derived: python3 -c "import json; d=json.load(open('on-the-record/hooks/hooks.json'));
print([h['command'] for e in d['hooks']['SessionStart'] for h in e['hooks']])"
— result: self-update.sh listed first, fires on every SessionStart firing
(startup/resume/clear/compact/fork per the event's own matcher-value set)
```

Before this PR, every one of those firings re-pulled the shared checkout
(`git -C "$CHECKOUT" pull -q --ff-only`, the code this PR removes — see the
diff quoted in the top finding above), so the hook chain for the rest of
that firing and every later hook firing in the same session ran whatever
code had just landed on `origin` moments earlier — the mechanism the issue
was filed against, not a property worth preserving on its own terms. After
this PR, nothing auto-invokes `spawn.py self-update`:

```
derived: grep -rn "self-update\|self_update" --include=*.py --include=*.sh
--include=*.json . — result (outside test/): spawn.py:2283-2284 (the
argparse dispatch line itself) and spawn.py:3259-3321 (the CLI function
body) only; no cron entry, no watchdog-tick call, no zero-session trigger
anywhere in the tree invokes it.
```

So the checkout's working tree now only ever advances when a human
explicitly types the command, with no reminder mechanism and no automatic
firing at the "zero sessions" moment the discipline is named after.
Combined with the previous finding (nothing surfaces accumulated
`pull=deferred:N-behind-origin` proactively), the practical risk this
trades into is: the checkout can now drift arbitrarily far behind `origin`
with nothing prompting a human to notice, where before it drifted at most
one hook-firing's worth. This is very close to, though not identical to,
the exact anti-pattern issue #2749's own "must not" clause forbids ("a flag
the orchestrator must remember to set") — the PR's answer converts an
implicit habit (#2670's manual discipline) into an explicit command, which
is real progress, but the command itself has no scheduling or nudge behind
it, so remembering is still the only thing standing between a fix landing
on `origin` and it ever reaching a live checkout.

**Four standing invariants, independently re-run** (fresh `git worktree` of
`e333add9` vs. `main`, not copied from the subject record):

```
derived: git diff main..e333add9 -- on-the-record/hooks/self-update.sh spawn.py \
  | grep -inE '^\+.*\brole\b' — result: one hit, "+    if a.role == \"self-update\":"
  — the pre-existing argparse dispatch attribute pattern (identical shape to
  the untouched "a.role == \"ps\"" line immediately above it), not a
  reintroduction of the retired role-axis noun. No return confirmed.
```

```
derived: python3 -m pytest -q on main (worktree) — result: 16 failed, 572 passed, 3 xfailed
derived: python3 -m pytest -q on e333add9 (worktree) — result: 16 failed, 579 passed, 3 xfailed
derived: diff <(main FAILED lines, sorted) <(e333add9 FAILED lines, sorted)
  — result: identical, empty diff. 579-572=7, exactly the two new test
  files' own count (7 `def test_`).
```

```
derived: 10x on-the-record/hooks/self-update.sh (main) vs 10x (e333add9),
  both against a checkout already current, same host — result: real
  0m0.122s both runs. No overhead increase (own timing, not the PR's
  quoted 0.494s/0.438s figures, but the same conclusion).
```

```
derived: python3 -m pytest test/test_self_update_pull_gate.py \
  test/test_self_update_working_tree_untouched.py -q (e333add9)
  — result: 7 passed
derived: python3 -m pytest test/test_watchdog_heartbeat_noise.py \
  test/test_ps_live_reliability.py -q -m "not slow" (e333add9)
  — result: 8 passed. Neither file is in the 16-item failing set above —
  monitor/watch machinery unbroken and not quieter.
```

## Why

The task was to independently verify PR #2823 as its own structurally-blind
evaluator, per the loaded `adversarial-review` skill (Step 1-3: no shared
context with the builder session, re-derive rather than restate). The
refusal-logic attack targeted the three explicit failure modes the task
named (stale, unreadable, recycled-pid roster) because a session-liveness
gate that answers wrong in either direction is worse than the bug it
replaces — permissive-wrong pulls under a live session (data-loss-adjacent),
strict-wrong wedges the checkout forever (availability). Both were
reproduced live rather than reasoned about abstractly, using a scratch
harness that monkeypatches `spawn._workspace_base()` so this machine's own
concurrently-running sessions (several were live during this review) could
not contaminate the isolated roster fixtures. The reflog-signature check on
the "open finding" was added because the PR's own record treats
`watchdog.py`'s hole as "plausibly a contributor" without checking whether
it is in fact a stronger match than the mechanism actually fixed — the
literal reflog message strings, reproduced from both commands against real
scratch git repos, settle that question rather than leaving it as
speculation on either side.

## What did not work

None.

## Upstream basis

- `a04cd4d2:docs/issue-2749/reports/silent-failure-audit-bbfffc81.md`
  (PR #2823's subject record; not merged to `main`, lives only on branch
  `issue-2749/silent-failure-audit-bbfffc81` — `canonical: git show
  a04cd4d2:docs/issue-2749/reports/silent-failure-audit-bbfffc81.md`, read
  live this session); every material command/result it claims was
  independently re-run above (fresh worktrees, fresh scratch git fixtures)
  rather than copied.
- `a4e0e6cb:on-the-record/hooks/self-update.sh`,
  `a4e0e6cb:spawn.py`, `a4e0e6cb:docs/specs/enforcement-boundary.md` — the
  PR's actual code diff, read directly via `git show`/`git diff` against
  `main` this session.
- `roster.py` (pre-existing, unmodified by this PR) — read directly for
  `_alive()` (`roster.py:206-218`), `_watcher_looks_real()`
  (`roster.py:175-203`), `_roster_load_checked()` (`roster.py:61-90`),
  `_claim_only_live_sessions()` (`roster.py:93-133`) — the liveness
  primitives `self_update_pull_cli()` reuses.
- `watchdog.py` (pre-existing, unmodified by this PR) — read directly for
  `watchdog_freshness_check()` (`watchdog.py:1277-1317`), the mechanism the
  subject record's own "Open findings #1" names as unfixed.
- `gh issue view 2749` / `gh pr view 2823 --json ...` — read live this
  session, for the issue's actual acceptance text and the PR's actual diff
  and commit list.

## Open findings

1. derived: git pull -q --ff-only against a scratch checkout one commit
behind a scratch bare remote; git reflog -1 — result:
```
  d51f74f HEAD@{0}: pull -q --ff-only: Fast-forward
```
derived: git fetch -q; git merge --ff-only -q origin/HEAD against the same
kind of scratch checkout; git reflog -1 — result:
```
  41655c5 HEAD@{0}: merge origin/HEAD: Fast-forward
```
canonical: watchdog.py:1293-1298 (quoted in full in "What was done" above)
— its merge target is literally `origin/HEAD`, matching the issue's own
quoted reflog line; self-update.sh's removed `git -C "$CHECKOUT" pull -q
--ff-only` (a4e0e6cb^:on-the-record/hooks/self-update.sh:42) cannot produce
that message format, confirmed by the first `derived:` run above.

**Verdict: CONFIRMED — reflog-signature mismatch.** The reflog evidence
issue #2749 was filed on matches `watchdog.py`'s still-unfixed merge
command, not `self-update.sh`'s old `pull --ff-only`. Resolution path: the
PR's own recommended follow-up (route `watchdog_freshness_check()`'s merge
through the same zero-live-session gate `self_update_pull_cli()` now uses)
is the correct fix, and given this finding, is not merely a nice-to-have —
without it the specific hazard the issue's own evidence names is still
live.

2. derived: scratch harness, roster fixture `{"issue-1/foo": {"pid":
os.getpid(), "work": "/nonexistent", "issue": 1}}` (this python process's
own pid, guaranteed alive but not the session the entry claims),
`spawn.self_update_pull_cli()` called directly — result:
```
self-update 거부: 살아있는 세션이 있다 —
  roster      issue-1/foo  pid 4030348
exit=1, pull-check: pull=refused:1-live-sessions
```
canonical: roster.py:206-218 (`_alive()`, quoted in full in "What was
done" above) — no cmdline identity check, unlike `_watcher_looks_real()` in
the same file (`roster.py:175,188-189`, also quoted above); recovery path
traced via `watchdog.py:1670-1673` (also quoted above) — pruning is gated
on the same `_alive()`-family check.

**Verdict: CONFIRMED — recycled-pid indefinite wedge.**
`self_update_pull_cli()`'s refusal gate can wedge indefinitely on a
recycled pid, with no self-healing path and no signal in the refusal
message that the block might be stale. Resolution path: generalize
`_watcher_looks_real()`'s cmdline-identity check (or a cheaper
process-start-time comparison against the roster entry's own recorded
timestamp, if one exists) to the roster-pid liveness check
`self_update_pull_cli()` and the watchdog's own pruning both use — a shared
fix, not scoped to this PR's diff alone.

3. derived: grep -rn "self-update\|self_update" --include=*.py
--include=*.sh --include=*.json . — result (outside test/):
spawn.py:2283-2284, spawn.py:3259-3321 only; nothing else in the tree
invokes the command.

Not a defect in this PR's diff, but a materially reduced safety margin
worth a named owner: with the automatic pull removed and no automation
ever invoking `spawn.py self-update`, the checkout's staleness ceiling
changed from "at most one hook firing" to "unbounded until a human
remembers," and nothing proactively surfaces the accumulated
`pull=deferred:N` drift (grep result quoted under "`.pull-check` state
machine" above). Resolution path: either a periodic check (e.g. the
watchdog tick, once finding 1 routes its own merge through the
live-session gate, could also print/alert on an accumulated `deferred:N`
past some threshold) or an explicit decision, recorded somewhere an
operator will see it, that unbounded staleness is the accepted tradeoff.

## Next steps

None — `loop_state` is `landed`.

derived: every acceptance command and standing invariant above was
executed live this session against fresh worktrees/scratch fixtures (not
copied from the subject record). Three open findings survived independent
verification: one (the reflog-signature mismatch) materially changes how
the PR's central claim should be read, the other two (recycled-pid wedge,
unbounded post-fix staleness) are real gaps in the replacement mechanism's
own robustness. The PR's four standing-invariant claims (no role-axis
return, identical failing-test-name sets, no overhead increase,
monitor/watch machinery unbroken) all independently reproduced clean
(quoted under "Four standing invariants" above).

skill-verdict: adversarial-review — applied: invoked; loaded the skill's
SKILL.md before treating either the subject PR's record or the task's own
framing as settled — every command above was run fresh against isolated
worktrees/scratch git fixtures this session, and the reflog-signature check
on the open finding was added specifically because the subject record left
it as an unresolved "plausibly" rather than checking it.
skill-verdict: work-in-english — applied: invoked; wrote this record and
the commit message/PR title/body in English per the skill; only the final
user-facing summary is in Korean.
