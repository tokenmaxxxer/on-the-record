#!/usr/bin/env bash
# issue #2348: shared per-session shard writer for the hook-fires counter
# (issue #2028), sourced by directive.sh/stop-gate.sh/stop-poll-rearm.sh so
# the three always-on hooks compute the same shard id from the same
# session_id the same way, instead of three separate inline copies —
# mirrors the poll-rearm.sh precedent those same three hooks already
# source for shared arm/checkout logic.
#
# `.orchestrate-hook-fires.log` was one append-only path every hook firing
# in every session wrote to, guaranteeing a git merge conflict whenever two
# sessions' commits both picked up their own accumulated counter lines.
# Sharding by session (hook_fires.py's `_hook_fires_shard_id()`:
# sha256(session_id)[:24], same formula directive.sh's own monitor-notice
# marker already uses) removes the shared path, not just the individual
# conflict instances.
#
# hook_fires_record <hook-label> <payload-json>
# Appends one line to .orchestrate-hook-fires/<shard>.log under the CWD
# this hook fires in. <shard> is "unknown" when session_id is
# missing/unparseable from <payload-json> — a counter write must never
# block on, or be dropped by, a malformed payload (fails open, matching
# every other on-the-record hook's stdin-JSON handling). Best-effort:
# swallows every failure, matching the flat-file write it replaces.
hook_fires_record() {
  local label="$1" payload="$2"
  { HOOK_FIRES_LABEL="$label" HOOK_FIRES_PAYLOAD="$payload" HOOK_FIRES_ROOT="$(pwd -P)" \
    python3 - <<'PY'
import hashlib
import json
import os
from datetime import datetime, timezone

label = os.environ.get("HOOK_FIRES_LABEL", "")
payload_raw = os.environ.get("HOOK_FIRES_PAYLOAD", "")
root = os.environ.get("HOOK_FIRES_ROOT", "")

session_id = None
try:
    payload = json.loads(payload_raw)
    if isinstance(payload, dict):
        sid = payload.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid
except ValueError:
    pass

shard = (
    hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()[:24]
    if session_id else "unknown"
)
shard_dir = os.path.join(root, ".orchestrate-hook-fires")
os.makedirs(shard_dir, exist_ok=True)
line = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + " " + label + "\n"
with open(os.path.join(shard_dir, shard + ".log"), "a") as f:
    f.write(line)
PY
  } 2>/dev/null || true
}
