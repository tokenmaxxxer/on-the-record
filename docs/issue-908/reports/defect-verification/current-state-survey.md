# issue #908 — current-state survey (phase 1)

subject: issue-908
role: defect-verification
kind: current-state-survey
loop_state: survey-drafted

## Scope

code_under_review:
- spawn.py

closed_checks cited: none exist for this specific claim yet; the only
prior artifact is the raw run log from the #895 feature-scenario probe,
read below as evidence of the symptom, re-derived against spawn.py
directly, not cite-and-skipped.

## Scout: skip record

Skipped. This is a pure defect-reproduction/pinning task with no product
surface and no open design decision — the issue asks only to locate the
exact code path where a dying delegation fails to leave a trace, not to
choose among competing designs. Skip condition met: "the spec literally
leaves no design decision open."

## The symptom, as raw evidence

canonical: `docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md`,
read this session (its step 6, describing the #895 feature-scenario
live run against the real GitHub fixture host) — quoted verbatim:
```
6. canonical: `harness.driver.poll_for_pr_ready("JiwonJung94/
   northpole-harness-fixture", "issue-10/implementation", timeout_sec=480,
   interval_sec=15)` return value, run this session — `{"ready": false,
   "reason": "no OPEN/MERGEABLE PR ... within 480s"}`. canonical: `gh api
   repos/JiwonJung94/northpole-harness-fixture/branches --jq
   '.[].name'`, run this session immediately after — output was exactly
   `main` (one line, no `issue-10/*` branch).
   canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/
   issues/10/timeline --jq '.[].event'`, run this session — empty output
   (zero events). canonical: `ps aux | grep -E "claude -p|spawn.py"`, run
   this session — no process tied to this run's `dest` path or issue #10
   in the listing.
   canonical: `find <isolated MUSTER_STATE_ROOT> -type f`, run this
   session — empty output (no muster roster file ever written for this
   run). The first turn's own narration of a live background spawn did
   not correspond to any surviving process, branch, PR, issue comment, or
   state file — all four checks immediately above are the citation for
   that claim.
```

canonical: same file, its step 7 (also read this session) — the recovery
actually observed:
```
7. Resumed the same session (`--resume b5faf166-...`, `--permission-mode
   bypassPermissions`, per #889) with a generic status-check nudge (not
   an answer to any question the session had asked). ... `.result`:
   "The respawn bootstrapped cleanly this time... role got its isolated
   workspace on branch `issue-10/implementation`, and its session is
   live." canonical: `ps aux | grep issue-10`, run this session
   immediately after — one live `spawn.py implementation ... --issue 10`
```

canonical: the "empty output (no muster roster file ever written for
this run)" line quoted directly above — no roster/state file was ever
written for that spawn attempt, not a stale entry, not a
crashed-but-registered entry. That rules out every death-detection path
in `spawn.py` that operates on already-registered roster entries
(`roster_watchdog`, `reconcile`, `_maybe_resume_for_ready_pr`) as the
location, since none of them see a key that was never written. The
defect has to live upstream of roster registration itself.

## Where registration happens in spawn.py, pinned by line

canonical: `spawn.py`, read this session, lines 4942-5178 — `_spawn_one()`
is the single function both `main()` and `drive()` share for launching a
role session (spawn.py:4942-4949, docstring: "main() 과 drive() 가 같은
몸통을 쓴다"). Walking the `issue is not None` path (the only path
relevant — a delegation is always issue-scoped) top to bottom:

1. spawn.py:4982 `_acquire_spawn_claim(cwd, issue, role)` — the only disk
   trace written before any subprocess exists: a
   `<workspace>.spawn-claim` lock file (spawn.py:4852-4901). Concurrency
   lock, not a monitored roster entry (see below).
2. spawn.py:4986-5018 — branch checkout, task-file write, rulebook/plugin
   resolution (`plugin_dirs()`, `core_plugin_dirs()`), `role_settings()`,
   temp settings-file write. No roster or event write in this span.
3. spawn.py:5075 `child_pid = os.fork()`. The parent branch
   (5076-5116) arms the `watch --follow` watcher and either blocks
   (`_await_bounded`) or returns immediately (`--no-wait`,
   5104-5114). The child branch continues at:
4. spawn.py:5117 `_rewrite_spawn_claim_pid(cwd)`, 5118 `os.setsid()`,
   5125-5129 three `os.dup2()` calls redirecting stdin/stdout/stderr to
   `/dev/null`. None of these five calls (5117-5129) is wrapped in
   `try`/`except` — an `OSError` from any of them propagates unhandled
   and the fork-child terminates.
5. spawn.py:5130-5133 `subprocess.Popen(cmd, ...)` — a `FileNotFoundError`
   or other `OSError` here (e.g. `claude` missing from PATH) is also
   unhandled at this point.
6. spawn.py:5134 `roster_register(roster_key, {...})` — the first and
   only place in `_spawn_one()` that writes to the monitored roster
   (`roster_register()`: spawn.py:1847-1851, via `_roster_save()`:
   spawn.py:1803-1805).
7. spawn.py:5177 `_append_event(events_path, "session-start", ...)` —
   the first and only `events.jsonl` write in the function
   (`_append_event()`: spawn.py:2760-2763, append-only), and it comes
   after roster_register.

derived: `python3 - <<'PY'` (run this session against the current
`spawn.py`, exact command and output):
```
$ python3 - <<'PY'
src = open("spawn.py").read().splitlines()
fork = next(i for i,l in enumerate(src) if "os.fork()" in l) + 1
reg = next(i for i,l in enumerate(src) if "roster_register(roster_key" in l) + 1
print(fork, reg, reg - fork)
PY
5075 5134 59
```
59 lines of fork-child setup (setsid, 3x dup2, Popen) execute between the
`os.fork()` and the first roster write, none guarded by a `try`/`except`
that would record a death before or after it happens.

## The defect, pinned

canonical: the line-walk above (spawn.py:4982-5134) plus the `python3`
derivation immediately above it — any unhandled failure in `_spawn_one()`
between `_acquire_spawn_claim()` (spawn.py:4982) and `roster_register()`
(spawn.py:5134) — most acutely the unguarded fork-child setup at
spawn.py:5117-5129 and `subprocess.Popen()` at spawn.py:5130-5133 —
leaves zero trace in both channels the rest of the system uses to detect
a live or dead delegation: the roster (spawn.py:1796-1852) and the
append-only event log (spawn.py:2760-2763, first written for a
delegation at spawn.py:5177, itself downstream of roster_register).

canonical: spawn.py:2395 (`if not _alive(e.get("pid", 0)):`, inside
`roster_watchdog()`), cross-checked against the step-6 quote above (no
surviving process, empty issue timeline, empty `MUSTER_STATE_ROOT`) — a
crash after roster_register would still leave a roster entry for that
check to find dead and diagnose; a crash before it leaves nothing for
that check to even iterate over, because the loop it lives in only walks
`_roster_load()` entries (spawn.py:2373, 2382).

### Why the `.spawn-claim` file doesn't close the gap

canonical: `grep -n "spawn-claim" spawn.py`, run this session:
```
4853:    return Path(str(work) + ".spawn-claim")
4858:    — 재스폰 경로의 `.respawn-claim-{ts}`(이슈 #132)와 같은 계열이지만,
4864:    claim_path = _spawn_claim_path(work)
4930:    claim_path = _spawn_claim_path(work)
```
`_acquire_spawn_claim()` (spawn.py:4856-4901) does write a disk artifact
before the fork, at spawn.py:4982. It does not close the gap:

- It lives at `<workspace>.spawn-claim` (spawn.py:4852-4853), a sibling
  of the isolated per-spawn workspace directory — not the `ROSTER` path
  `roster_register()`/`_roster_load()` read and write.
- No death-detection consumer reads it: `roster_watchdog()`
  (spawn.py:2349-2458) iterates `_roster_load()` exclusively
  (spawn.py:2373); the grep above shows no `glob`/scan of `*.spawn-claim`
  anywhere in the file.
- Its only two functional call sites are: write once, at spawn.py:4982;
  release once, at spawn.py:5376, on the normal-completion path near the
  end of `_spawn_one()`. The only reader of an orphaned claim is the
  next `_acquire_spawn_claim()` call for the same `(issue, role)`
  (spawn.py:4888-4900, `_alive(pid)` then stale-cleanup) — reactive, on
  next attempt, never proactive, never event-emitting.

## Confirming the poll-resume path retries blindly, without recording the death

canonical: spawn.py:2349-2458 (`roster_watchdog()`, read this session in
full) — its death-detection branch:
```
2373: d = _roster_load()
...
2382: for key, e in sorted(d.items()):
...
2395:     if not _alive(e.get("pid", 0)):
```
operates only over `d = _roster_load()` — keys `roster_register()`
actually wrote. A delegation that died before spawn.py:5134 is not a
member of `d`, so every branch inside this loop —
`_post_session_end_comment` (2402), `diagnose_health`/`dead_report`
(2411-2417), `_maybe_resume_for_ready_pr` (2426) — is structurally
unreachable for it; none of them can fire for a key that was never
inserted.

canonical: the step-7 quote above from
`docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md`
— what actually recovered the #895 run was the external harness's
`harness.driver.poll_for_pr_ready()` 480-second timeout followed by a
plain `--resume` of the orchestrator's own top-level session, entirely
outside `spawn.py`'s roster machinery. `spawn.py` itself recorded
nothing about the death anywhere before that outside retry happened.
The retry that saved the #895 run was blind by construction, because the
roster/event channels `spawn.py` offers had nothing registered to
observe.

## Attempt outcome

canonical: `python3 -c "src=open('spawn.py').read().splitlines(); print(next(i for i,l in enumerate(src) if 'os.fork()' in l)+1, next(i for i,l in enumerate(src) if 'roster_register(roster_key' in l)+1)"`,
run this session — output `5075 5134`, matching "Where registration
happens" above. Attempt 1, source: issue #908 body verbatim ("pin where
a dying spawn fails to write a roster/record entry or emit an event").
Outcome: reproduced.

canonical: `python3 -c "src=open('spawn.py').read().splitlines(); print(src[2372].strip(), '|', src[2394].strip())"`,
run this session — output `d = _roster_load()` `|` `if not
_alive(e.get("pid", 0)):`. Attempt 2 (source: issue #908 body verbatim,
"confirm the poll-resume path retries blindly"). Outcome: reproduced.

This survey does not propose a fix — pinning only, per role directive.
The finding write-up (severity, `addressed_to: coding`) is phase-2
material and belongs in the per-issue defect-verification record once
phase 2 opens (contract v3 s19); this document is the phase-1
current-state survey feeding that write-up.

## Accumulation

Not accumulation-cost-shaped (no per-item/per-N-lines cost curve here) —
a single reproduction round over one code path in one file.
canonical: the "Attempt outcome" section above (both attempts already
executed live against the current `spawn.py`) — a fresh live-kill
reproduction (spawn a real delegation, SIGKILL the fork-child between
spawn.py:5075 and 5130, observe roster/events) was not run in this
survey: the #895/#907 evidence quoted above already demonstrates the
exact failure mode end-to-end against a real GitHub host, and a
synthetic local kill would exercise the same code-path gap with weaker
external validity than the real run already on record. A hermetic,
on-demand repro (e.g. for a regression test) is left for issue #908 step
2.
