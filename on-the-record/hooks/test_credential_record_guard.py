"""Tests for credential-record-guard.sh (issue #858)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "credential-record-guard.sh"

import sys
sys.path.insert(0, str(HOOKS_DIR))
from credential_example_allowlist import (
    AWS_EXAMPLE_ACCESS_KEY_ID,
    GITHUB_EXAMPLE_CLASSIC_PAT,
)


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


def t_non_docs_path_is_ignored(tmp_path):
    r = _run({"file_path": str(tmp_path / "src" / "foo.py"),
              "content": "token: ghp_" + "a" * 40})
    assert r.returncode == 0


def t_full_gho_token_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "token: gho_" + "A" * 40})
    assert r.returncode == 2
    assert "credential" in r.stderr


def t_full_ghp_token_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "token: ghp_" + "b" * 40})
    assert r.returncode == 2


def t_full_ghs_token_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "token: ghs_" + "c" * 40})
    assert r.returncode == 2


def t_full_ghr_token_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "token: ghr_" + "d" * 40})
    assert r.returncode == 2


def t_full_github_pat_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "token: github_pat_" + "e" * 30})
    assert r.returncode == 2


def t_full_openai_style_key_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "key: sk-" + "f" * 25})
    assert r.returncode == 2


def t_full_aws_key_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "key: AKIA" + "G" * 16})
    assert r.returncode == 2


def t_redacted_marker_is_allowed(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "token: gho_" + "A" * 40 + "[REDACTED]"})
    # the marker replaces the secret body in real usage; simulate by
    # putting [REDACTED] immediately after a short prefix instead.
    r2 = _run({"file_path": str(p), "content": "token: gho_A5ji[REDACTED]"})
    assert r2.returncode == 0


def t_short_truncated_prefix_is_allowed(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "token: gho_A5ji..., truncated"})
    assert r.returncode == 0


def t_ordinary_prose_is_untouched(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "This record discusses gh auth tokens in general "
                         "without including any actual secret value."})
    assert r.returncode == 0


def t_multiedit_split_credential_is_denied(tmp_path):
    p = _record_path(tmp_path)
    token = "ghp_" + "z" * 40
    half = len(token) // 2
    r = _run({
        "file_path": str(p),
        "edits": [
            {"old_string": "a", "new_string": "prefix " + token[:half]},
            {"old_string": "b", "new_string": token[half:] + " suffix"},
        ],
    }, tool_name="MultiEdit")
    assert r.returncode == 2


def t_canonical_aws_example_key_is_allowed(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "example key: " + AWS_EXAMPLE_ACCESS_KEY_ID})
    assert r.returncode == 0


def t_canonical_github_example_pat_is_allowed(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "example token: " + GITHUB_EXAMPLE_CLASSIC_PAT})
    assert r.returncode == 0


def t_novel_akia_shaped_string_still_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "key: AKIA" + "H" * 16})
    assert r.returncode == 2


def t_multiedit_independent_short_fragments_allowed(tmp_path):
    p = _record_path(tmp_path)
    r = _run({
        "file_path": str(p),
        "edits": [
            {"old_string": "a", "new_string": "some prose here"},
            {"old_string": "b", "new_string": "more prose there"},
        ],
    }, tool_name="MultiEdit")
    assert r.returncode == 0
