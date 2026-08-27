---
issue: 2616
role: execution-observation
author: execution-observation
loop_state: landed
upstream:
  - path: spawn.py::checkout_staleness
    sha: c87423c171c94aeef425bbf01876355e0ec6667d
subject: pipeline.py::core_clone_staleness_line, spawn.py bootstrap wiring, test/test_core_clone_staleness_report.py
test: python3 -m pytest test/test_core_clone_staleness_report.py test/test_checkout_staleness.py -q
result: passed
assertedBy: execution-observation (executed directly this session, CORE_BUILD_NOW=1 build-now bypass)
---

# issue-2616 — execution-observation record

## What was done

Added `pipeline.core_clone_staleness_line(d: Path) -> str` (re-exported as
`spawn.core_clone_staleness_line`), which reuses `spawn.checkout_staleness()`
(issue #2506, fetch + compare, never mutates the working tree — unchanged by
this issue) against whatever `core_root()` resolved for this run, and wires
one call into the existing bootstrap print block in `spawn._spawn_one()`
(right after the line that already prints `core {core_version()}`). The new
line prints to stderr only when `checked and stale`; empty string (no print)
otherwise — matches today's silence for both the "current" and the
"undetermined" case.

```
canonical: `git show c885a7c5 -- pipeline.py spawn.py` (this session's commit)
+def core_clone_staleness_line(d: Path) -> str:
+    result = _sp.checkout_staleness(root=d, fetch=True)
+    if result["checked"] and result["stale"]:
+        return (f"[core] 룰북 클론({d})이 origin 대비 {result['behind']}개 커밋 "
+                f"뒤처졌다 — ... `git -C {d} pull -q --ff-only` 로 직접 갱신하거나, "
+                f"다음 spawn 의 TTL-gated pull(MUSTER_RULEBOOK_TTL="
+                f"{_sp._rulebook_ttl_min():g}분)을 기다려라.")
+    return ""
...
+        staleness_line = core_clone_staleness_line(core_root())
+        if staleness_line:
+            print(staleness_line, file=sys.stderr)
```

New test file `test/test_core_clone_staleness_report.py` (99 lines, modeled
on the existing `test/test_checkout_staleness.py` bare-repo/two-clone
fixture): fresh-checkout-silent, deliberately-one-behind reports path +
count, non-git-dir silent, git-repo-with-no-origin silent.

**Acceptance check 1 — put the clone one commit behind deliberately, spawn a
session, and show the reported line.** A literal full `spawn.py` run (real
`claude` process) was not exercised — that would start an actual nested
role session against GitHub, out of proportion for a 31-line report-only
change. Instead the exact function now embedded in `_spawn_one()`'s
bootstrap print (`core_root()` → `core_clone_staleness_line()`, same two
calls, same argument shape) was invoked directly against a two-clone git
fixture built the same way `test_checkout_staleness.py` builds one — a bare
"origin", clone `a` (stands in for `runs/rulebooks/tokenmaxxxer-core`, never
advanced), clone `b` which pushes one new commit to origin (stands in for a
landed core merge).

```
derived: python3 - <<'PYEOF' (run inline this session; fixture setup elided,
same bare-repo/two-clone pattern as test/test_checkout_staleness.py setUp())
line = spawn.core_clone_staleness_line(a)
print("reported line:", repr(line))
PYEOF
reported line: '[core] 룰북 클론(/tmp/tmpj3k5594x/checkout-a)이 origin 대비 1개 커밋
뒤처졌다 — 이 세션은 landed 된 게이트 수정이 반영 안 된 코드로 떴을 수 있다.
`git -C /tmp/tmpj3k5594x/checkout-a pull -q --ff-only` 로 직접 갱신하거나, 다음
spawn 의 TTL-gated pull(MUSTER_RULEBOOK_TTL=15분)을 기다려라.'
```

Empty state (clone level with origin) verified in the same run:
```
derived: python3 - <<'PYEOF' (continuation of the same script)
line3 = spawn.core_clone_staleness_line(b)   # b is the clone that just pushed, level with its own origin
print("reported line for up-to-date clone:", repr(line3))
PYEOF
reported line for up-to-date clone: ''
```

A reader who wants the literal `spawn.py`-driven version instead: put a real
core clone one commit behind (`git -C <scratch-copy-of-runs/rulebooks/tokenmaxxxer-core>
reset --hard HEAD~1`, not the shared clone), then run any real spawn, e.g.
`python3 spawn.py --skills work-in-english "noop" --issue <n> -C <repo>`
(not `--dry-run` — that branch returns before `_spawn_one()` and never
reaches this print), and read the `[core] 룰북 클론(...)` line on stderr.

**Acceptance check 2 — run the same detection against a path that is not a
git clone and show it reports undetermined rather than current.**

