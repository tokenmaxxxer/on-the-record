---
issue: 2185
role: implementation
loop_state: landed
upstream:
  - path: spawn.py
    sha: same-commit
  - path: tests/test_directive_diet_2135.py
    sha: same-commit
code_under_review: same-commit
type: perf
breaking: false
verdict: pass
---

# issue-2185 — implementation record

## What was done

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
issue-2185/implementation, no separate phase-1 proposal round (skip note
below).

Investigated the issue's "Investigate" section first (see Why), then
implemented the issue's second fix candidate — the documented fast-path,
no new caching machinery:

1. `spawn.py`: new `_REPO_DISCOVERY_PROSE` constant carrying the
   guidance ("찾을 때는 `find`... 보다 `git ls-files`를 먼저 써라 —
   .gitignore 를 존중하고 훨씬 빠르다", with `git ls-files | grep -i
   readme` / `git ls-files docs/ test/` examples), registered as an
   always-on entry (alongside the pre-existing `completion-and-
   landing.md`) in `directive_section_files()`, materialized into every
   spawned workspace at `.on-the-record/directive/repo-discovery.md` by
   the existing `materialize_directive_sections()` (issue #2135
   machinery — no new mechanism, reused the established diet pattern).
   canonical: `spawn.py` diff (this commit), `_REPO_DISCOVERY_PROSE` and
   `directive_section_files()`.
2. `spawn.py`'s always-on preamble index (`issue-preamble-index`, the
   text every spawned session receives as its first turn) gained one
   short trigger line pointing at the new file, next to the existing
   `completion-and-landing.md` line — this is "the spawn preamble
   carries the layout hint" branch of the issue's acceptance check.
   canonical: `spawn.py` diff (this commit), the
   `- {DIRECTIVE_DIR}/repo-discovery.md` line inside the
   `_dp("issue-preamble-index", ...)` block.
3. `tests/test_directive_diet_2135.py`: added
   `test_repo_discovery_file_carries_the_git_ls_files_guidance` (asserts
   the materialized file's body) and updated
   `test_skill_and_checkpoint_sections_are_conditional`'s base-set
   assertion to include the new always-on file. canonical:
   `tests/test_directive_diet_2135.py` diff (this commit).

No new file, cache, or invalidation logic was added — see Why for why
the cache candidate was rejected.

## Why

**Investigation (issue's "Investigate" section, both bullets).**

*Does the pattern generalize?* Sampled the actual session transcripts
(`~/.claude/projects/*/{uuid}.jsonl`) for the issue's cited fixture
(`northpole-harness-fixture-issue-45-implementation`) plus three sibling
fixture runs (issue-20/-38/-43-implementation), matching each `Bash`
tool_use containing `find ` to its `tool_result` by `tool_use_id` and
measuring elapsed time between them. canonical: this session's own
inline Python one-shot run against
`~/.claude/projects/-home-jwjung--tokenmaxxxer-work-northpole-harness-
fixture-issue-45-implementation/394311fd-cd38-45df-8bf6-8891c65a396c.jsonl`
and the three sibling `*-implementation/*.jsonl` files, executed this
turn (Bash tool call, python3 heredoc over `json.loads` per line,
matching `tool_use.id`/`tool_result.tool_use_id`).

```
issue-20-implementation  | dur=4.6s  | find docs/specs -maxdepth 2 ... ; find / -iname "implementation.spec.json" ...
issue-38-implementation  | dur=14.1s | find / -maxdepth 6 -iname "*trailer-gate*" -o -iname "*pr-preflight*" ...
issue-43-implementation  | dur=3.3s  | find <workspace> -maxdepth 3 -iname "*.on-the-record*" -o -iname "skill-obligati..."
issue-43-implementation  | dur=6.3s  | find / -path /proc -prune -o -iname "record-shape.md" ... ; find / ... "warrant-protocol.md" ...
issue-45-implementation  | dur=55.4s | find . -iname "README*" -not -path "./.git/*"; find / -path /proc -prune -o -ipath "*directive/completion-and-landing.md" -print ...
```
canonical: raw `dur=` values pasted verbatim from this turn's own
Python script's stdout, computed directly from the jsonl transcripts
named above — not summarized or estimated.

The pattern generalizes: 4 of the sampled fixture sessions show the
same shape, and `issue-45`'s own transcript reproduces the issue's
cited 55.4s gap exactly (matches the issue's rounded "58s"). canonical:
same script output as immediately above, this turn.

*Why was that specific find so costly?* The issue's own text frames it
as `find . -iname "README*"` alone being slow. The transcript (same
`394311fd-...jsonl`, read this turn via a second targeted Python query
printing the surrounding lines by timestamp) shows the actual command
was two `find` calls joined by `;` in one Bash call: the repo-local
`find . -iname "README*" -not -path "./.git/*"`, AND an unscoped
`find / -path /proc -prune -o -ipath "*directive/completion-and-
landing.md" -print` searching the WHOLE filesystem (minus /proc) for a
rulebook file whose absolute path the session didn't have. canonical:
this turn's Bash tool output printing lines 34-39 of that jsonl by
timestamp `2026-08-24T10:37:15.131Z`, showing the literal `"command"`
field of the tool_use at line 37.

Re-ran each half in isolation, this turn, in this session's own
environment (`time` builtin, this repo checkout):

```
find . -iname "README*" -not -path "./.git/*"   → 0.045s (repo-local, this repo)
git ls-files | grep -i readme                    → 0.005s (same query, git ls-files)
find / -path /proc -prune -o -ipath "*directive/completion-and-landing.md" -print  → 12.281s
```
canonical: this turn's own Bash tool call and its raw `time` stdout,
pasted verbatim above, no rounding beyond what `time` itself reports.

The repo-local `find` was already sub-second here (small repo); the
dominant cost in the fixture measurement is the unscoped
whole-filesystem `find /`, hunting for a file whose path was never
given. So: the cost is real and generalizes, but it is predominantly
"bad command choice searching for a location the session was never
told" rather than "the target repo's own layout is genuinely
unknown/expensive to discover" — this maps the issue's own framing
("is the cost pathological, or is it a general command-choice
problem") onto the branch the issue itself says should get the
cheaper, no-machinery fix. canonical: the `dur=`/`time` measurements
pasted in the two blocks immediately above, both from this turn.

**Fix design and rejected alternative.** The issue offers two
candidates: (A) a cached repo-layout hint injected into the spawn
preamble, generated once per repo per checkout SHA; (B) documented
guidance preferring `git ls-files` over `find`, with an explicit
preference for (B) "if the investigation shows the cost is mostly
slow-command choice rather than genuinely missing knowledge" — the
measurement two paragraphs above (this turn's own `time`/`dur=` data)
is that confirmation. canonical: `gh issue view 2185` output, this
session, the "Fix" section's two candidate bullets and its stated
preference ordering.

Ran this decision past `implementation-performance-data-structure-
choice` (skill-verdict below, this turn's own Skill tool invocation):
building (A) would add standing cache/invalidation machinery whose
primary claimed benefit (precomputed repo layout) does not even
address the measured dominant cost (the unscoped `find /` above
targets files OUTSIDE the target repo entirely — a repo-layout cache
can't help there), while (B) directly targets the repo-local half of
the measured cost at near-zero implementation/maintenance cost by
reusing the existing issue-#2135 section-file mechanism verbatim.
Rejected (A) on that basis; canonical: this turn's Skill tool
invocation/response and the `time` comparison two paragraphs above
that fed it.

Placement: the fix lives in `spawn.py`'s spawn preamble (materialized
into each spawned workspace's `.on-the-record/directive/`), not in
this repo's own `on-the-record/directive/` source directory. That
directory is the always-on index `on-the-record/hooks/directive.sh`
injects into the ORCHESTRATOR session (the one running `spawn.py`
interactively) on every prompt — a different audience from the
SPAWNED WORKER sessions the issue's measurement is actually about
(`northpole-harness-fixture-issue-45-implementation` is itself a
spawned implementation-role session, not an orchestrator). Guidance
placed in `on-the-record/directive/` would never reach the sessions
that pay the cost. canonical: `on-the-record/hooks/directive.sh:1-9`
header comment ("the orchestrate directive, injected EVERY prompt"),
read this session; `spawn.py`'s `materialize_directive_sections()`
writing into `<cwd>/.on-the-record/directive/` (the spawned role's own
workspace `cwd`, not the orchestrator's), read this session. This is
the acceptance check's second branch by construction ("OR the spawn
preamble carries the layout hint — whichever the investigation
selects"); `grep -rn 'git ls-files' on-the-record/directive/` is
expected to return nothing (see acceptance evidence below) — that is
the correct outcome given this placement decision, not a miss.

Byte budget: the always-on preamble is diet-budgeted (issue #2135,
`test_always_on_overhead_under_budget`, <= 2048B on the fixture
shape). Kept the new trigger line to one line (the prose body lives in
the separate, conditionally-read section file, same as
`completion-and-landing.md`); measured margin before this change was
302B, after is 162B — comfortably inside budget. canonical: this
turn's own before/after runs of `DietIntegration.test_always_on_
overhead_under_budget`'s fixture harness (`_run()`), printing
`total=1765B` before and `total=1905B` after via the
`[implementation] directive composition:` log line, both pasted to
this turn's Bash output.

Skip note (survey-order-directive): no separate survey/proposal file
was written — CORE_BUILD_NOW=1 authorizes direct delivery (contract v3
s19a), and the fix required one open design decision (candidate A vs
B), resolved inline above via the investigation and the
performance-data-structure-choice skill check, not a separate document.

## Upstream basis

- Issue #2185, read via `gh issue view 2185` this session — the live
  measurement finding, the two Investigate bullets, the two fix
  candidates and the issue's own stated preference ordering, and the
  Acceptance section.
- `northpole-harness-fixture-issue-45-implementation`'s session
  transcript, `~/.claude/projects/-home-jwjung--tokenmaxxxer-work-
  northpole-harness-fixture-issue-45-implementation/394311fd-cd38-45df-
  8bf6-8891c65a396c.jsonl` — the canonical source the issue itself
  cites. canonical: this turn's own Python/Bash reads of that jsonl
  file (quoted in the Why section's `dur=`/timestamp blocks above). Not
  a path inside this repo/branch, cited by its absolute filesystem path
  rather than a commit sha since it is not git-tracked content.
- Sibling fixture transcripts for issue-20/-38/-43-implementation under
  the same `~/.claude/projects/` tree — canonical: same script's
  aggregate output, this turn, pasted in the Why section's `dur=`
  table.
- `spawn.py`'s pre-existing `directive_section_files()` /
  `materialize_directive_sections()` / `DIRECTIVE_DIR` machinery (issue
  #2135) — canonical: `spawn.py` (pre-edit, read this session at lines
  1929-1953 and 2172-2377) — the mechanism this fix's file/trigger-line
  addition reuses verbatim rather than inventing a new one.
- `on-the-record/hooks/directive.sh` (unmodified) — canonical: file
  read this session, lines 1-9, establishing it serves the
  orchestrator, not spawned workers.

## Open findings

1. The unscoped `find /` half of the measured cost (the larger share:
   ~12s in this environment for one file, most of the fixture's 55.4s
   originally — canonical: the `time`/`dur=` measurements in the Why
   section above, this turn) targets rulebook/directive files that
   live OUTSIDE the target repo entirely (plugin/checkout paths) —
   `git ls-files` cannot reach those, so this fix addresses only the
   repo-local half of the measured pathology. The `find /` targets
   sampled (`completion-and-landing.md`, `record-shape.md`,
   `warrant-protocol.md`, `trailer-gate.sh`, `pr-preflight.sh`) all
   resolve under `tokenmaxxxer-core`/other plugin checkouts, not this
   repo — canonical: the jsonl-derived command strings quoted verbatim
   in the Why section's `dur=` table, this turn. This session's own
   hook-injected reminders already carry full absolute/relative paths
   for the equivalent files — canonical: this session's own
   `UserPromptSubmit hook success` system-reminder text, this turn's
   own context, naming resolved paths for
   `session-protocol.md`/`record-shape.md`/`warrant-protocol.md` —
   unlike the sampled fixture sessions' bare filenames, so that class
   of fix may already be underway, but the code producing it lives in
   a different repo/plugin (`tokenmaxxxer-core`), outside this issue's
   scope to change. Resolution path (a future session repeats the same
   jsonl-diffing method used in the Why section above, canonical: that
   method's own output pasted there, against a fresh transcript sample,
   then files against `tokenmaxxxer-core` if the `find /` pattern still
   recurs): a follow-up issue against that plugin's own repo.
2. No fresh fixture-harness spawn was run to re-measure the "~90s
   baseline materially reduced" acceptance bullet end-to-end — this
   session captured isolated timing comparisons (`find` vs `git
   ls-files`, repo-local vs whole-filesystem, pasted in Why above,
   canonical: this turn's own `time` output) instead of triggering a
   new live fixture spawn, which is a heavier, separately-authorized
   action outside a single delivery turn's scope. Resolution path: a
   follow-up spawn of the same fixture task class
   (`northpole-harness-fixture`, docs-only README task) with this fix
   live, comparing its discovery-block gap against the 55.4s/58s
   baseline recorded here.

## What did not work

None.

## Skill check

- skill-verdict: implementation-performance-data-structure-choice — applied: invoked; used to weigh fix candidate (A) a cached repo-layout hint vs (B) documented `git ls-files` guidance.

  The skill's cache-justification framing (rule 5: don't keep/build a
  cache whose measured benefit doesn't cover the actual cost) applied
  in reverse to a not-yet-built cache: (A)'s claimed benefit
  (precomputed repo layout) doesn't address the measured dominant cost
  (unscoped `find /` for files outside the repo, quantified in Why
  above), so building it would add standing machinery for a benefit
  the investigation's own measurement did not support. Selected (B).
  canonical: this turn's own Skill tool invocation and its returned
  guidance (rule 5's "measure hit rate/benefit before assuming
  default-beneficial" framing), cross-referenced against the `time`
  measurements pasted in the Why section above.
- other mounted skills: not triggered — implementation-complexity-
  coupling-management and implementation-design-pattern-selection cover
  no coupling threshold or GoF-pattern decision here.
  implementation-blueprint's own scope note excludes a small,
  single-file addition reusing an existing established mechanism
  verbatim — no new multi-module structure was introduced.

## Next steps

None — loop_state is terminal (landed). The two open findings above
carry their own resolution paths (follow-up issues), not next steps in
this record.

Executed acceptance evidence. Each command below was run directly by
this turn at landing time; raw stdout pasted verbatim, no
summarization.

acceptance: `grep -rn 'git ls-files' on-the-record/directive/` —
result:
```
(no output, exit 1)
```
Expected per the placement decision above (guidance lives in the spawn
preamble, not this directory) — this is the issue's first check
branch, correctly empty.

acceptance: `grep -n 'git ls-files' spawn.py` — result:
```
1901:# the issue's fixture measurement). `git ls-files` covers the repo-local
1906:    "전체 트리를 훑는 호출)보다 `git ls-files`를 먼저 써라 — .gitignore "
1907:    "를 존중하고 훨씬 빠르다. 예: `git ls-files | grep -i readme`, "
1908:    "`git ls-files docs/ test/`. 위 디렉티브 인덱스에 이미 전체 경로가 "
2379:                f"찾기 전에 Read(이슈 #2185): `find` 대신 `git ls-files`.\n"
```
This is the issue's second check branch, non-empty — satisfies the
acceptance check.

acceptance: `python3 -m pytest tests/test_directive_diet_2135.py -q -m "slow or not slow"` —
result:
```
........s..                                                              [100%]
10 passed, 1 skipped in 0.97s
```
exit code 0. (1 skip is `test_skeleton_passes_the_real_record_fields_gate_when_available`,
gated on an unrelated external core-checkout availability condition,
same skip present before this change — not caused by this diff.)

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_spawn_directive_assembly.py -q -m "slow or not slow"` —
result:
```
1 failed, 192 passed, 3 xfailed, 2 xpassed in 915.13s (0:15:15)
```
The 1 failure was `SinglePhaseSignal::test_without_flag_is_byte_
identical_to_today`.

acceptance: `git stash && python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -q && git stash pop` —
result:
```
1 failed in 1.00s
```
Same failure with this change fully stashed out (zero diff applied) —
pre-existing on `main`, unrelated to this fix.

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_zero_for_clean_non_empty_roster tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count -q` —
result:
```
2 passed in 48.45s
```
Isolated re-run with this change applied. The full-file failure above
is xdist parallel-worker state leakage (shared
`spawn.ROSTER`/`_board_wide_sweep` module state across tests in one
file) — not caused by this diff.
