---
issue: 2326
role: adversarial-review-813a3aa7
author: adversarial-review-813a3aa7
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2875 (branch issue-2326/silent-failure-audit+diagnose-first-0f11c1bf, head efd3d777bdbe1f0467efd022dee6852910f58213, untracked in this review session's own working tree)
type: verification
breaking: false
verdict: partial -- the decisive claim (a budget-exceeded run can never be read as a pass) holds under independent adversarial reproduction, and the symlink-fastpath fix generalizes structurally rather than by spelling. But the round's own checked "no overhead increase, measured under concurrency" invariant does not hold: the per-repo-root advisory lock measurably serializes genuinely independent concurrent edits and, at the PR's own real-repo-scale 8-way identical-edit test shape, produces a worse outcome distribution than no lock at all on well-provisioned hardware -- see "What was done" below for the executed evidence.
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/silent-failure-audit+diagnose-first-0f11c1bf.md
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
  - path: on-the-record/hooks/otr_lint_test_timeout_plugin.py
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
  - path: tests/test_spawn_gate_wiring.py
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
---

# issue-2326 — adversarial-review-813a3aa7 record

## What was done

Independently re-derived PR #2875's four claims against a fresh checkout
of the PR branch (`git fetch origin pull/2875/head`, head
`efd3d777bdbe1f0467efd022dee6852910f58213`), not by re-reading the PR's
own record. All commands below ran in this session, against real
subprocess invocations of the shipped hook script -- no mock of the
hook's own internals. The hook script, its pytest plugin, and its
regression-test file are all untracked in this review session's own
working tree (this branch is based on `main`, which never merged PR
#2866 or PR #2875) -- see "Upstream basis" below for their exact paths
and the sha they were read at on PR #2875's own branch.

**1. Reproduced the original failure first, on the fixed branch.**

canonical: the hook script's full python body (lines 137-575, see
Upstream basis for path and sha), read directly this session before any
reproduction attempt.

Ran the same 8-concurrent shape PR #2870 used against a real `spawn.py`
edit, fresh `git clone` of this branch (35 impacted test files matched
by the import-graph selector -- derived: `python3 /tmp/repro_8way.py
/tmp/otr-repro-a`, this session, output line count; default 15s budget,
no lock override):

```
run 0: rc=0 dur=13.20s shape=FULL-FAILURE-REPORT
run 1: rc=0 dur=15.03s shape=EXPLICIT-INCOMPLETE
run 2: rc=0 dur=15.03s shape=EXPLICIT-INCOMPLETE
run 3: rc=0 dur=15.03s shape=EXPLICIT-INCOMPLETE
run 4: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 5: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 6: rc=0 dur=15.05s shape=EXPLICIT-INCOMPLETE
run 7: rc=0 dur=15.06s shape=EXPLICIT-INCOMPLETE
```
derived: `python3 /tmp/repro_8way.py /tmp/otr-repro-a` (this session's
own harness, not the PR's), run 3 times across this session (24 total
invocations) -- 0 empty/silent, 0 unrecognized across all 24. The exact
text a budget-exceeded run emits, captured verbatim this session:

```
lint-test-on-edit: budget exceeded (15s) -- verdict INCOMPLETE, NOT
verified clean: lint/test checks for spawn.py did not finish in time
```
derived: single hook invocation under `OTR_LINT_TEST_BUDGET_S=15` inside
the 8-way concurrent batch above, this session. This message cannot be
mistaken for a clean pass -- the decisive claim holds: across all 24
invocations run this session, zero produced empty stdout, and every
budget-exceeded run's JSON explicitly said "INCOMPLETE" or "ALREADY
CONFIRMED FAILING", never silence.
canonical: this session's own 24-invocation run log directly above
(3 batches of 8, each batch's per-run shapes recorded at the time it
ran) -- not a summary or a grep signal, the raw classified output of
each subprocess call.

**2. Attacked the durability claim directly.**

canonical: the hook script's `_FAILED_LINE_RE` /
`_extract_confirmed_failures` block (lines 425-441, see Upstream basis
for path and sha), read directly this session.

First isolated how pytest actually writes a `-v` progress line, since
that determines whether a mid-write kill can produce a false read.
`strace -f -e trace=write -s 200` on a real `python3 -u -m pytest -v`
run against a 4-test fixture showed each result line is written as
four separate `write()` syscalls, not one:

```
write(1, "../../../../../tmp/durability-probe/tests/test_probe.py::test_b_fails ", 70) = 70
write(1, "FAILED", 6)           = 6
write(1, " [ 50%]", 7)          = 7
write(1, "\n", 1)               = 1
```
derived: `strace -f -e trace=write -s 200 -o /tmp/strace2.out python3 -u -m pytest -o addopts= -v /tmp/durability-probe/tests/test_probe.py`, this session.
This means a kill can only land in one of two states: before the
outcome-word `write()` (nodeid only, no "FAILED"/"ERROR" token present
-- `_FAILED_LINE_RE` cannot match, correctly falls through to the
INCOMPLETE report, never a false confirm) or after it (the outcome word
is a single already-completed `write()` syscall, durable regardless of
what happens next). No window exists where a partial write could
produce the literal token "FAILED" or "ERROR" for a test that actually
succeeded.

Then constructed the actual race end-to-end through the real hook (not
just the write-syscall probe): a fixture with one test that fails in
under 0.1s and one that sleeps 30s, both importing the edited module,
budget forced to 2s so the kill lands mid-run:

```
lint-test-on-edit: budget exceeded mid-run (tests/test_a_fails_fast.py,
tests/test_b_sleeps_past_budget.py) -- 1 test(s) ALREADY CONFIRMED
FAILING before the timeout (scan incomplete, more may be broken):
tests/test_a_fails_fast.py::test_calls_broken
```
derived: constructed fixture at `/tmp/durfix` (a real `git init` repo,
`shared_thing.py` plus two test files), `OTR_LINT_TEST_BUDGET_S=2
OTR_LINT_TEST_PER_FILE_TIMEOUT_S=100 bash <hook-script-path> post`
against a real edit payload for `shared_thing.py`, this session. The
recovered failure is exactly the one real failure that had already
happened -- not fabricated, not missing.

Checked the one plugin class that could break this guarantee (a rerun
plugin that overwrites an already-flushed FAILED line with a later
successful-outcome line), and its live-risk status:
```
$ pip show pytest-rerunfailures
WARNING: Package(s) not found: pytest-rerunfailures
```
derived: `pip show pytest-rerunfailures`, this session -- not installed
in this repo, so no live vector to a false-positive "ALREADY CONFIRMED
FAILING" was found today. canonical: this exact `pip show` output
immediately above -- this is a property of the current dependency set,
not a structural guarantee independent of it, tracked as Open finding 2
below with this same citation.

**3. Attacked the lock -- this is the finding that changes the verdict.**

canonical: the hook script's `_acquire_repo_lock` function (lines
369-396, see Upstream basis for path and sha), which scopes the lock to
`hashlib.sha1(root_dir...)` -- one lock file per repo root, not per
edited file or per overlapping test set.

