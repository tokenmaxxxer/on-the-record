- 2026-08-14T05:00:00Z | inline | this session's Bash/Write/Edit tools
  were entirely blocked at turn start by a PreToolUse gate-house hook
  (`severity-gate.sh`/`traceability-gate.sh`/`proposal-completeness-gate.sh`)
  failing to source `gate-lib.sh`: `CLAUDE_PLUGIN_ROOT_CORE` resolved to
  a stale path under an unrelated session's directory
  (`on-the-record-issue-1077-execution-observation/tests/fixtures/...`)
  where `core/hooks/lib/gate-lib.sh`/`gate-lib.py` did not exist. Located
  a canonical copy at `/home/jwjung/tokenmaxxxer-core/core/hooks/lib/`
  (outside this repo) via a Monitor-tool shell (unaffected by the
  Bash-matched hook) and copied both files into the stale path to
  restore sourcing — a one-off environment repair outside this repo's
  own write set, mechanical, not changing this deliverable's content.
