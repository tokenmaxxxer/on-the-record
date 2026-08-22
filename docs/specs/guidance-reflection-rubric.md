# Guidance-reflection rubric

Companion to `scripts/measure_skill_invocation.py` (issue #1960 lineage).
Invocation measures whether a mounted skill was *called*. This rubric
measures whether the resulting deliverable/record actually *reflects*
that skill's rules — the thing invocation cannot tell you on its own.

## Scope

For one completed role session and one skill mounted in that session,
judge whether the session's deliverable/record content complies with
that skill's stated rules. Judging is builder-blind: the judge sees the
rubric, the skill's rules, and the deliverable/record text, not the
builder's own self-assessment (2026-08-22 requirements-engineering
consult, self-grading-bias caveat).

## Verdict categories

- `yes` — the deliverable/record contains an identifiable passage that
  satisfies a specific rule of the skill. The verdict must cite that
  passage (or a close paraphrase with a locator) as evidence.
- `no` — the deliverable/record contains an identifiable violation of a
  specific rule, or the rule's required artifact/step is absent where
  the skill clearly applied. The verdict must cite the violation or the
  absence as evidence.
- `partial` — the rule is only partially satisfied (applies to part of
  the deliverable but not all of it), or the judge panel itself splits
  evenly with no majority (see multi-judge mechanism below). Evidence
  must say which.

A verdict with no evidence citation is not a valid verdict under this
rubric — evidence is mandatory for every row, including `no`.

## Multi-judge mechanism

Self-grading is biased toward `yes`. To control for it, reflection for
each skill is scored by a panel of independent judge calls, each using
a distinct lens on the same rubric + skill + deliverable:

1. **Compliance lens** — "did the deliverable comply with this skill's
   rules?"
2. **Violation lens** — "did the deliverable violate this skill's
   rules?"
3. **Applicability lens** — "was this skill's rule even triggered by
   this task, and if so was it followed?"

Default panel size is 3 (one call per lens above); a 2-judge panel
(compliance + violation lens) is a supported cost-saving mode. The
majority verdict wins:

- 3 judges, clear majority (2+ agree) → that verdict.
- 3 judges, no verdict has a majority (rare three-way split) → `partial`.
- 2 judges, agree → that verdict.
- 2 judges, disagree (even split) → `partial`.

Each row also carries `votes`, the raw list of per-lens verdicts, so
the majority computation is auditable rather than opaque.

## Row shape

Each row in a session's reflection table is one of:

- Skill row: `{skill, reflected, evidence, votes}` — `reflected` is
  `yes`, `no`, or `partial`.
- Not-applicable row: for a session with **zero mounted skills**, one
  explicit row `{status: "not-applicable", reason: "no-mounted-skills"}`
  — never an empty or missing output for that session. This mirrors
  `measure_skill_invocation.py`'s one-row-per-input discipline.

## Out of scope

This rubric does not judge whether a skill *should* have been mounted,
does not re-score `measure_skill_invocation.py`'s own invocation
counts, and does not alter the mounted skills' own content.
