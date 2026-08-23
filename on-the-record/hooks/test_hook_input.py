#!/usr/bin/env python3
"""issue #2093 — the shared parser is total: it returns, it never raises.

Acceptance check 2: tilde expansion, heredoc, malformed JSON all return typed
results, never raise.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hook_input import (  # noqa: E402
    CdTarget,
    NoCdTarget,
    OpaqueCommand,
    Payload,
    Unparseable,
    cd_target,
    parse_payload,
    resolved_cwd,
    tool_command,
)


# --- parse_payload ---------------------------------------------------------

def test_parse_payload_accepts_a_well_formed_payload():
    p = parse_payload('{"tool_name": "Bash", "tool_input": {"command": "ls"}}')
    assert isinstance(p, Payload)
    assert p.tool_name == "Bash"
    assert tool_command(p) == "ls"


@pytest.mark.parametrize(
    "raw,reason",
    [
        ("{", "malformed-json"),
        ("not json at all", "malformed-json"),
        ('{"a": }', "malformed-json"),
        ("", "empty-input"),
        ("   \n ", "empty-input"),
        (None, "none-input"),
        ("[1, 2, 3]", "non-dict-payload"),
        ('"a string"', "non-dict-payload"),
        (object(), "non-text-input"),
    ],
)
def test_parse_payload_returns_typed_failure_never_raises(raw, reason):
    result = parse_payload(raw)
    assert isinstance(result, Unparseable)
    assert result.reason == reason


def test_parse_payload_handles_bytes_and_unicode():
    p = parse_payload('{"tool_input": {"command": "echo 日本語 🎉"}}'.encode("utf-8"))
    assert isinstance(p, Payload)
    assert "🎉" in tool_command(p)


def test_parse_payload_tolerates_a_100kb_input():
    blob = '{"tool_input": {"command": "%s"}}' % ("x" * 100_000)
    p = parse_payload(blob)
    assert isinstance(p, Payload)
    assert len(tool_command(p)) == 100_000


def test_tool_command_is_total_over_missing_fields():
    assert tool_command(parse_payload("{}")) == ""
    assert tool_command(parse_payload('{"tool_input": null}')) == ""
    assert tool_command(parse_payload('{"tool_input": []}')) == ""
    assert tool_command(parse_payload('{"tool_input": {"command": 7}}')) == ""
    assert tool_command(parse_payload("{")) == ""
    assert tool_command(None) == ""
    assert tool_command({"tool_input": {"command": "ok"}}) == "ok"


# --- cd_target -------------------------------------------------------------

def test_cd_target_expands_an_unexpanded_tilde():
    """The #2092 instance: `~` must not survive into a filesystem call."""
    result = cd_target("cd ~/work/repo && git commit -m x")
    assert isinstance(result, CdTarget)
    assert not result.path.startswith("~")
    assert result.path == os.path.expanduser("~/work/repo")


def test_cd_target_expands_a_quoted_tilde():
    result = cd_target('cd "~/work/repo" && gh pr create')
    assert isinstance(result, CdTarget)
    assert result.path == os.path.expanduser("~/work/repo")


def test_cd_target_returns_a_plain_absolute_path_unchanged():
    assert cd_target("cd /tmp/x && ls") == CdTarget("/tmp/x")


def test_cd_target_reports_a_heredoc_as_typed_opaque():
    cmd = 'cat <<EOF\ncd /not/a/real/target && rm -rf /\nEOF'
    result = cd_target(cmd)
    assert isinstance(result, OpaqueCommand)
    assert result.reason == "heredoc"


def test_cd_target_reports_unbalanced_quotes_without_raising_valueerror():
    result = cd_target("cd /tmp && echo 'unterminated")
    assert isinstance(result, OpaqueCommand)
    assert result.reason == "unbalanced-quotes"


def test_cd_target_reports_a_100kb_command_as_oversize():
    result = cd_target("cd /tmp && echo " + "y" * 100_000)
    assert isinstance(result, OpaqueCommand)
    assert result.reason == "oversize-command"


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit -m x",
        "echo 'nested \"quotes\" here'",
        "echo 日本語 && cd /tmp",  # a `cd` that is not the leading prefix
    ],
)
def test_cd_target_reports_no_prefix_for_well_formed_commands(cmd):
    assert isinstance(cd_target(cmd), NoCdTarget)


def test_cd_target_is_total_over_non_string_input():
    assert isinstance(cd_target(None), OpaqueCommand)
    assert isinstance(cd_target(object()), OpaqueCommand)
    assert isinstance(cd_target(b"cd /tmp && ls"), CdTarget)
    assert isinstance(cd_target(""), NoCdTarget)


# --- resolved_cwd ----------------------------------------------------------

def test_resolved_cwd_prefers_the_cd_target_then_falls_back():
    assert resolved_cwd("cd /tmp/x && ls") == "/tmp/x"
    assert resolved_cwd("git commit -m x", default="/fallback") == "/fallback"
    assert resolved_cwd("cat <<EOF\nx\nEOF", default="/fallback") == "/fallback"
    assert resolved_cwd("ls") == os.getcwd()


# --- the module-wide totality property ------------------------------------

HOSTILE_INPUTS = [
    None,
    "",
    "{",
    "[]",
    bytes([0xff, 0xfe, 0x00]) + b"binary",
    "cd ~ && ls",
    "cat <<'EOF'\nbody\nEOF",
    "echo 'unbalanced",
    "x" * 100_000,
    "unicode \U0001F389 " + chr(0) + "trailing backslash \\",
    object(),
    12345,
    {"not": "a string"},
]


@pytest.mark.parametrize("raw", HOSTILE_INPUTS)
def test_no_entry_point_raises_on_any_input(raw):
    """The single property the whole library exists to guarantee."""
    parse_payload(raw)
    tool_command(raw)
    cd_target(raw)
    resolved_cwd(raw, default="/tmp")
