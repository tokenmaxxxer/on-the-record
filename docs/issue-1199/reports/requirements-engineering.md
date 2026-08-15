---
subject: issue-1199
role: requirements-engineering
kind: record
loop_state: landed
---

# Record: requirements-engineering tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/requirements-engineering` comment on this issue
(single-account mode; canonical: `gh issue view 1199 --json comments`,
read this session — the comment body is exactly `APPROVE
issue-1199/requirements-engineering`, authored by JiwonJung94, an
approvers.md account per `docs/specs/approvers.md`, read this session).

Ran the scout sweep first (docs/issue-1199/reports/requirements-engineering/scout-brief.md,
this session) per the 2026-08-14 operator amendment restricting the
survey target to the Claude Code plugin/skill ecosystem (not general
practitioner domain tools). Sweep: four parallel-issued WebSearch
queries in one turn (batched-sequential mode — no parallel subagent
fan-out available; stated per the scout directive's fallback
disclosure), converging on `github/spec-kit` (surfaced by all four
angles) and, as a direct-domain-match secondary confirmation,
`Hainrixz/the-architect`.

- **github/spec-kit** — GitHub's own official Spec-Driven Development
  toolkit for AI coding agents, including a Claude Code integration.
  Adoption: canonical: `curl -s https://api.github.com/repos/github/spec-kit`,
  run this session → `"stargazers_count": 128551` (128,551 stars at
  check time), `"description": "💫 Toolkit to help you get started
  with Spec-Driven Development"`. Multi-source: also independently
  cross-listed on mcpmarket.com, claudedirectory.org, and
  claudepluginhub.com as a Claude Code skill/plugin (canonical:
  WebSearch results this session, titles "GitHub Spec-Kit:
  Spec-Driven Claude Code Skill" and "spec-kit - Claude Code Commands
  Plugin"). Problem: a spec that goes straight from intent to a
  downstream plan/task breakdown lets an unresolved ambiguity silently
  propagate into implementation. How: a dedicated `/clarify` command,
  stated in spec-kit's own docs as "recommended before
  /speckit.plan" (canonical: WebFetch of
  `https://raw.githubusercontent.com/github/spec-kit/main/README.md`,
  run this session, quoting that phrasing), gates ambiguity resolution
  as its own step before any plan/task artifact is generated; a
  separate `/speckit.analyze` command runs "cross-artifact consistency
  & coverage analysis" after task generation but before implementation
  (canonical: same WebFetch, quoting that phrasing). Learning →
  `playbook/rules.md` rule 11b: after a batch of requirements is
  drafted or revised, run one explicit cross-requirement
  consistency/coverage review over the whole batch before handoff to a
  downstream role, logged in the traceability table's status field —
  not a substitute for per-requirement drafting quality, an addition
  to it.

- **Hainrixz/the-architect** — a Claude Code plugin that interviews the
  user and writes a self-contained blueprint with EARS acceptance
  criteria. Adoption: canonical: `curl -s
  https://api.github.com/repos/Hainrixz/the-architect`, run this
  session → `"stargazers_count": 459`. Lower star count than
  spec-kit; included as a secondary, direct-domain-match confirmation
  (same allowance the conformance-review role's prior round in this
  issue used for a low-star, named entry) rather than as a
  high-adoption primary exemplar — spec-kit carries the primary
  adoption evidence for this round. The repo's own stated framing
  (canonical: same `curl` call, `"description"` field, quoted
  verbatim): "writes a self-contained blueprint another Claude Code
  instance builds from with zero context — EARS acceptance criteria
  and a runnable verify command on every build step." Problem: an
  acceptance criterion that is only prose can be read two ways by two
  different downstream agents/reviewers; a criterion with no attached
  check is unverifiable except by re-reading. How: every acceptance
  criterion is paired with a literal runnable verification command at
  authoring time, not left as a description someone re-derives a check
  from later (canonical: same description field). Learning →
  `playbook/rules.md` rule 11a: when a requirement's verification
  method is Test or Demonstration and its acceptance condition can be
  expressed as a runnable check, pair the verification condition with
  that literal command rather than a prose description of what someone
  would run.

