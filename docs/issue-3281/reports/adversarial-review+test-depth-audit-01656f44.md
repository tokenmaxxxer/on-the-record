---
issue: 3281
role: adversarial-review+test-depth-audit-01656f44
author: adversarial-review+test-depth-audit-01656f44
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true
loop_state: done
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3282
    sha: b5a83907cdcb3000d472f3ed6e269b2d85ce44b9
  - path: docs/issue-3281/reports/silent-failure-audit+test-derivation-e073366a.md
    sha: b5a83907cdcb3000d472f3ed6e269b2d85ce44b9
---

# issue-3281 — adversarial-review+test-depth-audit-01656f44 record

## What was done

Independent verification of PR #3282, focused on the axis the
orchestrator's own pre-check had not covered: does the bash-3.2 array
guard actually hold on real bash 3.2, and do the two *other*
`KNOWN_PROC_SITES` entries meet the runtime-visibility bar this PR held
its own new entry to. Did not repeat the orchestrator's already-checked
ground (both acceptance checks pass; reverting the guard re-fails the
check; `os.path.isdir`-mocked `NoProcOnPlatform` path).

**1. Real bash 3.2, not a bash-5 argument.**

canonical: `docker pull bash:3.2` — result: `Status: Image is up to date for bash:3.2`, `docker.io/library/bash:3.2`.

derived: `docker run --rm bash:3.2 bash -c 'echo $BASH_VERSION'` — result: `3.2.57(1)-release`.

Checked out PR head `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9` into
`/tmp/pr3282-wt` via `git worktree add`. Reproduced the bug on the
*pre-fix* form first, to prove the reproduction itself is real:

derived: ran, under `bash:3.2` with `set -euo pipefail; UNSET_ARGS=()`, the verbatim original form `env "${UNSET_ARGS[@]}" true` — result:
```
/repro.sh: line 4: UNSET_ARGS[@]: unbound variable
exit=1
```
Confirms bash 3.2 genuinely treats a zero-element array as unbound under
`set -u`.

Then drove the *actual* `UNSET_ARGS`-construction loop copied verbatim
from `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:scripts/issue-3041/run_pair.sh`
lines 53-56 (`while IFS= read -r var; do UNSET_ARGS+=(-u "$var"); done <
<(env | grep -oE '^(CLAUDE|MUSTER)_[A-Z0-9_]*' | sort -u)`) through
`bash:3.2`, both with the pre-fix line and the fixed line, in the two
real shapes that loop produces:

