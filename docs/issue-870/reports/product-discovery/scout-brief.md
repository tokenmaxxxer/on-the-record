---
subject: issue-870
kind: scout-brief
---

# Scout brief — fake-success detection, default-on (issue #870)

Stage count: 1 sweep stage (single WebFetch on the official hooks
reference), 0 deepening stages — saturated after stage 1 because the
open question was narrowly mechanical ("which hook events can block,
and what can they see") and the fetch answered it completely; no
exemplar-judgment round was needed. Mode: single fetch, not a
multi-angle fan-out — the only external unknown was the hooks event
catalog itself, not a competitive-product space (this deliverable
extends an internal gate system, not a new external-facing product).

canonical: https://code.claude.com/docs/en/hooks (fetched this session, 2026-08-11)

## Category must-bes (from the official reference)

- `PreToolUse` supports `deny`/`ask`/`defer` and can rewrite
  `tool_input` before a tool runs — the only event type able to stop an
  action before it happens.
- `Stop` and `SubagentStop` support a `decision: "block"` response that
  keeps the turn/subagent going instead of letting it end — the only
  event types able to act at turn/session-end rather than at one tool
  call.
- `TaskCompleted` supports blocking a task from being marked done.
- `PostToolUse`/`PostToolUseFailure` carry no block capability — context
  or `exit 2` error surfacing only.
- `SessionStart`/`SessionEnd` carry no block capability — injection or
  cleanup only.
- Plugin hooks (`hooks/hooks.json`) register against the same event set
  as user/project settings, resolved by `matcher` (tool name) then `if`
  (args pattern), and combine with project/user-level hooks rather than
  replacing them.

Sources:
- https://code.claude.com/docs/en/hooks

## Performance axes this deliverable competes on

canonical: https://code.claude.com/docs/en/hooks (decision-control table, read this session)

- Axis 1, fail-safe direction: does an unmet condition default to a
  refused action, or to a silently-passed one?
- Axis 2, position in the flow: before a claim is written (`PreToolUse`)
  vs. after a turn/session already ended (nothing) vs. before a
  turn/session may end (`Stop`/`SubagentStop`) vs. before a task is
  marked done (`TaskCompleted`).
- Axis 3, cost per fired check: a mechanical regex/tag-presence check
  (cheap, the existing `record_lint.py` model) vs. an actual build/run
  (expensive, needs a stored per-target command) vs. a second agent's
  judgment (most expensive — real tokens and latency per claim).

## Adopt / skip

canonical: https://code.claude.com/docs/en/hooks (`PreToolUse`, `Stop`, `SubagentStop` rows, read this session)

- **Adopt**: `PreToolUse` as the enforcement point for mechanism (a) —
  it is the only event type that can refuse a write before it lands,
  matching how `on-the-record/hooks/record-claim-guard.sh` already
  gates `Write|Edit|MultiEdit` today (mechanical, cheap, no model
  call).
- **Adopt**: `Stop`/`SubagentStop` as a second enforcement point for
  mechanism (b), narrower than (a) — this event type can keep a turn or
  subagent from ending. Even when a write-time regex is bypassed by
  synonym choice (a limitation #793's own hunt record already logs
  against its narrower marker vocabulary — canonical:
  docs/issue-793/reports/product-discovery/hunt-verify-before-claim.md,
  read this session), the session or subagent still cannot conclude a
  turn that just asserted an outcome with no matching acceptance-run
  evidence for that turn.
- **Skip**: an HTTP or MCP-tool hook type for this deliverable — no
  external service is needed; a `command` hook (shell script over
  `gates/*.py`, the codebase's own established pattern) covers both
  enforcement points with zero new infrastructure.
- **Skip**: a `prompt`-type hook (LLM yes/no judgment on the claim
  itself) as the PRIMARY mechanism — candidate C's semantic-truth
  judgment problem (already ruled out in #793's own RICE table on
  Confidence/Effort — canonical:
  docs/issue-793/proposals/verify-before-claim.md, read this session)
  applies identically here; a `prompt`/`agent` hook type existing does
  not change that a same-session or same-turn model call cannot
  independently check its own prior claim. It stays viable only as the
  adversarial role (mechanism c), run by a structurally separate
  session/role, never as a hook-embedded judgment call.

## Gap line

canonical: docs/issue-793/proposals/verify-before-claim.md (read this session, "Gate extension" section)

The state that #793 shipped gates STATE/DEFECT claims for citation
presence at write time via `PreToolUse` on `docs/issue-*/reports/**`. It
does not gate OUTCOME claims ("requirement met", "done", "PASS") for
citation kind (an executed-live acceptance run vs. a bare assertion),
and no existing gate occupies the `Stop`/`SubagentStop` enforcement
point at all — every gate under `gates/` fires at write-time
(`PreToolUse`) or at PR open-time (`gh`-backed preflight scripts), never
at turn/session end. That is exactly the surface issue #870 asks about.
