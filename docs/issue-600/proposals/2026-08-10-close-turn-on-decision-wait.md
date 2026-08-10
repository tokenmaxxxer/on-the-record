---
status: proposed
Subject: issue-600
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - docs/specs/reconciled-index.md
---

# Proposal — close the turn while waiting on a human decision (issue #600)

## Request
An orchestration session that has nothing left to do except wait for the
user's decision must close its turn instead of holding it open with
repeated "waiting" status text. Holding the turn queues the user's actual
reply unread until they interrupt — observed live, four consecutive
"대기 중입니다" outputs before an interrupt landed the user's decision.

## Constraints (from the issue and survey)
- Zero-install, hooks-only — no GitHub Actions (2026-08-08 policy).
- Extends, never replaces, `decision-queue-stopgate.sh`'s existing age
  tiers (already solves "queue is non-empty," issue #466/#374).
- The check must state its own gaming-resistance and false-positive
  posture explicitly (issue text, acceptance criterion 2).
- Red/green testable: a waiting-declaration reply over a non-empty queue
  must flag; a normal queue-relay reply that closes the turn must pass.

## Rationale
The issue's own text frames the detection mechanism as "the deployed
check's own design choice" and names one explicit alternative: a
PreToolUse detector for foreground sleep/poll loops. That alternative is
considered and rejected here — the incident evidence (four repeated Stop
turns, each printing a status line, with no intervening tool call at
all) is a Stop-surface pattern, not a tool-call pattern; a PreToolUse
sleep/poll detector would never fire on a session that isn't sleeping or
polling, only declaring itself "waiting" via plain text. The chosen
design is a Stop-surface conjunction instead: (a) decision-queue
non-empty (existing signal) AND (b) the last assistant message matches a
waiting-declaration phrasing set with no background-arm marker. A
text-only check (phrasing match alone, no state fact) was also
considered and rejected: it is trivially gameable by rephrasing away
from the trigger list, exactly the weakness `report-framing-check.sh`
already has for the same class of check. Conjoining the state fact
closes that gap — an operator cannot make a genuinely non-empty decision
queue disappear by choosing different words.

## What will be done

### 1. Contract text — `run.md`, new subsection under "턴 예산 규칙 (#535)"
Add a 4th rule (numbered rule 4, not a new section — the failure is a
turn-budget violation, and belongs where rule 3 already lives) stating,
in the same imperative register as rules 1-3:

> **규칙 4 — 남은 작업이 사람의 결정뿐이면 그 자리에서 턴을 닫는다.**
> 결정 큐(7번 스텝) 또는 미션 보드의 waiting-for-human-decision 항목에만
> 걸려 있고 arm 할 background 작업이 없는 경우에도 규칙 3 과 동일하게
> 턴을 닫는다. "대기 중입니다" 류 상태 문장을 반복해 턴을 점유하는
> waiting-declaration 루프, 그리고 결정 도착 여부를 foreground 에서
> 스스로 폴링하는 것 — 둘 다 금지. 사용자의 다음 메시지 자체가 다음
> 턴을 여는 신호다; 세션이 스스로 신호를 만들 필요가 없다.

This closes gap 1 from the survey by naming the exact case rule 3 left
implicit. `docs/specs/reconciled-index.md` gets its matching row in the
same commit (acceptance criterion 1's "spec-index updated in the same
unit").

### 2. Stop-surface check — extend `decision-queue-stopgate.sh`
Add a second, independent branch inside the existing Python block (same
file, same fresh-read-per-turn shape as today — no new state, per the
scout brief's "skip: brand-new persisted-state hook"):

- **Input added**: the hook already reads stdin as `payload`; today only
  `flows --json`'s `decision_queue` is consulted. Add
  `payload.get("last_assistant_message")` (same field
  `report-framing-check.sh` already reads from the same event shape) as
  the second input.
- **Condition (a)** (existing, unchanged): `decision_queue` non-empty —
  at ANY age, not just tier-1/tier-2, since the incident's queue item was
  fresh (`age_hours=0.3`) and still needs this new check to fire.
- **Condition (b)** (new): `last_assistant_message` matches a
  waiting-declaration phrasing set (e.g. `대기 중`, `기다리는 중`,
  `waiting for`, `standing by`) **and** shows no evidence the turn is
  closing (no background-arm marker — reuse the same "armed
  background/observation" language rule 1-3 already put in the reply
  convention, i.e. absence of `background`/`observation`/`백그라운드`
  tokens near the waiting phrase).
- **Verdict**: (a) AND (b) → `{"decision": "block"}` with a reason naming
  the exact violation and pointing at run.md rule 4 — new, independent of
  the existing age-tier `block`, and fires even when both age tiers would
  stay silent (tier 1/2 need `age_hours >= 1`; this fires at any age).
  (a) without (b), or (b) without (a) → existing behavior only (age-tier
  logic, or silent).

#### Gaming-resistance posture (required by acceptance criterion 2)
Conjoining (a) state with (b) text is the deliberate defense identified
in the scout brief: a text-only check (rephrase away from the trigger
list) is trivially gameable, as `report-framing-check.sh`'s own known
weakness shows. Requiring the state fact too closes that gap — an
operator cannot make a genuinely non-empty decision queue disappear by
choosing different words; they can only actually close the turn (which is
the compliant behavior) or actually resolve the queue item. Residual gap,
stated plainly: a session that closes the turn via a background-arm
marker *without doing anything real* in the background would pass — this
check verifies the turn-closing *behavior signal*, not that a background
watch was genuinely armed. That verification is out of scope for a
Stop-surface text/state check; catching a faked background-arm claim
would need a different, non-textual signal and is not attempted here.

#### False-positive posture (required by acceptance criterion 2)
The phrasing list is necessarily incomplete and Korean/English-biased;
false negatives (a genuine violation using unlisted phrasing) are
accepted as the cost of a deny-shaped check that must not block
legitimate replies. False positives are bounded by requiring BOTH
conditions: a reply that legitimately mentions "waiting" as part of
relaying the decision queue's contents (step 7's compressed queue format)
but also closes the turn (no further foreground work implied, matches
existing turn-closing reply shapes already accepted elsewhere in run.md)
does not match condition (b)'s "no background-arm marker" clause. Sessions
with an empty decision queue are out of scope per the issue's stated
empty state — condition (a) alone already guarantees this.

### 3. Tests — `test_decision_queue_stopgate.py`
Add the red/green pair the acceptance criterion names, following the
file's existing `_run()` harness (extend its payload to carry
`last_assistant_message` alongside `flows_payload`):

- **Red**: `decision_queue` non-empty (any age) + `last_assistant_message`
  containing a waiting-declaration phrase with no background-arm marker
  → asserts `decision == "block"` and the reason names rule 4.
- **Green**: same non-empty queue, but `last_assistant_message` is a
  normal step-7 decision-queue relay that also closes the turn (contains
  a background-arm marker, or is a queue-relay shape distinct from a bare
  waiting declaration) → asserts existing age-tier behavior only (no new
  block from this branch).
- Existing 7-case suite (empty/sub-1h/1-4h/4h+/mixed/`ORCHESTRATE_OFF`
  /role-session) must stay green, unmodified in expectation — this is an
  additive branch, not a replacement.

## Accumulation
`_run()`'s test helper gains one new optional kwarg
(`last_assistant_message`), and the CHECK block inside
`decision-queue-stopgate.sh` gains one new branch reading one new env var
(`STOPGATE_STDIN_JSON`) — not a new per-item inline `subprocess`/`gh`
call site, and not a `roles/*.json`-style repeated-file edit. If a third
turn-occupancy signal (a different Stop-surface state fact) is added
later, it extends this same branch/kwarg shape rather than opening a new
call site; the branch already reads its one stdin payload and one `flows
--json` call per Stop event, matching the existing age-tier branch, so
there is no N-times-more accumulation risk from this change.

## Out of scope (this proposal)
- Implementing the above (step 2 in the issue's own 실행 계획 — a
  separate phase/session).
- Any change to `decision-queue-stopgate.sh`'s existing age-tier
  thresholds or wording.
- Detecting foreground polling by means other than the Stop-surface
  text/state check above (e.g. a PreToolUse sleep/poll-loop detector) —
  the issue's own text frames this as "the deployed check's own design
  choice"; this proposal's choice is the Stop-surface conjunction above,
  not a PreToolUse addition, because the incident evidence (repeated Stop
  turns each printing a status line) is a Stop-surface pattern, not a
  tool-call pattern.
## Boundary sketch (context/container)
```
[Human operator] --decision reply (fresh turn)--> [Orchestration session]
[Orchestration session] --Stop event (payload incl. last_assistant_message)--> [Claude Code harness]
[Claude Code harness] --stdin payload--> [decision-queue-stopgate.sh]
[decision-queue-stopgate.sh] --flows --json--> [spawn.py] --reads--> [board state / decision_queue]
[decision-queue-stopgate.sh] --block/allow decision--> [Claude Code harness] --forces or ends turn--> [Orchestration session]
```
Inside `decision-queue-stopgate.sh`, the new branch reads the same one
stdin payload and the same one `flows --json` call per Stop event as the
existing age-tier branch — no new external call, no new persisted state,
no new hook file or event type:
```
stdin payload
  ├─ decision_queue (via spawn.py flows --json)   [existing]
  │     └─ age-tier branch: >=4h block, >=1h context, else silent
  └─ last_assistant_message (new, same payload)    [new, this issue]
        └─ waiting-declaration branch:
             (decision_queue non-empty, any age) AND
             (waiting phrase present AND no background-arm marker)
             => block, reason names run.md rule 4
```
Both branches can fire independently — the new branch reaches a fresh
`age_hours=0.3` item the age-tier branch would leave silent, matching the
incident (its queue item was under 1h old).

## How you'll know it worked
- `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q`
  exits 0, including the new red/green pair.
- `run.md` contains rule 4 verbatim under the #535 section; commit
  carries a matching `docs/specs/reconciled-index.md` row.
- Manual replay of the incident shape (non-empty queue, four repeated
  "대기 중입니다" Stop turns) is blocked by the extended hook instead of
  reaching a fifth silent turn.

## What did not work
(none yet — appended live during phase 2 if anything breaks)
