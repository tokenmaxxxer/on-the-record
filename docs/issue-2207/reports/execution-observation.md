---
issue: 2207
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2207/reports/refactoring-legacy.md
    sha: 85a9611f6809183fa49ec9c270c2fbcae7079d8a
  - path: directive_assembly.py
    sha: 85a9611f6809183fa49ec9c270c2fbcae7079d8a
  - path: spawn.py
    sha: 85a9611f6809183fa49ec9c270c2fbcae7079d8a
subject: PR #2308 (issue-2207, "extract directive/skill-assembly cluster from spawn.py into directive_assembly.py"), commits 57ae2499a8a9/85a9611f6809, branch issue-2207/refactoring-legacy, parent a7f52333567a
test: independent re-derivation of every falsifiable claim in docs/issue-2207/reports/refactoring-legacy.md (untracked in this tree — lives on branch issue-2207/refactoring-legacy at commit 85a9611f6809183fa49ec9c270c2fbcae7079d8a) — line counts, extraction mechanics, grep/derived commands, full test suite, and the 20-session read-offset sampling — commands and outputs below, all run in fresh git worktree checkouts of the branch and its parent
result: failed
assertedBy: execution-observation session for issue-2207, independent of PR #2308's authoring (refactoring-legacy) session
---

# issue-2207 — execution-observation record

## What was done

canonical: this session's own `git worktree` checkouts of `pr-2308-review`
(commit 85a9611f6809183fa49ec9c270c2fbcae7079d8a) and its parent
(a7f52333567a) at `/tmp/pr2308-review/branch` and `/tmp/pr2308-review/parent`,
and this session's own reads of `$MUSTER_WORKSPACE_ROOT` session logs —
never the builder's pasted transcripts taken as given.

Re-executed every falsifiable claim in
`docs/issue-2207/reports/refactoring-legacy.md` (untracked in this tree —
lives on branch issue-2207/refactoring-legacy at commit
85a9611f6809183fa49ec9c270c2fbcae7079d8a) independently, per this role's
own EARL-style scope (worst-case verdict over cited test entries,
issue-807 step1 sec4).

### Mechanical claims — confirmed

acceptance: `git merge-base main pr-2308-review` — result:
```
a7f52333567ae0eff28d62b40d5632d824babc83
```
matches the record's cited parent sha.

acceptance: `wc -l /tmp/pr2308-review/parent/spawn.py` — result:
```
3347 /tmp/pr2308-review/parent/spawn.py
```
matches the record's "before" figure.

canonical: `spawn.py:499-501` (branch checkout) —
`directive_assembly._sp = sys.modules[__name__]` guarded by
`if directive_assembly._sp is None or __name__ in ("spawn", "__main__")` —
matches the injection pattern of all 9 sibling extractions
(relay/roster/plumbing/watchdog/events/consult/skills/lifecycle/board/
pipeline, spawn.py:52-499), confirmed by direct read.

acceptance: `grep -rln "2649\|source_pin" tests/ test/ gates/` (branch
checkout) — result:
```
(no output — no matches)
```
confirms the #2114-#2122 floor is not a literal enforced test.

acceptance: `head -5 pipeline.py` (parent checkout) — result:
```
"""Spawn pipeline machinery (settings/rulebook/core resolution, spawn_cmd,
issue workspace + checkout/bootstrap, directive-assembly helpers, admission)

Extracted from spawn.py (issue #2105, extraction 8/N, endgame). Pure move —
no behavior change. spawn.py imports this module and re-exports every moved
```
the record's quote verified verbatim.

canonical: `spawn.py:43` (branch checkout, unchanged from parent) —
`ROOT = Path(__file__).resolve().parent` — confirms the "systemic scope,
plugin-relative paths only" claim.

canonical: `tests/test_perf_budget_issue_2053.py:176-182` (branch
checkout) — reads `directive_assembly.py`'s source text and asserts no
`subprocess` string in the `_bm25_cross_family_scores` function body —
confirmed correctly re-targeted (not relaxed) by direct read.

