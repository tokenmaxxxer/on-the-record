# requirements-engineering — issue #1131

kind: requirements-engineering
loop_state: landed

## Summary of work

Phase 2 (build) of the approved proposal
(docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md,
status: approved via `APPROVE issue-1131/requirements-engineering`,
single-account mode, per the issue comment thread). Built the
consumer→upstream defect channel's requirements artifact set, committed
at 128b5ad.
canonical: git show 128b5ad --stat, read this session

- `docs/specs/upstream-defect-channel.md` — EARS-pattern spec (UDC-1
  through UDC-5), a source-of-truth traceability table, and a resolved
  ambiguity list.
- `docs/specs/requirements.md` (+`requirement-digest.md`) — appended
  R002-R004 tying issue #1131's three enforceable requirements to their
  gate-test check functions.
- `roles/upstream-defect-report.json` — the report_only role element for
  this channel.
- canonical: on-the-record/commands/report-upstream.md, read this session
  `on-the-record/commands/report-upstream.md` — the consumer-facing
  command element, containing (in this order): draft-assembly,
  dedup-check, preview-and-confirm, filing-or-fallback, and an explicit
  no-PR-path section.
- canonical: on-the-record/hooks/upstream-defect-scope-guard.sh, read this session
  `on-the-record/hooks/upstream-defect-scope-guard.sh` +
  `on-the-record/hooks/test_upstream_defect_scope_guard.py`, registered
  in `docs/specs/enforcement-boundary.md`/`generated-paths.md` — a
  universal PreToolUse Bash deny gate covering `gh pr create` (incl.
  `GH_REPO`-env-prefixed), `gh api ... /pulls`, GraphQL
  `createPullRequest`, `hub pull-request`, and direct `curl`/`wget`
  against the REST pulls endpoint or GraphQL, wired into
  `on-the-record/hooks/hooks.json`. Coverage surface per
  canonical: docs/issue-1131/reports/requirements-engineering/2026-08-13-hunt-upstream-defect-channel-requirements.md,
  read this session — the post-proposal warrant hunt this replaces the
  original single-shape design.
- `gates/test_upstream_finding_channel.py` — the acceptance gate named
  in issue #1131.
- canonical: gh issue view 1131 --comments (APPROVE reply comment), read this session
  `docs/reports/upstream-findings/2026-08-13-watcher-registry-stale-pid.md`
  — the first real case named in the issue's phase-1 proposal, citing
  #1133 as the canonical upstream tracking issue for the underlying
  watcher defect, per the APPROVE comment's coordination note.

code_under_review:
- docs/specs/upstream-defect-channel.md
- docs/specs/requirements.md
- docs/specs/requirement-digest.md
- docs/specs/enforcement-boundary.md
- docs/specs/generated-paths.md
- docs/specs/reconciled-index.md
- roles/upstream-defect-report.json
- on-the-record/commands/report-upstream.md
- on-the-record/hooks/upstream-defect-scope-guard.sh
- on-the-record/hooks/hooks.json
- on-the-record/hooks/test_upstream_defect_scope_guard.py
- gates/test_upstream_finding_channel.py
- docs/reports/upstream-findings/.gitkeep
- docs/reports/upstream-findings/2026-08-13-watcher-registry-stale-pid.md

## Why

Issue #1131: consumer sessions (target repos with on-the-record
installed) had no channel to report on-the-record plugin defects
upstream — a live example (watcher registry showing stale pids as
`DEAD` after re-arm) died as chat text with no upstream trace.

canonical: docs/specs/northpole.md §2/§5, read this session
This work serves northpole req#2 (full record-ability) and req#5
(problems are not pushed back to the human wholesale — the agent
assembles the draft and runs the dedup check; the human only confirms).

## Upstream basis

docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md
(status: approved)

## Structured requirements doc

REQ-UDC-1
statement: The /report-upstream command SHALL assemble a defect draft containing the plugin version sha, reproduction evidence, and observation context.
ears_pattern: ubiquitous
verification_method: Test
verification: gates/test_upstream_finding_channel.py asserts the draft contains a version-sha line, a reproduction section, and an observation-context section.

