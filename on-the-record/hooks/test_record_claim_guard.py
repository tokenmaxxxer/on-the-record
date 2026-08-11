"""Tests for record-claim-guard.sh (issue #457 Group A+B porting)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "record-claim-guard.sh"


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


def _record_path(tmp_path):
    p = tmp_path / "docs" / "issue-999" / "reports" / "implementation.md"
    p.parent.mkdir(parents=True)
    return p


def t_non_record_path_is_ignored(tmp_path):
    r = _run({"file_path": str(tmp_path / "src" / "foo.py"),
              "content": "count: 5 of 10 items with no derivation"})
    assert r.returncode == 0


def t_unverifiable_without_reason_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "unverifiable:\n"})
    assert r.returncode == 2
    assert "issue #310" in r.stderr


def t_unverifiable_with_reason_passes(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "unverifiable: this is a subjective UX judgment.\n"})
    assert r.returncode == 0


def t_checked_unverifiable_without_reason_is_denied(tmp_path):
    p = _record_path(tmp_path)
    line = "- did the thing — checked: test/foo.py::t_x — result: unverifiable\n"
    r = _run({"file_path": str(p), "content": line})
    assert r.returncode == 2
    assert "issue #331" in r.stderr


def t_bare_count_claim_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "25 of 107 works are done.\n"})
    assert r.returncode == 2
    assert "issue #333" in r.stderr


def t_derived_count_claim_passes(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "25 of 107 `derived: pytest -q` works are done.\n"})
    assert r.returncode == 0


def t_count_inside_fence_is_ignored(tmp_path):
    p = _record_path(tmp_path)
    content = "```\n25 of 107 passed\n```\n"
    r = _run({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_bare_test_count_claim_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "We ran 38 tests passing with no failures.\n"})
    assert r.returncode == 2
    assert "issue #333" in r.stderr


def t_orphaned_path_reference_is_denied(tmp_path):
    (tmp_path / ".git").mkdir()
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "See `src/does_not_exist.py` for details.\n"},
             cwd=tmp_path)
    assert r.returncode == 2
    assert "issue #330" in r.stderr


def t_existing_path_reference_passes(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n")
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "See `src/real.py` for details.\n"},
             cwd=tmp_path)
    assert r.returncode == 0


def t_state_claim_without_canonical_tag_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "The verify role found the defect in the parser.\n"})
    assert r.returncode == 2
    assert "issue #793" in r.stderr


def t_state_claim_with_canonical_tag_passes(tmp_path):
    p = _record_path(tmp_path)
    content = ("canonical: src/parser.py:42-58\n"
               "The verify role found the defect in the parser.\n")
    r = _run({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_malformed_payload_is_allowed_not_denied(tmp_path):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    r = subprocess.run(["bash", str(GUARD)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0


def t_edit_tool_uses_new_string(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "old_string": "x", "new_string": "5 of 9 tests"},
             tool_name="Edit")
    assert r.returncode == 2
    assert "issue #333" in r.stderr


# --- record-claim-shape-directive.sh (issue #730) -------------------------

DIRECTIVE = HOOKS_DIR / "record-claim-shape-directive.sh"


def _run_directive(claude_role="implementation"):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if claude_role is None:
        env.pop("CLAUDE_ROLE", None)
    else:
        env["CLAUDE_ROLE"] = claude_role
    return subprocess.run(
        ["bash", str(DIRECTIVE)],
        input="", capture_output=True, text=True, env=env, timeout=20,
    )


def t_directive_names_all_four_record_lint_rules():
    r = _run_directive(claude_role="implementation")
    assert r.returncode == 0
    out = r.stdout
    assert "<record-claim-citation-directive>" in out
    # count-needs-citation (#333: bare count/ratio needs a code fence or
    # a `derived:` tag)
    assert "derived:" in out and "#333" in out
    # unverifiable-needs-reason (#310 and the #331 checked-claim variant)
    assert "unverifiable:" in out and "#310" in out
    assert "#331" in out
    # path-must-resolve (#330: a backtick-quoted path must resolve)
    assert "#330" in out
    # canonical-source-required (#793: a state/defect claim needs a
    # `canonical:` tag naming the source actually read)
    assert "canonical:" in out and "#793" in out


def t_directive_is_silent_without_claude_role():
    r = _run_directive(claude_role=None)
    assert r.returncode == 0
    assert r.stdout == ""


def t_directive_fails_open_without_orchestrate_off_flag_set_wrong():
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = "1"
    env["CLAUDE_ROLE"] = "implementation"
    r = subprocess.run(["bash", str(DIRECTIVE)], input="", capture_output=True,
                        text=True, env=env, timeout=20)
    assert r.returncode == 0
    assert r.stdout == ""


def t_directive_shows_visible_notice_on_renamed_check_function(tmp_path):
    # before-landing hunt (issue #730, stance 0): a rename of a
    # record_lint check attribute must not silently produce the same
    # empty output as the intentional no-op paths.
    import shutil

    gates_src = HOOKS_DIR.parent / "gates"
    tmp_gates = tmp_path / "gates"
    shutil.copytree(gates_src, tmp_gates)
    lint_path = tmp_gates / "record_lint.py"
    text = lint_path.read_text()
    lint_path.write_text(
        text.replace("def bare_count_claim_check", "def bare_count_claim_check_renamed", 1))

    tmp_hooks = tmp_path / "hooks"
    tmp_hooks.mkdir()
    shutil.copy(DIRECTIVE, tmp_hooks / DIRECTIVE.name)

    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["CLAUDE_ROLE"] = "implementation"
    r = subprocess.run(["bash", str(tmp_hooks / DIRECTIVE.name)], input="",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
    assert "<record-claim-citation-directive>" in r.stdout
    assert "could not generate" in r.stdout
