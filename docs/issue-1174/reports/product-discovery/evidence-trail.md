# Issue #1174 — product-discovery operational playbook: evidence trail

amendments-reconciled: issuecomment-5277049385 read this session
(2026-08-13T06:53:57Z) — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277049385` output read
this turn — body: "Verdict: PR #? -> escalate (depth or impact axis did
not clear)". The comment names no PR number and no role, so it cannot be
tied to a specific PR; treated as a review verdict against some other
role's delivery in the same fan-out round, not clearly this one.
Flagged here for the operator, no content change made in response since
the target is unidentified.

## What was done

Authored playbook/ in tokenmaxxxer/product-discovery-rulebook (local
checkout: /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook),
branch issue-1174/product-discovery, commit 4703b98, pushed to
origin/issue-1174/product-discovery. 5 axis files, one per this
rulebook's 5 skills:

- playbook/jtbd-problem-framing.md — 10 rules
- playbook/opportunity-solution-tree-branching.md — 10 rules
- playbook/rice-ice-prioritization.md — 10 rules
- playbook/hypothesis-preregistration.md — 10 rules
- playbook/guardrail-metric-status.md — 10 rules

Each rule is condition -> choice -> source, with a rule_count_floor: 10
frontmatter per file (moderate tier: N_min = max(8, axes x 2), 5 axes)
and 2 REMOVAL-category rules per axis (amendment 4 of
docs/issue-1174/proposals/operational-playbook-program.md), 50 rules
total.

derived:
```
$ cd /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook && grep -c '^[0-9]\+\.' playbook/*.md
playbook/guardrail-metric-status.md:10
playbook/hypothesis-preregistration.md:10
playbook/jtbd-problem-framing.md:10
playbook/opportunity-solution-tree-branching.md:10
playbook/rice-ice-prioritization.md:10
```

## Why

Issue #1174: role sessions carry methodology pointers, not
practitioner-depth decision rules. This is product-discovery's own
fan-out unit — decompose the domain (problem framing, opportunity
tracking, prioritization, hypothesis registration, guardrail status)
into decision axes and author web-sourced condition->choice->source
rules per axis.

## Upstream basis

docs/issue-1174/proposals/operational-playbook-program.md (this repo).

## PR status — blocked, branch+relay note per fallback

canonical: this turn's own tool-call error text, pasted verbatim — gh
pr create against tokenmaxxxer/product-discovery-rulebook was refused by
on-the-record/hooks/pr-preflight.sh because a new issue comment
(issuecomment-5277049385) landed after session start and the record
file did not yet cite it.

canonical: this turn's own tool-call error text, pasted verbatim — the
follow-up attempt to write that same record path (inside the rulebook
checkout, not this repo, so no working-tree file here to link) was
refused by on-the-record/hooks/approval-gate.sh because no APPROVE
issue-1174/product-discovery comment from an approvers.md account
exists yet.

pr-preflight requires a write to the rulebook repo's own
reports/product-discovery.md record file, which matches the
phase-2-gated pattern (docs/issue-<n>/reports/<role>.md) enforced by
approval-gate.sh in the same repo, and approval-gate refuses that write
pre-approval — this session cannot self-approve. Per this task's own
instruction ("push, open the rulebook PR (or branch+relay note)"),
falling back to branch + relay note:

- Branch: issue-1174/product-discovery on
  github.com/tokenmaxxxer/product-discovery-rulebook, commit 4703b98,
  pushed — canonical: `git log --oneline -1` and `git push` output read
  this turn in that checkout.
- Relay ask: an approver (docs/specs/approvers.md) posts
  "APPROVE issue-1174/product-discovery" on issue #1174, OR opens the
  rulebook PR directly from the pushed branch — either unblocks
  docs/issue-1174/reports/product-discovery.md in the rulebook repo and
  the PR-open step.

## Open findings

- issuecomment-5277049385 ambiguity (see amendments-reconciled line
  above) — canonical: same comment body quoted above. Resolution path:
  operator confirms in the issue thread which PR/role the verdict
  targets.
- No live role-session citation of these rules executed yet (issue's
  Acceptance check 2) — canonical: no such citation found in this
  session's own work above (nothing to cite; the rulebook PR has not
  yet landed). Resolution path: a later product-discovery role session,
  after the rulebook PR lands, cites one of these rules in a real
  judgment and that citation gets logged back to issue #1174.

## Addendum — same deadlock recurs in this repo

canonical: this turn's own tool-call error text, pasted verbatim —
attempting `gh pr create` in this repo (on-the-record) was also refused
by on-the-record/hooks/pr-preflight.sh, this time citing a second new
issue comment, issuecomment-5277087571 (an automated "Judgment opened"
notice about this branch, read via `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277087571` this turn),
demanding the same amendments-reconciled line in this repo's own
docs/issue-1174/reports/product-discovery.md — the identical
phase-2-gated path pattern, so the identical approval-gate deadlock
applies here too. Not retrying further PR-open attempts, since each
retry risks surfacing yet another post-spawn comment and re-triggering
the same block; commit+push stands as this session's completion per the
task's own branch+relay fallback.

## Next steps

- Approver posts "APPROVE issue-1174/product-discovery" on issue #1174
  (or opens the rulebook PR directly), unblocking the rulebook repo's
  own record write and PR creation — canonical: the PR-status section
  above.
- Once merged, execute the Acceptance-check-2 live citation.
