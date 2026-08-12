---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
  - docs/issue-1013/reports/implementation.md
---

Subject: issue-1013

## Request

Build blocks A-F of session-ownership scoping exactly as designed in the
merged `docs/issue-1013/proposals/session-ownership-scoping.md`
(product-discovery phase-1, PR #1016): a shared `_roster_own()` filter
applied to `roster_watchdog()`, the undisposed-PR gate
(`_undispositioned_role_prs()`), auto-respawn's orphan handling, and
`roster_ps()`'s watcher-identity line, plus the `--all` CLI thread-through
already defined for `watchdog`.

## Constraints

- Skip condition (scout-directive): the spec leaves no design decision
  open. The merged design already names the exact helper signature
  (`_roster_own(d: dict, all_scope: bool) -> dict`), the four call sites
  (B roster_watchdog, C the PR gate, D auto-respawn/orphan surfacing, E
  the watcher-identity line), and the CLI surface to reuse (`--all`,
  spawn.py:4497-4499). No survey or scout pass is run this turn; this
  proposal cites that skip condition instead of re-deriving the design.
- Do not recreate `docs/issue-1013/proposals/session-ownership-scoping.md`
  or its survey/hunt record — this proposal is a thin phase-1 wrapper
  authorizing this role's own branch/PR to build the already-approved
  design, per role-handoff contract v3 s19 (phase-2 build requires an
  approval act scoped to this role's own branch,
  `issue-1013/implementation`, distinct from the approval already given to
  `issue-1013/product-discovery`).
- The merged design's own open finding stands: nothing in the repository
  ever sets `ORCHESTRATOR_SESSION_ID` today, so on every real invocation
  `_roster_own()` degenerates to `None == None` self-matching for every
  session (no real cross-session scoping yet) until a launcher/harness
  wires that env var — out of this proposal's write set by the upstream
  design's own "Out of scope" section. Building A-F now is still correct:
  it is the mechanism the harness-side fix will activate, and the
  empty-state-parity behavior (today's `None`-only case) is exactly what
  the acceptance criteria require to stay unchanged.

## Rationale

Considered building directly on this branch without a phase-1 proposal,
since the design itself was already approved on the product-discovery
branch and this session's invocation instructed "BUILD... APPROVE
posted." Rejected: checking the issue's own comment history found exactly
one APPROVE comment — `APPROVE issue-1013/product-discovery` — and none
scoped to `issue-1013/implementation`; `CORE_BUILD_NOW` is unset in this
session's environment, so the build-now bypass does not apply either.
`on-the-record/hooks/approval-gate.sh` mechanically confirmed this by
refusing a direct write to `tests/test_spawn.py` on this branch pending
that approval. A minimal proposal that references (not repeats) the
existing design keeps the record honest without re-litigating decisions
already made, and lets phase-2 build without a second design round once
approved.

## What will be done

Once this proposal is approved for `issue-1013/implementation`
specifically, build exactly blocks A-F as specified in the upstream
design doc's "What will be done" section — no reinterpretation:

- **A.** `_roster_own(d: dict, all_scope: bool) -> dict` — the shared
  filter: `all_scope=True` returns `d` unchanged; otherwise entries whose
  `session_id` equals the caller's own id (via
  `os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None`, covering the
  `None == None` empty-state case) unioned with orphaned entries.
- **B.** `roster_watchdog(auto_respawn=False, all_scope=False)` filters
  the loaded roster through `_roster_own()` before its scan loop; entries
  that are orphaned (owning session non-`None` and not the caller's own,
  unresolvable) print under a distinct `[orphaned]` label.
- **C.** `_undispositioned_role_prs()` builds a branch -> session_id map
  from `_roster_own()` (own-scope) and skips any open PR whose
  `headRefName` matches a roster entry the caller owns — narrowing the
  gate's exclusion, not removing it.
- **D.** Auto-respawn only fires `_auto_respawn_check()` on entries the
  caller owns; orphaned dead entries are reported, never respawned, by a
  session that did not own them.
- **E.** `roster_ps()`'s watcher-status line gains a session comparison —
  a live, real watcher owned by a different session prints
  `워처: pid N (다른 세션 소유)` instead of implying local ownership;
  `_watcher_looks_real()` itself is unchanged.
- **F.** `spawn.py watchdog --all` / `--auto-respawn --all` thread
  `all_scope=True` into `roster_watchdog()`, reusing the existing `--all`
  flag; without `--all` both default to own-scope.
- `tests/test_spawn.py` gains the issue's own acceptance case: two roster
  entries with distinct `session_id`s where default scope sees only the
  caller's own entry, `--all` surfaces both, an orphaned entry surfaces
  under default scope, and a single-session/empty-state roster
  (`session_id: None` throughout) behaves identically to today.
- `docs/issue-1013/reports/implementation.md` recording the build.

## Out of scope

- Redesigning A-F or the upstream design doc.
- Symptom 5 (interleaved `poll-watchdog.log`) — confirmed by the upstream
  survey to live outside `spawn.py`.
- Wiring a real `ORCHESTRATOR_SESSION_ID` set-point in any launcher or
  harness driver — the upstream design's own open finding defers this to
  a companion issue; A-F builds the mechanism the set-point will later
  activate, and empty-state parity (today's universal `None` case) is
  itself part of this proposal's acceptance criteria.
- Any change to gate mechanics, role rulebooks, or files outside the
  frozen write set above.

## Accumulation

This adds one shared ~10-15 line helper (`_roster_own()`) reused at four
existing call sites (B-E), not a new subsystem — no new persistent state
format, no new file, no new roster schema field (`session_id` already
exists, spawn.py:5427/5516). If a future symptom needs a fifth
roster-scanning call site scoped the same way, it reuses `_roster_own()`
rather than reimplementing the `session_id`-equality-with-`None`-match
logic inline — the accumulation cost stays flat at one helper regardless
of how many call sites eventually consume it.

## How you'll know it worked

- `tests/test_spawn.py`'s new scoping test class passes: own-entry
  filtering, `--all` full view, orphan surfacing under default scope, and
  single-session/empty-state parity with today's unscoped output.
- `python3 -m py_compile spawn.py` succeeds.
- The full `tests/test_spawn.py` suite still passes (no regression in the
  four call sites' existing behavior).
