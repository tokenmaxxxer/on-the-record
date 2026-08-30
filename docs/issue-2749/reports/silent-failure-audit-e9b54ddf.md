---
issue: 2749
role: silent-failure-audit-e9b54ddf
author: silent-failure-audit-e9b54ddf
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: roster.py:_session_looks_real, spawn.py:self_update_pull_cli
type: implementation-record
breaking: false
verdict: blocking-findings-fixed-scope-narrowed-to-advances
loop_state: landed
upstream:
  - path: docs/issue-2749/reports/adversarial-review-28904fd2.md
    sha: 37549eea3fe4f096f836ddbf026a9d9a754b0fde
  - path: docs/issue-2749/reports/silent-failure-audit-bbfffc81.md
    sha: a04cd4d298803d9060d0279fb361d0a00de2b094
  - path: spawn.py
    sha: same-commit
  - path: roster.py
    sha: same-commit
---

# issue-2749 — silent-failure-audit-e9b54ddf record

## What was done

canonical: `gh pr view 2823 --comments` (JiwonJung94, CHANGES review) —
two blocking findings and one non-blocking item, quoted in full under
Upstream basis.

Continued PR #2823 (`issue-2749/silent-failure-audit-bbfffc81`, tip
`e333add99cdd3aff5aa3fa186bd5b96020820738` before this delivery) directly
on its own branch, addressing that review. CORE_BUILD_NOW=1 was set
(spawner env — `checked: printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW" —
result: CORE_BUILD_NOW=1`), so this delivered directly under contract v3
s19a (build-now bypass) — no phase-1 proposal round.

