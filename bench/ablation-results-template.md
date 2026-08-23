# Quality-ablation results — issue #2130 (TEMPLATE)

> Copy this file per measurement campaign. Every verdict below is filled by
> the ADJUDICATOR (the operator, or a documented independent grader session
> labeled as such) — never by either arm, never by the runner. No pass/fail
> aggregation is computed anywhere in the tooling; any aggregate written
> here must be derived by the adjudicator from the per-task raw tables and
> presented next to them, not instead of them.

## Campaign metadata

- date:
- rulebook/plugin version (arm A):  <!-- git SHA of on-the-record at run time -->
- model (both arms):
- max-turns budget (both arms):
- reps per task per arm:  <!-- protocol minimum: 2 -->
- adjudicator identity + independence note:

## Task inventory

| task | class | fixture | reps A | reps B |
|---|---|---|---|---|
| t01-version-bugfix | bugfix | harness/fixture-target |  |  |
| t02-format-flag | feature | harness/fixture-feature |  |  |
| t03-unit-conversion | underspecified | harness/fixture-ambiguous |  |  |
| t04-potion-overheal | bugfix | harness/fixture-arcade |  |  |
| t05-difficulty-flag | feature | harness/fixture-arcade |  |  |
| t06-xp-curve | derivation | harness/fixture-arcade |  |  |
| t07-save-underspecified | underspecified | harness/fixture-arcade |  |  |

## Per-task raw tables (one section per task — never omit a run)

### <task-id>

| run | arm | rep | wall-clock (s) | cost (USD) | turns | acceptance items met / total (adjudicated) | fabricated claims found |
|---|---|---|---|---|---|---|---|
|  | A | 1 |  |  |  |  |  |
|  | A | 2 |  |  |  |  |  |
|  | B | 1 |  |  |  |  |  |
|  | B | 2 |  |  |  |  |  |

Adjudication sheet for this task: link the filled scoresheet-*.md files here.
Notes (qualitative differences, refusals, clarifying questions asked):

<!-- repeat the section above for every task -->

## Wall-clock and cost distributions

List every observation (no means-only reporting):

- arm A wall-clock (s), all runs:
- arm B wall-clock (s), all runs:
- arm A cost (USD), all runs:
- arm B cost (USD), all runs:

## Adjudication sheet index

| scoresheet file | filled by | date | independent of builder? |
|---|---|---|---|
|  |  |  |  |

## What N=this-size cannot claim (pre-written; keep in the final doc)

With 6-10 tasks and 2-3 reps per arm, this campaign CANNOT support:

1. **Any statistically significant quality delta.** At this N, a 1-2 task
   difference in adjudicated acceptance items is indistinguishable from
   noise; no significance test is meaningful and none may be reported.
2. **Generalization beyond these fixtures.** Both fixture bases are small,
   stdlib-only Python CLIs. Nothing here transfers by itself to large
   codebases, other languages, or multi-day tasks.
3. **A verdict about the model.** Both arms run the same model tier; the
   measured object is the SYSTEM around it, and only on these task shapes.
4. **Cost/latency conclusions beyond direction-of-effect.** Per-run
   variance in turns and wall-clock at reps=2 exceeds typical arm gaps;
   report distributions, claim at most "consistently higher/lower in every
   observed pair" when that is literally true.
5. **Anything about tasks where an arm's runs were UNMEASURED** (crash,
   timeout, missing result event). Those rows stay in the tables marked as
   such; they are not silently dropped and not counted for either arm.

What it CAN support: existence results ("arm B fabricated an artifact claim
on task X, rep Y — here is the blank artifact"), per-task qualitative
comparisons with linked evidence, and a priced, reproducible protocol for a
larger N.

## Verdict paragraph (adjudicator-authored)

<!-- honest about the above; cites specific rows -->
