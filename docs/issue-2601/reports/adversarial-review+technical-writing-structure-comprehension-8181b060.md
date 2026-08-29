---
issue: 2601
role: adversarial-review+technical-writing-structure-comprehension-8181b060
author: adversarial-review+technical-writing-structure-comprehension-8181b060
skills: adversarial-review (skill-repository(c05de12)), technical-writing-structure-comprehension (skill-repository(c05de12))
verifies_subject: true  # independent verification of skill-repository PR #117 + companion on-the-record PR #2716
loop_state: complete
upstream:
  - path: gh pr view 117 --repo tokenmaxxxer/skill-repository
    sha: same-commit
  - path: 1a5966c1:docs/issue-2601/reports/technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a.md (tokenmaxxxer/on-the-record, PR #2716; untracked in this checkout — read from a fresh clone at that commit)
    sha: 1a5966c18621cc813a85747747dafef1cb90ca8b
code_under_review: skill-repository (git@github.com:tokenmaxxxer/skill-repository.git) PR #117, base 5da544f3bc0ca89f65e1628f5480fb169d35e08a, head c05de12ac4a14b2b4db87d9d61ced5955b878c16
type: independent-verification
breaking: false
verdict: pass
---

# issue-2601 — adversarial-review+technical-writing-structure-comprehension-8181b060 record

## What was done

Independently re-verified skill-repository PR #117 ("remove tokenmaxxxer
axis-reference role vocabulary, leave ordinary English intact") and its
companion on-the-record PR #2716, working from a fresh clone rather than
either PR's stated conclusions. All six numbered attack points from the
spawning task are covered below.

**1. Over-application — a changed occurrence that should have been kept.**
Absent. I read the entire 1,331-line diff (all 216 changed line-pairs
across 81 files), not a sample. Every changed occurrence self-references
this system's spawn/session vocabulary: `role spec`, `role's own X field`,
`role intake`, `role start`, `contract v3 role: X` (line 787 of
`requirements-engineering-rules/SKILL.md` literally names "contract v3",
this session's own contract vocabulary — direct proof the surrounding
"role" usage is tokenmaxxxer self-reference, not skill-repository's own
domain concept). The three named danger areas are confirmed byte-identical:
canonical: `git diff 5da544f..pr-117 --stat -- skills/accessibility-aria-and-contrast-rules/ skills/secure-coding-authorization-access-control/ skills/org-design-role-competency-definition/` — result: empty output for all three (no diff, directory names untouched).
I additionally grepped the diff for grammar/architecture/character-role
patterns ("role of", "role in", "component ... role", "pattern ... role")
and found only self-referential hits (e.g. "the architecture role" =
`architecture-interface-contract-shape` referring to itself; "the next
role (requirements-engineering)" = this repo's own skill-handoff chain).
derived: `grep -nE '^[0-9]+:[+-]' <full.diff> | grep -iE 'role of|role in|role that|role for'` — result: 6 hits, all self-referential — none are the ARIA/RBAC/org-job/grammatical/character-role classes the task named as danger zones.

One initially-suspicious pattern turned out not to be a finding after
tracing it: two lines cite `on-the-record/hooks/role-spec-reference-guard.sh`
(untracked in this checkout) and two lines cite
`docs/specs/role-handoff-contract.md` (also untracked in this checkout) —
both were hand-reworded (not mechanically substituted) instead of
renamed to a `skill-`-prefixed guess.
canonical: `git log --all --diff-filter=A --name-only | grep -i spec-reference-guard` on a fresh `tokenmaxxxer/on-the-record` clone shows `on-the-record/hooks/role-spec-reference-guard.sh` was added, then `git log --all --oneline --grep="role-spec-reference-guard"` shows commit `b0d0610a` ("issue-2138: gate retirement (#2144)") removed it — renamed from `on-the-record/hooks/role-spec-reference-guard.sh` to nothing (deleted, not renamed to a skill-prefixed name), unrelated to this sweep. `git ls-tree -r main --name-only | grep -i spec-reference-guard` on that same clone — result: empty (does not exist under any name at on-the-record main HEAD today). `find . -iname '*handoff-contract*'` on that same clone's main checkout — result: empty (`docs/specs/role-handoff-contract.md`, untracked, never existed under that exact path; a *different* path, `contract/role-handoff-contract.md`, appears in old commit history only, per `git log --all --diff-filter=A --name-only | grep -i handoff-contract`). Hand-rewording a citation to an already-dead/never-existent path, rather than inventing a renamed one, is the cautious call, not over-application.

**2. `role`->`skill` reading correctly in context.** Present, no meaning
changes found. I read all 216 changed line-pairs (not just 20) in full
diff context. Zero added (`+`) lines still contain `role`/`역할` —
derived: `git diff 5da544f..pr-117 -- skills | grep -E '^\+' | grep -v '^+++' | grep -ciE '\brole\b|역할'` — result: 0 — confirming the substitution is clean (no leftover or reintroduced occurrences). I specifically hunted for the failure mode the task named — "text about which skill to mount reading as though the skill itself acts" — by grepping the diff for `mount|spawn|invoke|select the|--role|--skill`. derived: same grep — result: 2 hits, both the same untracked dead-path citation described in point 1 above (`docs/specs/role-handoff-contract.md`, untracked, replaced with "the spawning contract") — no mount/activation-language inversion found anywhere.

**3. Classification table totals 384 and reconciles with the diff.**
Present. I independently rebuilt the table from scratch — not by trusting
its printed numbers — using `git archive <sha> -- skills | tar -x` into an
empty directory (never a working-tree grep) at the PR's own merge-base.
derived: `git ls-tree -r 5da544f --name-only -- skills | while read f; do c=$(git show 5da544f:"$f" | grep -noiE '\brole\b|역할' | wc -l); [ "$c" -gt 0 ] && echo "$c\t$f"; done` — result: 116 files, sum 384, matching the table's per-file counts on every single row (`diff` between my derived list, sorted, and the table's 116 rows transcribed from the companion record: exit 0, zero differences). Cross-referencing dispositions: the 81 files the table marks axis-reference/mixed are exactly `git diff --name-only 5da544f..pr-117` (`diff` between the two sorted lists: exit 0), and the 35 files it marks pure-ordinary have zero intersection with the changed-files list (`comm -12`: empty output).

**4. Re-derived counts.** Present. Via `git archive` into empty
directories (base commit 5da544f, PR head c05de12) rather than a
working-tree grep. derived: `find <base-tree-dir> -type f -print0 | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result: 384. `find <head-tree-dir> -type f -print0 | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result: 157. `find <base-tree-dir> -type f -print0 | xargs -0 grep -lZiE '\brole\b|역할' | tr -cd '\0' | wc -c` — result: 116 files. 384 − 157 = 227, matching the claimed axis-reference count exactly, and combined with the 0-added-role-occurrences check in point 2, this confirms 0 remain in the 227-occurrence axis-reference subset — no aggregate coincidence masking a per-line swap.

**5. Skill triggerability.** Present, no breakage found, but 19 files
carry a changed line inside their frontmatter `description:` trigger
block — worth naming explicitly since the task flagged this as a real
risk. derived: `awk '/^diff --git/{f=$0} /^@@.*description:/{print f}' <full.diff>` — result: 19 files (`blameless-postmortem`, `customer-support-research-log`, `experiment-trust`, `hypothesis-testing`, `incident-response-tool-landscape`, `market-analysis-mece-proposal`, `pr-communications-message-planning-and-evaluation-rules`, `product-discovery-hypothesis-testing`, `product-discovery-one-pager`, `release-engineering-deployment-rollout-strategy`, `release-engineering-error-budget-policy`, `release-engineering-readiness-checklist`, `requirements-engineering-rules`, `tech-feasibility`, `technical-feasibility-build-vs-buy-dependency-health`, `technical-feasibility-build-vs-buy`, `technical-feasibility-license-scan`, `technical-feasibility-stride-table`, `test-authoring-isolation-and-fixture-strategy`). In every one of these, the changed text is self-referential meta-description ("the release-engineering role's steady phase" -> "skill's steady phase", "the feasibility role's `probing` state" -> "skill's"), not a literal trigger phrase a real user would type — the actual quoted trigger examples in every changed description (e.g. `accessibility-aria-and-contrast-rules`'s own "ARIA role" trigger text, confirmed untouched in point 1) are unedited throughout, per the same full-diff read as points 1-2. See Open findings #1 below for the one residual unknown this leaves.

**6. Double `Closes` lines.** Present, confirmed via live API calls, not
inference. derived: `gh issue view 2601 --repo tokenmaxxxer/skill-repository` — result: `GraphQL: Could not resolve to an issue or pull request with the number of 2601. (repository.issue)`. derived: `gh pr view 2601 --repo tokenmaxxxer/skill-repository` — result: `GraphQL: Could not resolve to a PullRequest with the number of 2601.` skill-repository has no issue or PR #2601; the bare `Closes #2601` line is confirmed a no-op, and the fully-qualified `Closes tokenmaxxxer/on-the-record#2601` is the only line that does anything on merge.

**Companion record's own self-correction, independently confirmed.** The
companion record's "What did not work" section and its deviation-log file
(paths untracked in this checkout, path/sha cited in Upstream basis below,
read from a fresh on-the-record clone) describe two lines
(`release-engineering-readiness-checklist/SKILL.md:25`,
`release-engineering-error-budget-policy/SKILL.md:64`) that were
mechanically mis-edited on a first pass, then caught and reverted before
the PR landed. canonical: `git show 5da544f:skills/release-engineering-readiness-checklist/SKILL.md | sed -n '25p'` vs `git show pr-117:skills/release-engineering-readiness-checklist/SKILL.md | sed -n '25p'` — result: identical (`research/2026-07-27-role-practice/ops.md`\`):\` on both). Same check on `release-engineering-error-budget-policy/SKILL.md:64` — result: identical. derived: `grep -rn 'skill-practice\|skill-interaction' <head-tree-dir>` — result: 0 matches (no corruption survives anywhere in the final tree).

## Why

The task's stated failure mode is over-application (a session optimizing
for a low residual count damages skills), so the review weight went to
the 227 changed occurrences, not the 157 kept ones — reading the entire
diff rather than sampling it, and re-deriving every count from `git
archive` extractions of a fresh clone rather than trusting either PR's
printed numbers or a working-tree grep in an already-checked-out repo.

## Upstream basis

- `gh pr view 117 --repo tokenmaxxxer/skill-repository` (title, body,
  test plan, base/head shas), sha: same-commit (read live).
- `gh issue view 2601 --repo tokenmaxxxer/on-the-record` (Ask, Acceptance,
  Non-goals — the issue this PR pair claims to satisfy), sha: same-commit.
- Companion record (path untracked in this checkout:
  `docs/issue-2601/reports/technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a.md`)
  and its deviation-log entry (also untracked in this checkout:
  `docs/issue-2601/reports/technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a/deviation-log/20260829T110620985598-2715d7c22381a359.md`)
  — both read from a fresh clone of `tokenmaxxxer/on-the-record` at commit
  `1a5966c18621cc813a85747747dafef1cb90ca8b` (PR #2716's branch tip at
  time of review) — read for their claims only, every claim then
  re-derived independently rather than trusted.
- Fresh clone of `tokenmaxxxer/skill-repository`, PR #117 fetched as
  `refs/pull/117/head`, merge-base `5da544f3bc0ca89f65e1628f5480fb169d35e08a`,
  head `c05de12ac4a14b2b4db87d9d61ced5955b878c16` — all counts and diffs
  in this record are derived from this clone, not from any working tree
  this session had mounted skills from.

## Open findings

1. Point 5 above (trigger-description edits) is Present-with-a-residual-
   unknown, not a clean Absent. derived: same `awk` scan cited in point 5
   — result: 19 files with a changed `description:`-block line, and in
   all 19, `grep -c 'ARIA role\|RBAC\|access-control'` against the
   changed lines returns 0 — none touch a literal domain-keyword trigger
   phrase, only self-referential "the X role" -> "the X skill" meta-text.
   This session's own skill-matching this turn ran on description-text
   semantic match rather than a fixed keyword table (stated in this
   session's own spawn context, not independently tested here), so
   self-referential wording inside a description should not affect real
   trigger matching — but I had no way to run skill-repository's actual
   downstream consumer against before/after description text to
   mechanically confirm zero regression, so this stays open rather than
   closed. Resolution path: if skill-repository's trigger-matching
   consumer becomes testable in isolation, re-run the 19 files' before/
   after description text through it directly.
2. No other open findings — all six numbered attack points from the
   spawning task returned Present (claim holds) after independent
   re-derivation; none returned Absent (claim fails) or Incorrect.

skill-verdict: adversarial-review — applied: invoked; this record's entire method follows the skill's core mechanism (structurally independent evaluator working from raw commands in a fresh clone, blind to the builder's conclusions until each claim was independently re-derived) rather than trusting either PR's stated numbers.
skill-verdict: technical-writing-structure-comprehension — applied: invoked; used while drafting this record's prose to keep sentences within the skill's target range and break dense evidence blocks into per-claim paragraphs rather than one undifferentiated wall of citations.

## Next steps

loop_state: complete — acceptance: `gh pr view 117 --repo tokenmaxxxer/skill-repository --json state,mergeable` — result:
```
{"mergeable":"MERGEABLE","state":"OPEN"}
```
All six requested verification attack points returned Present (see What
was done); no defect was confirmed in either PR. Landing this record
(commit, push, PR against `on-the-record` main) is the only remaining
step.
