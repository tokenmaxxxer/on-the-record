"""Tests for issue #556: gate cache-layout resolution and ownership-check
order in record-claim-guard.sh (role-spec-reference-guard.sh retired, issue #2138).

Covers the issue's three acceptance checks:
1. Each hook resolves its gates/ module from the plugin cache layout
   (packaged on-the-record/gates/ copy) and does not crash with
   ModuleNotFoundError.
2. Ownership check precedes any crashable work: with the gate module
   deliberately unimportable, a write outside the owned surface exits 0.
3. Fail-closed is preserved for owned paths: with the gate module
   deliberately unimportable, a write to an owned path still exits non-zero.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ON_THE_RECORD = HOOKS_DIR.parent
REPO_ROOT = ON_THE_RECORD.parent

RCG_OWNED_PATH = "docs/issue-999/reports/implementation.md"
RCG_OWNED_CONTENT = "unverifiable:\n"

# issue #2295: the packaged copy under on-the-record/gates/ (what a real
# installed plugin session actually resolves per issue #556) is a
# hand-maintained duplicate of these three files under the repo-root
# gates/ (the source of truth developed against). Nothing before this
# test enforced the two stay in sync — gates/role_spec_shape.py picked up
# playbook_refs/judgment_axes checks (issues #1174, #573) and
# gates/record_lint.py picked up the sibling-import-collision fix (issue
# #2226) while the packaged copies silently kept serving the old,
# incomplete/buggy behavior to every hook session that resolves gates
# from the plugin cache layout — no error, no warning, tests still green,
# because nothing compared the two trees. This pins the invariant.
_SYNCED_GATE_FILES = ("gates.py", "record_lint.py", "role_spec_shape.py")


def test_packaged_gates_copy_matches_source_of_truth():
    mismatched = []
    for name in _SYNCED_GATE_FILES:
        src = (REPO_ROOT / "gates" / name).read_text(encoding="utf-8")
        packaged = (ON_THE_RECORD / "gates" / name).read_text(encoding="utf-8")
        if src != packaged:
            mismatched.append(name)
    assert not mismatched, (
        f"on-the-record/gates/{{{', '.join(mismatched)}}} has drifted from "
        f"gates/{{{', '.join(mismatched)}}} — sync the packaged copy (it is "
        f"what a real installed hook session resolves per issue #556, not "
        f"the repo-root file)."
    )


def test_packaged_gates_copy_drift_check_actually_catches_drift(tmp_path):
    """Live-fire proof: seed a packaged copy one byte off from its source
    and confirm the comparison above would refuse it, not pass trivially."""
    seeded_root = tmp_path / "seeded"
    seeded_gates = seeded_root / "on-the-record" / "gates"
    seeded_gates.mkdir(parents=True)
    (seeded_gates / "role_spec_shape.py").write_text(
        (REPO_ROOT / "gates" / "role_spec_shape.py").read_text(encoding="utf-8")
        + "\n# drifted\n", encoding="utf-8")

    src = (REPO_ROOT / "gates" / "role_spec_shape.py").read_text(encoding="utf-8")
    packaged = (seeded_gates / "role_spec_shape.py").read_text(encoding="utf-8")
    assert src != packaged, "seeded fixture failed to introduce drift"


def _run(script, tool_input, plugin_root, tool_name="Write"):
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    return subprocess.run(
        ["bash", str(script)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _make_cache_dir(tmp_path):
    """Simulate ~/.claude/plugins/cache/tokenmaxxxer/on-the-record/<hash>/:
    a copy of on-the-record/ only — repo-root gates/ is never present."""
    cache = tmp_path / "cache" / "on-the-record"
    shutil.copytree(ON_THE_RECORD / "hooks", cache / "hooks")
    shutil.copytree(ON_THE_RECORD / "gates", cache / "gates")
    return cache


def _make_broken_gates_cache(tmp_path):
    """A cache dir whose packaged gates/ exists but cannot be imported."""
    cache = tmp_path / "cache" / "on-the-record"
    shutil.copytree(ON_THE_RECORD / "hooks", cache / "hooks")
    gates = cache / "gates"
    gates.mkdir(parents=True)
    broken = "raise ImportError('simulated broken module')\n"
    (gates / "gates.py").write_text(broken)
    (gates / "record_lint.py").write_text(broken)
    (gates / "role_spec_shape.py").write_text(broken)
    return cache


# --- check 1: resolves gates/ from the packaged cache layout, no crash ---

def t_rcg_resolves_from_cache_layout(tmp_path):
    cache = _make_cache_dir(tmp_path)
    p = tmp_path / RCG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(p), "content": RCG_OWNED_CONTENT}, cache.parent)
    assert "ModuleNotFoundError" not in r.stderr
    assert r.returncode in (0, 2)


# --- check 2: ownership check precedes import; outside-surface passes ---

def t_rcg_ownership_check_precedes_import(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    outside = tmp_path / "outside" / "note.md"
    outside.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(outside), "content": "5 of 9 items, no derivation"}, cache.parent)
    assert r.returncode == 0, r.stderr


# --- check 3: fail-closed preserved for owned paths ---

def t_rcg_fail_closed_for_owned_path(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    p = tmp_path / RCG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(p), "content": RCG_OWNED_CONTENT}, cache.parent)
    assert r.returncode == 2, r.stderr


# --- issue #948: a hooks.json-wired script committed without the exec
# bit (100644) dies with "/bin/sh: Permission denied" on every
# invocation and silently never runs -- fail-open, not fail-closed.
# `git ls-files -s on-the-record/hooks/` is the read evidence: 4
# scripts (delegated-judgment-gate.sh, live-fire-claim-real-run-guard.sh,
# live-fire-test-guard.sh, test-authoring-invariant-guard.sh) were
# committed 100644 while every other wired .sh sibling was 100755.

def _wired_hook_scripts():
    """Every ${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh basename referenced
    anywhere in hooks.json's command strings."""
    hooks_json = json.loads((HOOKS_DIR / "hooks.json").read_text())

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
        elif isinstance(node, str):
            yield node

    names = set()
    for s in walk(hooks_json):
        # findall, not search: since issue #2093 every registration is
        # `fail-open-wrapper.sh <real-hook.sh> [args]`, so a first-match-only
        # scan would check the wrapper's exec bit 58 times and the wrapped
        # scripts' never.
        for name in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/hooks/([\w.-]+\.sh)", s):
            names.add(name)
    assert names, "no ${CLAUDE_PLUGIN_ROOT}/hooks/*.sh commands found in hooks.json"
    return sorted(names)


def _assert_wired_scripts_executable(hooks_dir):
    """Raises AssertionError naming every hooks.json-wired script under
    hooks_dir that is missing the exec bit."""
    non_exec = [
        name for name in _wired_hook_scripts()
        if not os.access(hooks_dir / name, os.X_OK)
    ]
    assert not non_exec, (
        "hooks.json-wired script(s) committed without exec bit "
        "(100644, dies with 'Permission denied' on invocation): "
        + ", ".join(non_exec)
    )


def t_all_wired_hook_scripts_are_executable():
    _assert_wired_scripts_executable(HOOKS_DIR)


def t_seeded_non_exec_wired_script_is_refused(tmp_path):
    """Live-fire proof the assertion actually catches the failure mode,
    not just passing trivially against an already-fixed tree: seed a
    copy of the hooks dir with one wired script stripped of its exec
    bit and confirm the regression check refuses it."""
    seeded = tmp_path / "hooks"
    shutil.copytree(HOOKS_DIR, seeded)
    # stop-gate.sh: still a direct hooks.json registration after #2146
    # collapsed the PreToolUse rows into the dispatcher (record-claim-
    # guard.sh, the previous target, is now dispatcher-sourced, so its
    # exec bit no longer decides whether it runs).
    target = seeded / "stop-gate.sh"
    target.chmod(target.stat().st_mode & ~0o111)
    assert not os.access(target, os.X_OK)

    try:
        _assert_wired_scripts_executable(seeded)
    except AssertionError as e:
        assert "stop-gate.sh" in str(e)
    else:
        raise AssertionError("expected the seeded non-exec script to be refused")
