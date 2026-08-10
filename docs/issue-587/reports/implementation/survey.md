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

## Round 2 — timeline event 4 ("Remediation PR merged")

Remediation round, operator-relayed 2026-08-10. Basis: the step-3
execution-observation record
(`docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md`,
per-event table, row 4) — empirically drove a real fixture merge and grepped
the shipped surface; event 4 does not fire anywhere in tracked code. Design
decision already fixed by the architecture doc's §12 hand-off text ("this
phase does not invent a new merge-detection channel, it reuses the one
already observed posting `[watch] ... session-end:` style messages") —
implementation's job here is picking the concrete integration point inside
that existing channel, which is a real open decision (not covered by the
architecture doc's own write set, which lists only `remediation_spawn.py`/
its test/`run.md`), so this is not a skip-condition round.

### 1. `on-the-record/hooks/delegated-judgment-gate.sh` (edit)

Reject-path write, re-read at
`on-the-record/hooks/delegated-judgment-gate.sh` lines 330-410, writes
`remediation-<seq>.md` with `finding_source`, `routed_to`, `target_path`,
`required_fix`, `contradicting_role`, `round`, `status`, `timestamp` — no
field names the *candidate* PR (`pr_ref`, already in scope as a local
variable at that point in the script, used to post the routing comment).
#573 §12's event-4 format ("Remediation merged: PR #<m> resolves round <r>
of PR #<n>") needs `<n>` — the candidate PR — at merge-detection time, which
runs in a different process/invocation than the reject-path write. Confirmed
by reading the full reject-path block: no existing record field can supply
it without a new field.

### 2. `spawn.py` (edit)

Confirmed via read: `_pr_open_or_merged_for_branch` (spawn.py:1082) already
collapses OPEN and MERGED into one "delivered" signal for the
already-delivered idempotency check — reused as-is by
`gates/remediation_spawn.py`'s idempotency lookup (round 1 above) — but
nothing in spawn.py distinguishes MERGED specifically, and no existing
call site scans `remediation-*.md status: open` records the way
`_roster_reconcile_unreported` (spawn.py, `RosterReconcileUnreported` test
class) scans the workspace index for unacked session-ends. That function is
the closest existing shape: a periodic/on-demand sweep, idempotent via a
fixed comment marker read back through `_issue_comments` before posting
(same pattern `_post_session_end_comment` and `_post_stall_comment` both
use). No sweep over `remediation-*.md` exists today — confirmed by grep,
zero hits for `remediation-` in spawn.py.

### 3. Test file

`test_spawn.py` already carries `PostSessionEndComment` and
`RosterReconcileUnreported` classes covering the two closest analogues
(idempotent comment posting off a marker; a scan-and-report sweep) — the new
test lives in the same file, following the same
setUp/tearDown-monkeypatch-`subprocess.run` style already used throughout
(confirmed: no separate test file per spawn.py function; one file for the
whole module).

## No new state store (round 2)

The candidate-PR field added to `remediation-<seq>.md` is not new state — it
extends a record the gate already writes, the same way `round`/`status`
already do; no new file/table/marker. Idempotency for the merge comment
reuses the fixed-marker read-then-check pattern already in
`_post_session_end_comment`/`_post_stall_comment`, applied to a new marker
string — not a new mechanism.
