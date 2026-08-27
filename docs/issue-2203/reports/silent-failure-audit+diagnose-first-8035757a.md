---
code_under_review:
  - roster.py
  - board.py
  - spawn.py
  - test/test_ps_live_reliability.py
type: fix
breaking: false
# canonical: python3 -m pytest test/test_ps_live_reliability.py -q — result: 4 passed (executed live this session)
verdict: pass
loop_state: landed
issue: 2203
role: silent-failure-audit+diagnose-first-8035757a
author: silent-failure-audit+diagnose-first-8035757a
upstream: []
---

# issue-2203 — silent-failure-audit+diagnose-first-8035757a record

Subject: issue-2203

canonical: `gh issue view 2203` output (read this session, three comments) — CORE_BUILD_NOW=1 in this session's environment (`printenv | grep CORE_BUILD_NOW`, executed this session) authorizes the s19a build-now bypass, skipping the phase-1 proposal round.

skill-verdict: diagnose-first — applied: invoked; used the skill's Stage 0-2 gates (problem statement without solution/cause, live-reproduction baseline, narrow→dig→verify, Amdahl share check) to test the issue's own reinstall hypothesis before implementing, and to widen scope once the issue's 2026-08-25 comment falsified "reinstall required" as the sole cause (see Why below).
skill-verdict: silent-failure-audit — applied: invoked; audited my own new `except` blocks in `_claim_only_live_sessions()` and found the first draft silently absorbed a claim-directory-scan failure and per-file claim-parse failures into an empty list — same shape as the bug this issue is about, just on the claim side. Fixed before landing (see What was done).

## What was done

canonical: `240190ebd2eab323913d1c72bd32c5113aa4dafa` (commit landed this session, carries every file below)

