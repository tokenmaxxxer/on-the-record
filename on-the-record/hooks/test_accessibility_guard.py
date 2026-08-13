"""Tests for accessibility-guard.sh (issue #1130, row 1)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "accessibility-guard.sh"


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


def t_non_markup_path_is_ignored(tmp_path):
    r = _run({"file_path": str(tmp_path / "foo.py"), "content": "<img src=x>"})
    assert r.returncode == 0


def t_seeded_violation_img_with_no_alt_is_denied(tmp_path):
    r = _run({
        "file_path": str(tmp_path / "widget.tsx"),
        "content": "export const W = () => <img src=\"logo.png\" />;",
    })
    assert r.returncode == 2
    assert "alt" in r.stderr


def t_img_with_alt_passes(tmp_path):
    r = _run({
        "file_path": str(tmp_path / "widget.tsx"),
        "content": "export const W = () => <img src=\"logo.png\" alt=\"logo\" />;",
    })
    assert r.returncode == 0


def t_button_with_no_text_and_no_label_is_denied(tmp_path):
    r = _run({
        "file_path": str(tmp_path / "widget.html"),
        "content": "<button onclick=\"go()\"></button>",
    })
    assert r.returncode == 2
    assert "accessible name" in r.stderr


def t_button_with_text_passes(tmp_path):
    r = _run({
        "file_path": str(tmp_path / "widget.html"),
        "content": "<button onclick=\"go()\">Submit</button>",
    })
    assert r.returncode == 0


def t_orchestrate_off_disables_guard(tmp_path):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": str(tmp_path / "widget.html"), "content": "<img src=x>"},
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(GUARD)], input=payload, capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
