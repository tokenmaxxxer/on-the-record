# defect-verification operational playbook — evidence trail (issue #1174)

## What was done

Authored `playbook/*.md` into the `tokenmaxxxer/defect-verification-rulebook`
checkout at
`/home/jwjung/tokenmaxxxer/rulebooks/defect-verification-rulebook/playbook/`,
per the operational-playbook-program proposal, matching the
capacity-planning/api-design precedent already landed for this issue:
playbook as a top-level content dir peer to the rulebook's existing
plugin dirs, one file per decision axis. README's Layout section updated
to point at it. Pushed branch `issue-1174/operational-playbook`, opened
rulebook PR: https://github.com/tokenmaxxxer/defect-verification-rulebook/pull/34

derived: `ls /home/jwjung/tokenmaxxxer/rulebooks/defect-verification-rulebook/playbook/`
```
independence-from-upstream-verdicts.md
reproduction-evidence-quality.md
severity-band-assignment.md
```

derived: `grep -c '^[0-9]\+\.' /home/jwjung/tokenmaxxxer/rulebooks/defect-verification-rulebook/playbook/*.md`
```
independence-from-upstream-verdicts.md:10
reproduction-evidence-quality.md:10
severity-band-assignment.md:10
```

derived: `grep -c '\*\*REMOVAL\*\*' /home/jwjung/tokenmaxxxer/rulebooks/defect-verification-rulebook/playbook/*.md`
```
independence-from-upstream-verdicts.md:2
reproduction-evidence-quality.md:2
severity-band-assignment.md:2
```

Each axis file exceeds its own `rule_count_floor: 8` (10 rules landed)
and carries >= 2 REMOVAL-classified rules.

## Decision axes (defect-verification's own domain, moderate tier)

- severity-band-assignment — deterministic band lookup (Critical/High ->
  blocking, Medium/Low/Unknown -> advisory): what actually drives the
  call, and what must never drive it (priority, review cleanliness,
  rarity)
- reproduction-evidence-quality — what makes an evidence pointer
  (repro steps, commit sha, run output, log excerpt) actually
  re-derivable by coding instead of a paraphrase
- independence-from-upstream-verdicts — how this role stays a genuine
  independent re-attempt rather than a re-litigation of review's
  Present verdicts or qa's reports, given confirmation-bias's
  documented pull toward deferring to a prior clean result

Three axes at the moderate tier gives a role-level floor of
max(8, 3*2) = 8 rules total minimum; the count above (30 rules across
3 files) clears that by a wide margin, matching the depth the
capacity-planning (45 rules/5 axes) and api-design precedents already
established for this issue.

## Sources (fetched/searched this session)

- https://www.qamadness.com/bug-severity-vs-priority/
- https://www.kualitee.com/blog/guide/bug-severity-levels-explained/
- https://www.kualitee.com/blog/bug-management/severity-levels-vs-priority-levels-bug-tracking/
- https://www.qawolf.com/blog/what-makes-a-great-bug-report
- https://marker.io/blog/steps-to-reproduce-a-bug
- https://www.testdevlab.com/blog/issue-reproduction-why-reproducing-bugs-matter
- https://blog.magicpod.com/confirmation-bias-in-qa-unveiling-the-hidden-traps
- https://xebia.com/blog/mapping-biases-to-testing-confirmation-bias/
- https://www.practitest.com/resource-center/article/cognitive-biases-in-software-testing/
- https://katalon.com/resources-center/blog/cognitive-biases-in-software-testing
- https://www.functionize.com/blog/the-impact-of-cognitive-bias-on-software-testing

## Why

requirement: northpole req#1 (specialist delegation is only real with
specialist knowledge at decision depth) — docs/specs/northpole.md.
This role's own quality-bar judgments (severity banding, evidence
sufficiency, independence discipline) were previously governed by
methodology pointers only (verify/verify-outcome-gate/ schema checks),
not by the practitioner-depth decision rules the operator demanded
across all 43 roles.

## Basis

docs/issue-1174/proposals/operational-playbook-program.md (approved
design doc, section (b) N_min formula and section (d) playbook
location).

## kind

report

## loop_state

awaiting_approval

## Open findings

None — this is phase-1 research/evidence material, not a defect
finding. The actual on-the-record phase-2 record
(docs/issue-1174/reports/defect-verification.md) is gated behind an
"APPROVE issue-1174/defect-verification" comment per contract v3 s19,
matching the capacity-planning precedent; it is not written this
session.
