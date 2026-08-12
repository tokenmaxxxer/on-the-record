#!/usr/bin/env bash
# PreToolUse (Bash|WebFetch): deny fail-closed when a known credential/
# secret pattern reaches the network (issue #903, following #894/#902's
# security re-eval — the one residual class the on-the-record
# review-before-main / revert compensating controls cannot undo:
# once a token leaves the process over the network it is compromised
# for good, no matter how the resulting change is reviewed or reverted
# afterward).
#
# Universal, pattern-based — NOT a per-project command allow/deny list
# (the operator already rejected that approach as intractable across
# diverse targets, per the issue body). This checks two surfaces:
#
#   Bash: tool_input.command contains BOTH a credential-shape match AND
#   a network-reaching signal (curl/wget/nc/ssh/scp as a command word,
#   anywhere in the command or after a `|` pipe segment).
#
#   WebFetch (and any other tool exposing a url/headers/body-shaped
#   tool_input): a credential-shape match anywhere in tool_input.url,
#   tool_input.headers, or tool_input.body.
#
# Same credential pattern set as credential-record-guard.sh (gho_/ghp_/
# ghs_/ghr_/github_pat_/sk-/AKIA). Kept as a separate file rather than
# folding into credential-record-guard.sh: that hook is scoped to
# docs/** Write/Edit/MultiEdit content leakage, a different tool_name
# set and a different fragment-extraction shape; this hook answers a
# different question (command/network leakage) over a different
# tool_name set (Bash/WebFetch) — one hook file per concern, matching
# every other hook in this directory.
#
# HONEST LIMIT: this is a plaintext-pattern match. base64/hex/rot13/
# split-string obfuscation of the credential text evades it. This
# raises the bar for the one irreversible-harm class; it is not a
# perfect boundary. The complementary control this cannot replace is
# network egress allow-listing at the hosting environment level —
# transfer that concern there, do not expect this hook to catch an
# obfuscated exfiltration attempt.
#
# Shape modeled on credential-record-guard.sh: stdin JSON payload, a
# trap remapping unexpected exit to 2 (fail closed by construction),
# ORCHESTRATE_OFF kill switch checked first, python3 for the actual
# logic, exit 2 + stderr message to deny, exit 0 to pass.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2
CNG_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, sys

sys.path.insert(0, os.environ.get("CNG_HOOKS_DIR", ""))
from credential_example_allowlist import EXAMPLE_ALLOWLIST

def deny(msg):
    sys.stderr.write("credential-network-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CNG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
tool_name = e.get("tool_name") or ""
if tool_name not in ("Bash", "WebFetch"):
    sys.exit(0)
ti = e.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)

CRED_PATTERNS = [
    (r"gh[oprs]_[A-Za-z0-9]{36,}", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub fine-grained PAT"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI-style secret key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
]

def find_credentials(text):
    if not isinstance(text, str):
        return []
    hits = []
    for pat, label in CRED_PATTERNS:
        for m in re.finditer(pat, text):
            if m.group(0) in EXAMPLE_ALLOWLIST:
                continue
            hits.append(label)
            break
    return hits

NETWORK_TOOLS = {"curl", "wget", "nc", "ncat", "netcat", "ssh", "scp", "sftp", "telnet"}

def command_reaches_network(command):
    if not isinstance(command, str):
        return False
    try:
        # shlex handles quoting; a command with unbalanced quotes falls
        # back to a coarse word split so a malformed command can never
        # silently skip the network check.
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    # Split on shell separators so a network tool anywhere in a
    # pipeline / chain (a | curl ..., x && wget ..., x; nc ...) is
    # still seen as a command word, not just argv[0].
    words = re.split(r"[|;&]+|\$\(|`", command)
    candidate_words = set(tokens)
    for segment in words:
        for tok in segment.split():
            candidate_words.add(tok.strip("()"))
    for word in candidate_words:
        base = word.rsplit("/", 1)[-1]
        if base in NETWORK_TOOLS:
            return True
    return False

hits = []

if tool_name == "Bash":
    command = ti.get("command")
    if command_reaches_network(command):
        hits = find_credentials(command)
elif tool_name == "WebFetch":
    for field in ("url", "headers", "body"):
        val = ti.get(field)
        if isinstance(val, dict):
            val = json.dumps(val)
        hits += find_credentials(val)

if hits:
    deny(
        "credential/secret pattern (%s) reaching the network via %s is denied "
        "fail-closed (issue #903). This blocks the one irreversible-harm class "
        "review-before-main and revert cannot undo. If this is a false "
        "positive, remove the secret-shaped text from the command/input."
        % (", ".join(sorted(set(hits))), tool_name)
    )
sys.exit(0)
PY

CNG_PAYLOAD="$payload" CNG_HOOKS_DIR="$CNG_HOOKS_DIR" python3 -c "$GUARD"
rc=$?
exit "$rc"
