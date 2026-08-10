---
loop_state: phase-1-survey
---

# Current-state survey: issue #628 silent-failure hunt

Subject: #628. This issue does not name a single observed
role/session/PR — it names a day-wide hunt across the delivery PRs
listed in the issue body's "today's landed flows" section, plus one
core-repo issue. Observed artifacts read this session: `gh issue view
628` (full body), and for every PR the issue names as a hunt surface:
`gh pr view <n> --json number,title,state,mergeCommit,url` for
on-the-record PRs #575, #580, #583, #585, #594, #595, #603, #606, #621,
#591, #607, #622, and for core-repo PRs #191, #194 (`--repo
tokenmaxxxer/tokenmaxxxer-core`), resolving `core#189` to
`tokenmaxxxer/tokenmaxxxer-core` issue #189 ("Rejection/withdrawal must
be first-class across the deployed surface"). Confirmed merge SHAs, per
`gh pr view` output read this session:

| Surface | PR | repo | merge SHA |
|---|---|---|---|
| #566 product-capture-stopgate.sh | #575 | on-the-record | `60a40915` |
| #476 claim-scan-preflight.sh | #580 | on-the-record | `0c644b07` |
| #573 delegated-judgment-gate.sh | #583 | on-the-record | `6ef913ff` |
| #573 boundary-spec verdict rows | #585 | on-the-record | `cbcdd3b9` |
| #586 axis matrix batch 1 | #594 | on-the-record | `c3f45917` |
| #587 remediation spawn-task gen | #595 | on-the-record | `be71072d` |
| #587 remediation-merged event 4 | #603 | on-the-record | `08e78cb3` |
| #587 reconcile --remediation-merged | #606 | on-the-record | `16773ec3` |
| #587 -C target threading | #621 | on-the-record | `f9bc7314` |
| core#189 scope-gate emergency fix | #191 | tokenmaxxxer-core | `c62579f7` |
| core#189 rejection lifecycle build | #194 | tokenmaxxxer-core | `dc52e03a` |
| #577 contract-guard time scoping | #591 | on-the-record | `d8b8f401` |
| #597 framing sixth condition | #607 | on-the-record | `d6103d1a` |
| #600 decision-wait stop rule | #622 | on-the-record | `b83146e2` |

Not yet read this session — deferred to phase 2, per the role
directive's research gate: the patch content of the PRs above,
`hooks/hooks.json` wiring, and the fixture-drive targets themselves.
This survey pins scope and the evidence trail; phase 2 reads the diffs
and drives the surfaces.

## Scope named

Observed role: none singular — the issue assigns this
execution-observation session the hunt directly (its own 실행 계획 names
`step 1 execution-observation`), covering the merged PRs in the table
above plus the two "phase 2 in flight" surfaces named in the issue body
(#576, #619), which the issue marks as not-yet-landed and therefore out
of this hunt's fixture-drive scope (nothing merged yet to independently
drive).

## Tension the survey surfaces (not resolved here)

The role directive prohibits re-running the observed role's code
("PROHIBITED, always: never re-run the observed role's code"); issue
#628's own method requirements mandate exactly that ("Independent
re-execution ONLY: drive shipped entrypoints... on fixture repos").
Precedent exists for reconciling this: `docs/issue-512/proposals/
2026-08-09-execution-observation-fixture-run.md` distinguished "invoking
the already-shipped hook script against a fixture I build myself, to
observe present runtime behavior" (permitted, and the acceptance
criterion the issue itself named) from "re-executing the implementation
work" (prohibited — rebuilding/modifying the hooks, or re-doing the
authoring decision). This survey adopts the same reading: driving a
shipped CLI/hook entrypoint on a fixture is observation, not
re-authoring, and matches #628's own acceptance criteria
(`provenance: executed-live`).

## Write surfaces this session touches (thin/unknown before execution)

- Which of #573's `delegated-judgment-gate.sh`, #586's `--roles-dir`
  entrypoint, #566's stop-hook, and core#189's REJECT-token lifecycle
  are actually wired into `hooks/hooks.json` / a CLI verb table, versus
  merely present as a script with no caller — unknown until phase 2
  greps the wiring files and drives the entrypoint.
- Whether #587's `-C`-target-threading PR (#621) actually fixed the
  ROOT-vs-target defect the earlier PRs in that chain left behind, and
  whether the sibling-sweep audit the issue references ever happened —
  unknown until phase 2 reads #621's diff and searches for that audit
  report.
- #577/#591's time-scoping predicate behavior when evaluated fresh
  (the issue flags this session's own hook cache as predating the fix)
  — unknown until phase 2 forces a fresh evaluation.
- No file under any observed role's `src/`, `test/`, or another issue's
  `docs/issue-<n>/` path (outside this role's own report/proposal paths)
  will be edited by this observation.

## Scout skip record

Scouting is skipped: issue #628 is fully prescriptive — it names the
surfaces, the signature classes to hunt for, and the method (independent
re-execution on fixtures) with no open design decision about *what* to
build. Skip condition "spec literally leaves no design decision open"
applies.
