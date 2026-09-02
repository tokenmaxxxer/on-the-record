---
issue: 3049
role: adversarial-review+test-depth-audit+silent-failure-audit-d8d84b13
author: adversarial-review+test-depth-audit+silent-failure-audit-d8d84b13
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent builder-blind verification of PR #3088's own deliverable
code_under_review: 2bf34f4631d694a3caebfe9c63975ccc3e0df268
loop_state: landed
type: verification
breaking: false
verdict: pass — both acceptance criteria and all three must-not clauses Present, independently re-run
upstream:
  - path: PR #3088 (issue-3049/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71)
    sha: 2bf34f4631d694a3caebfe9c63975ccc3e0df268
---

# issue-3049 — adversarial-review+test-depth-audit+silent-failure-audit-d8d84b13 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly as an independent builder-blind
verification of PR #3088, not a proposal round.

canonical: `gh issue view 3049` (read at session start) — the two acceptance
checks and three must-not clauses used below are quoted verbatim from that
read. canonical: `gh pr view 3088` (read at session start) — the PR's own
claimed map ("all four shapes caught") and test-plan numbers, read before
any independent run, so this session's own runs below could be compared
against a claim instead of assumed to match it.

Checked out PR #3088's head commit `2bf34f4631d694a3caebfe9c63975ccc3e0df268`
into an isolated `git worktree` at `/tmp/pr-3088-verify` (this session's own
branch and PR #3088 itself were never edited), and a second worktree at
`/tmp/main-baseline` on `origin/main` (`573e7382282be24439c223c1603be648dd0e158f`)
for the pre-existing-failure comparison. Both worktrees were removed
(`git worktree remove --force`) once every command below had already run
and its output captured into this record; all paths below that live only on
PR #3088's branch are cited commit-pinned (`<sha>:<path>`), since they are
not reachable from this session's own branch.

### Acceptance criterion 1 — `python3 gates/probe_cwd_shapes.py`

derived: `python3 gates/probe_cwd_shapes.py` (run in `/tmp/pr-3088-verify`
at `2bf34f46:gates/probe_cwd_shapes.py`) — result:
```
bare-pushd: documented=caught actual=caught commit='[master 4e79035] add_probe_bare_pushd'
pushd-plusN: documented=caught actual=caught commit='[master 4bc208e] add_probe_pushd_plusn'
env-prefixed-cd: documented=caught actual=caught commit='[master 0a07bce] add_probe_envprefix'
cdpath: documented=caught actual=caught commit='/tmp/otr-probe-cwd-shapes-adb6jtxx/cdpath/cdpath_target/back'
ok
```
exit=0. Independently reproduces the PR's own claimed map exactly — all four
of bare `pushd`, `pushd +N`/`-N`, env-prefixed `cd`, and `$CDPATH` are caught
by `2bf34f46:on-the-record/hooks/gate-registration-post-guard.sh` on this
run, on a fresh scratch repo this session did not prepare in advance.
**Verdict: Present.**

### Acceptance criterion 2 — `python3 -m pytest tests/test_cwd_shape_coverage.py -q`

derived: `python3 -m pytest tests/test_cwd_shape_coverage.py -q` (run in
`/tmp/pr-3088-verify` at `2bf34f46:tests/test_cwd_shape_coverage.py`) —
result:
```
........                                                                 [100%]
8 passed in 1.20s
```
canonical: `2bf34f46:docs/issue-3049/reports/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71.md`
lines 323-326, read directly in the PR worktree — its "## Open findings"
section reads "None. All four shapes are caught by the companion; no
uncaught gap to name a cost for, per the acceptance amendment's own
empty-state clause." This satisfies the issue's empty-state clause ("if all
four are caught, state that as the finding"). Since this session's own run
of acceptance criterion 1 above independently confirmed zero uncaught
shapes (not cited from this PR record — re-derived), there is no uncaught
shape whose cost this delivery was obligated to name; the "cost named"
requirement is vacuously satisfied, not skipped. **Verdict: Present.**

### Must-not 1 — no PreToolUse command-text parser extension

derived: `git diff origin/main --stat -- on-the-record/` (run in
`/tmp/pr-3088-verify`) — result: empty (no output, no files listed).
derived: `git diff origin/main --name-only` (same worktree) — result:
```
docs/issue-3049/reports/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71.md
docs/issue-3049/reports/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71/deviation-log/20260902T070628927235-e47e66f78a5db6d0.md
docs/specs/enforcement-boundary.md
gates/probe_cwd_shapes.py
tests/test_cwd_shape_coverage.py
```
Neither `gate-registration-guard.sh` nor `gate-registration-post-guard.sh`
appears in the changed-file list at all — the PR did not touch the
PreToolUse parser, let alone extend it. **Verdict: Present** (must-not
upheld).

### Must-not 2 — no widening either hook to fail closed

derived: same `git diff origin/main --name-only` command and result quoted
directly above under must-not 1: neither hook file changed, so no fail-open
behavior was altered in either direction by this delivery. **Verdict:
Present** (must-not upheld).

### Must-not 3 — no marking a shape caught on the companion's own claim without running it

canonical: `2bf34f46:gates/probe_cwd_shapes.py:185-186` (read in
`/tmp/pr-3088-verify`) —
```python
    genuinely_staged = any(
        l.startswith("A") and shape["added_path"] in l for l in staged_lines
    )
```
this ground-truth check against real `git log -1 --name-status` output runs
*before* the companion is ever invoked; a shape that fails it returns
`not-reproducible` and the companion is never consulted for that shape.
Only once that check holds true does `2bf34f46:gates/probe_cwd_shapes.py:232`
(`post_res = _run(["bash", str(POST_GUARD), "post"], ...)`) feed the real
captured `git commit` stdout into the unmodified
`2bf34f46:on-the-record/hooks/gate-registration-post-guard.sh`, and
`2bf34f46:gates/probe_cwd_shapes.py:269` compares its report text against
the ground-truth sha and path (`abbrev_sha in report_text and
shape["added_path"] in report_text`) rather than trusting the companion's
exit code alone. **Verdict: Present** (must-not upheld, structurally
enforced in code at the cited lines, not just asserted in prose).

### Mutation check — does the probe fail in both directions?

The issue's acceptance text requires the probe fail if "a caught shape
silently becoming uncaught" or "an uncaught one being quietly closed
without this record being updated." The equality check in `main()` is a
plain `actual != documented`, so both directions reduce to the same
comparison; this session verified that comparison fires by editing the
code directly rather than trusting the PR's own claim to have already
proven it — the PR's own record independently reports the identical
experiment at `2bf34f46:docs/issue-3049/reports/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71.md`
lines 128-131 (read after, not before, running the check below).

derived: in `/tmp/pr-3088-verify`, edited a working copy of
`2bf34f46:gates/probe_cwd_shapes.py` to change
`DOCUMENTED_STATUS["bare-pushd"]` from `"caught"` to `"uncaught"`, ran
`python3 gates/probe_cwd_shapes.py`, then restored the file and confirmed
`git diff --stat` showed no output afterward — result:
```
FAIL: bare-pushd: documented status 'uncaught' but this run observed 'caught' -- companion report: "...gate-registration-guard (post-commit report, issue #2705): the following commit(s) already exist in git history..."
bare-pushd: documented=uncaught actual=caught commit='[master f476811] add_probe_bare_pushd'
exit=1
```
Confirms the probe objects to a mismatch (exit 1, `FAIL:` line naming the
disagreement) rather than passing silently. **Confirms Present** for
acceptance criterion 1's fail-in-either-direction requirement.

### Regression baseline — full suite, PR vs. `origin/main`

derived: `python3 -m pytest tests/ -q` (run in `/tmp/main-baseline` at
`573e7382`) — result: `5 failed, 182 passed, 2 warnings in 6.66s`.
derived: `python3 -m pytest test/ -q` (same worktree) — result:
`15 failed, 548 passed, 3 xfailed in 32.36s`.
derived: `python3 -m pytest tests/ -q` (run in `/tmp/pr-3088-verify` at
`2bf34f46`) — result: `5 failed, 190 passed, 2 warnings in 9.40s` (the +8
delta is exactly the 8 new `test_cwd_shape_coverage.py` tests confirmed
under acceptance criterion 2 above).
derived: `python3 -m pytest test/ -q` (same worktree) — result:
`15 failed, 548 passed, 3 xfailed in 32.12s`, byte-identical counts to the
`origin/main` run above — `test/` is untouched by this PR's diff, per the
`git diff origin/main --name-only` result already quoted under must-not 1.

derived: `python3 -m pytest tests/ -q 2>&1 | grep '^FAILED' | sort` run in
each worktree, then `diff main_failed.txt pr_failed.txt` — result: no diff
output, plus a direct read of both files, identical five lines in each:
```
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_when_gate_finds_none
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_never_silent_even_without_pr_number
```
The PR neither fixes nor introduces any `tests/`/`test/` failure; it is
purely additive.

Note: the task brief that spawned this session cited a main baseline of "5
failed / 105 passed." This session's own independently-reproduced main
baseline above is 182 passed, not 105 — recorded as observed, not silently
reconciled. The additivity judgment above uses this session's own
re-derived main baseline (182→190), not the brief's uncited number, since
182 is the only main-baseline count this session actually ran itself.

### test-depth-audit — `2bf34f46:tests/test_cwd_shape_coverage.py` (8 tests)

canonical: full file content read in `/tmp/pr-3088-verify`, cross-checked
against the `8 passed` pytest run under acceptance criterion 2 above.
derived: 8 GA / 8 total = 100% verification density (all 8 tests carry a
Genuine Assertion (GA); none are Execution-Only, Mock-Dominated,
Happy-Path-Only, or Dead):
1. `test_bare_pushd_matches_documented_status` — GA, asserts `result["ok"]` and `result["status"] == DOCUMENTED_STATUS[name]`.
2. `test_pushd_plusN_matches_documented_status` — GA, same assertion shape.
3. `test_env_prefixed_cd_matches_documented_status` — GA, same.
4. `test_cdpath_matches_documented_status` — GA, same.
5. `test_all_four_shapes_are_genuinely_staged_by_real_git` — GA, asserts `result["ok"]` per shape (ground-truth tie to must-not 3 above).
6. `test_probe_script_exits_zero_and_prints_ok` — GA, asserts `returncode == 0` and `"ok" in stdout.splitlines()`.
7. `test_neither_guard_script_was_modified_by_this_delivery` — GA, asserts (via `git diff origin/main -- <hook path>`) that the diff is empty — the same must-not checks above expressed as a pytest assertion, not prose.
8. `test_failing_bundled_command_reports_reason_not_a_crash` — GA, asserts `result["ok"] is False` and `"exited" in result["reason"]` (the not-reproducible edge the issue's empty-state clause names).

Tests 1-4's assertions were mutation-confirmed live in this session (the
flip test above), not just read — a genuine regression in `run_shape()`'s
`caught` determination would fail them.

### silent-failure-audit — `2bf34f46:gates/probe_cwd_shapes.py`

canonical: full file content read in `/tmp/pr-3088-verify`. Enumerated
every error-handling site: the top-level `except Exception` in `main()`,
the `post_res.returncode != 0` guard, the `pre_res.returncode != 0` guard,
the `json.JSONDecodeError` catch around the companion's stdout parse, and
the `genuinely_staged`/sha-regex not-found paths — derived: 5 sites total,
5 Handled (H), 0 Silently Absorbed. Each records a specific reason string,
appends to `failures`, and the run exits non-zero with the reason printed;
none is an empty catch or a silently-substituted default. This matches the
PR's own stated fixes (its body names an `ORCHESTRATE_OFF` inherited-env
risk and an unchecked `post`-mode exit code as two things it found and
fixed) — cross-checked against the code read above, not re-derived by
independently breaking `post` mode, since doing so would require patching
the hook script itself, which the must-not clauses forbid this
verification from doing.

