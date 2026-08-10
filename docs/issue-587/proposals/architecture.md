# Issue #587 — architecture proposal (phase 1)

status: proposed
files:
  - gates/remediation_spawn.py
  - gates/test_remediation_spawn.py
  - on-the-record/commands/run.md
  - docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md (phase 2, test)

## Context

Rejections already route mechanically to a `docs/issue-<n>/decisions/remediation-<seq>.md` record
(`on-the-record/hooks/delegated-judgment-gate.sh`, #573 §7), with round counting and escalation
already derived solely from that record family (#573 §8, no new state — see survey.md). The one
step still done by a human is turning a `status: open` remediation record into an actual spawned
role session: the orchestrator (per `on-the-record/commands/run.md`) reads the routing comment and
writes its own task prose for `spawn.py <role> "<task>"`. That is exactly the judgment call #587
asks on-the-record to broker mechanically instead, plus an end-to-end proof that the whole loop —
issue → judged PR → verdicts → rejection → remediation spawn → remediation PR → re-judgment →
closure — actually fires all five §12 timeline events on real git surface.

## Decision

### 1. `gates/remediation_spawn.py` — finding → spawn-task generator (zero-install)

New module in the same family as `gates/spawn_coverage.py`/`gates/closure_sweep.py` (plain
Python, no new dependency, invoked by `spawn.py` and by the orchestrator loop, never installed
separately). One function does the whole job:

```python
def pending_remediation_tasks(root: Path, issue: int) -> list[dict]:
    """Read docs/issue-<n>/decisions/remediation-*.md, return one dict per
    status: open record: {role, task, remediation_path, round}."""
```

`task` is built by a fixed template over the record's own fields — never free-authored:

```
f"Remediation round {round}: fix `{target_path}` — {required_fix} "
f"(routed from `{remediation_path}`, finding: `{finding_source}`)"
```

`role` is `routed_to` verbatim. A record whose `status` is not `open` (i.e. `resolved` or
`escalated`) is excluded — `escalated` records are the operator's to see (they already reach the
operator via the existing escalation comment path, #573 §8), never auto-spawned. A repo with zero
`remediation-*.md` files, or zero `status: open` among them, returns `[]` — empty is not an error,
matching the acceptance criterion's explicit "no findings -> no tasks" requirement.

**Idempotency (no new state store):** before returning a task, check whether it was already
launched by looking for an existing `issue-<n>/<role>` branch or open PR carrying a
`Remediation: <remediation_path>` trailer (same trailer convention this repo's warrant proposals
already use for `Proposal:` — `git log --grep`/`gh pr list` are the lookup, not a new file). A
round already spawned (branch or PR exists) is excluded from `pending_remediation_tasks`'s
output — this reuses git/GitHub as the state store that already exists, per the "no new state
store" requirement, rather than adding a marker file.

### 2. `spawn.py` wiring

`spawn.py` gains a thin call site (implementation's to place, not re-designed here): given
`--issue <n> -C <repo>`, before falling through to manual role/task args, call
`remediation_spawn.pending_remediation_tasks` and, if any are pending, spawn each with the
generated `role`/`task` verbatim and `Remediation: <remediation_path>` embedded in the branch's
first commit trailer for the idempotency check above to find later. This is additive to the
existing manual `spawn.py <role> <task>` path, not a replacement — a human can still spawn
anything by hand; the generator only removes the *routing* judgment call for remediation-specific
launches.

### 3. `run.md` contract step

New step in `on-the-record/commands/run.md`'s orchestrator loop, ordered right after the existing
board-read step and before any manual "decide what to spawn next" judgment: **when
`remediation_spawn.pending_remediation_tasks` names a pending task for the issue in scope, launch
it via `spawn.py --issue <n> -C <repo>` verbatim and report — never re-derive routing, never
re-write the task text, never decide by reading the PR/issue comments yourself.** This is the
literal contract change #587 asks for: routing judgment moved from orchestrator prose to the
generator's fixed template.

### 4. E2E fixture-target-repo scenario (design, phase-2 executes it)

A disposable fixture repo (created fresh under a temp dir per test run, torn down after — not this
repo's own board, matching the acceptance criterion) that:

1. Has a minimal `roles/*.json` set (two roles: one that owns the axis under judgment, one that
   owns the file the rejecting finding names) and an `approvers.md`.
2. Opens a candidate PR, drives the gate to a `reject` verdict with a routable `finding` — fires
   timeline events 1-2 (`PR opened under judgment`, `Verdict synthesized`).
3. Confirms `remediation_spawn.pending_remediation_tasks` returns exactly one task derived from the
   resulting `remediation-1.md`, and that the routing comments/timeline event 3 (`Remediation
   routed`) are present.
4. Drives a second PR (simulating the remediation session's fix) to `approve`, and merges it —
   fires timeline event 4 (`Remediation PR merged`) via the existing `spawn.py watch` merge
   detection.
5. Re-runs the gate on the original candidate to confirm closure; separately, a second fixture path
   drives 4 rejection rounds to confirm `status: escalated` fires timeline event 5 (`Escalation to
   operator`).

Each step's `gh` calls target the fixture repo (not this one) via `-C <fixture-path>`, matching
existing test conventions in `on-the-record/hooks/test_delegated_judgment_gate.py`. The e2e script
lives at `gates/test_remediation_e2e.py` (or an implementation-chosen equivalent path within
`gates/`), asserting on the actual PR/issue comment bodies and `remediation-*.md`/`auto-*.md`
record contents, not mocks.

## C4 — container/boundary view

```
+-----------------------------------------------------------------------+
|                      Target repo (fixture or real)                    |
|                                                                        |
|  [Candidate PR] --judged by-->  [delegated-judgment-gate.sh]          |
|                                        |                               |
|                                        | writes (reject + finding)     |
|                                        v                               |
|                          [remediation-<seq>.md]  (status: open)       |
|                                        |                               |
|                                        | read-only                     |
|                                        v                               |
|                     [gates/remediation_spawn.py]  <-- NEW              |
|                    (template over record fields only;                 |
|                     idempotency via git log/gh pr list)                |
|                                        |                               |
|                                        | {role, task, remediation_path}|
|                                        v                               |
|                              [spawn.py --issue n]                      |
|                                        |                               |
|                                        v                               |
|                        [issue-<n>/<routed_to> role session]           |
|                          (per on-the-record/commands/run.md's          |
|                           new "launch and report" step)                |
|                                        |                               |
|                                        v                               |
|                          [Remediation PR]  --> re-judged by gate       |
|                                        |                               |
|                                        v                               |
|                    [Issue timeline: 5 firing events, #573 §12]        |
+-----------------------------------------------------------------------+
```

Dependency direction: `remediation_spawn.py` depends only on the record files the gate already
writes (read-only) and on `git`/`gh` for idempotency lookups — it never depends on `spawn.py`
internals, and `spawn.py` depends on `remediation_spawn.py`'s output shape, not vice versa. No
component gains a new outbound dependency the gate/`spawn.py` boundary didn't already have.

## Consequences

- Positive: removes the one manual judgment call #587 names; task text is now always traceable to
  a specific record field, closing the "never free-authored" acceptance bar directly.
- Positive: zero new state — idempotency and round/escalation both ride on records and git/GitHub
  state that already exist, so there's nothing new to keep consistent or garbage-collect.
- Negative: idempotency-by-branch/PR-existence is a `gh`/`git` round-trip per candidate task,
  same cost class as every other `gh`-call-per-hook-run this repo already accepts (survey.md).
- Negative: the fixture e2e is comparatively expensive to run (spins up a real disposable repo);
  scoped to phase-2 execution, not part of the fast unit-test path.

## Alternatives considered

- **A dedicated remediation-routing registry/queue file**, decoupled from `remediation-*.md`
  itself. Rejected: #573's own scout-brief already rejected this shape for the routing record
  itself; extending that rejection here keeps one source of truth instead of two files that could
  drift (open task queue vs. record status).
- **Have the gate spawn directly**, skipping a separate generator module. Rejected: the gate's
  `write_scope` is `on-the-record/hooks/*.sh` per its own role definition — spawning a role session
  is an orchestration action, not a judgment write, and keeping it in `gates/` (already the home of
  `spawn_coverage.py`/`closure_sweep.py`, both orchestration-adjacent, non-judgment code) keeps the
  gate itself narrowly scoped to writing verdicts and routing records.
- **Free-text task authored by `remediation_spawn.py` beyond the fixed template** (e.g. summarizing
  multiple pending rounds into one prose paragraph). Rejected: the acceptance criterion is explicit
  that task text must be "derived from the finding record, never free-authored" — a fixed template
  with only field substitution is the only shape that satisfies that literally and stays testable
  by exact-string assertion in the unit test.

## Hand-off

Interface shape for `pending_remediation_tasks`'s exact return dict / `spawn.py` call-site
signature is implementation's to finalize against real argument-parsing conventions already in
`spawn.py`. No performance budget implicated beyond the existing per-`gh`-call cost class already
accepted throughout this gate family. e2e fixture-repo teardown mechanics (temp dir lifecycle) are
implementation/execution-observation's to build; this proposal fixes only the five events it must
observe and the boundary it must not cross (a real, disposable fixture repo, never this repo's own
board).