- `roster.py`:
  - `_roster_load_checked() -> tuple[dict, str | None]`: reads `ROSTER` and
    distinguishes `FileNotFoundError` (a genuinely-empty roster — no
    session has ever registered, a legitimate empty state) from any other
    `OSError` or `ValueError`/non-dict JSON (the file exists but couldn't
    be read or parsed — must never read as "no sessions"). `_roster_load()`
    itself is untouched — every other caller (`_live_workspaces()`,
    watchdog, lease sweeps, the `#2492` prune path) keeps its existing
    fail-to-`{}` behavior; only `ps` needed the distinction.
  - `_claim_only_live_sessions(d) -> tuple[list[tuple[str, int]], list[str]]`:
    globs `*.spawn-claim` under `_workspace_base()` (the same claim files
    `_acquire_spawn_claim()` uses to refuse a duplicate spawn), and for
    each live claim (pid alive) whose `work` path doesn't match any
    *alive* roster entry, reports it as a discrepancy. Second return value
    is a list of scan-failure warnings (base-directory glob failure, or an
    individual claim file that couldn't be read/parsed) — a
    silent-failure-audit finding on the first draft (see below) surfaced
    that these were originally swallowed via a bare `continue`/early
    `return out`.
  - `_roster_save()`: was a plain `write_text()` (truncate-then-write, not
    atomic); now writes to a tempfile and `os.replace()`s it, the same
    pattern `_rewrite_spawn_claim_pid()` already uses for the claim file.
    Closes the window where an unlocked reader (`ps` never took
    `_roster_locked()`) could observe a truncated/partial write as invalid
    JSON — reproduced live in the test below.
- `spawn.py`: re-exports `_roster_load_checked` and `_claim_only_live_sessions`
  from `roster.py`, following the existing re-export pattern for every
  other roster/claim function in this file.
- `board.py` `roster_ps()`: now calls `_roster_load_checked()` and
  `_claim_only_live_sessions()` instead of the old `_roster_load()`.
  - A roster read/parse failure prints `"확인 불가 — 로스터 파일을 읽지
    못함(<reason>)"` plus an explicit "don't read this as empty" line,
    lists any claim-only live sessions found, and returns exit code `2`.
  - A clean roster load with zero entries and zero claim discrepancies and
    zero scan warnings still prints the plain `"돌고 있는 역할 세션 없음"`
    and returns `0` — unchanged from before, so genuine absence stays
    legitimate (acceptance criterion 2).
  - Any claim-only discrepancy is printed as an explicit warning block
    listing `pid`/`work`, whether or not the roster read itself succeeded.
  - Any claim-scan warning also downgrades the exit code to `2`, even when
    the roster read succeeded — see Why for the reasoning on why this
    errs conservative.
- `test/test_ps_live_reliability.py` (new; test count derived below), one
  real subprocess as a live-session stand-in throughout:
  - `test_live_session_survives_roster_write_corruption`: registers the
    subprocess in the roster + a claim file, confirms `RUNNING` +
    `rc=0`, then overwrites `ROSTER` with truncated JSON (the
    interrupted-write shape `_roster_save()`'s old form could leave for a
    concurrent unlocked reader) and confirms `ps` says `확인 불가`, lists
    the claim-only session, never prints the bare empty line, and returns
    `2`.
  - `test_live_session_missing_from_roster_but_claim_alive`: reproduces
    the issue's own freshest live incident shape (2026-08-25) — a
    roster that parses fine (`{}`) but is simply missing the entry, while
    the claim file still shows the session alive. Confirms `ps` surfaces
    it as `claim-only` rather than a bare empty line.
  - `test_corrupt_claim_file_surfaces_as_warning_not_silent_skip`: an
    unreadable claim file produces an explicit `경고` line and `rc=2`
    instead of being silently skipped.
  - `test_genuinely_no_sessions_still_reports_empty`: no roster file, no
    claim files — confirms the plain empty message and `rc=0` are
    unchanged (acceptance criterion 2, regression guard).

derived: `grep -c 'def test_' test/test_ps_live_reliability.py` — result: 4 (executed this session; the four tests are the ones itemized above).

derived: `git stash` the code changes (keeping the new test file) then `python3 -m pytest test/test_ps_live_reliability.py -q` — result: 2 failed, 2 passed against the pre-fix code (executed this session). The 2 failures are `test_live_session_survives_roster_write_corruption` and `test_live_session_missing_from_roster_but_claim_alive`, both on the assertion that the bare `'돌고 있는 역할 세션 없음'` line must not appear — confirms the tests actually exercise the bug, not just the fix's own code path.

Acceptance requirement met — checked: `python3 -m pytest test/test_ps_live_reliability.py -q` — result: 4 passed.
Acceptance requirement met — checked: `python3 -m pytest test/ -q` — result: 263 passed, 15 failed, all 15 failures present and identical before this change (checked: `git stash && python3 -m pytest test/ -q` — result: 260 passed, 17 failed, executed this session — the 2 extra failures there are these same new tests failing pre-fix, not a different set) — no regression introduced.

## Why

canonical: `gh issue view 2203 --comments` (read this session)

**Investigate, per the issue's stated order — test the reinstall hypothesis first.**
The issue's first two incidents both followed a plugin reinstall and asked
to test that mechanism directly before theorizing further. I looked for
the concrete reinstall mechanism in this codebase:
`on-the-record/hooks/self-update.sh` (SessionStart hook) runs `git pull
-q --ff-only` against the same checkout directory that houses
`runs/active.json` (`ROOT = Path(__file__).resolve().parent`,
`STATE_ROOT = ROOT / "runs"`, `ROSTER = STATE_ROOT / "active.json"` —
`spawn.py:48,646,1005`). `runs/` is gitignored (`.gitignore:1`,
`git check-ignore -v runs/active.json` confirms), so a normal
fast-forward pull does not touch it directly — there is no code path
where `git pull` itself deletes or truncates `active.json`.

**The hypothesis does not hold as stated — the issue's own third comment
falsifies it.** The 2026-08-25 fresh live reproduction in the issue
thread shows the exact same roster/claim disagreement with *no reinstall
event at all*: the roster simply had no entry for a session whose
spawn-claim (and process, and growing log) were all still alive. That
comment already draws the right conclusion and names the fix direction:
cross-check `ps` against the claim state the spawn-refusal path trusts,
rather than assuming reinstall is a required trigger. I did not find
independent evidence narrowing this second mechanism (why the roster
entry itself is missing) further within this session's scope — it may be
a registration-timing gap, a stale-dead-entry misclassification, or
something else; the fix below is deliberately mechanism-agnostic about
*why* an entry is missing, because a claim-based cross-check catches
disagreement regardless of cause.

**What I did find, independently, that plausibly explains the
reinstall correlation without needing reinstall to be the sole cause:**
`_roster_load()` swallowed `OSError`/`ValueError` into `{}` (same as
genuine emptiness), and `_roster_save()` was a plain non-atomic
`write_text()` — a `ps` call landing between truncate and rewrite (no
lock is held by readers) would see invalid JSON and silently read it as
"no sessions." A burst of concurrent session-start/reinstall activity is
exactly the kind of window that makes this race more likely to fire,
without reinstall being a necessary condition for the underlying bug —
consistent with both being true at once: reinstall as a probability
amplifier, not the mechanism itself.

**Fix direction, matching the issue's explicit ask:** "if enumeration
cannot be made reliable, [ps] must distinguish 'no session' from 'cannot
determine'". Two independent defenses, because the two recorded
mechanisms are different: (1) `_roster_load_checked()` for the
read/parse-failure shape, (2) claim-file cross-checking for the
shape where the roster read succeeds but is simply missing an entry —
covering both without needing to fully resolve mechanism (2)'s root
cause, which the issue's own scope note leaves open ("say so with the
evidence rather than quietly moving to another cause" — done above).

**Why claim-scan failures also downgrade the exit code to 2, even when
the roster read succeeded:** the silent-failure audit (see below) found
that the claim cross-check itself could silently degrade to "found
nothing" on its own read failures — the same shape of bug this issue
exists to close, just moved one layer over. Since the whole point of the
claim check is to be the fallback when the roster can't be trusted, a
fallback that fails quietly defeats the purpose; erring toward an
explicit, slightly-more-frequent "확인 불가" is the conservative choice
given the two recorded incidents were both destructive actions taken on
a false "no session" read, not merely inconvenienced by an extra warning.

**Coordination with issue #2492** (checkout-scoped `_live_workspaces()`/
`ROSTER` on the prune path, currently in progress in parallel): not
touched here. `_roster_load()` itself (which `_live_workspaces()` and the
prune path call) is byte-identical to before this change — I added a new
sibling function (`_roster_load_checked()`) rather than modifying it, and
`_claim_only_live_sessions()`/the `roster_ps()` changes are read-only
(`ps` still doesn't delete/modify workspaces, only the pre-existing
dead-roster-entry removal at the end of the existing loop, which this
change doesn't touch). The one piece of genuinely shared machinery is
`_roster_save()`, now atomic instead of a plain `write_text()` — used by
`roster_register()`/`roster_remove()`, which #2492's checkout-scoped fix
will also read the output of. This is a format-preserving change (same
JSON content, same call signature) so it should not conflict with
#2492's work, but flagging it here per the instruction to say so rather
than silently couple the two.

**Design alternative considered and rejected:** teaching `roster_ps()`
to also treat a "dead" roster entry contradicted by a live claim as
still-alive (skip its removal) rather than only warning about it
separately. Rejected for this issue: that would touch the same
dead-entry-removal code path `roster_ps()` shares to some degree with the
prune-adjacent machinery #2492 is actively changing, and the issue
explicitly says "do not change prune behavior here." The warning-based
approach achieves the acceptance requirement (a live session is never
rendered as a bare, unqualified absence) without touching removal
timing.

## What did not work

None.

## Upstream basis

None — `CORE_BUILD_NOW=1` (s19a build-now bypass) skipped the phase-1
proposal round for this session, so no `docs/issue-2203/proposals/`
directory was ever created (untracked — this path does not exist in the
working tree). derived: `git ls-files docs/issue-2203/` — result: only
this record's own path is tracked, no `proposals/` entries (executed
this session). This record has no upstream proposal input.

## Open findings

- The root cause of mechanism (2) — a roster entry missing entirely while
  its spawn-claim and process stay alive, no read/parse error involved —
  is not fully diagnosed. The claim-based cross-check in this fix makes
  `ps` correct regardless of that mechanism, but a future session could
  usefully instrument `roster_register()`/the dead-entry removal path in
  `roster_ps()` to catch it happening in real time (e.g. log every
  `roster_remove()` call with its triggering `_alive()` check) rather than
  relying on the claim-file fallback indefinitely.
- Not evaluated: whether any external tooling parses `spawn.py ps`'s exit
  code and would need to handle the new `2` ("확인 불가") value —
  `roster_ps()` previously always returned `0`. checked: `grep -rn
  "roster_ps()" spawn.py board.py` — result: the only call site is
  `spawn.py:1850` (`return roster_ps()`, the `ps` CLI subcommand
  dispatch) — no in-repo caller branches on its return value today.

## Next steps

None — loop_state is `landed`.
