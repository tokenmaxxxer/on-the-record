---
issue: 3182
role: silent-failure-audit+adversarial-review+test-depth-audit-f6d7707f
author: silent-failure-audit+adversarial-review+test-depth-audit-f6d7707f
skills: silent-failure-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3184's round-4 deliverable
loop_state: done
type: verification
breaking: false
verdict: Fourth independent verification of PR #3184, round 4 (commit 046f12b7ee7234812430f487ffeed7ede5aae3fd). Both defects PR #3203's record found are genuinely fixed. Extending the attack past round 4's own repro found one new, narrow instance of the same defect class round 4's except-site-only sweep missed -- os.statvfs() succeeding but reporting exactly 0 free inodes still reports the precondition satisfied. Not a regression introduced by round 4 -- it mirrors an identical pattern already in spawn.py's own real gate. All three acceptance checks and the full suite reproduce clean this round; read-only behavior, exit-code discrimination, and the bidirectional doc-drift test hold under independently constructed mutants distinct from round 3's and PR #3203's own.
upstream:
  - path: docs/issue-3182/reports/adversarial-review+test-depth-audit+conformance-review-traceability-and-evidence-1839fd7b.md
    sha: 163a1a0a4fc1f4d9841fce82003c39d7a0d16878
  - path: scripts/preflight/consumer_preconditions.py (untracked path here -- lives on PR #3184's branch, not yet merged to main)
    sha: 046f12b7ee7234812430f487ffeed7ede5aae3fd
  - path: tests/test_issue_3182_citation_line_accuracy.py (untracked path here -- lives on PR #3184's branch)
    sha: 046f12b7ee7234812430f487ffeed7ede5aae3fd
---

# issue-3182 — silent-failure-audit+adversarial-review+test-depth-audit-f6d7707f record

## What was done

Fourth independent verification of PR #3184 (`tokenmaxxxer/on-the-record#3182`,
branch `issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`),
now at round 4. canonical: `gh pr view 3184 --json number,title,headRefName,state`
(this round) -- `state: OPEN`, tip `046f12b7ee7234812430f487ffeed7ede5aae3fd`
(derived: `gh pr view 3184 --json commits -q '.commits[-1].oid'` (this round)
-> `046f12b7ee7234812430f487ffeed7ede5aae3fd`). All work ran in a `git
worktree` fetched at that tip, outside `/tmp`
(`/home/jwjung/.tokenmaxxxer/work/_review-worktrees/pr3184`, removed via
`git worktree remove --force` at the end of this session -- derived:
`git worktree list` (this session, after cleanup) -> only this session's own
primary worktree listed). PR #3184 itself was never edited, commented on, or
merged this round.

### 1. Observation-failure fix -- Present, extended past the original repro

derived: reproduced PR #3203's exact monkeypatch this round (`shutil.disk_usage`
faked to succeed, `os.statvfs` faked to raise `OSError`) against
`check_workspace_disk_headroom()` at
`scripts/preflight/consumer_preconditions.py:210-223` (untracked path here,
worktree above, commit `046f12b7ee7234812430f487ffeed7ede5aae3fd`), via a
scratch script (`fault_inject_1.py`, case A) --
```
result: satisfied=False detail='953674MB free at <probe>, but inode headroom
could not be observed: OSError: simulated statvfs failure'
```
Confirms the fix: unsatisfied, naming what could not be observed. Extended
with four more injections against the same function, each derived this
round via the same scratch script
(`/home/jwjung/.tokenmaxxxer/work/_review-worktrees/scratch/fault_inject_1.py`,
run against the fetched worktree above):

- `os.statvfs` succeeds but returns an object missing `f_favail` (case B) --
  ```
  result: satisfied=False detail="...AttributeError: 'NoInodeFields' object
  has no attribute 'f_favail'"
  ```
  caught by the existing `except (OSError, AttributeError)`.
