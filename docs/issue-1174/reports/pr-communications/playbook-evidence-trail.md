# Evidence trail: pr-communications operational-playbook fan-out (issue #1174)

## What was done
Authored `playbook/message-planning-and-evaluation-rules.md` in the
`pr-communications` role's rulebook repo
(`tokenmaxxxer/pr-communications-rulebook`), on branch
`issue-1174/operational-playbook`, pushed, PR opened:
https://github.com/tokenmaxxxer/pr-communications-rulebook/pull/19
canonical: gh pr view 19 --repo tokenmaxxxer/pr-communications-rulebook --json url,state,number — result: {"number":19,"state":"OPEN","url":"https://github.com/tokenmaxxxer/pr-communications-rulebook/pull/19"}

derived:
```
$ grep -cE '^[0-9]+\.' playbook/message-planning-and-evaluation-rules.md
13
$ grep -c '\*\*REMOVAL' playbook/message-planning-and-evaluation-rules.md
3
```
13 numbered condition -> choice -> source rules across six axes
(objective/channel fit, message hierarchy, approval sequencing,
risk/Q&A prep, evaluation criteria, persuasion technique), 3 of them
REMOVAL-category, one counter-example, one recorded open gap
(release-timing/embargo mechanics, not researched this round).

Ran the batch depth gate locally against the file before pushing:
canonical: python3 gates/playbook_depth_gate.py <rulebook-checkout>/playbook/message-planning-and-evaluation-rules.md --role pr-communications --floor 12 --axes objective-channel-fit,message-hierarchy,approval-sequencing,risk-qa-prep,evaluation-criteria,persuasion-technique — result: "role=pr-communications accepted=12 floor=12 count_ok=True" and a final "PASS" line (one candidate block — the axis-list bullet under the front-matter header — was correctly rejected as not itself a rule).

## Why
Fan-out unit of issue #1174 ("operational playbooks for all roles:
practitioner decision rules in each rulebook"), amendment 1 (deep
three-layer research, source-cited, no pretrained recall) and amendment
4 (removal-category rules required per axis): the operator's
requirement is condition/choice tables at practitioner depth, sourced
per-rule, landed in the role's own rulebook repo (not the marketplace
spec repo, which stays the verification layer).

## Upstream basis
docs/issue-1174/proposals/operational-playbook-program.md

## Evidence trail (fetched sources, this session, 2026-08-13)
1. https://2012books.lardbucket.org/books/public-relations/s10-the-public-relations-process-r.html
   and https://pracademy.co.uk/insights/pr-planning-toolkit/ -> rulebook
   PR rules 1, 2, 3, 13 (audience-first channel choice, per-segment
   messaging, one-core-message removal rule, redundant-supporting-
   message removal rule).
2. https://jobs.prsa.org/career-resources/finding-talent-10/crisis-communications-checklist-24-hour-response-protocol-405,
   https://jobs.prsa.org/career-resources/finding-talent-10/crisis-communication-plan-a-checklist-381,
   https://jobs.prsa.org/career-resources/finding-talent-10/executive-communications-during-crisis-spokesperson-preparation-guide-409
   -> rulebook PR rules 7, 8, 9, 10 (pre-drafted Q&A before first
   statement, named-approver sign-off, shared holding statement across
   spokespeople, stale-entry removal rule).
3. https://amecorg.com/resources/barcelona-principles-4-0/ -> rulebook
   PR rules 11, 12 (outputs/outtakes/outcomes success criteria set
   before send; outcome claims require outtake-level evidence beneath
   them).
4. https://www.davidpublisher.com/Public/uploads/Contribute/5cc1077dd950d.pdf,
   https://virtualspeech.com/blog/ethos-pathos-logos-public-speaking-persuasion,
   https://www.ebsco.com/research-starters/social-sciences-and-humanities/theories-persuasion
   -> rulebook PR rules 4, 5, 6 (proof point required per key message,
   ethos/pathos/logos selection by audience objection type, explicit
   loss-framing under prospect theory).
canonical: playbook/message-planning-and-evaluation-rules.md in
tokenmaxxxer/pr-communications-rulebook@issue-1174/operational-playbook
(this session's own fetch+write, see PR #19 diff) — every numbered rule
line in that file carries its own `Source:` citation to one of the
above.

No pretrained-recall content was used as a rule source; every rule
traces to one of the four fetch angles above (query log and per-angle
findings in scout-brief.md, same directory).

## Current kind and loop_state
kind: report
loop_state: pending-review
canonical: gh pr view 19 --repo tokenmaxxxer/pr-communications-rulebook --json url,state,number — result: state OPEN, no review yet — this record only asserts the PR was opened, not that its content was accepted.

## Open findings
- Channel-specific release-timing/embargo mechanics were not
  researched this round — the four fetched angles covered planning,
  Q&A/crisis, evaluation, and persuasion theory, not release-timing
  specifics.
  next steps: run a targeted fetch on embargo/simultaneous-release
  practitioner guidance and append the rule(s) to the same rulebook
  branch/PR.
  resolution path: one follow-up WebSearch+WebFetch round on
  release-timing mechanics, appended as a commit on
  issue-1174/operational-playbook before that PR merges.
- This fan-out unit covers the pr-communications role only; the parent
  issue's full role set is handled as separate fan-out units, not by
  this record.
  next steps: none owned by this record — other roles' rulebooks are
  out of this session's write scope.
  resolution path: n/a to this unit; tracked at the parent issue level.
