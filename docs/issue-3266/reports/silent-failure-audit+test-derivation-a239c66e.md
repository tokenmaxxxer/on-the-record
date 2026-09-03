---
issue: 3266
role: silent-failure-audit+test-derivation-a239c66e
author: silent-failure-audit+test-derivation-a239c66e
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: done
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3269
    sha: bac2cef31c19680578dcec807ebaef43a20cb820
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3271 (docs/issue-3266/reports/silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1da15a65.md)
    sha: 9bdb7390bb86bb4e18121a735059e696e93bde68
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3272 (docs/issue-3266/reports/adversarial-review+test-depth-audit-4d603aad.md)
    sha: 54c4c084078b454eb44055057927ca055e20754e
---

# issue-3266 — silent-failure-audit+test-derivation-a239c66e record

## What was done

canonical: `gh pr view 3269 --json state,mergeable` (state: OPEN, mergeable:
CONFLICTING before this round) and `gh pr view 3271`/`gh pr view 3272`
(both state: MERGED) -- read directly this session before any edit.

Round 2 on this issue. PR #3269 (the untracked-stub reclaimability
classifier in `lifecycle.py`) was verified sound by two independent
reviews -- PR #3271 and PR #3272, both merged -- but had drifted out of
date with `main` and could no longer land. This round:

1. Rebased PR #3269's branch (`bac2cef3` classifier commit + its record
   commit) onto current `main` at `5e7d48b8`. `lifecycle.py` and `spawn.py`
   merged automatically (`dry_run` from `3e35a8a5` and the classifier's own
   changes touch disjoint regions). Only `scripts/preflight/consumer_preconditions.py`
   conflicted -- pure line-number anchors that had moved twice on `main`
   since the PR branched. derived: `grep -n "os.fork()\|def
   _spawn_capacity_check\|shutil.disk_usage\|_spawn_capacity_check(work)\|proc
   = subprocess.Popen(" spawn.py` against the post-merge working tree gave
   738 (`def _spawn_capacity_check`), 749 (`shutil.disk_usage`), 754
   (`sys.exit(`), 3368 (`_spawn_capacity_check(work)` call site), 2772 and
   4939 (the two `os.fork()` sites), 5061 (`proc = subprocess.Popen(`) --
   all 4 conflicted anchor pairs were hand-fixed to these re-derived
   numbers rather than trusting either side of the conflict.
