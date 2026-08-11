"""Tests for live-fire-test-guard.sh (issue #914 step 2, mechanism b).
Drives the CALLER (the hook process, via a real git repo fixture), not
the guard's derivation logic directly -- same convention
test_gate_registration_guard.py uses to drive gate-registration-guard.sh.
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "live-fire-test-guard.sh"

BOUNDARY_HEADER = "| mechanism | verdict | reason |\n|---|---|---|\n"

LIVE_FIRE_SH_TEST = '''"""fixture live-fire test."""
import json, os, subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "new-guard.sh"


def _run(payload):
    return subprocess.run(
        ["bash", str(SCRIPT)], input=json.dumps(payload),
        capture_output=True, text=True, timeout=20,
    )


def t_allow():
    r = _run({"tool_name": "Bash", "tool_input": {"command": "echo hi"}})
    assert r.returncode == 0


def t_deny():
    r = _run({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})
    assert r.returncode == 2
'''

NON_LIVE_FIRE_SH_TEST = '''"""fixture non-live-fire test -- only imports/checks the file exists."""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "new-guard.sh"


def t_exists():
    assert SCRIPT.exists()
'''

LIVE_FIRE_GATE_TEST = '''"""fixture live-fire test for a gates/*.py module."""
import new_gate


def t_allow():
    assert new_gate.check({"ok": True}) is True


def t_deny():
    assert new_gate.check({"ok": False}) is False
'''

NON_LIVE_FIRE_GATE_TEST = '''"""fixture non-live-fire test -- import only."""
import new_gate


def t_imports():
    assert new_gate is not None
'''


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "gates").mkdir()
    (repo / "on-the-record" / "hooks").mkdir(parents=True)
    (repo / "docs" / "specs").mkdir(parents=True)
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER, encoding="utf-8")
    return repo


def _stage_all(repo):
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)


def _run(repo, command="git commit -m test"):
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": command},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=repo,
    )


def t_new_hook_script_with_no_test_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new-guard.sh" in r.stderr
    assert "no live-fire test staged" in r.stderr


def t_new_hook_script_with_non_live_fire_test_denies_commit(tmp_path):
    """#909's orphan shape: a test file exists, but it never pipes a
    crafted payload into the script as a real lifecycle event."""
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "on-the-record" / "hooks" / "test_new_guard.py").write_text(
        NON_LIVE_FIRE_SH_TEST, encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new-guard.sh" in r.stderr
    assert "does not live-fire it" in r.stderr


def t_new_hook_script_with_passing_live_fire_test_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\n"
        "payload=\"$(cat)\"\n"
        "case \"$payload\" in *'git commit'*) exit 2;; esac\n"
        "exit 0\n",
        encoding="utf-8")
    (repo / "on-the-record" / "hooks" / "test_new_guard.py").write_text(
        LIVE_FIRE_SH_TEST, encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-guard.sh` | contract | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    # the fixture's own live-fire test must actually pass against the
    # fixture script, proving this is a real assertion, not decoration.
    pr = subprocess.run(
        ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "-o", "python_functions=test_* t_*",
         str(repo / "on-the-record" / "hooks" / "test_new_guard.py")],
        capture_output=True, text=True, timeout=30,
    )
    assert pr.returncode == 0, pr.stdout + pr.stderr


def t_live_fire_n_a_trailer_exempts_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-lib.sh").write_text(
        "#!/usr/bin/env bash\ntrue\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new-lib.sh` | contract | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(
        repo,
        command=(
            "git commit -m \"$(cat <<'EOF'\n"
            "add new-lib.sh\n\n"
            "Live-fire-N/A: sourced library, no lifecycle-event surface\n"
            "EOF\n)\""
        ),
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def t_unregistered_hook_script_left_to_gate_registration_guard(tmp_path):
    """No enforcement-boundary.md row at all -- gate-registration-guard.sh's
    business, not this guard's; must not double-deny the same condition."""
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "hooks" / "new-guard.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr


def t_new_gate_module_with_no_test_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text(
        "def check(e):\n    return bool(e.get('ok'))\n", encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new_gate.py" in r.stderr
    assert "no live-fire test staged" in r.stderr


def t_new_gate_module_with_import_only_test_denies_commit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text(
        "def check(e):\n    return bool(e.get('ok'))\n", encoding="utf-8")
    (repo / "gates" / "test_new_gate.py").write_text(
        NON_LIVE_FIRE_GATE_TEST, encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 2, r.stdout
    assert "new_gate.py" in r.stderr
    assert "does not live-fire it" in r.stderr


def t_new_gate_module_with_live_fire_test_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "gates" / "new_gate.py").write_text(
        "def check(e):\n    return bool(e.get('ok'))\n", encoding="utf-8")
    (repo / "gates" / "test_new_gate.py").write_text(
        LIVE_FIRE_GATE_TEST, encoding="utf-8")
    (repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
        BOUNDARY_HEADER + "| `new_gate.py` | repo-local | test fixture |\n",
        encoding="utf-8")
    _stage_all(repo)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
