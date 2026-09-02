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
# issue #3134 repair round 5 (PR #3175's two gaps): (1) `-R`/`--repo`/
# `--repo=`/an inline `GH_REPO=...` prefix/a `cd` into a different
# checkout were all accepted by the command-shape check and then dropped
# before the confirming `gh pr view` call, so confirmation could run
# against the WRONG repo's PR while still pushing to this checkout's own
# `origin` -- decoupled confirmation from the thing actually merged. Now
# refused outright: the repo this hook may land backlinks for is fixed to
# the session's OWN cwd's `origin` (never a `cd` target inside the
# command, never a `-R`/`--repo`/`GH_REPO` value) before the command is
# even inspected, and any of those signals naming a DIFFERENT repo exits
# nonzero with one stderr line naming both repos, writing nothing. (2)
# every declined path used to be silent (`sys.exit(0)`, no stderr) --
# round 4's own audit named this. Every decline below is now one of three
# classes, per PR #3175's own framing: class A ("not a merge, nothing to
# do" -- the command wasn't `gh pr merge`-shaped at all, or was
# `--help`/`-h`/`--dry-run`) stays silent, exit 0 -- this is a designed
# quiet outcome (every ordinary Bash call reaches this hook; spamming
# stderr on each one would bury the signal), not an absorbed failure.
# Class B ("was a merge, confirmation could not run" -- `gh` unlaunchable,
# non-zero exit, malformed/empty JSON) and class C ("was a merge,
# confirmed not merged") each emit exactly one stderr line and exit
# nonzero. The PR number fed to the confirming `gh pr view` is read off
# `tool_response` (the Bash tool's own result, i.e. what `gh pr merge`
# actually printed on success) rather than re-parsed out of the command
# string -- the command string is attacker/author-controlled shape, not a
# report of what happened.
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

# issue #3134 repair round 5: an inline `VAR=value` prefix (the shape
# `GH_REPO=other/repo gh pr merge ...` takes -- Claude's Bash tool does
# not persist exported env vars across calls, so this inline form is the
# only way a command can actually carry `GH_REPO`) is stripped off before
# matching the `gh pr merge` shape, both at the top level and again right
# after a `cd DIR &&` -- otherwise it fell through to class A ("not a
# merge") and never got checked against gap 1's repo-remit rule at all.
_ENV_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _strip_env_prefix(toks):
    envs = {}
    i = 0
    while i < len(toks):
        m = _ENV_ASSIGN_RE.match(toks[i])
        if not m:
            break
        envs[m.group(1)] = m.group(2)
        i += 1
    return envs, toks[i:]


env_prefix, _rest = _strip_env_prefix(tokens)
if len(_rest) >= 3 and _rest[0] == "gh" and _rest[1] == "pr" and _rest[2] == "merge":
    _tail = _rest[3:]
    target_cwd = None
elif len(_rest) >= 6 and _rest[0] == "cd" and _rest[2] == "&&":
    _inner_envs, _inner = _strip_env_prefix(_rest[3:])
    if len(_inner) >= 3 and _inner[0] == "gh" and _inner[1] == "pr" and _inner[2] == "merge":
        env_prefix.update(_inner_envs)
        _tail = _inner[3:]
        target_cwd = cd_target_dir(cmd)
    else:
        sys.exit(0)  # class A: not a merge command
else:
    sys.exit(0)  # class A: not a merge command

if any(_is_operator_token(t) for t in _tail):
    sys.exit(0)  # class A: chained/substituted -- not a bare merge command

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
if any(t in NON_MERGE_FLAGS for t in _tail):
    sys.exit(0)  # class A: not a merge -- help/dry-run never merges anything

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

# --- issue #3134 repair round 5, gap 1: repo targeting -------------------
# The repo this hook may land backlinks for is fixed BEFORE the command is
# inspected at all: the session's own `cwd`'s `origin` (never a `cd`
# target from inside the command -- "cd into another checkout, then
# merge" is one of the shapes this refuses). `-R`/`--repo`/`--repo=`/an
# inline `GH_REPO=` prefix/a `cd` to a checkout with a different `origin`
# all name a PR outside this remit: confirming against it would run
# `gh pr view` against the wrong repo (round-4 verification, PR #3175,
# gap 1 -- "-R is accepted by the shape check and dropped before the
# confirming gh pr view call"). Refused before any `gh pr view` call, so
# the confirmation step itself is never pointed at the wrong repo.
_REPO_RE = re.compile(r"[:/]([^/:\s]+/[^/:\s]+?)(?:\.git)?/?$")


def _normalize_repo(value):
    if not value:
        return None
    value = value.strip()
    m = _REPO_RE.search(value)
    return (m.group(1) if m else value).lower()


