---
issue: 2293
role: implementation
loop_state: landed
upstream:
  - path: pipeline.py
    sha: same-commit
code_under_review:
  - pipeline.py
  - spawn.py
  - watchdog.py
  - tests/test_admission_checklist.py
  - tests/test_spawn_gate_wiring.py
type: feat
breaking: none
verdict: pass
---

# issue-2293 — implementation record

## What was done

Build-now delivery (contract v3 s19a, `CORE_BUILD_NOW=1` set by the
spawner) — no phase-1 proposal round.

1. **Admission-time refusal of degenerate/issue-number-shaped tasks**
   (`pipeline.py`): added `_admission_check_degenerate_task(ctx)`, a new
   row in `spawn.py`'s existing `ADMISSION_CHECKS` data table (issue
   #2100 machinery — "adding an item is adding a table row, never new
   gate code"). It refuses admission when the positional `task` is
   bare-numeric, `#<n>`-shaped, or `-<n>`-shaped (`^[#-]?\d+$`) and
   `--issue` was not given, printing the almost-certain intent:
   `task looks like an issue number; did you mean: spawn.py <role> "<task>" --issue <n>`.
   Purely local/deterministic (no gh/network call) — a real refusal, never
   fail-open, and it runs first in the table so it fires before any
   workspace/branch/roster side effect exists.
2. **Explicit override**: `--force-adhoc-task` (new CLI flag, threaded
   through `_spawn_one(..., force_adhoc_task=False)` into the admission
   `ctx`) lets the rare legitimate numeric-task adhoc spawn bypass this
   one row.
3. **`task` now flows into admission `ctx` and into roster entries**:
   `_spawn_one`'s `admission_gate({...})` call gained `"task": task` and
   `"force_adhoc_task": force_adhoc_task`; both roster-registration sites
   (`_early_roster_entry` and the post-fork `roster_register(...)` call)
   gained `"task": task` — needed by both the admission check and the
   watchdog change below.
4. **Adhoc-visibility in watchdog output** (`watchdog.py`,
   `diagnose_health()`): every diagnosis for an entry with `issue is None`
   now gets its `detail` prefixed with `ADHOC task="<first ~8 words>" — `
   (or `ADHOC (no task recorded) — ` when the field is absent/blank), via
   the function's existing single `_diagnosis()` wrapper. This reaches the
   `[poll-report] {key}: {state} — {detail}` line that prints on *every*
   tick regardless of state (HEALTHY included) — the exact line the
   consumer incident showed reporting "HEALTHY" with no hint that the
   session's mission was the string "538". The roster key already carried
   an `adhoc/{role}/{pid}` prefix (pre-existing — see Upstream basis);
   this change adds the missing piece, the task text, to the same line.
5. Tests added to two existing files (no new test files):
   `tests/test_admission_checklist.py` gained an "item 6" section, and
   `tests/test_spawn_gate_wiring.py`'s `DiagnoseHealth` class gained two
   more cases.
   derived: `git diff --stat tests/test_admission_checklist.py tests/test_spawn_gate_wiring.py` (execution results are in the Provenance section below, item 5)

## Why