*Holder-dies case*: confirmed no deadlock. A process that acquires the
flock and is then `SIGKILL`ed releases it immediately (kernel-level fd
close semantics, not application code) -- a second waiter reacquired
the same lock path immediately after the kill:

```
holder reported: HELD
holder killed, pid gone: -9
re-acquired after killed holder: True in 0.000s
```
derived: `python3 /tmp/lock_holder_dies.py`, this session (a standalone
`fcntl.flock` harness against the same lock-path convention the hook
uses). No deadlock risk from a dead holder.

*Two-repos case*: confirmed no cross-repo contention -- the lock path is
`sha1(root_dir)`, and two distinct absolute paths hash to two distinct
lock files:
```
$ python3 -c "import hashlib; print(hashlib.sha1(b'/tmp/repoA').hexdigest()[:16]); print(hashlib.sha1(b'/tmp/repoB').hexdigest()[:16])"
9a64611ceb3d6a19
d5e17c794b78922a
```
derived: this exact computation, this session. Edits to different repos
never queue behind each other.

*Same-repo, independent-edit case*: this is where the "no overhead
increase" claim breaks. Built a fixture with 4 completely disjoint
modules (`mod1.py` through `mod4.py`), each with its own test file
importing only that module (no shared test, no shared code), each test
taking about 2.4s. Measured 4 concurrent edits (one per module) against
the real hook, with and without the lock (a byte-for-byte copy of the
hook with only the `_acquire_repo_lock` call short-circuited to
`(None, False)`):

```
WITH lock:    mod1=2.38s mod2=4.78s mod3=7.17s mod4=9.57s  (staircase --
              each waits for the previous)  TOTAL WALL CLOCK: 9.57s
WITHOUT lock: mod1=2.49s mod2=2.49s mod3=2.49s mod4=2.49s  (true parallel)
              TOTAL WALL CLOCK: 2.49s
```
derived: `python3 /tmp/lock_overhead.py` run against both the real hook
script (with lock) and a copy with the lock call short-circuited (no
other change), this session, on a 16-core host -- derived: `nproc` = 16,
this session. This is a measured wall-clock overhead of 9.57s / 2.49s =
3.8x for editing four files that share nothing -- the lock serializes
work that was never in contention for anything but the lock itself.

