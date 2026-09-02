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
PIN_SHA="e102772480545a6be0af733f51020c97e7357ba7"
MODEL="sonnet"
BUDGET="1.5"
TOOLS_ON="Read,Glob,Grep,Write,Edit,TodoWrite,Skill"
TOOLS_OFF="Read,Glob,Grep,Write,Edit,TodoWrite"

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
