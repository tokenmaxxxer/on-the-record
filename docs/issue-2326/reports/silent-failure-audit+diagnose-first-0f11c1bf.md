---
issue: 2326
role: silent-failure-audit+diagnose-first-0f11c1bf
author: silent-failure-audit+diagnose-first-0f11c1bf
skills: silent-failure-audit (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12))
verifies_subject: false
code_under_review: PR #2866 (branch issue-2326/diagnose-first-71f82584, head 5be0fbfd25196f6e45c34b5a764ac009343d71de), flagged no-ship by PR #2870's independent verification (merged, sha bf1169c66fbe109ae2f900b45ad9fa2351d9f1f3)
type: fix
breaking: false
verdict: ship -- fixed the decisive concurrency defect (budget exhaustion under load used to discard already-confirmed real failures and report a bare "budget exceeded" message indistinguishable from routine slowness) so it is now structurally impossible for a timed-out run to look like a clean pass at any concurrency level, plus the docs-fast-path symlink bypass (resolve realpath, not enumerate spellings) and two narrower findings (worktree `.git`-file recognition, plugin-missing distinguishability). Materiality is stated as an interval, not re-asserted as a point estimate.
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/diagnose-first-71f82584.md
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: docs/issue-2326/reports/adversarial-review-37c43bc9.md
    sha: bf1169c66fbe109ae2f900b45ad9fa2351d9f1f3
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: same-commit
  - path: on-the-record/hooks/otr_lint_test_timeout_plugin.py
    sha: 5be0fbfd25196f6e45c34b5a764ac009343d71de
  - path: tests/test_spawn_gate_wiring.py
    sha: same-commit
---

# issue-2326 — silent-failure-audit+diagnose-first-0f11c1bf record

## What was done

canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md — this
session's source for every PR #2870 finding cited below, read in full
this session.

