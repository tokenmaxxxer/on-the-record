---
issue: 3095
role: adversarial-review+test-depth-audit+experiment-trust-b108e611
author: adversarial-review+test-depth-audit+experiment-trust-b108e611
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3106's own deliverable against issue #3095
loop_state: landed
code_under_review: e06909962b58130aa889b8c15561ade355bf89f3
type: defect-verification-record
breaking: false
verdict: 5 of 5 checked criteria Present (3 required acceptance checks, both
  explicit must-nots). Mechanism-reuse is Present with a disclosed,
  reasonable-but-real narrower divergence from PR #3084's shape (key
  compounding vs. a value-side repo field). Separately, this session's own
  broader sweep (not one of issue #3095's own criteria) found the
  cross-repo-leak pattern is NOT swept clean elsewhere in gates/ or
  watchdog.py -- logged as open findings, not counted against PR #3106.
upstream:
  - path: gates/spawn_on_pr.py
    sha: e06909962b58130aa889b8c15561ade355bf89f3
---

# issue-3095 — adversarial-review+test-depth-audit+experiment-trust-b108e611 record

## What was done

canonical: `gh issue view 3095 --repo tokenmaxxxer/on-the-record --comments`
output -- title "spawn-on-pr's parked-subject list leaks across repos the
same way requirement-drift did", targets R007, asks the fix to reuse PR
#3084's mechanism or document why not, and requires a sensitivity control
(the same unmodified probe must leak on main and not on the branch) per
issue #3081's must-not #2 (a check that passed vacuously on both trees was
mistaken for evidence there).

canonical: `gh pr view 3106 --repo tokenmaxxxer/on-the-record` output --
changes span `gates/spawn_on_pr.py`,
`e0690996:gates/probe_parked_report_repo_leak.py`,
`e0690996:tests/test_spawn_on_pr_repo_scope.py`,
`docs/specs/enforcement-boundary.md`, and the builder's own record +
deviation-log entry. derived: `gh pr view 3106 --repo
tokenmaxxxer/on-the-record --json additions,deletions` -- result:
`{"additions":699,"deletions":6}`.

This is a second independent, builder-blind verification of PR #3106
(branch head `e06909962b58130aa889b8c15561ade355bf89f3`) -- a different
verification is running in parallel; this record reaches its own verdict
by executing code, not by reading the parallel session's output or the
builder's record as settled.

Setup for everything below: `git fetch origin pull/3106/head:pr-3106-review`
then `git worktree add /tmp/pr-3106-review pr-3106-review` (PR #3106's
branch, contains `e0690996:gates/probe_parked_report_repo_leak.py` and
`e0690996:tests/test_spawn_on_pr_repo_scope.py`, both untracked in this
session's own working tree since they exist only on PR #3106's branch)
and `git worktree add /tmp/otr-main-verify origin/main` (main at
`7ee166122719b8b4f3bcde72d9a5c73885aaceee`, which already includes PR
#3089 -- the dependency the builder's own second issue-comment names as
blocking a clean read on all three required checks together) -- two
linked worktrees, so every command below ran the actual PR/main code, not
a paraphrase.

### Required acceptance check 1 -- `e0690996:tests/test_spawn_on_pr_repo_scope.py`

derived: `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q` (run
from `/tmp/pr-3106-review`, `e0690996:tests/test_spawn_on_pr_repo_scope.py`)
-- result: `6 passed in 1.62s`. Present.

### Required acceptance check 2 -- `e0690996:gates/probe_parked_report_repo_leak.py`

derived: `python3 gates/probe_parked_report_repo_leak.py` (run from
`/tmp/pr-3106-review`, `e0690996:gates/probe_parked_report_repo_leak.py`)
-- result:
```
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): ['issue-3059']
ok
```
exit 0. Present.

### Required acceptance check 3 -- `python3 -m pytest tests/ -q`