The same effect reproduces at the PR's own real-repo-scale test shape
(8 concurrent invocations of the identical `spawn.py` edit, 35 impacted
test files, default 15s budget) -- and here the lock does not merely
add overhead, it produces a worse outcome distribution than no lock at
all, on this 16-core host:

```
                        FULL-FAILURE-REPORT   EXPLICIT-INCOMPLETE   PARTIAL-RECOVERED
WITH lock,    run A:    1/8                    6/8                   0/8
WITH lock,    run B:    1/8                    7/8                   0/8
WITH lock,    run C:    1/8                    7/8                   0/8
WITHOUT lock, run A:    4/8                    0/8                   4/8
WITHOUT lock, run B:    4/8                    0/8                   4/8
WITHOUT lock, run C:    5/8                    0/8                   3/8
```
derived: `python3 /tmp/repro_8way.py /tmp/otr-repro-a` (with lock) vs
`python3 /tmp/repro_8way_nolock.py /tmp/otr-repro-a` (lock call
short-circuited, otherwise byte-identical), each run 3 times back to
back in this session against the same fresh checkout. With 16 real
cores and only 8 concurrent single-process pytest invocations, the OS
scheduler can run all 8 substantially in parallel when nothing forces
them to queue; forcing them onto one lock instead means invocations
5 through 8 spend most of their budget waiting for invocations 1
through 4's test step to finish before their own even starts,
guaranteeing more of them exhaust the budget than would have without
the lock. This directly contradicts the PR's own record, which
describes the lock as reducing "how often the budget is hit" -- on this
hardware, measured 3 times each way, it did the opposite.

This does not undermine the durability fix verified in the section
above (every run in both the locked and unlocked measurements still
reported explicitly, never silently -- canonical: the same two 3-run
tallies immediately above, 0 silent/empty results across all 48
invocations) -- the lock is additive to that guarantee, not a
precondition for it. But it does falsify the round's own checked "no
overhead increase" invariant (see "Open findings" and the invariant
re-derivation below): the PR's concurrency test only ever exercised 8
identical edits (same test set, so full serialization costs nothing
beyond what CPU contention already implies for overlapping work) -- it
never tested disjoint concurrent edits, which is the shape that exposes
the regression and the shape the task explicitly asked to be measured.

**4. The symlink fix: tried shapes it was not built against.**

canonical: the hook script's realpath-resolution block (lines 247-267:
resolve, then extension check, then `"docs" in real_parts[:-1]`, see
Upstream basis for path and sha), read directly this session.

Built 4 shapes in a fresh synthetic repo, none matching the single
`docs/live_spawn.py -> ../spawn.py` shape the fix was built against:

```
A (2-hop symlink chain, docs -> docs -> real code outside docs):
  docs/level1_A.py -> link2_A.py -> ../real_code_A.py           => LINT-CAUGHT (correct)
B (symlinked DIRECTORY component, not a symlinked file):
  docs/realcode_B -> ../src_real (real dir), edit realcode_B/module_B.py => LINT-CAUGHT (correct)
C (literal invoked path has NO "docs" substring anywhere,
   target genuinely lives in docs/):
  weird_alias_C.py -> docs/notes_C.py                            => SKIPPED (correct -- really is docs)
D (deep nested docs path escaping via 3 levels of ..):
  docs/sub/dir/link_D.py -> ../../../real_code_D.py               => LINT-CAUGHT (correct)
```
derived: `python3 /tmp/test_shape.py <path> <label>` against each of the
4 constructed symlinks in `/tmp/symtest` (a real `git init` repo), this
session -- all 4 classified correctly. Shapes A, B, D resolve outside
`docs/` and were correctly NOT skipped despite looking docs-shaped in
the literal invoked path; shape C resolves genuinely inside `docs/` and
was correctly skipped despite its literal invoked path containing no
"docs" substring at all. This confirms the fix resolves paths
structurally rather than matching a wider set of spellings -- the
round's claim on this point holds.

**5. Materiality: interval, not point estimate -- confirmed.**

canonical: PR #2875's own new content (the round-4 record file, the
hook script's header comment, and `docs/reports/product/quality-bar.md`
-- see Upstream basis for the record's path and sha), each read
directly this session.

