# Scout brief — issue #745: session cost-structure valuation

Stage count: 1 sweep round, 3 parallel `WebSearch` angles in one batch (native tool-level fan-out,
not agent fan-out). No deepening round: judge point 1 found the three angles converging on the same
shape (condition by measured value, don't cut uniformly), so a second round would not have changed
any build-facing decision — saturation reached on round 1, well inside the 5-stage/3min budget.

Segment fit: this deliverable is an internal cost/value audit of an agentic-coding governance repo,
not a consumer product. The closest comparable literatures are LLM reasoning-budget engineering,
audit-log retention economics, and QA-coverage economics — not a product category to clone.

## Must-bes, by angle

- **Reasoning-budget angle**: match thinking spend to problem difficulty, not a uniform cut
  ("token-budget-aware reasoning" — tokenoptimize.dev). Load-bearing caveat: Anthropic's own
  newer models reportedly reject a manual `budget_tokens` in favor of adaptive, model-controlled
  thinking (redis.io) — a per-role manual thinking-budget knob may not be a viable lever on
  whatever model this repo's sessions actually run on. This repo has no `budget_tokens` /
  `thinking_budget` / `effort` config anywhere today (derived: `grep -rn "budget_tokens\|thinking_budget\|effort" roles/*.json spawn.py` — no hits), so the knob's viability is unconfirmed, not refused.
- **Audit-log angle**: tier retention by measured value, not a uniform policy — high-signal logs
  kept long/full, low-signal logs pruned/summarized. One cited case cut storage cost ~35% while
  extending high-value retention 4x (graylog.org, cubeapm.com).
- **QA-coverage angle**: 100% coverage is called a "vanity metric" in mainstream practice;
  risk-weighted sampling (weighted by change risk, not a blanket rate) is the recommended
  alternative to blanket 100% review (qt.io, codecov.io).

## Adopt / skip

- **Adopt**: value-tiered treatment for all three cost items — audit-log tiering and QA
  risk-sampling both converge on "condition by measured value," and this repo already has two
  internal precedents for exactly that shape: freelunch's own contract-pinned-vs-judgment-needing
  reasoning-effort split for dispatched workers, and warrant's own docs-only fast path that fully
  skips a before-landing hunt dispatch when the diff has nothing executable in it.
- **Skip**: a uniform "cut thinking/records/observation by X%" — every angle explicitly warns
  against blanket cuts as the failure mode (vanity-metric coverage, indiscriminate log deletion,
  non-adaptive budget caps that degrade quality without a way to detect the degradation).

## Gap line

Current state meets none of the three angles' must-bes on the primary role-session surface: no
thinking-budget knob exists, no record retention/tiering policy exists, and execution-observation
conditioning exists on paper (`roles/execution-observation.json`'s `board_condition` clause) but is
orchestrator-judgment-only — not measured, not enforced. Missing across all three: a named metric
that distinguishes "spend that bought the named good" from "spend that didn't" — exactly this
issue's ask.

Sources:
- https://redis.io/blog/token-budget-aware-llm-reasoning/
- https://www.tokenoptimize.dev/guides/llm-token-optimization-strategies
- https://graylog.org/post/how-to-build-a-cost-effective-log-retention-strategy/
- https://cubeapm.com/blog/log-retention-guide/
- https://www.qt.io/software-insights/is-70-80-90-or-100-code-coverage-good-enough
- https://about.codecov.io/blog/the-case-against-100-code-coverage/