- `os.statvfs` raises a non-`OSError` (`ValueError`, case D) -- the function
  itself re-raises (its local `except` only names `OSError`/`AttributeError`),
  but `run_checks()`'s outer catch-all at `consumer_preconditions.py:389`
  (untracked path here) degrades the whole check instead of the whole script
  crashing:
  ```
  result (via cp.run_checks(), same scratch script): {'name':
  'workspace_disk_headroom', 'satisfied': False, 'remedy': '... (observed:
  check raised ValueError: weird non-OSError failure)', ...}
  ```
  the script never crashes and never reports satisfied, though the message
  is generic rather than naming the inode observation specifically.
- the probed path is removed between the `shutil.disk_usage()` call and the
  `os.statvfs()` call (case E) --
  ```
  result: satisfied=False detail="...FileNotFoundError: [Errno 2] No such
  file or directory: '.../tmpuwrp90gx'"
  ```
- `os.statvfs` succeeds and returns `f_favail=0` (case C) --
  ```
  result: satisfied=True detail='953674MB free, n/a free inodes at <probe>'
  ```
  a new, narrower instance of the same defect class -- see "Open findings"
  below.

### 2. Sweep -- every other precondition, same shape -- Present, one gap in round 4's own method

derived: independently fault-injected an observation failure into every
`CHECKS` entry's check function (not a re-read of round 4's own
`except`-site grep), via a second scratch script
(`fault_inject_sweep.py`, this round, same worktree):
`claude_cli_on_path` (`shutil.which` raises `RuntimeError`),
`git_cli_on_path`/`gh_cli_authenticated`/`git_identity_configured`
(`shutil.which` succeeds, `subprocess.run` raises `OSError`/`TimeoutError`/
`PermissionError`), `skill_repository_resolvable` (`Path.is_dir`/
`Path.iterdir` raise a non-`OSError` `RuntimeError`, both the top-level and
the nested-`iterdir` case), `home_claude_skills_dir_present` and
`target_repo_board_file_present` (`Path.is_dir`/`Path.is_file` raise a
non-`OSError` `RuntimeError`).
```
result (fault_inject_sweep.py, this round): claude_cli_on_path -> unsatisfied
[OK]; git_cli_on_path -> unsatisfied [OK]; gh_cli_authenticated ->
unsatisfied [OK]; git_identity_configured -> unsatisfied [OK];
skill_repository_resolvable -> unsatisfied [OK] (both injections);
home_claude_skills_dir_present -> unsatisfied [OK];
target_repo_board_file_present -> unsatisfied [OK]
```
Seven check functions probed (`git_identity_configured` counted once;
`skill_repository_resolvable` probed twice) -- derived: counting the
`check_one(...)` calls in `fault_inject_sweep.py` itself, this round -- all
report unsatisfied, none crash the script. `posix_fork_support` (pure
`hasattr`, no I/O) and `remote_push_access` (hardcoded `False`, no
observation performed) have no observation-failure mode to inject --
confirmed by reading `check_posix_fork`/`check_remote_push_access`,
`consumer_preconditions.py:82-87,175-184` (untracked path here, same
worktree), directly. Zero new defects among these eight functions.

Round 4's own sweep, per its own record (`docs/issue-3182/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923.md`,
untracked path here, worktree above, sha
`046f12b7ee7234812430f487ffeed7ede5aae3fd`), states its method as: "derived:
`git grep -n "except" scripts/preflight/consumer_preconditions.py`, 5
matches" and classifies exactly those 5 `except` sites. That method
structurally cannot find the zero-free-inodes gap in item 1 above, because
that gap is not an `except` site at all -- canonical:
`scripts/preflight/consumer_preconditions.py:225` (untracked path here,
same worktree), read directly this round: `if free_inodes and free_inodes <
min_inodes:` -- a boolean-falsy branch inside the try block's success path,
invisible to a grep for `except`. The defect class this round's brief named
("a satisfied verdict surviving an observation that did not happen") is
broader than "except sites"; round 4's sweep covered the narrower literal
reading of its own chosen search term.

### 3. Citation test discrimination -- Present, plus two edge cases probed and reported