2. Fixed the three findings both reviews raised, all in the over-deletion
   direction:
   - **FIFO hang** (PR #3271): `_report_stub_has_no_content()` now does
     `path.lstat()` and checks `stat.S_ISREG(st.st_mode)` *before* calling
     `read_text()` -- a FIFO (or any non-regular file) returns `False`
     (kept, not reclaimable) immediately instead of blocking forever on a
     read with no writer.
   - **Symlink workspace escape** (PR #3271): when `lstat()` shows a
     symlink, the target is resolved (`path.resolve(strict=True)`) and
     checked for containment inside the workspace
     (`target.relative_to(w.resolve(strict=True))`) before anything about
     it is trusted; a target outside the workspace returns `False`
     regardless of what it looks like. A symlink whose target stays inside
     the workspace is unaffected (still read and classified on its own
     content, as before).
   - **Heading-only / bare-hash misread** (PR #3272): the line-skip
     condition changed from "any line starting with `#`" to
     `_STRUCTURAL_HEADING_RE = re.compile(r"^#{1,2}(?:\s.*)?$")` -- only a
     level-1 or level-2 ATX heading (the two levels the record skeleton
     itself uses: the `# issue-N -- role record` title and `## <Section>`
     headers) is treated as disposable structure. A level-3+ heading
     carrying real prose, or a bare `#`-prefixed line with no space after
     the hash (not valid heading syntax at all), now counts as content.
3. Added 4 regression tests to `tests/test_issue_3266_reclaimable_stub.py`
   covering all three fixes plus one already-covered control, and re-ran
   both acceptance checks and the full suite.
4. Re-measured `spawn.py clean --dry-run` on this machine, genuinely
   read-only this time (`3e35a8a5` wired `--dry-run` after the earlier
   round's numbers were produced by real deletion passes), before (current
   `main`) and after (this branch) -- see Upstream basis / measurement
   below.

## Why

canonical: `gh pr view 3271` and `gh pr view 3272` output (both state:
MERGED), bodies read in full this session -- both report zero flips in the
unsafe direction and confirm the classifier fails closed on every
synthetic OSError-raising case they constructed, alongside the three
findings this round fixes.

Do not rebuild the classifier -- both independent reviews already confirmed
it correct on its own terms per the citation immediately above. The task
was narrower: make PR #3269 mergeable again, and close the three specific
gaps the reviews found without touching anything the reviews didn't flag.
Each fix stays inside `_report_stub_has_no_content()` and preserves its
existing fail-closed contract (every branch that can't establish real
content returns `False`, i.e. "kept") -- consistent with the acceptance's
`must not` direction: it is always safer to leave a workspace than to lose
one.

skill-verdict: silent-failure-audit — applied: invoked; enumerated every
`except`/error-branch site added or touched in the rewritten
`_report_stub_has_no_content()` (5 sites: `lstat()`, `resolve(strict=True)`,
`relative_to()`, `target.stat()`, `read_text()`) and classified each --
all 5 are Handled by the pre-existing, documented design: every branch that
cannot establish real content returns `False` (kept/protected), matching
the function's own docstring contract cited above. None absorb an error in
the dangerous (over-deletion) direction. The one gap this audit surfaces
but does *not* fix (out of this round's scope -- named as "unresolved" by
PR #3271 itself, not one of the three findings this PR was asked to close)
is that all 5 branches collapse to the same generic `False` with no
distinguishing diagnostic at the `roster_clean()` print line -- an operator
still cannot tell "FIFO" from "symlink escape" from "permission denied"
from the `남김` output alone. See Open findings below.

skill-verdict: test-derivation — applied: invoked; treated the three review
findings themselves as the requirements for this round -- each already
stated as a concrete before/after behavior in the PR #3271/#3272 bodies
cited above -- and derived one equivalence-partition test per finding on
the input dimension each defect turns on: special-file type at the report
path (FIFO vs. regular vs. the pre-existing directory-at-path case),
symlink target locality (outside the workspace vs. the pre-existing
inside-workspace and dangling/self-loop cases), and line-content shape
(level-3+ heading with prose vs. bare non-heading `#`-line vs. the
pre-existing level-1/2 structural-heading and `None.` cases) -- plus kept
the existing control (`test_crashed_session_shape_is_reclaimable`)
unchanged to confirm the fix doesn't disturb the classifier's original
corpus-validated behavior (canonical: `bac2cef3`'s commit message and the
`_report_stub_has_no_content()` docstring in `lifecycle.py`, both already
citing the `~/.tokenmaxxxer/salvage-20260903` corpus split this control
test's shape is drawn from -- exact figures re-verified independently by
PR #3272, see its body). Medium-depth: this is infrastructure maintenance
on an already-reviewed predicate, not a fresh feature, so one boundary case
per finding plus the existing control was judged proportionate over a full
formal partition/traceability matrix.

skill-verdict: work-in-english — applied: invoked implicitly per this
project's standing routing rule; this record, the commit messages, and the
PR title/body are in English, and Korean is reserved for the end-of-turn
summary.

other mounted skills: not triggered (skill_judge amendment named
adversarial-review, defect-verification-independence-from-upstream-verdicts,
merge-gates, parallel-decomposition, implementation-audit as candidate
matches for this task -- judged not-applicable: the first two are
verification-role skills for auditing someone else's deliverable
independently, and this round's role is implementer applying findings two
other sessions already verified, not a third independent verification;
parallel-decomposition does not apply because this session's own STEP 1
freelunch tally (first message of this turn) found this a single
sequential unit -- rebase, then fix, then measure, each depending on the
previous step's real output -- with no freezable contract to split it on;
merge-gates and implementation-audit have no distinct trigger match beyond
what the hook-contract and record-shape directives already enforce
mechanically for this landing).

## What did not work

None.

## Upstream basis

- PR #3269 (`bac2cef3`): the classifier this round rebases and fixes --
  `_is_harness_scaffolding_path()`, `_report_stub_has_no_content()`,
  `_is_reclaimable_untracked_noise()` in `lifecycle.py`.
- PR #3271 (`9bdb7390`, record at
  `docs/issue-3266/reports/silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1da15a65.md`):
  source of the FIFO-hang and symlink-escape findings, fixed here.
- PR #3272 (`54c4c084`, record at
  `docs/issue-3266/reports/adversarial-review+test-depth-audit-4d603aad.md`):
  source of the heading-only/bare-hash finding, fixed here; also the origin
  of the stale-closing-keyword incident this round was warned to avoid
  repeating.

Acceptance checks, run on this branch after both fixes and the rebase:

acceptance: `python3 -m pytest tests/test_issue_3266_reclaimable_stub.py test/test_workspace_dirty_classification.py -q` — result:
```
....................                                                     [100%]
20 passed in 0.96s
```
(12 from `tests/test_issue_3266_reclaimable_stub.py` -- 8 pre-existing + 4
new regression tests for the three fixes -- and 8 unchanged from
`test/test_workspace_dirty_classification.py`.)

Full suite, run on this branch:

acceptance: `python3 -m pytest -q` — result:
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
2 failed, 1624 passed, 3 xfailed in 47.27s
```

derived: `git clone` of this branch checked out to `origin/main` in a
scratch directory, then `python3 -m pytest -q
harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
on-the-record/checks/test_macos_bash32_compat.py -q` -- result: both fail
identically on `main` alone (same assertion content), confirming the
acceptance's "must not: no new failures relative to main" holds. Neither
failure touches `lifecycle.py`, `spawn.py`, or either test file this round
changed.

**Measurement (genuine dry run, `--dry-run` is read-only as of `3e35a8a5`
-- derived: read `roster_clean()`'s `dry_run` branch in `lifecycle.py`
directly -- it prints and increments a counter but never calls
`_delete_workspace()`, and skips `_prune_worktrees()` too):**

Both runs against this machine's real `~/.tokenmaxxxer/work`, back to
back, same machine state:

acceptance: `python3 spawn.py clean --dry-run -C <repo>` on `origin/main` (scratch checkout) — result:
```
[dry-run] 정리 끝 — 지움 0, 남김 45
```
acceptance: `python3 spawn.py clean --dry-run -C <repo>` on this branch — result:
```
[dry-run] 정리 끝 — 지움 0, 남김 45
```

derived: `diff /tmp/measure_main.txt /tmp/measure_fixed.txt | grep -c
'^<'` and the matching `grep -c '^>'` both = 22 (out of 45 total kept-line
pairs) -- 22 of the 45 kept-workspace detail lines changed wording between
the two runs (the classifier is doing real work: several `미추적 파일 N건`
counts dropped, one workspace's untracked bracket disappeared entirely),
but the summary counts are identical on both sides and 0 workspaces flipped
from kept to reclaimable on this specific machine state.

This is a genuine, freshly-run result on this machine's current state, not
a re-run of the earlier count (derived: `gh issue view 3266 --json
comments`, read this session -- the issue's 2026-09-03T04:42:24Z comment
quotes "지움 1, 남김 32" from that pass) from this issue's thread -- that
number came from a real-deletion `clean` pass (per PR #3271's finding 4,
`--dry-run` was not actually read-only until `3e35a8a5` landed after that
comment was posted), and this machine had already been hand-cleaned down
to 45 workspaces since then, by the same comment's own account. Every one
of the 45 remaining workspaces is blocked by an unpushed commit and/or a
real content change in addition to (or instead of) untracked-stub noise,
so removing the stub-noise contribution alone was not enough to flip any
of them this time. This is consistent with, not contradictory to, the
issue's most recent reopened-state comment (2026-09-03T05:39:47Z, same `gh
issue view` read): the untracked-stub cause this classifier targets is
narrow, and the remaining causes (unpushed commits dominating every kept
workspace on this now-mostly-clean machine) are unmeasured and out of this
round's scope.

## Open findings

1. `roster_clean()`'s kept/deleted print lines still carry no
   distinguishing reason beyond the coarse `[미추적 파일 N건]` /
   `[미push 커밋 N건]` counts -- an operator cannot tell from the output
   alone that a workspace's untracked count dropped because of this
   classifier, or which of the five fail-closed branches in
   `_report_stub_has_no_content()` fired for a given file. Named by PR
   #3271 as its own open finding 1, explicitly "not fixed by PR #3269";
   still not fixed here -- out of this round's stated scope (rebase +
   the three named findings + re-measurement). Resolution path: thread a
   reason string through `_is_reclaimable_untracked_noise()` back to the
   caller's `detail` construction.
2. The remaining causes that keep every workspace on this machine (almost
   entirely unpushed commits, per the measurement above) are unmeasured.
   Not this round's scope; the issue stays open for that measurement per
   this PR's own "Advances, not closes" framing.

## Next steps

acceptance: acceptance checks and full-suite run cited in Upstream basis
above — result: applied, tested, and passing on this branch's current
HEAD (aside from the two confirmed-pre-existing-on-main failures). None
remain for this round; the two open findings above are scoped to a future
round, not this one.
