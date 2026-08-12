# Scout pass — issue #973

Skipped. Reason: this is internal orchestration tooling extending this repo's own harness machinery
(`spawn.py`'s `consult_cmd`/`spawn_cmd`, the official `SendMessage`/`ListAgents` cross-session
primitive) — not a consumer-facing product surface with an external category to benchmark. There is
no comparable external product whose must-bes/performance axes would steer this design; the two
inputs that steer it are the harness's own documented capability facts (canonical: gh issue view
751 --comments, read this session — code.claude.com/docs/en/cross-session-messaging.md) and this
repo's own prior findings record (docs/issue-751/reports/defect-verification.md), both already cited
in docs/issue-973/reports/product-discovery/current-state.md. Same skip shape as
docs/issue-659/reports/product-discovery/scout-brief.md for the same class of problem.
