---
subject: issue-776
role: product-discovery
kind: scout-brief
---

# Scout brief — E2E agent acceptance harnesses (issue #776)

Stage count: 1 sweep stage (2 parallel WebSearch angles: benchmark-design
angle, eval-harness-infra angle) + 1 judge point, no deepening round
needed (saturation reached at judge point 1 — both angles converged on the
same must-bes). Mode: parallel (two WebSearch calls in one turn).

## Category must-bes (Kano)
- Execution-based verdict, not narration: SWE-bench's harness runs the
  agent's produced patch inside a container at a pinned commit and checks
  the actual test outcome, never trusts the agent's own claim of success.
- Fixed, reproducible environment per run: same pinned repo state every
  run, so a re-run after a fix measures the fix, not environment drift.
- Per-instance pass/fail signal, not one aggregate score: SWE-bench and
  Harness-Bench both report instance/dimension-level outcomes so a
  specific failure is traceable to a specific cause.

## Performance axes strong systems compete on
1. Harness-effect control — Harness-Bench's headline finding: identical
   model weights under different scaffolding/harness config produce
   10-20pt score swings; a credible harness pins its own config so results
   are comparable run-over-run.
2. Zero-human-intervention depth — Human-on-the-Bridge/ProofAgent line
   frames human effort as upfront-only (curate the eval intelligence once),
   never mid-run; matches req #4/#5's "no push-back to human" bar.

## Adopt / skip
- Adopt: pin the fixture repo + harness invocation config (session
  settings, model, plugin version) identically across baseline and every
  re-run, so a signal flip is attributable to the backlog fix under test,
  not harness drift (mirrors Harness-Bench's finding).
- Adopt: execution-based per-requirement signal (build+run the artifact,
  check the real outcome) over a doc/log-analysis check — this is
  literally what req #3 itself demands, so the harness must not violate
  the requirement it is measuring.
- Skip: general-purpose simulator/mutator eval-platform infra (e.g.
  ai-agent-eval-harness's multi-turn/simulator/mutator components) — this
  harness needs exactly one fixture + one representative requirement,
  re-run repeatedly; building a generic eval platform is scope beyond
  what issue #776 or northpole.md asks for.

## Segment fit
on-the-record is a Claude Code plugin, not a model/API being benchmarked —
closest fit is SWE-bench's harness half (pinned fixture + execution-based
verdict), not its dataset-scale half; single-fixture, single-requirement,
repeatable-baseline is the right size.

## Gap line
Current state (docs/issue-749/reports/conformance-review.md) already has
a per-requirement MET/PARTIAL/GAP verdict table — but it was produced by
static code reading, not execution. The field's must-be it's missing is
exactly "execution-based verdict, not narration" (axis 1 above) and "fixed
reproducible environment" (must-be 2) — both are what this harness must
supply. The "per-requirement signal, not aggregate" must-be is already met
in spirit by the conformance-review table shape; the harness should keep
that per-requirement granularity rather than collapsing to one score.

Sources:
- [Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows](https://arxiv.org/html/2605.27922v1)
- [2026 Comparative Analysis: Coding Agent Evaluation Harnesses After SWE-bench Saturation](https://www.appliedtechnologyindex.com/research/2026-comparative-analysis-coding-agent-evaluation-harnesses-after-swe-bench/)
- [Human-on-the-Bridge: Scalable Evaluation for AI Agents](https://arxiv.org/html/2606.16871v1)
- [GitHub - najeed/ai-agent-eval-harness](https://github.com/najeed/ai-agent-eval-harness)
