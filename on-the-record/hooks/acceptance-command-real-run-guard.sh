#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on a `git commit` staging an
# `acceptance: <command> — result: PASS|FAIL` citation (the #870/#892
# citation shape) whose claimed result does not match an ACTUAL re-run of
# that command against the REAL current target — issue #914 step 2,
# mechanism (a) (generalizes #870 candidate-b), sibling to
# gate-registration-guard.sh and live-fire-test-guard.sh on the same
# `git commit` interception point.
#
# #892 (record_lint.py's outcome_claim_citation_check) already requires
# an OUTCOME claim ("done"/"PASS"/"complete") to carry a citation that
# LOOKS like an executed-live reference (this exact `acceptance: ... —
# result: ...` shape is already in its accepted vocabulary). What #892
# never checks is whether the cited command actually ran, this turn,
# against the real current tree, and actually produced the claimed
# result — a stale or fabricated `acceptance: pytest — result: PASS`
# line satisfies #892 identically to a genuine one. This guard closes
# that gap by re-running the cited command itself at commit time.
#
# One-time-confirmed acceptance command per target, mirroring #831's
# remote-preflight setup pattern: instead of an ephemeral ledger_write
# event (out of reach for a stateless PreToolUse hook with no access to
# spawn.py's orchestrator-side runs/ledger.jsonl), the confirmation is a
# durable, git-tracked row in docs/specs/acceptance-commands.md — adding
# that row IS the one-time confirmation event, discoverable the same way
# docs/specs/approvers.md/enforcement-boundary.md rows already are.
#
# Trigger: any staged (`A`/`M`, or the destination side of `R`/`C`) file
# whose staged content contains an `acceptance: <command> — result:
# PASS|FAIL` line. `result: UNMEASURED` is the degrade path (#310's
# `unverifiable:` shape reused per the phase-1 proposal) and is never
# re-run — an UNMEASURED claim makes no assertion to verify.
#
# For each such citation:
#   - the cited command must appear verbatim as a recorded row in
#     docs/specs/acceptance-commands.md — an uncommitted-to-the-registry
#     command citing PASS/FAIL is refused (never a false PASS from an
#     ad hoc, never-confirmed command string);
#   - the command is then actually executed (bounded timeout, no shell
#     interpolation — shlex-split argv, matching this plugin's
#     no-footgun convention) against the real current working tree;
#   - the citation's claimed result must match the actual exit status
#     (0 -> PASS, nonzero -> FAIL) or the commit is refused.
#
# Escape hatch: commit-message trailer `Acceptance-recheck-N/A: <reason>`
# for a citation that genuinely cannot be re-run at commit time (mirrors
# live-fire-test-guard.sh's `Live-fire-N/A:` trailer convention).
#
# Fails open on any environment gap (missing python3/git, not a `git
# commit`, no staged citation, unreadable registry). Fails closed only
# on a positively-determined unregistered command or a result mismatch.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }
command -v git >/dev/null 2>&1 || { trap - EXIT; exit 0; }

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("acceptance-command-real-run-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("ACRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

# same punctuation-aware tokenizer gate-registration-guard.sh uses
# (issue #866/#876/#882): survives global `git` options and unspaced
# subshell punctuation without a false negative or a substring false
# positive.
try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

if re.search(r"(?im)^\s*Acceptance-recheck-N/A\s*:\s*\S", cmd):
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()

try:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                        capture_output=True, text=True, timeout=20, cwd=cwd)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
repo_root = r.stdout.strip()
if not repo_root:
    sys.exit(0)

try:
    r = subprocess.run(["git", "diff", "--cached", "--name-status"],
                        capture_output=True, text=True, timeout=20, cwd=repo_root)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)

staged = set()
for line in r.stdout.splitlines():
    if not line.strip():
        continue
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    status, path = parts[0], parts[-1]
    if status == "D":
        continue
    staged.add(path)

if not staged:
    sys.exit(0)


def read_staged(rel_path):
    rr = subprocess.run(["git", "show", ":" + rel_path],
                         capture_output=True, timeout=20, cwd=repo_root)
    if rr.returncode != 0:
        return None
    try:
        return rr.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


_ACCEPTANCE_CITE_RE = re.compile(
    r"acceptance:\s*(.+?)\s*(?:—|--|-)\s*result:\s*(PASS|FAIL|UNMEASURED)\b")

citations = []  # (path, command, claimed)
for path in sorted(staged):
    text = read_staged(path)
    if text is None:
        continue
    for m in _ACCEPTANCE_CITE_RE.finditer(text):
        command_str = m.group(1).strip().strip("`")
        claimed = m.group(2).upper()
        if claimed == "UNMEASURED":
            continue
        citations.append((path, command_str, claimed))

if not citations:
    sys.exit(0)

registry_text = read_staged("docs/specs/acceptance-commands.md")
if registry_text is None:
    abs_registry = os.path.join(repo_root, "docs/specs/acceptance-commands.md")
    try:
        with open(abs_registry, "r", encoding="utf-8") as f:
            registry_text = f.read()
    except OSError:
        registry_text = ""

_ROW_RE = re.compile(r"^\|\s*[^|]*\|\s*`([^`]+)`\s*\|", re.MULTILINE)
recorded_commands = {m.group(1).strip() for m in _ROW_RE.finditer(registry_text)}

problems = []
for path, command_str, claimed in citations:
    if command_str not in recorded_commands:
        problems.append(
            f"{path}: cites `acceptance: {command_str} — result: {claimed}` "
            "but that command has no row in docs/specs/acceptance-commands.md "
            "-- record it there once (the one-time-confirmed acceptance "
            "command for this target) before citing a PASS/FAIL result, or "
            "cite `UNMEASURED-with-reason: no acceptance command on record "
            "for this target` instead."
        )
        continue
    try:
        argv = shlex.split(command_str)
    except ValueError:
        problems.append(f"{path}: acceptance command `{command_str}` is not "
                         "a parseable shell command -- cannot re-run it")
        continue
    if not argv:
        continue
    try:
        run = subprocess.run(argv, cwd=repo_root, capture_output=True,
                              text=True, timeout=180)
        actual_pass = run.returncode == 0
    except subprocess.TimeoutExpired:
        problems.append(
            f"{path}: acceptance command `{command_str}` did not complete "
            "within 180s -- cannot confirm the claimed result this turn; "
            "cite UNMEASURED-with-reason if it is genuinely too slow to "
            "re-run at commit time, or add an "
            "`Acceptance-recheck-N/A: <reason>` commit trailer"
        )
        continue
    except OSError as ex:
        problems.append(
            f"{path}: acceptance command `{command_str}` failed to start "
            f"({ex}) -- cannot confirm the claimed result"
        )
        continue
    claimed_pass = claimed == "PASS"
    if actual_pass != claimed_pass:
        problems.append(
            f"{path}: cites `acceptance: {command_str} — result: {claimed}` "
            f"but a real re-run against the current target just exited "
            f"{run.returncode} ({'PASS' if actual_pass else 'FAIL'}) -- the "
            "claim does not match a real re-execution of its own recorded "
            "acceptance command"
        )

if problems:
    deny(
        "a done/works claim for a target deliverable must be backed by an "
        "actual re-run of that target's recorded acceptance command against "
        "the real current target (issue #914 mechanism a):\n"
        + "\n".join(problems)
    )
PY

ACRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
