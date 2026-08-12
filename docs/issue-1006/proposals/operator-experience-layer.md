---
status: proposed
files:
  - on-the-record/hooks/directive.sh
  - docs/handbooks/operator-experience.md
  - harness/fixture-operator-experience/test_flow.py
  - harness/fixture-operator-experience/seed_vague.json
  - harness/fixture-operator-experience/seed_precise.json
  - gates/operator_experience.py
---

Subject: issue-1006

## Intent

An operator opens an installed on-the-record session, converses in plain
language, and everything else — issue drafting, spawning, verification,
merge, reporting — is delegated by default. The current-state survey
(`docs/issue-1006/reports/product-discovery/2026-08-12-survey.md`) found 3
of 5 sub-requirements already substantially built in `directive.sh`; this
proposal covers the two genuinely open ones (first-contact interaction
guidance, requirement-elicitation trigger) plus one legibility seam
(mid-flight narration while background work is armed), and adds the
harness scenario the issue's acceptance names.

## Constraints (carried from the issue and role directives)

- Plugin elements only, default-on — no new opt-in flag (issue req#7).
- Compose with landed machinery, do not re-derive it: requirement-digest
  (#943/#970), deviation loop (#958/#988), 4-part `final_report` (#878).
  Panel (#985) was searched for in this repo tree and not found — no
  landed panel mechanism exists to compose with, so this proposal composes
  only with the three mechanisms actually located.
- Everything on the record (issue req#2) — elicitation output must land in
  the same requirement-capture path directive.sh already describes, not a
  side channel.
- Two-phase flow: this PR stops after research + proposal; the harness
  fixture and gate are phase-2 (implementation) deliverables, listed in the
  frozen write set above so approval covers them, but not built this turn.

## What will be done (design, for phase-2 to build)

**A. First-contact guidance (req#3).** A new block appended to
`directive.sh`'s existing heredoc, gated the same way `poll_rearm_arm_if_due`
already checks state (a marker file under the workspace, e.g.
`.orchestrate-greeted`, written on first fire) so it prints once per
workspace, not every turn — the existing injection already runs every
`UserPromptSubmit`, so an ungated block would repeat itself and violate the
"surfaced by the session itself, not read from docs" requirement by being
noisy rather than informative. Content: 3-4 lines in operator language —
what to say (plain requirements, no skill names needed), what happens next
(issueize → spawn → verify → merge → report, one line), what they'll be
asked (approve/reject at PR points only). Mirrors the register of
`directive.sh`'s own "REPLY STRUCTURE" section, not repo-doc prose.

**B. Requirement-elicitation trigger (req#4).** A branch inserted before
directive.sh's existing "Requirements become ISSUES" line: when the
orchestrator judges the user's ask does not yet carry a testable
`## Acceptance`-shaped criterion (the same shape `requirement-digest.md`
and the ACCEPTANCE FORMAT section already require for issues), it asks 1-3
targeted clarifying questions in-conversation before drafting the issue —
routed through the `requirements-quality` and/or `user-discovery` skills
per their existing trigger conditions, not a new skill. Empty-state path
(precise ask): the existing issue-drafting line fires unchanged, no
detour — this is the acceptance criterion's "empty state: a precise
requirement skips elicitation and goes straight to delegation."

**C. Mid-flight narration (req#5 gap).** One line added at the TURN-BUDGET
RULES arming point (`directive.sh:130-137`'s existing "close the turn the
moment remaining work is armed" instruction): state what was armed and
what event ends the wait, in the same operator-language register as
REPLY STRUCTURE, before the turn closes — not a new narration mechanism,
one more sentence at an existing decision point.

**D. Requirement traceability at completion (req#1 gap).** The AUTONOMOUS
ASYNC COMPLETION section's verify step gains one clause: cite which
requirement (issue number / requirement-digest entry) the merged PR
answers, so the 4-part `final_report` names the requirement it closes, not
just "PR merged."

**E. Harness scenario.** `harness/fixture-operator-experience/test_flow.py`
follows the `fixture-requirement-digest` + `gates/requirement_digest.py`
pairing shape: two seeded conversations (`seed_vague.json`,
`seed_precise.json`), asserting the vague path hits elicitation before
issue-drafting and the precise path does not, per the issue's stated
acceptance and empty-state text.

## Out of scope

- Building A-E's code (phase-2, pending approval).
- The panel (#985) — not found in this tree; if it lands before phase-2
  starts, phase-2 re-checks composition against it, but this proposal does
  not invent a stand-in.
- Any change to spawn.py, role rulebooks, or gate mechanics beyond the one
  new `gates/operator_experience.py` and fixture pair listed in the write
  set.

## How this will be known to work

- `harness/fixture-operator-experience/test_flow.py` passes locally,
  demonstrating: vague ask → elicitation → precise requirement captured →
  delegated run → legible narration → role-verified completion report (the
  issue's own acceptance wording).
- The precise-ask seed skips straight to delegation (empty-state check).
- A hunt dispatch on this proposal (per the warrant directive) finds no
  contradiction between A-D's directive.sh additions and the existing
  DELEGATION-IS-DEFAULT / TURN-BUDGET-RULES text they're inserted next to.

## What did not work

None.
