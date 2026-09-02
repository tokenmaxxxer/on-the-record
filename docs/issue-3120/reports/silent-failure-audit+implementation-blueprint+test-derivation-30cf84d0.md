---
issue: 3120
role: silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0
author: silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: same-commit
type: bugfix
breaking: false
verdict: delivered-partial-scope
upstream:
  - path: N/A (this session's own build; no prior docs/issue-3120/ artifact existed to build on)
    sha:
---

# issue-3120 — silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0 record

## Scope note

This delivers **layers 1 and 2 only** of the three-layer prescription in
the issue body. Layer 3 (automatic re-arm from the turn-driven hook,
`on-the-record/hooks/directive.sh`) and the second, independent defect
(the wake-notice-never-clears bug, also in `directive.sh`) are explicitly
out of scope for this session per the spawning instructions — another
session owns `directive.sh`. This session never opened that file for
writing. The two acceptance checks covering that other scope
(a probe for dead-heartbeat re-arm and a probe for the wake-notice
clearing, named in the issue's Acceptance section but not yet present as
files in this tree) are not part of this delivery and are expected to
land separately.

## What was done

**Layer 1 — classify `rc=95` explicitly.** `on-the-record/monitors/poll-heartbeat.sh`'s
existing crash classification (`watchdog_rc -ge 128 || watchdog_rc -eq 97`)
gained a sibling `elif` branch for `watchdog_rc -eq 95`
(`WATCHDOG_STALE_CODE_SENTINEL`, defined `spawn.py:672-677`, returned
`spawn.py:2577`), emitting its own `[watchdog-stale-code]` line:

```
canonical: on-the-record/monitors/poll-heartbeat.sh:532-540 (derived: git show HEAD:on-the-record/monitors/poll-heartbeat.sh | sed -n '532,540p')
    elif [ "${watchdog_rc}" -eq 95 ]; then
      ...
      printed_text="$(printf '%s\n[watchdog-stale-code] watchdog exited rc=%s (checkout HEAD changed — restarting)' "${printed_text}" "${watchdog_rc}")"
    fi
```

`on-the-record/monitors/poll_heartbeat_delta.py`'s `ALWAYS_RE` (the
line-keyed dedup's always-emit set) gained `watchdog-stale-code` alongside
the pre-existing `watchdog-crash`, so the label survives the delta filter
on the one tick it fires, mirroring the existing convention for the crash
label.

**Layer 2 — self-heal via `exec` instead of dying with nothing to restart
it.** On `rc=95`, after the tick's own output is captured and diffed, the
script re-execs itself in place:

```
canonical: on-the-record/monitors/poll-heartbeat.sh:595-601 (derived: git show HEAD:on-the-record/monitors/poll-heartbeat.sh | sed -n '595,601p')
      _exec_target="${CHECKOUT}/on-the-record/monitors/poll-heartbeat.sh"
      if [ -f "${_exec_target}" ]; then
        printf '[poll-heartbeat] stale code (rc=95) -- restarting via exec %s\n' "${_exec_target}"
        exec bash "${_exec_target}"
      else
        printf '[poll-heartbeat] stale code (rc=95) but restart target unavailable at %s (mid-update?) -- skipping restart this tick\n' "${_exec_target}"
      fi
```

The freshness check itself (`watchdog.py:1867` `watchdog_freshness_check`,
`watchdog.py:1860` `watchdog_current_head`) is untouched — this only
changes what `poll-heartbeat.sh` does with the `rc=95` result it already
receives.

**Two acceptance probes** (`gates/probe_heartbeat_rc95_is_classified.py`,
`gates/probe_heartbeat_survives_head_change.py`) and six pytest cases
added to `on-the-record/monitors/test_poll_heartbeat.py`
(`t_heartbeat_classifies_stale_code_rc95`,
`t_heartbeat_rc95_not_confused_with_crash_rc97`,
`t_heartbeat_routine_nonzero_rc_gets_neither_label`,
`t_heartbeat_stale_code_restart_target_missing_skips_restart_not_crash`,
`t_heartbeat_stale_code_execs_and_keeps_ticking`,
`t_poll_heartbeat_delta_always_emits_stale_code_label`).

canonical: acceptance: `python3 gates/probe_heartbeat_rc95_is_classified.py` — result: ok, rc=0
canonical: acceptance: `python3 gates/probe_heartbeat_survives_head_change.py` — result: ok, rc=0
canonical: acceptance: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` — result: 46 passed
canonical: acceptance: `python3 -m pytest tests/ -q` — result: 254 passed, 0 failed
canonical: acceptance: `python3 -m pytest test/ -q` — result: 15 failed, 548 passed, 3 xfailed (pre-existing, owned by #3091 — unrelated to this diff: failures are in test_convention_equivalence.py, test_local_dependency_env.py, test_spawn_cross_family_skill_selection.py, test_spawn_skill_judge_haiku_timeout_overlap.py, test_spawn_artifact_skill_pairing.py, none of which import or reference poll-heartbeat.sh/watchdog.py/spawn.py's watchdog role)

Both probes were also run against the pre-fix tree (temporarily
`git stash push` on just the two touched non-test files) and both failed
there — probe 1: "produced no distinct '[watchdog-stale-code]'-style
label"; probe 2: "rc=95 was not classified on the tick that hit it" —
confirming the acceptance requirement "both must fail against current
main".

canonical: derived: `git stash push -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/poll_heartbeat_delta.py && python3 gates/probe_heartbeat_rc95_is_classified.py; python3 gates/probe_heartbeat_survives_head_change.py; git stash pop` — result: both FAIL (see exact stderr text quoted above), then git stash pop restored this delivery's code

## Why

**Layer 1 shape.** The new branch mirrors the pre-existing `rc==97`
crash branch exactly (same `printed_text` append idiom, same
`_poll_watchdog_log_append`/delta-filter flow) rather than inventing a
new mechanism, so the label reaches the same Monitor stdout channel and
survives the same dedup logic the crash label already relies on —
verified needed by directly reading `poll_heartbeat_delta.py`'s
`ALWAYS_RE`/`TAG_RE`: neither regex matches a bracket-tag line with no
colon (the exact shape both `[watchdog-crash] watchdog exited rc=%s` and
the new stale-code line use), so without the `ALWAYS_RE` addition the
label would fall through to the pure-hash fallback key and could be
suppressed as "unchanged" on a byte-identical repeat.

canonical: on-the-record/monitors/poll_heartbeat_delta.py:29-41 (derived: git show HEAD:on-the-record/monitors/poll_heartbeat_delta.py | sed -n '29,41p')

**Layer 2 shape — `exec`, not a plain `exit`.** The issue names two things
to establish by running, not reasoning; both were run, not just reasoned
about, in this session's own sandbox:

1. **pid/fd preservation across `exec`.** A minimal script
   (`exec "$0" second`) run under `wait $!` printed the identical pid
   before and after the exec. A second script redirected its stdout into
   a fifo, wrote a line, exec'd itself, and a concurrent background
   reader consuming that fifo captured both the pre- and post-exec lines
   with no gap — the reader never observed a close/reopen event.
   canonical: derived: two throwaway scripts run directly in this
   session's own Bash tool (not committed; not part of the deliverable)
   — captured output `FIRST-STAGE pid=3420698 before-exec` /
   `SECOND-STAGE pid=3420698 writing-through-inherited-fd`, one
   continuous fifo capture across the exec.
2. **The mid-update exec-into-nothing failure mode.** A script that
   `exec`'d a path with no file there printed bash's own
   "No such file or directory" and the calling process exited 127 —
   the line after the `exec` call was never reached. canonical: derived:
   same session, throwaway script, captured output
   `wrapper-saw-exit-code=127`.
3. **Whether the platform's own live Monitor wrapper tracks pid or
   pipe, specifically.** This session's own Monitor process for
   on-the-record itself was inspected read-only.
   canonical: derived: `ps -ef | grep poll-heartbeat` (found a live
   `bash .../poll-heartbeat.sh`, pid 3387957, parent 3387955 running the
   harness's `eval ... < /dev/null` wrapper) followed by
   `ls -la /proc/3387955/fd /proc/3387957/fd`: both the wrapper and the
   child share the SAME stdout/stderr socket inodes
   (`socket:[1053022360]`, `socket:[1053022362]`), i.e. inherited file
   descriptors, not a per-process reopen. This establishes the wrapper's
   plumbing is fd-based (consistent with a pipe/pid-inheriting model
   that `exec` does not disturb), but this session deliberately did
   **not** signal, kill, or `exec` that live process itself to test
   restart behavior end-to-end against the real wrapper — that process is
   this session's own active infrastructure, a shared, hard-to-reverse
   resource, and experimenting on it risked breaking this very session's
   monitoring. unverifiable: full end-to-end confirmation that the real
   platform Monitor wrapper survives an `exec`-based restart without any
   gap it would treat as failure — the fd-sharing observation is strong
   supporting evidence (same mechanism the synthetic fifo test in point 1
   confirms is transparent to a downstream reader) but this session chose
   not to run the live, irreversible experiment needed to close that gap
   completely; that residual is honestly named here rather than asserted
   as proven.

Given points 1–3, `exec` is the right mechanism: it is the only one of
the three that keeps the SAME pid and the SAME inherited fds throughout,
which is what a pipe- or pid-tracking wrapper both need to see an
uninterrupted live monitor.

**Guard before exec, not after.** Point 2 above is why the exec target's
own presence is checked immediately before the `exec` call, reusing the
existing `[ ! -f "${CHECKOUT}/spawn.py" ]` guard's pattern (issue #2163,
`on-the-record/monitors/poll-heartbeat.sh:495-505`) rather than trusting
the top-of-loop check (which ran up to ~120s + `roster_watchdog()`'s own
runtime earlier, too stale a signal for a mid-update race).

canonical: on-the-record/monitors/poll-heartbeat.sh:495-505 (derived: git show HEAD:on-the-record/monitors/poll-heartbeat.sh | sed -n '495,505p')

**Residual TOCTOU, named rather than silently shipped
(silent-failure-audit finding).** The `[ -f "${_exec_target}" ]` check and
the `exec bash "${_exec_target}"` call are two separate commands, not one
atomic operation — a concurrent external process (a second, independent
marketplace update racing this exact instant, distinct from the one that
already completed inside the `spawn.py watchdog` call that produced this
tick's `rc=95`) could still leave the file mid-write in that narrow
window. If that happens, `exec bash` would hit a bash parse error on a
truncated file and the whole Monitor process would die anyway,
unguarded — the exact failure class this issue exists to close, now
reachable only through this much narrower window. This is not eliminated
in this delivery, for two reasons: (a) it is the same class of accepted,
narrow risk the pre-existing top-of-loop guard already carries by design
(issue #2163's own comment documents an equivalent window for the
directory-level case), so this delivery's exposure is not a new risk
category, only a second, narrower instance of one already accepted in
this file; (b) eliminating it (e.g. copy-then-exec-the-copy, or a retry
loop) is exactly the kind of "re-arm more aggressively" scope-widening
the issue's must-not list warns against for adjacent problems, and was
judged not worth the added complexity for a window this narrow without a
live incident motivating it, the same bar the issue itself applied to
Layer 3. Flagged here as an open finding rather than silently accepted
without a record.

**Test derivation.** `watchdog_rc` is treated as the input under
equivalence partitioning: `{rc >= 128 or rc == 97 (crash, pre-existing)},
{rc == 95 (stale-code, new)}, {any other value (routine anomaly count,
issue #1274's own contract for roster_watchdog()'s return value)}`. All
three partitions now have a pinned test
(`t_heartbeat_rc95_not_confused_with_crash_rc97`,
`t_heartbeat_classifies_stale_code_rc95`,
`t_heartbeat_routine_nonzero_rc_gets_neither_label` — the third was added
after invoking the test-derivation skill mid-session flagged it as the
one partition still missing from the initial pass, see skill-verdict
below). The exec target's existence is a second, independent boundary
(`present` / `absent`), covered by
`t_heartbeat_stale_code_execs_and_keeps_ticking` and
`t_heartbeat_stale_code_restart_target_missing_skips_restart_not_crash`.

## What did not work

None — no approach was tried and abandoned. The one place this session
stopped short of full coverage (the TOCTOU window above, and item 3 in
"Why" above) is a deliberate scope/safety decision, not a failed attempt,
and is recorded as an open finding below rather than under this heading.

## Upstream basis

No prior `docs/issue-3120/` artifact existed at session start beyond the
pre-written skeleton this record fills in — no proposal/, no survey/.
canonical: derived: `ls docs/issue-3120/reports/` (result: only
`silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md`,
the skeleton, present before this session's edits). Upstream basis is the
GitHub issue itself, canonical: `gh issue view 3120` output (verbatim
quoted inline in this session's own transcript and used directly to
derive the acceptance checks), plus direct code reading of
`spawn.py:672-677,2564-2578`, `watchdog.py:1860-1907`, and
`on-the-record/monitors/poll-heartbeat.sh` (pre-change) performed live in
this session.

## Open findings

1. **Live-wrapper `exec` confirmation covers fd-sharing only, not a real
   end-to-end restart against the platform wrapper.**
   canonical: derived: `ls -la /proc/3387955/fd /proc/3387957/fd` (this
   session's own live Monitor process — same inspection cited under "Why"
   point 3): fd-sharing was confirmed by direct, read-only inspection of
   this session's own real Monitor process; a full
   restart-survives-under-the-real-wrapper test was deliberately not run
   against that live process (shared, hard-to-reverse resource). No
   further resolution attempted in this session — the fd-sharing evidence
   plus the synthetic fifo-transparency test together are judged
   sufficient grounds to ship, but a future session with a disposable
   Monitor-armed sandbox could close this residual gap.
2. **Residual exec-target TOCTOU window** (see "Why", "Residual TOCTOU"):
   accepted, not eliminated, for the reasons stated there. Resolution
   path, if a live incident ever motivates it: copy the exec target to a
   private tmp path immediately after the existence check and exec that
   copy instead of the live path, closing the window at the cost of one
   extra file copy per stale-code tick (rare by construction).
3. **Layers 3 and the wake-notice bug are explicitly not addressed here**
   (see "Scope note") — tracked by the other session's ownership of
   `on-the-record/hooks/directive.sh`, not by this record.

## Next steps

None from this session for layers 1/2 — canonical: acceptance: all six
check commands quoted under "What was done" above were run in this
session and their results recorded there. A PR is opened from this
branch per the build-now bypass; the PR trailer names `Advances #3120`
(not `Closes`), since layers 3 and the wake-notice fix remain — this is
intentional partial delivery, per this session's phase-2 preflight
guidance for that shape.

skill-verdict: silent-failure-audit — applied: invoked; audited the new `elif watchdog_rc -eq 95` branch and the exec-target existence guard in on-the-record/monitors/poll-heartbeat.sh, classified both as Handled, and surfaced the exec-target TOCTOU gap as an Unguarded (accepted-risk) finding, recorded above under "Open findings" item 2.
skill-verdict: test-derivation — applied: invoked; used equivalence partitioning on watchdog_rc and boundary analysis on exec-target existence; the invoke itself flagged the missing "routine nonzero rc" partition, which was then added as t_heartbeat_routine_nonzero_rc_gets_neither_label.
skill-verdict: implementation-blueprint — not-applicable: single-file bugfix extending an existing, already-established branch/guard structure in one bash script — no new module boundary or architecture decision to select a structure for.
other mounted skills: not triggered (work-in-english followed as house convention without a separate invoke; parallel-decomposition/implementation-audit/test-depth-audit/agent-coordination do not match a solo single-file bugfix with no fan-out).