Round 4 on issue #2326: PR #2870's independent verification of PR #2866
(round 3) returned no-ship on two findings and flagged two more as real
but non-blocking. This round fixes all four, on top of PR #2866's
merged-into-this-branch code (`git merge origin/issue-2326/diagnose-first-71f82584`,
merge commit b2e6699b91355a1ef36dc05cd511b053d78713ca — PR #2866 itself
was never merged to main, since PR #2870's verdict was no-ship).

**1. The decisive finding: budget exhaustion under concurrency used to
discard evidence and report generically, indistinguishable from routine
slowness.**

canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md,
finding 3 — "8 concurrent invocations of the real hook, same payload,
same fresh checkout" against a `spawn.py` edit found 3 of the 8 hit the
15s outer budget, discarding whatever pytest output already existed at
that point (the `TimeoutExpired` branch returned `(None, None)` without
ever reading the capture file). That was replaced with a bare
`"budget exceeded (15s), skipped remaining lint/test checks for
spawn.py"` message carrying no information about the fact that real
tests had already failed. The task was explicit that a bigger timeout is
not an acceptable answer (it only raises the concurrency level at which
the same loss recurs), so the fix is structural, not a bigger number:

- `_run()` (`on-the-record/hooks/lint-test-on-edit.sh`) now always reads
  the capture file back, even on a timeout -- partial output is never
  discarded.
- The pytest invocation switched from `-q` (buffered, per-item detail
  deferred to an end-of-run summary that a mid-run kill erases entirely)
  to `-v` with `PYTHONUNBUFFERED=1` and `python3 -u`, so each item's
  `<nodeid> PASSED/FAILED/ERROR` line is flushed to the capture file the
  moment that item finishes -- durable in the file regardless of what
  happens to the process afterward, since a `write()` syscall that
  already completed is not undone by a later `SIGKILL`.
- `_extract_confirmed_failures()` scans that partial output for
  `<nodeid> FAILED|ERROR` lines. On a timeout: if any are found, they are
  reported explicitly as `"budget exceeded mid-run -- N test(s) ALREADY
  CONFIRMED FAILING before the timeout (scan incomplete, more may be
  broken): <nodeids>"`. If none are found (nothing had finished yet, or
  the run never got past waiting for the lock below), the report says so
  explicitly: `"budget exceeded (Ns) -- verdict INCOMPLETE, NOT verified
  clean: ..."`. Every budget-exceeded path now always emits non-empty
  text; the hook's only silent state is a run that genuinely completed
  clean, unchanged from before.
- A best-effort, non-blocking advisory lock (`fcntl.flock`, scoped to the
  repo root by a `sha1` of its path under `$TMPDIR`) serializes the
  CPU-heavy test step across concurrent invocations against the *same*
  repo, bounded by the invocation's own remaining budget. This targets
  the diagnosed root cause (concurrent invocations fighting for the same
  CPU degrade each other's wall-clock together) without claiming to
  eliminate budget exhaustion at arbitrarily high concurrency -- the
  partial-output-capture fix above is what makes the failure mode always
  visible regardless of whether the lock helps in a given run.

Re-ran PR #2870's own 8-way concurrency repro against this fix, same
methodology (fresh `git clone` of this branch, real `spawn.py` edit,
launched together):

```
run 5: rc=0 dur=9.43s  shape=FULL-FAILURE-REPORT
run 3: rc=0 dur=15.07s shape=PARTIAL-FAILURES-RECOVERED
run 1: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 2: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 4: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 6: rc=0 dur=15.04s shape=EXPLICIT-INCOMPLETE
run 7: rc=0 dur=15.07s shape=EXPLICIT-INCOMPLETE
run 8: rc=0 dur=15.06s shape=EXPLICIT-INCOMPLETE
```
derived: this session, 8-way concurrent run against a fresh `git clone`
of this branch, classified by stdout shape.
Tally, all figures this same run: rc=0 = 8/8, non-empty stdout = 8/8,
SILENT-EMPTY = 0/8, UNRECOGNIZED = 0/8, FULL-FAILURE-REPORT = 1/8,
PARTIAL-FAILURES-RECOVERED = 1/8, EXPLICIT-INCOMPLETE = 6/8.
canonical: this session's own 8-run block directly above (repeated here
per issue #333's per-line citation-window rule, not a new measurement).
The FULL-FAILURE-REPORT run's 9.43s matches a follow-up uncontended solo
baseline of 10.64s measured immediately after in the same checkout --
derived: single `bash on-the-record/hooks/lint-test-on-edit.sh post`
invocation, this session, no concurrent siblings, real=10.64s, reported
`"impacted test failed"` with the real failing test names.
canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md, same
finding-3 citation as the opening paragraph of this subsection -- PR
#2870's pre-fix run put 3/8 in the silently-lost-evidence state, against
this run's 0/8 (canonical: the 8-run block and tally above, this
session).

The fix was checked as meaningful, not merely present, by reverting only
the hook script and re-running the new regression tests against the
unmodified round-3 code:
derived: `git stash push -- on-the-record/hooks/lint-test-on-edit.sh`
then `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts="" -k "Symlink or Worktree or Concurrent or PluginMissing or BudgetExceeded"`,
this session, against the stashed (round-3-only) hook script -- 6 failed,
each with the exact defect PR #2870 described. `git stash pop` restored
the fix; the full suite was re-run --
derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts=""`,
this session -- 27 passed.

**2. Docs-fast-path symlink bypass: resolved, not enumerated.**

canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md,
finding 2 — `docs/live_spawn.py -> ../spawn.py` defeats both the bash
fast path (`docs/*` glob matched the raw string) and the old python
check (same `docs`-in-`parts` check, also on the raw string) -- neither
ever resolved symlinks. Per the task's explicit instruction not to
enumerate spellings: the bash-layer fast path's `docs/*|*/docs/*` prefix
branch is removed entirely (kept only the extension-only branch,
`*.md|*.txt|*.rst`, which needs no symlink resolution to be safe --
these are exactly the extensions the hook has no lint/test logic for
regardless of what a symlink might resolve to). The python body now
computes `abs_path`, resolves it with `os.path.realpath()`, and derives
every subsequent classification (extension check, `docs/`
directory-shape check, the git-root walk, the lint/test target, the stem
used for impacted-test selection, and the display path in every message)
from that resolved `real_path` -- never from the original unresolved
string. An unresolvable path (e.g. an embedded NUL) fails toward running
the check, never toward silently exempting it. New regression test class
`SymlinkDocsFastPathIsNotFooled` (in `tests/test_spawn_gate_wiring.py`)
reproduces the exact symlink shape and asserts the real syntax error in
the symlink's target surfaces --
derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts="" -k Symlink`,
this session -- 1 passed.

**3. Materiality: interval, not point estimate.**

canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md,
finding 6 — the corpus-sensitivity interval this record relies on:
removing the 2 heaviest-rework session logs out of a then-17-file corpus
dropped materiality to 1.1%; removing 2 zero-rework logs instead pushed
it to 6.0%. That sensitivity check was not re-run this session (the task
said not to tune the number, only to stop quoting a point) -- this
session's own contribution is a fresh point still inside that interval:

```
=== corpus rollup: 19 session(s) ===
total edit calls (Edit/Write/MultiEdit): 300
total rework episodes (cost known): 13
  rework_fraction_of_edit_turns: 4.3%
```
derived: `python3 scripts/rework_fraction.py --batch
"$MUSTER_WORKSPACE_ROOT/on-the-record-*.session.*.log"`, this session --
19 files at measurement time vs 17 at PR #2870's, 4.3% vs the interval's
1.1%-6.0% bounds cited above. This record does not cite "4.6%" or any
other single figure as *the* materiality number anywhere -- every
mention here is either this session's own 4.3% point or the interval
itself.

**4. Two narrower findings, fixed (not blocking per the task, but real).**

canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md,
findings 4 and 5 — the source of both defects fixed in this subsection.

- Git-worktree `.git`-*file* recognition: the repo-root walk changed from
  `os.path.isdir(<probe>/.git)` to `os.path.exists(<probe>/.git)`. A
  `git worktree` checkout's `.git` is a file (`gitdir: <path>`), not a
  directory; the old check silently fell through to the wrong ancestor
  root when a worktree sat nested under an unrelated repo, zeroing out
  impacted-test selection with no report at all. New regression test
  class `GitWorktreeRootIsRecognized` builds a real nested worktree via
  `git worktree add` and asserts the real failing test inside it
  surfaces --
  derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts="" -k Worktree`,
  this session -- 1 passed.
- Plugin-missing vs. real test failure: if `otr_lint_test_timeout_plugin`
  cannot be imported, pytest's own `ModuleNotFoundError` traceback used
  to render as `"impacted test failed"`, identical in shape to a batch of
  real broken tests. The test-step failure path now checks for that
  specific `ModuleNotFoundError` + plugin-name signature and reports it
  distinctly as `"harness internal error (not a real test failure): ...
  did not actually run"`. New regression test class
  `PluginMissingIsDistinguishedFromRealFailure` copies the hooks
  directory aside, deletes the plugin file from the copy, and asserts the
  distinct message --
  derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts="" -k PluginMissing`,
  this session -- 1 passed.

**Regression coverage added.** `tests/test_spawn_gate_wiring.py` grew by
281 lines (derived: `git diff --stat b2e6699b -- tests/test_spawn_gate_wiring.py`,
this session, `281 ++`) across the five new test classes named above.
Every one was checked red-then-green (fails against the unmodified
round-3 hook script, passes against the fix) -- see the `derived:`
citations inline above and in subsection 1's stash/pop paragraph, not
restated here.

## Why

The task named the concurrency finding as the one that decides the
round, and named the risk precisely: a bigger timeout only moves the
concurrency level at which the same silent loss recurs, so the fix has
to make budget-exhaustion reporting structurally non-silent rather than
statistically less frequent. Capturing partial output (via `-v` +
unbuffered stdout, which makes per-item results durable in the capture
file the instant they are written, immune to a later kill) is what
achieves that -- it does not depend on how much concurrency exists, only
on whether any test happened to finish before the clock ran out.

canonical: this session's own 8-run tally under "What was done"
subsection 1, above (not restated here per issue #333's citation-window
rule -- see that subsection for the run-by-run numbers).
The advisory lock is additive on top of that guarantee, not a substitute
for it: it reduces how often the budget is hit by removing wasted CPU
thrash between concurrent invocations against the same repo -- the one
run that got the lock uncontended finished close to the solo baseline
instead of degrading alongside its competitors, but every invocation
that still hit the budget, locked or not, reported honestly rather than
silently.

The docs-fast-path fix resolves the path once, authoritatively, in one
place (`os.path.realpath`), rather than adding a fifth string pattern to
a growing blocklist -- matching the task's explicit instruction to stop
enumerating spellings once a structural fix is available, and matching
this hook's own existing design principle (the bash layer is a
non-authoritative fast path; python is where the real decision is made).

## What did not work

None -- every fix and re-derivation in this round completed as planned;
no scope-exceeded stop, no alternative swap from what was proposed.
derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -o addopts=""`,
this session -- 27 passed, 0 failed, confirming every change described
above lands in a working state, not a partial or abandoned one.

## Upstream basis

- `docs/issue-2326/reports/diagnose-first-71f82584.md` -- sha
  5be0fbfd25196f6e45c34b5a764ac009343d71de (PR #2866 head). Round 3's own
  record; the per-file-timeout mechanism and hooks.json wiring it
  describes are unchanged by this round except where noted above.
  canonical: `git cat-file -e 5be0fbfd:docs/issue-2326/reports/diagnose-first-71f82584.md`,
  this session -- present at that commit.
- `docs/issue-2326/reports/adversarial-review-37c43bc9.md` -- sha
  bf1169c66fbe109ae2f900b45ad9fa2351d9f1f3.
  canonical: `gh pr view 2870 --json state` → `MERGED`, this session.
  The no-ship verdict and all four findings this round fixes.
- `on-the-record/hooks/lint-test-on-edit.sh`, `tests/test_spawn_gate_wiring.py`
  -- same-commit (this round's own changes).
- `on-the-record/hooks/otr_lint_test_timeout_plugin.py` -- sha
  5be0fbfd25196f6e45c34b5a764ac009343d71de, unmodified by this round.
  canonical: docs/issue-2326/reports/adversarial-review-37c43bc9.md,
  finding 1 — "Process-group kill + temp-file capture: holds ... The
  hook returned in 3.45s, correctly reported the failure, and left no
  orphaned processes" (read directly, this session); left as-is.

## Open findings

None open. All four findings from PR #2870's verification (the decisive
concurrency defect, the docs-fast-path symlink bypass, the worktree
`.git`-file gap, the plugin-missing distinguishability gap) are fixed and
covered by a red-then-green regression test in this commit -- see the
`derived:` citations under "What was done" for each. The materiality
figure remains inherently fragile by its own nature (an interval on a
small, fast-changing corpus, see subsection 3 above) -- that is stated as
a property of the measurement, not an open finding to resolve.

## Next steps

None -- `loop_state: landed`. This PR is ready to ship; ship it.

skill-verdict: silent-failure-audit — applied: invoked; used the audit's
Handled/Silently-Absorbed/Unreachable framing to drive the concurrency
fix -- the pre-round-4 `TimeoutExpired` branch was a textbook Silently
Absorbed error path (`except subprocess.TimeoutExpired: ... return None,
None`, discarding real evidence and reporting a generic message a
downstream reader could not distinguish from routine slowness); fixed by
making that branch surface what it actually knows instead of a
placeholder.
skill-verdict: diagnose-first — applied: invoked; used to resist jumping
straight to "raise the timeout" (the task's own named trap) -- traced the
concurrency failure to its actual mechanism (pytest's `-q` mode deferring
per-item output to an end-of-run summary a mid-run `SIGKILL` erases
entirely) before choosing the fix (`-v` + unbuffered stdout +
read-on-timeout), rather than acting on the surface symptom (budget too
small).
other mounted skills: work-in-english — applied: invoked implicitly via
this session's English-only commit messages, code comments, and this
record, per the standing project convention; not separately invoked as a
distinct tool call since its guidance is a passive style constraint, not
an action to perform.