derived: `grep -rn "%" <hook-script-path> docs/reports/product/quality-bar.md <round-4-record-path>`, this session. This
round's own materiality mentions are all either "4.3%" alongside the
explicit "1.1%-6.0%" interval, or the interval itself -- the only bare
"4.6%"/"4.5%" figures found by that grep live in round 3's untouched
record file (`diagnose-first-71f82584.md`, not modified by this PR),
not in this round's own claims. Confirmed: no single figure is asserted
as *the* materiality number anywhere this round added or touched.

**6. Standing invariants, re-derived independently (not copied from the PR's own record).**

Coverage note (the task's named test-coverage trap): every command
below runs `test/ tests/` -- it does NOT collect `harness/`, which
carries its own test files:
```
$ grep -c "def test_" harness/test_driver.py harness/test_signals.py
harness/test_driver.py:26
harness/test_signals.py:7
```
derived: this exact command, this session. Checked whether this blind
spot is live for this specific PR:
```
$ grep -rl "lint-test-on-edit\|hooks.json\|PostToolUse" harness/*.py
(no output -- no matches)
```
derived: this exact command, this session. `harness/` tests do not
reference any file this PR touches, so the gap is real (every round of
this issue, including this one, has had it) but not currently hiding a
regression from this PR's own changes.

- No role-axis reintroduction:
```
$ grep -n "role" <hook-script-path> <plugin-path> <regression-test-path>
131:# No role-axis: this hook keys nothing on a role/skill identity...
136:# (docs/decisions/2026-08-25-retire-role-axis-staging.md).
137:# gates, per the retired-role-axis decision
```
derived: this exact command (paths per Upstream basis below), this
session -- 3 matches, all inside the hook's own disclaimer comment,
none in executable code.

- No new bug, compared as SETS OF NAMES (not counts): fresh `git clone`
  of `origin/main` and a fresh `git clone` of this PR's head, `python3
  -m pytest test/ tests/ -q` in each, `grep '^FAILED' | sort` on both,
  `diff` between the two sorted files:
```
$ diff /tmp/main_failed.txt /tmp/pr_failed.txt
(no output -- files identical)
$ wc -l /tmp/main_failed.txt /tmp/pr_failed.txt
15 /tmp/main_failed.txt
15 /tmp/pr_failed.txt
```
derived: this session, both commands above. `origin/main` result line:
"15 failed, 470 passed, 3 xfailed". This branch's result line: "15
failed, 497 passed, 3 xfailed". The delta between 497 and 470 is
exactly the new regression-test file's own new-test count:
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py --collect-only -q -o addopts=""
27 tests collected in 0.01s
```
derived: this exact command, this session.

- No overhead increase, measured under concurrency: FAILS -- see the
  lock-attack section above for the full derived: citations.

- Monitor/watch machinery unbroken, not quieter:
```
$ python3 -m pytest test/ tests/ -q -k "monitor or watch"
origin/main:  15 passed in 1.01s
this branch:  15 passed in 1.10s
```
derived: this session, both worktrees, this exact command. Identical
pass count, not quieter.

## Why

The task named the durability claim as load-bearing and asked for the
race to be constructed directly rather than taken on the code's word --
the `strace` probe was the fastest way to settle whether "unbuffered
plus -v" actually closes the write-then-kill race, because it shows the
exact syscall boundaries a kill can land between, which no amount of
reading the python source alone would reveal. The lock measurement
followed the task's explicit instruction to measure under concurrency
rather than accept the "additive, reduces frequency" framing at face
value -- the PR's own concurrency evidence never varied whether the
edits were independent, which is exactly the condition under which a
repo-root-scoped lock's cost is entirely avoidable overhead rather than
legitimate contention management.

## What did not work

None -- every reproduction attempt in this session completed and
produced a result (confirming or falsifying the corresponding claim).
canonical: the six numbered subsections under "What was done" above,
each closed with its own `derived:`-cited command and result -- no
attempt was abandoned mid-way, and no scope-exceeded stop occurred.

## Upstream basis

- `docs/issue-2326/reports/silent-failure-audit+diagnose-first-0f11c1bf.md`
  -- sha `efd3d777bdbe1f0467efd022dee6852910f58213`, untracked in this
  review session's own working tree -- this PR's own record, present on
  its branch at this sha, read in full this session as the claims list
  to attack, not as a source of evidence.
- `on-the-record/hooks/lint-test-on-edit.sh` -- sha
  `efd3d777bdbe1f0467efd022dee6852910f58213`, untracked in this review
  session's own working tree -- this PR's shipped hook script, present
  on its branch at this sha, read directly this session; line numbers
  cited above are from this version.
- `on-the-record/hooks/otr_lint_test_timeout_plugin.py` -- sha
  `efd3d777bdbe1f0467efd022dee6852910f58213`, untracked in this review
  session's own working tree -- unchanged by this round, read directly
  this session.
- `tests/test_spawn_gate_wiring.py` -- sha
  `efd3d777bdbe1f0467efd022dee6852910f58213`, untracked in this review
  session's own working tree -- this round's new regression-test file,
  read directly this session.
- `docs/issue-2326/reports/adversarial-review-37c43bc9.md` (PR #2870's
  verification, the round-3 no-ship basis this round claims to fix) --
  canonical: `gh pr view 2870 --json state` -> `MERGED`, this session --
  read to confirm which four findings this round claims to address, not
  used as evidence for whether it actually does.

## Open findings

1. **Lock overhead regression (blocking for the "no overhead increase"
   invariant, not for the decisive durability claim).** The per-repo-
   root advisory lock serializes concurrent edits that share no files
   and no test dependency, at a measured 3.8x wall-clock cost for 4
   disjoint edits, and produces a worse budget-exhaustion rate than no
   lock at all at the PR's own 8-way identical-edit test scale on a
   16-core host (canonical: the two "WITH lock" / "WITHOUT lock" tables
   in the lock-attack section above, this session's own measurements).
   Resolution path: either scope the lock more narrowly than "the whole
   repo root" (e.g., per matched-test-file-set, or per edited-module),
   make it configurable/skippable for well-provisioned hosts, or drop
   it and rely solely on the durability fix (which does not depend on
   the lock for correctness -- confirmed in the unlocked measurements
   above, where every invocation still reported explicitly, never
   silently).
2. **Durability guarantee is plugin-set-dependent, not structural.**
   canonical: the `pip show pytest-rerunfailures` result in the
   durability-attack section above, this session -- the package is not
   installed, so the never-false-positive property holds today but is a
   property of the current dependency set, not an invariant independent
   of it: a rerun-style plugin that overwrites an already-flushed
   FAILED line with a later successful-outcome line would let
   `_extract_confirmed_failures()` report a failure for a test whose
   later rerun actually succeeded. Not a live bug today, since no such
   plugin is present; worth a one-line guard or comment noting the
   assumption if this hook's dependency set ever changes. Non-blocking.
3. **Test-coverage trap, structural not new.** Every round's "no new
   bug" comparison, including this one, is scoped to `test/ tests/` and
   has never covered `harness/` (canonical: the coverage-note grep
   results in the invariant re-derivation section above). Confirmed not
   live for this PR specifically (no reference to changed files from
   `harness/`), but the blind spot persists into future rounds unless
   the comparison command's own scope changes. Non-blocking for this
   PR.

## Next steps

None -- `loop_state: landed`. canonical: the verdict line in this
record's own frontmatter above, derived from the six numbered
subsections under "What was done" (this session's own executed
evidence, not a restatement of PR #2875's claims). The ship decision on
PR #2875 should weigh the lock-overhead finding above (the lock does
not deliver what it claims to, and measurably regresses the outcome
distribution on well-provisioned hardware) against the fact that the
decisive durability and symlink fixes both hold under direct
adversarial reproduction.

skill-verdict: adversarial-review — applied: invoked; this session
acted as the structurally independent evaluator itself (per the role-
handoff protocol, not a separately spawned sub-session) -- received the
PR's diff and its own record, but re-derived every claim from a fresh
checkout and constructed original attack scenarios (the disjoint-edit
lock measurement, the strace write-boundary probe, the 4 novel symlink
shapes) rather than re-running or re-reading the PR's own evidence as
proof.
other mounted skills: work-in-english — applied: invoked implicitly via
this session's English-only commit messages and this record, per the
standing project convention; not separately invoked as a distinct tool
call since its guidance is a passive style constraint, not an action to
perform. test-depth-audit, silent-failure-audit, implementation-audit,
parallel-decomposition, verify-finding-record — not-applicable: this
session's task was a direct adversarial reproduction of a fix's own
claims (durability, lock behavior, symlink resolution), not a test-
suite depth audit, an error-handling-path audit, a spec-to-code
traceability audit, a parallel build-fanout decision, or a defect-
verification record under docs/issue-<n>/reports/defect-verification/.
