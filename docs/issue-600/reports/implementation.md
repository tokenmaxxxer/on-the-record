---
code_under_review:
  - on-the-record/commands/run.md
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - docs/specs/reconciled-index.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #600

## What was done
Implemented the approved phase-1 design
(`docs/issue-600/proposals/2026-08-10-close-turn-on-decision-wait.md`,
architecture merged via PR #615):

1. `on-the-record/commands/run.md` — added 규칙 4 under `## 턴 예산 규칙
   (#535)`: waiting on a human decision closes the turn; no
   waiting-declaration loops, no foreground polling. Updated the
   trailing "이 세 규칙은" → "이 네 규칙은" summary sentence.
2. `on-the-record/hooks/decision-queue-stopgate.sh` — added a second,
   independent Stop-surface branch: `decision_queue` non-empty at any
   age AND `last_assistant_message` matches a waiting-declaration phrase
   (대기 중/기다리는 중/waiting for/standing by) with no background-arm
   marker (background/observation/백그라운드/옵저베이션) → `block`,
   reason names run.md rule 4. Wired the existing but previously-unused
   captured stdin `payload` into the embedded Python check via a new
   `STOPGATE_STDIN_JSON` env var (no new external call, no new
   persisted state — same one stdin payload, same one `flows --json`
   call per Stop event as the existing age-tier branch).
3. `on-the-record/hooks/test_decision_queue_stopgate.py` — extended
   `_run()` with an optional `last_assistant_message` kwarg; added the
   red/green pair
   (`t_waiting_declaration_over_fresh_queue_blocks`,
   `t_queue_relay_that_closes_turn_is_not_blocked_by_new_branch`). All 9
   tests in the file pass; the original 7-case suite's expectations are
   unmodified.
4. `docs/specs/reconciled-index.md` — regenerated via `python3
   gates/spec_index.py --update` to record `run.md`'s new hash in the
   same commit.

## Why
The issue's incident evidence (four consecutive "대기 중입니다" Stop
turns before the user had to interrupt) is a Stop-surface pattern, not a
foreground tool-call pattern — a PreToolUse sleep/poll detector would
never fire on a session that only declares itself waiting via plain
text. The chosen design conjoins the existing decision-queue state fact
with the new text signal, closing the gaming gap a text-only check would
have (rephrase-to-evade), per the proposal's Rationale section.

## Upstream basis
docs/issue-600/proposals/2026-08-10-close-turn-on-decision-wait.md

## Open findings
None.

## Next steps
Commit this record and the code together, push, open the delivery PR
carrying `Closes #600`.

## Resolution path
Not applicable — no open finding to resolve.

## What did not work
None — the design translated directly into code. The one snag was
process-level, not design-level: editing the pre-existing phase-1
proposal file to add the `## Accumulation` field (required by
`accumulation-claim-guard.sh`, which fires on any `.py` write in this
repo since several already-tracked files exceed its 3-inline-subprocess-
call threshold) tripped `proposal-shape-gate.sh`'s seven-section-shape
check, because the proposal predated that gate's canonical heading
names. Resolved by reshaping the proposal's headings to the canonical
set (`## Request`/`## Rationale`/`## What will be done`/`## How you'll
know it worked`) while preserving all its original content, and adding
the required `## Accumulation` section — no substantive content was
lost or changed. Also had to add
`docs/issue-600/reports/implementation/survey.md` (stating the
scout-directive skip condition: this phase's design is fully specified
by the approved proposal, no open design decision) to satisfy
`survey-order-gate.sh` before that proposal edit was permitted.

## Doc-placement ladder
- [x] Contract text (env var/config-key/setup-step class) →
  `on-the-record/commands/run.md` (규칙 4), same turn.
- [x] Spec-index update → `docs/specs/reconciled-index.md`, same turn
  (regenerated via `gates/spec_index.py --update`).
- No new env var, dependency, or migration introduced — nothing else on
  the ladder applies.

## Hunt cadence
Not dispatched — this session is a headless, single-shot phase-2
implementation turn (contract v3 s22): a background hunter's finding
would arrive after this turn already ended, with no later turn to
consume it in. Deferred to whichever reviewing session/role runs next
with a live turn to receive it.
