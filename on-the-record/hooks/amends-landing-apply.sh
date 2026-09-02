#!/usr/bin/env bash
# PostToolUse (Bash): the automatic caller of the `amends:` landing step --
# issue #3134 repair round 3, finding 3.
#
# Round 2 built `gates/amends_index.py::write_backlinks()`/
# `--apply-backlinks` (the landing-step action that writes a corrector's
# backlink into its amended target) but nothing anywhere called it
# automatically -- no CI workflow exists in this repo, no hook, no code
# path. A correcting PR could land with its `amends:` edge permanently
# unlinked unless a human remembered to run the CLI by hand (confirmed
# live: docs/issue-3134/reports/adversarial-review+knowledge-management-
# supersession-lifecycle+silent-failure-audit-48484397.md, "What was
# done" item 4 -- no `.github/workflows`, no caller in
# `merge-allow-gate.sh`, no caller anywhere).
#
# `PostToolUse` cannot deny -- this hook is pure side-effect, mirroring
# `post-landing-obligation-gate.sh`'s own strict `gh pr merge`/
# `cd DIR && gh pr merge` command-shape validation and orchestrator-only
# posture. Unlike that hook (which resolves issue/role from the merged
# PR's OWN head branch), `amends:` is repo-local (same class as
# `spec_index.py` -- checks this repo's own tree, not a consumer's), so
# there is no per-issue branch to resolve here: this hook always targets
# the checkout `gh pr merge` itself ran from.
#
# issue #3134 repair round 4: "did the merge actually succeed" is NOT
# decided by `tool_response`-text failure markers (there is no exit-code
# field in the PostToolUse payload for Bash, which is why round 3 reached
# for text in the first place) -- `gh pr merge --help` matches the
# command-shape check and carries no failure marker either, and PR #3168
# reproduced this hook pushing to a scratch remote's default branch in
# response to that non-merge command. Fixed two ways: reject
# `--help`/`-h`/`--dry-run` outright, and require `gh pr view <pr>
# --json state,mergedAt` to independently confirm `state == "MERGED"`
# with a non-empty `mergedAt` before calling `land()` at all. Absence of
# a failure marker is never sufficient on its own anymore.
#
# `gates/amends_landing.py::land()` does the actual work: clones the
# merged checkout's own `origin` remote at its default branch into a
# disposable directory (never mutates the orchestrator's own live working
# tree -- a concurrently-running session or human may be using it),
# applies backlinks + regenerates the index there, and pushes the result
# straight back if anything changed. A clone/push failure is logged to
# stderr and never blocks anything -- same fail-open posture as
# `post-landing-obligation-gate.sh`.
#
# Identity: orchestrator only (`TOKENMAXXXER_SPAWNED` empty), same
# SessionStart-snapshot-first / live-env-var-fallback check
# `merge-allow-gate.sh` already uses -- a spawned session is never
# supposed to run `gh pr merge` at all (contract v3 s10: "never approve or
# merge yourself"), and this hook must not auto-push a follow-up commit on
# its behalf if one somehow does.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0
[ -f "$CHECKOUT/gates/amends_landing.py" ] || exit 0

GUARD=""
IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

try:
    e = json.loads(os.environ.get("ALA_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
if not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)

# --- strict command-shape validation, ported from merge-allow-gate.sh /
# post-landing-obligation-gate.sh -----------------------------------------
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)

OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


sys.path.insert(0, os.environ.get("OTR_HOOKS_DIR", ""))
from hook_input import cd_target_dir  # noqa: E402

if len(tokens) >= 3 and tokens[0] == "gh" and tokens[1] == "pr" and tokens[2] == "merge":
    _tail = tokens[3:]
    target_cwd = None
elif (len(tokens) >= 6 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] == "gh" and tokens[4] == "pr" and tokens[5] == "merge"):
    _tail = tokens[6:]
    target_cwd = cd_target_dir(cmd)
else:
    sys.exit(0)

if any(_is_operator_token(t) for t in _tail):
    sys.exit(0)

# --- issue #3134 repair round 4: a command-shape match is not proof a
# merge happened. `gh pr merge --help` matches every check above this
# line, and under the old "no failure marker in the tool_response text"
# heuristic it was indistinguishable from a real merge -- PR #3168's
# independent verification reproduced this live, pushing to a scratch
# remote's default branch in response to `--help`. Fixed with two
# checks, not one: reject any flag that cannot possibly perform a merge
# (its help/dry-run text has no failure marker either, so text alone
# never rules these out), THEN require `gh pr view` -- not the captured
# response text, not the absence of an error string -- to confirm the PR
# is actually MERGED before doing anything.
NON_MERGE_FLAGS = {"--help", "-h", "--dry-run"}
if any(t in NON_MERGE_FLAGS for t in tokens):
    sys.exit(0)

