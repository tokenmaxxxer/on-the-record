---
subject: issue-749
role: conformance-review
kind: survey
loop_state: phase1-survey
---

# Survey: northpole-conformance backlog (issue #749)

what was done: read all five landed dimension audits (issue-750 A: role-session
behavior, issue-751 B: inter-agent comm, issue-752 C: core judgment capability,
issue-753 D: session-completion durability, issue-754 E: problem-resolution
composition) plus `docs/specs/northpole.md` (the 7 requirements), deduplicated
every PARTIAL/GAP finding across them, mapped each to the northpole
requirement(s) it blocks, and ranked by (northpole-centrality x
observed-failure-frequency).

why: issue #749 asks for one ranked backlog over the five audits' findings so
the gap "many problems" becomes traceable fix issues instead of a wall of
text (northpole req #6).

upstream:
- docs/specs/northpole.md
- docs/issue-750/reports/architecture/survey.md
- docs/issue-751/reports/architecture/survey.md
- docs/issue-752/reports/architecture/survey.md
- docs/issue-753/reports/architecture/survey.md
- docs/issue-754/reports/architecture/survey.md

## Provenance note

None of the five source audits has landed its phase-2 record yet — each is
still `status: proposed`, its evidence living only in its
`docs/issue-<n>/reports/architecture/survey.md`. This survey therefore reads
the survey files directly (cited per-row below), not a `reports/architecture.md`
that does not yet exist for any of the five. issue #749's prompt names the
path docs/issue-753/reports/architecture.md, but that file does not exist on
disk today — issue-753's actual and only content is
`docs/issue-753/reports/architecture/survey.md`.

## Requirement #7 direct evidence (per issue #749's specific instruction)

Issue #749 asks to "use a consult to the relevant role and inspect the
deployed directive surface a non-orchestrator target session actually
receives" for req #7. This session itself is that instance: it is a spawned,
non-orchestrator `conformance-review` role session, invoked headless with no
explicit skill invocation, and this turn's own `SessionStart` hooks (visible
in this session's transcript) delivered, automatically and in full: the
role directive (`conformance-review`'s `YOU DECIDE`/`USE_WHEN`/`PRODUCES`
block), the role-handoff interaction protocol (contract v3), the warrant
proposal-gate directive, the scout directive, the freelunch orchestration
directive, and the terse output directive — none invoked by name, all
plugin-delivered. This directly confirms the hook-delivery layer of req #7
(`on-the-record/hooks/hooks.json` wiring `SessionStart` hooks, per
`docs/specs/northpole.md` req #7's own traceability note) reaches a plain
target session on install alone.

Separately, `docs/issue-750/reports/architecture/survey.md` sub-area C (line
125-133 of that file) is the audit finding that collides directly with req
#7: `on-the-record/UNENFORCED-CLAUSES.md` and `docs/specs/enforcement-boundary.md`
label `gates/reexecution_gate.py` "contract, CI-supplement" — a plugin-only
install (the mandatory default under req #7) never triggers it. So req #7 is
**PARTIAL, not MET**: the *hook/directive* delivery layer this session just
received reaches a plain session with no explicit invocation (confirmed
directly, this turn); the *gate/enforcement* layer for real-wired
verification (req #3) does not, by the audits' own explicit labeling. Both
observations are folded into the backlog row for req #3/#7 below (rank 2).

## Deduplicated, ranked backlog

Source column cites the survey.md file for the audit that carries the
primary evidence; a row synthesizing more than one audit's finding lists all
sources. Ranking is qualitative (northpole-centrality x observed-failure-
frequency), following each source audit's own per-row rank input, and is
restated as the ranked backlog table in this issue's phase-2 proposal, which
is the record this survey feeds.

1. Concurrent-rulebook-clone TOCTOU race — GAP — req #1 — highest observed
   frequency of any finding (majority of one parallel same-role spawn batch,
   per the issue-753 prompt itself) — source: issue-753 survey §6 — repo:
   on-the-record (`spawn.py` `rulebook_checkout()`, `core_root()`).
2. Real-wired verification (`reexecution_gate.py`) is CI-supplement-only,
   never triggered on a plugin-only install — GAP — req #3 + req #7
   (structural collision) — structural/permanent by current labeling —
   source: issue-750 survey sub-area C; corroborated this turn by direct
   session evidence above — repo: on-the-record (`spawn.py`/hooks) + muster.
3. Watch/ps subsystem: role-blind pid check, unconfirmed watcher pid,
   rejected-PR history masking a real `silent-failure` — PARTIAL — req #1,
   req #4 — high (independently reproduced findings within one week,
   derived: issue-750 survey.md sub-area D's dated hunt-report citations) —
   source: issue-750 survey sub-area D — repo: muster (`spawn.py`
   watch/roster/watchdog).
4. Missing schema-and-gate-enforced decision-record primitive (required
   reasoning/alternatives field, currently `decision_drivers: required
   false`) — GAP, named root cause other core-judgment findings point at —
   req #4, req #5 — source: issue-752 survey §5 (and §1/§3/§4, which all cite
   it as the shared root) — repo: on-the-record (`roles/specs/*.spec.json`)
   + this repo's `gates/`.
5. Role-initiated resolution composition absent by design: issue authorship,
   role→role spawn, and merge are all human-only; `consult_cmd()` is
   opinion-only (no branch/commit/PR); no reusable "resolution recipe"
   artifact exists — GAP against req #5's "problems are not pushed back to
   the human" as stated (the current design is explicit "자동 진행 없음",
   by intent, but the audit found no role-composable alternative for the
   sub-cases req #5 asks for) — source: issue-754 survey (all four
   sub-steps + primitive table) — repo: on-the-record (`spawn.py`,
   `on-the-record/commands/run.md`).
6. Absorbed-branch/untracked-only re-cut deadlock: proposed fix
   (`docs/issue-732/proposals/absorbed-branch-untracked-recut.md`) not yet
   landed; a second latent gap (leftover stash invisible to `clean`'s guard)
   found even in the proposed fix — PARTIAL — req #1 — high (named live
   incidents cited by number across the strand docs, per issue-753 survey
   §1) — source: issue-753 survey §1 — repo: on-the-record (`spawn.py`).
7. No independent check that a claimed judgment (`axis_evaluation`,
   `progressed` classification, board delta) is genuine reasoning versus a
   mechanically emitted matching string — GAP — req #4, req #5 — medium
   (mechanism-level, no direct repro of a fabricated judgment found, but
   adjacent proven failures exist) — source: issue-750 survey sub-area B;
   corroborated by issue-752 survey §4 ("every gate found fires against an
   artifact that already embodies a completed judgment") — repo: muster
   (`spawn.py` `classify()`, `on-the-record/hooks/delegated-judgment-gate.sh`).
8. No mechanism forwards a predecessor role's board-record body into a
   successor's spawn-time task string; the entire bridge is the
   orchestrating conversation typing a pointer/excerpt by hand — GAP — req
   #5 — medium, this session's own spawn is direct-turn evidence of the
   pattern — source: issue-751 survey sub-area 3 (spawn-time context) +
   OF-1 — repo: on-the-record (`spawn.py` `_spawn_one()`).
9. Orchestrator failure-signature blindness: `_respawn_or_cap` collapses
   every crash into one bucket and retries blindly within the cap instead of
   branching on *why* the session broke — PARTIAL — req #1 — bounded (cap
   prevents runaway) but recurring, defers diagnosis to a human every time
   the cap is hit — source: issue-753 survey §3 — repo: on-the-record
   (`spawn.py` `_respawn_or_cap`/`_auto_respawn_check`).
10. `consult_cmd()` has zero board-record read access; every consult is
    contextually isolated except for what the caller manually pastes into
    the question string — GAP — req #5 — structural, same shape as row 8 —
    source: issue-751 survey sub-area 1 + OF-2; issue-752 survey §2 — repo:
    on-the-record (`spawn.py` `consult_cmd()`).
11. Directive says proposal→judge→produce→record; spawn.py's completion
    signal (`classify()`, `rc = proc.wait()`) is process/log-mechanical, not
    a content check that the directive was actually followed — PARTIAL —
    req #1, req #4 — medium — source: issue-750 survey sub-area A — repo:
    muster (`spawn.py`).
12. PR-status comment functions (`_post_session_end_comment`,
    `_post_crash_comment`, `_post_stall_comment`) carry a status marker and a
    URL/path only, never board-record findings content — PARTIAL (req #4,
    human-legible reporting, is cheapest exactly where this gap bites: a
    human scanning the issue thread) — low-medium — source: issue-751 survey
    sub-area 4 + OF-3 — repo: on-the-record (`spawn.py`).
13. Gates found across core-judgment sub-areas police an already-completed
    judgment (risk_report, delegated-judgment-gate, axis-ownership check);
    none helps a role enumerate or weigh options before committing — GAP —
    req #4, req #5 — recurring pattern, same root as row 4 but recorded
    separately since the audit calls it out as a distinct, independently
    observed pattern across three gates — source: issue-752 survey §4 —
    repo: on-the-record (`gates/risk_report.py`,
    `on-the-record/hooks/delegated-judgment-gate.sh`).
14. Resumability degrades to silent no-op for workspace-reconstruction
    failures (clone races, absorbed-branch re-cut) though the common
    dirty-workspace-survives case is handled — PARTIAL — req #1 — narrower,
    lower observed frequency than the clone-race and re-cut-deadlock rows
    above — source: issue-753 survey §4 — repo: on-the-record (`spawn.py`).
15. Goal-loop continuation (#699 R3) is landed as directive text a session
    reads at `SessionStart`, with no gate verifying it was followed and no
    cross-session resume artifact — PARTIAL — req #1 — lower observed
    frequency than the clone-race and re-cut-deadlock rows above (R3
    recently landed, no field incident cited yet) — source: issue-753
    survey §5 — repo: on-the-record (`on-the-record/hooks/directive.sh`,
    `spawn.py` goal-loop wiring).
16. Concurrent same-issue roles cannot see each other's in-flight findings
    until one side merges (board is merged-only); correct for write safety
    but unannounced anywhere as a communication limit — PARTIAL — req #5 —
    low, structural-by-design rather than a proven incident — source:
    issue-751 survey sub-area 2 (point 3) + OF-4 — repo: role-handoff
    contract (board semantics), not a single repo's code.
17. `decision_drivers` (the reasoning-for-weighing field) is
    `required: false` in `roles/specs/architecture.spec.json`, and only the
    axis-evaluation template (a narrow fixed set) enforces real
    decision-procedure shaping — PARTIAL — req #4 — low, narrowest scope,
    one strong counter-example (axis template) already shows the fix is
    buildable — source: issue-752 survey §3 — repo: on-the-record
    (`roles/specs/*.spec.json`, `gates/record_lint.py`).

## Requirements with no PARTIAL/GAP finding across the five audits

- Req #2 (full record-ability): no audit surfaced a gap in the record
  mechanism itself (proposal-first + `record-scaffold.sh` +
  `record-claim-guard.sh`); `docs/specs/northpole.md`'s own traceability
  note is the mechanism, and this survey's own construction (a
  record-claim-guard-passing document assembled from five prior records) is
  a live instance of it working. Recorded MET, not omitted.
- Req #6 (condensed requirement management): no audit found a gap in
  `docs/specs/requirements.md`'s registry mechanism or
  `docs/specs/northpole.md` itself; this survey is itself an instance of
  condensing five scattered audits into one table, the mechanism req #6
  demands. Recorded MET, not omitted.

Both are stated here explicitly per issue #749's acceptance empty-state
clause ("a requirement with no serving mechanism is recorded GAP, never
silently omitted") — read together with `docs/specs/northpole.md`'s own
"Gaps" section (no requirement is a bare GAP), the correct reading for #2
and #6 is MET-with-no-new-finding, not an omission.

## Open findings

- OF-1: rows 1, 2, and 6 (clone race, plugin-only reexecution gap,
  absorbed-branch deadlock) are the three highest-ranked and are all
  unlanded fixes in on-the-record/spawn.py — none has a phase-2 record yet
  in its own source issue either.
- OF-2: row 4 (missing decision-record primitive) is cited as the shared
  root cause by three of the five source audits' own findings (issue-752
  §1/§3/§4/§5, issue-751 OF-2, issue-750 sub-area B) — fixing it likely
  narrows rows 4, 7, 10, 13 simultaneously, though this survey does not
  verify that claim by building anything (read-only).
- OF-3: none of the five source audits has landed a phase-2 record; this
  backlog's `source:` citations point at `survey.md` files, which are
  themselves phase-1, unapproved artifacts. If a source survey's content
  changes before its own phase-2 record lands, this backlog's citations
  may drift from the eventual landed record.

## Next steps

This issue's phase-2 proposal restates this ranking as the required
deliverable table; on approval, phase-2 writes the terminal record at
docs/issue-749/reports/conformance-review.md per contract v3 s19.

## Resolution path

Each backlog row above is meant to lift directly into a fix issue on its
named responsible repo; opening those issues is out of scope for this
read-only conformance-review audit and is deferred to whoever picks up the
ranked backlog (rank order suggests issue-opening order: rows 1, 2, 3 first).
