## Deviation log

- 2026-08-13T00:00:00Z, `filed`, issuecomment-5277047482 (operator
  "Requirement clarification") landed on issue #1219 after this session's
  proposal was already approved and this build already in flight: it widens
  the fix from re-anchoring watchdog *output* (this build's frozen write
  set — `spawn.py`, `tests/test_spawn.py`) to gating whether the tokenmaxxxer
  board watchdog machinery *attaches at all* in a session whose cwd is not
  the plugin repo (no monitor registration, no 60s heartbeat, no
  orchestrate-board directive naming the marketplace checkout, unless the
  target repo itself has on-the-record board structure). That needs a new
  board-structure-detection design decision and touches
  `on-the-record/hooks/directive.sh` / `poll-rearm.sh` — outside this
  proposal's approved write set and requiring judgment a reviewer should
  weigh alternatives on. Per SCOPE-EXCEEDED: finishing what this proposal
  covers (the output re-anchoring fix, already built and tested) and
  reporting the widened requirement for the next issue/role, not building
  it inline. Reported, not spawned.