# --- identity: orchestrator only, never a spawned session ---------------
spawned = bool(os.environ.get("TOKENMAXXXER_SPAWNED", ""))
session_id = e.get("session_id")
if isinstance(session_id, str) and session_id:
    state_dir = os.environ.get(
        "OTR_SKILL_BIND_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-role-bind"),
    )
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    snapshot_path = os.path.join(state_dir, safe_session + ".json")
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
        if isinstance(snapshot, dict) and "spawned" in snapshot:
            spawned = bool(snapshot["spawned"])
    except (OSError, ValueError):
        pass
if spawned:
    sys.exit(0)  # a role session — never this hook's target

run_cwd = target_cwd or e.get("cwd") or os.getcwd()

# --- resolve a PR reference `gh pr view` accepts (number, or a full URL's
# number), ported from merge-allow-gate.sh's own PR-number resolution --
# (path:on-the-record/hooks/merge-allow-gate.sh lines 180-197). No
# explicit number (an implicit "current PR" merge) falls through to a
# bare `gh pr view` below, which itself needs `run_cwd` still checked out
# on the merged branch to resolve anything -- `gh pr merge` moves the
# checkout to the base branch and deletes the head branch by default, so
# that case legitimately confirms nothing and is left unreached (no
# backlink applied) rather than guessed at.
rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]
url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
if url_m:
    pr_ref = url_m.group(2)
else:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    pr_ref = num_m.group(1) if num_m else None

# --- authoritative confirmation: MERGED state comes from `gh pr view`
# itself, never from tool_response text or the absence of an error
# string -- the one check the old heuristic skipped entirely -----------
view_cmd = ["gh", "pr", "view"]
if pr_ref:
    view_cmd.append(pr_ref)
view_cmd += ["--json", "state,mergedAt"]
try:
    vr = subprocess.run(view_cmd, capture_output=True, text=True,
                         timeout=30, cwd=run_cwd)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if vr.returncode != 0:
    sys.exit(0)  # gh could not confirm a PR here — nothing to apply
try:
    info = json.loads(vr.stdout)
except ValueError:
    sys.exit(0)
if (not isinstance(info, dict) or info.get("state") != "MERGED"
        or not info.get("mergedAt")):
    sys.exit(0)  # not actually merged

# --- resolve this checkout's own origin remote + default branch ---------
try:
    r = subprocess.run(["git", "-C", run_cwd, "remote", "get-url", "origin"],
                        capture_output=True, text=True, timeout=20)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0 or not r.stdout.strip():
    sys.exit(0)
remote = r.stdout.strip()

branch = "main"
try:
    br = subprocess.run(
        ["git", "-C", run_cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True, timeout=20,
    )
    if br.returncode == 0 and br.stdout.strip():
        branch = br.stdout.strip().rsplit("/", 1)[-1]
except (OSError, subprocess.SubprocessError):
    pass

checkout = os.environ.get("ALA_CHECKOUT")
script = os.path.join(checkout, "gates", "amends_landing.py")
try:
    result = subprocess.run(
        [sys.executable, script, remote, branch],
        capture_output=True, text=True, timeout=180,
    )
except (OSError, subprocess.SubprocessError) as exc:
    # A hang past the 180s cap (TimeoutExpired) or an unlaunchable
    # interpreter/script (OSError) must not surface as a raw traceback --
    # same fail-open-and-report posture as every other subprocess call in
    # this file, just applied to the one call this file's own review
    # (issue #3134 repair round 3, silent-failure-audit skill) found
    # unguarded.
    sys.stderr.write("amends-landing-apply: " + str(exc) + "\n")
    sys.exit(0)
if result.returncode != 0:
    sys.stderr.write("amends-landing-apply: " + result.stderr.strip() + "\n")
sys.exit(0)
PY

[ -n "$GUARD" ] || { echo "amends-landing-apply: heredoc assignment produced no program (disk full / temp file unavailable?) -- bailing, backlinks not applied this call" >&2; exit 0; }

OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)" ALA_PAYLOAD="$payload" ALA_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
exit 0
