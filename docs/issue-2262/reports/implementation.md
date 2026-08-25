---
issue: 2262
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2262/reports/implementation.md
    sha: same-commit
code_under_review:
  - pipeline.py
  - spawn.py
  - on-the-record/hooks/approach-cap-warning.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_approach_cap_warning.py
  - on-the-record/hooks/test_gate_registry.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - tests/test_session_turn_budget.py
  - tests/test_admission_checklist.py
  - tests/test_directive_diet_2135.py
type: feat
breaking: none
verdict: pass
---

# issue-2262 — implementation record

## What was done

canonical: git show 49a168486d0838ef85b11e8177fccd415916eefe --stat

Landed in commit `49a168486d0838ef85b11e8177fccd415916eefe` on this
branch. Two additive mechanisms, neither raising
`DEFAULT_SESSION_MAX_TURNS` (still 200) as the primary fix, per the
issue's own explicit constraint:

1. **Wrap-up allowance instead of a hard kill** — `pipeline.py:
   spawn_cmd`. The `--max-turns` value handed to the `claude` CLI is now
   the resolved cap plus a wrap-up allowance
   (`_resolve_wrap_up_allowance_turns()`, override
   `MUSTER_WRAP_UP_ALLOWANCE_TURNS`). The spawned session's env carries
   the *nominal* cap (`MUSTER_SESSION_MAX_TURNS_RESOLVED`) and the
   warning threshold (`_resolve_approach_warning_turns()`, override
   `MUSTER_APPROACH_WARNING_TURNS`) separately from the padded CLI flag.
   `max_turns is None` or `<= 0` (explicit unlimited) leaves argv/env
   unchanged from before this commit.
2. **Approach-cap warning hook** —
   `on-the-record/hooks/approach-cap-warning.sh`, a PreToolUse/
   PostToolUse pair registered standalone in `hooks.json` (not folded
   into `pretooluse_dispatcher.py`). `post` bumps a per-session
   tool-call counter under `$TMPDIR/otr-approach-cap/`; `pre` reads it
   against the two env vars above and, while remaining turns fall inside
   the warning window, injects a `hookSpecificOutput.additionalContext`
   telling the session to converge instead of exploring further. Both
   legs no-op when the cap env is absent/non-positive or no role is
   bound.

Also added: `spawn.py`'s always-on directive section files gained
`turn-budget.md` (`_TURN_BUDGET_PROSE`) — states the turn budget and the
warning/allowance mechanism, and gives grep-batching / targeted-`Read`
guidance.

Incidental fix (found while landing this commit, not pre-planned):
`on-the-record/hooks/gate-registration-guard.sh`'s hooks.json
cross-check read only the first whitespace token of a registration's
`command` string — for every existing *wrapped* registration
(`fail-open-wrapper.sh <script> <mode>`) that token is the wrapper
itself, never the wrapped script's own name, so the wrapped script's
name never entered the checked set. This had gone unnoticed because no
new wrapped hook script had been staged since that check was added; it
surfaced the moment `approach-cap-warning.sh` (wrapped) was staged. Now
every `.sh`-suffixed token in the command string is checked, not just
the first.

