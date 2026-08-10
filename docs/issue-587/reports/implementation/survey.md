# Issue #587 — implementation current-state survey (phase 1)

Skip condition: neither scout skip condition applies wholesale — but the design
decisions themselves were already resolved in the approved architecture proposal
(`docs/issue-587/proposals/architecture.md`, PR #589, `APPROVE issue-587/architecture`).
This survey covers only what implementation needs freshly verified before coding:
the exact record shape it reads and the exact contract file it edits. No new
design decision is open — the interface shape (return dict fields, template
string, idempotency lookup) is spelled out in the architecture doc's Decision
section 1 and Hand-off. Scout's product-facing sweep is not triggered: this is
wiring against an already-frozen internal contract, not a product-shaped surface.

## Write surfaces

### 1. gates/remediation_spawn.py (new file, does not exist yet)

Sibling to `gates/spawn_coverage.py` / `gates/closure_sweep.py`: plain Python,
`from __future__ import annotations`, injectable pure function + thin CLI, no
new dependency. `spawn.py` itself is out of this proposal's write set —
confirmed against architecture's `files:` list, which does not include
`spawn.py`; only its section 2 discusses wiring, marked "implementation's to
place, not re-designed here" but that wiring is not requested by this issue's
step-2 instructions, which name only the generator, its test, and the run.md
step.

Record shape it reads (written by `on-the-record/hooks/delegated-judgment-gate.sh`'s
reject-path, one docs/issue-<n>/decisions/remediation-<seq>.md per routed
finding):

```
---
finding_source: docs/issue-<n>/decisions/auto-<seq>.md
routed_to: <role>
target_path: <path>
required_fix: <text>
contradicting_role: <role>
round: <int>
status: open | escalated
timestamp: <rfc3339>
---
```

`status: resolved` is not written by the gate today (only `open`/`escalated` —
confirmed by reading the gate's full reject-path write); the generator still
excludes anything not `status: open` per the architecture doc, which is
forward compatible if a future gate ever marks a record resolved.

### 2. gates/test_remediation_spawn.py (new file, does not exist yet)

Sibling test module, same style used across `gates/test_*.py`
(plain `assert`, functions named `test_*`, `tmp_path`-based, no network).
Confirmed via `gates/test_closure_sweep.py` shape (injectable pure function
tested with constructed dicts/tmp dirs).

### 3. on-the-record/commands/run.md (edit)

Orchestrator loop step 3 ("누구를 깨울지" — the board-read-then-decide step) is
the step the architecture doc says the new contract step must precede. The
edit adds one step between board-read and the free-judgment routing
paragraph: when the generator names a pending task for the issue in scope,
launch it via `spawn.py` verbatim and report — never re-derive routing.
The architecture hand-off defers the exact `spawn.py` call-site signature to
implementation, but `spawn.py` itself is outside this proposal's write set,
so the run.md step instructs the orchestrator to pass the generator's
`role`/`task` output straight through to the existing `spawn.py <role>
"<task>" --issue <n> -C <repo>` invocation form (no new spawn.py flag
needed) — a same-turn interface note, not a design change, since the CLI
shape is unchanged and only the source of `<role>`/`<task>` moves from
orchestrator prose to the generator's output.

## Idempotency lookup

`git log`/`gh pr list` reused per the architecture doc, matching the
`Proposal:` trailer convention already used by warrant proposals in this
repo's own git log. Concretely: `gh pr list --json headRefName,body`
filtered on the `Remediation: <remediation_path>` trailer text, plus a local
branch-name check for `issue-<n>/<role>`, since a spawned-but-not-yet-PR'd
branch also counts as already-launched.

## No new state store

Confirmed: everything read (remediation-*.md records) is already written by
the gate; everything checked for idempotency (branches, PRs) already exists
via git/gh. No new file, table, or marker is introduced.