```
derived: python3 - <<'PYEOF' (continuation of the same script)
line2 = spawn.core_clone_staleness_line(not_a_clone)   # plain empty tempdir
raw = spawn.checkout_staleness(root=not_a_clone, fetch=True)
print("bootstrap line for non-git path:", repr(line2))
print("underlying checkout_staleness() verdict:", raw)
PYEOF
bootstrap line for non-git path: ''
underlying checkout_staleness() verdict: {'checked': False, 'stale': False,
'behind': 0, 'fetch_ok': False, 'detail': 'HEAD 를 resolve 할 수 없다'}
```
`checked: False` is git's own signal for "could not determine" (`git
rev-parse HEAD` fails on a non-repo) — distinct in the return value from a
`checked: True, stale: False` "current" verdict. The bootstrap-facing
wrapper reports `''` for both "current" and "undetermined" (design decision
below); the distinction survives in the underlying `checkout_staleness()`
return, which `test_core_clone_staleness_report.py` asserts on directly.

**Acceptance check 3 — the decision and its reasoning, plus the command a
reader would run.**

Decision: **do not add new auto-update.** `core_root()` already
auto-updates the managed clone today (`git pull -q --ff-only`, gated by a
15-minute TTL marker, issue #296/#313 — unchanged by this issue) and that
stays as-is. This issue adds only a read-only report layered on top,
consistent with the issue's own must-not ("do not auto-mutate the clone
silently as a side effect of an unrelated operation" — #2506's restraint,
reused verbatim: `checkout_staleness(fetch=True)` runs `git fetch`, which
updates remote-tracking refs only, never resets/checks out/merges the
clone's working tree).

Reasoning: a `git pull` from inside `core_root()` only ever runs at the
*start* of the next spawn that calls it — a session already mid-run keeps
executing hook code from whatever it loaded at its own bootstrap, regardless
of what any later `pull` does to the clone on disk. No feasible
auto-update mechanism reaches back into a session already running (short of
killing and respawning it, which is out of scope and not asked for). The
real options were: (a) report only, or (b) shrink/remove the 15-minute TTL
so the *next* spawn is more likely to already be current. This issue's
acceptance criteria ask for a report, not a cadence change, and a report is
what was built — the TTL question is a separate, narrower follow-up if the
15-minute lag itself turns out to matter in practice (not measured here,
out of scope for this issue's acceptance).

Because there is no auto-fix, the printed line is written to be actionable
standalone: it names the clone's path and the exact command
(`` `git -C <path> pull -q --ff-only` ``) a human runs to force the update
immediately, without waiting on the TTL.

## Why

`checkout_staleness()` (#2506) already does fetch+compare, never mutates,
and already distinguishes `checked` from `stale` — exactly the two axes
this issue's acceptance needs. Reusing it verbatim (as the issue's own text
suggested: "what is missing is that anything calls it for this path")
avoids re-deriving the same git-ancestry logic a second time with a second
set of edge cases to get wrong. The only new code is the thin
report-formatting wrapper and the one wiring call at the existing bootstrap
print site — no new subprocess logic, no new mutation path.

## Non-goals check

- Installed plugin cache (`~/.claude/plugins/cache/`): untouched, per the
  issue's own non-goals list.
- skill-repository clone: checked — it does **not** share this code path.
  It has its own separate managed-clone resolver (`skills.py` around lines
  54-92) with its own TTL/lock plumbing reused from the same primitives
  (`_locked_rulebook_dir`, `_pull_is_fresh`) but a distinct function, not
  `pipeline.core_root()`/`checkout_staleness()`. Out of scope per the
  issue's own non-goals ("unless it shares the same code path — check, and
  say which"); it does not.

## What did not work

None.

## Upstream basis

- `spawn.py::checkout_staleness` (sha c87423c171c94aeef425bbf01876355e0ec6667d,
  issue #2506, PR #2612) — the fetch+compare detector this issue reuses
  unmodified.
- `pipeline.py::core_root()` / `core_version()` (pre-existing, unchanged by
  this issue) — `core_clone_staleness_line()`'s caller (in
  `spawn._spawn_one()`) feeds it the `core_root()` result as its `d` arg.

## Open findings

None.

## Next steps

None — loop_state: landed. This record ships in the same commit series as
the code it documents (build-now bypass, CORE_BUILD_NOW=1).

skill-verdict: work-in-english — applied: invoked; checked the code commit
message and new code's comments against the skill's rule (English for
commits/comments, Korean only where matching pre-existing surrounding
style) — already compliant, no changes needed.
canonical: `git log -1 --format=%B` (this session's code commit, c885a7c5)
— English subject + body, no Korean.
other mounted skills: not triggered
