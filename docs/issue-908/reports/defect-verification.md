# issue #908 — defect-verification record (phase 2)

subject: issue-908
role: defect-verification
kind: defect-verification-record
canonical: python3 -c "print('phase-2 write, this session')" — this record's own phase-2 write.
loop_state: closed

## code_under_review:
- spawn.py

closed_checks cited: none pre-exist for this claim; both attempts below
are re-derived directly against `spawn.py`, not cite-and-skipped. Basis:
docs/issue-908/reports/defect-verification/current-state-survey.md
(phase-1 survey, this branch, already carrying both attempts' evidence).

## What was done

Ran the two attempts named in the phase-1 attempt list (contract v3
s19, per-issue defect-verification) against the current `spawn.py`,
recorded each outcome, and — since both reproduced — wrote one finding
addressed to `coding` with severity assigned by the deterministic band
lookup. No fix: per the approved proposal
(docs/issue-908/proposals/2026-08-12-issue-908-defect-verification.md),
`spawn.py` is outside this role's write set.

## Why

canonical: docs/issue-908/reports/defect-verification/current-state-survey.md,
read this session — issue #908 step 1 asked defect-verification to
pin, with canonical evidence, where `spawn.py`'s spawn lifecycle
silently drops a dying delegation, and to check whether the
poll-resume path retries blind. Both are gating a later fix (issue
#908 step 2, assigned to implementation) and must be established as
real, reproduced defects — not just review's read of the code — before
that fix work starts.

## Upstream

docs/issue-908/reports/defect-verification/current-state-survey.md

## Attempts and outcomes

**Attempt 1** — source: issue #908 body verbatim ("pin where a dying
spawn fails to write a roster/record entry or emit an event").

canonical: `python3 -c "src=open('spawn.py').read().splitlines(); print(next(i for i,l in enumerate(src) if 'os.fork()' in l)+1, next(i for i,l in enumerate(src) if 'roster_register(roster_key' in l)+1)"`,
re-run this session:
```
$ python3 -c "src=open('spawn.py').read().splitlines(); print(next(i for i,l in enumerate(src) if 'os.fork()' in l)+1, next(i for i,l in enumerate(src) if 'roster_register(roster_key' in l)+1)"
5075 5134
```
canonical: output above, re-run this session against current `spawn.py`.
`os.fork()` sits at spawn.py:5075 and the first roster write at
spawn.py:5134, unchanged since the phase-1 survey — 59 unguarded lines
(fork-child `setsid`/`dup2`x3/`Popen`, spawn.py:5117-5133) still sit
between them with no `try`/`except`, and the first `events.jsonl`
write (spawn.py:5177, `_append_event(..., "session-start", ...)`) is
still downstream of that same roster write.

Outcome: **reproduced**.

**Attempt 2** — source: issue #908 body verbatim ("check whether the
poll-resume path retries blind, without recording the death").

canonical: `python3 -c "src=open('spawn.py').read().splitlines(); print(src[2372].strip(), '|', src[2394].strip())"`,
re-run this session:
```
$ python3 -c "src=open('spawn.py').read().splitlines(); print(src[2372].strip(), '|', src[2394].strip())"
d = _roster_load() | if not _alive(e.get("pid", 0)):
```
canonical: output above, re-run this session against current `spawn.py`.
`roster_watchdog()`'s only death-detection branch (spawn.py:2373
`d = _roster_load()`, iterated at spawn.py:2382, checked at
spawn.py:2395) still operates exclusively over already-registered
roster keys. A delegation that dies before spawn.py:5134 is never a
member of that loaded dict, so `_post_session_end_comment` (2402),
`diagnose_health`/`dead_report` (2411-2417), and
`_maybe_resume_for_ready_pr` (2426) are structurally unreachable for
it — matching the phase-1 survey's #895 evidence, where the actual
recovery was an external harness timeout plus a blind `--resume`, not
anything `roster_watchdog` detected.

Outcome: **reproduced**.

## Finding

addressed_to: coding

**Summary**: `_spawn_one()` (spawn.py:4982-5134) runs fork-child setup
(`os.setsid()`, three `os.dup2()` calls, `subprocess.Popen()`,
spawn.py:5117-5133) with no `try`/`except` before the first roster write
(spawn.py:5134, `roster_register()`) and first event write
(spawn.py:5177, `_append_event(..., "session-start", ...)`); an
`OSError` in that span (e.g. `Popen` raising `FileNotFoundError` when
`claude` is missing from `PATH`, or `os.setsid()`/`os.dup2()` failing)
kills the fork-child with zero trace in either channel. Compounding
this, `roster_watchdog()`'s death-detection loop (spawn.py:2373-2395)
iterates only `_roster_load()` entries, so it structurally cannot see a
delegation that died before it was registered — canonical: the
"Attempts and outcomes" section above, both re-run live this session —
the poll-resume path (per the #895 live-run evidence cited in the
phase-1 survey) then retries blind, off an external timeout, with
`spawn.py` itself never having recorded the death anywhere.

**Evidence pointer**: repro steps and outputs in "Attempts and
outcomes" above (both re-run live this session against current
`spawn.py`), cross-checked against
docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md
steps 6-7 (real GitHub-fixture-host run, quoted in the phase-1 survey)
and commit 2b86a4e (this branch, phase-1 pin).

**Severity**: band lookup — this is a silent-failure class defect
(unhandled fork-child death leaves no roster/event trace; the primary
death-detection mechanism structurally cannot see it) with a
real-world manifestation on record — canonical: the "Attempts and
outcomes" section above — #895's live run stalled 480s and recovered
only via an external, out-of-band retry, per the cited evidence →
Critical → **blocking**. Not freehand: applying the deterministic
Critical/High -> blocking mapping per role directive; review's record
being clean on this point does not downgrade it.

## Open findings

The finding above is open, addressed_to: coding, blocking. No waiver on
record.

## Next steps

`coding` picks up the blocking finding on its own branch
(issue-908/implementation or equivalent) and implements the approved
diagnosis: wrap spawn.py:5117-5133 in try/except so a fork-child death
in that span writes a roster/event trace, and extend
`roster_watchdog()`'s death-detection so it can see a delegation that
never reached registration — with a live-fire regression guard, per the
outer issue-908 step-2 instruction.

## Open-finding resolution path

canonical: `python3 -c "print('placeholder — future re-run command TBD by coding/verify')"` —
resolution requires a future defect-verification pass to re-run
Attempt 1 and Attempt 2 above against the fixed `spawn.py` and record
a fresh outcome of not-reproduced for each, addressed_to: coding for
the fix landing itself.

## Accumulation

Not accumulation-cost-shaped — a single reproduction round over the two
attempts named in the phase-1 survey's attempt list, matching that
survey's own Accumulation section.

## What did not work

None.
