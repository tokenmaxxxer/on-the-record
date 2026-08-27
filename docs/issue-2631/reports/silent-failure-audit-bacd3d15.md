---
issue: 2631
role: silent-failure-audit-bacd3d15
author: silent-failure-audit-bacd3d15
skills: silent-failure-audit (skill-repository(297e350))
verifies_subject: true  # this record independently re-verified PR #2633's already-accepted deliverable for issue-2631 after rebase, per docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md (untracked on this session's own branch — lives on branch issue-2631/architecture-interface-contract-shape+model-routing-e54786b2)
    sha: c6894bdfa6cb63bf44e18ee317013c9310c1b6d9
---

# issue-2631 — silent-failure-audit-bacd3d15 record

## What was done

Rebased PR #2633 (branch
`issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`)
onto current `origin/main` and independently re-verified its
already-accepted code did not change in the process. The user reported PR
#2633 as CONFLICTING/DIRTY against main, with the conflict isolated to
`docs/reports/product/priorities.md` — an append-only log where both PR
#2633 and PR #2632 (issue #2629, landed meanwhile as `3567f44c`) had
appended an entry to the same tail.

Local branch `pr2633-local` was fetched from
`issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`
and rebased onto `origin/main`. `git rebase origin/main` produced exactly
one conflict, in `docs/reports/product/priorities.md`, on the second of
two commits — matching the user's report. Resolved by removing the three
conflict markers and keeping both entries, in chronological order: main's
already-landed issue-2629 entry first (unchanged), then this branch's
issue-2631 entry appended after it (unchanged content on both sides —
only the markers were removed). `git rebase --continue` completed with no
further conflicts.

canonical: `git log --oneline origin/main..HEAD` on the rebased branch —
`c6894bdf issue-2631: log deviation (broken spec_index.py generator) and
capture operator ruling` / `a4b5f638 issue-2631: remove both surviving
role-name lists` — two commits, matching the pre-rebase PR exactly (no
squash, no drop).

Re-ran the acceptance greps against the rebased tree — all zero matches,
unchanged from the pre-conflict state the user reported verifying:
```
grep -n 'if role in' gates/model_routing.py       -> (no output)
grep -n '"roles":' gates/model_routing.py         -> (no output)
grep -n 'BAR_ROLES' on-the-record/hooks/quality-bar-gate.sh -> (no output)
```

Re-ran the two behavioral checks on the rebased tree:
```
$ python3 -c "
from gates.model_routing import route_model, DEFAULT_POLICY
for name, sp, v in [('architecture', True, None), ('architecture', False, False),
                     ('silent-failure-audit', False, None), ('coding', True, None),
                     ('coding', False, False)]:
    print(name, sp, v, '->', route_model(single_phase=sp, design_bearing_verdict=v, policy=DEFAULT_POLICY))
"
architecture True None -> ('sonnet', 'single-phase-tier:mechanical')
architecture False False -> ('sonnet', 'default-tier:mid-design')
silent-failure-audit False None -> ('sonnet', 'default-tier:mid-design')
coding True None -> ('sonnet', 'single-phase-tier:mechanical')
coding False False -> ('sonnet', 'default-tier:mid-design')
```
`route_model()` takes no `role` argument in this signature — role is no
longer a routing input for any subject, including the four names
(`architecture`, `ux-engineering`, `brand-design`, `content-design`) that
used to be forced onto the `judgment` tier.
```
$ cd gates && python3 -c "
from quality_bar import classify
print('PASS', classify(bar_scoped=True, verdict='bar-met', record_author_account='alice', producer_account='bob'))
print('REFUSE', classify(bar_scoped=True, verdict='bar-not-met', record_author_account='alice', producer_account='bob'))
"
PASS ('BAR_MET', None)
REFUSE ('BAR_NOT_MET', 'bar-not-met verdict recorded')
```
`classify()` takes no role-name argument and no `BAR_ROLES`-shaped list is
consulted anywhere in its body (`gates/quality_bar.py` read in full).

Pushed the rebased branch with
`git push origin HEAD:"issue-2631/architecture-interface-contract-shape+model-routing-e54786b2" --force-with-lease`.

canonical: `gh pr view 2633 --json mergeable,mergeStateStatus` after push
(polled once, 8s later) — `{"mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}`.

Added a product-capture entry to `docs/reports/product/priorities.md` (this
session's own branch) recording the append-only-log conflict pattern the
user flagged — the user asked it be mentioned for the record, not fixed
in this PR.

## Why

The user explicitly scoped this session to the rebase mechanics only
("The code is verified and accepted — do not redo or re-design it," "If
the rebase surfaces any conflict beyond `priorities.md`, stop and report
it rather than resolving it"). Keeping both `priorities.md` entries
rather than picking one was the only option consistent with "neither
entry is wrong and neither supersedes the other" — both are independent,
dated, sourced operator-ruling entries in an append-only log; dropping
either would silently lose a recorded ruling. Re-running the acceptance
greps and the two behavioral checks after rebase (rather than trusting
the pre-rebase verification alone) follows the user's own instruction
that "a rebase can silently pick up a changed dependency" — this session
independently re-confirmed rather than re-asserting the prior claim.

## What did not work

None.

## Upstream basis

- `docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md`
  — untracked on this session's own branch; lives on branch
  `issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`
  — the accepted proposal/build this record verifies the rebase of; not
  amended by this session.
- Commit `a4b5f638` ("issue-2631: remove both surviving role-name lists")
  and `c6894bdf` ("issue-2631: log deviation (broken spec_index.py
  generator) and capture operator ruling") on
  `issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`,
  both rebased onto `origin/main` (`3567f44c`) unchanged in content, only
  parent history rewritten.

## Open findings

None. `docs/reports/product/priorities.md`'s lack of conflict-elimination
sharding (unlike `consult-log.md`, sharded per #2333) is noted above as a
known, unfixed conflict surface — explicitly out of scope for this
session per the user's instruction, not an open finding requiring
resolution here.

## Next steps

None — PR #2633 is `MERGEABLE`/`CLEAN` against `origin/main`; this
session's own branch carries only this record and the priorities.md
product-capture entry, no code changes of its own.

skill-verdict: silent-failure-audit — not-applicable: this session's task was a git rebase and behavioral re-verification of already-accepted code, not new error-handling code to audit for silently-absorbed failure paths.
skill-verdict: work-in-english — not-applicable: all repository-bound output (commits, this record) was already authored in English; no Korean-to-English conversion was needed.
