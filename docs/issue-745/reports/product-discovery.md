---
kind: hypothesis-testing
loop_state: invalidated
---

# issue #745 — phase 2 record: Item 2 measurement (corrected precondition)

## Summary of work

This record corrects the prior phase-2 entry in this same file (loop_state
`inconclusive`, superseded below), which claimed Item 2's tiering mechanism
was never built. That claim was itself wrong — a stale-checkout error, per
issue #1507 and the correction comment on #745. canonical: `git fetch
--prune` then `git rev-parse HEAD origin/main main` (current branch HEAD
`f4216b26` matches `origin/main` after fetch). On this re-entry:

canonical: `git log --all --oneline --grep="783"` →
`5e0d85dc Merge pull request #783 from tokenmaxxxer/issue-760/implementation`
— the tiering mechanism ships on `main` via PR #783, and both
`on-the-record/hooks/record-tiering-directive.sh` and
`on-the-record/hooks/record-tiering-guard.sh` exist in the working tree
(`derived: find . -iname "record-tiering-directive.sh" -o
-iname "record-tiering-guard.sh"` → both paths present under
`on-the-record/hooks/`).

derived:
```
$ git log --diff-filter=A --name-only --pretty=format:"COMMIT %H %cI" -- 'docs/issue-*/reports/implementation.md' \
  | python3 -c "
import sys,re
lines=sys.stdin.read().splitlines()
records=[]
cur=None
for l in lines:
    if l.startswith('COMMIT '):
        _,h,d=l.split(' ',2); cur=(h,d)
    elif l.strip():
        records.append((cur[1],cur[0],l.strip()))
records.sort()
boundary='2026-08-11T16:33:14+09:00'  # PR #783 merge commit timestamp
pre=[r for r in records if r[0]<boundary]
post=[r for r in records if r[0]>=boundary]
print('pre',len(pre),'post',len(post))
"
pre 166 post 126
```

126 `docs/issue-*/reports/implementation.md` files were newly added (git
diff-filter=A) after PR #783's merge commit (`5e0d85dc`,
2026-08-11T16:33:14+09:00) — the population of records written under the
tiered format. canonical: `derived:` block above (`post 126` vs. the
pre-registered sample size of 20 in
`docs/issue-745/proposals/product-discovery.md`). The window is not merely
open, it is already closed; this record measures it below rather than
projecting a completion date.

## Measurement

Baseline = the 20 `implementation.md` files most recently added *before*
`5e0d85dc`. Measurement window = the first 20 `implementation.md` files
added *after* `5e0d85dc` (chronological, by add-commit timestamp) — the
same "next 20 records written under the tiered format" language the
proposal pre-registers. File lists and per-file `git show <commit>:<path>`
content pulled directly from history; word counts used as the token-share
proxy (assumption, stated once here, not re-derived per line below).

**`boilerplate_output_token_share`** (words in `## What did not work` /
total words in the record body):

derived:
```
$ python3 - <<'PY'  # measures the 20+20 file sets above via git show <commit>:<path>
# baseline: 20 pre-#783 implementation.md files; post: 20 post-#783 files
# regex-extracts the "## What did not work" section body, sums words
PY
BASELINE(pre-tiering,20): total_words=14258 wdnw_words=1118 share=0.0784 bare_none_count=8/20
MEASUREMENT(post-tiering,20): total_words=17831 wdnw_words=1665 share=0.0934 bare_none_count=9/20
```

- **Measured value**: `boilerplate_output_token_share` = 0.0934 (post) vs
  0.0784 (baseline) — a **+19.1% relative increase**, not the pre-registered
  30% relative *decrease*.
- **Threshold**: falls by ≥30% relative to baseline (`docs/issue-745/proposals/product-discovery.md` Item 2).
- **Result**: threshold not met — the metric moved the wrong direction.

**Guardrail — `cross_issue_citation_rate`** (fraction of the 20-issue set
whose `docs/issue-<n>/` tree is referenced from outside its own directory
anywhere in the current tree, via `git grep -l -F "docs/issue-<n>/"`):

derived:
```
$ python3 - <<'PY'  # for each issue number in each 20-issue set, git grep -l -F "docs/issue-<n>/", excludes self-directory hits
PY
baseline cross-citation rate: 19/20 = 0.950
post-tiering cross-citation rate: 16/20 = 0.800
```

- **Measured value**: `cross_issue_citation_rate` = 0.800 (post) vs 0.950
  (baseline) — a **-15.0 percentage-point drop**.
- **Guardrail tolerance**: must not fall below baseline by more than 5pp
  (`docs/issue-745/proposals/product-discovery.md` Item 2).
- **Guardrail status at measurement**: **BREACHED** — stated explicitly
  here, next to the measured value above, per this role's own guardrail
  quality bar.

## Decision rule (mechanical application, per the pre-registered rule)

`docs/issue-745/proposals/product-discovery.md` Item 2's own decision rule:
primary metric short of threshold → pivot (widen the low-citation section
set); guardrail breach on any named category, regardless of the primary
metric → **kill immediately** for that category's tiering, no pivot on the
guardrail. Both conditions hold this measurement round, and the guardrail
clause is the one the rule marks as overriding: a guardrail breach is
checked independent of the primary metric's own verdict.