derived: retargeted a synthetic anchor (`"child_pid = os.fork()"`) onto a
comment line bearing the identical text, then onto the real call line below
it, via `_line_is_code_match` imported directly from
`tests/test_issue_3182_citation_line_accuracy.py` (untracked path here,
worktree above), scratch script `citation_discrimination_probe.py`, this
round --
```
result: comment-line match=False (expect False); real-call-line
match=True (expect True)
```
acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q`
(untracked path here, this round, worktree outside `/tmp`) -- result:
```
10 passed in 0.91s
```
This includes `test_all_sixteen_real_anchors_still_pass`, whose own body
asserts `checked == 16` (`tests/test_issue_3182_citation_line_accuracy.py:341`,
untracked path here) -- all sixteen real anchors independently confirmed
still passing through the discriminating matcher by this pytest run.

Two edge cases beyond the brief's explicit list, both probed this round with
scratch fixtures against `_line_is_code_match` directly (same scratch
script):
- **Call split across two lines** (`os.fork(\n    )\n`) --
  ```
  result: line1 'os.fork()' match=False, line2 match=False; line1
  'os.fork(' partial match=True
  ```
  the matcher works line-by-line, so a substring straddling a line break
  matches neither line -- a false negative, not the reported false-positive
  direction. No live `CHECKS` anchor currently spans a multi-line call, per
  the 10-passed pytest run above (which includes the 16-anchor count
  assertion); not a live regression, flagged in Open findings as a latent
  limitation.
- **Match inside an f-string** --
  ```
  result: assigned f-string ('msg = f"calling os.fork() now..."')
  match=True; bare f-string statement (docstring-shaped, unassigned)
  match=False
  ```
  an f-string that participates in a real expression still matches, same as
  any other non-bare string literal; a *bare* f-string statement (the
  f-string equivalent of a docstring) is correctly masked out. Both
  behaviors are consistent with round 4's own documented, deliberate choice
  (canonical: round 4's own record's "Why" section, quoted in "Upstream
  basis" below) to mask only bare-statement strings, not all strings -- no
  divergence found.

### 4. Regression check -- Present except the one item above

- Read-only: derived: `git status --porcelain` before and after two
  consecutive runs (plain and `--json`) of
  `scripts/preflight/consumer_preconditions.py` (untracked path here) in
  the worktree above, this round --
  ```
  result (diff of before/after status files): no output, empty diff
  ```
- Satisfied/unsatisfied verdicts: acceptance: `python3 scripts/preflight/consumer_preconditions.py --json`
  (untracked path here, this round, worktree outside `/tmp`) -- result:
  ```
  exit=1; satisfied count 9 / 10 -- derived: python3 -c "import json;
  d=json.load(open('json2.txt')); print(sum(1 for p in d['preconditions']
  if p['satisfied']), '/', len(d['preconditions']))" in the same command,
  this round; the one unsatisfied entry is remote_push_access (mandated by
  design, section on hardcoded-False above)
  ```
- Handbook lists: derived: reading `docs/handbooks/install-sufficiency.md`
  (untracked path here, worktree above) via `grep -n "^- \|^#"`, this round
  -- 4 bullets under "What could be removed by changing the plugin" (grep
  output lines 63,70,77,89) + 6 bullets under "Preconditions that cannot be
  removed" (grep output lines 101,103,106,109,113,118); `4 + 6 = 10`,
  matching the 10 total `CHECKS` entries derived in the satisfied/unsatisfied
  bullet immediately above (9 satisfied + 1 unsatisfied = 10).
- Exit-code discrimination: derived: reproduced the always-`return 0`
  mutant in a disposable `cp` copy of the worktree above (not round 4's own
  copy), this round --
  ```
  result: python3 -m pytest
  tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_exit_code_tracks_actual_satisfaction_state
  -q -o addopts="-n0" -> FAILED -- AssertionError: 0 != 1
  ```
  confirming the test still discriminates.
- Bidirectional doc-drift test: derived: reproduced the removal direction
  with a different `CHECKS` entry than PR #3203 used
  (`workspace_disk_headroom` instead of `git_identity_configured`, for an
  independently constructed mutant) in a second disposable `cp` copy, this
  round --
  ```
  result: python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py
  -q -o addopts="-n0" -> 1 failed, 3 passed --
  test_doc_table_row_count_matches_live_precondition_count: AssertionError:
  10 != 9
  ```
  confirming the test catches removal regardless of which entry is removed.
- Zero silently absorbed error paths: **not fully true this round** -- the
  five `except` sites (`consumer_preconditions.py:68,157,202,213,389`,
  untracked path here) are all Handled per the silent-failure-audit
  catalog, confirmed by the sweep in section 2 above, but the
  zero-free-inodes branch at `consumer_preconditions.py:225` (same file) is
  a Silently-Absorbed-shaped defect (a real "0" measurement conflated with
  "unavailable", producing a satisfied verdict without genuine confirmation)
  that lives outside any `except` block -- see Open findings.

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` (untracked path here, this round, worktree outside `/tmp`) -- result:
```
11 passed in 13.07s
```
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` (untracked path here, this round) -- result:
```
4 passed in 9.04s
```
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` (untracked path here, this round) -- result:
```
4 passed in 4.83s
```
derived: `python3 -m pytest tests/ -q` (this round, full suite, worktree outside `/tmp`) -- result:
```
399 passed, 2 warnings in 17.77s
```
The two warnings are the same pre-existing, unrelated pinned-fixture-divergence
notice (issue #3019, `test_skill_candidates_floor.py`) round 3's and round
4's own records both note -- canonical: the warning text itself, printed in
this round's own pytest output above, names `captured 2026-09-01T03:40:29Z`
and `_bm25_cross_family_scores()`, neither touched by this round or by PR
#3184's own diff.

## Why

Attacked the two named fixes first with the exact reproduction (section 1's
case A), then deliberately varied the failure shape (missing field, zero
value, wrong exception type, vanishing path -- section 1's cases B-E) rather
than only re-confirming the one shape already known to be fixed -- a fix
proven against one monkeypatch shape does not by itself prove the
surrounding branch is robust to adjacent shapes of the same failure.
canonical: section 1's own fault-injection results above (case C, `f_favail=0`
-> `satisfied=True`) -- this is what surfaced the zero-free-inodes gap: it
is not the shape PR #3203 reproduced (an exception), so round 4's fix (an
`except` clause) does not touch it.

