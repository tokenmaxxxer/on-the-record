#!/usr/bin/env bash
# PreToolUse (Bash): plugin-only default-on orchestrator merge-allow gate —
# issue #810, candidate 4 of docs/issue-810/proposals/technical-feasibility.md.
#
# Grants `hookSpecificOutput.permissionDecision: "allow"` for a `gh pr merge`
# call, scoped three ways per the proposal's Safety argument:
#   (a) TOKENMAXXXER_SPAWNED resolves empty — orchestrator only, never a
#       spawned session. Identity read reuses session-role-bind.sh's
#       SessionStart snapshot, exactly the way approval-gate.sh already
#       does (path:on-the-record/hooks/approval-gate.sh lines 72-92) — a
#       later in-session re-export of the env var cannot flip this hook's
#       belief about who is running. Issue #2538: only presence is ever
#       tested here, never a skill name, so this needs no skill identity —
#       the spawned-flag is the same presence signal without one.
#   (b) the command is `gh pr merge` against a resolvable, explicit PR
#       number — reuses contract-guard.sh's target-repo resolution
#       (path:on-the-record/hooks/contract-guard.sh lines 66-79) so no bare
#       `gh pr merge` (implicit "current PR") is ever auto-allowed.
#   (c) gates/landing_readiness.py's `classify` (path:gates/landing_readiness.py
#       line 31), invoked via its own CLI entrypoint against the target
#       checkout, reports that exact PR as READY with no reason suffix.
#
# Any other shape (unresolvable command, spawned session, PR not exactly READY,
# lookup failure) falls through to plain `exit 0` with no JSON — no change
# from today's classifier/manual-grant behavior. This hook only ever ADDS a
# permission signal; it never emits `"deny"` itself, and per the phase-2
# empirical check recorded in docs/issue-810/reports/implementation.md, an
# existing deny gate's exit-code-2 on the same `gh pr merge` call still wins
# over this hook's JSON `"allow"` when both fire — this hook cannot make a
# bad merge easier, only a good one faster.
#
# issue #824: the command-shape check is strict, not a substring search —
# the entire tool_input.command must tokenize (via shlex.shlex(posix=True,
# punctuation_chars=True), the only tokenizer that tracks bash's real
# quote/escape state instead of hand-rolling a quote-pairing regex — see
# docs/issue-824/proposals/strict-merge-allow-validation.md) to exactly
# ["gh","pr","merge",...args] or ["cd",DIR,"&&","gh","pr","merge",...args],
# with no other chaining/substitution operator token anywhere else in the
# list, before the PR-number/READY check ever runs — closing the
# `gh pr merge <n> && <anything>` bypass (any position, any chain operator,
# including a backslash-escaped-quote payload that desyncs a naive
# quote-stripping regex).
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2: cheap bash-level short-circuit before the python3 spawn below --
# skip the interpreter launch entirely when the raw payload plainly can't match this
# gate's own command-shape condition (checked again, authoritatively, in python).
grep -qE 'gh[[:space:]]+pr[[:space:]]+merge' <<<"$payload" || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

# --- locate the on-the-record checkout, for `gates/landing_readiness.py` ---
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
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0
[ -f "$CHECKOUT/gates/landing_readiness.py" ] || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys
# issue #2093: the shared total parser replaces this hook's own ad-hoc
# `cd <path> &&` regex. It ships next to the hooks (never under gates/,
# which a consumer checkout need not have) and it never raises.
sys.path.insert(0, os.environ.get("OTR_HOOKS_DIR", ""))
from hook_input import cd_target_dir  # noqa: E402


try:
    e = json.loads(os.environ.get("MAG_PAYLOAD", ""))
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

# --- strict command-shape validation (issue #824) ---------------------------
# The whole command must tokenize to exactly one of the two recognized
# shapes below, with no other chaining/substitution operator token
# anywhere else in the list — a substring match on "gh pr merge" is not
# enough, since `gh pr merge 42 && evil` (or `;`, `|`, prepended instead of
# appended, ...) contains that substring too. This runs before any
# identity/readiness check; failing it falls through to the same plain
# `exit 0` as every other unreached shape.
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)  # no legitimate invocation needs substitution or a newline

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)  # unbalanced quoting — unreached, same fail-open posture as today

# shlex's own `punctuation_chars` omits `;` (it is still split into its own
# token, just not tracked in that attribute) — add it explicitly so every
# shell control operator this hook must catch is covered.
OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


if len(tokens) >= 3 and tokens[0] == "gh" and tokens[1] == "pr" and tokens[2] == "merge":
    _tail = tokens[3:]
elif (len(tokens) >= 6 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] == "gh" and tokens[4] == "pr" and tokens[5] == "merge"):
    _tail = [tokens[1]] + tokens[6:]  # DIR, then everything after "merge"
else:
    sys.exit(0)  # not one of the two recognized shapes — unreached