derived: original (unguarded) form, container `env` carrying no `CLAUDE_*`/`MUSTER_*` vars (`UNSET_ARGS` ends up empty — the common case; this orchestrator's own shell carries no such vars either) — result:
```
case A with ORIGINAL unguarded form:
/s.sh: line 8: UNSET_ARGS[@]: unbound variable
---outer exit=1
```

derived: fixed (`${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"}`) form, same empty-array case — result:
```
UNSET_ARGS count: 0
case A survived, exit=0
```

derived: fixed form, `docker run --rm -e CLAUDE_FOO=x -e MUSTER_BAR=y ...` (non-empty `UNSET_ARGS`) — result:
```
UNSET_ARGS count: 4
OK: correctly stripped
```
(`env | grep -E '^(CLAUDE_FOO|MUSTER_BAR)='` found neither var — `-u` still strips both correctly with the guard in place.)

derived: re-ran the same three cases on this host's own bash — `bash --version` reports `GNU bash, 버전 5.1.16(1)-release` — result: all three behave identically in shape (empty array survives *both* the guarded and the original unguarded form on bash 5.1.16 — `env "${UNSET_ARGS[@]}" true` printed `OK: original survives empty array on bash5 (exit 0)`; the non-empty case strips `FOO`/`BAZ` the same way as under bash 3.2). This is exactly why a bash-5-only dev/CI shell never caught the bug, and directly confirms must-not #2 (the guard changes nothing for a non-empty array) on both bash versions rather than by reading the diff.

derived: `docker run --rm -v /tmp/pr3282-wt/scripts/issue-3041/run_pair.sh:/run_pair.sh bash:3.2 bash -n /run_pair.sh` — result: `bash3.2 syntax OK` (beyond the PR's own bash-5 `-n` check).

**2. The other two `KNOWN_PROC_SITES` entries — roster.py and watchdog.py.**

canonical: `git diff origin/main -- test/test_proc_identity_degradation_visibility.py` (run from `/tmp/pr3282-wt`) — result: empty diff; `git show origin/main:test/test_proc_identity_degradation_visibility.py` — result: succeeds (file already on `main`, untouched by this PR). Both sites predate PR #3282: `git log --oneline --all -- test/test_proc_identity_degradation_visibility.py` — result: single commit `71167c3a issue-2924: standing macOS/bash-3.2 compat check + runtime-visible /proc identity degradation (#2955)`.

Read both degrade paths directly rather than trusting the allowlist
comment at `on-the-record/checks/macos_bash32_compat.py:65` (this
branch's own copy — `KNOWN_PROC_SITES = {"roster.py", "watchdog.py"}`,
unchanged from `main` here since this record doesn't touch it):

- `roster.py:47-61` (`_note_proc_identity_degraded`) prints
  `[proc-identity] {site}: ...` **unconditionally**, once per process,
  the first time either `_watcher_looks_real()` or `_session_looks_real()`
  degrades for lack of `/proc` — regardless of what the caller does with
  the (weaker) liveness verdict it gets back. Confirmed via the
  pre-existing test class in `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:test/test_proc_identity_degradation_visibility.py`
  (`ProcIdentityNoteTest.test_note_prints_exactly_once_per_process`,
  `test_watcher_looks_real_notes_when_proc_unavailable`).
- `watchdog.py`'s `_proc_start_time()` degradation is narrower: the
  runtime notice (the `"신원 확인 불가"` substring inline in the returned
  message) only appears inside `watchdog_lock_acquire()`'s **refusal**
  branch (`b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:watchdog.py` around
  line 1878, `degraded_note = ... if other_start is None else ""`) — i.e.
  only when a stale/reused-pid lock spuriously "matches" via `None ==
  None` and blocks a new watchdog from starting. On the ordinary,
  uncontended startup path the function writes
  `{"pid": ..., "start_time": None}` to the lock file and returns
  `(True, "")` — no print anywhere on that path.

canonical: `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:spawn.py` lines 2647-2649:
```python
ok, msg = watchdog_lock_acquire()
if not ok:
    print(msg)
    return WATCHDOG_LOCKED_SENTINEL
```
`msg` (empty string on the success path) is only ever printed when `ok`
is `False`, confirming directly from the caller (not inferred) that a
successful, degraded macOS acquire prints nothing to any operator.

Neither site "fails open" — both keep denying/weakening exactly as
documented, never silently pretending full verification succeeded. But
they sit at different points on loud-vs-silent: `roster.py` is loud on
every degraded call; `watchdog.py` is loud only in the one branch where
the degradation could produce an operator-visible wrong verdict, silent
on the far more common plain-startup branch. See Open finding #1.

**3. Must-nots.** Linux `/proc` reads:

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` (from `/tmp/pr3282-wt`, real Linux host, no mocking) — result:
```
84 passed in 0.96s
```
Nothing in the PR's diff touches the pre-existing Linux-path assertions
in that file (`git diff origin/main -- tests/test_amendment_channel.py`
only adds one new test method, quoted in Open finding #2 below — it does
not modify any existing test body). Shell-guard parity for non-empty
arrays: covered in §1 above, confirmed on both bash 3.2 and bash 5.1.16
directly, not inferred from the diff.

**4. Scope claim.**

canonical: `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:docs/issue-3281/reports/silent-failure-audit+test-derivation-e073366a.md`
lines 173-190 ("Open findings" section) — states plainly: "A green check
is not a macOS-works claim. This fix makes the static check pass, and
passing it is necessary but not sufficient for the macOS axis — it does
not prove `run_pair.sh` or the amendment channel actually execute
correctly on macOS. No macOS/bash-3.2 install-and-run of R007 was
performed by this session." Not overstated. It also candidly records
that session had no bash-3.2 shell reachable ("no macOS or bash-3.2
environment was reachable from this session") — the specific gap this
record's §1 fills with a real bash-3.2 run.

## Why

The task's four questions are each independently falsifiable by either
running real bash 3.2 or reading the two grandfathered `/proc` sites'
actual code paths, so that is what this record did for all four, rather
than trusting the PR's or the orchestrator's own prose.

## What did not work

None.

## Upstream basis

- PR #3282, head `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9` — the code
  under review; checked out into `/tmp/pr3282-wt` via `git worktree add`
  (removed at the end of this session via `git worktree remove --force`,
  confirmed via `git worktree list` showing only this session's own
  worktree afterward).
- `origin/main` at `7d857d5f` — checked out into `/tmp/main-wt` for
  parity comparison (also removed at the end of this session).
- Issue #3281 — canonical: `gh issue view 3281 --repo tokenmaxxxer/on-the-record`.
- `docker.io/library/bash:3.2` — the real bash-3.2 environment used for
  §1, pulled fresh this session.

## Open findings

1. **`watchdog.py`'s /proc-degradation notice is narrower than
   `roster.py`'s, and narrower than the bar this PR held its own new
   `amendment_channel.py` entry to (informational, not a defect in this
   PR).** The check's rule
   (`on-the-record/checks/macos_bash32_compat.py:34-41`, this branch's
   own copy) requires a runtime-visible notice "before it is added to
   the reviewed set" — a forward-looking gate on *new* entries.
   `roster.py`/`watchdog.py` are not new entries: both landed in issue
   #2924 (commit `71167c3a`), and PR #3282 does not touch either file
   (see §2 above). So this is not something PR #3282 broke or is
   obligated to fix. But the asymmetry found in §2 is real and worth
   naming: on an uncontended macOS watchdog startup (the ordinary case),
   nothing tells an operator that identity verification is running
   degraded — only a *misfire* (a stale lock spuriously blocking a new
   watchdog) surfaces the `"신원 확인 불가"` note, and only inside that
   refusal message (confirmed via the `spawn.py:2647-2649` caller quoted
   in §2, which only prints `msg` on the `not ok` branch). Resolution
   path, if anyone picks it up: an unconditional once-per-process notice
   on `watchdog_lock_acquire()`'s success path too, mirroring
   `roster.py`'s `_note_proc_identity_degraded()` pattern (print once,
   not per lock acquisition).

2. **Test-depth gap: the shell-side fix has no automated test that
   executes the guard, only a static pattern-match lint (informational).**
   `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:on-the-record/checks/macos_bash32_compat.py`
   line 71 (`_ARRAY_BARE_RE`) and line 72 (`_ARRAY_GUARD_MARK = "[@]+"`)
   define a textual scan for the literal `[@]+` marker string on the same
   line as `${VAR[@]}` — it proves the marker string is present, not that
   bash 3.2 actually survives the expansion.

   derived: `grep -rln "run_pair.sh\|UNSET_ARGS" test/ tests/` (from `/tmp/pr3282-wt`) — result: no output, zero matches. No pytest (or other) test executes `run_pair.sh`'s `UNSET_ARGS` handling under any bash.

   The PR's own test plan (`gh pr view 3282 --repo tokenmaxxxer/on-the-record --json body -q .body`) lists `bash -n scripts/issue-3041/run_pair.sh — syntax OK` and a prose "Manual bash-5 boundary check", neither of which is an automated regression test — only the marker-string lint (`python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -q`) re-runs on every `pytest` invocation. This session's §1 above is, as far as this record can establish, the first actual bash-3.2 execution of this code path in this issue's history, and it required a one-off `docker pull` this repo's own test suite does not currently automate.

   The one *new* Python test this PR does add,
   `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9:tests/test_amendment_channel.py`
   (`RecordAmendmentFromResponse.test_no_proc_on_platform_is_fail_closed_with_a_distinct_notice`),
   classified per test-depth-audit as **Genuine Assertion**: asserts the
   specific result type (`isinstance(result, ac.NoProcOnPlatform)`, and
   explicitly `assertNotIsInstance(result, ac.NoRegisteredRepo)`),
   asserts no marker file was written (`assertIsNone(ac.read_marker(...))`),
   and asserts both `"no /proc"` and `"macOS"` appear in the stderr
   notice; mocks only `os.path.isdir` for the literal `/proc` path with a
   real fallback (`side_effect=lambda p: False if p == "/proc" else
   real_isdir(p)`) for every other path, so it is not mock-dominated.

   acceptance: `python3 -m pytest tests/test_amendment_channel.py -k no_proc_on_platform -q` (from `/tmp/pr3282-wt`) — result:
   ```
   1 passed in 0.90s
   ```
   Not a defect, but the concrete cash-out of the PR's own "necessary,
   not sufficient" caveat (§4 above): the sufficiency gap for the shell
   half specifically is "no CI-runnable bash-3.2 execution exists," not
   only "no macOS box was tried."

## Next steps

None from this record — read-only independent verification, no build
phase opened. Findings #1 and #2 are informational follow-up for whoever
next touches this subsystem; per the task's explicit "do not edit or
merge PR #3282," this record does not act on them itself.

skill-verdict: adversarial-review — applied: invoked; ran the
independent-verification protocol against PR #3282 as a structurally
separate session (spawned fresh, no shared context with the PR's builder
session) — re-derived every claim in scope directly (a real bash-3.2 run
via `docker`, direct reads of `roster.py`/`watchdog.py`/`spawn.py`, a
standalone rerun of the new test) rather than trusting the PR's or
orchestrator's prose.

skill-verdict: test-depth-audit — applied: invoked; classified the one
new test PR #3282 adds as Genuine Assertion (Open finding #2), and
separately identified that the shell-side fix -- the PR's other half --
has no automated test at all beyond a static marker-string lint; only a
real bash-3.2 execution (performed by this record, not by the PR) proves
the guard's actual runtime effect.

other mounted skills: not triggered (defect-verification-independence-from-upstream-verdicts,
technical-feasibility-reversibility-tag, product-discovery-guardrail-metrics,
implementation-audit, flow-metrics, prose-modes were surfaced by
post-dispatch skill_judge amendments but the Skill tool did not recognize
them by name in this session; their guidance where applicable --
re-deriving rather than citing upstream verdicts, treating a
not-reproduced claim with the same rigor as a reproduced one -- was
followed in substance throughout this record, e.g. §1's from-scratch
bash-3.2 reproduction of the pre-fix bug before trusting the fix, even
though the skills themselves could not be invoked through the Skill
tool).