Ran the sweep independently by fault-injection against every check function
rather than re-reading round 4's `except`-site classification, per this
round's brief ("do that sweep yourself, independently"). canonical: section
2 above's comparison of this round's fault-injection method against round
4's own record's stated `git grep -n "except"` method -- doing the sweep
independently is what surfaced the gap in round 4's own sweep *method*
(except-sites only) as itself a finding: the completeness of a sweep
depends on matching the sweep's search method to the shape of the defect
class named, not just re-deriving the same enumeration a prior round
already produced.

Reproduced the exit-code and doc-drift mutation tests with deliberately
different mutants than round 3/PR #3203 used (a different `CHECKS` entry
for the doc-drift removal) -- canonical: section 4 above's two `derived:`
reproductions, each naming the specific mutant used (`workspace_disk_headroom`
removal vs. PR #3203's `git_identity_configured` removal) -- so the
reproduction is independent rather than a restatement of a prior round's
own scratch work.

## Upstream basis

- `docs/issue-3182/reports/adversarial-review+test-depth-audit+conformance-review-traceability-and-evidence-1839fd7b.md`
  (PR #3203, sha `163a1a0a4fc1f4d9841fce82003c39d7a0d16878`, read via `git
  show <sha>:<path>` this round) -- the two defects round 4 was tasked to
  fix, and the citation-test/statvfs reproduction details this round's
  item 1 and item 3 extend.
- `docs/issue-3182/reports/implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf.md`
  (round 3's own record, on this branch, sha
  `25176d39b6ea54154064fe00f1d9059d912371fc`) -- background for the ten
  `CHECKS` entries and the three previously reported out-of-scope
  `sys.exit` gates (`core_root`/`core_plugin_dirs`, `require_doctor`,
  `ensure_target_remote`), unchanged by this round, not re-litigated here.
- `docs/issue-3182/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923.md`
  (round 4's own record, untracked path here -- lives on PR #3184's branch,
  sha `046f12b7ee7234812430f487ffeed7ede5aae3fd`, read via `git show
  <sha>:<path>` against the fetched worktree this round) -- round 4's own
  claims, independently re-derived throughout this record rather than
  trusted; its "Why" section states the string-masking design choice this
  round's item 3 f-string probe checked against ("considered excluding
  *all* string literals ... rejected it: two of the 16 real anchors ...
  cite text that lives inside a string literal that *is* the actual code").
- `scripts/preflight/consumer_preconditions.py` (untracked path here),
  `tests/test_issue_3182_citation_line_accuracy.py` (untracked path here),
  `tests/test_issue_3182_preflight.py` (untracked path here),
  `tests/test_issue_3182_install_sufficiency_doc.py` (untracked path here),
  `docs/handbooks/install-sufficiency.md` (untracked path here) -- all live
  on PR #3184's branch, sha `046f12b7ee7234812430f487ffeed7ede5aae3fd`,
  read from the worktree fetched at that tip, this round.
- `spawn.py:729-764` (`_spawn_capacity_check`) -- derived: `sed -n
  '725,765p' spawn.py` (this round, read from this same worktree's
  checkout) -- confirms the zero-free-inodes falsy-check pattern found in
  item 1 above is an exact mirror of spawn.py's own real gate
  (`if free_inodes and free_inodes < min_inodes:` appears at both
  `spawn.py:754` and `consumer_preconditions.py:225`), not a divergence
  introduced by the preflight script.

## Open findings

1. **`check_workspace_disk_headroom()` reports satisfied when
   `os.statvfs()` succeeds and returns exactly `f_favail=0`.** canonical:
   `scripts/preflight/consumer_preconditions.py:225` (untracked path here,
   read directly this round in the worktree above):
   `if free_inodes and free_inodes < min_inodes:` -- `0` is falsy in
   Python, so a real zero-free-inodes measurement takes the same branch as
   "not applicable," and the function falls through to `return True,
   f"...{free_inodes or 'n/a'} free inodes..."`, reporting the precondition
   satisfied while printing "n/a free inodes" for a measurement that was
   actually `0`, not unavailable -- reproduced this round, section 1's
   case C (`fault_inject_1.py`): `satisfied=True detail='953674MB free,
   n/a free inodes at <probe>'`. This is the same defect class PR #3203's
   record found and round 4 fixed (a satisfied verdict surviving an
   observation that did not genuinely confirm sufficiency), in a location
   round 4's `except`-site-only sweep (section 2 above) could not have
   found. Not a regression introduced by round 4 or any prior round of
   this issue's chain -- canonical: `spawn.py:754` (derived: `sed -n
   '725,765p' spawn.py`, "Upstream basis" above) carries the identical `if
   free_inodes and free_inodes < min_inodes:` pattern, and the preflight
   script's own module docstring (`consumer_preconditions.py:9-13`,
   untracked path here) states it deliberately "mirrors spawn.py's own
   logic" -- so if this is a real bug, it already exists in the production
   gate this preflight is modeling, not only in the preflight itself.
   Resolution path: distinguish "not observed" (the `except` branch,
   already fixed this round) from "observed as exactly zero" (this
   branch) -- e.g. track observability with a sentinel (`None`) rather
   than relying on `0`'s truthiness, in both this script and, as a
   separate follow-up outside this issue's scope, `spawn.py` itself.
2. **Citation-accuracy matcher: a call literally split across two source
   lines cannot match either line.** No live `CHECKS` anchor is currently
   affected -- acceptance: `python3 -m pytest
   tests/test_issue_3182_citation_line_accuracy.py -q` (untracked path
   here, section 3 above) -- result: `10 passed`, including the 16-anchor
   count assertion. A latent limitation, not a live defect; worth a code
   comment or docstring note if the matcher is extended, not urgent enough
   to block this round.
3. Carried forward, unchanged by round 4 or this round: the three
   dispatch-path `sys.exit` gates round 3's record found and explicitly
   deferred (`core_root`/`core_plugin_dirs` at
   `pipeline.py:408-447,500-513`, `require_doctor` at `pipeline.py:521-548`,
   `ensure_target_remote` at `pipeline.py:786-820`) remain open, outside
   this round's authorized scope (the two round-4 defects plus the sweep),
   same as round 4's own record states -- canonical: round 3's own record
   (cited in "Upstream basis" above), "Open findings" section.

## Next steps

acceptance: `python3 -m pytest tests/ -q` (this round, full suite, section "What was done" area above) -- result: `399 passed, 2 warnings` -- all three issue-acceptance checks and the full suite reproduce clean this round, so `loop_state: done` reflects this verification's own completion, not PR #3184's landing (merge is out of this session's authority per contract v3). Round 4's two defect fixes are confirmed genuine (sections 1 and 3 above); this round found one new, narrow, non-regression defect of the same class (Open finding 1) plus two non-blocking edge-case observations (Open findings 2-3), recorded above for a follow-up round to pick up. Per the brief: PR #3184 was not merged and not edited this round -- derived: `git status --porcelain` run in the fetched worktree immediately before its removal, this round -- result: empty (no uncommitted changes ever introduced there); all fault injection ran against disposable worktree/scratch copies outside `/tmp`, cleaned up (`git worktree remove --force`, `rm -rf`) at the end of this session -- derived: `git worktree list` (this session, after cleanup) -> only this session's own primary worktree listed.

## skill-verdict

skill-verdict: silent-failure-audit — applied: invoked; used the
enumerate-classify-trace-forward procedure against
`check_workspace_disk_headroom()` and all nine other `CHECKS` check
functions via targeted fault injection (section 2 above, not a re-read of
round 4's own `except`-site grep), classifying the zero-free-inodes branch
in Open finding 1 as Silently Absorbed under the catalog's
"default/fallback value substituted without recording that a fallback
occurred" pattern (a real `0` measurement conflated with "unavailable") --
canonical: section 1 case C and Open finding 1 above, both citing the same
`consumer_preconditions.py:225` line and its reproduced result
(`satisfied=True detail='953674MB free, n/a free inodes at <probe>'`).
skill-verdict: adversarial-review — applied: invoked; treated round 4's own
record as a claim to attack rather than a status to confirm -- reproduced
its two fix claims exactly (section 1 case A, section 3), then deliberately
varied each fix's failure shape past what round 4 itself tested (section 1
cases B-E), and reran its sweep by independent fault injection instead of
trusting its `except`-site enumeration (section 2) -- canonical: section 2
above's direct comparison of this round's method against round 4's own
record's stated `git grep -n "except"` method, which is what surfaced both
the zero-inodes gap and the sweep-method gap.
skill-verdict: test-depth-audit — applied: invoked; classified
`test_all_sixteen_real_anchors_still_pass` and
`test_doc_table_row_count_matches_live_precondition_count` as Genuine
Assertion by reproducing mutants independently constructed from this
round's own reading (a different removed `CHECKS` entry than PR #3203 used,
a synthetic retargeted-anchor fixture rather than only the existing
`CitationCommentAndStringDiscriminationTest` fixtures), per section 4
above's independently-constructed-mutant reproduction:
```
acceptance: python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q -o addopts="-n0" (workspace_disk_headroom-removed mutant copy, this round)
result: 1 failed, 3 passed -- AssertionError: 10 != 9
```
rather than accepting round 4's or PR #3203's own reproduction as sufficient
proof of depth.
other mounted skills: not triggered — work-in-english's guidance was
followed for this record's own English text (Korean reserved for any final
chat summary); it enforces via core hooks, not a Skill-tool call.
