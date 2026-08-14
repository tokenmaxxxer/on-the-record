---
status: proposed
files:
  - docs/issue-1202/reports/execution-observation/current-state-survey.md
  - docs/issue-1202/proposals/execution-observation-step3-live-finding.md
  - docs/issue-1202/reports/execution-observation.md
---

## Intent

Issue #1202 step 3 asks this role to close the one acceptance-check gap
PR #1242's own record leaves open (docs/issue-1202/reports/implementation.md,
"MOCK: not run this session"): exercise the advisory-queue machinery
live against a scratch fixture repo — write a genuine finding, confirm
`gates/finding_shape.py` accepts/rejects correctly, confirm the
per-session N=3 rate bound fires, confirm `spawn.py findings-due`
surfaces the un-relayed finding and stops surfacing it once
`relayed_to_issue:` is stamped.

## Constraints

- This role never re-executes the observed role's task and never edits
  under `implementation`'s src/test/docs paths (role directive, this
  session) — all fixture work happens under `/tmp/fixture-1202`, never
  inside this repository.
- This role never spawns a peer role session on its own initiative
  (SCOPE-EXCEEDED rule). No `coding`/`record-authoring` role session is
  spawned this turn; the fixture's finding file is hand-authored by this
  session, clearly disclosed as a simulation, not a live nested
  `claude -p` role session — same disclosure pattern as
  docs/issue-1160/reports/execution-observation.md leg 2.
- No CORE_BUILD_NOW bypass is set this session (checked: `env |
  grep -i core_build_now` → empty, this session). No
  "APPROVE issue-1202/execution-observation" comment exists yet on
  issue #1202 (checked: `gh issue view 1202 --json comments`, this
  session — only the requirements-engineering and implementation
  APPROVEs are present). Phase 2 (the verdict record) opens only once
  that approval lands.

## What will be done

Verdict levels this record will check, once phase 2 opens: outcome
(did PR #1242 land requirements 1-5, per the spec's recomputation rule
over the implementation record's cited step-level results) and step
(is `finding_shape.py` / `findings_due.py` deficient against acceptance
check 4, evidenced by the live fixture run below). Trajectory is
expected to read "not applicable, because this session observes a
single delivery PR (#1242) with an already-approved phase-1 proposal
and phase-2 build, not a phase-1→phase-2 path with an open judgment
call to trace" — that determination itself is deferred to phase 2, not
asserted here.

Evidence already gathered this session (research, not verdict): built
`/tmp/fixture-1202` as a scratch git repo with a real
`docs/reports/status.md` carrying a genuine
record-authoring.md-defined defect (a bare "3 of 5 checks passed"
count claim with no `derived:` line). Wrote three findings under
`docs/reports/findings/record-authoring/` citing that real defect,
each independently passing `gates/finding_shape.py`
(`python3 gates/finding_shape.py <path>` → exit 0 for all three); a
fourth deliberately malformed finding (empty `## Evidence`) was
rejected (`REJECT: missing/empty section: ## Evidence`, exit 1).
`finding_shape.check_rate_bound(root, "record-authoring",
"sim-session-1202", bound=3)` returned `None` before findings 2 and 3
and the reject reason naming the summary-line path before a would-be
4th. `python3 spawn.py findings-due -C /tmp/fixture-1202` listed all
three un-relayed findings and excluded the session-summary file;
stamping `relayed_to_issue: 9999` on one dropped it from the next
`findings-due` run. This evidence will be re-cited with full command
output in the phase-2 record.

## Out of scope

Spawning a real nested role session to author the finding
autonomously (see Constraints); building or changing any
`implementation`-owned code; re-verifying requirements 1-3, which PR
#1242's own reproduced unit-test output already backs.

## How you will know it worked

docs/issue-1202/reports/execution-observation.md exists, committed on
this branch, written only after phase 2 opens (an
"APPROVE issue-1202/execution-observation" comment lands), with an
independence statement preceding all verdict language, all three
verdict levels addressed (trajectory explicitly marked not applicable
with reason if that holds), every verdict-bearing sentence citing its
source, and `loop_state` set per the spec's terminal-state table.

## What did not work

None.
