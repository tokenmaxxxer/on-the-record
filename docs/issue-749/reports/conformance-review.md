---
subject: issue-749
role: conformance-review
kind: record
loop_state: landed
---

# Northpole-conformance review (issue #749)

## what was done

Integrated the five landed dimension-gap audits (issue-750 role-session
behavior, issue-751 inter-agent comm, issue-752 core judgment capability,
issue-753 session-completion durability, issue-754 problem-resolution
composition) into one MET/PARTIAL/GAP verdict over all 7
`docs/specs/northpole.md` requirements, and one deduplicated, ranked
17-row backlog over every PARTIAL/GAP finding across those five audits.
Requirement #7 (default-on/plugin-only/no-explicit-invocation reach) was
audited using this session's own directive surface as direct evidence, per
issue #749's specific instruction.

## why

Issue #749 asks to turn "many problems" (the expected gap between the
northpole target and current implementation) into a ranked, traceable
backlog rather than a wall of text (northpole req #6), so that each row
can lift directly into a fix issue on its responsible repo.

## upstream

- docs/issue-749/reports/conformance-review/survey.md
- docs/issue-749/proposals/2026-08-11-northpole-backlog.md
- docs/specs/northpole.md
- docs/issue-750/reports/architecture/survey.md
- docs/issue-751/reports/architecture/survey.md
- docs/issue-752/reports/architecture/survey.md
- docs/issue-753/reports/architecture/survey.md
- docs/issue-754/reports/architecture/survey.md

## Provenance note

None of the five source audits has landed its phase-2 record yet — each is
still `status: proposed`, its evidence living only in its own
`docs/issue-<n>/reports/architecture/survey.md`. This record therefore
cites those survey files directly, per row, not a `reports/architecture.md`
that does not exist for any of the five.

## Per-requirement verdict

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Orchestration to completion | PARTIAL | Goal-loop and respawn/re-cut mechanisms exist in `spawn.py`, but multiple unlanded gaps (clone-race TOCTOU, absorbed-branch/re-cut deadlock, blind failure-signature retry, resumability no-op on workspace-reconstruction failure, no gate verifying goal-loop directive was followed) leave completion unreliable in the cited failure modes — see backlog rows 1, 6, 9, 14, 15. |
| 2 | Full record-ability | MET | No audit surfaced a gap in the record mechanism itself (proposal-first + `record-scaffold.sh` + `record-claim-guard.sh`); this record's own construction, passing `record-claim-guard.sh`, is a live instance of it working. |
| 3 | Real-wired verification | GAP | `gates/reexecution_gate.py` is labeled "contract, CI-supplement" in `on-the-record/UNENFORCED-CLAUSES.md` and `docs/specs/enforcement-boundary.md` per issue-750 survey sub-area C (line 125-133) — a plugin-only install never triggers it. See backlog row 2. |
| 4 | Autonomous completion + human-legible reporting | PARTIAL | PR-status comment functions report a status marker and URL/path only, never board-record findings content (issue-751 sub-area 4); no gate checks a claimed judgment against the artifact beyond an already-completed state (issue-750 sub-area B, issue-752 §4); `decision_drivers` is `required: false` (issue-752 §3/§5) — see backlog rows 4, 7, 11, 12, 13, 17. |
| 5 | Problems are not pushed back to the human | GAP | Role-initiated resolution composition is absent by design — issue authorship, role→role spawn, and merge are all human-only; `consult_cmd()` is opinion-only with no board-record read access and no reusable resolution-recipe artifact — see backlog rows 5, 8, 10, 16. |
| 6 | Condensed requirement management | MET | No audit found a gap in `docs/specs/requirements.md`'s registry or `docs/specs/northpole.md` itself; this record's own construction — condensing five scattered audits into one table — is itself an instance of the mechanism req #6 demands. |
| 7 | Inviolable constraint — default-on, plugin-only, no explicit invocation | PARTIAL | Direct evidence, this session: the `SessionStart` hooks delivered the role directive, the contract v3 interaction protocol, and the warrant/scout/freelunch/terse directives automatically, with no explicit skill invocation — confirming the hook/directive delivery layer reaches a plain target session on plugin-install-alone. But the gate/enforcement layer for real-wired verification (req #3) does not reach that same plain session, per the same issue-750 finding backing req #3's GAP verdict above — the two layers diverge under req #7's own reach test. |

Per the acceptance empty-state clause ("a requirement with no serving
mechanism is recorded GAP, never silently omitted"), all 7 requirements are
recorded above with an explicit verdict — none omitted.

## Ranked backlog (17 rows, deduplicated across the five source audits)

| Rank | Finding | Verdict | Blocked req(s) | Responsible repo | Fix direction |
|---|---|---|---|---|---|
| 1 | Concurrent-rulebook-clone TOCTOU race in `spawn.py` `rulebook_checkout()`/`core_root()` | GAP | #1 | on-the-record | Serialize or lock rulebook checkout per concurrent spawn batch. |
| 2 | `reexecution_gate.py` is CI-supplement-only, never triggered on a plugin-only install (structural collision with req #7) | GAP | #3, #7 | on-the-record (spawn.py/hooks) + muster | Wire real-wired verification into the plugin-install hook path, not only CI. |
| 3 | Watch/ps subsystem: role-blind pid check, unconfirmed watcher pid, rejected-PR history masking a real silent-failure | PARTIAL | #1, #4 | muster (spawn.py watch/roster/watchdog) | Bind watcher checks to role identity and confirmed pid; surface masked silent-failures in reporting. |
| 4 | Missing schema-and-gate-enforced decision-record primitive (`decision_drivers: required false`) — named shared root cause | GAP | #4, #5 | on-the-record (roles/specs/*.spec.json) + gates/ | Make the reasoning/alternatives field required and gate-enforced across all role specs, not only the axis template. |
| 5 | Role-initiated resolution composition absent by design: issue authorship, spawn, merge are human-only; `consult_cmd()` is opinion-only | GAP | #5 | on-the-record (spawn.py, on-the-record/commands/run.md) | Add a role-composable resolution-recipe artifact/primitive beyond human-only issue/spawn/merge. |
| 6 | Absorbed-branch/untracked-only re-cut deadlock; proposed fix unlanded; second latent gap (leftover stash invisible to clean's guard) | PARTIAL | #1 | on-the-record (spawn.py) | Land `docs/issue-732/proposals/absorbed-branch-untracked-recut.md` and extend its guard to cover leftover stash. |
| 7 | No independent check that a claimed judgment is genuine reasoning vs. a mechanically emitted matching string | GAP | #4, #5 | muster (spawn.py classify()) + on-the-record (delegated-judgment-gate.sh) | Add a check that validates judgment content, not just presence of a matching string. |
| 8 | No mechanism forwards a predecessor role's board-record body into a successor's spawn-time task string; bridge is manual typing | GAP | #5 | on-the-record (spawn.py `_spawn_one()`) | Auto-forward predecessor board-record content/pointer at spawn time. |
| 9 | Orchestrator failure-signature blindness: `_respawn_or_cap` collapses every crash into one bucket, retries blindly within cap | PARTIAL | #1 | on-the-record (spawn.py `_respawn_or_cap`/`_auto_respawn_check`) | Branch retry behavior on failure signature instead of one blind bucket. |
| 10 | `consult_cmd()` has zero board-record read access; consult context is only what the caller manually pastes | GAP | #5 | on-the-record (spawn.py `consult_cmd()`) | Give consult calls board-record read access. |
| 11 | `spawn.py` completion signal (`classify()`, `rc = proc.wait()`) is process/log-mechanical, not a content check that directive steps were followed | PARTIAL | #1, #4 | muster (spawn.py) | Add a content-level check of directive-step completion, not only process exit status. |
| 12 | PR-status comment functions carry a status marker and URL/path only, never board-record findings content | PARTIAL | #4 | on-the-record (spawn.py) | Include board-record findings summary in PR-status comments, not only a pointer. |
| 13 | Gates police an already-completed judgment (risk_report, delegated-judgment-gate, axis-ownership); none helps enumerate/weigh options beforehand | GAP | #4, #5 | on-the-record (gates/risk_report.py, delegated-judgment-gate.sh) | Add a pre-commitment option-enumeration aid, not only post-hoc gates. |
| 14 | Resumability degrades to silent no-op for workspace-reconstruction failures (clone races, absorbed-branch re-cut) | PARTIAL | #1 | on-the-record (spawn.py) | Surface workspace-reconstruction failures instead of silently no-op-ing. |
| 15 | Goal-loop continuation (#699 R3) is directive text only, no gate verifying it was followed, no cross-session resume artifact | PARTIAL | #1 | on-the-record (directive.sh, spawn.py goal-loop wiring) | Add a gate check and a cross-session resume artifact for goal-loop continuation. |
| 16 | Concurrent same-issue roles cannot see each other's in-flight findings until merge (board is merged-only); unannounced as a limit | PARTIAL | #5 | role-handoff contract (board semantics) | Document the limit explicitly, or add an in-flight visibility mechanism. |
| 17 | `decision_drivers` is `required: false` in `roles/specs/architecture.spec.json`; only the axis-evaluation template enforces real decision-procedure shaping | PARTIAL | #4 | on-the-record (roles/specs/*.spec.json, gates/record_lint.py) | Extend the axis-template's enforcement pattern to `decision_drivers` generally. |

Ranking is qualitative (northpole-centrality x observed-failure-frequency),
following each source audit's own per-row rank input; full derivation and
per-row source citations are in
docs/issue-749/reports/conformance-review/survey.md.

## kind

record

## loop_state

landed

## open findings

- OF-1: rows 1, 2, and 6 (clone race, plugin-only reexecution gap,
  absorbed-branch deadlock) are the three highest-ranked and are all
  unlanded fixes in on-the-record/spawn.py — none has a phase-2 record yet
  in its own source issue either.
- OF-2: row 4 (missing decision-record primitive) is cited as the shared
  root cause by three of the five source audits' own findings (issue-752
  §1/§3/§4/§5, issue-751 OF-2, issue-750 sub-area B) — fixing it likely
  narrows rows 4, 7, 10, 13 simultaneously, though this record does not
  verify that claim by building anything (read-only).
- OF-3: none of the five source audits has landed a phase-2 record; this
  backlog's `source:` citations (in the survey) point at `survey.md` files,
  themselves phase-1, unapproved artifacts. If a source survey's content
  changes before its own phase-2 record lands, this backlog's citations may
  drift from the eventual landed record.

## open-finding-resolution-path

Each backlog row above is meant to lift directly into a fix issue on its
named responsible repo; opening those issues is out of scope for this
read-only conformance-review audit and is deferred to whoever picks up the
ranked backlog. Rank order suggests issue-opening order: rows 1, 2, 3 first.