REQ-UDC-2
statement: WHEN a defect draft has been assembled, the channel SHALL check it against open upstream issues for a duplicate before presenting it to the user.
ears_pattern: event-driven
verification_method: Test
verification: gates/test_upstream_finding_channel.py asserts the dedup-check step precedes the confirmation step in the command's own instructions.

REQ-UDC-3
statement: WHILE the draft has not received explicit user confirmation, the channel SHALL NOT invoke any network call that files the draft upstream.
ears_pattern: state-driven
verification_method: Test
verification: gates/test_upstream_finding_channel.py asserts no `gh issue create` call-shape appears before the confirmation step in the command's own instructions.

REQ-UDC-4
canonical: on-the-record/hooks/upstream-defect-scope-guard.sh, read this session
statement: The channel SHALL file confirmed drafts as GitHub issues only and SHALL NOT invoke any pull-request-creation call shape.
ears_pattern: ubiquitous
verification_method: Test
verification: on-the-record/hooks/test_upstream_defect_scope_guard.py and gates/test_upstream_finding_channel.py both assert every named PR-creation call shape is denied by the real hook script.

REQ-UDC-5
statement: WHEN the upstream repo is unreachable at filing time, the channel SHALL save the draft to docs/reports/upstream-findings/ and report the fallback to the user.
ears_pattern: event-driven
verification_method: Test
verification: gates/test_upstream_finding_channel.py asserts the fallback directory and the first-real-case fixture file exist.

Full text (ID + statement + ears_pattern + verification_method +
verification_condition per requirement) at
docs/specs/upstream-defect-channel.md §Requirements, using the plain
`UDC-1`..`UDC-5` numbering these REQ-UDC-1..REQ-UDC-5 ids above map onto
1:1. Summary:

| ID | ears_pattern | statement (condensed) | verification_method |
| --- | --- | --- | --- |
| REQ-UDC-1 | ubiquitous | assemble draft with version sha, repro, context | Test |
| REQ-UDC-2 | event-driven | dedup check against open upstream issues before draft is shown | Test |
| REQ-UDC-3 | state-driven | no filing network call before user confirmation | Test |
| REQ-UDC-4 | ubiquitous | issues only — every PR-creation call shape structurally denied | Test |
| REQ-UDC-5 | event-driven | unreachable upstream falls back to docs/reports/upstream-findings/ | Test |

## Traceability matrix

| ID | Description | Source | Downstream Link | Status |
| --- | --- | --- | --- | --- |
| REQ-UDC-1 | draft assembly (version sha + repro + context) | docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md | on-the-record/commands/report-upstream.md | open |
| REQ-UDC-2 | duplicate check before filing | docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md | on-the-record/commands/report-upstream.md | open |
| REQ-UDC-3 | confirmation gate before any network filing call | docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md | on-the-record/commands/report-upstream.md | open |
| REQ-UDC-4 | issues-only, PR-path structurally denied | docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md | on-the-record/hooks/upstream-defect-scope-guard.sh | enforced |
| REQ-UDC-5 | unreachable-upstream fallback | docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md | docs/reports/upstream-findings/ | open |
| northpole-req2 | full record-ability | docs/specs/northpole.md | docs/specs/upstream-defect-channel.md | open |
| northpole-req5 | problems not pushed back to the human wholesale | docs/specs/northpole.md | docs/specs/upstream-defect-channel.md | open |
| northpole-req7 | hooks/plugin elements only, no CI | docs/specs/northpole.md | roles/upstream-defect-report.json | open |

canonical: acceptance: python3 -m pytest gates/test_upstream_finding_channel.py on-the-record/hooks/test_upstream_defect_scope_guard.py -q — result: PASS
Row REQ-UDC-4's `enforced` status reflects that run. The other rows stay
`open`: mechanical test coverage is in place (gates/test_upstream_finding_channel.py
covers all five), but no live consumer session has exercised the command
element end to end yet (it is interpreted by an LLM session, not run
directly by this gate test).