The builder's own second issue comment records this check was
unsatisfiable at the time PR #3106 was authored, because main itself was
red (pre-existing `tests/test_respawn_deliverable_gate.py` failures owned
by issue #3083, repaired by PR #3089) -- not a defect in PR #3106. That
dependency has since landed: `git log --oneline` (this session's own
branch) shows `7ee16612 issue-3083: fix hooks.json additive guard and
respawn-gate debounce test gap (#3089)` as the newest commit on
`origin/main`. Re-running the check fresh against current main confirms
the blocker is gone:

derived: `python3 -m pytest tests/ -q` (run from `/tmp/otr-main-verify`,
current `origin/main`, i.e. main WITH #3089 applied) -- result: `216
passed in 9.40s`.
derived: `python3 -m pytest tests/ -q` (run from `/tmp/pr-3106-review`,
PR #3106's branch) -- result: `222 passed in 10.37s`. derived: `216 + 6 =
222` (216 from the `origin/main` run directly above, plus this PR's own
six tests per "Required acceptance check 1" above) -- matches the 222
shown in the PR-branch run exactly. Present.

### Must-not 1 -- do not fix this by suppressing or rate-limiting the waiting-for-human line

derived: `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q -k includes_own_repo`
(run from `/tmp/pr-3106-review`) -- result: `1 passed` -- confirms a
repo's own genuine parked subject still surfaces after the fix, so a fix
that silenced everything to close the leak would have failed this test.
The probe's own `out_a` check (quoted in "What was done" above, `ok`
requires `SUBJECT in out_a`) enforces the same property independently.
Present.

### Must-not 2 -- sensitivity control: the same unmodified probe must leak on main and not on the branch

This is the exact clause issue #3081's must-not existed to prevent (a
check that passes vacuously on both trees being mistaken for evidence),
so this session ran it itself instead of relying on a description of
having done so.

derived: `cp /tmp/pr-3106-review/gates/probe_parked_report_repo_leak.py
/tmp/otr-main-verify/gates/probe_parked_report_repo_leak.py &&
python3 gates/probe_parked_report_repo_leak.py` (run from
`/tmp/otr-main-verify`, current `origin/main`, unmodified probe file
copied over unchanged) -- result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): ['issue-3059']
```
exit 1.
derived: the same unchanged probe file, run from `/tmp/pr-3106-review`
(PR #3106's own branch) -- result: `ok`, exit 0 (quoted in full under
"Required acceptance check 2" above).

Both runs shown, same file, byte-for-byte identical between the two
invocations (copied, not re-derived) -- leaks on main, passes on the
branch. Present.

### Mechanism reuse vs. reimplementation -- comparison against PR #3084

canonical: `git show e5172b24 -- watchdog.py` (PR #3084's full diff, read
from `/tmp/pr-3106-review`, `e5172b24` is the merged commit both this
session's and the builder's record cite as PR #3084's landing sha).
`watchdog._drift_cache_key(repo, number)` re-keys every
`requirement_drift_cache.json` entry as `f"{repo}:{number}"` -- both the
read path (`cache.get(_drift_cache_key(repo_slug, num))`) and the write
path go through the compound key, so a foreign-repo entry is not merely
misread, it is a different dict key entirely; retention/eviction falls
out of ordinary key non-membership, with no separate eviction branch
needed.

derived: `grep -n "_repo_slug" gates/spawn_on_pr.py watchdog.py spawn.py`
(run from `/tmp/pr-3106-review`) -- confirms PR #3106's
`spawn_missing_for_pr()`/`parked_report()` call `spawn._repo_slug(root)`,
the identical attribution primitive `watchdog.requirement_drift()` calls
for the drift cache (`watchdog.py:1155`, `_sp._repo_slug(root)`) --
**same repo-attribution point, genuinely reused, not reimplemented.**

Divergence: PR #3106 does NOT reuse `_drift_cache_key`'s compound-key
shape. `gates/spawn_on_pr.py`'s park state stays keyed by the bare
`subject` string (unchanged) and adds a `"repo"` field to each entry's
*value* instead. Eviction is an explicit branch --
```python
if prior is not None and prior.get("repo") != repo_slug:
    prior = None
```
(`gates/spawn_on_pr.py`, in `spawn_missing_for_pr()`) -- rather than key
non-membership. Read-time filtering (`parked_report`) and this
write-time eviction branch produce the same outcome #3084 gets from
compound keys for the two properties issue #3095's own acceptance
actually tests (report-time leak, retention/eviction split) --
confirmed identical by this session's own probe/test runs above, run
against the real entrypoints, not by reading the diff alone.

Behavior is NOT fully identical, and the builder's record
(`e0690996:docs/issue-3095/reports/implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md`,
"Why" section) discloses this explicitly, unprompted: because the key
itself still isn't repo-scoped, two different repos' ticks can still
collide **on write** for a literal same-numbered subject (e.g. both
repos independently have their own "issue-100") -- #3084's compound key
closes this for drift; this fix does not close it for park state. The
builder names the reason (`gates/test_spawn_on_pr.py`'s pre-existing
fixtures hardcode the bare-subject-key assumption throughout) --

derived: `grep -c "KEY = SUBJECT" gates/test_spawn_on_pr.py` (run from
`/tmp/pr-3106-review`) -- result: `1` (the line `KEY = SUBJECT # issue
#2628: park state is keyed by subject alone, not "subject/role"`).
derived: `python3 -m pytest gates/test_spawn_on_pr.py -q` (run from
`/tmp/pr-3106-review`, this session's own independent re-check of the
builder's compatibility claim) -- result: `27 passed`.

Judgment on whether the stated reason holds: it is a real, checkable
engineering constraint (a documented, re-derivable fixture count that
would need rewriting), not a structural impossibility manufactured to
justify skipping work -- the issue's own instruction only required "say
so in the record with the reason," which the builder's record does,
including the specific residual gap the choice leaves open and why the
issue's own acceptance checks do not exercise that gap.

derived: `grep -n "SUBJECT =" tests/test_spawn_on_pr_repo_scope.py` (run
from `/tmp/pr-3106-review`, `e0690996:tests/test_spawn_on_pr_repo_scope.py`)
-- result: one fixed `SUBJECT` constant (`"issue-3059"`) reused across
every test, never two distinct same-named-but-cross-repo subjects seeded
in the same test -- so none of the six pytest cases construct a
same-numbered subject across two repos.

This is a real trade-off (write-side protection intentionally narrower
than #3084's), not a merely-cosmetic one -- but it is disclosed, bounded,
and does not touch either property issue #3095's acceptance actually
gates. Present, with the divergence named as required.

### Broader sweep -- is there remaining orchestrator-shared state in gates/ or watchdog.py that reports per-repo without a repo key?

This was not one of issue #3095's own three acceptance checks or two
must-nots (both of which are scoped to `gates/spawn_on_pr.py`'s park
state specifically) -- it is this session's own adversarial extension,
per the spawning brief's instruction to grep for the pattern rather than
assume these two were the only instances. It does not count against PR
#3106, which stayed inside issue #3095's stated scope.

derived: `grep -rln "orchestrator_state_path" gates/ watchdog.py spawn.py`
(run from `/tmp/pr-3106-review`) -- result: 7 files (`gates/gh_delta.py`,
`gates/state_paths.py`, `gates/spawn_on_approve.py`,
`gates/board_read.py`, `gates/closure_sweep.py`, `gates/spawn_on_pr.py`,
`watchdog.py`). Every orchestrator-cross-tick-state file in the codebase
routes through this one accessor, so this grep is exhaustive for the
class of state this pattern applies to.

**Confirmed leaking (empirically reproduced, not by inspection alone):**
`gates/board_read.py`'s `board_snapshot.json` (`snapshot_path()`,
explicitly documented in that function's own docstring as
"orchestrator-scoped... `root` never determines where our own cross-tick
memory lives," same shape park state had before this fix).
`board_read(root, slug, ...)`'s steady-state delta path merges a
repo-scoped GraphQL delta into the FULL shared snapshot
(`issues = dict(snap["issues"]); prs = dict(snap["prs"])` inside
`gates/board_read.py`'s `board_read()`) and returns that merged dict as
`board["issues"]`/`board["prs"]` -- unfiltered by `slug`. A full read for
repo A populates the shared snapshot with repo A's issue/PR numbers; when
repo B's tick runs next (different `root`, different `slug`), it loads
the SAME snapshot file (the path ignores `root`/`slug` entirely) and its
delta merge starts from repo A's stale entries, keeping them in the
returned board.

derived: a targeted repro script (`gates/board_read.py`'s real
`board_read()`, `run` mocked to return canned GraphQL responses keyed by
`owner/name`, no other mocking) run from `/tmp/pr-3106-review`:
```
board A issues: {'100': {'number': 100, 'state': 'OPEN', 'title': 'repoA issue', ...}}
board B issues: {'100': {'number': 100, 'state': 'OPEN', 'title': 'repoA issue', ...}} meta_B source: delta
```
`board_read(root_B, "org/repoB", force_full=False)` returns issue #100
titled "repoA issue" -- a different repo's data, verbatim -- because the
snapshot never dropped it and the delta path only adds to what the
snapshot already had. Consumed by `watchdog._board_read()`/
`watchdog._board_pr_index()`, which routes it into branch/PR-index
decisions closure_sweep and spawn_on_pr's own logic use. This is the
same defect class as the original bug, unfixed, and outside this PR's
touched files.

derived: `git diff origin/main...HEAD --stat` (run from
`/tmp/pr-3106-review`) -- result:
```
 .../implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d.md | 220 +++++++++++++++++++++
 .../20260902T074039474451-214b4bd62dd70a4f.md      |  29 +++
 docs/specs/enforcement-boundary.md                 |   1 +
 gates/probe_parked_report_repo_leak.py             | 204 +++++++++++++++++++
 gates/spawn_on_pr.py                               |  45 ++++-
 tests/test_spawn_on_pr_repo_scope.py               | 206 +++++++++++++++++++
 6 files changed, 699 insertions(+), 6 deletions(-)
```
`gates/board_read.py` does not appear.

**By inspection, same unscoped-key shape (bare subject/PR-number/signal
key, no repo field, shared across every swept repo via
`orchestrator_state_path`), not independently re-executed against a live
two-repo runtime within this session's remaining scope, but the code
path is unambiguous from the file itself:**

- `gates/closure_sweep.py`'s `_load_out_of_index_seen`/
  `_save_out_of_index_seen` functions (`closure_sweep_out_of_index_seen.json`)
  -- a bare `set[str]` of subject names already reported out-of-index
  once. A subject already flagged for repo A silently suppresses repo
  B's own genuine first-time out-of-index report for a same-named
  subject (`if subject not in out_of_index_seen`).
  derived: `grep -n 'def _load_out_of_index_seen\|def _save_out_of_index_seen\|if subject not in out_of_index_seen' gates/closure_sweep.py`
  (run from `/tmp/pr-3106-review`) -- result: 3 matches, no `repo`
  parameter used in the key anywhere in those three lines.
- `gates/closure_sweep.py`'s `load_backoff_state`/`recheck_backoff`
  functions (`gh_quota_backoff.json`, "recheck" namespace) -- keyed by
  bare subject via `recheck_backoff(state, key, changed)`. This is not a
  peripheral file: it feeds directly into the exact
  `spawn_missing_for_pr()` flow PR #3106 just fixed
  (`closure_sweep.recheck_backoff(backoff_state, subject, False)` inside
  `gates/spawn_on_pr.py`) -- a subject's recheck-pacing state can still
  cross repos even though its park-state entry now cannot.
  derived: `grep -n 'def recheck_backoff\|closure_sweep.recheck_backoff' gates/closure_sweep.py gates/spawn_on_pr.py`
  (run from `/tmp/pr-3106-review`) -- result: 2 matches, confirming both
  the definition (subject-keyed, no repo parameter) and the call site
  inside the fixed function.
- `gates/spawn_on_approve.py`'s `load_attempted`/`_save_attempted`
  functions (`spawn_on_approve_attempted.json`) -- bare
  subject-keyed dict, no repo field.
  derived: `grep -n 'def load_attempted\|def _save_attempted' gates/spawn_on_approve.py`
  (run from `/tmp/pr-3106-review`) -- result: 2 matches, neither
  signature takes or uses a repo/slug argument in the key.
- `watchdog.py`'s `_watchdog_note_gh_failure`/`_watchdog_note_unmappable_pr`/
  `_watchdog_note_unmappable_subject_branch` functions
  (`watchdog_noise_state.json`) -- three sub-namespaces
  (`gh_failure_streaks` keyed by signal name, `unmappable_prs_reported`
  keyed by bare `str(pr_number)`, `unmappable_subject_branch_reported`
  keyed by bare subject), all one-shot/streak markers shared across
  every repo without a repo dimension. PR numbers, like issue numbers,
  are repo-local -- the same collision risk the issue's own SUBJECT
  choice (`issue-3059`) names.
  derived: `grep -n 'gh_failure_streaks\|unmappable_prs_reported\|unmappable_subject_branch_reported' watchdog.py`
  (run from `/tmp/pr-3106-review`) -- result: 6 matches across the three
  functions, none keyed with a repo/slug component.

**Not leaking, confirmed correctly scoped:**

- `watchdog.py`'s `requirement_drift_cache.json` -- fixed by PR #3084
  (`_drift_cache_key`), confirmed above under "Mechanism reuse."
- `gates/spawn_on_pr.py`'s `spawn_on_pr_parked.json` -- fixed by PR
  #3106, this review's subject (confirmed Present above).
- `gates/closure_sweep.py`'s accumulation-trend state
  (`_accumulation_repo_key(root)`) -- already repo-keyed; its own
  docstring documents this as a previously-fixed instance of the
  identical bug (self-described: "이전엔 파일 하나에 레포 구분 없이 최신
  카운트 하나만 얹혀서... delta 는 반드시 같은 레포의 직전 항목하고만
  비교한다"). derived: `grep -n "_accumulation_repo_key" gates/closure_sweep.py`
  (run from `/tmp/pr-3106-review`) -- result: matches confirming
  `repo_key = _accumulation_repo_key(root)` gates every read/write.
- `gates/gh_delta.py`'s cursor -- the returned `items` are always freshly
  fetched per-`slug` from `gh api repos/{slug}/issues` each call (no
  stale cross-repo item is ever merged into the return value); only the
  cursor `since`/`etag` timestamp is shared across repos, a milder drift
  risk (a wrong `since` lower bound), not a content leak in the same
  sense as the other instances above -- noted, not counted as a primary
  instance.
- `gates/closure_sweep.py`'s board-sweep-queue state -- a queue of
  generic category name strings (`"spawn-on-pr"`, `"closure-sweep"`,
  etc.), not per-subject/per-repo content; low risk, not pursued
  further.

**Answer to the sweep question: not a clean sweep.** At least one
instance (`gates/board_read.py`) is confirmed leaking by direct
reproduction against the real entrypoint (quoted above), and at least
four more share the identical unscoped-bare-key shape by direct code
citation with line-level `grep` confirmation (quoted above). Logged
under "Open findings" below as follow-up scope, not a defect in PR
#3106.

### Test depth audit -- `e0690996:tests/test_spawn_on_pr_repo_scope.py` and the probe

derived: `wc -l tests/test_spawn_on_pr_repo_scope.py` (run from
`/tmp/pr-3106-review`, `e0690996:tests/test_spawn_on_pr_repo_scope.py`)
-- result: `206`.
derived: `grep -c "^    def test_" tests/test_spawn_on_pr_repo_scope.py`
(run from `/tmp/pr-3106-review`,
`e0690996:tests/test_spawn_on_pr_repo_scope.py`) -- result: `6`.
Enumerated by name via the same grep with `-n`:
1. `TestParkedReportFiltersByRepo::test_parked_report_includes_own_repo`
2. `TestParkedReportFiltersByRepo::test_parked_report_excludes_other_repo`
3. `TestParkedReportFiltersByRepo::test_parked_report_not_identical_across_repos`
4. `TestRetentionRepoScoped::test_retention_when_repo_matches`
5. `TestRetentionRepoScoped::test_no_retention_when_entry_is_another_repos`
6. `TestLegacyEntries::test_legacy_entry_without_repo_key_excluded_from_resolvable_repo`

- Test 1: GA -- asserts `parked_report(root_a) == [SUBJECT]`, a specific
  falsifiable value.
- Test 2: GA -- asserts `parked_report(root_b) == []` after seeding only
  repo A's entry -- would fail if the pre-fix code (return every
  `parked=True` entry) ran.
- Test 3: GA, the strongest in the file -- asserts both repos' outputs
  are each correct AND `out_a != out_b`, directly implementing the
  "identical output is the tightest available signal" rationale issue
  #3081's comment established and this issue's own acceptance check 2
  reuses.
- Test 4: GA -- drives the real `spawn_missing_for_pr()` entrypoint
  (only gh/git/spawn I/O boundaries mocked, per the fixture's `_wire()`
  helper; the park/repo-attribution logic itself is not mocked) and
  asserts `pairs == []`, `state[SUBJECT]["parked"] is True`,
  `state[SUBJECT]["repo"] == REPO_A`, and the report -- four independent
  falsifiable checks on one call.
- Test 5: GA -- the eviction case: seeds a foreign-repo entry with
  `"attempts": 5`, asserts `pairs != []` (spawned, not parked), asserts
  `state[SUBJECT]["attempts"] == 1` (restarted, not inherited from the
  foreign 5), and asserts the report does not phantom-park it. This is
  the one test that would fail hardest against a reimplementation that
  merely filtered read-time output without also evicting write-time
  retention -- confirms the eviction branch is exercised, not just
  present in source.
- Test 6: GA -- legacy no-`repo`-key entries excluded from a resolvable
  repo's report, covering the `entry.get("repo") == repo_slug` comparison
  against `None`.

Mocking covers only the external I/O boundary (gh/git/spawn calls); the
park-state read/write/filter/evict logic under test runs for real in
every one of the six -- 0 Mock-Dominated. All six carry a specific,
falsifiable assertion -- 0 Execution-Only, 0 Dead. Not Happy-Path-Only as
a suite: tests 5 and 6 are explicitly negative/edge cases (foreign-repo
eviction, unattributed legacy entry).

derived: `6 / 6 = 100%` verification density (matches the `6 passed`
result quoted under "Required acceptance check 1" above one-for-one).

The standalone probe (`e0690996:gates/probe_parked_report_repo_leak.py`)
independently exercises the same four properties end-to-end through two
real ticks (park, then a second tick with a foreign-repo entry
substituted) rather than per-property pytest cases, and is itself the
sensitivity-control instrument verified above -- also fully GA, no
assertion that could pass vacuously (each `_fail()` branch checks a
specific list/dict value against the real function's output).

Gap this suite does not cover, matching the divergence named above: no
case constructs two repos' entries under the *same* key simultaneously
to exercise the write-time collision the bare-subject-key choice leaves
open -- consistent with the builder's own record naming this same gap.

## Why

derived: `python3 gates/probe_parked_report_repo_leak.py` -- result
`FAIL: ...` exit 1 on `/tmp/otr-main-verify` (unmodified main) vs. `ok`
exit 0 on `/tmp/pr-3106-review` (PR #3106's branch), same file, both runs
this session's own, quoted in full under "Must-not 2" above.

The task asked specifically to compare against the sibling fix (PR
#3084) rather than treat the required checks as the whole story, to
independently re-run the sensitivity control rather than rely on a
description of it, and to check whether this two-instance pattern (drift
cache, park state) is closed everywhere in `gates/`/`watchdog.py` or just
in those two files. The mechanism comparison was made by reading both
diffs and confirming the shared attribution primitive (`_repo_slug`) via
`grep`, not by reading the PR description's own characterization of
itself (quoted under "Mechanism reuse" above). The sensitivity control
was re-run from a fresh worktree of unmodified main with the exact probe
file copied over unchanged, not re-derived from scratch, which could
accidentally construct a different probe (quoted directly above and
under "Must-not 2"). The sweep was pursued to an actual working repro of
`gates/board_read.py` rather than stopping at this session's own
required-check re-runs (quoted under "Required acceptance check" above,
each individually) -- the repro is quoted in full under "Broader sweep"
above.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 3095 --repo tokenmaxxxer/on-the-record
--comments` (2 comments read in full).
canonical: `gh pr view 3106 --repo tokenmaxxxer/on-the-record` and its
diff (read in full across `gates/spawn_on_pr.py`,
`e0690996:gates/probe_parked_report_repo_leak.py`,
`e0690996:tests/test_spawn_on_pr_repo_scope.py`,
`docs/specs/enforcement-boundary.md`, the builder's own record and
deviation-log entry, both at `e0690996`).
canonical: `git show e5172b24 -- watchdog.py` (PR #3084's full diff) --
the sibling mechanism this session compared PR #3106 against.

`gates/spawn_on_pr.py`, `e0690996:gates/probe_parked_report_repo_leak.py`,
`e0690996:tests/test_spawn_on_pr_repo_scope.py` at PR #3106's branch head
`e06909962b58130aa889b8c15561ade355bf89f3`, and `origin/main` at
`7ee166122719b8b4f3bcde72d9a5c73885aaceee` (current main, includes PR
#3089) -- both read directly via linked git worktrees
(`/tmp/pr-3106-review`, `/tmp/otr-main-verify`), not the PR's rendered
diff alone.

## Open findings

1. canonical: this session's own `board_read()` repro and
   `git diff origin/main...HEAD --stat` output, both quoted under
   "Broader sweep" above. `gates/board_read.py`'s `board_snapshot.json`
   leaks across repos the identical way requirement-drift's cache and
   spawn-on-pr's park state both did: a repo B call returns a repo A
   issue verbatim after repo A's full read populated the shared,
   unfiltered snapshot. Consumed by `watchdog._board_read()`/
   `watchdog._board_pr_index()`, which feeds branch/PR matching
   decisions in closure_sweep and spawn_on_pr. Not touched by PR #3106
   and outside issue #3095's stated scope (which named
   `gates/spawn_on_pr.py`'s park state specifically) -- flagged as a new
   instance of the same defect class for a follow-up issue, using the
   same repo-attribution mechanism (`spawn._repo_slug`) both #3084 and
   #3106 already established.
2. canonical: this session's own `grep` citations for each file, quoted
   under "Broader sweep" above. Four further orchestrator-shared state
   files carry the identical unscoped-bare-key shape by code inspection
   (not independently re-executed against a live two-repo runtime this
   session): `gates/closure_sweep.py`'s out-of-index-seen state and
   `gh_quota_backoff.json`'s "recheck" namespace (the latter feeding
   directly into `spawn_missing_for_pr()`, the very function PR #3106
   touched), `gates/spawn_on_approve.py`'s attempted-state, and
   `watchdog.py`'s noise-state (three sub-namespaces). Resolution path:
   each would need the same fix shape PR #3106 applied (or PR #3084's
   compound-key shape) plus a dedicated probe per file, the same way
   issue #3095 did for park state after #3084 covered drift. Recommend a
   single follow-up issue enumerating all five remaining instances (this
   list plus `board_read.py` above) rather than one issue per file, so
   the fix is designed once against the whole class instead of drifting
   apart again one file at a time -- the exact failure mode issue #3095
   itself was opened to close.
3. canonical: the builder's record's "Why" section content, read via
   `gh pr diff 3106` as part of "What was done" above. PR #3106's
   bare-subject-key choice (vs. #3084's compound key) leaves a narrower,
   disclosed gap open: a literal same-numbered subject genuinely parked
   in two different swept repos can still overwrite on write, not just
   misread. The builder's own record names this and the reason
   (pre-existing `gates/test_spawn_on_pr.py` fixture compatibility,
   confirmed via this session's own `grep -c "KEY = SUBJECT"` under
   "Mechanism reuse" above). This session judges the reason as real and
   the disclosure as adequate per the issue's own instruction ("say
   so... with the reason") -- not re-opening PR #3106 over it, but
   noting it here so a future session closing this residual gap does not
   have to rediscover it from the diff.

## Next steps

None from this session -- `loop_state: landed`. The three open findings
above are handoffs (candidate follow-up issues), not further work
planned by this record. Per instruction: PR #3106 was not edited,
approved, or merged by this session.

skill-verdict: adversarial-review — applied: invoked; ran this
verification of PR #3106 blind to the builder's session (no access to the
builder's prompt/reasoning, only `gh` reads of the issue and PR plus the
merged commits both PRs cite), and reached an independent verdict by
executing code (worktrees, a repro script, re-run tests/probes) rather
than reading either the builder's or the parallel verification session's
claims as settled.
skill-verdict: test-depth-audit — applied: invoked; classified every test
in `e0690996:tests/test_spawn_on_pr_repo_scope.py` and the standalone
probe per the "Test depth audit" section above (derived: 6 GA / 6 total =
100% verification density).
skill-verdict: experiment-trust — not-applicable: this task is a
code-defect verification against a GitHub issue's acceptance criteria,
not an A/B/variant experiment comparison; no experimentation platform,
sample ratio, or randomized assignment is involved anywhere in this
deliverable.
skill-verdict: work-in-english — applied: invoked; this record, all
commands, and all quoted code are in English.
other mounted skills (implementation-audit,
conformance-review-finding-record,
defect-verification-independence-from-upstream-verdicts, merge-gates,
parallel-decomposition): not triggered -- this record's target file is
this session's own role record (an adversarial-review-shaped
defect-verification record), not a
`docs/issue-<n>/reports/conformance-review.md` file, and this session did
neither multi-agent build fan-out nor a merge decision, so those skills'
own named triggers did not fire.