**1. Fixed the permanent-wedge bug (blocking).** `self_update_pull_cli()`
built its "who is live" list with bare `roster._alive()`
(`os.kill(pid, 0)`), the same reuse-blind check `_watcher_looks_real()`
was already written to replace for watcher pids (issue #488). Added
`roster._session_looks_real(pid, work)` (`roster.py`, next to
`_watcher_looks_real`/`_alive`): alive-check first, then confirm identity
via `/proc/<pid>/cwd` against the roster entry's recorded `work`
workspace, falling back to bare-alive when `/proc` or `work` is
unavailable. `self_update_pull_cli()`'s `live_roster` computation now
calls `_session_looks_real()` instead of `_alive()`, and the refusal
message widened to print `key`, `pid`, *and* `work` per roster line, so a
human can independently run `readlink /proc/<pid>/cwd` and check the
claim.

**2. Scope decision on the founding evidence (blocking).**

canonical: `docs/issue-2749/reports/adversarial-review-28904fd2.md` (PR
#2831, independent verification of PR #2823) — reproduced live that the
issue's founding reflog line (`merge origin/HEAD: Fast-forward`) matches
`watchdog.py`'s `watchdog_freshness_check()` merge, not `self-update.sh`'s
old `git pull --ff-only`, and that the two commands produce distinct
reflog message strings.

Decision: **do not close `watchdog.py`'s route in this delivery** — see
Why, below, for the reasoning — so the PR trailer changes from
`Closes #2749` to `Advances #2749`. Issue #2749 stays open, now scoped to
`watchdog.py`'s still-unconditional merge.

**3. Answered the non-blocking staleness-ceiling question in the record**
(see Why, below) rather than leaving it silent.

Code changes: `roster.py` (+32 lines: `_session_looks_real`), `spawn.py`
(+19/-6: alias + `self_update_pull_cli()` live-check swap + refusal
message), `test/test_self_update_pull_gate.py` (+44/-2: fixed
`test_live_roster_session_refuses_without_pulling`'s fixture to give the
fake session process a `cwd` matching its `work` field — a real spawned
session's registered pid always does, since it's the `claude` subprocess
itself — plus one new test,
`test_reused_pid_of_crashed_session_does_not_wedge_forever`, that
registers a roster entry whose `work` is the checkout but whose pid
belongs to an unrelated live process with a *different* cwd — exactly
what pid reuse looks like from the roster's point of view — and asserts
self-update proceeds instead of refusing forever).

`derived: python3 -m pytest test/test_self_update_pull_gate.py
test/test_self_update_working_tree_untouched.py -q` — result: `8 passed`
(was 7 before this delivery's one new test).

skill-verdict: silent-failure-audit — applied: invoked; audited the one
new error-handling site in `_session_looks_real()` (the `OSError` catch
around `Path.resolve()`, guarding a TOCTOU race where the pid exits
between the `cwd_link.exists()` check and the `resolve()` call) —
classified Handled: on `OSError` it returns `True` (falls back to
bare-alive, the *safe* direction — a refusal-worthy false positive rather
than a wedge-worthy false negative), matching `_watcher_looks_real()`'s
existing degrade-on-unreadable-`/proc` pattern. No Silently Absorbed sites
introduced. Also audited (not touched, see What did not work):
`_claim_only_live_sessions()`'s own bare `_alive()` call
(`roster.py:128`) — classified Silently Absorbed in the narrow sense that
a reused claim-file pid still reads as live forever, but leaving it was a
deliberate scope decision (the claim's recorded pid is the fork-wrapper's
own pid, not `cwd`-verifiable the same way — see What did not work), not
a stub-and-forget; logged under Open findings.
skill-verdict: work-in-english — applied: invoked; this record, all code
comments, and commit/PR text are in English (conversational replies to
the user stayed Korean per the user's own language — the skill governs
repository-bound artifacts, not conversational turns).

## Why

**Why `_session_looks_real()` uses `cwd`, not the reviewer's literal
`_watcher_looks_real()`.** The review asked to "use the primitive that
already handles pid reuse." Read literally — calling
`_watcher_looks_real(pid, issue, skill)` on the roster's own session
pid — it would break in the wrong direction:

`derived: sed -n '196,203p' roster.py`
```python
    if "watch" not in parts or str(issue) not in parts:
        return False
    if skill is not None and skill not in parts:
        return False
    return True
```

`_watcher_looks_real()` requires the literal token `"watch"` in
`/proc/<pid>/cmdline`, because it exists to verify *watcher* processes
(`spawn.py watch --issue <n> --session <skill> ...`). A live `claude`
session's own cmdline never contains it:

`derived: sed -n '661,664p' pipeline.py`
```python
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "--verbose",
           "--exclude-dynamic-system-prompt-sections"]
```

Passing a real, live session pid through `_watcher_looks_real()` would
always return `False` — "not real" — which would make
`self_update_pull_cli()` treat *every* live session as dead and pull
unconditionally, silently reopening the exact hazard #2749 was filed on
(the checkout advancing under live sessions). That is a worse failure than
the one being fixed, so it was rejected; see What did not work.

What actually generalizes from `_watcher_looks_real()` is the *pattern* —
alive-check, then best-effort identity confirmation via `/proc`, with
graceful degrade when `/proc` or the confirming datum is unavailable — not
its literal `cmdline`/`"watch"` check. Traced `self_update_pull_cli()`'s
data back to its source — the roster's final `pid` field is *always*
overwritten to `proc.pid`, the `claude` subprocess itself:

`derived: sed -n '4404,4417p' spawn.py`
```python
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, env={**os.environ, **extra_env}, start_new_session=True,
            )
        except OSError as exc:
            ...
        roster_register(roster_key, {
            "pid": proc.pid, "skill": skill,
            "issue": issue, "ts": int(time.time()),
            "work": str(cwd), "log": str(log_path),
```

This holds for both the fork-based (checkpoint) and direct (adhoc/bounded)
spawn paths, since both fall through to the same `Popen` call before this
final `roster_register`. That process's own `/proc/<pid>/cwd` is therefore
reliably `cwd` (the roster entry's `work` field) for as long as it is the
real session — and a pid-reused unrelated process essentially never
happens to share that exact cwd. `cwd` is the identity signal that
actually exists for this pid; `cmdline` tokens are not.

**Why `Advances #2749`, not `Closes #2749`.** Per `hook-contract.md`'s
`pr-preflight.sh` note and the review: landing `Closes` on an issue whose
founding symptom still reproduces is the thing being refused here on
purpose.

`derived: sed -n '1302,1308p' watchdog.py`
```python
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
        del pull  # 실패해도(로컬 커밋 등) advisory — HEAD 비교로 판정한다
```

`watchdog.py:watchdog_freshness_check()` still runs this unconditionally,
every watchdog tick, regardless of how many sessions are live — the same
shape of hazard (a mechanism nobody explicitly asked at that moment
advancing the checkout hooks execute from) as the `self-update.sh` bug
this PR fixes, and per the `adversarial-review-28904fd2.md` finding above,
it is the mechanism that actually produced the issue's founding reflog
line. Closing `watchdog.py`'s route properly is not a small addition to
this diff: `watchdog_freshness_check()`'s whole *purpose* is to detect
"did the checkout's HEAD move" so the watchdog can restart on stale code,
and today it does that by moving the HEAD itself (merge, above) and
comparing before/after. Making the merge deliberate (mirroring this PR's
`self-update.sh` fix) would require re-deriving that freshness signal from
the *fetched* origin ref instead of the *merged* local HEAD — a change to
what "stale" means for the watchdog, with its own restart-timing risk, not
a mechanical port of this PR's pattern. Rather than rush that under this
PR's diff and risk a shallow, unverified fix to the mechanism that
actually matters more (a stuck watchdog is worse than a racy checkout),
scoping it out honestly and leaving #2749 open is the call — matching the
reviewer's own stated preference ("I would rather have the honest scope
than the tidy close"). Issue #2749 remains open, specifically for
`watchdog.py`'s route; a future delivery under this same issue should
close it before `Closes #2749` is used again.

**Why the staleness-ceiling question (item 3) is answered here, not
fixed.**

`derived: grep -rn "self-update" on-the-record/hooks/*.sh` — result: no
match. `derived: grep -n "\"self-update\"" spawn.py` — result: only the
CLI dispatch table entry (`spawn.py:2284`, `return
self_update_pull_cli()`), no other caller.

`derived: grep -rn "pull-check" *.py on-the-record/hooks/*.sh` — result:
only `on-the-record/hooks/self-update.sh` and `self_update_pull_cli()`'s
own `_pull_check_write()`/reader touch the file; nothing else reads it.

Nothing in the tree auto-invokes `spawn.py self-update`, and the four
`.pull-check` states it writes are not read by anything else. This moves
the checkout's staleness ceiling from "at most one `SessionStart` firing"
(the old, hazardous-but-bounded behavior) to "unbounded until a human or
the orchestrator remembers to run `spawn.py self-update`." That is the
correct trade against #2670's hazard analysis — #2670 established that
*the pull*, not staleness, is the thing that must never happen without an
actor deciding it, and unbounded-but-deliberate is strictly safer than
bounded-but-accidental for the property #2670 cares about. It does not, on
its own, resolve *how* the checkout is meant to actually advance in
practice: today that is a manual `spawn.py self-update` invocation, with
no scheduled or event-driven trigger and no surfacing of the
`.pull-check` state anywhere a human or the orchestrator would naturally
look (`spawn.py ps`, watchdog health output). That gap is real and is a
reasonable candidate for a follow-up under #2749 or a new issue — this
delivery leaves the choice of "who decides when to run `self-update`"
explicit and deliberate (the whole point of this issue) rather than
automated, since automating the trigger without also addressing #910
finding #4's staleness argument or #2670's hazard analysis would just
relocate the same unresolved question.

## What did not work

- Tried passing the roster's session pid straight through
  `_watcher_looks_real(pid, issue, skill)`, as the review's wording
  literally suggests — reasoned through it before writing any code and
  rejected it: `_watcher_looks_real()` hardcodes `"watch"` as a required
  `cmdline` token (`roster.py:199`, quoted under Why), which no live
  `claude` session's `cmdline` ever contains (`pipeline.py:661`, quoted
  under Why), so every live session would read as "not real" and
  self-update would pull unconditionally — silently reopening the exact
  hazard #2749 exists to close, and strictly worse than the bug being
  fixed. Wrote `_session_looks_real()` instead, reusing the same
  alive-then-confirm-via-`/proc` *pattern* keyed on `cwd` (see Why).
- Considered extending the same fix to `_claim_only_live_sessions()`
  (`roster.py:93-133`), which also feeds `self_update_pull_cli()`'s
  refusal decision and also uses bare `_alive()` (`roster.py:128`) — for
  full wedge-closure this looked like the same bug in a second place.

  `derived: sed -n '840,854p' roster.py`
  ```python
  def _rewrite_spawn_claim_pid(work: str) -> None:
      """fork 직후 자식 분기에서 클레임의 pid 를 자기 자신(자식)으로 재기록한다.
      ...
      """
      claim_path = _sp._spawn_claim_path(work)
      try:
          existing = json.loads(claim_path.read_text())
      except (OSError, ValueError):
          return
      existing["pid"] = os.getpid()
  ```

  `derived: grep -n "os.chdir" spawn.py` — result: no match.

  Claim files record `os.getpid()` — the fork *wrapper's own* pid,
  captured right after `os.fork()` and before it `Popen`s the actual
  `claude` subprocess — and that wrapper process is never `os.chdir()`'d
  to the workspace. A `cwd`-based identity check on this pid would
  therefore false-negative on genuinely live claim-only sessions (their
  wrapper's `cwd` is whatever the orchestrator's own `cwd` was at spawn
  time, not the workspace), which is a regression, not a fix. Left
  `_claim_only_live_sessions()` unchanged — this is the narrower residual
  gap called out under Open findings, not the reviewer's named bug.

## Upstream basis

- `docs/issue-2749/reports/adversarial-review-28904fd2.md` (PR #2831,
  independent verification of PR #2823, sha
  `37549eea3fe4f096f836ddbf026a9d9a754b0fde`) — reproduced live both
  blocking findings this delivery addresses (reflog-signature mismatch;
  recycled-pid indefinite wedge) and the non-blocking staleness-ceiling
  observation.
- `docs/issue-2749/reports/silent-failure-audit-bbfffc81.md` (PR #2823's
  own delivery record, sha `a04cd4d298803d9060d0279fb361d0a00de2b094`) —
  the subject this session continues; its own record already flagged
  `watchdog.py`'s fetch+merge as a related-but-out-of-scope finding.
- `spawn.py`, `roster.py` — sha `same-commit` (this delivery edits both in
  the same commit as this record).

## Open findings

canonical: `watchdog.py:1302-1308` (quoted verbatim under Why, via
`derived: sed -n '1302,1308p' watchdog.py`) and
`docs/issue-2749/reports/adversarial-review-28904fd2.md` (PR #2831).

- **`watchdog.py:watchdog_freshness_check()` still unconditionally
  advances the checkout** (`git fetch && git merge --ff-only origin/HEAD`,
  every tick, no live-session gate — quoted under Why) — the mechanism
  that actually produced #2749's founding reflog evidence per
  `adversarial-review-28904fd2.md`. Resolution path: a follow-up delivery
  under issue #2749 that re-derives the watchdog's staleness signal from
  the fetched origin ref instead of a merged local HEAD, mirroring this
  PR's `self-update.sh` fix, before the issue can carry `Closes #2749`.
- **`_claim_only_live_sessions()` (`roster.py:93-133`) still uses bare
  `_alive()`** for its own pid-liveness check (`roster.py:128`), so a
  claim-file pid reused by an unrelated process could in principle still
  wedge `self_update_pull_cli()` via the `claim_only` path even after this
  fix. Narrower than the reviewer's named bug (the roster-pid path, now
  fixed) and not independently reproduced as live — logged here rather
  than silently left. Resolution path: a follow-up would need a
  wedge-safe identity signal for the fork-wrapper pid specifically (its
  `cwd` doesn't work — see What did not work); not designed here.
- **Nothing surfaces `.pull-check`'s state anywhere a human or the
  orchestrator would naturally look**, and nothing schedules
  `spawn.py self-update` — see Why (item 3) for the reasoning that this is
  a deliberate, not silent, trade for now. Resolution path: a follow-up
  issue for either a scheduled/event-driven trigger or surfacing
  `.pull-check` in `spawn.py ps`/watchdog health output, weighed against
  #910 finding #4 and #2670 before automating anything.

## Next steps

None from this session — `loop_state: landed`. The three items above are
handed off as open findings, not next steps this session owes.