def _origin_repo(dirpath):
    try:
        rr = subprocess.run(["git", "-C", dirpath, "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if rr.returncode != 0 or not rr.stdout.strip():
        return None
    return _normalize_repo(rr.stdout.strip())


def _decline(prefix, message):
    sys.stderr.write((prefix + message).replace("\n", " ").rstrip() + "\n")
    sys.exit(1)


registered_cwd = e.get("cwd") or os.getcwd()
registered_repo = _origin_repo(registered_cwd)
if registered_repo is None:
    # class B: this WAS a merge command, but the confirmation machinery
    # itself (here, resolving this session's own repo) could not run.
    _decline("amends-landing-apply: ",
              "could not resolve this session's own registered repo "
              "(git remote get-url origin failed in " + str(registered_cwd)
              + ") -- declining to land backlinks")


def _explicit_repo_flag(tail_tokens):
    i = 0
    while i < len(tail_tokens):
        t = tail_tokens[i]
        if t in ("-R", "--repo"):
            return tail_tokens[i + 1] if i + 1 < len(tail_tokens) else None
        if t.startswith("--repo="):
            return t[len("--repo="):]
        if t.startswith("-R") and t != "-R":
            return t[2:]
        i += 1
    return None


explicit_flag = _explicit_repo_flag(_tail)
env_repo = env_prefix.get("GH_REPO") or os.environ.get("GH_REPO")

target_repo = None
target_repo_raw = None
if explicit_flag:
    target_repo_raw = explicit_flag
    target_repo = _normalize_repo(explicit_flag)
elif env_repo:
    target_repo_raw = env_repo
    target_repo = _normalize_repo(env_repo)
elif target_cwd:
    target_repo_raw = target_cwd
    target_repo = _origin_repo(target_cwd)

if target_repo_raw is not None and target_repo != registered_repo:
    # class B1/gap-1 refusal: named repo differs from (or, for a `cd`
    # target, could not be confirmed to match) the registered repo --
    # write nothing, name both repos in the one stderr line, exit nonzero.
    _decline(
        "amends-landing-apply: ",
        "refusing merge outside remit -- registered repo is '"
        + registered_repo + "', command targets '"
        + (target_repo or target_repo_raw) + "'",
    )

run_cwd = target_cwd or registered_cwd

# --- resolve a PR reference `gh pr view` accepts from the TOOL RESULT,
# not the command string -- issue #3134 repair round 5, gap 1's second
# half. The command string is authored input (what was asked for); the
# merged PR number that actually happened is what `gh pr merge` itself
# printed on success, captured in this hook's own `tool_response`. An
# implicit "current PR" merge (or a response whose wording this cannot
# parse) still falls through to a bare `gh pr view` below, which itself
# needs `run_cwd` still checked out on the merged branch to resolve
# anything -- `gh pr merge` moves the checkout to the base branch and
# deletes the head branch by default, so that case legitimately confirms
# nothing and is left unreached (no backlink applied) rather than guessed
# at.
resp = e.get("tool_response")
if isinstance(resp, str):
    resp_text = resp
elif resp is not None:
    try:
        resp_text = json.dumps(resp)
    except (TypeError, ValueError):
        resp_text = str(resp)
else:
    resp_text = ""
pr_m = re.search(r"[Mm]erged pull request #(\d+)", resp_text) or re.search(r"#(\d+)", resp_text)
pr_ref = pr_m.group(1) if pr_m else None

# --- authoritative confirmation: MERGED state comes from `gh pr view`
# itself, never from tool_response text or the absence of an error
# string -- the one check the old heuristic skipped entirely. Every
# failure to confirm (class B) or a confirmation that reports the PR is
# not merged (class C) now emits exactly one stderr line and exits
# nonzero, instead of the silent `sys.exit(0)` PR #3175 found on every
# one of these paths. -----------------------------------------------------
view_cmd = ["gh", "pr", "view"]
if pr_ref:
    view_cmd.append(pr_ref)
view_cmd += ["--json", "state,mergedAt"]
try:
    vr = subprocess.run(view_cmd, capture_output=True, text=True,
                         timeout=30, cwd=run_cwd)
except (OSError, subprocess.SubprocessError) as exc:
    _decline("amends-landing-apply: ",
              "gh pr view confirmation failed (subprocess error: "
              + str(exc)[:200] + ") -- declining to land backlinks")
if vr.returncode != 0:
    _decline("amends-landing-apply: ",
              "gh pr view confirmation failed (gh exited "
              + str(vr.returncode) + ": "
              + (vr.stderr.strip() or "no stderr")[:200]
              + ") -- declining to land backlinks")
try:
    info = json.loads(vr.stdout)
except ValueError:
    _decline("amends-landing-apply: ",
              "gh pr view confirmation failed (malformed JSON from gh pr "
              "view) -- declining to land backlinks")
if not isinstance(info, dict) or "state" not in info:
    _decline("amends-landing-apply: ",
              "gh pr view confirmation failed (empty/insufficient JSON "
              "from gh pr view) -- declining to land backlinks")
state = info.get("state")
if state != "MERGED" or not info.get("mergedAt"):
    _decline("amends-landing-apply: ",
              "gh pr view confirms PR " + (pr_ref or "(unresolved)")
              + " is not merged (state=" + str(state)
              + ") -- declining to land backlinks")

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

# issue #3134 repair round 5, gap 2: the guard's own exit code now
# carries the decline classification (class B/C: nonzero; class A and a
# confirmed-and-landed run: 0) instead of being forced to 0 unconditionally
# -- this repo's own hook contract already treats any nonzero-and-not-2
# exit from a PostToolUse hook as non-blocking (on-the-record/hooks/
# hook_input.py's own module docstring), so propagating it here changes
# nothing about `PostToolUse`'s inability to deny, only what an operator
# reading stderr+exit code can tell about why nothing landed.
OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)" ALA_PAYLOAD="$payload" ALA_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
exit $?
