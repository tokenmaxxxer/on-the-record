---
issue: 2409
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2211/reports/implementation.md
    sha: 188ceb3e4328fad06d8ab79aca19d2b787f42015
  - path: docs/issue-2262/reports/implementation.md
    sha: same-commit
code_under_review:
  - directive_assembly.py
  - spawn.py
  - scripts/related_files.py
  - scripts/session_waste_metrics.py
  - tests/test_directive_diet_2135.py
  - tests/test_spawn_directive_assembly.py
  - tests/test_related_files.py
  - tests/test_session_waste_metrics.py
type: feat
breaking: none — additive prose constants, two new always/conditionally-materialized directive section files, two new standalone scripts; no existing gate, prose constant, or record field changed or removed
verdict: pass
---

# issue-2409 — implementation record

## What was done

canonical: git show f9f8041f --stat

Three additive mechanisms, one per waste class the issue measured (177
sessions, 2026-08-25: median 15.0min/67 turns, 62% of 9,555 Bash calls
neither pytest/git/gh, 6.9 hook-refusal `tool_result` errors/session, 105
`spawn.py` + 96 own-record-file redundant re-reads), plus the
instrumentation artifact the acceptance section asks for so these classes
are tracked going forward rather than re-derived by hand each time.

1. **Instrumentation artifact** (Acceptance item 1) —
   `scripts/session_waste_metrics.py`. Reuses
   `trajectory_analyzer.parse_session_log`/`tool_use_events`/
   `tool_result_index`/`harness_fields` (issue #2214) rather than
   re-parsing the log. Adds: `classify_bash()` (pytest/git/gh/other, by
   first real command token after stripping `VAR=` prefixes — matches how
   the issue's own 9,555-call count was produced); `hook_refusals()`
   (regex `PreToolUse:(\w+) hook error: \[(hook path)\]: ([\w-]+):`,
   confirmed against real corpus lines, not invented — see Upstream
   basis); `redundant_file_reads()`/`named_offender_counts()` (`Read`
   calls per `file_path` collapsed across offsets, since a second `Read`
   of the same file at a different offset is still a redundant trip back
   into it — deliberately not `trajectory_analyzer.repeated_read_offsets`,
   which only catches exact-offset repeats); `per_turn_breakdown()` — one
   row per tool_use in stream order with its classification, "what each
   turn's tool call was for". CLI: `python3
   scripts/session_waste_metrics.py <session_log> [--md]` for one session,
   `--batch '<glob>'` for a corpus rollup (regenerate command below).

2. **Exploratory-Bash reduction** (Acceptance item 2) —
   `scripts/related_files.py` + new always-for-code-scoped-roles directive
   section `task-lookup.md` (`_TASK_LOOKUP_PROSE`, `directive_assembly.py`,
   gated by the same `code_scoped` flag `known-paths.md` already uses,
   issue #2227 REQ-10). One call —
   `python3 scripts/related_files.py <issue-number> [--keyword W ...]` —
   returns `docs/issue-<n>/`'s tracked tree (`git ls-files`), every
   code/test/spec file outside that tree already mentioning the issue
   (`issue-<n>`, `issue #<n>`, or `#<n>`, one `git grep`), and optional
   keyword hits — the "supported lookup that returns what N greps
   currently return" the acceptance section names as an example
   mechanism.

3. **Hook-refusal-as-upfront-contract** (Acceptance item 3) — new
   always-on directive section `hook-contract.md` (`_HOOK_CONTRACT_PROSE`).
   Six numbered rules, each a direct summary of a real
   `pretooluse_dispatcher.py` gate (not invented): (1) heredoc-shaped
   `git commit`/`gh pr|issue create|comment` gets refused for role
   sessions every time (issue #1976, `heredoc-command-refusal-gate.sh`) —
   use two `-m` flags / `--body-file`; (2) a state/defect/outcome claim in
   `docs/**` needs a `canonical:`/`derived:` tag with an executed-live
   citation, no orphaned/untracked backtick paths, no bare counts
   (`record-claim-guard.sh`, mirroring `gates/record_lint.py` — this rule
   fired for real against an earlier draft of this very record, see
   Upstream basis); (3) `acceptance:`/`live-fire:` citations must match a
   command re-run now, not a reused past result
   (`acceptance-command-real-run-guard.sh`,
   `live-fire-claim-real-run-guard.sh`); (4) a `docs/specs/*`-touching
   commit needs `gates/spec_index.py --update` in the same commit
   (`spec-index-preflight.sh`); (5) a new gate/hook script needs a
   matching `enforcement-boundary.md`/`generated-paths.md` row
   (`gate-registration-guard.sh`); (6) `CORE_BUILD_NOW=1` already bypasses
   the phase-2 approval gates (`approval-gate.sh`, `pr-preflight.sh`).

4. **Redundant-read reduction** (Acceptance item 4) — folded into the
   existing `turn-budget.md` section (`_TURN_BUDGET_PROSE`,
   `directive_assembly.py`) as a third numbered item, rather than a new
   file: tells a session not to re-open `spawn.py`/`directive_assembly.py`
   for prose/env-var names already injected verbatim via
   `--append-system-prompt` (issue #2204), and not to re-`Read` its own
   record file after every `Edit` (Edit already errors on failure; the
   harness tracks file state).

`spawn.py`'s re-export block gained `_TASK_LOOKUP_PROSE`/
`_HOOK_CONTRACT_PROSE`, matching the existing one-line-per-constant
pattern for every other `_*_PROSE` name.
canonical: git show f9f8041f -- spawn.py

Tests added/updated: `tests/test_directive_diet_2135.py` (three new
methods plus one updated set-equality assertion),
`tests/test_spawn_directive_assembly.py` (one updated assertion block),
`tests/test_related_files.py` (new file, real temp git repos, no
mocking), `tests/test_session_waste_metrics.py` (new file, synthetic
stream-json fixtures matching `tests/test_trajectory_analyzer.py`'s
existing `_tool_use`/`_tool_result` helper shape). Exact counts are in
the pasted acceptance run below rather than retyped here.

## Why

derived: gh issue view 2409 --json body,comments

The issue names three independently-attackable waste classes and asks
for a stated mechanism per class, not a single fix. Each mechanism above
maps 1:1 to one class, following the exact precedent shape
`docs/issue-2185`/`docs/issue-2211`/`docs/issue-2262` already established
for this repo's directive-diet lineage: a hand-authored (not generated)
prose constant, gated into `directive_section_files()`, materialized to
`.on-the-record/directive/<name>.md` AND delivered via
`--append-system-prompt` (issue #2204's channel — no new "Read this file"
round trip). No new hook, no new gate, no new delivery mechanism was
introduced; extending a mechanism three prior issues already validated is
what "add no per-spawn overhead or new conflict surface" (operator's
frozen constraint, issue #2409 comment 2026-08-25) requires by
construction, not by retrofit — the same reasoning issue #2262's record
gave for its own additive-only design.

`hook_refusals()`'s regex was written against real refusal lines pulled
from the actual 177-session corpus (grep-sampled live this session — see
Acceptance evidence), not the issue body's prose — the corpus confirmed
the exact shape `PreToolUse:<Tool> hook error: [<hook path>]: <gate>:
<message>` and, critically, surfaced `board-gate` as a refusal category
outside this repo entirely.
canonical: grep -rn "board-gate" on-the-record/hooks/*.sh on-the-record/hooks/*.py pretooluse_dispatcher.py — run live this session — no live registration found, one incidental doc-comment mention in gates/gates.py only
`board-gate` is emitted by the separate tokenmaxxxer-core plugin
(`$CLAUDE_PLUGIN_ROOT_CORE`, per this same session's own SessionStart
hook output: "[core] Interaction protocol"), outside this repo's write
set. `hook-contract.md` therefore does not cover it; see Open findings
for the concrete count this left uncovered.

`related_files.py` resolves the `docs/issue-<n>/` exclusion by filtering
in Python rather than a git exclude-pathspec (`:!docs/issue-<n>/**`):
exclude-magic pathspec globbing needs `core.globPathspecs` or explicit
`:(exclude)` composition that varies by git version and repo config — a
portability footgun for a two-line filter this doesn't need.

Redundant-read guidance was folded into the existing `turn-budget.md`
file rather than a fourth new file: it is the same underlying behavior
`_TURN_BUDGET_PROSE`'s existing items (1)/(2) already address (batch
exploration, don't page a whole file) — a third numbered item in the same
section is more discoverable than a same-tier sibling file a session
would need to separately notice.

Design choices made without a phase-1 proposal (build-now bypass,
`CORE_BUILD_NOW=1` set by the spawner, contract v3 s19a) — confirmed this
session by reading `on-the-record/hooks/approval-gate.sh:186` and
`pr-preflight.sh:243`, both of which special-case this env var.

## What did not work

An earlier draft of this record's Open findings/Acceptance sections was
refused twice by this repo's own `record-claim-guard.sh` while writing it
(bare count claims with no `canonical:`/`derived:` tag, and two paths
cited — `tests/test_related_files.py`, `tests/test_session_waste_metrics.py`
— that were not yet committed to git history). Both are exactly the
`hook-contract.md` rules this delivery adds (rule 2's citation-shape
requirement, and the untracked-path check the same gate also runs).
Fixed by committing the code/test files first (this record's own
citations now resolve against real git history) and adding the missing
`canonical:`/`derived:` tags below — kept as a concrete, live
demonstration that the gate's rules are real and that this delivery's
own record had to follow them, not just describe them.

## Upstream basis

`docs/issue-2211/reports/implementation.md` and
`docs/issue-2262/reports/implementation.md` established the
`directive_section_files()`/materialize/`--append-system-prompt` pattern
and the `code_scoped` gating this issue's two new sections reuse
unchanged.

GitHub issue #2409 (`gh issue view 2409`) supplied the three waste
classes, the 177-session measurement table, the acceptance section, and
the operator's frozen no-side-effects constraint (issue comment,
2026-08-25).

`on-the-record/hooks/pretooluse_dispatcher.py`'s `GATES` list (lines
250-303) and the 20 individual gate scripts' header comments supplied
`hook-contract.md`'s six rules — read directly this session
(`sed -n '250,303p' on-the-record/hooks/pretooluse_dispatcher.py`; each
gate script's own header comment), not paraphrased from memory or from
the issue body.

## Open findings

- **`board-gate` refusals are not covered by `hook-contract.md`.** In the
  5-issue live measurement below it is the single largest category.
  canonical: acceptance table below — result: board-gate=10 of 35 total
  refusals across the 5 sampled sessions. It is emitted by the
  tokenmaxxxer-core plugin, not this repo — same out-of-write-set shape
  issue #2211's record already flagged for the directive-index one-liner.
  Resolution path: a companion issue against tokenmaxxxer-core to publish
  `board-gate`'s branch/`maintenance-targets:` rule as its own directive
  section, mirroring how this repo's own gates are now summarized here.
- **`pr-preflight`/`acceptance-command-real-run-guard` refusals are only
  partially covered.** canonical: acceptance table below — result:
  pr-preflight=2, acceptance-command-real-run-guard=1 of 35 total in the
  sample. `hook-contract.md` rule 6 names `pr-preflight.sh`'s
  `CORE_BUILD_NOW` bypass but not its other checks (title/body shape,
  `Closes` trailer phase rules); rule 3 covers
  `acceptance-command-real-run-guard.sh`'s core claim but the sample's
  one hit predates this delivery so it is not independently
  live-fire-tested. Resolution path: expand `hook-contract.md` if a
  future measurement shows these categories staying high after this
  delivery.
- **No corpus-scale "after" re-measurement was performed** — see
  Acceptance evidence below for exactly what was and was not measured,
  and the honest 5x-target gap statement.

## Next steps

None — `loop_state: landed`. The three open findings above are
resolution-path-only, not blocking follow-up work on this delivery.

## Acceptance evidence (executed)

**Regenerate the instrumentation artifact** (Acceptance item 1):
```
$ python3 scripts/session_waste_metrics.py <session_log> [--md]
$ python3 scripts/session_waste_metrics.py --batch '<glob>'
```

A real generated instance of this artifact — not just the regenerate
command — is committed at
`docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`:
the same 5-session rollup as the before/after table below (per-session
`wall_clock_ms`/`num_turns`/`bash_total`/`bash_other_share`/
`hook_refusals`/`named_offenders`, plus each session's `hook_refusals_by_gate`
breakdown), produced by `batch_summary()` plus one `analyze()` call per
path (the CLI's own `--batch` flag only accepts a single glob with no
brace-expansion, so the multi-issue selection needs the same short
`python3 -c` driver already shown below rather than the bare CLI form).
canonical: python3 -c "import sys, json; sys.path.insert(0, 'scripts'); import session_waste_metrics as sw; paths = ['/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2314-implementation.session.20260825T124527.1898083.log', '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2331-implementation.session.20260825T132149.4048637.log', '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2348-implementation.session.20260825T165751.3137898.log', '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2382-implementation.session.20260825T165945.3150594.log', '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2393-implementation.session.20260825T182737.1665378.log']; s = sw.batch_summary(paths); [row.update(hook_refusals_by_gate=sw.analyze(row['session_log'])['hook_refusals']['by_gate']) for row in s['per_session']]; print(json.dumps(s, indent=2, ensure_ascii=False))" — result: pass — run live this session; output diffed byte-for-byte identical to the committed artifact file (`diff <(above command) docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json` — empty diff) and its `bash_total`/`hook_refusals_total`/`named_offenders_total`/per-session rows match the before/after table below exactly, confirming both were produced by the same live run rather than hand-typed. This addresses conformance-review PR #2420's NR1b finding (per-turn-breakdown artifact previously documented only as a regenerate command, no generated instance committed).

**Targeted new/updated tests** (env -u CORE_BUILD_NOW: this session's own
env carries CORE_BUILD_NOW=1 for the build-now bypass, which one
pre-existing, unrelated test —
`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today` —
asserts is absent from a spawned subprocess's env).
canonical: git stash -u && env -u CORE_BUILD_NOW python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -q -m "" -p xdist -n0 && git stash pop — result: pass on a clean tree with CORE_BUILD_NOW unset — run live this session, confirming this failure mode is pre-existing and unrelated to this delivery
```
$ env -u CORE_BUILD_NOW python3 -m pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_related_files.py tests/test_session_waste_metrics.py -q -m "" -p xdist -n0
```
canonical: acceptance: pytest targeted suite — result: pass — run live
this session, pasted output below.

### Before/after — 5 real issues, measured live this session

Corpus: this checkout's own real `*.session.*.log` files for 5 distinct
real `implementation`-role sessions from the 177-session corpus the issue
measured (issues 2314, 2331, 2348, 2382, 2393 — the largest/most-complete
log per issue where more than one exists). **Before** numbers are these
sessions' real, already-executed history (this delivery did not exist
when they ran); this delivery cannot retroactively change them.

```
$ python3 -c "
import sys; sys.path.insert(0, 'scripts')
import session_waste_metrics as sw
paths = [<the 5 session log paths named above>]
print(sw.batch_summary(paths))
for p in paths: print(sw.analyze(p)['hook_refusals']['by_gate'])
"
```

| issue | Bash total | other-share | hook refusals | wall-clock | turns | spawn.py re-reads | own-record re-reads |
|---|---|---|---|---|---|---|---|
| 2314 | 80 | 96.3% | 8 (record-claim-guard=5, heredoc=2, board-gate=1) | 25.0 min | 108 | 0 | 0 |
| 2331 | 76 | 98.7% | 10 (board-gate=5, record-claim-guard=3, heredoc=1, pr-preflight=1) | 34.3 min | 112 | 0 | 3 |
| 2348 | 100 | 65.0% | 7 (heredoc=3, record-claim-guard=2, acceptance-real-run=1, pr-preflight=1) | 37.2 min | 177 | 5 | 2 |
| 2382 | 111 | 78.4% | 0 | n/a (no terminal `result` event — truncated log) | n/a | 17 | 0 |
| 2393 | 129 | 96.1% | 10 (board-gate=4, record-claim-guard=4, heredoc=2) | 38.8 min | 139 | 6 | 2 |
| **rollup** | **496** | **86.3%** | **35 (7.0/session)** | median 35.8min (n=4) | median 125.5 (n=4) | **28** | **7** |

canonical: acceptance: session_waste_metrics.py batch over the 5 real
issue-2314/2331/2348/2382/2393 implementation session logs — result:
pass (tool runs, produces the table above) — run live this session.
Gate totals across the 5 sessions, summed from the per-session `by_gate`
breakdown pasted above: record-claim-guard=14, heredoc-command-refusal-gate=8,
board-gate=10, pr-preflight=2, acceptance-command-real-run-guard=1
(=35 total, matching the rollup row).

**After — what was and was not measured**, stated honestly per the
issue's own "a partial win stated with numbers is acceptable; an
unmeasured claim is not":

- **Measured, live, this session** (hook-refusal mechanism): a real
  nested `claude -p` role session (`CLAUDE_ROLE=implementation`,
  `--plugin-dir on-the-record/`, the real `directive_section_files()`
  output including `hook-contract.md` via `--append-system-prompt`,
  scratch repo `/tmp/otr-2409-livefire`, task: create a file and commit
  it with a real message) produced its first commit as
  `git commit -m "..." -m "..."` (two `-m` flags) with zero `is_error`
  tool_results and `terminal_reason: completed` — the exact
  heredoc-shaped-first-attempt failure `heredoc-command-refusal-gate.sh`'s
  own docstring names (issue #1976), and that the 5-issue sample above
  hit in 3 of the 5 sessions (8 refusals total, see the gate totals just
  above), did not occur.
  canonical: acceptance: live-fire hook-contract commit-shape check —
  result: pass — run live this session (log:
  `/tmp/otr-2409-livefire-session.log`, commit `6d1b0bf` in that scratch
  repo)
- **Measured, live, this session** (exploratory-Bash mechanism): of the
  5 sessions' 496 real historical Bash calls, 104 match the file-hunting
  shape `task-lookup.md`/`known-paths.md` jointly target (`find`, or a
  `docs/issue-<n>`/`$ON_THE_RECORD`-family lookup) — counted live against
  the real command text (regex over each session's actual Bash `input`
  strings), not estimated; per-issue: 2314=23, 2331=32, 2348=16, 2382=6,
  2393=27 (=104, 21% of the 496-call total above).
  `python3 scripts/related_files.py <issue>` was then run live for all 5
  real issue numbers and returned each issue's docs tree plus every
  issue-mentioning file in exactly one call each (docs_tree/issue_mentions
  counts: 2314=6/6, 2331=6/7, 2348=4/19, 2382=3/0, 2393=4/3 — 5 calls
  total, one per issue). This proves the lookup functions correctly
  against real data; it does not by itself prove a full re-run session
  would only make 1 call instead of the ~21-per-session lookup-shaped
  calls made historically (a session might still make follow-up greps
  the lookup's output doesn't answer).
  canonical: acceptance: related_files.py live run against issues
  2314/2331/2348/2382/2393 — result: pass — run live this session
- **NOT measured**: `record-claim-guard.sh` avoidance (rule 2, 14 of the
  35 sampled refusals, the largest covered category) was not
  independently live-fire-tested — doing so needs a deliberately-
  malformed record write to reproduce, and this session's own earlier
  refused draft (see "What did not work") is the closest thing to that
  test this delivery has, but it demonstrates the gate firing correctly,
  not the new prose preventing it (the draft was written before this
  session had internalized its own rule 2 wording).
- **NOT measured**: redundant-read reduction (mechanism 4) — no live
  session re-run measuring fewer `spawn.py`/own-record `Read` calls;
  functional-only (the prose is present and correctly worded, checked by
  the new test assertions).
- **NOT measured**: a corpus-scale "after" re-run (median wall-clock/turns
  across a comparable batch, Acceptance item 5) — spawning 5+ new full
  ~15-minute `implementation`-role sessions against real GitHub issues to
  regenerate this number would itself open real duplicate PRs against a
  shared repo (the exact side-effect issue #2262's own live-fire evidence
  deliberately avoided by using a throwaway scratch repo instead of
  `spawn.py`'s real issue/board/PR machinery) — outside this delivery
  session's safe blast radius without separate operator authorization.

**Honest 5x-target statement**: the operator's target is 15min/67 turns
-> roughly 3min/13 turns. This delivery does not claim to have reached it
or measured a corpus-scale number that could confirm or refute it. What
is measured: two of the three waste-class mechanisms
(hook-refusal-contract, exploratory-Bash lookup) function correctly
against real data drawn from the same 5 real issues the acceptance
section asks for. By the gate-total breakdown above, `hook-contract.md`'s
covered categories (record-claim-guard + heredoc-command-refusal-gate)
account for 22 of the 35 sampled refusals; `board-gate` (out of this
repo's write set) plus the smaller pr-preflight/acceptance-real-run
categories account for the remaining 13. The exploratory-Bash lookup's
covered shape (104 of 496 sampled Bash calls) is 21% of that sample. This
is a partial, honestly-bounded win on the classes this repo can act on —
not a corpus-measured 5x result, and not a claim that the remaining
79%/board-gate share is addressed.

### Targeted test run (pasted output)

```
$ env -u CORE_BUILD_NOW python3 -m pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_related_files.py tests/test_session_waste_metrics.py -q -m "" -p xdist -n0
............s........................................................... [ 90%]
........                                                                 [100%]
79 passed, 1 skipped in 36.27s
```
canonical: acceptance: pytest targeted suite — result: pass — run live
this session (79 passed, 1 skipped, matching the pasted summary count).

### Full-suite comparison — not run; reason stated

A full `-m "not slow"` run was attempted for the broader regression check
`docs/issue-2211`/`docs/issue-2262`'s records both did. This host's root
filesystem hit its real capacity twice while attempting it this session
(`df -h /` dropped to 19M then 570M then 740M free on a 916G volume,
100% used, shared across many concurrent sessions' `/tmp/claude-1000`
work — not this delivery's own files, `du -sh /tmp/claude-1000` showed
10G there against 869G used overall).
canonical: df -h / — result: 740M free, 100% used — run live this
session, after killing one of this session's own background subprocess-
heavy test runs to recover from an earlier 19M-free state
Repeating a ~500s+ subprocess/git-clone-heavy full-suite run risked
tipping a shared, already-saturated disk into failure for other
concurrent sessions on the same host — a real, observed resource
constraint, not a convenience skip. In its place: `tests/test_spawn_observation_recovery.py`
(the largest pre-existing suite touched only incidentally by including it
in an early combined run, not part of this delivery's `code_under_review`)
was spot-checked in isolation for the one failure that combined run
surfaced —
`Watchdog::test_delegation_phrasing_signal` — and confirmed unrelated:
canonical: git worktree add --detach /tmp/otr-2409-baseline-check 92de5808 && cd /tmp/otr-2409-baseline-check && env -u CORE_BUILD_NOW python3 -m pytest tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal -q -m "" -p xdist -n0 — result: fails identically on 92de5808 (the parent commit, before this delivery) — run live this session, worktree removed after
This delivery's own targeted suite above is the acceptance evidence of
record; the full-suite regression comparison precedent set — not
performed this session, stated honestly rather than fabricated.

## What was NOT touched

Per the issue's explicit instruction to state this: no verification,
record, or observer step was removed or thinned. Untouched: the
issue→spawn→PR flow, both observer roles (conformance-review,
execution-observation), verify-at-landing evidence requirements,
consult-trace. Untouched code: `on-the-record/hooks/pretooluse_dispatcher.py`,
`hooks.json`, and all 20 individual gate scripts (`record-claim-guard.sh`,
`heredoc-command-refusal-gate.sh`, etc.) — every gate's actual strictness
and behavior is byte-identical to before this delivery.
canonical: git status --short on-the-record/hooks/ — result: pass — run
live this session, empty output (no changes to any gate script)
`hook-contract.md` only states their existing rules earlier, it does not
loosen or tighten any of them. Untouched: `DEFAULT_SESSION_MAX_TURNS`,
the existing `_COMPLETION_PROSE`/`_LANDING_BATCHING_PROSE`/
`_REPO_DISCOVERY_PROSE`/`_KNOWN_PATHS_PROSE`/`_SKILL_CHECK_PROSE`/
`_SKILL_VERDICT_PROSE` constants (only `_TURN_BUDGET_PROSE` gained an
appended paragraph; every other existing constant is byte-identical).
canonical: git diff f9f8041f^ f9f8041f -- directive_assembly.py
Also untouched: `write_record_skeleton()`, the record-skeleton content,
and the 2,048B stdin directive-overhead budget (new content rides
`--append-system-prompt` like `known-paths.md` already does, not the
stdin preamble that budget measures). Untouched: `board-gate` and any
other tokenmaxxxer-core-owned mechanism — out of this repo's write set
(see Open findings).

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: extends one
already-established mechanism (`directive_section_files()`/materialize/
`--append-system-prompt`, issues #2185/#2211/#2262/#2204) with two more
prose constants and two standalone scripts each under 150 lines — not a
new multi-module structure decision.
skill-verdict: implementation-complexity-coupling-management — not-applicable:
no coupling/cohesion metric crossed a threshold; `scripts/related_files.py`
and `scripts/session_waste_metrics.py` are new standalone modules with no
caller into them from `spawn.py`/`directive_assembly.py` (they are
session-invoked CLIs, matching `scripts/behavior_metrics.py`'s existing
shape), and `session_waste_metrics.py` importing `trajectory_analyzer` is
a one-directional reuse of an existing public module, not a new
cross-module coupling direction.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern indirection was introduced or considered; both new scripts
are direct function-per-concern modules matching `behavior_metrics.py`'s
existing precedent shape.
skill-verdict: implementation-performance-data-structure-choice — not-applicable:
no perf-cliff-prone data-structure/algorithm/communication-scheme choice
was in play; `related_files.py` and `session_waste_metrics.py` are O(n)
single-pass classifiers over already-small inputs (one `git grep`/`git
ls-files` call, one session log's event list).
skill-verdict: diagnose-first — applied: invoked; before writing any
mechanism, read the real `pretooluse_dispatcher.py` GATES list and gate
scripts to find which refusals actually recur (not guessed), grepped the
real 177-session corpus for the true refusal-line shape and for the true
`board-gate` non-existence-in-this-repo finding, and measured live
Bash-call classifications on 5 real sessions before writing any prose —
the diagnose-before-act discipline this skill exists to force, applied to
an issue that is itself a "speed something up" request.
other mounted skills: not triggered (work-in-english — applied
implicitly throughout: this record, commit message, and code comments are
in English, while the pre-existing Korean directive-fragment convention
in `directive_assembly.py`'s `_*_PROSE` constants was matched for the two
new constants, same precedent issue #2262's record already set).
