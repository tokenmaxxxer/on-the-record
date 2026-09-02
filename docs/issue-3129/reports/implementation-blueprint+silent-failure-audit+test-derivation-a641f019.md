---
issue: 3129
role: implementation-blueprint+silent-failure-audit+test-derivation-a641f019
author: implementation-blueprint+silent-failure-audit+test-derivation-a641f019
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/amendment_channel.py, on-the-record/hooks/amendment-channel.sh
loop_state: landed
type: feature
breaking: false
verdict: pass — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 35 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 289 passed, 0 failed
upstream: []
---

# issue-3129 — implementation-blueprint+silent-failure-audit+test-derivation-a641f019 record

## What was done

Build-now delivery (`CORE_BUILD_NOW=1` in this session's environment, spawner-set): a local-file amendment channel that lets an orchestrator's mid-flight issue-body correction reach a running, headless spawned worker session — the two channels the issue names as broken (a cross-session message that needs the recipient's own user to approve, which a headless worker has nobody to give; and an issue-body amendment that reaches `check_runner`'s scoring but not the already-spawned process, which read the issue once at spawn and never again) stay broken; this adds a third, working one.

New files:
- `on-the-record/hooks/amendment_channel.py` — the state machine. `write_amendment(state_dir, issue, note)` bumps a monotonic `version` int inside a JSON marker (`$TMPDIR/otr-amendment/issue-<n>.marker.json` by default, `$OTR_AMENDMENT_STATE_DIR` override) — an explicit content field, never the file's raw mtime, specifically because Linux and macOS mtime granularity differ (the issue's own cross-platform requirement). `check_notice(state_dir, session_id, issue)` compares that version against a per-`(session_id, issue)` "seen" file and fires a notice string at most once per version bump, writing the seen file to the new version *before* returning so the same amendment never re-announces. `maybe_write_from_command` detects `gh issue edit <n> ... --body|--body-file|--body=|--body-file= ...` in a session's own Bash tool calls and extracts the corrected text as the marker's `note`. `issue_for_cwd` resolves a worker's own issue number from its `issue-<n>/<role>` branch name via a local `git rev-parse` call — no network. `run_hook` composes all of this into the one call a `PostToolUse` payload needs.
- `on-the-record/hooks/amendment-channel.sh` — thin wrapper, registered unmatched in `PostToolUse` (fires on every tool call). Pipes stdin to `amendment_channel.py`, unconditional trailing `exit 0` regardless of the python process's own exit code — never a blocking gate.
- `tests/test_amendment_channel.py` — 35 unit tests covering marker read/write round-trip and corruption fail-open, fire-once-per-amendment, absorbed-stops-announcing (including the S1→S1 double-amend-before-absorption transition and a fresh-process re-check that the seen state actually persisted to disk), `gh issue edit` command-detection equivalence classes, `issue_for_cwd` branch parsing, `run_hook` end-to-end, and the stderr diagnostic added by the silent-failure-audit pass below.
  - acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result:
    ```
    ...................................                                      [100%]
    35 passed in 0.86s
    ```
- `gates/probe_running_session_sees_amendment.py` / `gates/probe_amendment_notice_fires_once.py` — the issue's two named acceptance probes. Both subprocess the real, unmodified `amendment-channel.sh` against a scratch git repo on an `issue-<n>/<role>` branch, matching the existing `gates/probe_cwd_shapes.py` convention.
  - acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: `ok`
  - acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: `ok`

Wiring: `on-the-record/hooks/hooks.json` registers `amendment-channel.sh` in the unmatched `PostToolUse` group via `fail-open-wrapper.sh`. `on-the-record/hooks/hook_classification.json` classifies it `observability`. `on-the-record/hooks/test_hook_classification.py`'s live-registration-count literal moved 14→15 (13→14 wrapped). `docs/specs/enforcement-boundary.md` carries rows for the hook script and both probes; `docs/specs/generated-paths.md` carries the hook script's row.