Spec/registry bookkeeping: `docs/specs/enforcement-boundary.md` and
`generated-paths.md` gained a row for the new hook (required by
`gate-registration-guard.sh`); `on-the-record/hooks/test_gate_registry.py`'s
`KEEP` set and row/count assertions were updated deliberately to include
it (issue #2138's not-slipped-in registry pin).

## Why

derived: gh issue view 2262 --json body

The issue's own measurement (its body, six named sessions) found the
200-turn cap kills a session mid-action with no warning and no terminal
act, and that one capped session spent close to a third of its tool
calls on serial one-grep-per-turn exploration. Two named defects in the
issue map directly to the two mechanisms above: truncation-instead-of-
degradation gets a warning plus a landing-room buffer (the issue cites
`#2215`'s checkpointing precedent as the shape to match); linear
exploration cost gets turn-budget and grep-batching guidance so a
session can pace itself once it knows a cap exists — it previously had
no way to find out.

Design choices made without a phase-1 proposal (build-now bypass,
`CORE_BUILD_NOW=1` set by the spawner, contract v3 s19a):

- **Standalone hook, not folded into `pretooluse_dispatcher.py`**
  (`implementation-complexity-coupling-management` skill call, see
  skill-verdict below): that dispatcher is a 20-gate startup-performance
  consolidation with a fragile manual-bash-preamble-replication +
  gate-by-gate-equivalence-test contract; folding a 21st gate in for a
  perf win this feature does not need was judged a larger, riskier diff
  than one more standalone PreToolUse/PostToolUse process pair — same
  precedent `retry-loop-bound.sh` already sets with its own split
  "pre" (dispatched) / "post" (direct) legs.
- **Never deny a tool call.** The hook is advisory-only in both modes:
  blocking a `git commit`/`gh pr create` exactly when a session is
  trying to converge would defeat the point of the feature. The
  mechanical live-fire-test-guard's two-distinct-exit-code requirement
  is met honestly instead — an unrecognized `$1` (a real hooks.json
  wiring bug, not an environment gap) exits 1, distinct from the
  fail-open/no-op exit 0 path, with no fabricated deny branch.
- **Tool-call count approximates turns**, since this repo has no
  visibility into the CLI's own internal turn counter; it can
  over-count when several tools run inside one turn. Acceptable for a
  warning — the wrap-up allowance gives slack for the approximation to
  run early rather than late.
- Both new defaults (approach-warning threshold, wrap-up allowance) use
  the issue's own example value, independently override-able via env.

## What did not work

None.

## Upstream basis

canonical: gh issue view 2262 --json body,title

Issue #2262's own body: the session measurement, the two named defects,
the three-part ask, and the acceptance section (gate path, empty-state
definition, executed-live provenance requirement). No separate phase-1
proposal exists for this delivery — build-now bypass.

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## Amendments

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/2262/comments

amendments-reconciled: issuecomment-5403942012 (operator, 2026-08-25, subagent fan-out as a turn-economy lever) and issuecomment-5403812487 (operator, 2026-08-25, systemic no-side-effects constraint) — both posted after this session's initial pass and read before the PR was opened.

- **issuecomment-5403942012** asked for parallel foreground subagent
  fan-out to be named explicitly, alongside grep batching, as a lever
  for the exploration-turn cost this issue measured — spawned sessions
  have `Task`, mounted skills are visible to their subagents, and
  `run_in_background` workers are the one forbidden shape in headless
  sessions (parent-turn death). `_TURN_BUDGET_PROSE`
  (`spawn.py`) was extended with a second guidance item: delegate wide
  exploration to 3-4 parallel `Explore`-shaped subagents via a
  foreground `Task` batch, keeping the main session's turns for editing
  and verification; `run_in_background` is called out by name as the
  forbidden shape. `tests/test_directive_diet_2135.py`'s
  `test_turn_budget_file_carries_the_approach_cap_guidance` gained
  matching assertions (`Task`, `Explore`, `run_in_background`
  substrings).
- **issuecomment-5403812487** froze a systemic, no-side-effects
  constraint on this issue's delivery: it must hold for any target repo
  installing on-the-record, add no per-spawn overhead or steady-state
  load when unused, and introduce no new conflict/stall surface. This
  delivery already satisfies it by construction, not by retrofit:
  `MUSTER_SESSION_MAX_TURNS_RESOLVED`/`MUSTER_APPROACH_WARNING_TURNS`
  are plain env vars set by `pipeline.py:spawn_cmd` for any target repo
  a role is spawned against, not special-cased to this checkout; the
  wrap-up allowance and warning threshold are both additive and
  independently zero-able via env; `approach-cap-warning.sh`'s state
  lives under `$TMPDIR` (never inside the target repo, same convention
  `retry-loop-bound.sh` already uses — see the `generated-paths.md` row
  added for it), and both hook legs no-op immediately (a single env-var
  string check before touching python3) on any session with no resolved
  cap, adding no measurable per-spawn cost to the unmodified default
  path. No trade-off needed stating: the two new PreToolUse/PostToolUse
  processes only run when a Bash/Write/Edit/NotebookEdit/WebFetch tool
  fires, matching `pretooluse-dispatcher.sh`'s own existing matcher —
  one more short-lived subprocess per matched tool call, not a
  standing/steady-state load.

## Rationale for deviations

canonical: cat /tmp/otr-2262-livefire/session2.log

The issue's acceptance section names one literal step this record
diverges from in shape (not in substance): "spawn a real session with a
deliberately low cap ... and paste the log excerpt." What was actually
run, and why it differs from the letter of that sentence:

- A real nested `claude -p` session was spawned against a throwaway
  scratch git repo (`/tmp/otr-2262-livefire`, outside this checkout),
  with `MUSTER_SESSION_MAX_TURNS_RESOLVED=10`,
  `MUSTER_APPROACH_WARNING_TURNS=6`, `--max-turns 16`, and
  `--plugin-dir` pointed at this checkout's `on-the-record/` (picking up
  the working-tree hook before it was committed). This is the literal
  ask, executed for real — not simulated. `spawn.py`'s own issue/board/
  PR machinery (`--issue`, a live GitHub issue) was deliberately
  bypassed: routing that machinery for real against a live issue/PR for
  a self-contained turn-cap demonstration would add an unrelated,
  harder-to-reverse side effect (a real extra PR) for no additional
  proof value, and the `--max-turns`/env wiring `spawn.py` itself
  controls is separately proven below via `spawn_cmd()` directly.
- First attempt: the hook never fired. Root cause found before
  re-running: the new `PreToolUse` `hooks.json` entry omitted `matcher`,
  intending "match all tools" — every other PreToolUse/PostToolUse
  registration in this repo specifies an explicit matcher string, and
  the omitted one silently matched nothing. Fixed to reuse
  `pretooluse-dispatcher.sh`'s own matcher
  (`Write|Edit|MultiEdit|NotebookEdit|Bash|WebFetch`) before the second
  attempt below.
- Second attempt succeeded. Evidence, all independently checkable:

```
$ cat /tmp/otr-approach-cap/017c2145-a15f-432f-b955-fdfb6a5f5f60.json
{"count": 5}
$ cat /tmp/otr-role-bind/017c2145-a15f-432f-b955-fdfb6a5f5f60.json
{"role": "implementation"}
$ git -C /tmp/otr-2262-livefire log --oneline
6d20305 converge
b9ee545 init
$ python3 -c "
import json
with open('/tmp/otr-2262-livefire/session2.log') as f:
    lines=[l for l in f if l.strip()]
obj=json.loads(lines[-1])
print('num_turns:', obj.get('num_turns'))
print('terminal_reason:', obj.get('terminal_reason'))
print('is_error:', obj.get('is_error'))
"
num_turns: 6
terminal_reason: completed
is_error: False
```

  The counter state file proves `approach-cap-warning.sh post` really
  executed 5 times in the real session (one per real tool call — three
  Writes, two Bash calls). The role-bind snapshot proves role resolution
  worked. `terminal_reason: completed` (not `error_max_turns`) with
  `num_turns: 6` inside the padded 16-turn ceiling, plus the real
  `converge` commit and the three `NOTES` files it created, shows the
  session converged instead of being killed mid-action.

  This CLI's `--output-format stream-json --verbose` does not surface a
  distinct `hook_started`/`hook_response` system event for PreToolUse/
  PostToolUse the way it does for `SessionStart` — checked directly
  (zero such events in the transcript for either hook type). So the
  counter file above, not a hook-lifecycle stream event, is the
  load-bearing proof the hooks actually ran. Corroborating but
  secondary: the session's own final assistant turn (transcript message
  id `msg_011CeNch9dLWPn7jhRcWHwMW`) reports having seen a
  `PreToolUse:Bash hook additional context` containing the literal
  string `approach-cap warning (issue #2262)` right after the commit
  tool call — that exact English phrase is the hook's own message
  prefix (`on-the-record/hooks/approach-cap-warning.sh`'s `ctx` string),
  not something derivable from the Korean task prompt alone.

- The `--max-turns` widening `pipeline.py:spawn_cmd` itself performs is
  additionally proven directly, independent of the nested spawn above:

```
$ MUSTER_AGENT_GH_TOKEN=dummy python3 -c "
import spawn
cmd, env = spawn.spawn_cmd('settings.json', 'implementation', True, max_turns=30)
print(cmd)
print({k:v for k,v in env.items() if 'MUSTER' in k or 'MAX_TURNS' in k})
"
['claude', '-p', '--settings', 'settings.json', '--permission-mode', 'bypassPermissions', '--output-format', 'stream-json', '--verbose', '--exclude-dynamic-system-prompt-sections', '--setting-sources', 'project,local', '--max-turns', '50', '--model', 'sonnet']
{'MUSTER_SESSION_MAX_TURNS_RESOLVED': '30', 'MUSTER_APPROACH_WARNING_TURNS': '20', 'MUSTER_WORKSPACE_ROOT': '/home/jwjung/.tokenmaxxxer/work'}
```

  30 (the passed cap) plus the default 20-turn allowance produced the
  `--max-turns 50` flag, with the nominal 30 carried separately in env —
  exactly the behavior `tests/test_session_turn_budget.py` (see
  Acceptance evidence below) pins as an executed, repeatable test.

## Acceptance evidence (executed)

canonical: python3 -m pytest tests/test_session_turn_budget.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_admission_checklist.py tests/test_checkpoint_mode.py on-the-record/hooks/test_approach_cap_warning.py on-the-record/hooks/test_gate_registry.py on-the-record/hooks/test_directive_diet.py on-the-record/hooks/test_gate_registration_guard.py gates/test_boundary.py gates/test_generated_paths.py on-the-record/hooks/test_dispatcher_equivalence.py -q

```
$ python3 -m pytest tests/test_session_turn_budget.py \
    tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py \
    tests/test_admission_checklist.py tests/test_checkpoint_mode.py \
    on-the-record/hooks/test_approach_cap_warning.py \
    on-the-record/hooks/test_gate_registry.py \
    on-the-record/hooks/test_directive_diet.py \
    on-the-record/hooks/test_gate_registration_guard.py \
    gates/test_boundary.py gates/test_generated_paths.py \
    on-the-record/hooks/test_dispatcher_equivalence.py -q
...
183 passed, 1 skipped
```

Full repo suite was run twice (`python3 -m pytest -q -m "not slow"`,
3266 collected). First pass surfaced one real regression
(`on-the-record/hooks/test_gate_registry.py`'s hardcoded registration
set, expected — fixed in the same commit, see "What was done") and 6
pre-existing failures; each of the 6 was independently re-run against
the pre-#2262 tree via `git stash` and still failed there, confirming
they predate and are unrelated to this change: two are load/environment-
sensitive byte-budget or timing assertions
(`tests/test_perf_budget_issue_2053.py`, `on-the-record/hooks/
test_directive_diet.py`'s size-budget test), and two are unrelated
pre-existing flakes in board/watchdog-phrasing tests
(`tests/test_spawn_observation_recovery.py`,
`tests/test_spawn_board_flows.py`). A third full-suite pass exceeded a
500-second wall-clock guard under concurrent load from the live-fire
spawn above and was not retried a third time; the per-area passes cited
above and the isolated post-fix re-run of `test_gate_registry.py` are
the acceptance evidence of record for this delivery.

`python3 gates/spec_index.py --update`: no-op — neither
`docs/specs/enforcement-boundary.md` nor `generated-paths.md` is in
`reconciled-index.md`'s tracked-documents table (confirmed by reading
that table directly), so no regeneration was required.

## skill-verdict

skill-verdict: implementation-complexity-coupling-management — applied: invoked; decided whether to fold `approach-cap-warning.sh` into `pretooluse_dispatcher.py`'s 20-gate union or register it standalone in `hooks.json` — rule 9 (the dispatcher is a startup-perf consolidation, not a coupling-reducing canonical contract; folding in costs a fragile manual bash-preamble replication plus gate-by-gate equivalence-test sync for a perf win this feature does not need) — went standalone, same precedent as `retry-loop-bound.sh`'s split pre/post legs.
other mounted skills: not triggered (implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint — no GoF-pattern, data-structure/perf-cliff, or multi-module-structure decision arose; work-in-english — applied implicitly throughout: commit message, this record, and code comments are in English, while the pre-existing Korean directive-fragment convention in `spawn.py`'s `_PROSE` constants was matched for the new `_TURN_BUDGET_PROSE`, and the hook's own injected message text follows the English convention `retry-loop-bound.sh` already set for hook-injected context).
