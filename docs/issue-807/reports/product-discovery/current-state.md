---
kind: current-state-survey
---

# Current-state survey — issue #807

## Background / context

code_under_review:
- roles/specs/*.spec.json (43 files)
- docs/specs/northpole-harness.md
- harness/signals.py
- docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-design.md
- docs/issue-776/reports/execution-observation.md

Northpole reqs #1/#3/#4/#5 depend on each of the ~43 roles being able to
render a real domain judgment, not just fire and produce a plausible
record. #776 already built and specced a harness (`harness/`,
`docs/specs/northpole-harness.md`) — but its 7 signals all check
wiring-shaped facts (delegation event present, record readable, build
exit code, report has 4 named parts, no human-input stall, one canonical
requirement record, precondition holds). canonical:
`docs/specs/northpole-harness.md` §3 (read in full this session) — none
of the 7 rows mentions the CONTENT validity of a role's domain judgment;
row 3's own build+run check is the closest thing to a content check and
it only verifies the *fixture's* pass/fail, not any role's reasoning.

Each `roles/specs/*.spec.json` already carries a `source_standard` field.
derived:
```
$ python3 -c "
import json,glob
n=0
for f in sorted(glob.glob('roles/specs/*.spec.json')):
    d=json.load(open(f))
    if d.get('source_standard'): n+=1
print(n, 'of', len(glob.glob('roles/specs/*.spec.json')))
"
43 of 43
```
canonical: `roles/specs/security-threat-model.spec.json` (read in full
this session) — `source_standard` names STRIDE/OWASP Threat Dragon,
`required_fields` enumerates the STRIDE category enum, `reference_
resolution` and `recomputation` each name a `checked_by` mechanical
guard script or a stated `TBD` follow-up. So the SCHEMA-CONFORMANCE half
of "valid deliverable" (does the record use the right fields, in the
right shape, per a named external standard) is already wired for all 43
roles, with a real citation.

What is NOT present, checked directly against the issue's three
capacities: canonical: `roles/specs/*.spec.json` schema (`role`,
`source_standard`, `required_fields`, `reference_resolution`,
`recomputation`, `write_scope`, `loop_state`, `use_when` — the full key
set across all 43 files, read via the same script above) has no field
for (a) the role's JUDGMENT method (how it reaches a defensible call,
distinct from the deliverable's field shape), (b) an explicit "what does
a hollow-but-plausible instance of this deliverable look like, and how
would a reviewer catch it" statement, or (c) the role's FINDING method
(how it surfaces requirements/defects only its lens sees, as opposed to
what fields it fills once a finding is already handed to it). The
`source_standard` citation grounds the deliverable's shape; it does not,
by itself, ground judgment or finding.

## Problem stated without any solution attached (JTBD tuple)

Job performer: the person operating on-the-record on a real repo (via the
human-directed orchestrator or a self-driven plain session), who is
trusting a role's delegated output without independently redoing that
role's domain work.

Job: know whether a role's record reflects a real, defensible domain
judgment — not just that the role fired, produced fields in the right
shape, and passed the mechanical gates.

Circumstance: the role produced a confident, schema-conformant record;
nothing in the current wiring (spec guards, #776 harness) distinguishes
that from a record that is schema-conformant but substantively wrong or
empty of real domain reasoning — the gap is invisible until a human
happens to read the record closely enough to notice, or until a
downstream failure surfaces it much later.

Desired outcome: a mechanical signal — inside the existing spec guards
and/or the #776 harness — that can tell "domain-valid" from
"plausible-but-hollow" for at least the load-bearing roles, the same way
the harness already mechanically tells "delegation happened" from
"delegation did not happen."

The issue text names a solution shape ("research-grounded methodology,"
"adversarial review," "harness signal") — the JTBD above restates the
underlying need (a way to KNOW, not just a document that CLAIMS) so
step 2's audit design isn't pre-committed to a specific artifact shape
before the rubric (this proposal, §1) fixes what "grounded" and
"adversarial" actually cash out to per role.

## Where this sits in the opportunity-solution tree (OST vocabulary)

- **Outcome**: delegated role judgment is trustworthy without a human
  re-deriving it — northpole reqs #1/#3/#5 hold under delegation, not
  just under direct human execution.
- **Opportunity**: "role fired + record is schema-conformant" is
  currently treated as sufficient evidence of valid judgment; it is not
  — the #776 harness has no content-validity signal (canonical: §3 table
  above).
- **Candidate solutions** (this proposal picks and scopes one; step 2
  builds it, step 3 re-measures):
  1. Per-role rubric addition to each `*.spec.json` (judgment method +
     hollow-instance description + finding method), checked at install
     time only (static/structural) — cheap, but does not itself catch a
     hollow *instance*, only a hollow *definition*.
  2. Runtime adversarial-flip signal added to the #776 harness (defect
     re-injected into a load-bearing role's deliverable; a same-domain
     refutation pass must flip its verdict) — catches hollow instances,
     but only for roles wired into the harness's fixture run.
  3. Both, staged: (1) first as the cheap structural floor covering all
     43 roles, (2) second as the deep signal covering the load-bearing
     subset first (this proposal's recommendation — see proposal
     Solution & prioritization).
- **Discriminating assumption test**: whether a same-domain adversarial
  refutation agent, given only the deliverable (not the producing role's
  reasoning) plus one deliberately reintroduced defect, reliably flips
  its verdict — pre-registered as this proposal's own follow-on
  hypothesis-test object for step 2, not resolved here.
