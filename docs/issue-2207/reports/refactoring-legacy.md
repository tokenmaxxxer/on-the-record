---
issue: 2207
role: refactoring-legacy
author: refactoring-legacy
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
motivation: Large Class (Fowler's code-smell catalog) — spawn.py mixed
  ~10 unrelated concerns as top-level functions in one 3,486-line module;
  measurement below shows the spawn-time directive/record-skeleton/cross-
  family-skill assembly concern is what sessions repeatedly re-page.
mechanics: Extract Class, applied module-level (spawn.py has no classes;
  its "classes" are the existing sibling-module extractions — relay.py,
  roster.py, plumbing.py, watchdog.py, events.py, consult.py, skills.py,
  lifecycle.py, board.py, pipeline.py — spawn.py re-exports every moved
  name so `spawn.<name>` and `mock.patch.object(spawn, "<name>")` keep
  working, per the established issue-#2105 extraction series). Moved 25
  names (functions + their private constants, 518 lines) verbatim into a
  new 10th module, directive_assembly.py.
verdict: pass
---

# issue-2207 — refactoring-legacy record

## What was done

canonical: this session's own read of `spawn.py` (this branch's parent
commit 46da1c8a199048b380c363a936e92bca1c7c5393, lines 1–3486) and of the
20 session logs listed in Upstream basis.

Re-delivers issue #2207: a prior session already applied Extract Class to
this exact concern (commits 57ae2499a8a9 "extract directive/skill-
assembly cluster from spawn.py into directive_assembly.py" and 85a9611f6809
"reconcile operator-frozen constraint", branch issue-2207/refactoring-legacy,
PR #2308) and that delivery was independently re-derived by an
execution-observation session (merged PR #2327,
`docs/issue-2207/reports/execution-observation.md`) as mechanically sound
— extraction mechanism, scope, no source-pin-floor breakage, no added
per-spawn overhead, correct BM25 relocation all confirmed by that
independent re-run — but with the record's own supporting arithmetic
wrong in three ways: an 11-line `wc -l` miscount, a "20 most recent"
session-log sample that brace-expanded to 21 entries, and two of the
seven detailed per-session read-offset tallies undercounting (issue-2262
missing an offset, issue-2241 missing one too). PR #2308 itself was
closed unmerged by the 2026-08-25 history rewrite (its `git merge-base`
against the current `main` is 1249 commits back — canonical: `git
merge-base HEAD 85a9611f6809183fa49ec9c270c2fbcae7079d8a` = same commit
`git log --oneline 61f9345b..85a9611f | wc -l` = 1249 commits), so this
session re-applies the same Extract Class move against the current `main`
(the code arrived by cherry-picking commit 57ae2499's non-record diff and
re-resolving conflicts against the code that landed on `main` while
#2308 sat unmerged — see Upstream basis) and re-derives every figure
below fresh, rather than re-typing the prior record's numbers.

**Extract Class**, applied to the cluster of functions that assemble a
spawned session's directive text, on-demand section files, record
skeleton, and cross-family BM25 skill matching — the region the fresh
measurement (below) still shows sessions re-paging. Moved verbatim (no
behavior change) from `spawn.py` into a new module `directive_assembly.py`:

- `_CHECKPOINT_CONTRACT_BLOCK`, `_checkpoint_contract_block`,
  `_checkpoint_index_block`
- `DIRECTIVE_DIR`, `DEFAULT_SESSION_MAX_TURNS`, `_COMPLETION_PROSE`,
  `_LANDING_BATCHING_PROSE`, `_TURN_BUDGET_PROSE`, `_REPO_DISCOVERY_PROSE`,
  `_KNOWN_PATHS_PROSE`, `_SKILL_CHECK_PROSE`, `_SKILL_VERDICT_PROSE`,
  `_role_touches_code`, `directive_section_files`,
  `materialize_directive_sections`, `_directive_system_prompt_block`
- `_RECORD_SKELETON`, `_stamp_additive_record_fields`,
  `write_record_skeleton`, `composition_breakdown`
- `_SKILL_USE_SENTENCE_RE`, `_TOKEN_RE`, `_STOPWORDS`, `_BM25_K1`,
  `_BM25_B`, `_CROSS_FAMILY_CONSULT_TOPN`, `_bm25_cross_family_scores`,
  `_cross_family_skill_matches`

derived: `grep -c "^[A-Za-z_][A-Za-z0-9_]* = directive_assembly\." spawn.py`
(the re-export block) = 25 — six more names than #2308's original 19
(`DEFAULT_SESSION_MAX_TURNS`, `_TURN_BUDGET_PROSE`, `_role_touches_code`,
`_stamp_additive_record_fields`, plus the pre-existing `directive_section_files`
gaining a `code_scoped` parameter and `write_record_skeleton`/`_RECORD_SKELETON`
gaining an `author_line` parameter): issues #2227, #2241, and #2262 landed
new code into this same cluster on `main` while PR #2308 sat unmerged, so
this redelivery's move is a strict superset of #2308's, carrying that new
code along rather than leaving it stranded in `spawn.py`.

derived: `wc -l spawn.py` after = 2997 (before, at the parent commit
46da1c8a199048b380c363a936e92bca1c7c5393, was 3486 — that figure names a
different git ref's content, out of this hermetic check's working-tree
scope).
derived: `wc -l directive_assembly.py` after = 553 (new file; 518 lines of
moved code plus a ~35-line module docstring/import header, same shape as
the other 9 sibling extractions).

`spawn.py` imports `directive_assembly` and re-exports every one of the
above names at module level, exactly like the prior 9 extractions
re-export from their own module (`_sp = None` at the top of
`directive_assembly.py`; `spawn.py` sets
`directive_assembly._sp = sys.modules[__name__]` right after import, same
guard as the other 9). Two correctness details this pattern exists
specifically to cover, both present in the moved code and freshly
re-checked against the current tree:

- `spawn.ROOT` is patched directly by several tests — canonical:
  `gates/test_clean_reconcile_safety.py:65`, `tests/test_flows.py:84`,
  `tests/test_spawn_checkout_network.py:897` (each does `spawn.ROOT =
  ...`, re-grepped this session, same line numbers as #2308's record) —
  `write_record_skeleton` reads `_sp.ROOT`, never a locally-computed
  path, so those patches still take.
- The checkpoint blocks embed spawn.py's own path in text handed to the
  *spawned* session (`python3 <path> await-approval ...`). Using local
  `__file__` inside `directive_assembly.py` would have pointed a spawned
  session at the wrong file; both blocks resolve it via
  `Path(_sp.__file__).resolve()` instead.

One existing test asserted `_bm25_cross_family_scores`'s source text is
free of `subprocess` calls by regex-scanning `spawn.py` directly — the
test `test_bm25_scoring_makes_no_network_or_consult_call`, in
`tests/test_perf_budget_issue_2053.py`. Updated it to scan
`directive_assembly.py` instead (the function's new home), reusing
#2308's own already-reviewed fix for this test rather than relaxing or
deleting the check.

acceptance: `python3 -m pytest -q` (full suite, default `-n auto` from
`pytest.ini`) — result:
```
10 failed, 4428 passed, 1 skipped, 21 xfailed, 2 xpassed in 801.21s (0:13:21)
```
derived: re-ran all 10 failing node IDs against the unmodified parent
commit (`git stash`, same commit 46da1c8a199048b380c363a936e92bca1c7c5393
this branch is built on) — result:
```
6 failed, 4 passed in 11.62s
```
6 of the 10 reproduce identically on the parent commit, unmodified by
this diff. derived: re-ran the remaining 4 in isolation on this branch
(with the extraction applied) — result:
```
4 passed in 11.76s
```
all 4 pass in isolation — consistent with this shared host's own
documented full-suite-under-`-n auto` timing/load flakiness (the same
pattern `docs/issue-2207/reports/execution-observation.md` already found
for PR #2308's own full-suite run on this host). Zero of the 10 failures
is attributable to this diff; none touch `spawn.py`, `directive_assembly.py`,
or `tests/test_perf_budget_issue_2053.py`.

### Operator-frozen constraint reconciliation

amendments-reconciled: https://github.com/tokenmaxxxer/on-the-record/issues/2207#issuecomment-5403812267
(2026-08-25T01:28:08Z) — "must hold systemically for every session ...
against any target repo", "no added per-spawn overhead or steady-state
load, no new conflict surfaces ..., no stall/deadlock modes, no
consumer-tree pollution", trade-offs measured and stated, not discovered
later. (#2308's own commit 85a9611f6809 already answered this once;
re-answered here fresh since #2308 never landed.)

- Systemic scope: canonical: `directive_assembly.py` and `spawn.py` both
  live in the on-the-record plugin's own checkout (this repo), never in a
  target/consumer repo — `spawn.py:43` (unchanged by this move),
  `ROOT = Path(__file__).resolve().parent`, is the plugin root, not the
  target repo a session is spawned against. Every function moved
  reads/writes only plugin-relative or spawned-workspace-relative paths
  (`_sp.ROOT`, `cwd`/`work` parameters), never something specific to this
  self-hosted checkout.
- No added per-spawn overhead: derived: `python3 -c "import time;
  t=time.time(); import spawn; print(time.time()-t)"`, this session's own
  environment — result: `0.541` s cold-import. This cost is paid once per
  process start, not per spawn call — the functions themselves execute
  identical bytecode to before the move (verbatim copy, no wrapper/
  indirection beyond the existing `_sp.<name>()` pattern every one of the
  other 9 extractions already uses at the same call sites).
- No new conflict/stall surface: canonical: this commit introduces no new
  file writes, locks, subprocess calls, or background threads —
  `materialize_directive_sections`/`write_record_skeleton` write exactly
  the same paths (`<cwd>/.on-the-record/directive/*`,
  `<cwd>/docs/issue-<n>/reports/<role>.md`) they wrote before the move,
  from the same call sites.
- No consumer-tree pollution: canonical: `git status --short` (this
  session, post-move, before staging) shows only `directive_assembly.py`,
  `spawn.py`, `tests/test_perf_budget_issue_2053.py`, and this docs record
  changed under version control — no file under a spawned workspace or
  target repo is touched by this commit. (One unrelated side effect this
  session hit and reverted before committing: the parallel full test-suite
  run truncated the tracked `roles/implementation.json` to its own tmp-dir
  isolation failure — `git checkout -- roles/implementation.json` restored
  it; that file carries no change in this commit's diff.)
- Trade-off stated: the acceptance benefit (fewer `spawn.py` partial
  reads) accrues only to sessions reading `spawn.py`'s remaining
  concerns; a session whose task lands specifically in
  `directive_assembly.py`'s new concern gets no read-cost change from
  this move alone (it now pages a 553-line file — `wc -l
  directive_assembly.py` — instead of finding the same content inside a
  3,486-line one — strictly smaller, never worse). See Open findings for
  the post-landing re-measurement this trade-off still needs, and for a
  second trade-off this session's fresh measurement surfaced that #2308's
  own record did not have data for: a comparable amount of `spawn.py`
  re-reading now also clusters in a region this move does NOT cover.

## Why

canonical: `on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log`
(the issue's own original cited evidence, from before the history
rewrite) and the 20 session logs listed in Upstream basis (this
session's own fresh sample, re-derived rather than reused from #2308's
record).

Issue-2201's original session log showed 19 of that session's 50 `Read`
calls landing on `spawn.py` — the issue's own founding measurement, still
true of the historical log and unaffected by the history rewrite (the
log itself is not a git-tracked artifact).

Sampled the 20 most recent on-the-record `*-implementation` session logs
under `$MUSTER_WORKSPACE_ROOT` as of this session's investigation time
(2026-08-25, ending at issue-2285's 14:40:28 log) — a fresh sample, not
a re-citation of #2308's now-superseded one, since this session's own
working tree (and the sessions that produced these logs) both postdate
the history rewrite. Extracted each log's `Read` tool_use events the same
`(file_path, offset)` shape `trajectory_analyzer.py`'s
`repeated_read_offsets`/`tool_use_events` already parse for this repo
(issue #2214), via a standalone aggregation script.

derived: python3 script reading each `*.session.*.log` with
`json.loads` per line, filtering `type=="assistant"` tool_use entries
named `Read`, grouping by `os.path.basename(file_path)` — reproduction:
```
python3 -c "
import json, os
from collections import defaultdict
for path in [...20 log filenames, see Upstream basis...]:
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
10 of the 20 touched `spawn.py` at all (script output, this session);
their per-session `spawn.py` Read-call counts (partial + any offset-less
full read): **14 (issue-2293), 7 (issue-2262), 6 (issue-2291), 5
(issue-2227), 5 (issue-2284, 1 full + 4 partial), 5 (issue-2241, 1 full +
4 partial), 5 (issue-2229, 1 full + 4 partial), 3 (issue-2203), 2
(issue-2333), 1 (issue-2312)**. The other 10 sampled sessions never read
`spawn.py`. Partial-read offsets for the sessions with more than 2:

```
issue-2293: 2380,2870,2560,1674,1762,3095,3035,1107,1236,2518,3108,3125,2437,455
issue-2262: 2260,1880,1096,1926,2270,2560,1947
issue-2291: 1555,840,2465,2527,3060,1772
issue-2227: 1900,2560,2369,2408,2076
issue-2284: 2820,2085,2090,2130 (+1 offset-less full read)
issue-2241: 1219,1459,1110,1229 (+1 offset-less full read)
issue-2229: 1380,1094,1193,1290 (+1 offset-less full read)
```

derived: classifying all 50 partial-read offsets above against this
session's moved cluster (lines 1910–2427 of the pre-move `spawn.py`, this
branch's parent commit) — 11 fall inside it (concentrated in issue-2293
(1), issue-2227 (3), issue-2284 (3), and issue-2262 (4)), 25 fall below
it (issue-2241, issue-2229, issue-2312, issue-2333, and most of
issue-2203, issue-2291, issue-2262, issue-2293, and issue-2227 — the
`issue_workspace`/`_recut_absorbed_branch`/admission-table region
#2308's own record already flagged as "same hot zone, left in place",
see Open findings), and 14 fall above it (issue-2293's and issue-2291's
higher offsets, 2465–3125, land in the admission-checks/`_spawn_one`
body that has grown since #2308's own measurement and was not
separately flagged before). This confirms the pattern this issue asked
about is still recurring (not a one-off) and that the moved cluster is
still a real, non-trivial part of it — 11/50 = 22% of the sampled
partial reads — without this move covering all of it — consistent with the issue's own
"only if the sample supports it" framing: it does, for this specific
cluster, and the remaining hot zones are a distinct area this session
did not touch (see Open findings).

The #2114–#2122 2,649-line source-pin floor the issue describes is not
present in this checkout as a literal enforced test. derived:
`grep -rln "2649\|source_pin" tests/ test/ gates/` — result: one match,
`tests/test_perf_budget_issue_2053.py`, which is this session's own
comment referencing "the source-pin below" (the regex-based test scanning
`directive_assembly.py`'s function body) — not a literal 2,649-line floor
assertion anywhere. `pipeline.py`'s own module docstring already calls
itself "extraction 8/N, endgame" for the #2105 series — this extraction
is a step beyond that self-declared endgame, justified by the fresh
measurement above rather than by continuing the series on a fixed
schedule.

## Upstream basis

- canonical: the 20 sampled session logs under `$MUSTER_WORKSPACE_ROOT`,
  read directly for this investigation (most-recent-first as of this
  session's investigation time):
  `on-the-record-issue-{2285,2293,2291,2333,2331,2227,2313,2312,2315,2314,2284,2203,2241,2262,2278,2268,2266,2226,2229,2219}-implementation.session.*.log`
  — derived: `ls $MUSTER_WORKSPACE_ROOT | grep '^on-the-record-issue-.*-implementation\.session\.'`
  piped through a timestamp sort, top 20 taken; 20 distinct issue numbers,
  no duplicates (re-checked against #2308's own record's brace-expansion
  miscount — see What was done).
- `on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log`
  — the issue's own original cited evidence, re-checked here (unaffected
  by the history rewrite — a plain log file, not a git object).
- `docs/issue-2207/reports/execution-observation.md` (this repo,
  `loop_state: handed-off`, `result: failed` on PR #2308's own record
  arithmetic though the extraction itself was confirmed sound) — the
  independent re-derivation this redelivery's corrected figures respond
  to.
  sha: 46da1c8a199048b380c363a936e92bca1c7c5393
- commits 57ae2499a8a927656b18d288035ceadffe7e6f49 and
  85a9611f6809183fa49ec9c270c2fbcae7079d8a (branch issue-2207/refactoring-legacy,
  PR #2308, closed unmerged by the 2026-08-25 history rewrite — `git
  merge-base HEAD 85a9611f6809183fa49ec9c270c2fbcae7079d8a` =
  61f9345b5e535600e9d4facfcd9483681f3b41b4, 1249 commits behind current
  `main`) — the code diff this session cherry-picked and re-resolved
  against `main`'s current state of the same cluster.
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
  read-count distribution against `directive_assembly.py`'s.
- New this session (not present in #2308's own record, which had no data
  on it): the fresh 20-log sample's `spawn.py` offsets split across this
  move's cluster (11/50 = 22%) and two other regions — below it (25/50 =
  50%, `issue_workspace`/`_recut_absorbed_branch`/admission-table,
  already flagged by #2308's record as left in place) and above it
  (14/50 = 28%, the admission-checks/`_spawn_one` body, which has grown
  since #2308's measurement and was not separately flagged before).
  Resolution path: a
  follow-up issue, scoped to whichever of those two regions the
  post-landing re-measurement (above) still shows as hot, applying the
  same step-decomposition practice (one named refactoring at a time)
  this session followed.
- `issue_workspace`/`_recut_absorbed_branch` sit in the same
  lower-offset hot zone but were left in `spawn.py`, same as #2308's own
  finding. derived: `grep -rn "def issue_workspace\|def _recut_absorbed_branch" test/test_branch_role_field.py test/test_local_dependency_env.py`
  — result: both files locate these functions by scanning `spawn.py`'s
  literal source text (`text.index("def issue_workspace(")`) to assert
  code-shape invariants, a heavier coupling than the
  `mock.patch.object(spawn, ...)` form the functions moved in this
  change have. Resolution path: unchanged from #2308's own record — a
  follow-up issue, not attempted here to keep this step to one named
  refactoring.

## Next steps

None — `loop_state: landed` is terminal for this record kind
(coding-record).

## What did not work

None in the delivered diff. This session's own full-suite test run (see
What was done) raced against a concurrent background process on this
shared host that momentarily truncated the unrelated, untouched
`roles/implementation.json` to a tmp-dir isolation leak in some other
test/session — caught via `git status --short` before staging and
restored with `git checkout -- roles/implementation.json`; it carries no
change in this commit and is unrelated to this refactor's own diff.

skill-verdict: refactoring-legacy-refactoring-step-decomposition — applied: invoked; Extract Class is the smallest catalog step that makes progress here (rule 1) — a step beyond #2105's own self-declared "endgame" (pipeline.py's docstring), justified by fresh measurement rather than a fixed schedule (rules 4 and 7); ran the full suite before merging the sequence (rule 2).
skill-verdict: refactoring-legacy-verification-cadence — applied: invoked; ran the two targeted subset suites (`tests/test_perf_budget_issue_2053.py`, `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, plus the directive/checkpoint/observation-recovery suites) fast-first before escalating to the full suite (rules 2 and 3); treated the two failures that surfaced as a stop-and-investigate signal, reproduced them against the unmodified parent commit rather than adjusting any test (rule 5).
skill-verdict: refactoring-legacy-characterization-test-scope — not-applicable: pure verbatim move (Extract Class, no behavior change) already backed by the existing full regression suite and the established 9-extraction sibling pattern — no previously-untested legacy surface is being touched, so no new characterization tests are needed.
skill-verdict: refactoring-legacy-seam-selection — not-applicable: no new or changed behavior is being introduced into untested code (pure move), so no seam-placement decision arises.
skill-verdict: refactoring-legacy-strangler-fig-migration — not-applicable: a single in-repo module extraction, not a live-traffic migration with a cutover/decommission decision.
skill-verdict: conformance-review-traceability-and-evidence — not-applicable: cross-family match on this session's task text (issue #2001) — this session is a refactoring-legacy build, not a conformance-review verdict/traceability task.
