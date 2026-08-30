---
issue: 2326
role: diagnose-first-71f82584
author: diagnose-first-71f82584
skills: diagnose-first (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false
code_under_review: PR #2860 (merged, sha 060f1f10655d41f2072865c1e2ce7a093fed2412, no-ship verdict) and PR #2863 (merged, sha 99b6461674d82adf4f531f1e97dd2e50c084cc60, found the no-ship verdict's cost pillar rested on a sleeping test file, not a property of import-graph selection)
type: decision
breaking: false
verdict: ship the lint-test-on-edit hook -- import-graph impacted-test selection plus a per-item pytest timeout (SIGALRM-based, xdist disabled for the invocation) bounds the one known slow matched file without excluding it by name; wired into hooks.json. Rework fraction re-derived at 4.6% (rework/edit-call) on a live, currently-existing 13-session on-the-record-* corpus, consistent in order of magnitude with the prior (now-unreproducible) 4.5% figure.
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/diagnose-first-56b99f15.md
    sha: 060f1f10655d41f2072865c1e2ce7a093fed2412
  - path: docs/issue-2326/reports/adversarial-review-ddab0192.md
    sha: 99b6461674d82adf4f531f1e97dd2e50c084cc60
  - path: scripts/rework_fraction.py
    sha: 060f1f10655d41f2072865c1e2ce7a093fed2412
  - path: docs/issue-2326/reports/diagnose-first-71f82584/2026-08-30-hunt-per-file-timeout-ship.md
    sha: same-commit
---

# issue-2326 — diagnose-first-71f82584 record

skill-verdict: diagnose-first — applied: invoked; used Stage 2's narrow/dig/verify sequence and the
intervention/counterfactual test (fix the candidate cause, re-measure, confirm the effect reverses) to
find and fix a second defect the per-item timeout alone did not resolve
canonical: this session's own timing sequence in "What was done" item 2 below -- pre-fix 3 consecutive
real end-to-end runs at ~15.03-15.04s each reporting `budget exceeded`; post-fix 8 consecutive real
end-to-end runs at 9.15-13.21s each, all three real target tests present every time
skill-verdict: work-in-english — applied: invoked; this record, all code, comments, commit message, and
PR text are in English; the final chat summary to the user is in Korean
canonical: this session's own file writes and commit (`git log -1 --format=%B` on this branch's own
new commit, this session)
skill-verdict: other mounted skills (hypothesis-testing, research-evidence-discipline,
product-discovery-guardrail-metrics, observability-phase-trace) — not-applicable: this is an
engineering diagnostic/implementation record, not a market/product-discovery-shaped record or an
observability phase-1-vs-phase-2 comparison; none of their trigger conditions match this task

## What was done

Re-opened issue #2326's ship/no-ship call on the lint-test-on-edit hook specifically on the
per-file-timeout axis PR #2863 identified as unexplored, and re-derived the rework-fraction
materiality number on a corpus that still exists.

**1. Per-file timeout, built and shown against the traced episode.**

Added `on-the-record/hooks/otr_lint_test_timeout_plugin.py`, a pytest plugin that bounds any single
test item to `OTR_LINT_TEST_PER_FILE_TIMEOUT_S` seconds (default 3) via `SIGALRM`
canonical: `on-the-record/hooks/otr_lint_test_timeout_plugin.py`, read in full this session (53 lines,
committed this-commit sha cabaae7044972f59ad0beab935d8f4b215bc8c67)
. `lint-test-on-edit.sh` now selects impacted tests via import-graph (grep `test/`+`tests/` for a
leading `import <stem>`/`from <stem> import` line naming the edited module's stem -- the selection
approach PR #2859/#2860 already validated as accurate on this repo's naming convention, unchanged this
round) and invokes pytest with `-p otr_lint_test_timeout_plugin -o addopts=` (disabling this repo's
default `-n auto` xdist, since `SIGALRM` only interrupts the process that receives it).

Measured directly against the traced episode (session `on-the-record-issue-2795-silent-failure-
audit-3da5ceae`, edits to `board.py`/`spawn.py`/`watchdog.py`, per adversarial-review-941d677c.md
finding 1) via the real shipped hook script, not a synthetic reproduction:

