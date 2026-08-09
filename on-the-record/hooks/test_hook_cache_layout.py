"""Tests for issue #556: gate cache-layout resolution and ownership-check
order in role-spec-reference-guard.sh and record-claim-guard.sh.

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
import shutil
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ON_THE_RECORD = HOOKS_DIR.parent

RSRG_OWNED_PATH = "docs/issue-999/reports/security-threat-model.md"
RSRG_OWNED_CONTENT = "See `src/real.py` for details.\n"
RCG_OWNED_PATH = "docs/issue-999/reports/implementation.md"
RCG_OWNED_CONTENT = "unverifiable:\n"


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

def t_rsrg_resolves_from_cache_layout(tmp_path):
    cache = _make_cache_dir(tmp_path)
    p = tmp_path / RSRG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "role-spec-reference-guard.sh",
              {"file_path": str(p), "content": RSRG_OWNED_CONTENT}, cache.parent)
    assert "ModuleNotFoundError" not in r.stderr
    assert r.returncode in (0, 2)


def t_rcg_resolves_from_cache_layout(tmp_path):
    cache = _make_cache_dir(tmp_path)
    p = tmp_path / RCG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(p), "content": RCG_OWNED_CONTENT}, cache.parent)
    assert "ModuleNotFoundError" not in r.stderr
    assert r.returncode in (0, 2)


# --- check 2: ownership check precedes import; outside-surface passes ---

def t_rsrg_ownership_check_precedes_import(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    outside = tmp_path / "outside" / "note.md"
    outside.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "role-spec-reference-guard.sh",
              {"file_path": str(outside), "content": "irrelevant content"}, cache.parent)
    assert r.returncode == 0, r.stderr


def t_rcg_ownership_check_precedes_import(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    outside = tmp_path / "outside" / "note.md"
    outside.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(outside), "content": "5 of 9 items, no derivation"}, cache.parent)
    assert r.returncode == 0, r.stderr


# --- check 3: fail-closed preserved for owned paths ---

def t_rsrg_fail_closed_for_owned_path(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    p = tmp_path / RSRG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "role-spec-reference-guard.sh",
              {"file_path": str(p), "content": RSRG_OWNED_CONTENT}, cache.parent)
    assert r.returncode == 2, r.stderr


def t_rcg_fail_closed_for_owned_path(tmp_path):
    cache = _make_broken_gates_cache(tmp_path)
    p = tmp_path / RCG_OWNED_PATH
    p.parent.mkdir(parents=True)
    r = _run(cache / "hooks" / "record-claim-guard.sh",
              {"file_path": str(p), "content": RCG_OWNED_CONTENT}, cache.parent)
    assert r.returncode == 2, r.stderr