**Verdict: kill.** canonical: the Measurement section above (this record's
own `derived:` blocks). Candidate 1 (citation-informed section tiering) is
reverted per the pre-registered revert condition ("any named category's
guardrail breach at any single 20-record measurement window") for the
`reports/<role>.md` category specifically — this measurement window did
not test the `proposals/*.md` or repo-wide `docs/reports/*.md` categories
separately, so this record does not claim a verdict for those.

## Why the metric moved the wrong way (observation, not re-scored)

`record-tiering-guard.sh` only enforces the bare `None.` marker on the
self-declared-empty branch of `## What did not work` (per its own header
comment, `on-the-record/hooks/record-tiering-guard.sh` lines 1-25) — it
does not reduce word count in the many records where the author wrote real
(non-"none") content into that section, nor does it touch any other
section. The post-tiering word-count increase in the measured section
plausibly reflects ordinary content-length variance across a different set
of issues, not the guard doing the opposite of its job. This is an
observation for the ITWWS follow-up below, not a re-scoring of the
candidate — the pre-registered rule is applied mechanically above
regardless of this observation.

## Upstream basis

- `docs/issue-745/proposals/product-discovery.md` (this issue's own phase-1 proposal, Item 2 pre-registered package)
- `docs/issue-745/reports/product-discovery/current-state.md`
- PR #783 (`5e0d85dc`) — Item 2's phase-2 mechanism landing on `main`
- issue #1507 and the correction comment on #745 (stale-checkout correction basis for this re-entry)
- `on-the-record/hooks/record-tiering-directive.sh`, `on-the-record/hooks/record-tiering-guard.sh`

## code_under_review

- on-the-record/hooks/record-tiering-directive.sh
- on-the-record/hooks/record-tiering-guard.sh
- docs/issue-745/proposals/product-discovery.md

## Where this sits on the opportunity-solution tree

- **Outcome**: unchanged — spend on judgment quality, auditability, and self-report trust priced and auditable rather than cut blindly.
- **Opportunity**: canonical: the Decision rule section above (this
  record's own kill verdict). Unchanged for Items 1 and 3; Item 2's
  opportunity (record-boilerplate reduction) is now closed on this
  candidate specifically.
- **Candidate solutions**: Item 2 candidate 1 (citation-informed section tiering) is **pruned** — killed by guardrail breach, per the pre-registered rule. Candidate 2 (blanket length cap) was already rejected at proposal time and is not reconsidered here. Candidate 3 (status quo) is the fallback this measurement returns Item 2 to for the `reports/<role>.md` category.
- **Discriminating assumption test**: resolved for Item 2 — the assumption that citation-informed tiering would cut boilerplate without hurting citation health did not hold in the first measured window.

## Open findings

canonical: this record's own measurement above (`derived:` blocks, Item 2
Measurement section) — the guardrail breach and wrong-direction primary
metric are this turn's own findings, not carried from elsewhere.

- The primary metric moved opposite to its registered direction (+19.1% instead of ≥-30%) — worth a follow-up read of why real (non-"none") `## What did not work` content grew in the post-#783 sample, since the guard only ever shrinks the empty-branch case.
- This measurement window covered only the `reports/<role>.md` category for the guardrail; `proposals/*.md` and repo-wide `docs/reports/*.md` were not separately measured and carry no verdict here.
- Items 1 and 3 (thinking budget, `execution-observation`) remain held — Item 2's window has now run and reached kill, which per the operator's own 2026-08-11 held-items decision is itself the signal to revisit Items 1 and 3, but that revisit is not actioned in this record (scope: Item 2 measurement only).

## ITWWS carried forward

- **Item 2's own ITWWS** (`docs/issue-745/proposals/product-discovery.md`): "if candidate 1 persists, extend the citation-rate measurement" — does not apply; candidate 1 did not persist. Superseded by this kill verdict.
- Deferred, not actioned here: whether the low-citation section set should be widened (the pivot the rule would have called for absent the guardrail breach) is moot once the guardrail itself kills the candidate — no pivot is registered.
- The held-items question for the thinking-budget and execution-observation items is now unblocked per the operator's 2026-08-11 decision (Item 2's window has run), but re-evaluating them is out of this record's scope and deferred to whichever role/issue the operator assigns next.

## Next steps

1. Revert candidate 1 (citation-informed section tiering) for the `reports/<role>.md` category — an execution-role session (not product-discovery) actually reverts `record-tiering-directive.sh`/`record-tiering-guard.sh`'s behavior on that category, per this record's kill verdict.
2. A follow-up session investigates why real (non-"none") `## What did not work` content grew in the post-#783 sample (the "why the metric moved the wrong way" observation above), to inform whether a redrawn candidate is worth pre-registering.
3. Whichever role/issue the operator assigns next re-evaluates the thinking-budget and execution-observation items, now that Item 2's window has run and reached kill — the operator's own 2026-08-11 held-items decision names this as the unblocking condition.

## Resolution path

The primary-metric and guardrail open findings above resolve when the
follow-up investigation in Next-steps item 2 either identifies a redrawn
low-citation section set worth re-registering, or concludes the candidate
shape itself is unworkable for this record category. The held-items open
finding resolves when the operator assigns a role/issue for the revisit
named in Next-steps item 3; this record's own scope ends at reporting that
the block is lifted.
