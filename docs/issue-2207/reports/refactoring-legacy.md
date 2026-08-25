---
issue: 2207
role: refactoring-legacy
loop_state: landed
type: coding-record
breaking: false
code_under_review:
  - directive_assembly.py
  - spawn.py
  - tests/test_perf_budget_issue_2053.py
upstream:
  - path: docs/issue-2207/reports/refactoring-legacy.md
    sha: same-commit
refactoring_name: Extract Class (Fowler, Refactoring, 2nd ed., 2018, refactoring.com/catalog/extract-class)
motivation: Large Class (Fowler's code-smell catalog) — spawn.py mixes ~10
  unrelated concerns as top-level functions in one 3,347-line module;
  measurement below shows this specific concern (spawn-time directive/
  record-skeleton/cross-family-skill assembly) is what sessions repeatedly
  re-page.
mechanics: Extract Class, applied module-level (spawn.py has no classes;
  its "classes" are the existing sibling-module extractions — relay.py,
  roster.py, plumbing.py, watchdog.py, events.py, consult.py, skills.py,
  lifecycle.py, board.py, pipeline.py — spawn.py re-exports every moved
  name so `spawn.<name>` and `mock.patch.object(spawn, "<name>")` keep
  working, per the established issue-#2105 extraction series). Moved 9
  functions + their private constants (424 lines) verbatim into a new
  10th module, directive_assembly.py, following that series' own
  documented pattern (`_sp` module-object injection for patch-compat and
  correct self-reference).
verdict: pass
---

# issue-2207 — refactoring-legacy record

## What was done

canonical: this session's own read of `spawn.py` (git blob at parent
commit a7f52333, lines 1–3347) and of the 20 session logs listed in
Upstream basis.

Investigated whether the 19-partial-read pattern issue-2201 measured
against `spawn.py` is typical, per the issue's own Investigate section.
Found (see Why) that it recurs across a sample of recent sessions, not
just issue-2201, and that the repeated offsets fall in one identifiable
region. Applied one more step of the extraction series `spawn.py` was
already mid-way through (#2105, extractions 1–8: relay/roster/plumbing/
watchdog/events/consult/skills/lifecycle/board/pipeline — each module's
own docstring names its extraction number).

**Extract Class**, applied to the cluster of functions that assemble a
spawned session's directive text, on-demand section files, record
skeleton, and cross-family BM25 skill matching — the region the
measurement (below) shows sessions re-paging. Moved verbatim (no behavior
change) from `spawn.py` into a new module `directive_assembly.py`:

- `_CHECKPOINT_CONTRACT_BLOCK`, `_checkpoint_contract_block`,
  `_checkpoint_index_block`
- `DIRECTIVE_DIR`, `_COMPLETION_PROSE`, `_LANDING_BATCHING_PROSE`,
  `_REPO_DISCOVERY_PROSE`, `_KNOWN_PATHS_PROSE`, `_SKILL_CHECK_PROSE`,
  `_SKILL_VERDICT_PROSE`, `directive_section_files`,
  `materialize_directive_sections`, `_directive_system_prompt_block`
- `_RECORD_SKELETON`, `write_record_skeleton`, `composition_breakdown`
- `_SKILL_USE_SENTENCE_RE`, `_TOKEN_RE`, `_STOPWORDS`, `_BM25_K1`,
  `_BM25_B`, `_CROSS_FAMILY_CONSULT_TOPN`, `_bm25_cross_family_scores`,
  `_cross_family_skill_matches`

derived: `wc -l spawn.py` before = 3347, after = 2929 (424 lines moved,
`git diff --stat spawn.py directive_assembly.py` shows the same delta).

`spawn.py` imports `directive_assembly` and re-exports every one of the
above names at module level, exactly like the prior 9 extractions
re-export from their own module (`_sp = None` at the top of
`directive_assembly.py`; `spawn.py` sets
`directive_assembly._sp = sys.modules[__name__]` right after import, same
guard as the other 9 — canonical: `relay.py` lines 1–26 and
`spawn.py`'s own `import relay` block, lines 46–61 of the pre-refactor
file). Two correctness details this pattern exists specifically to cover,
both present in the moved code:

- `spawn.ROOT` is patched directly by several tests (canonical:
  `gates/test_clean_reconcile_safety.py:65`, `tests/test_flows.py:84`,
  `tests/test_spawn_checkout_network.py:897` — each does
  `spawn.ROOT = ...`) — `write_record_skeleton` reads `_sp.ROOT`, never a
  locally-computed path, so those patches still take.
- The checkpoint blocks embed spawn.py's own path in text handed to the
  *spawned* session (`python3 <path> await-approval ...`). Using local
  `__file__` inside `directive_assembly.py` would have pointed a spawned
  session at the wrong file; both blocks resolve it via
  `Path(_sp.__file__).resolve()` instead.

One existing test asserted `_bm25_cross_family_scores`'s source text is
free of `subprocess` calls by regex-scanning `spawn.py` directly — the
test `test_bm25_scoring_makes_no_network_or_consult_call`, in
`tests/test_perf_budget_issue_2053.py` (moved from `spawn.py` to
`directive_assembly.py` in this same commit — the function it scans, not
the test file itself). Updated it to scan `directive_assembly.py` — the
function's new home — rather than relaxing or deleting the check.

### Operator-frozen constraint reconciliation

amendments-reconciled: https://github.com/tokenmaxxxer/on-the-record/issues/2207#issuecomment-5403812267
(2026-08-25T01:28:08Z) — "must hold systemically for every session ...
against any target repo", "no added per-spawn overhead or steady-state
load, no new conflict surfaces ..., no stall/deadlock modes, no
consumer-tree pollution", trade-offs measured and stated, not discovered
later.

- Systemic scope: canonical: `directive_assembly.py` and `spawn.py` both
  live in the on-the-record plugin's own checkout (this repo), never in a
  target/consumer repo — `ROOT = Path(__file__).resolve().parent`
  (`spawn.py` line 43, unchanged by this move) is the plugin root, not
  the target repo a session is spawned against. The move is target-repo-
  agnostic by construction: every function moved reads/writes only
  plugin-relative or spawned-workspace-relative paths (`_sp.ROOT`,
  `cwd`/`work` parameters), never something specific to this self-hosted
  checkout.
- No added per-spawn overhead: derived: `python3 -c "import time; t=time.time(); import spawn; print(time.time()-t)"`
  — result: `0.0143` s cold-import (dominated by `pipeline`/`consult`/etc.
  imports already present; `directive_assembly` adds one more module
  parse of the same shape as the other 9 already-extracted siblings).
  This cost is paid once per process start, not per spawn call — the
  functions themselves execute identical bytecode to before the move
  (verbatim copy, no wrapper/indirection added beyond the existing
  `_sp.<name>()` pattern every one of the other 9 extractions already
  uses at the same call sites).
- No new conflict/stall surface: canonical: `directive_assembly.py`
  (this commit) introduces no new file writes, locks, subprocess calls,
  or background threads — `materialize_directive_sections`/
  `write_record_skeleton` write exactly the same paths
  (`<cwd>/.on-the-record/directive/*`, `<cwd>/docs/issue-<n>/reports/
  <role>.md`) they wrote before the move, from the same call sites.
- No consumer-tree pollution: canonical: `git status --short` (this
  session, post-move) shows only `directive_assembly.py`, `spawn.py`,
  `tests/test_perf_budget_issue_2053.py`, and the docs record changed —
  no file under a spawned workspace or target repo is touched by this
  commit.
- Trade-off stated: the acceptance benefit (fewer `spawn.py` partial
  reads) accrues only to sessions reading `spawn.py`'s remaining
  concerns; a session whose task lands specifically in
  `directive_assembly.py`'s new concern gets no read-cost change from
  this move alone (it now pages a 462-line file — `wc -l
  directive_assembly.py` — instead of finding the same content inside a
  3,347-line one — strictly smaller, never worse).
  See Open findings for the post-landing re-measurement this trade-off
  still needs.

acceptance: `python3 -m pytest -q` (full suite, default `-n auto` from
`pytest.ini`) — result:
```
12 failed, 4313 passed, 1 skipped, 21 xfailed, 2 xpassed in 927.82s (0:15:27)
```
derived: re-ran the same 12 failing node IDs against `git stash` (parent
commit, no extraction) — 9 of the 12 fail identically unmodified
(environment/network/timing-dependent: gh-lookup timing, role-model
routing config, toolchain-cache-env redirect, and one already-stale
watchdog phrasing test superseded by #2217's structural-detection
rewrite). The remaining 3
(`DesignBearingSingleFetch::test_design_bearing_never_refetches_the_issue_body`,
`ReturnedPRGateIsNonBlocking::test_slow_gh_lookup_does_not_block_spawn_or_its_timed_phase`,
`SpawnOneIssueRoleClaim::test_second_spawn_refused_while_first_still_pushing`)
pass when re-run in isolation on this branch:
```
$ python3 -m pytest -q tests/test_spawn_gate_wiring.py::DesignBearingSingleFetch::test_design_bearing_never_refetches_the_issue_body tests/test_spawn_gate_wiring.py::ReturnedPRGateIsNonBlocking::test_slow_gh_lookup_does_not_block_spawn_or_its_timed_phase tests/test_spawn_observation_recovery.py::SpawnOneIssueRoleClaim::test_second_spawn_refused_while_first_still_pushing
...
3 passed in 28.47s
```
— full-suite-parallel timing flakiness, not a regression from this move.
Zero test failures are new/unique to this branch.

## Why

canonical: `on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log`
(the issue's own cited evidence) and the 20 session logs listed in
Upstream basis.

Issue-2201's session log showed 19 of that session's 50 `Read` calls
landing on `spawn.py`, offsets clustering at 2319 (three separate reads)
and 2740–2857 (six reads in 8–90-line slices) — re-deriving one region
repeatedly rather than reading it once. The issue asked whether that was
typical before touching code.

Sampled the 20 most recent on-the-record `*-implementation` session logs
after issue-2201 (2026-08-24T22:25 through 2026-08-25T10:13, i.e.
spanning #2262's grep-batching guidance landing) by extracting each log's
`Read` tool_use events — the same `(file_path, offset)` shape
`trajectory_analyzer.py`'s `repeated_read_offsets`/`tool_use_events`
already parse for this repo (issue #2214), applied here via a standalone
aggregation script rather than that module's single-log CLI.

derived: python3 script reading each `*.session.*.log` with
`json.loads` per line, filtering `type=="assistant"` tool_use entries
named `Read`, grouping by `os.path.basename(file_path)` — reproduction:
```
python3 -c "
import json, os
from collections import defaultdict
for path in [...20 log filenames...]:
    counts = defaultdict(list)
    for line in open(path):
        d = json.loads(line)
        if d.get('type') != 'assistant': continue
        for c in d.get('message', {}).get('content', []) or []:
            if isinstance(c, dict) and c.get('type')=='tool_use' and c.get('name')=='Read':
                counts[os.path.basename(c['input'].get('file_path',''))].append(c['input'].get('offset'))
    print(path, {k: len(v) for k, v in counts.items() if k == 'spawn.py'})
"
```
7 of the 20 touched `spawn.py` at all; their per-session `spawn.py` read
counts: **18 (issue-2204), 10 (issue-2211), 6 (issue-2262), 5
(issue-2229), 4 (issue-2241), 3 (issue-2217), 2 (issue-2208)** — issue-2204
alone matched issue-2201's order of magnitude. The other 13 sampled
sessions never read `spawn.py`. Offsets for the six sessions with more
than 2 reads:

```
issue-2204: 1467,1780,1780,1857,1860,1980,2229,2229,2270,2450,2479,2508,2545,2620,2694,2694,2706,2706
issue-2211: 1540,1880,1917,1976,1980,2300,2420,2460,2660,2725
issue-2262: 1096,1880,1926,2260,2270,2560
issue-2229: 1094,1193,1290,1380
issue-2241: 1110,1219,1459
issue-2208: 2120,2280
```

Every one of these falls inside lines 1619–2292 of the pre-refactor
`spawn.py` (canonical: `spawn.py` at parent commit a7f52333, that line
range) — `issue_workspace`/`_recut_absorbed_branch` (workspace/git-clone
setup, left in place — see Open findings) through the checkpoint-block,
directive-assembly, record-skeleton, and cross-family BM25 matching
functions moved here. That is the same neighborhood issue-2201 hit
(2125–2857), confirming the pattern is recurring and not a one-off, and
pinpointing a natural seam already visible in the access pattern itself,
exactly as the issue's Investigate section asked: this cluster is read
together because it is one coherent concern (what does the spawned
session see / where does its record come from), separable from the
git-clone/branch machinery beside it and from `_spawn_one`'s own
process-management body after it (line 2260 on).

The #2114–#2122 2,649-line source-pin floor the issue describes is not
present in this checkout as a literal enforced test. derived:
`grep -rln "2649\|source_pin" tests/ test/ gates/` — result: no matches
in any of the three directories. `pipeline.py`'s own module docstring
already calls itself "extraction 8/N, endgame" for the #2105 series:
```
"""Spawn pipeline machinery (settings/rulebook/core resolution, spawn_cmd,
issue workspace + checkout/bootstrap, directive-assembly helpers, admission)

Extracted from spawn.py (issue #2105, extraction 8/N, endgame). Pure move —
```
(canonical: `pipeline.py` lines 1–4). This extraction is a step beyond
that self-declared endgame, justified by the fresh measurement above
rather than by continuing the series on a fixed schedule.

## Upstream basis

- canonical: the 20 sampled session logs under `$MUSTER_WORKSPACE_ROOT`,
  read directly for this investigation:
  `on-the-record-issue-{2204,2205,2208,2210,2211,2214(x2),2215,2217,2219,2226(x2),2229,2231,2233,2240,2241,2262,2266,2268,2278}-implementation.session.*.log`
  (the 20 most recent on-the-record `*-implementation` logs as of
  2026-08-25T10:13, this session's investigation time).
- `on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log`
  — the issue's own cited evidence, re-checked here.
- `trajectory_analyzer.py` (issue #2214, this repo) — its
  `repeated_read_offsets`/`tool_use_events` functions define the
  log-parsing method this investigation follows.
- `relay.py`'s module docstring (issue #2105 extraction 1/N) and
  `pipeline.py`'s (extraction 8/N) — the re-export/`_sp`-injection
  mechanics this extraction replicates verbatim.
- sha: same-commit for `directive_assembly.py`, `spawn.py`,
  `tests/test_perf_budget_issue_2053.py` (all land in this commit).

## Open findings

- The acceptance check ("a re-measured engineering-class task ... shows
  materially fewer partial reads") is inherently a future observation —
  this session cannot re-run a fresh engineering task against its own
  fix and diff the result inside itself. Per the issue's own empty-state
  note ("measured against live session logs that already exist"), the
  re-measurement is a later-session check against logs produced after
  this PR lands. Resolution path: repeat the sampling method in Why (20
  most recent `*-implementation` logs) once a comparable number of
  post-landing sessions exist, and compare `spawn.py`'s per-session
  read-count distribution against `directive_assembly.py`'s (derived:
  same aggregation script as in Why, re-run post-landing).
- `issue_workspace`/`_recut_absorbed_branch` (lines 1619–1867 of the
  pre-refactor file) sit in the same hot zone but were left in `spawn.py`.
  derived: `grep -rn "def issue_workspace\|def _recut_absorbed_branch" test/test_branch_role_field.py test/test_local_dependency_env.py`
  — result: both files locate these functions by scanning `spawn.py`'s
  literal source text (`text.index("def issue_workspace(")`) to assert
  code-shape invariants (e.g. sidecar-write-before-every-return), a
  heavier coupling than the `mock.patch.object(spawn, ...)` form the
  functions moved in this change have. Resolution path: a follow-up
  issue, if the re-measurement above still shows this neighborhood as
  hot, scoped to updating those source-scanning tests alongside the move
  — not attempted here to keep this step to one named refactoring, per
  this role's own step-decomposition practice.

## Next steps

None — `loop_state: landed` is terminal for this record kind
(coding-record).

## What did not work

None.
