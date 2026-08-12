"""Tests for design-rationale-guard.sh (issue #960: first domain-cluster
gate off the 43-role invariant coverage matrix, row 18/43)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "design-rationale-guard.sh"


def _run(tool_input, tool_name="Write", cwd=None):
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": str(cwd) if cwd else os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def t_non_command_path_is_ignored(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run({"file_path": str(repo / "foo.md"), "content": "no frontmatter here"}, cwd=repo)
    assert r.returncode == 0


def t_seeded_violation_write_with_no_rationale_is_denied(tmp_path):
    # Seeded violation: a new command file with the existing
    # description:/argument-hint: fields but no design-rationale: field.
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "commands").mkdir(parents=True)
    r = _run({
        "file_path": str(repo / "on-the-record" / "commands" / "new.md"),
        "content": "---\ndescription: does a thing\nargument-hint: \"<x>\"\n---\n\nbody\n",
    }, cwd=repo)
    assert r.returncode == 2
    assert "design-rationale" in r.stderr


def t_write_with_rationale_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "commands").mkdir(parents=True)
    r = _run({
        "file_path": str(repo / "on-the-record" / "commands" / "new.md"),
        "content": (
            "---\ndescription: does a thing\nargument-hint: \"<x>\"\n"
            "design-rationale: keeps the surface single-purpose per issue #960\n"
            "---\n\nbody\n"
        ),
    }, cwd=repo)
    assert r.returncode == 0


def t_blank_rationale_value_is_denied(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "commands").mkdir(parents=True)
    r = _run({
        "file_path": str(repo / "on-the-record" / "commands" / "new.md"),
        "content": "---\ndescription: x\ndesign-rationale:   \n---\n\nbody\n",
    }, cwd=repo)
    assert r.returncode == 2


def t_edit_reconstructs_full_file_and_denies_when_rationale_removed(tmp_path):
    repo = _init_repo(tmp_path)
    cmds = repo / "on-the-record" / "commands"
    cmds.mkdir(parents=True)
    f = cmds / "run.md"
    f.write_text(
        "---\ndescription: x\ndesign-rationale: because reasons, issue #960\n---\n\nbody\n"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "seed"], check=True)

    r = _run({
        "file_path": str(f),
        "old_string": "design-rationale: because reasons, issue #960\n",
        "new_string": "",
    }, tool_name="Edit", cwd=repo)
    assert r.returncode == 2
    assert "design-rationale" in r.stderr


def t_edit_that_keeps_rationale_passes(tmp_path):
    repo = _init_repo(tmp_path)
    cmds = repo / "on-the-record" / "commands"
    cmds.mkdir(parents=True)
    f = cmds / "run.md"
    f.write_text(
        "---\ndescription: x\ndesign-rationale: because reasons, issue #960\n---\n\nold body\n"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "seed"], check=True)

    r = _run({
        "file_path": str(f),
        "old_string": "old body",
        "new_string": "new body",
    }, tool_name="Edit", cwd=repo)
    assert r.returncode == 0


def t_orchestrate_off_disables_guard(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "on-the-record" / "commands").mkdir(parents=True)
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(repo / "on-the-record" / "commands" / "new.md"),
            "content": "---\ndescription: x\n---\n\nbody\n",
        },
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(GUARD)], input=payload, capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
