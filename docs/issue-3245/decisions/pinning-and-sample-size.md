---
issue: 3245
type: pre-registration-amendment
date_stamp: 2026-09-03
status: registered-before-any-pair-scored-under-this-run
amends: docs/issue-3127/decisions/pre-registration.md
---

# issue-3245 — pinning decision and sample-size extension

Written before `scripts/consumer-path/run_pair.py` is invoked in any
`--execute` mode this session, and before any pair's H2 has been computed
under this run. This is an amendment to, not a replacement of,
`docs/issue-3127/decisions/pre-registration.md` — every field in that
file's Pre-registration form (primary metric (a), threshold/decision
rule (b), guardrail (c), secondary metrics (d)) carries over unchanged.
Two things change here, both before data collection, per that file's own
rule 8 (a decision rule cannot change after seeing results, at any n).

## 1. Skill-set pinning (the issue's own open question)

Issue #3230 measured skill selection disagreeing with itself on identical
input at a 43% rate. If each arm's dispatch independently re-ran
selection, a pair's on/off difference would confound "the skill helped or
didn't" with "the two arms happened to get handed different skills (or
the same skill at different confidence) by an unstable selector" — the
comparison would measure selection noise, not skill value.

**Decision: pin the skill set per pair.** The skill name passed to
`--skills` is fixed before either arm of a pair is dispatched and held
byte-for-byte identical between the on and off arm of that pair (only the
`skill-repo:` source-qualifier prefix differs on the off arm's string,
per `scripts/consumer-path/run_pair.py`'s module docstring — a resolution-
source control, not a different skill). This was already the shape
`scripts/issue-3127/run_consumer_pair.py --skill` established (a single
`--skill` CLI argument shared by both arms' `spawn_command()` calls); this
session does not change that shape, only makes explicit that it is a
deliberate choice, not an accident of the prior script's interface.

**What this answers, and what it does not.** Pinning measures **what a
skill is worth when the orchestrator's selection has already landed on
it** — i.e., given the skill was going to be used, does having its corpus
actually reachable help. It does **not** measure "what today's system
delivers end-to-end," because in production the selector itself might not
have picked this skill for this task, or might have picked it
inconsistently across a hypothetical rerun. A result from this run should
be read as "skill X, once selected, was/was not worth having reachable,"
never as "the system as shipped delivers this margin on this task class" —
that second claim would require running selection itself as part of the
manipulated variable, which is explicitly out of scope here (that is
issue #3230's own measurement, not this one's).

**Which skill.** `product-discovery-hypothesis-preregistration`, unchanged
from `docs/issue-3127/decisions/pre-registration.md` — not re-chosen now,
because two of the four already-provisioned measurement issues (19, 21)
already have real skills-on dispatches under that name (PR #3172, real
PRs #23/#24 in the target repo); picking a different skill for this run
would abandon that continuity for no stated reason, and re-deciding a
skill choice after already knowing those two real dispatches exist would
itself be a form of post-hoc selection this file's own discipline exists
to forbid.

## 2. Sample-size extension: n=2 (registered) -> n>=5 (this run's target)

`docs/issue-3127/decisions/pre-registration.md` registered n=2 minimum,
"extensible to the full n=4 set." Issue #3245 raises the floor further,
citing `docs/issue-3183/decisions/instrument-limitations.md` §3
("single-run-per-arm is not evidence... design target for this instrument
is a minimum of five paired trials"). This is a sample-size increase
stated **before** any pair is scored under this run (`docs/issue-3127/
_assets/consumer-path-results.json` still reads `run_status:
"not_executed"` at the time this file is written) — permitted under rule
8's own terms, which forbid changing the rule *after seeing results*, not
before. The decision rule (b), threshold, and guardrail (c) are unchanged;
only how many pairs must complete before the rule is applied changes,
from 2 to 5.

## 3. What this run can actually reach, decided before running

Two structural constraints, both discovered by inspection before any
dispatch this session (not caution calls made after a result was
inconvenient):

- **gh-guard refuses issue creation from every role session**
  (`runs/rulebooks/tokenmaxxxer-core/core/hooks/gh-guard.sh`, `CLAUDE_SKILL`
  set for this session; `gates/forbidden_action_rule.py` documents the
  same rule: "No role session can create a GitHub issue"). This session
  cannot itself file the additional measurement issues pairs 3-5 need on
  the target repo. Those issue bodies are drafted below
  (`## Open findings`) for the orchestrator/human to file — the sanctioned
  reassignment shape, not a bypass attempt.
- Two of the four already-provisioned issues (19, 21) already have real,
  open PRs from prior sessions' dispatches that predate this issue's
  launcher-owned trust root (`scripts/consumer-path/prepare_arms.py`, PR
  #3185). Those dispatches were never captured in a manifest+transport
  pair this launcher wrote before dispatch, so `verify_manipulation.py`
  correctly excludes them (no manifest on record) — reusing their
  deliverables as if they were trust-rooted would misrepresent what was
  actually checked. This run's own trust-rooted pairs are dispatched
  fresh, under fresh lease-disambiguated branches spawn.py assigns, and
  coexist with (do not replace) those prior PRs.

Given both constraints, this run's realistic ceiling is the number of
pairs this session can dispatch fresh through its own launcher against
the two already-provisioned issue numbers it has (19/20 and 21/22) — at
most n=2 — never the registered n>=5 floor. This is stated here, before
running either pair, exactly so a shortfall against the floor is read as
"the floor was not reached, for a stated structural reason" rather than
retro-fitted after the fact. See the accompanying record's "What did not
work" for what this run actually achieved against this ceiling.