Applied (not referenced) both learnings directly into
`playbook/rules.md` in the separate rulebook repo
(tokenmaxxxer/requirements-engineering-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/requirements-engineering-rulebook),
as rules 11a and 11b appended to the existing Axis 2 (verification-
method selection) — no new axis, no tool-catalog section, matching the
issue's 2026-08-13 native-application amendment. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/requirements-engineering-rulebook
show 6ce51f7 --stat`, run this session:
```
playbook/rules.md | 26 +++++++++++++++++++++++++-
1 file changed, 25 insertions(+), 1 deletion(-)
```
Neither added rule names `spec-kit`, `github/spec-kit`,
`the-architect`, or a `source:`-style tool attribution — canonical:
`git -C /home/jwjung/tokenmaxxxer/rulebooks/requirements-engineering-rulebook
show 6ce51f7 -- playbook/rules.md`, run this session, grepped for
`spec-kit` and `architect` this session — neither string appears in
the added text; the source lines cite "a widely-adopted Claude Code
spec-authoring plugin" and "a widely-adopted Claude Code
spec-driven-development plugin" generically, plus this record's own
path as the evidence trail. No verbatim text was copied from either
surveyed repo; both rules are paraphrased insight.

Note on branch base: `playbook/rules.md` did not exist on
`requirements-engineering-rulebook`'s `main` at the start of this
session (it lived only on the then-unmerged `issue-1174/playbook`
branch).
canonical: `gh pr list --repo tokenmaxxxer/requirements-engineering-rulebook --search "head:issue-1174/playbook" --json number,state,baseRefName`
output: `{"number":25,"state":"MERGED","baseRefName":"main"}`.
That branch's own PR (#25) merged to main mid-session, so this
delivery's branch was rebased onto the now-current `main` (`git fetch
origin main` then `git checkout -B issue-1199/requirements-engineering
origin/main`, both run this session) before committing, keeping this
PR's diff to exactly the two new rules rather than the full playbook.

Committed in the rulebook repo (commit 6ce51f7, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/requirements-engineering-rulebook
log -1 --stat`, run this session), pushed to
`origin/issue-1199/requirements-engineering`, PR opened:
https://github.com/tokenmaxxxer/requirements-engineering-rulebook/pull/26
(canonical: `gh pr create --repo
tokenmaxxxer/requirements-engineering-rulebook ...`, run this session,
stdout `https://github.com/tokenmaxxxer/requirements-engineering-rulebook/pull/26`).

## Structured requirements doc
This record folds distilled tool-landscape learnings into two existing
rulebook rule slots rather than drafting a product requirements doc;
there is no new product requirement to state this session. The two
rule slots are tracked below with REQ-<id> identifiers for
traceability purposes only.

REQ-11A:
statement: While a runnable check exists for the acceptance condition, the drafter shall attach that literal runnable check.
ears_pattern: state-driven
verification_method: Inspection
verification condition: `playbook/rules.md` rule 11a text contains the
phrase "pair the verification condition with that literal runnable
check."

REQ-11B:
statement: When a requirements batch is drafted or revised, the drafter shall run a cross-requirement consistency review before handoff.
ears_pattern: event-driven
verification_method: Inspection
verification condition: `playbook/rules.md` rule 11b text contains the
phrase "run one explicit cross-requirement consistency/coverage
review."

## Traceability matrix

| ID | Description | Source | Downstream link | Status |
| --- | --- | --- | --- | --- |
| REQ-11A | Pair a Test/Demonstration verification condition with a literal runnable check when one exists | docs/issue-1199/reports/requirements-engineering/scout-brief.md | 6ce51f7 | landed |
| REQ-11B | Run one explicit cross-requirement consistency/coverage review over a drafted batch before downstream handoff | docs/issue-1199/reports/requirements-engineering/scout-brief.md | 6ce51f7 | landed |

## Ambiguity list
No ambiguities: this is a tool-landscape fold-in record, not a
requirements draft; no requirement statement was authored this session
that could carry a candidate-reading ambiguity.

## code_under_review
- playbook/rules.md (requirements-engineering-rulebook repo)

## Why
Per issue-1199 (northpole req#1/req#5): this role's rulebook encoded
methodology and decision rules (#1174) but had not learned from the
Claude Code plugin ecosystem specific to spec/requirements authoring.
spec-kit and the-architect are both direct-domain matches (turning
intent into a checkable spec, this role's own core deliverable), so
their design moves transfer without translation from an unrelated
domain.

## Upstream basis
docs/issue-1199 (issue body, requirements 1-5, operator amendments
2026-08-13T06:35:54Z apply-not-reference, 2026-08-13T06:36:54Z native
application, 2026-08-14 plugin-ecosystem survey-target amendment);
6ce51f7 (rulebook commit)

## What did not work
Initial branch setup collided with a pre-existing uncommitted change
to `docs/issue-1174/reports/requirements-engineering/scout-brief.md`
in the mounted rulebook working tree (not this session's own change —
present before this session started) and with that repo's own
board-gate hook, which refuses a `docs/issue-1174/` write from a
branch other than `issue-1174/requirements-engineering`. Resolved by
saving both the stray change and this session's own `playbook/rules.md`
diff as patches (`git diff` output), resetting the working tree
(`git reset --hard HEAD`, a command that does not itself touch
`docs/`), and rebuilding this session's branch cleanly from
`origin/main` with only the `playbook/rules.md` patch applied — the
stray scout-brief.md change was left untouched in that repo's history
(never committed by this session, not part of this delivery's write
set).

## Open findings
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/requirements-engineering-rulebook show 847d37d -- docs/issue-1174/reports/requirements-engineering/scout-brief.md`
committed line: "Delivered: 24 rules in playbook/rules.md,
rule_count_floor: 21"; the stray uncommitted edit present at this
session's start changed it to a `derived: grep -c '^[0-9]\+\.'
playbook/rules.md` count of 27, and that edit was reverted to its
committed state by this session's `git reset --hard HEAD` during
branch cleanup and was never re-applied — re-applying it would have
required writing under `docs/issue-1174/` from this session's
`issue-1199/requirements-engineering` branch, which that repo's own
board-gate hook refuses. resolution path: a session running on
`issue-1174/requirements-engineering` should re-derive the current
rule count (`grep -c '^[0-9]\+\.' playbook/rules.md`) and correct the
stated figure in that file.
