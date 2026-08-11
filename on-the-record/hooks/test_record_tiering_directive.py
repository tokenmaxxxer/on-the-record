"""Tests for record-tiering-guard.sh + record-tiering-directive.sh (issue #760)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "record-tiering-guard.sh"
DIRECTIVE = HOOKS_DIR / "record-tiering-directive.sh"


def _run_guard(tool_input, tool_name="Write", cwd=None):
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


def _record_path(tmp_path):
    p = tmp_path / "docs" / "issue-999" / "reports" / "implementation.md"
    p.parent.mkdir(parents=True)
    return p


# --- record-tiering-guard.sh -----------------------------------------------

def t_padded_none_body_is_denied(tmp_path):
    p = _record_path(tmp_path)
    content = (
        "## What did not work\n\n"
        "None — no attempted approach was written then undone during "
        "this build; nothing failed.\n"
    )
    r = _run_guard({"file_path": str(p), "content": content})
    assert r.returncode == 2
    assert "issue #760" in r.stderr


def t_bare_none_with_period_passes(tmp_path):
    p = _record_path(tmp_path)
    content = "## What did not work\n\nNone.\n"
    r = _run_guard({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_bare_none_without_period_passes(tmp_path):
    p = _record_path(tmp_path)
    content = "## What did not work\n\nNone\n"
    r = _run_guard({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_real_content_of_any_length_passes(tmp_path):
    p = _record_path(tmp_path)
    body = "A finding was written up. " * 80  # long, real, non-"none" content
    content = f"## What did not work\n\n{body}\n"
    r = _run_guard({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_non_record_path_is_ignored(tmp_path):
    r = _run_guard({
        "file_path": str(tmp_path / "src" / "foo.py"),
        "content": "## What did not work\n\nNone padded out further.\n",
    })
    assert r.returncode == 0


def t_non_implementation_report_is_ignored(tmp_path):
    p = tmp_path / "docs" / "issue-999" / "reports" / "conformance-review.md"
    p.parent.mkdir(parents=True)
    r = _run_guard({
        "file_path": str(p),
        "content": "## What did not work\n\nNone padded out further.\n",
    })
    assert r.returncode == 0


def t_fragment_without_section_heading_is_ignored(tmp_path):
    p = _record_path(tmp_path)
    r = _run_guard({"file_path": str(p), "content": "## Some other section\n\nNone padded here.\n"})
    assert r.returncode == 0


def t_edit_tool_uses_new_string(tmp_path):
    p = _record_path(tmp_path)
    r = _run_guard(
        {"file_path": str(p), "old_string": "x",
         "new_string": "## What did not work\n\nNone but with extra words.\n"},
        tool_name="Edit",
    )
    assert r.returncode == 2
    assert "issue #760" in r.stderr


def t_split_edit_heading_then_padded_body_is_still_denied(tmp_path):
    # before-landing hunt (issue #760, stance 0): a fragment-only check
    # is bypassable by splitting the section heading and the padded
    # "None ..." body across two separate Edit calls, since each
    # PreToolUse invocation only sees its own call's fragment. The guard
    # must reconstruct the full resulting file (read current content +
    # apply the edit) instead of checking only the changed fragment.
    p = _record_path(tmp_path)
    p.write_text("# Report\n\nsome other content\n")

    r1 = _run_guard({
        "file_path": str(p),
        "old_string": "# Report\n\nsome other content\n",
        "new_string": "# Report\n\nsome other content\n\n## What did not work\n\nPLACEHOLDER\n",
    }, tool_name="Edit")
    assert r1.returncode == 0
    p.write_text("# Report\n\nsome other content\n\n## What did not work\n\nPLACEHOLDER\n")

    r2 = _run_guard({
        "file_path": str(p),
        "old_string": "PLACEHOLDER",
        "new_string": "None — actually the citation extraction failed silently and nobody noticed.",
    }, tool_name="Edit")
    assert r2.returncode == 2
    assert "issue #760" in r2.stderr


def t_edit_falls_back_to_fragment_when_file_unreadable(tmp_path):
    p = _record_path(tmp_path)  # file does not exist on disk
    r = _run_guard(
        {"file_path": str(p), "old_string": "x",
         "new_string": "## What did not work\n\nNone but padded further.\n"},
        tool_name="Edit",
    )
    assert r.returncode == 2
    assert "issue #760" in r.stderr


def t_malformed_payload_is_allowed_not_denied(tmp_path):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    r = subprocess.run(["bash", str(GUARD)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0


# --- record-tiering-directive.sh --------------------------------------------

def _run_directive(claude_role="implementation", orchestrate_off=""):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    if claude_role is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = claude_role
    return subprocess.run(
        ["bash", str(DIRECTIVE)],
        input="", capture_output=True, text=True, env=env, timeout=20,
    )


def t_directive_states_bare_marker_rule_and_real_content_exception():
    r = _run_directive(claude_role="implementation")
    assert r.returncode == 0
    out = r.stdout
    assert "<record-tiering-directive>" in out
    assert "None." in out
    assert "real entry" in out


def t_directive_is_silent_without_claude_role():
    r = _run_directive(claude_role=None)
    assert r.returncode == 0
    assert r.stdout == ""


def t_directive_fails_open_when_orchestrate_off_set():
    r = _run_directive(claude_role="implementation", orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""