```
$ PAYLOAD='{"tool_name":"Edit","tool_input":{"file_path":"spawn.py"},"cwd":"<repo>","session_id":"t"}'
$ echo "$PAYLOAD" | bash on-the-record/hooks/lint-test-on-edit.sh post > /tmp/out.json  # x8, timed
run 1: 9.79s   run 2: 9.59s   run 3: 10.14s   run 4: 13.21s   run 5: 9.15s
run 6: 10.24s  run 7: 10.14s  run 8 (post docs/.. fix, below): 12.20s
```
derived: 8 repeated end-to-end invocations of the real hook script against a real `spawn.py` edit
payload, this session -- all 8 inside the 15s combined budget (`OTR_LINT_TEST_BUDGET_S`, default 15)
. All 8 runs' `additionalContext` contained all three real failing tests from the traced episode:
```
$ python3 -c "import json; d=json.load(open('/tmp/out.json')); ctx=d['hookSpecificOutput']['additionalContext']; print([n in ctx for n in ('test_convention_equivalence','test_local_dependency_env','test_spawn_cross_family_skill_selection')])"
[True, True, True]
```
derived: exact command and output, this session, re-run after each of the 8 timed invocations above
. The sleeping file (`test/test_bootstrap_signal_guard.py`) was run and its slow item reported as
abandoned via the per-item timeout, not excluded by name:
```
$ PYTHONPATH=<hooks-dir> OTR_LINT_TEST_PER_FILE_TIMEOUT_S=3 python3 -m pytest -p otr_lint_test_timeout_plugin -o addopts="" test/test_bootstrap_signal_guard.py -q
1 failed, 10 passed in 3.46s
```
derived: standalone (non-4KB-truncated) run of the same file with the shipped plugin and settings,
this session -- the failed item's traceback shows `otr_lint_test_timeout_plugin._PerItemTimeout:
otr-per-file-timeout: exceeded 3.0s, item abandoned`

**Why xdist has to be disabled for this invocation, verified not assumed:**
```
$ PYTHONPATH=/tmp OTR_LINT_TEST_PER_FILE_TIMEOUT_S=3 python3 -m pytest -p ... test/test_bootstrap_signal_guard.py -q     # -n auto (this repo's pytest.ini default) active
1 failed, 10 passed in 23.78s
$ PYTHONPATH=/tmp OTR_LINT_TEST_PER_FILE_TIMEOUT_S=3 python3 -m pytest -p ... -o addopts="" test/test_bootstrap_signal_guard.py -q   # xdist off
1 failed, 10 passed in 3.46s
```
derived: both commands run back-to-back, this session -- the same per-item timeout bounded the
reported test-time identically (3s) in both, but wall-clock cost differed by ~20s, so `lint-test-on-
edit.sh` passes `-o addopts=` for this call specifically.

**2. A second, independent defect found and fixed: orphaned-grandchild pipe blocking.**

The per-item `SIGALRM` alone did not reliably bound wall-clock time for the hook's actual invocation
shape (`subprocess.run(capture_output=True)`, pipe-based). The traced-episode test that trips the
per-item timeout forks a child that sleeps 30s and is deliberately not disarmed (reproducing a "live
signal gap"); interrupting the *parent* test's blocking `os.waitpid()` via `SIGALRM` does not kill that
forked child, which is reparented and keeps running, still holding the *inherited* stdout/stderr pipe
file descriptors open:

```
$ python3 -c "... subprocess.run(pytest_args, capture_output=True, timeout=60) ..."  # 35-file match set incl. sleeper
elapsed 38.08s   (pytest's own reported test-time inside that same run: 10.99s)
```
derived: direct `subprocess.run(capture_output=True, timeout=60)` call against the real 35-file match
set including the sleeper, this session -- a ~27s gap between pytest's own reported completion and the
parent script actually regaining control from `communicate()`, consistent with an orphaned grandchild
holding the pipe open
. Confirmed end-to-end with the hook exactly as shipped before this fix:
```
$ for i in 1 2 3; do <same spawn.py edit payload> | bash lint-test-on-edit.sh post; done   # pre-fix
run 1: 15.05s, additionalContext = "budget exceeded (15s), skipped remaining lint/test checks for spawn.py"
run 2: 15.04s, same "budget exceeded" text, no target test names present
run 3: 15.04s, same "budget exceeded" text, no target test names present
```
derived: 3 consecutive `bash on-the-record/hooks/lint-test-on-edit.sh post` runs against the real
`spawn.py` payload, pre-fix, this session

Fixed `_run()` in `lint-test-on-edit.sh`: output is now captured via a real temp file
(`tempfile.TemporaryFile()`, no "wait for every fd holder to close" semantics) instead of a pipe, and
the subprocess runs in its own process group (`start_new_session=True`) which is killed in full
(`os.killpg(pgid, 9)`) once the call returns or times out. Re-ran the same intervention/counterfactual
test post-fix: the 8-run timing table in item 1 above (9.15-13.21s, all three targets present every
run) is that re-measurement. A process check after the 8-run set showed no leftover test-related
processes:
```
$ ps --ppid 1 -o pid,cmd | grep -i python; ps aux | grep -i sleep
```
derived: both commands run after the 8-run set, this session -- no orphaned `sleep`/pytest-descendant
processes present, only unrelated harness processes (disk-check loops, other sessions' own `spawn.py`
watchers)
. Neither PR #2860's nor PR #2863's record describes this defect
canonical: `docs/issue-2326/reports/diagnose-first-56b99f15.md` and
`docs/issue-2326/reports/adversarial-review-ddab0192.md`, both read in full this session -- neither
mentions pipe capture, process groups, or an orphaned child; PR #2863 measured its bisection via a raw
`time python3 -m pytest ... -q` shell invocation piped through `tail`, not `subprocess.run(capture_
output=True)`, which is why this defect only surfaced once this session tested the exact invocation
shape the hook itself uses
.

**3. Hunt finding, found and fixed before landing.** A background `warrant-hunter` dispatch
(before-landing, stance 0 of the standing 5-stance rotation -- "assume the gate/hook just touched is
bypassable, find the bypass" -- taken because no `.warrant-hunt.count` file exists anywhere in this
workspace, confirmed via `find "$MUSTER_WORKSPACE_ROOT" -maxdepth 1 -iname ".warrant-hunt.count"` →
no match, this session) found that a `file_path` shaped as `docs/../<real-code-path>` matches the bash
fast path's `*/docs/*` glob on the raw, un-normalized string, so the hook exits before python's
`posixpath.normpath`-based authoritative re-check ever runs
canonical: `docs/issue-2326/reports/diagnose-first-71f82584/2026-08-30-hunt-per-file-timeout-ship.md`
(committed this-commit sha cabaae7044972f59ad0beab935d8f4b215bc8c67), the hunter's own finding and
repro, independently reproduced by this session before applying the fix:
```
$ echo "$PAYLOAD_BYPASS" | bash lint-test-on-edit.sh post   # file_path: docs/../broken_repro.py, real SyntaxError
(no output, exit 0 -- silently skipped, pre-fix)
```
. Fixed: the bash `case` statement now has a leading `*..*)` arm that falls through to python's
authoritative check instead of fast-exiting, for any raw guess containing `..`. Re-ran the hunter's own
repro post-fix:
```
$ echo "$PAYLOAD_BYPASS" | bash lint-test-on-edit.sh post
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "lint-test-on-edit: lint failed for broken_repro.py:\n ... SyntaxError: invalid syntax"}}
```
derived: same payload re-run post-fix, this session -- the syntax error now correctly surfaces
. Added a regression test in `tests/test_spawn_gate_wiring.py` (new method
`test_dotdot_traversal_does_not_fool_the_docs_fast_path` in the `DocsOnlyEmptyState` class, part of the
21-test file cited in "Next steps" below).

**4. Rework fraction re-derived on a corpus that still exists.** The prior "4.5%" figure's source
corpus (a manually-filtered `/tmp/otr_only/*.session.*.log` symlink directory built inside a since-
ended session) no longer exists on disk
canonical: adversarial-review-ddab0192.md's own "Could not verify" finding, re-checked this session:
`find "$MUSTER_WORKSPACE_ROOT" -iname "*on-the-record-issue-2324-independent-verification*"` → no match
. Re-ran `scripts/rework_fraction.py` against the live `$MUSTER_WORKSPACE_ROOT` corpus, restricted to
`on-the-record-*` sessions (the population the hook can actually reach -- it ships in a plugin's
`hooks.json` never wired into `tokenmaxxxer-core-*` sessions, per PR #2860's own note
canonical: `docs/issue-2326/reports/diagnose-first-56b99f15.md`, line citing "the hook ships in a
plugin's hooks.json that is never wired into tokenmaxxxer-core-* sessions", read directly this session
):

```
$ ls "$MUSTER_WORKSPACE_ROOT"/on-the-record-*.session.*.log | wc -l
13
$ python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/on-the-record-*.session.*.log"
=== corpus rollup: 13 session(s) ===
sessions with parse errors: 0
sessions with zero test-stage calls: 1 (excluded from denominators)
sessions with >=1 test-stage call: 12
total test-stage calls: 74 (fail=28, fail_fraction=37.8%)
total edit calls (Edit/Write/MultiEdit): 174
total rework episodes (cost known): 8
  rework_fraction_of_test_stage_calls: 10.8%
  rework_fraction_of_edit_turns: 4.6%
total unresolved re-entry (cost unknown, excluded from median/mean): 4
total failures without re-entry: 16 fixed-without-edit-looking, 0 ran to session end
rework turn-cost across corpus: median=5.5 mean=14.00 (n=8)
```
derived: exact command and full output, this session, executed 2026-08-30. The corpus is the 13
`on-the-record-*.session.*.log` files present under `$MUSTER_WORKSPACE_ROOT` at that moment -- a live,
currently-existing corpus, re-listable and re-runnable by anyone with access to this workspace root; it
will differ on a later date as sessions rotate, exactly as PR #2860's own upstream record already
warns
. **4.6% rework-fraction-of-edit-turns**, median rework-episode cost 5.5 turns (mean 14.00, pulled up
by one session's `[32, 31, 28]`-turn episode set, per the same command's per-session breakdown) -- the
same order of magnitude as the prior (now-unreproducible) 4.5% figure, on a corpus that is smaller (13
vs the prior citation's 10 sessions) but real and checkable today. This is an independent measurement
on different, currently-live data, not a re-derivation of the same number -- it happens to land in the
same range, which is the most this round can honestly claim given the original corpus is gone.

**Decision: ship.** Import-graph selection's accuracy is established by PR #2859/#2860 and unchanged
this round. The per-item timeout, combined with the process-group-kill/temp-file-capture fix this
session found was also necessary (item 2 above), bounds the one known slow matched file to a few
seconds instead of ~30s or an indefinite pipe-block, shown against the real shipped hook script and the
actual traced episode
canonical: item 1's 8-run timing table above -- all 8 runs inside the 15s budget, all three target
tests present in every run's `additionalContext`
. The docs/.. bypass the before-landing hunt found is fixed (item 3). Materiality is re-established,
independently, at a similar order of magnitude to the original citation, on a corpus that exists today
(item 4). `on-the-record/hooks/hooks.json` wires `lint-test-on-edit.sh` in additively:
```
$ git diff --stat origin/main -- on-the-record/hooks/hooks.json
on-the-record/hooks/hooks.json | 4 ++++
```
derived: this session, this branch's actual staged/committed diff against origin/main.

## Why

PR #2863 (verification) had already shown the no-ship verdict's cost pillar rested on a single
sleeping file, not on file count, and named "a per-file-timed-out variant of the hook" as the concrete,
unexplored next step
canonical: `docs/issue-2326/reports/adversarial-review-ddab0192.md`, "Open findings" item 1, read
directly this session
-- this round's job was to build that variant and test it against the real thing, not re-argue the
point. Building the real hook (not a standalone timing script) and running it end-to-end against the
traced episode's actual payload shape is what surfaced the second defect (orphaned-grandchild pipe
blocking) that a pure "time the pytest command" measurement -- what both PR #2860 and PR #2863 did --
could not see, because that defect only manifests in the exact `subprocess.run(capture_output=True)`
invocation shape the hook itself uses. That is diagnose-first Stage 2's verify move taken seriously:
intervening on the candidate fix and re-measuring the actual artifact, not a proxy for it.

The rework-fraction re-derivation is scoped exactly to what the task asked: rebuild it on a corpus that
still exists, restricted to the population the hook can reach (matching PR #2859's own methodology for
comparability), and say plainly what corpus was used so a later reader can re-run it. It is not claimed
to be the same number as before -- it is an independent measurement that happens to land in the same
range, which is what materiality-on-a-different-corpus honestly looks like.

## What did not work

- First attempt at the per-item timeout invoked pytest via `capture_output=True` (a pipe), inheriting
  this repo's default `-n auto` xdist. Under `-n auto`, the same per-item bound left the sleeping file
  costing ~24s wall-clock instead of ~3s (xdist worker distribution overhead, not the timeout mechanism
  itself, was the culprit -- measured directly, see "What was done" item 1's xdist comparison) --
  switched to `-o addopts=""` for this specific invocation once measured, not assumed.
- After disabling xdist, three consecutive real end-to-end hook invocations against the traced
  episode's `spawn.py` edit still hit the outer 15s budget and reported `budget exceeded`, contra
  isolated `python3 -m pytest ... | tail` timings taken minutes earlier that showed 9-14s. Expected the
  discrepancy to be host-load noise (this is a shared, multi-tenant machine); it was not -- direct
  instrumentation (see "What was done" item 2) traced it to the orphaned-grandchild pipe-blocking
  defect, which is invocation-shape-specific, not load-specific. Fixed via process-group kill plus
  temp-file capture rather than raising the budget or lowering the per-file timeout, since either of
  those would have papered over a real defect instead of fixing it.
- A background `warrant-hunter` dispatch (before-landing, stance 0, forced full 180s/two-stance tier
  per the hooks/-path rule since the diff touches `on-the-record/hooks/`) found a real bypass -- see
  "What was done" item 3 and the hunt record at `docs/issue-2326/reports/diagnose-first-71f82584/
  2026-08-30-hunt-per-file-timeout-ship.md`. Fixed before landing rather than deferred.
- `python3 gates/spec_index.py --update` (the reconciled-index regenerator the docs/specs/* directive
  calls for) errors on this branch and on `origin/main` alike with `FileNotFoundError:
  roles/specs/brand-design.spec.json`
  derived: `git show origin/main:roles/specs/brand-design.spec.json` → no such object, this session;
  `python3 gates/spec_index.py --update` on this branch → same `FileNotFoundError`, this session
  -- a pre-existing breakage unrelated to this round's change, not attempted to fix here (out of
  scope for a hook-ship decision).

## Upstream basis

- `docs/issue-2326/reports/diagnose-first-56b99f15.md` (sha `060f1f10655d41f2072865c1e2ce7a093fed2412`,
  merged)
  canonical: `git log -1 --format=%H -- docs/issue-2326/reports/diagnose-first-56b99f15.md` →
  `060f1f10655d41f2072865c1e2ce7a093fed2412`, this session
  -- PR #2860's ship/no-ship redo; import-graph selection's accuracy and the rework_fraction.py
  boundary fix are taken as established here, not re-derived.
- `docs/issue-2326/reports/adversarial-review-ddab0192.md` (sha `99b6461674d82adf4f531f1e97dd2e50c084cc60`,
  merged)
  canonical: `git log -1 --format=%H -- docs/issue-2326/reports/adversarial-review-ddab0192.md` →
  `99b6461674d82adf4f531f1e97dd2e50c084cc60`, this session
  -- PR #2863's bisection of the 31.4-31.7s timing to `test_bootstrap_signal_guard.py`'s deliberate
  `time.sleep(30)` calls, and its "unverified, corpus gone" finding on the 4.5% figure.
- `docs/issue-2326/reports/adversarial-review-941d677c.md` (sha
  `b33943b9659ac46e6e8c0cb66a98e0b40db19742`, merged)
  canonical: `git log -1 --format=%H -- docs/issue-2326/reports/adversarial-review-941d677c.md` →
  `b33943b9659ac46e6e8c0cb66a98e0b40db19742`, this session
  -- the traced episode's own trajectory dump (session `on-the-record-issue-2795-silent-failure-
  audit-3da5ceae`, edits to `board.py`/`spawn.py`/`watchdog.py`, the three real failing tests).
- `scripts/rework_fraction.py` (sha `060f1f10655d41f2072865c1e2ce7a093fed2412`) -- read in full,
  re-run unmodified against a new corpus this session (no code change to this file this round).
- Live session-log corpus at `$MUSTER_WORKSPACE_ROOT/on-the-record-*.session.*.log` (13 files at
  measurement time, 2026-08-30, per the `ls | wc -l` output quoted in "What was done" item 4).
- PR #2855's branch (issue-2326/diagnose-first-4658f30a, head sha
  `d81146222a90804e39e730c5d08e62c47a171ab1`)
  canonical: `git fetch origin issue-2326/diagnose-first-4658f30a:refs/remotes/origin/pr2855-branch &&
  git log -1 --format=%H origin/pr2855-branch` → `d81146222a90804e39e730c5d08e62c47a171ab1`, this
  session
  -- fetched to read the original hook script's structure before rewriting it with import-graph
  selection and the per-item timeout.
- This session's own before-landing hunt: `docs/issue-2326/reports/diagnose-first-71f82584/
  2026-08-30-hunt-per-file-timeout-ship.md` (same-commit, sha cabaae7044972f59ad0beab935d8f4b215bc8c67).

## Open findings

1. The per-item timeout is validated against the one traced episode and its one known slow file. It
   has not been stress-tested against a wider sample of edited files, or against a slowness mode
   `SIGALRM` cannot interrupt cleanly (e.g. a tight CPU-bound loop with no syscall boundary). Resolution
   path: none attempted here (matches PR #2863's own open finding 1's scoping) -- a follow-up would need
   a broader sample of real edits before treating this as fully general.
2. The rework-fraction corpus (13 sessions) is smaller than the prior citation's (10, filtered from a
   larger set). The 4.6% figure is an independent measurement on different, currently-live data, not a
   re-derivation of the prior 4.5%. Resolution path: none needed for this round's ship decision
   (materiality holds at either number, given a real median per-episode cost of several turns per the
   `median=5.5` figure above), but a future reader re-running the exact command in "What was done" item
   4 will get a different corpus and a different number, by design (session logs rotate).

## Next steps

loop_state: landed.
acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` — result:
```
.....................                                                    [100%]
21 passed in 2.34s
```
acceptance: `python3 -m pytest test/ tests/ -q` in a clean `origin/main` worktree vs. this branch,
sorted `FAILED` lines diffed — result:
```
$ diff /tmp/failed_main.txt /tmp/failed_branch2.txt && echo "IDENTICAL SETS (post-fix)"
IDENTICAL SETS (post-fix)
```
(15 FAILED lines on each side, re-run twice this session -- once before and once after the docs/.. fix,
identical both times)
acceptance: `grep -n "role" scripts/rework_fraction.py on-the-record/hooks/lint-test-on-edit.sh on-the-record/hooks/otr_lint_test_timeout_plugin.py tests/test_spawn_gate_wiring.py` — result:
```
on-the-record/hooks/lint-test-on-edit.sh:89:# No role-axis: this hook keys nothing on a role/skill identity (only
on-the-record/hooks/lint-test-on-edit.sh:93:# gates, per the retired-role-axis decision
on-the-record/hooks/lint-test-on-edit.sh:94:# (docs/decisions/2026-08-25-retire-role-axis-staging.md).
```
(3 matches, all inside the new hook's own "No role-axis:" disclaimer comment explaining that the hook
does *not* key on role/skill identity -- the same disclaimer pattern the original PR #2855 hook shipped
with; `scripts/rework_fraction.py`, unmodified this round, has zero matches, as in every prior round's
citation)
acceptance: overhead measured on real edits, this round's own subject — result:
```
docs-only edit (.md file): 0.002s, no subprocess
low-fan-in code edit (watchdog.py, 1 impacted test): 1.14s
high-fan-in traced-episode edit (spawn.py, 34 impacted tests + bounded sleeper): 9.15-13.21s across 8 real end-to-end runs, inside the 15s budget every time
```
derived: 3 separate direct hook invocations this session (docs-only, watchdog.py, and the 8-run
spawn.py set already quoted in "What was done" item 1)
acceptance: `python3 -m pytest test/ tests/ -q -k "monitor or watch"` and
`python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` — result:
```
...............                                                          [100%]
15 passed in 1.17s
......                                                                   [100%]
6 passed in 0.84s
```
(both match PR #2860's and PR #2863's own citations exactly)

No further action by this role this round; the issue's fast-model-delegation follow-on (Ask's second
half) remains out of scope, as it has been every prior round, since it touches spawn/directive-assembly
surfaces owned by #2324/#2325.
