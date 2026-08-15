---
subject: issue-1199
role: product-discovery
kind: current-state-survey
---

# Current-state survey: product-discovery tool-landscape fold-in (issue-1199)

## Background/context
Issue #1199 (per northpole req#1/req#5) asks every role to survey the
most-adopted Claude Code plugins/skills in its own domain, analyze what
problem each solves and how, and fold the learnings natively into the
role's rulebook (no tool-catalog section, per the 2026-08-13
native-application amendment). The 2026-08-14 operator amendment
restricts the survey target to the Claude Code plugin ecosystem itself,
not general practitioner tools.

## Problem, stated without any solution attached (JTBD tuple)
The issue text names a solution up front ("survey plugins, fold learnings
in") — restating the underlying problem in the customer's terms:

- **Job performer**: this repository's product-discovery role (and, by
  extension, any team relying on its rulebook to make discovery-phase
  judgment calls).
- **Job**: decide, at each discovery-phase judgment point (which
  assumption to test next, which sibling solution to prototype first),
  what to do next when more than one option is technically valid.
- **Circumstance**: the role's rulebook already encodes methodology
  (JTBD framing, OST structure, RICE/ICE scoring, pre-registration) but
  was built without reference to how practitioners' own tooling resolves
  *ties* between multiple valid next steps — the rulebook states the
  structure but under-specifies the ordering rule within it.
- **Desired outcome**: when two or more assumptions or solution branches
  are simultaneously eligible for the next test, the rulebook already
  supplies a non-arbitrary tie-breaking rule, instead of leaving that
  call to unexamined judgment each time.

Gap: the issue's framing ("fold learnings in") is itself the solution;
the problem underneath it, restated above, is narrower than "improve the
rulebook generally" — it is specifically about missing tie-breaking
rules at two named judgment points.

## Opportunity-solution-tree placement
- **Outcome**: rulebook judgment calls resolve ties non-arbitrarily.
- **Opportunity**: practitioners' own most-adopted tooling may already
  encode a tie-breaking design move the rulebook currently lacks.
- **Candidate solutions**: (a) survey Claude Code plugins in this
  domain and paraphrase in any tie-breaking design move located; (b)
  invent a tie-breaking heuristic from first principles with no outside
  evidence.
- **Discriminating assumption test**: does a broadly-adopted plugin
  (evidenced by stars/forks/multi-source mention) encode a concrete
  design move for this exact tie, and does paraphrasing it into a rule
  keep the rulebook's existing structure intact (no attribution, no
  bloat)? canonical: this session's WebSearch/WebFetch results (`curl -s
  https://api.github.com/repos/phuryn/pm-skills` → 25262 stars; WebFetch
  of `github.com/deanpeters/Product-Manager-Skills` quoting "recommends
  the best proof-of-concept to test first") — answer: yes for both named
  judgment points, so branch (a) is the one taken below.

## Existing rulebook state (five axes)
canonical: `ls /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/`,
run this session:
```
guardrail-metric-status.md
hypothesis-preregistration.md
jtbd-problem-framing.md
opportunity-solution-tree-branching.md
rice-ice-prioritization.md
```
Each file already carries `rule_count_floor: 10` and 10 rules
(canonical: `grep -c '^[0-9]*\.' /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/*.md`,
run this session — each file returns 10). This fold-in extends two of
the five (hypothesis-preregistration, opportunity-solution-tree-branching)
with one new rule each, at the two judgment points named above where no
existing rule (canonical: same `grep`/read of both files this session)
states a tie-breaking order.
