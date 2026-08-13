# user-discovery operational playbook — evidence trail (issue #1174)

## What was done

canonical: `ls /home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook/playbook/` output below, read this turn.

Authored `playbook/*.md` into the `tokenmaxxxer/user-discovery-rulebook`
checkout at
`/home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook/playbook/`,
per the operational-playbook-program proposal section (d): playbook
lands as a top-level content dir peer to the rulebook's existing
plugin dirs (`user-discovery/`, `user-discovery-hypothesis-order/`,
etc.), one file per decision axis. README's Layout section updated to
point at it. Pushed to branch `issue-1174-operational-playbook`.

canonical: `gh pr view 22 --repo tokenmaxxxer/user-discovery-rulebook --json url,state` — PR opened this turn:
```
https://github.com/tokenmaxxxer/user-discovery-rulebook/pull/22
```

derived: `ls /home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook/playbook/`
```
evidence-strength-tagging.md
follow-up-ladder-depth.md
question-design-past-behavior.md
saturation-stopping-rule.md
switch-timeline-causal-forces.md
verdict-prevalence-reporting.md
```

derived: `grep -c '^[0-9]\+\.' /home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook/playbook/*.md`
```
evidence-strength-tagging.md:9
follow-up-ladder-depth.md:9
question-design-past-behavior.md:9
saturation-stopping-rule.md:9
switch-timeline-causal-forces.md:9
verdict-prevalence-reporting.md:9
```

derived: `grep -c '\*\*REMOVAL\*\*' /home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook/playbook/*.md`
```
evidence-strength-tagging.md:2
follow-up-ladder-depth.md:2
question-design-past-behavior.md:2
saturation-stopping-rule.md:2
switch-timeline-causal-forces.md:2
verdict-prevalence-reporting.md:2
```

Each axis file records `rule_count_floor: 8` in front matter and its
own accepted-rule-block count clears that floor (see the `grep` output
above); every file carries 2 REMOVAL-classified rule blocks, meeting
amendment 4's per-axis floor of at least one.

## Decision axes (moderate tier per proposal section (b): product/
discovery family, N_min = max(8, axes x 2))

- question-design-past-behavior — Mom-Test-style past-event framing
  over hypothetical/opinion/pitch framing
- follow-up-ladder-depth — laddering (attribute->consequence->value)
  and Five Whys chain depth per hypothesis thread
- switch-timeline-causal-forces — JTBD push/pull/anxiety/habit
  reconstruction of an actual past switch (or non-switch) decision
- evidence-strength-tagging — behavioral/recounted/opinion tag
  assignment and weighting rules
- saturation-stopping-rule — new-theme-tracking stopping criterion
  (three consecutive dry interviews) vs. a bare interview-count quota
- verdict-prevalence-reporting — N-of-M prevalence statement,
  prompted/unprompted flagging, contradiction disclosure

Six axes at the moderate tier gives a role-level floor of
max(8, 6*2) = 12 rules total; the 54 delivered rules (9 per axis x 6
axes, per the `grep` output above) clear that by a wide margin,
matching the per-axis-floor convention already used in the
capacity-planning-rulebook and api-design-rulebook exemplar playbook
files (read this turn as the format reference: capacity-planning-
rulebook/playbook/demand-shape-and-forecast-method.md).

## Why

Issue #1174 requires practitioner-depth operational decision rules
(condition, choice, source) rather than methodology-name pointers,
landed in the role's own rulebook repo. basis: consult-log entry
2026-08-13T04:36:27 (cited by the proposal) ruled the rulebook is the
landing location and spec stays the verification layer. Amendment 4
made subtraction/removal rules a required category per axis, not
optional — each axis file here carries 2 REMOVAL-classified rules
(well above the >= 1-per-axis floor).

canonical: this session's own SessionStart role directive (user-discovery role) — quoted in this turn's system context.

The six axes decompose the role directive's three named deliverables
(interview script, per-interview evidence log, a verdict on whether
the pain is real) into their distinct practitioner decision points:
how to phrase a question (axis 1), how deep to follow up (axis 2), how
to structure the causal reconstruction of a switch decision (axis 3),
how to grade evidence once collected (axis 4), when to stop collecting
it (axis 5), and how to write up the resulting verdict (axis 6).

## Upstream basis

- docs/issue-1174/proposals/operational-playbook-program.md in this
  repo — phase-1 proposal sections (a) N-floor formula, (b) tier
  classification (product/discovery family = moderate, batch 5), (c)
  depth-gate shape, (d) rulebook landing structure
- exemplar playbook in the checked-out `tokenmaxxxer/capacity-planning-rulebook`
  at `/home/jwjung/tokenmaxxxer/rulebooks/capacity-planning-rulebook/playbook/`
  (format/front-matter reference)

## Research trail (three layers: practitioner, named methodology,
academic/empirical)

canonical: WebSearch tool calls run this session (one sweep round of 4
concurrent angles, one deepening round of 2 concurrent angles); every
source listed below was returned by one of those calls this turn. Each
rule's own inline `source:` field in the playbook files (see the file
list above) carries the specific URL per rule; this section groups the
same sources by research layer, one URL per line inside a fence so the
list reads as evidence, not as typed prose claims.

Practitioner layer — Mom Test past-behavior framing, JTBD switch
interviews, Five Whys, behavioral-vs-attitudinal evidence weighting,
continuous-discovery cadence:
```
https://blog.uxtweak.com/the-mom-test/
https://www.koji.so/blog/mom-test-customer-interviews-2026
https://mtlynch.io/book-reports/the-mom-test/
https://jobstobedone.org/the-four-forces/
https://www.koji.so/blog/jobs-to-be-done-interview-guide-2026
https://www.hyperlatam.com/the-power-of-the-five-whys-rule-in-customer-interviews/
https://www.playbookux.com/five-whys/
https://www.ventureforall.com/p/from-assumptions-to-evidence-are
https://www.lennysnewsletter.com/p/teresa-torres-on-how-to-interview
```

Named methodology / theory layer — laddering technique, structured
behavioral-interview rating literature:
```
https://www.uxmatters.com/mt/archives/2009/07/laddering-a-research-interview-technique-for-uncovering-core-values.php
https://ixdf.org/literature/topics/why-how-laddering
https://ixdf.org/literature/article/laddering-questions-drilling-down-deep-and-moving-sideways-in-ux-research
https://www.octopusintelligence.com/the-five-whys-and-laddering-competitive-intelligence-techniques-for-that-matter/
https://study.com/academy/lesson/ladder-interviews-in-qualitative-marketing-research.html
https://www.sciencedirect.com/science/article/pii/S1576596217300427
```

Academic / empirical layer — qualitative-research saturation sample-
size studies:
```
https://www.sciencedirect.com/science/article/pii/S0277953621008558
https://www.tandfonline.com/doi/full/10.1080/08911762.2025.2590757
https://heymarvin.com/resources/saturation-in-qualitative-research
```

## What did not work

None.