## Why

canonical: this session's own execution results in every section above —
issue #3049 is explicit that a cwd shape *not* being caught is an
acceptable outcome, so the grading task here was not "did the PR make
everything green" but "is the map actually true, checked by running the
code, not by reading the PR's prose." Every finding above is grounded in a
command this session ran itself against the PR's actual head commit in an
isolated worktree, plus one adversarial mutation (the flip test) that the
PR's own record also happened to run — confirmed independently here, not
cited from that record as ground truth.

## Upstream basis

PR #3088 (`tokenmaxxxer/on-the-record#3088`), head commit
`2bf34f4631d694a3caebfe9c63975ccc3e0df268`, diffed against `origin/main`
`573e7382282be24439c223c1603be648dd0e158f`. Changed files (per
`git diff origin/main --name-only` under must-not 1 above, run against
that head): `2bf34f46:gates/probe_cwd_shapes.py` (new),
`2bf34f46:tests/test_cwd_shape_coverage.py` (new),
`2bf34f46:docs/specs/enforcement-boundary.md` (+1 row), plus the PR's own
record and deviation log under
`2bf34f46:docs/issue-3049/reports/silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71.md`
and its `deviation-log/` subdirectory. No file under `on-the-record/` is
touched by this PR.

## Open findings

canonical: this session's own runs across every acceptance/must-not
section above — none. Both acceptance criteria and all three must-not
clauses graded Present above, each independently re-derived rather than
taken on the PR's word. No disagreement found between this session's own
runs and the PR's claimed per-shape map.

