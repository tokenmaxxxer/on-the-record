---
issue: 2412
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: docs/issue-2286/reports/implementation.md
    sha: a34a3aa5f3bd6154f85aac90fc5fd4739db25f7a
  - path: docs/issue-2432/reports/implementation.md
    sha: 2cc6d10874d38474fb9ae18bd53da2982d01483f
code_under_review:
  - path: docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md
    sha: same-commit
type: docs
breaking: "no — docs-only change; no code, gate, or hook logic touched"
verdict: pass
---

# issue-2412 — implementation record

## What was done

1. **Resolution decided: amend the proposal-named paths, not R4.** Stage
   3's and stage 4's proposals (the only two of the seven-stage set that
   name a `docs/issue-2241/` destination) each get their named migration-
   doc path corrected to the tree the delivering child issue actually
   owns. Full reasoning and the rejected alternative are in "Why" below.
2. **The exact patch is written**, ready to apply, at
   `docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`:
   stage 3's untracked, never-created
   `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
   → `docs/issue-2286/reports/implementation/board-gate-r5-migration.md`
   (already landed there); stage 4's untracked, never-created
   `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`
   → `docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
   (already landed there).
3. **Stages 5 and 6 checked, no amendment needed.** canonical: `grep -n
   "docs/issue-2241" docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
   docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`, this
   session — no match in either file. Neither proposal names a
   `docs/issue-2241/` destination for its own deliverables, so neither
   collides with `board-gate.sh` R4/R5 the way stages 3-4 did.
