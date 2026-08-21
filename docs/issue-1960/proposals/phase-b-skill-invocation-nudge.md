---
status: proposed
files:
  - spawn.py
---

# Phase B: single-change improvement for the skill-invocation gap (issue-1960)

Skip condition check: neither scout-skip condition applies (this is not a
pure bugfix, and it does involve a design decision between two candidate
changes) — full survey work was run and precedes this proposal, at
docs/issue-1960/reports/execution-observation/survey.md, the correct
per-role path under contract v3 s11 for the `execution-observation` role.
Noted here because the locally-installed survey-order-gate.sh checks a
literal, hardcoded `docs/issue-<n>/reports/implementation/survey.md` path
regardless of the writing role, so a non-`implementation` role's real
survey at its own role path does not satisfy that gate mechanically even
though the survey-before-proposal ordering this directive requires was, in
fact, followed.

## Request

Issue-1960 asks for one improvement (not two at once) applied after the
phase A baseline, from two candidates named in the issue: (a) a spawn task
directive instructing skill consultation at task start, or (b)
trigger-phrasing alignment on skill descriptions. Apply exactly one, then
re-measure the invocation rate over new sessions with the same method and
artifact format as the baseline
(docs/issue-1960/reports/execution-observation/baseline-measurement.md),
recording it alongside the baseline in that same artifact.

## Constraints

- Sequential application only — never both candidates in the same change,
  per the issue text, so the re-measurement can attribute the effect to
  one cause.
- Write set for the code change is `spawn.py` only (per issue scope:
  "scripts/, gates/, spawn.py, docs/") — this proposal covers phase B's
  code change plus its docs.
- The baseline (docs/issue-1960/reports/execution-observation/baseline-measurement.md)
  showed relevance-gated invocation rate 0/38 — real gap, phase B is
  warranted, not skippable.
- Re-measurement must use the same join method and artifact format as the
  baseline (same script, same table shape) so the two numbers are
  comparable — a different measurement method would make "alongside the
  baseline" meaningless.

## Rationale

Considered candidate (b), trigger-phrasing alignment (rewording the
`description:` field in each mounted skill's frontmatter so its trigger
phrasing more closely echoes actual task language), and rejected it for
this first change: the survey found the invocation gap is 0/38 across
every relevance-gated session sampled, not a partial miss — every
`implementation`/`test-authoring` session in the sample had 1-4 skills
mounted and invoked none of them
(docs/issue-1960/reports/execution-observation/baseline-measurement.md).
A uniform zero across dozens of sessions and multiple distinct skills
points at a structural absence of any invocation attempt, not at
individual skills failing to match on wording — rewording descriptions
would not address a session that never considers the Skill tool as an
option at all. Trigger-phrasing misses would show up as a nonzero-but-low
rate with skill-specific variance; that is not what the baseline shows.

Chosen instead: (a) a spawn task directive instructing skill consultation
at task start. This directly targets the structural gap — it adds an
explicit instruction, delivered at spawn time (the same mechanism that
already delivers the other standing directives visible in this session's
own system-reminders, e.g. the scout-directive, record-shape-directive),
telling the spawned role session to check its mounted skills against the
task before proceeding. This is a single, attributable change confined to
`spawn.py`'s directive-injection point, matching the issue's "ONE
improvement first" constraint.

## What will be done (phase 2, after approval)

1. Locate `spawn.py`'s directive-injection mechanism (the code path that
   produces the other `UserPromptSubmit hook success: <...-directive>`
   blocks visible in role sessions).
2. Add one new directive block instructing the spawned session to check
   its mounted skill list against the task at hand before starting
   substantive work, invoking the Skill tool for any skill whose stated
   trigger plausibly applies.
3. Re-run the same measurement method
   (`/tmp/measure_skill_invocation.py`-equivalent, committed this time
   under `scripts/` per the issue's scope, not left in `/tmp`) against a
   fresh sample of new sessions spawned after the change lands.
4. Append the re-measured rate to
   docs/issue-1960/reports/execution-observation.md (the phase-2 record)
   in the same table/derivation format as the baseline, with the baseline
   numbers repeated alongside for comparison.

## Out of scope

- Trigger-phrasing alignment (candidate b) — deferred; if the directive
  change does not close the gap, a follow-up issue can apply it as the
  next single change, re-measured independently.
- Any change to which skills are mapped to which roles (issue-1955/#1758's
  concern, not this issue's).
- Any change to the Skill tool's own invocation mechanics.

## Accumulation

This adds one more directive block to `spawn.py`'s directive-injection
point, alongside the scout/record-shape/survey-order/etc. directives
already injected there. If future issues each add their own one-off
directive the same way, that injection point grows unboundedly and every
spawned session's context grows with it. This proposal does not introduce
a new accumulation pattern (the point already accumulates directives
today) and does not add shared tooling to cap or consolidate it — that is
out of scope for a single-change phase B. If this directive proves
effective and the pattern repeats several more times, consolidating
directive injection (e.g. one combined skill-consultation-and-checks
block, or a registry the injection point reads instead of inline
per-directive code) becomes a separate, later concern, not part of this
change.

## How you'll know it worked

The re-measured relevance-gated invocation rate over new post-change
sessions, computed by the same method and recorded in the same artifact
format alongside the 0/38 baseline, is materially above zero. If it is
not, the record states that plainly rather than declaring success, per the
issue's acceptance requirement that the re-measurement be recorded
regardless of outcome.