if any(_is_operator_token(t) for t in _tail):
    sys.exit(0)  # a chaining/substitution operator survives outside the
    # one tolerated `&&` of a recognized `cd DIR &&` prefix

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Same primitive approval-gate.sh already trusts (path:on-the-record/hooks/
# approval-gate.sh lines 72-92) — this hook only ever fires for the
# orchestrator (not spawned), the mirror image of approval-gate.sh's
# role-session-only trigger.
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
        pass  # no snapshot yet — fall back to the live env var
if spawned:
    sys.exit(0)  # a role session — never this hook's target, contract v3 s10 unchanged

# --- target-repo / explicit-PR-number resolution ----------------------------
# Ported from contract-guard.sh's already-hardened resolution
# (path:on-the-record/hooks/contract-guard.sh lines 66-79): only the forms
# that resolve to an explicit PR number are handled; a bare `gh pr merge`
# with an implicit "current PR" is left unreached (no allow, no deny).
target_cwd = None
target_repo_flag = None

# A `cd` target that does not exist here is no target at all (issue #2093):
# handing the claim to subprocess(cwd=...) is what crashed this guard.
target_cwd = cd_target_dir(cmd)

rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]

url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
repo_flag_m = re.search(r"(?:-R|--repo)[= ]([^\s/]+/[^\s/]+)", rest)

if url_m:
    pr = url_m.group(2)
    target_cwd = None
    target_repo_flag = url_m.group(1)
elif repo_flag_m:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)
    pr = num_m.group(1)
    target_cwd = None
    target_repo_flag = repo_flag_m.group(1)
else:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)  # implicit "current PR" — cannot resolve without a checkout
    pr = num_m.group(1)

if target_repo_flag and target_cwd is None:
    # -R/--repo or a full URL with no local `cd` checkout: landing_readiness.py
    # needs a local checkout (docs/specs/approvers.md, docs/issue-<n>/reports/)
    # to compute has_record/has_approval — not fetchable, explicit unreached.
    sys.exit(0)

run_cwd = target_cwd or e.get("cwd") or os.getcwd()

# issue #2719 removed the issue-#1130 routing-fix that used to live here.
# It withheld this hook's "allow" (never a hard deny — see the file header)
# for a `gh pr merge` when: MUSTER_SKILLS mounted "secure-coding" or
# "release-engineering" (`candidates = [r for r in ("secure-coding",
# "release-engineering") if r in mounted]`), the local diff touched a
# per-skill hardcoded path-pattern list (`TRIGGER_PATH_PATTERNS`, itself a
# 2-key dispatch table keyed by the same two names), and that skill's own
# `docs/issue-<n>/reports/<role>.md` was absent. That is `role in ROLES`
# reproduced under skill identity (issue #2626 finding A) — a fixed
# 2-name tuple plus a name-keyed dispatch table, the same shape core#343
# removed from approval-gate.sh's OBSERVER_ROLES. issue #2610's own
# comment on this code already named it as unreshaped debt from the
# deleted 44-entry role catalog before this removal.
#
# There is no non-identity signal this hook can use for "which skill's
# trigger patterns apply" without either keeping the identity check or
# reconstructing the same table under another name (a container/config
# move the #2548 test treats as no removal at all) — per the operator
# ruling of 2026-08-27, the capability is removed rather than reshaped.
#
# CAPABILITY REMOVED, asymmetrically:
#   - secure-coding: NOT a net loss. `on-the-record/hooks/quality-bar-
#     gate.sh` independently DENIES (not merely withholds an allow) any
#     `gh pr merge` on a secure-coding-bar-scoped PR (its own
#     `_TRIGGER_PATH_PATTERNS["secure-coding"]` is byte-identical to the
#     list removed here) lacking a `quality_bar_verdict: bar-met` line,
#     and per this hook's own file header a deny gate always wins over
#     this hook's allow. secure-coding diffs missing their record are
#     still blocked by that gate, unconditionally, whether or not this
#     hook would have granted its convenience allow.
#   - release-engineering: a REAL loss, with no replacement anywhere else
#     in either enforcement repo (grep confirmed — see this issue's
#     record). A `gh pr merge` on a release-engineering session touching
#     CHANGELOG.md/package.json/pyproject.toml/VERSION with no
#     `docs/issue-<n>/reports/<slug>.md` on disk no longer has its
#     auto-allow withheld by this hook; it is now treated the same as any
#     other session's diff once `gates/landing_readiness.py` reports
#     READY. This only ever affected whether the merge auto-executed
#     without an interactive confirmation — it never blocked a human from
#     merging manually, and no other gate denies on this basis, so the
#     loss is scoped to that convenience-friction, not to a hard block
#     disappearing.
#
# --- call the existing READY predicate, not a reimplementation -------------
checkout = os.environ.get("MAG_CHECKOUT")
script = os.path.join(checkout, "gates", "landing_readiness.py")
try:
    r = subprocess.run(
        [sys.executable, script, "--repo", run_cwd],
        capture_output=True, text=True, timeout=60,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)  # lookup failure — fail-open, same posture as contract-guard.sh

ready_line = re.compile(r"^PR #%s: READY\s*$" % re.escape(pr), re.MULTILINE)
if not ready_line.search(r.stdout):
    sys.exit(0)  # not exactly READY (blocked, or a reason suffix) — no allow

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": (
            "merge-allow-gate: PR #%s is landing_readiness=READY "
            "(gates/landing_readiness.py) and this is the orchestration "
            "session (not spawned) — issue #810." % pr
        ),
    }
}))
sys.exit(0)
PY

OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)" MAG_PAYLOAD="$payload" MAG_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
rc=$?
exit "$rc"