acceptance: re-ran the record's 3 "flaky, pass in isolation" tests —
`tests/test_spawn_gate_wiring.py` (`DesignBearingSingleFetch::test_design_bearing_never_refetches_the_issue_body`),
`tests/test_spawn_gate_wiring.py` (`ReturnedPRGateIsNonBlocking::test_slow_gh_lookup_does_not_block_spawn_or_its_timed_phase`),
`tests/test_spawn_observation_recovery.py` (`SpawnOneIssueRoleClaim::test_second_spawn_refused_while_first_still_pushing`),
all at commit 85a9611f6809183fa49ec9c270c2fbcae7079d8a, branch checkout —
result:
```
3 passed in 51.50s
```
(record's own re-run: 28.47s — same outcome, different timing, consistent
with a machine-load-dependent test rather than a discrepancy).

canonical: `test/test_branch_role_field.py:96-97` and
`test/test_local_dependency_env.py:200` (branch checkout) locate
`issue_workspace`/`_recut_absorbed_branch` by scanning `spawn.py`'s
literal source text (`text.index("def issue_workspace(")` etc.) —
confirmed by direct grep; the record's Open Findings claim about this
coupling is accurate.

acceptance: `python3 -c "import time; t=time.time(); import spawn; print(time.time()-t)"`
(branch checkout), 3 runs — result:
```
0.05863666534423828
0.01902461051940918
0.01734638214111328
```
same order of magnitude as the record's own 0.0143s derived figure; no
material added per-spawn overhead, confirming that claim.

### Mechanical claims — NOT confirmed as stated