## Ambiguity list

Statement: "Filing happens only with user confirmation" (issue #1131
req 3). Candidate readings: (a) confirmation gates the `gh issue create`
call only; (b) confirmation must also gate the read-only dedup-check
call.
Resolution: (a) — the dedup check is a read needed to show an accurate
draft; only the write call is "filing".

Statement: "plugin version (sha)" (issue #1131 req 1). Candidate
readings: (a) the on-the-record plugin install's own sha; (b) the
consumer target-repo's HEAD sha.
Resolution: (a) — the defect being reported is a plugin defect, so the
plugin's own version is what upstream triage needs.

Statement: "the upstream repo is unreachable" (issue #1131 req 5).
Candidate readings: (a) only the `gh issue create` call failing counts;
(b) the dedup-check call failing also counts.
Resolution: both trigger the fallback — a failed dedup check cannot rule
out a duplicate, so either failure leaves filing unsafe.

Full text with the same three items at
docs/specs/upstream-defect-channel.md §Ambiguity list.

## What did not work

Deviation (inline, mechanical — role-deviation-directive):

1. canonical: board-gate.sh PreToolUse denial, observed this session
   The approved write set named a fallback-record directory under the
   docs tree top level (per issue #1131 requirement 5's own wording),
   matching neither an issue tree nor a standing bucket. At write time,
   the plugin's board-gate hook (contract v3 s10) refused that path —
   it is not one of the six standing `docs/` buckets (`_assets,
   decisions, handbooks, proposals, reports, specs`) and has no
   issue-tree shape, with no override mechanism in the gate. Relocated
   the fallback directory to `docs/reports/upstream-findings/` (the
   `reports` bucket) throughout the write set — same function (a
   cross-issue findings home, not per-issue), compliant location.
2. canonical: PreToolUse Bash hook denials from gate-registration-guard.sh,
   live-fire-claim-real-run-guard.sh, acceptance-command-real-run-guard.sh,
   requirement-digest-preflight.sh, all observed this session
   `git commit` for the phase-2 write set was refused three more times
   by mechanical gates: `gate-registration-guard.sh` (new hook module
   needs a row in `docs/specs/enforcement-boundary.md` and
   `docs/specs/generated-paths.md` — added both), then
   `live-fire-claim-real-run-guard.sh` and
   `acceptance-command-real-run-guard.sh` both false-positived on
   pre-existing prose inside `enforcement-boundary.md` (another guard's
   own row documents the `live-fire:`/`acceptance:` citation shapes as
   literal example text within its own description, and the diff
   context around my added row made that pre-existing prose read as a
   new citation) — resolved via the guards' own documented escape
   hatches, `Live-fire-recheck-N/A:`/`Acceptance-recheck-N/A:` commit
   trailers, stating the false-positive reason. Then
   `requirement-digest-preflight.sh` required regenerating
   `docs/specs/requirement-digest.md` alongside `requirements.md` —
   regenerated and staged.

All four are mechanical gate friction forced by infrastructure outside
this role's write scope, not design changes to the delivered channel.

## Acceptance verification

checked: `python3 -m pytest gates/test_upstream_finding_channel.py
on-the-record/hooks/test_upstream_defect_scope_guard.py -q`
canonical: acceptance: python3 -m pytest gates/test_upstream_finding_channel.py on-the-record/hooks/test_upstream_defect_scope_guard.py -q — result: PASS

```
..................                                                       [100%]
18 passed in 0.52s
```

## Open findings

None. The phase-1 warrant hunt's finding (single-shape PR-guard design
leaving `gh api`/GraphQL/`GH_REPO`/hub/curl surfaces unguarded) was
folded directly into `upstream-defect-scope-guard.sh`'s coverage in this
phase-2 build. The board-gate path conflict and the three commit-gate
false positives above are the only new issues discovered during this
build, and all are fully resolved (not open) by the actions described in
`## What did not work`.
