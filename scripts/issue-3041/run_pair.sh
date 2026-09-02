#!/usr/bin/env bash
# Paired skills-on/skills-off run for issue #3041.
#
# Usage:
#   bash scripts/issue-3041/run_pair.sh <task-file> <task-id> <output-root>
#
# Produces, under <output-root>/<task-id>/:
#   skills-on/   -- clone of the target repo + DELIVERABLE.md written by an
#                   arm with the full skill corpus available (default)
#   skills-off/  -- clone of the same repo, same commit, same task text,
#                   run with --disable-slash-commands (skill layer suppressed)
#   skills-on.session.jsonl / skills-off.session.jsonl -- full stream-json
#                   tool-call transcripts, used for secondary instrumentation
#
# Model, repo state (pinned commit), task text and permission mode are held
# constant between the two arms; only the skill layer differs.
set -euo pipefail

TASK_FILE="$1"
TASK_ID="$2"
OUT_ROOT="$3"

REPO_URL="https://github.com/JiwonJung94/study-companion.git"
PIN_SHA="d6f14aebd1a79002fda3a7f22320ee63c6e7a736"
MODEL="sonnet"
BUDGET="1.5"
TOOLS_ON="Read,Glob,Grep,Write,Edit,TodoWrite,Skill"
TOOLS_OFF="Read,Glob,Grep,Write,Edit,TodoWrite"

# --setting-sources project,local (below) deliberately excludes the `user`
# scope to keep this repo's own operator hooks from leaking into the target
# subprocess -- but marketplace plugins also register at `user` scope, so
# that flag alone mounts zero skills in the skills-on arm too (issue #3053).
# --plugin-dir is session-scoped and orthogonal to --setting-sources: it
# loads the target skill corpus without pulling in the operator-hook plugin,
# which is registered separately in this machine's user settings. Verified
# live in issue #3053 (no hook-leak signal, corpus present in the init event).
PLUGIN_DIR="${MUSTER_SKILL_REGISTRY_ROOT:+$(dirname "$MUSTER_SKILL_REGISTRY_ROOT")}"
PLUGIN_DIR="${PLUGIN_DIR:-$HOME/skill-registry}"

TASK_TEXT="$(cat "$TASK_FILE")"
PROMPT="You are advising the team behind this repository (a study app for university students). Look at the repo to the extent it's useful, then do the following:

${TASK_TEXT}

Write your full answer to DELIVERABLE.md in the repo root. Do not modify any other file."

pair_dir="$OUT_ROOT/$TASK_ID"
rm -rf "$pair_dir"
mkdir -p "$pair_dir"

seed="$pair_dir/_seed"
git clone --quiet "$REPO_URL" "$seed"
git -C "$seed" checkout --quiet "$PIN_SHA"
echo "pinned_sha=$(git -C "$seed" rev-parse HEAD)"

run_arm() {
  local arm="$1"
  local ws="$pair_dir/$arm"
  cp -r "$seed" "$ws"
  rm -rf "$ws/.git"
  set +e
  if [ "$arm" = "skills-on" ]; then
    (
      cd "$ws"
      timeout 600 claude -p "$PROMPT" \
        --model "$MODEL" \
        --permission-mode bypassPermissions \
        --setting-sources project,local \
        --plugin-dir "$PLUGIN_DIR" \
        --tools "$TOOLS_ON" \
        --output-format stream-json --verbose \
        --max-budget-usd "$BUDGET" \
        > "$pair_dir/$arm.session.jsonl" 2> "$pair_dir/$arm.err.log"
    )
  else
    (
      cd "$ws"
      timeout 600 claude -p "$PROMPT" \
        --model "$MODEL" \
        --permission-mode bypassPermissions \
        --setting-sources project,local \
        --tools "$TOOLS_OFF" \
        --disable-slash-commands \
        --output-format stream-json --verbose \
        --max-budget-usd "$BUDGET" \
        > "$pair_dir/$arm.session.jsonl" 2> "$pair_dir/$arm.err.log"
    )
  fi
  local exit_code=$?
  set -e
  local has_deliverable="no"
  [ -f "$ws/DELIVERABLE.md" ] && has_deliverable="yes"
  echo "arm=$arm exit=$exit_code deliverable=$has_deliverable"
}

run_arm "skills-on"
run_arm "skills-off"

rm -rf "$seed"
echo "pair_dir=$pair_dir"
