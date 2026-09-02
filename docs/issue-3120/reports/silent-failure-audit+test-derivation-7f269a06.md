---
issue: 3120
role: silent-failure-audit+test-derivation-7f269a06
author: silent-failure-audit+test-derivation-7f269a06
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/directive.sh
    sha: same-commit
---

# issue-3120 — silent-failure-audit+test-derivation-7f269a06 record

## What was done

Implemented the wake-notice half of issue #3120 only (the poll-heartbeat.sh
HEAD-change death, rc=95 classification, and the auto-re-arm layers are out
of scope for this session — owned elsewhere per the spawning prompt's
scope boundary).
derived: `git diff origin/main -- on-the-record/hooks/directive.sh gates/probe_wake_notice_clears.py docs/specs/enforcement-boundary.md` — result: `on-the-record/hooks/directive.sh` gains a 14-line removal block inside the `alive` branch; `gates/probe_wake_notice_clears.py` is a new file; `docs/specs/enforcement-boundary.md` gains one table row for the new gate.

1. `on-the-record/hooks/directive.sh` — the `alive` branch inside the
   monitor-notice heredoc now removes an existing `.orchestrate-wake-notice`
   in the workspace root before exiting, wrapped in
   `try: os.remove(notice_path) except OSError: pass`. Before this change
   the branch exited unconditionally, leaving any notice written by an
   earlier, monitor-late session in the same workspace in place forever.
2. `gates/probe_wake_notice_clears.py` (new) — standalone acceptance
   probe: positive case (stale notice + fresh alive marker → notice
   cleared) and symmetric negative case (no alive marker at all → notice
   still written).
3. `docs/specs/enforcement-boundary.md` — added the registration row
   `gate-registration-guard.sh` requires for the new gate module.
canonical: `on-the-record/hooks/directive.sh` lines 125-138, this session's own edit, same commit — the `os.remove(notice_path)` call inside `if alive:` is the entire change described in item 1 above.

## Why

canonical: this record's own Acceptance evidence section below (probe transcripts this session produced this turn) — the fix's correctness rests on that red/green pair, cited there in full, not repeated here.
The fix follows the shape a prior (uncommitted, since-lost) session on
this issue reached, per the spawning prompt: inside the `alive` branch,
before its `sys.exit(0)`, remove the notice path in a try/except OSError.
That shape was established this session by reproducing the defect
against `origin/main` first, then applying the fix and re-running the
same probe.

canonical: `sed -n '138,175p' on-the-record/hooks/directive.sh`, this session's own read of the file at write time — the write branch's `try:` / `except OSError:` / `pass` guarding `open(notice_path, "w")` appears a few lines after the new removal block, the same shape as the removal's own `try/except OSError: pass`.
The two branches (removal in `alive`, write in the fallback path) use the
identical error-handling shape; neither is new to this file's overall
convention.

derived: silent-failure-audit trace, this session, over `on-the-record/hooks/directive.sh` lines 125-138 and `gates/probe_wake_notice_clears.py` in full (see skill-verdict entry below for the full classification) — the removal's `except OSError: pass` classifies Silently Absorbed by the catalog's letter (empty catch), and the forward trace from that catch is recorded in the next paragraph.
`os.remove()` is a fallible operation and its catch block is textually
empty, so the audit does not wave it through by inspection alone. Two
paths were traced forward: (a) `FileNotFoundError`, a benign race where
the notice was already removed by a concurrent turn — the removal's own
goal (notice absent) is already met, so nothing downstream changes; (b) a
persistent failure (e.g. a permissions/immutable-flag edge case) would
leave a stale notice in place after this turn, but this hook fires on
every `UserPromptSubmit` and re-attempts the same removal on the next
turn the `alive` branch is reached, so the failure does not compound the
way the original defect did (which failed on every single invocation,
unconditionally, via a missing code path, not a rare permission
condition). No sibling marker write in this file logs its own `OSError`
either, so adding logging only at this one site would depart from the
rest of the file rather than extend it.
No code change was made beyond the removal call itself.