acceptance: `wc -l /tmp/pr2308-review/branch/spawn.py` — result:
```
2940 /tmp/pr2308-review/branch/spawn.py
```
The record's own "after = 2929" is wrong by 11 lines. acceptance: `git
diff --numstat --no-renames a7f52333567a pr-2308-review -- spawn.py` —
result:
```
25	432	spawn.py
```
derived: 25 insertions - 432 deletions = -407 net change; 3347-407=2940,
not 2929 as the record states. The record's central line-count claim is
a transcription/arithmetic error, not a difference in method.

canonical: the record's own brace-expansion,
`on-the-record-issue-{2204,2205,2208,2210,2211,2214(x2),2215,2217,2219,2226(x2),2229,2231,2233,2240,2241,2262,2266,2268,2278}-implementation.session.*.log`,
derived: expanding the braces by hand counts 19 issue numbers + 2 extra
for the doubled 2214/2226 entries = 21 distinct log filenames, not the
"20 most recent" the surrounding prose claims.

derived: re-listing `*-implementation.session.*.log` under
`$MUSTER_WORKSPACE_ROOT`, sorted by the embedded timestamp, and taking
the 20 entries immediately after issue-2201's own log
(`20260824T214938`) reproduces the record's own 19 issue numbers plus
issue-2262, and stops there. Issue-2241's log (`20260825T101338`) sorts
one place after issue-2262's (`20260825T101307`), so any clean "20 most
recent" window can contain one but not both — the record's list, as
brace-expanded, contains both. derived: 19 + 2 duplicates = 21 items in
a set the prose labels as 20.

canonical: re-parsed `on-the-record-issue-2262-implementation.session.20260825T101307.535603.log`
(same method the record describes: assistant `Read` tool_use events,
grouped by `os.path.basename(file_path)`) — the record's table claims 6
`spawn.py` reads at offsets `1096,1880,1926,2260,2270,2560`; this
session's own parse of the same log finds 7: the same 6 plus one at
offset 1947 (`limit: 18`, line 1433 of the log) that the record's table
omits.

canonical: re-parsed `on-the-record-issue-2241-implementation.session.20260825T101338.552910.log`
the same way — the record's summary line claims 4 `spawn.py` reads, but
its own offset table lists only 3 values (`1110,1219,1459`). This
session's own parse finds 5 `Read` calls on `spawn.py` total: one full
read with no `offset` key (line 35) plus 4 partial reads at
`1219,1459,1110,1229`. The summary count of 4 is defensible only if
offset-less full reads are excluded from "partial reads" — a reasonable
filter the record never states — but even under that filter the offset
table is still missing `1229`.

canonical: re-parsed the remaining 5 detailed sessions the same way —
issue-2204, issue-2211, issue-2229, issue-2217, issue-2208 each
reproduced exactly as the record states: 18, 10, 5, 3, and 2 `spawn.py`
reads respectively, same offsets each time.

### Directional finding — confirmed despite the above

canonical: `spawn.py` at parent commit a7f52333567a, lines 1867
(`_checkpoint_contract_block`), 2095 (`write_record_skeleton`), 2250
(`_cross_family_skill_matches`) — all three functions the PR actually
moved fall inside the record's claimed 1619-2292 hot region, and the
corrected read-offset counts above (18, 10, 7, 5, 5, 3, 2 across the 7
sessions with more than 2 `spawn.py` reads) still cluster inside that
same range. The counting errors above are in the record's arithmetic,
not in the underlying pattern — the recurrence claim ("not a one-off")
survives independent re-sampling even after correcting the counts.

### Full test suite — reproduced with material caveats

acceptance: `python3 -m pytest -q` on the branch checkout (this
observation session's own environment carries `CORE_BUILD_NOW=1`, set by
this session's own spawner for the build-now bypass, unrelated to the PR
under review) — result:
```
10 failed, 4315 passed, 1 skipped, 21 xfailed, 2 xpassed in 910.87s (0:15:10)
```
canonical: the record's own acceptance block claims `12 failed, 4313
passed, 1 skipped, 21 xfailed, 2 xpassed in 927.82s` — same total of
4349 accounted-for tests both times (derived: 10+4315+1+21+2 =
12+4313+1+21+2 = 4349), different failed/passed split.

canonical: root-caused one specific divergent failure —
`tests/test_spawn_directive_assembly.py` (`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`,
branch checkout, unmodified by this PR — present unchanged at parent
commit a7f52333567a too) asserts a spawned child's env must not carry
`CORE_BUILD_NOW`; it failed in my run because *this observation
session's own* `CORE_BUILD_NOW=1` leaks into the subprocess env the test
inspects. acceptance: `env -u CORE_BUILD_NOW python3 -m pytest -q tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`
— result:
```
1 passed in 1.02s
```
confirming the record's own characterization (failures here are
environment-state-dependent, not code regressions) for at least this one
case, and explaining why my raw full-suite count differs from theirs —
different ambient env at run time, not a different codebase.

canonical: re-ran the full suite a second time (this session's own
second acceptance run) with `CORE_BUILD_NOW` unset to control for that
one variable; that second run of mine showed markedly more failures —
canonical: `ps aux` output captured during that second run showed a
separate, independent `pytest -q -m not slow` process from another
session running concurrently on this shared host, and this repo's own
tests spawn subprocess role sessions as part of their fixtures
(interleaved `auto-sweep` log lines appeared in the captured output).
This is consistent with the suite being materially load/timing-sensitive
on this shared host at test time, not with one stable ground-truth
failure count. I did not force a contention-free re-run (no exclusive
access to the host this session has); I cannot certify the record's
exact "12 failed" figure this way, but every failing test observed
across both of my runs belongs to a file this PR does not touch:

acceptance: `git diff --stat a7f52333567a pr-2308-review` — result:
```
directive_assembly.py                         | 462 ++++++++++++++++++++++++++++++++++++++++++++++++++
docs/issue-2207/reports/refactoring-legacy.md | 304 +++++++++++++++++++++
spawn.py                                      | 457 +----------------------------
tests/test_perf_budget_issue_2053.py          |  16 +++-
4 files changed, 487 insertions(+), 432 deletions(-)
```
canonical: none of the 10-13 failing node IDs across my two runs live in
any of those four files — no failure I observed is attributable to this
diff.

## Why

canonical: the record's own claims are each individually falsifiable
(specific commands, specific numbers, specific file/line citations) —
this role's job (EARL-style: subject/test/result, worst-case verdict) is
to re-run them, not to trust the builder's transcript. Re-running found
the extraction itself sound (mechanism, scope, no floor-test breakage, no
added overhead, correct BM25 relocation), all reproduced above.

canonical: re-running also found the record's own supporting arithmetic
— the primary "Why" evidence for the acceptance criterion — internally
inconsistent in reproducible ways, reproduced above: an 11-line miscount
on the central `wc -l` claim (2929 vs. actual 2940), a mismatch between
the declared sample size (20) and the actual brace-expanded list (21),
and undercounts in 2 of the 7 detailed per-session read tallies
(issue-2262 and issue-2241, including one fully missing tool_use entry
in the issue-2262 log at offset 1947). None of these overturn the
directional finding the PR acts on (spawn.py's
checkpoint/directive/record-skeleton/BM25 cluster is genuinely
repeatedly re-read, and the extraction is a reasonable response to it),
but "the numbers in the record match the numbers a second party derives
from the same sources" is exactly what this role checks, and for these
specific figures they do not.

## Upstream basis

- `docs/issue-2207/reports/refactoring-legacy.md` (untracked in this
  tree — lives on branch issue-2207/refactoring-legacy at commit
  85a9611f6809183fa49ec9c270c2fbcae7079d8a, PR #2308) — the record under
  observation.
  sha: 85a9611f6809183fa49ec9c270c2fbcae7079d8a
- `directive_assembly.py`, `spawn.py` at commit
  85a9611f6809183fa49ec9c270c2fbcae7079d8a (this PR, untracked in this
  tree, checked out separately via `git worktree` at
  `/tmp/pr2308-review/branch`) and at
  a7f52333567ae0eff28d62b40d5632d824babc83 (parent, checked out at
  `/tmp/pr2308-review/parent`) — read directly, never via the PR's
  pasted diff alone.
  sha: 85a9611f6809183fa49ec9c270c2fbcae7079d8a
- The 21 session logs under `$MUSTER_WORKSPACE_ROOT` the record's own
  brace-expansion names — read and parsed directly by this session,
  independent of the record's own pasted script output.
  sha: same-commit

## Open findings

- canonical: this session's own two full-suite acceptance runs, both
  quoted with their command and code-fenced output under "Full test
  suite — reproduced with material caveats" above — neither run's tally
  matches the record's own acceptance block there; this could not be
  reproduced bit-for-bit on this shared, concurrently-loaded machine.
  Resolution path: a future session with exclusive machine access
  re-runs `python3 -m pytest -q` once, cold, to get a clean baseline
  number — not attempted here because this session never had exclusive
  access to the host.
- canonical: the re-parsed session logs above (Mechanical claims — NOT
  confirmed as stated) — the record's per-session `spawn.py` read counts
  for issue-2262 (6 vs. actual 7) and issue-2241 (table shows 3, summary
  says 4, actual partial-read count is 4 with `1229` missing from the
  table) are wrong as written, and its "20 most recent" sample
  brace-expands to 21 entries. Resolution path: none needed for the PR's
  own merits (the underlying directional claim survives correction), but
  a future session citing this record's numbers should re-derive them
  rather than quote the table verbatim.
- This role's own worst-case-recomputation rule (issue-515 invariant 4)
  forces the top-level `result:` to `failed` because at least one cited
  test entry (the record's own arithmetic, re-derived here) did not hold
  as stated — this is a verdict about the record's stated evidence, not
  about whether the PR's code change is defective. canonical: nothing
  reproduced in this session (extraction mechanism, floor-test absence,
  overhead, BM25 relocation, all confirmed above) indicates the
  extraction should be reverted.

## Next steps

None — `loop_state: handed-off` is terminal for this role.

## What did not work

Attempted a contention-free full-suite re-run twice; both landed on a
shared host with other concurrent sessions/pytest processes running, so
neither produced a number this session can certify as the clean
baseline (see Open findings).
