#!/usr/bin/env python3
"""issue #2146 — single-dispatcher PreToolUse gate execution.

The 20 PreToolUse gate registrations used to run as 20 separate
fail-open-wrapper.sh + gate-script processes per tool call (measured
1,021ms serial for one Bash payload — each gate's LOGIC is cheap, the
cost is 20x process startup: bash + a fresh python3 interpreter per
gate). This dispatcher is registered ONCE for the union matcher and runs
all 20 checks inside one python process.

The gate scripts themselves stay on disk as the single source of truth:
every one of them is "bash preamble + one python body in a quoted PY
heredoc, payload passed via an env var". The dispatcher

  1. reads the stdin payload once,
  2. replicates each gate's bash preamble (kill switch, cheap grep
     fast-paths, tool-availability checks, extra env staging — see
     GATES below, each entry mirrors its script's preamble line for
     line), and
  3. extracts the PY heredoc body from the .sh file and exec()s it
     in-process with the same env-var contract, capturing SystemExit as
     the gate's exit code and stdout/stderr per gate.

Behavior contract preserved per gate (asserted by
test_dispatcher_equivalence.py, gate-by-gate, against the real scripts):

  * allow/deny verdicts and refusal-message text byte-identical;
  * fail-open semantics per gate: a crashing gate body is caught,
    ledgered via hook_ledger.record_fail_open, and never takes down the
    rest of the chain. Gates whose scripts trap non-0/2 exits into exit
    2 (fail CLOSED on crash: deliverable-guard and friends) keep that:
    their crash surfaces as a deny with the traceback on stderr, exactly
    as the standalone script behaved. Gates without that trap used to
    exit 1 (non-blocking, "skipped silently" by the platform's exit-code
    table) — in-dispatcher their crash is ledgered and does not affect
    the final exit code, which is the same platform-visible outcome;
  * exit-code contract: exit 2 with all deny messages on stderr when any
    gate denied, else exit 0. All matching gates always run (the
    platform ran all 20 registrations regardless of individual denies,
    so every deny message that used to appear still appears);
  * stdout hookSpecificOutput: at most one gate emits stdout JSON per
    call in practice (retry-loop-bound context for non-Bash;
    merge/spawn/gh-write allow decisions are mutually exclusive Bash
    shapes). The first non-empty gate stdout is forwarded verbatim.

Test-only escape hatch: OTR_DISPATCH_ONLY=<script.sh> runs exactly that
gate with the matcher check skipped — replicating a direct
`bash <script>` invocation for one-to-one equivalence comparison.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

# crash policies (what the script's bash trap did to a python-body crash):
VERBATIM = "verbatim"   # no trap: rc forwarded as-is (1 = non-blocking)
CLOSED2 = "closed2"     # trap 'rc!=0&&rc!=2 -> exit 2': crash fails CLOSED

BASH_TOOLS = frozenset({"Bash"})
WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})


def _grep_gh_pr_merge(p):
    return re.search(r"gh\s+pr\s+merge", p) is not None


def _grep_gh_pr_create_edit(p):
    return re.search(r"gh\s+pr\s+(create|edit)", p) is not None


def _grep_pr_base(p):
    return (re.search(r"gh\s+pr\s+create", p) is not None
            or ("gh" in p and "/pulls" in p))


def _grep_git_commit(p):
    return "git" in p and "commit" in p


def _grep_git_push(p):
    return "git" in p and "push" in p


def _need_gh_silent(env):
    return None if shutil.which("gh") else ""


def _need_gh_msg(script):
    def check(env):
        if shutil.which("gh"):
            return None
        return "[%s] skipping: gh not found (fail-open)\n" % script
    return check


def _need_git_silent(env):
    return None if shutil.which("git") else ""


def _need_git_msg(script):
    def check(env):
        if shutil.which("git"):
            return None
        return "[%s] skipping: git not found (fail-open)\n" % script
    return check


_CHECKOUT_CACHE = {}


def _checkout_resolve(clone):
    """Mirror of the _checkout_resolve() bash function in impact-guard.sh /
    merge-allow-gate.sh (clone fallback) and spawn-allow-gate.sh (no
    clone fallback)."""
    if clone in _CHECKOUT_CACHE:
        return _CHECKOUT_CACHE[clone]
    result = ""
    tm = os.environ.get("TOKENMAXXXER_CHECKOUT", "")
    if tm and os.path.isfile(os.path.join(tm, "spawn.py")):
        result = tm
    if not result:
        probe = HOOKS_DIR
        for _ in range(4):
            probe = os.path.dirname(probe)
            if os.path.isfile(os.path.join(probe, "spawn.py")):
                result = probe
                break
    if not result:
        home = os.environ.get("HOME", os.path.expanduser("~"))
        for cand in (
            os.path.join(home, ".claude/plugins/marketplaces/tokenmaxxxer"),
            os.path.join(home, ".claude/tokenmaxxxer/on-the-record"),
        ):
            if os.path.isfile(os.path.join(cand, "spawn.py")):
                result = cand
                break
    if not result and clone:
        own = os.path.join(os.environ.get("HOME", os.path.expanduser("~")),
                           ".claude/tokenmaxxxer/on-the-record")
        try:
            os.makedirs(os.path.dirname(own), exist_ok=True)
            subprocess.run(
                ["git", "clone", "-q",
                 "https://github.com/tokenmaxxxer/on-the-record.git", own],
                capture_output=True, timeout=120,
            )
        except Exception:
            pass
        if os.path.isfile(os.path.join(own, "spawn.py")):
            result = own
    _CHECKOUT_CACHE[clone] = result
    return result


def _env_contract(payload, env):
    env["OTR_HOOKS_DIR"] = HOOKS_DIR
    env["CG_SELF_PATH"] = os.path.join(HOOKS_DIR, "contract-guard.sh")
    return True


def _env_merge(payload, env):
    checkout = _checkout_resolve(clone=True)
    if not checkout:
        return False
    if not os.path.isfile(os.path.join(checkout, "gates",
                                       "landing_readiness.py")):
        return False
    env["OTR_HOOKS_DIR"] = HOOKS_DIR
    env["MAG_CHECKOUT"] = checkout
    return True


def _env_spawn(payload, env):
    checkout = _checkout_resolve(clone=False)
    if not checkout:
        return False
    env["SAG_CHECKOUT"] = checkout
    return True


def _env_impact(payload, env):
    checkout = _checkout_resolve(clone=True)
    if not checkout:
        return False
    env["IG_CHECKOUT"] = checkout
    env["IG_TARGET"] = os.getcwd()
    return True


def _env_retry(payload, env):
    if not payload:
        return False
    state_dir = os.environ.get(
        "OTR_RETRY_BOUND_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-retry-bound"))
    try:
        os.makedirs(state_dir, exist_ok=True)
    except OSError:
        pass
    env["OTR_RB_MODE"] = "pre"
    env["OTR_RB_STATE_DIR"] = state_dir
    env["OTR_RB_K"] = os.environ.get("OTR_RETRY_BOUND_K", "5")
    return True


def _env_cng(payload, env):
    env["CNG_HOOKS_DIR"] = HOOKS_DIR
    return True


def _env_crg(payload, env):
    env["CRG_HOOKS_DIR"] = HOOKS_DIR
    return True


def _env_rcg(payload, env):
    gates_dir = ""
    for rel in ("../gates", "../../gates"):
        cand = os.path.normpath(os.path.join(HOOKS_DIR, rel))
        if os.path.isdir(cand):
            gates_dir = cand
            break
    env["RCG_GATES_DIR"] = gates_dir
    return True


def _pre_approval(payload, env):
    # approval-gate.sh: `[ -n "${CLAUDE_SKILL:-}" ] || exit 0` before
    # reading the payload — a live-env check, deliberately ahead of the
    # snapshot resolution the python body then performs itself.
    # approval-gate.sh's own identity block still keys on CLAUDE_SKILL's
    # value (issue #2538: it dual-carrier-checks the value against the
    # branch/sidecar-derived role, see docs/issue-2538/reports/
    # implementation.md) — but the gate this dispatcher runs BEFORE the
    # payload read is presence-only, so it uses TOKENMAXXXER_SPAWNED.
    return bool(os.environ.get("TOKENMAXXXER_SPAWNED", ""))


# One entry per PreToolUse registration in hooks.json order.  Fields:
#   script      — the .sh file the python body is extracted from
#   tools       — the registration's matcher, applied to payload tool_name
#   payload_env — the env var the preamble passed the raw payload in
#   fastpath    — bash-preamble grep fast-path over the RAW payload text
#   need        — tool-availability check; returns None (present) or the
#                 skip message the preamble printed to stderr ("" = silent)
#   setup       — extra env staging mirroring the preamble; returns False
#                 to skip the gate (preamble exited 0)
#   crash       — VERBATIM or CLOSED2 (the script's trap policy)
GATES = [
    dict(script="retry-loop-bound.sh", tools=BASH_TOOLS | WRITE_TOOLS,
         payload_env="OTR_RB_PAYLOAD", setup=_env_retry, crash=VERBATIM),
    dict(script="deliverable-guard.sh",
         tools=WRITE_TOOLS | {"NotebookEdit"},
         payload_env="ORCH_PAYLOAD", crash=CLOSED2),
    dict(script="heredoc-command-refusal-gate.sh", tools=BASH_TOOLS,
         payload_env="HCRG_PAYLOAD", crash=VERBATIM),
    dict(script="upstream-defect-scope-guard.sh", tools=BASH_TOOLS,
         payload_env="UDSG_PAYLOAD", crash=CLOSED2),
    dict(script="contract-guard.sh", tools=BASH_TOOLS,
         payload_env="CG_PAYLOAD", fastpath=_grep_gh_pr_merge,
         need=_need_gh_msg("contract-guard.sh"), setup=_env_contract,
         crash=VERBATIM),
    dict(script="pr-preflight.sh", tools=BASH_TOOLS,
         payload_env="CG_PAYLOAD", fastpath=_grep_gh_pr_create_edit,
         need=_need_gh_silent, crash=VERBATIM),
    dict(script="pr-base-guard.sh", tools=BASH_TOOLS,
         payload_env="CG_PAYLOAD", fastpath=_grep_pr_base,
         need=_need_gh_silent, crash=VERBATIM),
    dict(script="spec-index-preflight.sh", tools=BASH_TOOLS,
         payload_env="CG_PAYLOAD", fastpath=_grep_git_commit,
         need=_need_git_silent, setup=_env_contract, crash=VERBATIM),
    dict(script="gate-registration-guard.sh", tools=BASH_TOOLS,
         payload_env="GRG_PAYLOAD", fastpath=_grep_git_commit,
         need=_need_git_msg("gate-registration-guard.sh"),
         setup=_env_contract, crash=VERBATIM),
    dict(script="acceptance-command-real-run-guard.sh", tools=BASH_TOOLS,
         payload_env="ACRG_PAYLOAD", fastpath=_grep_git_commit,
         need=_need_git_silent, setup=_env_contract, crash=CLOSED2),
    dict(script="live-fire-claim-real-run-guard.sh", tools=BASH_TOOLS,
         payload_env="LFCRG_PAYLOAD", fastpath=_grep_git_commit,
         need=_need_git_silent, setup=_env_contract, crash=CLOSED2),
    dict(script="impact-guard.sh", tools=BASH_TOOLS,
         payload_env="IG_PAYLOAD", setup=_env_impact, crash=VERBATIM),
    dict(script="merge-allow-gate.sh", tools=BASH_TOOLS,
         payload_env="MAG_PAYLOAD", fastpath=_grep_gh_pr_merge,
         need=_need_gh_silent, setup=_env_merge, crash=VERBATIM),
    dict(script="spawn-allow-gate.sh", tools=BASH_TOOLS,
         payload_env="SAG_PAYLOAD", setup=_env_spawn, crash=VERBATIM),
    dict(script="gh-write-allow-gate.sh", tools=BASH_TOOLS,
         payload_env="GWAG_PAYLOAD", crash=VERBATIM),
    dict(script="git-push-guard.sh", tools=BASH_TOOLS,
         payload_env="GPUG_PAYLOAD", fastpath=_grep_git_push,
         need=_need_git_silent, crash=VERBATIM),
    dict(script="credential-network-guard.sh",
         tools=BASH_TOOLS | {"WebFetch"},
         payload_env="CNG_PAYLOAD", setup=_env_cng, crash=CLOSED2),
    dict(script="record-claim-guard.sh", tools=WRITE_TOOLS,
         payload_env="RCG_PAYLOAD", setup=_env_rcg, crash=CLOSED2),
    dict(script="credential-record-guard.sh", tools=WRITE_TOOLS,
         payload_env="CRG_PAYLOAD", setup=_env_crg, crash=CLOSED2),
    dict(script="accumulation-claim-guard.sh", tools=WRITE_TOOLS,
         payload_env="ACG_PAYLOAD", crash=CLOSED2),
    dict(script="approval-gate.sh", tools=WRITE_TOOLS,
         payload_env="AG_PAYLOAD", setup=_pre_approval, crash=CLOSED2),
]

DISPATCHED_SCRIPTS = tuple(g["script"] for g in GATES)

_BODY_CACHE = {}


def _gate_body(script):
    """Extract and compile the quoted-PY-heredoc python body of a gate
    script. The .sh file stays the single source of truth; a script whose
    body cannot be found compiles to a no-op (fail-open)."""
    if script in _BODY_CACHE:
        return _BODY_CACHE[script]
    path = os.path.join(HOOKS_DIR, script)
    lines = []
    try:
        with open(path, encoding="utf-8") as fh:
            in_py = False
            for line in fh:
                if not in_py and "<<'PY'" in line:
                    in_py = True
                    continue
                if in_py:
                    if line.rstrip("\n") == "PY":
                        break
                    lines.append(line)
    except OSError:
        lines = []
    code = compile("".join(lines), path, "exec")
    _BODY_CACHE[script] = code
    return code


def _run_gate(gate, payload, raw_stderr):
    """Run one gate in-process. Returns (rc, stdout_text). Everything the
    gate writes to stderr is forwarded to raw_stderr."""
    script = gate["script"]
    fastpath = gate.get("fastpath")
    if fastpath is not None and not fastpath(payload):
        return 0, ""
    need = gate.get("need")
    if need is not None:
        msg = need(os.environ)
        if msg is not None:
            if msg:
                raw_stderr.write(msg)
            return 0, ""
    env = {}
    setup = gate.get("setup")
    if setup is not None and not setup(payload, env):
        return 0, ""
    env[gate["payload_env"]] = payload
    os.environ.update(env)

    out_buf, err_buf = io.StringIO(), io.StringIO()
    rc = 0
    crashed = False
    saved_path = list(sys.path)
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            gate_globals = {"__name__": "__main__", "__file__": script}
            try:
                exec(_gate_body(script), gate_globals)
            except SystemExit as exc:
                code = exc.code
                if code is None:
                    rc = 0
                elif isinstance(code, int):
                    rc = code
                else:
                    err_buf.write(str(code) + "\n")
                    rc = 1
            except BaseException:
                traceback.print_exc(file=err_buf)
                rc = 1
                crashed = True
    finally:
        sys.path[:] = saved_path

    if crashed or rc not in (0, 2):
        # the fail-open-wrapper's ledger contract, moved in-process
        try:
            import hook_ledger
            hook_ledger.record_fail_open(
                script, [script], hook_ledger.input_digest(payload), rc,
                "traceback" if crashed else "nonzero-exit")
        except Exception:
            pass

    if gate["crash"] == CLOSED2 and rc not in (0, 2):
        rc = 2

    raw_stderr.write(err_buf.getvalue())
    return rc, out_buf.getvalue()


def main():
    # kill switch — identical `case "${ORCHESTRATE_OFF:-}"` in every gate
    if os.environ.get("ORCHESTRATE_OFF", "") not in ("", "0", "false",
                                                     "no", "off"):
        return 0
    try:
        payload = sys.stdin.read()
    except Exception:
        payload = ""

    tool_name = None
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            tn = parsed.get("tool_name")
            if isinstance(tn, str) and tn:
                tool_name = tn
    except ValueError:
        pass

    only = os.environ.get("OTR_DISPATCH_ONLY", "")
    if only:
        # test-only single-gate mode: replicate a direct `bash <script>`
        # invocation one-to-one — no matcher, verbatim exit code/stdout.
        for gate in GATES:
            if gate["script"] == only:
                rc, out = _run_gate(gate, payload, sys.stderr)
                if out:
                    sys.stdout.write(out)
                return rc
        return 0

    denied = False
    stdout_payload = ""
    for gate in GATES:
        if tool_name is not None and tool_name not in gate["tools"]:
            # The platform applied this registration's matcher; an
            # unknown/absent tool_name runs every gate so a fail-closed
            # gate (deliverable-guard) still sees the malformed payload.
            continue
        try:
            rc, out = _run_gate(gate, payload, sys.stderr)
        except Exception:
            # dispatcher-level defect around one gate: fail open for that
            # gate only, never take down the chain
            try:
                import hook_ledger
                hook_ledger.record_fail_open(
                    gate["script"], [gate["script"]],
                    hook_ledger.input_digest(payload), None,
                    "dispatcher-error")
            except Exception:
                pass
            continue
        if rc == 2:
            denied = True
        if out and not stdout_payload:
            stdout_payload = out
    if stdout_payload:
        sys.stdout.write(stdout_payload)
    return 2 if denied else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        # a dispatcher crash must never block the tool call (fail open,
        # same posture as a crashing standalone gate without a trap)
        traceback.print_exc(file=sys.stderr)
        sys.exit(0)