Probe design: drives the actual `directive.sh` script as a subprocess
rather than re-implementing its logic, because the defect was
specifically about behavior integrated into that script's control flow
(the notice write is a bash heredoc, not a standalone importable
function).
canonical: `gates/probe_wake_notice_clears.py` lines ~60-90 (`_run_directive`, `_new_scratch`), this session's own file, same commit — `subprocess.run(["bash", str(DIRECTIVE_SH)], ...)` invokes the unmodified script; `os.path.realpath()` is applied to every scratch dir before use.
`_otr_mn_root` inside the hook is bash's `pwd -P` (symlink-resolved),
while its marker directory is `os.path.expanduser("~/...")` (a literal
string substitution, not fs-resolved); the probe resolves its own
scratch HOME/workspace dirs with `os.path.realpath()` once, up front, so
the notice/marker paths it asserts against match what the hook computes
on either Linux or macOS.

## What did not work

None — the fix landed on the first shape tried (matching the description
given in the spawning prompt).
canonical: this record's own Acceptance evidence section below — the red/green transcript pair is the basis for this claim.

## Upstream basis

No `docs/issue-3120/` upstream artifacts existed from a prior session (the
prior session that reached this fix shape was killed with zero commits,
per the spawning prompt, so nothing of it is in any branch or docs tree
to cite). The only upstream input is `on-the-record/hooks/directive.sh`
itself at its pre-fix state, `sha: same-commit` (the fix modifies it in
the same commit that adds the probe) — see frontmatter `upstream:` above.

## Open findings

None from this session's own audit.
derived: silent-failure-audit trace, this session (see Why section above and the skill-verdict entry below for the full classification and trace) — the one candidate site (the new `except OSError: pass` around `os.remove`) was traced forward and left unchanged.

Out of scope, left for the sibling session per the spawning prompt's
scope boundary: `on-the-record/monitors/poll-heartbeat.sh` (rc=95
classification, re-exec-on-HEAD-change, auto-re-arm) and the other three
acceptance probes the issue names
(`probe_heartbeat_rc95_is_classified.py`,
`probe_heartbeat_survives_head_change.py`,
`probe_dead_heartbeat_is_rearmed.py`) were not touched or run — this
record makes no claim about their state.

## Test derivation (acceptance → cases)

