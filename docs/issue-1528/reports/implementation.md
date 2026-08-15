---
code_under_review:
  - on-the-record/monitors/monitors.json
  - on-the-record/monitors/poll-heartbeat.sh
type: docs
breaking: false
canonical: this session's measurement — grep -c '60s' on-the-record/monitors/monitors.json returned 0
verdict: pass
loop_state: landed
---

# issue-1528 implementation record

## Summary of work

Updated the stale "60s" cadence text to the actual default (120s,
env-overridable via `POLL_HEARTBEAT_SLEEP_SECONDS`), per #1510:
- `on-the-record/monitors/monitors.json`: monitor `description` field.
- `on-the-record/monitors/poll-heartbeat.sh`: header comments (the
  `sleep 60` mention near the top, and the two "60s cadence"/"60s
  default" mentions in the test-hooks paragraph).

## Why

Skip condition: pure text/comment correction, no design decision open
(scout-directive / survey-order-directive skip condition — "pure
bugfix" text-drift fix). The runtime default was already 120s
(`sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"`,
on-the-record/monitors/poll-heartbeat.sh:166); only the user-facing
description and header comments still said 60s, misleading the operator
per issue #1528.

## Upstream basis

#1510 (PR #1513), which changed the runtime default to 120s but left
this text stale. Issue: #1528.

## Acceptance check

checked: `grep -c '60s' on-the-record/monitors/monitors.json` — result: 0
canonical: ran `grep -c '60s' on-the-record/monitors/monitors.json` in this session, output above.

## What did not work

None.

## Open findings

None.