silent-failure-audit pass (invoked via the Skill tool) against `amendment_channel.py`'s error-handling sites found one real Silently-Absorbed site: `write_amendment`'s own `except OSError: return None` is correct fail-open for the orchestrator's tool call, but `maybe_write_from_command` discarded the return value entirely — a disk-full/permission failure on the orchestrator's machine left zero trace anywhere that the worker would never see the correction. Fixed: one `sys.stderr.write(...)` line on that path, still non-blocking (regression test: `test_unwritable_state_dir_surfaces_a_stderr_diagnostic`). The audit also found `run_hook`'s two `except Exception: pass/return None` wrappers and `main()`'s blanket `except Exception` were defense-in-depth duplicating guarantees the inner functions already provide for their documented failure modes, but for a genuinely unanticipated bug they swallowed it with zero trace anywhere — not stderr, not `fail-open-wrapper.sh`'s own fail-open ledger (which greps stderr for a traceback regardless of exit code). Removed; a real bug now propagates to a stderr traceback the existing ledger mechanism already knows how to observe, at zero blocking-risk cost since the `.sh` wrapper's own trailing `exit 0` is unconditional either way.

test-derivation pass (invoked via the Skill tool) against the issue's two named design constraints, modeled as a 3-state machine (no-marker / unabsorbed / absorbed) over `write_amendment`/`check_notice` transitions plus equivalence partitions over the `gh` command shapes, surfaced two gaps: the S1→S1 transition and the `--body-file=<path>` equals-form partition. Both added as regression tests (`test_two_amendments_before_absorption_coalesce_into_one_notice`, `test_body_file_equals_form_reads_note_from_file`).

implementation-blueprint pass (invoked via the Skill tool) sanity-checked the already-built module boundary against the skill's classifier.
- derived: `python3 <skill-dir>/scripts/prep.py classify --single-file` — result:
  ```
  VETO: single file, single concern, no callers -> no-structure
  Reason: ceremony where it doesn't earn its keep -- just write it
  correctly and note 'this is a script; flat is fine'.
  ```
  Matches what was built (one flat module, no premature controller/service/repository split); the two probe files and the direct-import test file are issue-imposed/convention-matched, not speculative structure. No changes made from this pass.

Full suite, same session:
- acceptance: `python3 -m pytest tests/ -q` — result:
  ```
  289 passed, 2 warnings in 10.51s
  ```
- derived: `python3 -m pytest test/ -q` — result:
  ```
  15 failed, 548 passed, 3 xfailed in 31.60s
  ```
  All 15 failures are in `test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`, and `test_spawn_artifact_skill_pairing.py` — none touch `on-the-record/hooks/amendment_channel.py`, `amendment-channel.sh`, `hooks.json`, or any file this change edited; issue #3129's own prompt states these are pre-existing, owned by #3091.

## Why

Design choice 1 — explicit content version, not raw mtime: the issue names the Linux/macOS mtime-granularity difference as a hazard for the probes; a monotonic integer written into the marker's JSON content as the fire/absorb comparison sidesteps that hazard for the correctness path entirely.

Design choice 2 — automatic detection of `gh issue edit --body` in the orchestrator's own `PostToolUse`, rather than a separate CLI the orchestrator must remember to invoke: the same hook script already runs on every tool call for every session, so the write side and the read side are the same code path with no new manual step and no role-detection env var needed — an orchestrator's own cwd is simply never on an `issue-<n>` branch that also matches its own amendment, so it never notices itself.

Design choice 3 — absorb-before-return in `check_notice`: mirrors the existing `stop-poll-rearm.sh` `_monitor_liveness_check_and_notify` precedent (`notified_episode` written before the notice text is printed) already in this codebase for an analogous fire-once/re-arm state machine.
- canonical: `on-the-record/hooks/stop-poll-rearm.sh` read directly this session, `_monitor_liveness_check_and_notify`:
  ```python
  if state.get("notified_episode") == episode_key:
      sys.exit(0)
  ...
  with open(state_path, "w") as f:
      json.dump({"notified_episode": episode_key}, f)
  ```