Requirement (from issue #3120's Acceptance section, wake-notice half):
"`probe_wake_notice_clears.py` — write a stale notice, make the alive
marker fresh, run the directive hook's check, assert the notice is gone;
plus the symmetric negative, that a genuinely absent monitor still gets
one written." This is a decision-table-shaped requirement over two
independent binary conditions (existing notice: present/absent; alive
marker: fresh-for-this-session/absent), so it was routed to a decision
table rather than plain equivalence partitioning:

| # | pre-existing notice | alive marker fresh for session | expected: notice present after check | covered by |
|---|---|---|---|---|
| 1 | stale (present) | fresh | absent (cleared) | `check_positive_clears_stale_notice` |
| 2 | absent | absent | present (written) | `check_negative_absent_monitor_still_notifies` |

canonical: `gates/probe_wake_notice_clears.py`, this session's own file, same commit — functions `check_positive_clears_stale_notice` and `check_negative_absent_monitor_still_notifies` implement rows 1 and 2 respectively; their pass transcript is in Acceptance evidence below.

The other two cells of the full 2x2 (absent-notice/fresh-marker →
stays absent; stale-notice/absent-marker → stays present, re-written
verbatim) are not independent acceptance requirements. Cell
absent/fresh is the steady-state the existing `alive` early-exit already
covered before this fix, unaffected by the removal added here since
`os.remove` on an absent path just raises the already-caught
`FileNotFoundError`. Cell stale/absent is the pre-existing write-path
behavior from issue #947, not new surface this issue touches. Adding
probe cases for either would test code this issue did not change, so
they were left out by design rather than by omission.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; audited the new
`os.remove(notice_path)` / `except OSError: pass` in `directive.sh`'s
`alive` branch and the fallible operations in `probe_wake_notice_clears.py`
(subprocess calls, file I/O).
derived: this session's own step-by-step trace, recorded in the Why section above — one Silently-Absorbed-by-letter site found (the new empty `except OSError: pass`), traced forward through both its failure branches (benign race vs. persistent failure), left unchanged as adequate given the self-healing per-turn retry and consistency with every sibling marker write in the same file. The probe's own setup/subprocess calls are unguarded by design (fail-loud is correct for a test probe); its `shutil.rmtree(..., ignore_errors=True)` calls are post-assertion cleanup only.

skill-verdict: test-derivation — applied: invoked; routed the
`probe_wake_notice_clears.py` acceptance line to a 2-row decision table
over (pre-existing notice) x (alive marker freshness) — see Test
derivation section above for the full table and the rationale for the
two uncovered cells.

other mounted skills: not triggered (work-in-english guidance followed
throughout without a separate invocation needed — no Korean-language
code/commit/PR content was produced to translate).

## Acceptance evidence

canonical: `python3 gates/probe_wake_notice_clears.py` — result:
```
ok: stale wake-notice cleared once the alive marker is fresh
ok: genuinely absent monitor still gets a notice written
ok
```
exit 0.

derived: `git stash push -- on-the-record/hooks/directive.sh && python3 gates/probe_wake_notice_clears.py; git stash pop` — result:
```
FAIL: positive case: stale .orchestrate-wake-notice survived a directive.sh check where the alive branch must clear an existing notice
```
exit 1 (probe against the unfixed hook).

derived: `git show origin/main:on-the-record/hooks/directive.sh` extracted to a scratch path and swapped in as the probe's `DIRECTIVE_SH` target, re-run — result: same `FAIL: positive case: ...` line as above, exit 1, against the actual `origin/main` blob (not just this branch's own pre-fix working-tree state).

canonical: `python3 -m pytest tests/ -q` output, this session, this turn — result: `254 passed, 2 warnings in 10.23s` (0 failures; the 2 warnings are a pre-existing, unrelated pinned-fixture-divergence notice from `test_skill_candidates_floor.py`, issue #3019).

canonical: `python3 -m pytest test/ -q` output, this session, this turn — result: `15 failed, 548 passed, 3 xfailed in 32.05s`. All 15 failure test IDs match issue #3091's owned set (`test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_artifact_skill_pairing.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`) — none touch `directive.sh`, the notice contract, or any file this session edited; reported separately from `tests/` per the spawning prompt's explicit instruction.

Acceptance requirement met — checked: `bash -c "python3 gates/probe_wake_notice_clears.py"` — result: exit 0 (transcript above).

The other three acceptance checks the issue lists
(`probe_heartbeat_rc95_is_classified.py`,
`probe_heartbeat_survives_head_change.py`,
`probe_dead_heartbeat_is_rearmed.py`, and
`on-the-record/monitors/test_poll_heartbeat.py`) target
`on-the-record/monitors/poll-heartbeat.sh`, out of scope for this session.
Not run; no claim is made about their state.

## Next steps

None for this session's scope — the wake-notice half is landed (fix +
probe + spec registration, all committed) and a PR is being opened.
canonical: this session's own commits on `issue-3120/silent-failure-audit+test-derivation-7f269a06` (`git log --oneline -3`, this turn) — the fix, probe, and spec-row commits described above.

Follow-up, for whoever owns the `poll-heartbeat.sh` half: once that work
lands, re-run `python3 -m pytest tests/ -q` and all four acceptance
probes together, since this session's evidence covers only the
wake-notice probe in isolation.
