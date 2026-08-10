# Current-state survey — issue #566, architecture role

Scout skip record: scouting skipped. Reason — this is an internal infra hook whose shape is
fully bounded by this repo's own existing hook precedent (`stop-gate.sh`, `record-scaffold.sh`,
`report-framing-check.sh`) and by `docs/issue-566/proposals/product-discovery.md`'s already-
resolved open questions; there is no external product category to benchmark a bash
detection-hook's internals against.

## What exists today (`on-the-record/hooks/`)

- **Stop-hook payload shape**: every existing `Stop` hook (`stop-gate.sh`, `report-framing-
  check.sh`, `role-test-claim-guard.sh`) reads only `last_assistant_message` off a `*_PAYLOAD`
  env var, fed from stdin JSON. None of them read the full transcript. This issue needs the full
  session's *user* turns (a requirement can be stated several turns before `Stop` fires), not just
  the final assistant reply — the existing convention does not cover that, so the new hook reads
  `transcript_path` from the raw Stop payload directly (the field Claude Code's Stop event always
  carries) instead of reusing `last_assistant_message`.
- **Advisory vs. blocking pattern**: `stop-gate.sh` and `report-framing-check.sh` both fail open
  on ordinary turns (no-op) and, on violation, emit `hookSpecificOutput.additionalContext` — a
  same-turn correction nudge, never `"decision":"block"`. Both fail closed on internal error via a
  `trap`-based exit-code remap, and both honor `ORCHESTRATE_OFF` as a kill switch, and both no-op
  when `CLAUDE_ROLE` is set (role sessions, as opposed to the target-repo orchestrating session,
  are out of scope for these checks).
- **Scaffold pattern**: `record-scaffold.sh` is the only existing "create missing docs structure"
  precedent — CLI-invoked (not hook-fired, because nothing fires "about to start a record"), never
  overwrites an existing file, writes a placeholder-field skeleton.
- **`hooks.json` `Stop` array**: derived by inspection —
  ```
  grep -n '"Stop"' -A 20 hooks.json | grep -c command   # => 4
  ```
  today's command entries (`stop-gate.sh`, `role-test-claim-guard.sh`,
  `decision-queue-stopgate.sh`, `report-framing-check.sh`) are all additive; order between them is
  not load-bearing since each inspects an independent payload field.
- **Nothing today inspects a target repo's product-docs tree at all** — confirmed by
  `docs/issue-566/reports/product-discovery/current-state.md`: zero transcript-scoped hooks exist
  for this purpose. The four-file product-docs layout (see below) is a target-repo convention this
  issue introduces; it has no existing counterpart anywhere in this repository's own tree today.

## What product-discovery already decided (binding on this design)

Per the merged phase-1 proposal at `docs/issue-566/proposals/product-discovery.md` (PR #568):
a four-file layout under the target repo's docs directory — requirements, priorities, philosophy,
goals, each its own append-only dated log — detection at `Stop` via transcript pattern-match (not
self-report), write batched per session at `Stop` (not per turn), cross-check via git diff of the
session's own changes, bootstrap on first detected requirement rather than refusing outright,
deployed strictly under `on-the-record/hooks/` with no GitHub Actions. This survey does not
re-litigate any of those four; this role's job is the mechanism (regex vocabulary, hook name,
wiring, bootstrap behavior) that discharges them.