Design choice 4 — no `tool_response` success check on the `gh issue edit` detection: the channel is explicitly advisory (issue's own must-not: never a blocking gate), so a false-positive bump from a failed `gh` call costs a worker one harmless extra re-read, not a wrong decision.

## What did not work

None — derived: same-session `git log --oneline -8` — result: five sequential `issue-3129:` commits, each adding a working piece, none reverted or superseded; no design rework was needed after the first implementation pass.

## Upstream basis

Issue #3129 body — canonical: `gh issue view 3129` output (state: OPEN), read at session start and quoted in full in this session's own conversation transcript. No prior docs/issue-3129/ artifacts existed (this session's own `docs/issue-3129/reports/` scaffold is the first).

Existing-codebase precedents this design ports from, read directly from the working tree at session start: `on-the-record/hooks/stop-poll-rearm.sh` (fire-once/re-arm shape), `on-the-record/hooks/retry-loop-bound.sh` (`$TMPDIR`-rooted per-session state-file convention, `hookSpecificOutput.additionalContext` output shape), `on-the-record/hooks/hook_input.py` (total-function/never-raises contract), `on-the-record/hooks/fail-open-wrapper.sh` (stderr-traceback-grep ledger), `gates/probe_cwd_shapes.py` (real-shipped-script-via-subprocess probe convention).

Main-checkout absence:
- derived: `git show main:on-the-record/hooks/amendment_channel.py` — result:
  ```
  fatal: path 'on-the-record/hooks/amendment_channel.py' exists on disk, but not in 'main'
  ```
- derived: copied each probe file alone into a fresh `git clone` of this repo checked out to `main`, then ran it there — result: probe 1 printed `FAIL: no amendment marker written after a gh issue edit --body call -- amendment-channel.sh missing or its write path broken` (exit 1); probe 2 printed `FAIL: amendment #1 never reached the worker across 12 tool calls -- amendment-channel.sh missing, or the hook never fires the notice at all` (exit 1).

## Open findings

None open — derived: the one silent-failure-audit finding (write_amendment's discarded return value) was fixed in this same session (commit `61065ede`, this branch), not deferred; see "What was done".

## Next steps

None — canonical: this record's own `loop_state: landed` frontmatter field, set in this same commit. Build-now (`CORE_BUILD_NOW=1`) single-session delivery: code, tests, probes, and this record commit on this branch together; a PR opens next, not merged by this session.

## Skill verdicts

derived: `git show 61065ede --stat` — result:
```
 on-the-record/hooks/amendment_channel.py        | 55 +++++++++++++++++--------
 on-the-record/hooks/hook_classification.json    |  8 ++++
 on-the-record/hooks/hooks.json                  |  4 ++
 on-the-record/hooks/test_hook_classification.py | 13 +++---
 tests/test_amendment_channel.py                 | 41 ++++++++++++++++++
 5 files changed, 97 insertions(+), 24 deletions(-)
```
— the silent-failure-audit fix (`write_amendment`'s discarded-return-value diagnostic, the two removed defense-in-depth catches) and the test-derivation regression tests (`test_two_amendments_before_absorption_coalesce_into_one_notice`, `test_body_file_equals_form_reads_note_from_file`, `test_unwritable_state_dir_surfaces_a_stderr_diagnostic`) landed in this exact commit, both skills invoked via the Skill tool earlier in this same turn.

skill-verdict: implementation-blueprint — applied: invoked; classified the module boundary via `prep.py classify --single-file` (no-structure veto), confirmed the already-flat single-module structure needed no change (see "What was done")
skill-verdict: silent-failure-audit — applied: invoked; audited every try/except in `amendment_channel.py`, found one Silently Absorbed site (`write_amendment`'s discarded return value) and fixed it, and removed two redundant broad catches that were defeating `fail-open-wrapper.sh`'s traceback ledger (see "What was done")
skill-verdict: test-derivation — applied: invoked; modeled the fire-once/absorbed state machine and the `gh` command-detection equivalence classes, surfaced two gaps (S1→S1 double-amend, `--body-file=` equals-form) and added regression tests for both (see "What was done")
other mounted skills: not triggered
