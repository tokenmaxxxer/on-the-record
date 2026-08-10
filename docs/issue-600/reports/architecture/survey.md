# Current-state survey — issue #600

## Incident recap
2026-08-10, consumer-repo orchestration session: while waiting on a human
decision the session printed "대기 중입니다" four times instead of closing
its turn. Claude Code only surfaces mid-turn user input alongside the
*next* tool result, so the user's actual reply ("응 권고안 좋네") queued
unread until the user pressed interrupt. Root cause per the issue: the
session treated "waiting on a decision" as a reason to keep the turn open
and re-announce the wait, instead of closing the turn per the #535
turn-budget contract (arm/observe in background, close now, let the next
signal or the user's own reply open a fresh turn).

## What already exists (main, as of this survey)

### 1. Contract text (`on-the-record/commands/run.md`)
- `## 턴 예산 규칙 (Turn-Budget Rules, #535)` (lines ~433-461) states three
  rules: (1) work expected to take ≥30s goes to background, turn closes
  the moment observation is armed; (2) mechanically-repeated multi-item
  work batches into one background script, not N foreground calls; (3)
  "남은 작업이 background 에 걸린 시점에서 턴을 닫는다" — the turn closes
  the moment the remaining work is on background, generalizing the
  bounded-wait shape already used for role-session watch/re-arm
  (`directive.sh` ~60-92).
- These three rules are about **outstanding tool work** moving to
  background. None of the three sentences names the case this issue is
  about: the *only* remaining work is a **human's decision**, with no
  tool call to background at all — there is nothing to arm. A close
  reading could stretch rule 3 to cover it, but the text never says so,
  and the incident shows the stretch did not happen in practice.
- Step 7 of run.md ("사용자의 결정을 중계한다") already treats decision-queue
  relay as user-initiated ("결정 대기 항목이 2건 이상이면..."), but says
  nothing about what the orchestrator does with its *own* turn while
  waiting — it describes queue bookkeeping, not turn lifecycle.

### 2. Deployed Stop-surface check
`on-the-record/hooks/decision-queue-stopgate.sh` (issue #466, carrying the
#374 design) already:
- Reads `spawn.py flows --json` fresh every Stop event.
- Reads `decision_queue`; empty → silent, exit 0.
- Two age tiers: `age_hours >= 1` → non-blocking
  `hookSpecificOutput.additionalContext` reminder; `age_hours >= 4` →
  `{"decision": "block"}`, forcing one more turn.
- This is condition **(a)** of this issue's required check — "a non-empty
  decision queue" — already solved, and already exercised by
  `test_decision_queue_stopgate.py` (see that file for its case list:
  empty queue, sub-1h item, 1-4h item, 4h+ item, mixed tiers,
  `ORCHESTRATE_OFF`, role-session silence — `derived: git show
  b8eba9d:on-the-record/hooks/test_decision_queue_stopgate.py`).
- It never reads `last_assistant_message`. It cannot see *how* the
  session is behaving while the queue sits open — only that the queue is
  open. A session that loops "대기 중입니다" four times with a queue item
  at `age_hours=0.3` (below tier 1) sails through this check completely
  silent, exactly as the incident transcript shows (the queue item was
  fresh; nothing had aged into tier 1 yet).

### 3. Adjacent detection patterns already deployed
- `retry-loop-bound.sh` (#507): PreToolUse/PostToolUse pair, counts
  identical-signature tool-call denials per session, two-tier
  allow-with-context (K) / deny-outright (2K) escalation. Demonstrates
  the repo's house pattern for "same shape happened N times → escalate,"
  applicable to a Stop-turn text pattern the same way it is to a tool-call
  signature.
- `report-framing-check.sh` (#320): Stop hook, regexes
  `last_assistant_message` against a trigger pattern
  (`1단계|2단계|[이슈 #n]...→`), then checks for required framing
  elements. This is the repo's only existing precedent for a Stop hook
  that parses reply *text* rather than external state — directly
  reusable shape for reading a waiting-declaration phrasing pattern, with
  the same known weakness noted below.
- `directive.sh` (~60-92): documents the bounded-wait pattern already
  used for role-session `watch`/re-arm (block-then-report, re-arm after
  every non-terminal event) — the shape rule 3 of #535 generalizes, and
  the shape this issue's fix must not duplicate or conflict with.

## Gap (exact)
1. **run.md**: no sentence states that "only remaining work is a human
   decision" must close the turn, with no waiting-declaration loop and no
   foreground polling. Rule 3 of #535 is adjacent but does not name this
   case.
2. **Hook layer**: no check reads `last_assistant_message` for a
   waiting-declaration pattern *and* conjoins it with the non-empty
   `decision_queue` state that `decision-queue-stopgate.sh` already
   computes. The existing gate is state-only and silent below 1h; a
   text-only check (mirroring `report-framing-check.sh`) would be
   gameable by rephrasing alone, per the scout brief.
3. **Tests**: `test_decision_queue_stopgate.py` has no case pairing a
   waiting-declaration `last_assistant_message` with a non-empty queue —
   the exact red case this issue's acceptance criterion names.

## Constraints carried into the proposal
- Zero-install, hooks-only (2026-08-08 policy) — no GitHub Actions.
- Must not weaken or replace `decision-queue-stopgate.sh`'s existing age
  tiers — issue #600 adds a new detection axis, not a replacement.
- Must state, per the issue's own acceptance text, its own
  gaming-resistance and false-positive posture — not left implicit.
