# Current-state survey (issue #754) — automated problem-resolution composition

Scope: read-only survey of the de-facto diagnose→issue→spawn→verify→merge
loop, and every mechanism today's system offers a role for composing a
resolution to a problem it surfaces itself. No files changed in this pass.

## The loop as it runs today, step by step

derived: `on-the-record/commands/run.md` (`/run`, the orchestrator's own
loop skill)

1. **요구사항 → 이슈** — `on-the-record/commands/run.md`, lines 20-22:
   only the orchestrator, in conversation with the user, drafts and
   registers issues (`gh issue create`); a spawned role session never
   does this. The file states it explicitly: "당신은 대필자다" (you are
   a ghostwriter [for the user]).
2. **분류/스폰** — the orchestrator classifies which role leads
   (`on-the-record/commands/run.md`, from line 60) and calls `spawn.py`
   by hand.
3. **검증** — PR review/approval is a human act
   (`docs/specs/approvers.md`-gated Approve, or the single-account
   `APPROVE issue-<n>/<role>` issue comment — this session's own
   role-handoff contract v3 text, reproduced in the SessionStart
   reminder).
4. **머지** — `gh pr merge` is never automated by a role or by
   `spawn.py`; nothing in `spawn.py` shells out to `gh pr merge`
   (checked: `grep -n "pr merge" spawn.py` — result: no match, so merge
   stays a human GitHub act by contract rather than code this repo
   calls).

Every hop between these four steps requires a human turn in the
orchestrator's own conversation. `on-the-record/commands/run.md`, lines
363-372 ("자동 진행 없음", no auto-progression) states this as a
*design decision*, not a gap report: "어떤 스텝이 완료됐더라도, **다음**
스텝의 스폰은 그 턴에서 사용자의 명시적 동의가 있어야 한다" (even once
a step is complete, the **next** step's spawn needs the user's explicit
consent, in that same turn). Partial-line rejection
(`on-the-record/commands/run.md`, lines 373-382) reinforces the same
rule per-role: a rejected PR only respawns that one role, and only
after the same judgment/consent procedure as a fresh spawn — never an
automatic retry loop.

## What primitives exist for a role to compose across roles by itself

derived: `grep -n "^def " spawn.py | grep -iE "consult|spawn_one"`

- **`consult_cmd()`** (`spawn.py`, line 3556) is the only cross-role
  primitive callable from inside a role session. It loads another
  role's rulebook and returns a single JSON verdict
  (`{"answer", "confidence", "caveats"}`) — no branch, no commit, no
  PR (`spawn.py`, lines 3556-3560 docstring: "브랜치도 커밋도 PR 도
  만들지 않는다"). It is opinion-only. A role that consults another
  role gets a text judgment back into its own session; it cannot hand
  off actual *work* (a sub-investigation with its own deliverable)
  this way.
- **`_spawn_one()`** (`spawn.py`, line 4382) is the only primitive that
  opens a branch/workspace/PR pipeline for a role. It is called from
  `spawn_cmd()`, which is invoked from the CLI (`spawn.py`'s
  `argparse` entry point) — i.e., by the orchestrator's shell-out, not
  by a running role session. No code path in `spawn.py` has one role's
  own session invoke `_spawn_one()`/`spawn_cmd()` against itself
  (checked: `grep -n "_spawn_one(\|spawn_cmd(" spawn.py` — result:
  both names are called only from the CLI dispatch and from
  `_self_trigger_respawn()`/`_respawn_or_cap()`, which are themselves
  triggered by the *watcher* process after a crash/stall/session-end,
  not by a role choosing to compose a fix).
- **Respawn-on-failure** (`_respawn_or_cap()`, `spawn.py` line 2536;
  `_self_trigger_respawn()`, `spawn.py` line 2662) restarts the *same*
  role on the *same* task after a crash/stall — it is retry, not
  composition: it never assembles a *different* role or a *sequence*
  of roles in response to a surfaced defect.

## What a role does when it hits a problem mid-task

A role session that discovers a problem outside its own `YOU DECIDE`
scope is directed, by its own role rulebook's `BOUNDARY CASE` clause
(reproduced in this session's own SessionStart reminder for the
architecture role: "위 YOU DECIDE 범위를 벗어나면 멈추고 화살표대로
넘겨라"), to stop and leave a hand-off note in its own record for the
*next* role's session — a note the orchestrator must read and act on by
opening a new issue/spawn by hand. `consult_cmd()` lets it ask a
different role's rulebook a question mid-session, but the answer cannot
turn into a branch/PR without the orchestrator's separate spawn. There
is no code path by which a role, having identified a defect, can itself
(a) file the issue, (b) pick the resolving role(s) and their order, and
(c) spawn them — every one of those three sub-steps is gated to the
orchestrator's own conversational turn with the user.

## What the orchestrator did by hand on 2026-08-11

derived: `git log --oneline -5` (see gitStatus at session start) shows
merges for issue-745 (product-discovery) and issue-741
(implementation) landing today, each preceded by its own
diagnose→issue→spawn→verify→merge cycle run conversationally through
`/run` — i.e. the four-step loop above, executed by hand, once per
issue, with no code artifact recording the cycle itself as a reusable
unit. checked: `grep -rn "resolution.*recipe\|composition.*primitive" --include=*.py .` — result: no match, so no such object exists in this repo today.

## Sub-area evidence table (evidence, not verdict — verdicts in the proposal)

| sub-area | file:line | today |
|---|---|---|
| issue authorship | `on-the-record/commands/run.md` lines 20-22 | human-only by design |
| role→role spawn during a session | `spawn.py` line 4382 (`_spawn_one`), CLI-only call sites | none found |
| role→role consult during a session | `spawn.py` line 3556 (`consult_cmd`) | opinion-only, no deliverable |
| step-to-step auto-progression | `on-the-record/commands/run.md` lines 363-372 | explicitly disabled by design |
| retry-on-crash/stall | `spawn.py` line 2536, `spawn.py` line 2662 | same-role retry only, not composition |
| merge | not found in `spawn.py` | human GitHub act, by contract |
| recorded reusable "resolution recipe" | none found | absent |