4. **The patch could not be applied directly** to
   `docs/issue-2241/proposals/` from this session/branch — see "What did
   not work" and "Rationale for deviations". Filed instead as a `gh
   issue comment 2241` naming the exact fix and the two unblock paths
   (a session on the parent issue's own implementation branch, or a
   human adding a `maintenance-targets:` line naming the parent issue to
   a future delivering issue's body) — canonical: `gh issue view 2241
   --json comments`, this session, shows the filed comment.
5. **The already-landed stage-3 migration doc is now discoverable** from
   three places: the patch doc above (item 2), the `gh issue comment
   2241` (item 4), and this record — satisfying the acceptance item
   without editing a tree this session cannot write.

## Why

Chosen: amend the proposal-named destination to the delivering child
issue's own `reports/implementation/` tree. Rejected alternative: carve
a narrow `board-gate.sh` R4 exemption for parent-program document trees.

Rejected because, verified live this session:

- **R4 already has exactly this exemption, and it still wasn't enough.**
  `board-gate.sh` ships a `maintenance-targets:` issue-body declaration
  (core commit `f516947`, issue-222) that lets a role's own issue
  declare other `docs/issue-<n>/` trees it may also write — canonical:
  read live this session at
  `$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh:842-893`. Both issue
  #2286 (stage 3) and issue #2432 (stage 4) hit the identical R4 refusal
  and could have used this exemption, but neither issue's body carried
  the line — canonical: `gh issue view 2286 --json body -q .body` and
  `gh issue view 2432 --json body -q .body`, this session, `grep -i
  maintenance-targets` on each, no match on either — and a role session
  cannot self-grant it (`gh-guard` denies `gh issue edit`, per
  `docs/issue-2286/reports/implementation.md`'s and
  `docs/issue-2432/reports/conformance-review.md`'s own citations of
  that refusal). Two independent occurrences of the same gap is a
  pattern, not a one-off oversight — carving a *second*, redundant
  exemption mechanism inside R4 does not fix that human-step gap; it
  just adds a second lever nobody pulls.
- **The exemption would not have been sufficient anyway.** The
  proposal-named path sits under `reports/architecture/`, a different
  role's subtree than `implementation` (the role that actually delivers
  each stage). `board-gate.sh` R5 (`reports/` ownership,
  `$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh:899-1022`, deny format
  string at :1019-1022, "belongs to another role... never a foreign
  record. (contract v3 s11)") refuses that write independently of R4 —
  canonical: `docs/issue-2432/reports/conformance-review.md`'s "OF-1"
  finding, this repo, confirms both refusals fired in sequence for
  stage 4 and that the second one is R5, not "R11" as that stage's own
  record initially miscited it (there is no R11 in `board-gate.sh` —
  it ships exactly five rules, R1-R5). A `maintenance-targets` grant
  clears only R4's branch/tree-scope check
  (`$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh:888-890`, `if issue_dir
  in _maint_targets: continue`); it does not touch R5 at all. Fully
  unblocking the proposal-named path would additionally require the
  delivering session to write as the `architecture` role for that one
  file — disproportionate machinery for a single migration note.
- **This repo already has an unrestricted tree for genuinely
  cross-cutting, parent-program content**, and this very program already
  uses it: `docs/decisions/2026-08-25-retire-role-axis-staging.md` is
  the architecture-role ADR for all of issue #2241's seven stages, filed
  under the standing `docs/decisions/` bucket rather than under
  `docs/issue-2241/`. `board-gate.sh`'s own dispatch
  (`$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh:748-761`, `if not
  issue_hits: ... allow()`) grants any role on any branch write access
  to every standing bucket (`decisions`, `handbooks`, `specs`, ...) once
  R2's board precondition holds, with no per-issue declaration needed —
  read live this session. That mechanism already satisfies what a
  narrow R4 exemption for parent-program trees would be built to do; it
  just doesn't fit a single stage's own migration note, which documents
  one stage's landing-time facts, not a standing architectural
  decision governed by `gates/frozen_decisions.py`'s frozen/active/
  superseded lifecycle.
- **The redirect is not hypothetical** — it is what both prior stages
  already did, disclosed as a deviation each time
  (`docs/issue-2286/reports/implementation.md`'s "Deviations" section;
  `docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`).
  Naming the delivering issue's own tree up front removes the need for
  a disclosed deviation on every future stage that touches a
  program-level doc, and requires no new gate code and no per-issue
  human step.

## What did not work

Live probe, this session, branch `issue-2412/implementation`: an `Edit`
tool call replacing stage 3's proposal-named path in the stage-3
proposal file was refused. canonical, verbatim, produced live this
turn:

```
board-gate: writing docs/issue-2241/ requires branch
issue-2241/implementation (current: issue-2412/implementation), and
issue #2412's body declares no matching `maintenance-targets:` entry
for issue-2241. Every role output reaches main only through a PR the
human merges — never a direct write from another branch. (contract v3
s10)
```

Same R4 branch-scope shape as the two prior occurrences on issues #2286
and #2432 — this session's write scope does not reach the parent
issue's proposals tree either. See "Rationale for deviations".

## Upstream basis

The stage-3 and stage-4 proposals (both sha
`135712e8e4c56195aa0dedab6060db1610f3dc13`) name the two colliding paths
this record corrects. `docs/issue-2286/reports/implementation.md` (its
"Deviations" and "CHANGES-round fix attempt" sections) and
`docs/issue-2432/reports/implementation.md` /
`docs/issue-2432/reports/conformance-review.md` (its "OF-1" finding, the
R11→R5 citation correction) are the two prior, independent occurrences
of this exact collision this record builds its resolution on.
`$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh` (mounted core-plugin
checkout, read live this session at the line ranges cited in "Why") is
the authoritative source for R1-R5's actual behavior, superseding any
paraphrase in the docs above where the two disagree.

## Open findings

- **The stage-3/4 proposal files themselves remain unedited.**
  Resolution path: a session spawned on the parent issue's own
  implementation branch applies the patch at
  `docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`,
  or a human adds a `maintenance-targets:` line naming the parent issue
  to that session's issue body first (note: per "Why" above, the R5
  role-subtree check would still require that session to write as the
  `architecture` role for the original architecture/ path — moot once
  the patch above redirects to each child issue's own `implementation/`
  subtree, which needs no such grant). canonical: `gh issue comment
  2241` (this session) names both paths on the issue itself.
- none beyond the one above.

## Next steps

None from this session — `loop_state: landed`. The one open finding's
resolution path is fully stated above and does not block this issue's
own closure: the decision is made and recorded, the exact patch is
written, and the two already-landed stages' actual doc locations are
now discoverable from three independent places (see "What was done"
item 5).

## Rationale for deviations

The acceptance criteria this issue states expect the stage-3 proposal
and any sibling stage proposals to be directly updated. This session
could not do that: an `Edit`-tool content probe against the stage-3
proposal, this session, was refused by `board-gate.sh`'s branch-scope
rule — canonical: the verbatim refusal quoted in "What did not work"
above, produced live this turn. The same rule refused the analogous
probes issues #2286 and #2432 made before it — canonical:
`docs/issue-2286/reports/implementation.md`'s "Deviations" section and
`docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`,
both cited under "Upstream basis" above — for the same reason: a
session on this issue's own branch has no write access to a different
issue's `docs/issue-<n>/` tree without a `maintenance-targets:` grant,
which this issue's own body does not carry and which a role session
cannot add to any issue's body itself (`gh-guard` denies `gh issue
edit`). Delivered instead, matching the precedent both prior stages
set: the literal patch under this issue's own tree
(`docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`,
committed separately this session), plus a `gh issue comment 2241`
naming the fix and both unblock paths for whichever session or human
can actually apply it.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this session's own
record, commit messages, PR title/body, and the `gh issue comment 2241`
text are all authored in English per the skill's routing rule, since the
task-assigning turn was in Korean. other mounted skills
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint): not triggered — this issue is a docs-only
write-scope/path decision, not a code-structure or data-structure
choice.
