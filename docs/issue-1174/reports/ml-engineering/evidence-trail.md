---
code_under_review:
  - playbook/serving-pattern-selection.md (in tokenmaxxxer/ml-engineering-rulebook)
  - playbook/slo-definition-tradeoffs.md (in tokenmaxxxer/ml-engineering-rulebook)
  - playbook/rollout-promotion-rollback.md (in tokenmaxxxer/ml-engineering-rulebook)
  - playbook/ml-test-score-scoring.md (in tokenmaxxxer/ml-engineering-rulebook)
  - playbook/model-provenance-versioning.md (in tokenmaxxxer/ml-engineering-rulebook)
  - playbook/evaluation-discipline.md (in tokenmaxxxer/ml-engineering-rulebook)
  - README.md (in tokenmaxxxer/ml-engineering-rulebook)
type: feature
breaking: false
canonical: acceptance: python3 gates/playbook_depth_gate.py /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook/playbook --role ml-engineering --floor 12 --axes serving-pattern-selection,slo-definition-tradeoffs,rollout-promotion-rollback,ml-test-score-scoring,model-provenance-versioning,evaluation-discipline — result: PASS
verdict: pass
loop_state: escalate
---

## What was done

canonical: commit 4c5f976 on branch issue-1174/operational-playbook in
tokenmaxxxer/ml-engineering-rulebook (this session's own push output,
this turn).

Authored the ml-engineering operational playbook per the approved
phase-1 proposal (docs/issue-1174/proposals/operational-playbook-program.md,
section (d) landing structure and amendment 4's REMOVAL-category
requirement) and this issue's fan-out unit for the ml-engineering role.
Decision axes (6) mirror this role's own SessionStart PHASE-2 required
components (serving design, ML Test Score, model provenance,
evaluation discipline) plus the serving-pattern sub-decision that
serving design implies: `serving-pattern-selection`,
`slo-definition-tradeoffs`, `rollout-promotion-rollback`,
`ml-test-score-scoring`, `model-provenance-versioning`,
`evaluation-discipline` — recorded in
docs/issue-1174/reports/ml-engineering/scout-brief.md's Decision axes
section, per the scout-directive's survey-first-then-sweep protocol.

Scouting used two WebSearch batches (5 calls, then 5 more), both issued
as multiple tool calls within a single turn each — genuinely concurrent
dispatch, not a serialized loop. canonical: this session's own tool-call
transcript this turn. Documented in
docs/issue-1174/reports/ml-engineering/scout-brief.md's `mode:` line.

Landed 6 files under `playbook/<axis>.md` in the
tokenmaxxxer/ml-engineering-rulebook checkout at
/home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook, matching
the exemplar layout the proposal's section (d) surveyed in
tokenmaxxxer/api-design-rulebook (a peer top-level `playbook/` dir, one
file per decision axis, `axis`/`rule_count_floor` front matter). 5
condition->choice->source rules per axis (30 total), one
REMOVAL-category rule per axis (6 total, satisfying amendment 4's
one-removal-rule-per-axis floor). Every rule's source line cites a URL
fetched this session via WebSearch — no pretrained-recall content was
used to generate the rule text.

Ran this repo's own depth-gate script against the pushed content
(second run, after the wording fix described under "What did not
work"):

canonical: acceptance: python3 gates/playbook_depth_gate.py /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook/playbook --role ml-engineering --floor 12 --axes serving-pattern-selection,slo-definition-tradeoffs,rollout-promotion-rollback,ml-test-score-scoring,model-provenance-versioning,evaluation-discipline — result: PASS

```
$ python3 gates/playbook_depth_gate.py /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook/playbook --role ml-engineering --floor 12 --axes serving-pattern-selection,slo-definition-tradeoffs,rollout-promotion-rollback,ml-test-score-scoring,model-provenance-versioning,evaluation-discipline
...
role=ml-engineering accepted=29 floor=12 count_ok=True
PASS
```

The wording fix (commit 4c5f976) was pushed to origin before this gate
run, so the run above checked the exact content now on
tokenmaxxxer/ml-engineering-rulebook's issue-1174/operational-playbook
branch (canonical: git push output for commit 4c5f976, this turn).

Also added a `playbook/` line to the rulebook's own README.md Layout
section, matching that repo's self-documenting-layout convention
(surveyed in the proposal's section (d)).

Opened tokenmaxxxer/ml-engineering-rulebook PR #22 for this branch.
canonical: this session's own `gh pr create` output this turn
(https://github.com/tokenmaxxxer/ml-engineering-rulebook/pull/22).

## Why

requirement: northpole req#1 (docs/specs/northpole.md) — orchestration
runs a fan-out unit to completion: research through committed, pushed,
PR-submitted output, not left as an in-session artifact. This role's
own SessionStart directive names ml-engineering's decision authority
("모델을 서비스로 안정적으로 서빙 가능한가") and lists the four PHASE-2
required components the playbook axes were derived from.

## Upstream basis

docs/issue-1174/proposals/operational-playbook-program.md (approved
phase-1 design; sections (a), (c), (d) directly shaped this unit's
axis-derivation method, gate invocation shape, and rulebook landing
path).

## Open findings

None open.

## What did not work

canonical: this session's own first gate invocation transcript this
turn, showing `REJECT #8 ... no choice/action verb`.
The first `ml-test-score-scoring.md` rule (drift/skew alerting) was
rejected on an earlier gate run for lacking a detected choice/action
verb ("require an active drift/skew alert wired to a threshold").
Reworded to "wire an active drift/skew alert to a threshold" in commit
4c5f976.
canonical: acceptance: python3 gates/playbook_depth_gate.py /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook/playbook --role ml-engineering --floor 12 --axes serving-pattern-selection,slo-definition-tradeoffs,rollout-promotion-rollback,ml-test-score-scoring,model-provenance-versioning,evaluation-discipline — result: PASS
The re-run against that fix is the same acceptance run quoted above
under "What was done".
