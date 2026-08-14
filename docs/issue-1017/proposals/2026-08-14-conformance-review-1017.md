---
status: proposed
files:
  - docs/issue-1017/reports/conformance-review.md
---

## Request

#1017 asks for a requirement-ID linkage anchor (serving R001): a draft-time
backstop, a spawn-task requirement passthrough, and a digest next-action
line — landed as PR #1026, commit 834c1d5c02f58faf46290615596813a7085fe4a4,
on the issue-1017/implementation branch. Per the marketplace
conformance-review board condition (issue-521), this commit has no
conformance-review record yet — this proposal is the phase-1 requirement
list that phase 2 will render verdicts against.

## Constraints

- No holistic code-quality judgment — only per-requirement
  Present/Surface/Absent/Incorrect/Unverifiable verdicts.
- Verdicts are never rendered in phase 1; this proposal only extracts the
  checkable requirement list from the spec (issue #1017's own Ask +
  Acceptance sections).
- Evidence must be locatable in the artifact itself (the delivered files
  named in the survey), not inferred from the implementation role's own
  stated intent (docs/issue-1017/reports/implementation.md).

## What will be done (phase 2, on Approve)

Render one verdict per item below against the delivered files
(gates/requirement_linkage.py, spawn.py, gates/test_requirement_digest.py,
gates/test_requirement_linkage.py, docs/specs/enforcement-boundary.md):

1. Draft-time backstop — a new issue draft citing no requirement ID and no
   `infrastructure/no-direct-requirement` tag is flagged before spawn.
2. Escape tag — the literal `infrastructure/no-direct-requirement` tag (or
   a real `R\d+`/`northpole req#<n>` citation) passes the same check.
3. Spawn-task passthrough — a spawned role session's task text carries the
   requirement ID(s) cited by its issue.
4. Digest next-action — `requirement_drift()`'s uncited-live-requirement
   print names the requirement's digest paraphrase and source issue,
   replacing the prior bare ID-list print.
5. Advisory-only scope — the structural check applies to newly drafted
   issues/spawns only; no retroactive blocking of already-open issues
   (grandfathering).
6. Test coverage — `gates/test_requirement_digest.py` carries the
   untagged-new-issue and tagged-infrastructure-issue cases named in
   #1017's Acceptance section.
7. Gate registration — the new module is registered in
   `docs/specs/enforcement-boundary.md` per gate-registration-guard.sh.

## Out of scope

- Fixing anything found Absent/Incorrect — findings are handed off to the
  implementation role, never patched by this role.
- Re-litigating the phase-1 proposal's own design choices (already
  approved at docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md).

## How you'll know it worked

- `docs/issue-1017/reports/conformance-review.md` carries one verdict per
  item above, each citing a file:line or command-output source.