## Next steps

None — `loop_state: landed`. derived: `git worktree list` (run in this
session's own tree after cleanup) — result: only this session's own
worktree remains, confirming `/tmp/pr-3088-verify` and `/tmp/main-baseline`
were removed and PR #3088's branch was never committed to. This is a
terminal verification record; PR #3088 was not merged or edited by this
session, per the spawning instructions.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; structured the whole
verification as a builder-blind re-run of the PR's claimed map against an
isolated checkout, comparing this session's own results to the PR's claim
rather than reading the claim as ground truth.
skill-verdict: test-depth-audit — applied: invoked; classified all tests
in `2bf34f46:tests/test_cwd_shape_coverage.py` as Genuine Assertion (see
table above), with 4 of them mutation-confirmed live via the flip test.
skill-verdict: silent-failure-audit — applied: invoked; enumerated and
classified every error-handling site in `2bf34f46:gates/probe_cwd_shapes.py`
as Handled, cross-checked against the PR's own claimed fixes.
skill-verdict: implementation-audit — applied: invoked; used its
claim-vs-evidence classification (Present/Surface/Absent/Incorrect/
Unverifiable) as the grading vocabulary for both acceptance criteria and
all three must-not clauses per this issue's own acceptance-check framing.
other mounted skills: not triggered.
