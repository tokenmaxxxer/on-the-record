# Current-state survey — issue #600 phase 2 (implementation)

Scope: implement the approved phase-1 proposal
(`docs/issue-600/proposals/2026-08-10-close-turn-on-decision-wait.md`,
architecture merged via PR #615). No new design decision is open here —
the write set, the rule text, and the check's branch logic are already
frozen by that proposal; this phase turns it into committed code.

## Write set confirmed on disk

- `on-the-record/commands/run.md` — `## 턴 예산 규칙 (#535)` section
  present at line 433, rules 1-3 exist as described in the proposal;
  adding rule 4 is a direct insertion after rule 3, before the
  "이 세 규칙은" summary sentence (which itself needs updating to "네
  규칙").
- `on-the-record/hooks/decision-queue-stopgate.sh` — existing script
  reads `payload` (stdin) into a bash var but only forwards
  `STOPGATE_FLOWS_JSON` to the embedded Python check; `payload` itself
  was captured but unused. Confirmed: adding a `STOPGATE_STDIN_JSON` env
  var carrying the same `$payload` is the only wiring change needed to
  give the new branch access to `last_assistant_message`, matching the
  proposal's "same one stdin payload... no new external call" design.
- `on-the-record/hooks/test_decision_queue_stopgate.py` — existing
  `_run()` helper already hardcodes `last_assistant_message: "ok"` in
  the payload it sends; confirmed a one-line change (add a kwarg,
  default `"ok"`) is enough for new tests to control it without touching
  the seven existing test cases' call sites.
- `docs/specs/reconciled-index.md` — checked for an existing #535 /
  decision-queue-stopgate row to extend in the same commit.

## Skip condition

This phase-2 unit implements a fully-specified phase-1 design (proposal
already carries `## Design` with exact rule text, exact branch logic,
gaming/false-positive posture, and a red/green test spec) — no design
decision is left open for this survey to inform. Recorded per the
scout-directive's mandatory skip-record requirement.
