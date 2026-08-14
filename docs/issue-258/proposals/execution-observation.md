---
kind: proposal
loop_state: proposed
---

# Proposal — issue #258 (phase 1, execution-observation)

## Subject

`on-the-record/commands/run.md` at commit
`74353e50eca2ac908767dbfb0b01ce4d7336017b` (PR #259, merged
2026-08-04T00:29:24Z) — a 13-line, single-file prose insertion into step 1
of the orchestrator loop. No code path (`spawn.py`, gates, hooks) changed
in that commit.

This is a phase-1 proposal; no verdict is rendered here. Phase 2 will
render all three of the role's mandated verdict levels.

## Skip record (scout-directive)

Scouting is skipped. Reason: not product-shaped work with a competitive
field to survey. The commit is a documentation/procedure-prose insertion;
the acceptance criteria are already mechanically checkable by direct text
inspection of the merged file (grep for named strings, ordering of the
insertion relative to step 2, diff-stat scope), with no external research
question open.

## Verdict levels to be checked, and against what evidence

- **outcome** — whether PR #259 (subject issue-258, merged
  `74353e50eca2ac908767dbfb0b01ce4d7336017b`) satisfies issue #258's
  decision items 1-4, recomputed as the worst case across cited
  step-level results, per
  `roles/specs/execution-observation.spec.json`'s recomputation rule
  (EARL `passed`/`failed`/`cantTell`/`inapplicable`/`untested`).
- **trajectory** — whether the phase-1→phase-2 path (implementation PR
  #259, conformance-review PR #260) followed contract v3 s19: proposed
  before implementing, obtained real human approval at each gate —
  checked against `gh issue view 258 --comments` and each PR's
  approval-gate/merge history.
- **step** — whether the single changed artifact
  (`on-the-record/commands/run.md`) actually carries, at the merge
  commit, each of the four textual claims already asserted by the
  implementation report's own acceptance checklist and by the
  conformance-review's Present verdicts — checked by re-running the
  underlying commands directly against `git show
  74353e50eca2ac908767dbfb0b01ce4d7336017b:on-the-record/commands/run.md`,
  not by re-reading either role's prose claim as proof.

## What will be done (phase 2, on approval)

1. `git show 74353e50eca2ac908767dbfb0b01ce4d7336017b:on-the-record/commands/run.md`
   into a scratch file — the merge commit's content, not the current
   branch tip (which carries later, unrelated commits touching the same
   file).
2. `git diff 3c27dc9 74353e5 --stat` to confirm file scope (one code file
   plus three `docs/issue-258/` records).
3. `grep -n` each of the four textual claims (names the `Skill` tool and
   negates plain-text paraphrase; states skill invocation does not
   produce the deliverable; states role sessions receive no skills; skill
   sub-step precedes step 2's role-classification heading) against the
   merge-commit content.
4. `sed`/`grep` check that no markdown table was inserted alongside the
   skill sub-step (issue #258 decision 4: per-task judgment, not a fixed
   mapping table like step 2's).
5. `grep -rni skill spawn.py roles/` to confirm the out-of-scope surfaces
   (`spawn.py`, `roles/<role>.json` catalogs) carry no skill-injection
   change.
6. Recompute the worst-case verdict across all cited test entries and
   record it — not a standalone summary asserted independently of the
   cited results.

## How you'll know it worked

- Phase-2 record renders outcome/trajectory/step verdicts, each entry
  citing a subject/test pair that resolves to a repo path, commit sha, or
  a command actually run (spec's reference-resolution rule).
- At least one `passed` or `failed` entry tied to a command actually run
  (spec's gate_b_contrast — not all-`untested`/`cantTell`).
- Overall verdict = worst case across cited results, not asserted
  independently.