The consumer incident (issue #2293 body): `spawn.py implementation 538`
meant `--issue 538` but was typed without the flag, so argparse silently
bound `"538"` to the positional `task` and a live agent spawned with that
three-character mission, reported HEALTHY throughout. Root cause named in
the issue: "correctness depended on the caller's flag discipline" — a
cheap admission-time check closes that class of typo.

Design choices, each picked to honor the issue's frozen constraint
("systemic for all consumer sessions, no added overhead/conflict/stall
surfaces, nothing in the consumer tree"):

- Reused the issue #2100 admission-checklist table instead of adding new
  gate machinery — the table is designed for exactly this ("adding an
  item is adding a table row"), so no new stall/conflict surface is
  introduced.
- The check is 100% local (regex + two dict lookups) — no gh/network
  call, so it can never itself become a fail-open/flaky-network class,
  and it costs nothing measurable per spawn.
- Reused `diagnose_health()`'s existing single `_diagnosis()` choke point
  for the watchdog change rather than editing each of its ~6 return
  sites individually or adding a new printed line — one small diff,
  every existing caller/test of `diagnose_health()` still gets a
  well-formed dict with the same keys plus an unconditionally-present
  `detail` (empty prefix for issue-scoped entries).
- Everything lands in this checkout (`on-the-record`'s own `pipeline.py`/
  `spawn.py`/`watchdog.py`/`tests/`) — nothing is written into any
  consumer/target repo's tree.
- The regex (`^[#-]?\d+$`) is deliberately conservative: it matches only a
  task that is *entirely* a number (optionally `#`- or `-`-prefixed), not
  e.g. "3 bugs to fix" or "issue 538" — this avoids refusing legitimate
  free text that merely starts with or contains digits, at the cost of
  not catching every conceivable "issue-number-shaped" phrasing (see Open
  findings). The `-` prefix was added after a before-landing warrant hunt
  (stance: assume the gate just touched is bypassable) reproduced a real
  bypass — see "Before-landing hunt" below.

## Before-landing hunt (issue #2293, warrant protocol)

One background `warrant-hunter` ran before landing (build-now mode has no
phase-1 proposal, so only the before-landing dispatch applies), stance 0
("assume the gate just touched is bypassable — find the bypass"). It
returned a real FINDING: the original regex `^#?\d+$` missed a
negative-shaped task like `-538` — argparse's own "a lone `-<digits>`
token is not treated as an option" special-case let it reach `task`
exactly like the bare `"538"` incident, reaching a live spawn unrefused.
Full record:
`docs/issue-2293/reports/implementation/2026-08-25-hunt-degenerate-task-admission-refusal.md`
(commit `7d65738b`). Fixed in this same commit — regex widened to
`^[#-]?\d+$`, one regression test added
(`test_negative_numeric_task_also_refuses`), re-verified live (Provenance
item 6 below).

## What did not work

`_DEGENERATE_TASK_RE = re.compile(r"^#?\d+$")` (the first version) did
not match a leading-minus numeric task — replaced with
`re.compile(r"^[#-]?\d+$")` after the before-landing hunt reproduced the
gap (see above).

## Upstream basis

- Issue #2293 body (consumer's own diagnosis of the 2026-08-25 incident) —
  the direct basis for both the admission-refusal shape and the
  watchdog-adhoc-visibility ask.
- `pipeline.py`'s `ADMISSION_CHECKS`/`admission_gate()` machinery (issue
  #2100) — the extension point this change adds one row to.
  sha: same-commit (cited path `pipeline.py` lands in this same commit)
- `watchdog.py`'s `diagnose_health()` (issue #782 scope-expansion, issue
  #1966 extension) — the existing single choke point (`_diagnosis()`
  helper) this change extends.
  sha: same-commit (cited path `watchdog.py` lands in this same commit)
- The `adhoc/{role}/{pid}` roster-key convention already existed before
  this issue.
  canonical: `git log -p -1 -S 'adhoc/{role}' -- spawn.py` → commit
  `aeb3167f` ("Agent roster: spawn.py ps / kill, registered per spawn"),
  predates this issue — only the missing task-text piece needed adding.

## Open findings

- The degenerate-task regex (`^[#-]?\d+$`, widened per the before-landing
  hunt above) still does not catch multi-token issue-number phrasings
  such as `"issue 538"` or `"issue-538"` — only a task that is
  bare-numeric, `#`-prefixed, or `-`-prefixed matches. This was a
  deliberate scope choice (see Why) to avoid false-positive refusals on
  legitimate free-text tasks. Resolution path: if a live incident surfaces
  one of these broader shapes, widen `_DEGENERATE_TASK_RE` in
  `pipeline.py` in a follow-up issue; no structural change would be
  needed (same table row, same predicate contract).

## Next steps

None — loop_state is terminal (`landed`).

## Provenance (executed-live, issue #2293 acceptance)

1. Verbatim incident repro — refusal with its suggestion:
   acceptance: `python3 spawn.py implementation 538` — result:
```
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
   acceptance: `cat runs/active.json` (immediately after, same shell) — result:
```
(no roster file)
```

2. Override path admits the same numeric task, whole-table check:
   acceptance: `_admission_check_degenerate_task({'issue': None, 'task': '538', 'force_adhoc_task': True, ...})` and `admission_gate({..., 'force_adhoc_task': True, 'single_phase': True, ...})` — result:
```
degenerate-task check verdict with --force-adhoc-task: True
full admission_gate refused item (None = admitted): None
```
   acceptance: `python3 spawn.py --help | grep -A6 force-adhoc-task` — result:
```
  --force-adhoc-task    spawn: explicit override letting a bare-numeric or
                        '#<n>'-shaped task pass admission without --issue —
                        for the rare legitimate numeric-task adhoc spawn
                        (issue #2293). Without --issue AND without this flag,
                        a numeric-shaped task is refused at admission with a
                        did-you-mean --issue suggestion.
```

3. Adhoc-labeled watchdog line, real `diagnose_health()` on a synthetic
   no-issue entry (task="538"):
   acceptance: `spawn.diagnose_health('adhoc/implementation/12345', entry, state={})` then formatted as the real `[poll-report]` line — result:
```
[poll-report] adhoc/implementation/12345: HEALTHY — ADHOC task="538" — adhoc/implementation/12345: 최근 로그 성장, RUNNING
```

4. Normal spawn (real task text, or real task text + `--issue`) checked
   directly against the new row — both return `True` (admitted, no
   message):
   acceptance: `_admission_check_degenerate_task({'issue': 2293, 'task': 'PR 12 를 리뷰해라', ...})` and the same with `'issue': None` — result:
```
degenerate-task check verdict for a normal issue-scoped spawn: True
degenerate-task check verdict for a normal adhoc (non-numeric) task: True
```

5. Test suites (serial, `-n0`, to avoid unrelated `pytest-xdist` worker
   pollution — see note below). Final numbers below are post-fix (include
   the negative-number regression test added after the before-landing
   hunt):
   acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -n0 -q` — result:
```
86 passed in 3.06s
```
   acceptance: `python3 -m pytest tests/test_admission_checklist.py -n0 -q` — result:
```
30 passed in 10.90s
```
   acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -n0 -q` — result:
```
1 failed, 69 passed in 89.93s
```
   canonical: the one failure, `test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace`,
   was reproduced identically on a clean HEAD via `git stash && python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace -q && git stash pop` — same assertion failure, pre-existing and untouched by this diff.
   acceptance: new admission tests only — `python3 -m pytest tests/test_admission_checklist.py -n0 -q -k "numeric_task or force_adhoc or issue_given_skips or ordinary_task_text or empty_or_missing_task"` — result:
```
7 passed, 23 deselected in 0.08s
```
   acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py::DiagnoseHealth -n0 -q` — result:
```
18 passed in 0.12s
```
   (this class's 18 total includes the 2 new adhoc-visibility cases added
   by this change, alongside the pre-existing HEALTHY/STALLED/DEADLOCKED
   cases.)

6. Before-landing-hunt fix re-verified live, after widening the regex to
   `^[#-]?\d+$`:
   acceptance: `python3 spawn.py implementation -538` (real CLI, this repo's own checkout) — result:
```
[admission] degenerate-task: task '-538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
   acceptance: `cat runs/active.json` (immediately after, same shell) — result:
```
{}
```
   (empty roster — confirms no session was spawned this time, unlike the
   hunter's pre-fix repro which did spawn a live nested session.)

Empty-state parity: existing `ADMISSION_CHECKS`-table tests build a `ctx`
dict without a `"task"` key (pre-existing, unmodified) and still pass —
see the `30 passed` result above (item 5), which includes every
pre-existing test in that file. `ctx.get("task")` defaults to `None` →
`""` → the new row returns `True` immediately, byte-identical to before
this change.
