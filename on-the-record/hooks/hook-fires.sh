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
# Deliberately pure-bash-plus-coreutils, not python3 (operator-frozen
# constraint, issue #2348: "no added per-spawn overhead or steady-state
# load" for a fix that must hold for every session against any target
# repo): these three hooks fire on every single UserPromptSubmit/Stop
# event, fleet-wide — a python3 interpreter start on that path is a real,
# avoidable per-fire cost the old plain `printf >>` never paid, and
# python3 availability isn't guaranteed in a generic consumer repo either
# (this file's own hash step must not depend on it). `sha256sum`/`shasum
# -a 256`/`openssl dgst -sha256` are tried in that order — near-universal
# across Linux/macOS/BSD — falling back to the same `unknown` bucket a
# missing session_id already uses if none exist, so a write is still
# counted rather than silently dropped.
#
# hook_fires_record <hook-label> <payload-json>
# Appends one line to .orchestrate-hook-fires/<shard>.log under the CWD
# this hook fires in. <shard> is "unknown" when session_id is
# missing/unparseable from <payload-json>, or no sha256 tool is available
# — a counter write must never block on, or be dropped by, a malformed
# payload or a minimal environment (fails open, matching every other
# on-the-record hook's stdin-JSON handling). Best-effort: swallows every
# failure, matching the flat-file write it replaces.
hook_fires_record() {
  local label="$1" payload="$2" root session_id shard shard_dir
  root="$(pwd -P)"
  session_id="$(printf '%s' "$payload" | \
    grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | \
    sed -E 's/^.*:[[:space:]]*"([^"]*)"$/\1/')"
  shard=""
  if [ -n "$session_id" ]; then
    if command -v sha256sum >/dev/null 2>&1; then
      shard="$(printf '%s' "$session_id" | sha256sum | cut -c1-24)"
    elif command -v shasum >/dev/null 2>&1; then
      shard="$(printf '%s' "$session_id" | shasum -a 256 | cut -c1-24)"
    elif command -v openssl >/dev/null 2>&1; then
      shard="$(printf '%s' "$session_id" | openssl dgst -sha256 | awk '{print $NF}' | cut -c1-24)"
    fi
  fi
  [ -n "$shard" ] || shard="unknown"
  shard_dir="${root}/.orchestrate-hook-fires"
  { mkdir -p "$shard_dir" && \
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$label" >>"${shard_dir}/${shard}.log"
  } 2>/dev/null || true
}
