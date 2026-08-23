#!/usr/bin/env python3
"""issue #2093 — a hook that fails open leaves a visible ledger line.

Acceptance check 3: a deliberately-broken stub hook run through
`fail-open-wrapper.sh` records a fail-open ledger line.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys

import pytest

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HOOKS_DIR)

from hook_ledger import input_digest, ledger_path, record_fail_open  # noqa: E402

WRAPPER = os.path.join(HOOKS_DIR, "fail-open-wrapper.sh")


def _stub(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def _run(hook, ledger, payload='{"tool_name": "Bash"}', args=()):
    env = dict(os.environ)
    env["OTR_FAIL_OPEN_LEDGER"] = str(ledger)
    return subprocess.run(
        ["bash", WRAPPER, hook, *args],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def _lines(ledger):
    if not os.path.exists(ledger):
        return []
    with open(ledger, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --- the ledger module itself ---------------------------------------------

def test_ledger_path_honours_the_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("OTR_FAIL_OPEN_LEDGER", str(tmp_path / "l.jsonl"))
    assert ledger_path() == str(tmp_path / "l.jsonl")


def test_ledger_path_defaults_under_the_home_claude_dir(monkeypatch):
    monkeypatch.delenv("OTR_FAIL_OPEN_LEDGER", raising=False)
    assert ledger_path().endswith(
        os.path.join(".claude", "on-the-record", "fail-open.jsonl")
    )
    assert "~" not in ledger_path()


def test_record_fail_open_appends_one_json_line(tmp_path, monkeypatch):
    ledger = tmp_path / "deep" / "l.jsonl"
    monkeypatch.setenv("OTR_FAIL_OPEN_LEDGER", str(ledger))
    assert record_fail_open("x.sh", ["x.sh", "pre"], "sha256:abc", 1, "nonzero-exit")
    assert record_fail_open("y.sh", [], "sha256:def", 127, "traceback")
    lines = _lines(str(ledger))
    assert [line["hook"] for line in lines] == ["x.sh", "y.sh"]
    assert lines[0]["exit_code"] == 1 and lines[0]["reason"] == "nonzero-exit"


def test_record_fail_open_never_raises_on_an_unwritable_ledger(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv("OTR_FAIL_OPEN_LEDGER", str(blocker / "sub" / "l.jsonl"))
    assert record_fail_open("x.sh", [], "", 1, "nonzero-exit") is False


def test_input_digest_is_stable_and_not_the_input_itself():
    d = input_digest('{"secret": "hunter2"}')
    assert d == input_digest('{"secret": "hunter2"}')
    assert "hunter2" not in d
    assert d.startswith("sha256:")
    assert input_digest(None) != input_digest("x")


# --- the wrapper, end to end ----------------------------------------------

def test_broken_stub_hook_through_the_wrapper_records_a_fail_open(tmp_path):
    """The acceptance case: a hook that crashes leaves exactly one line."""
    ledger = tmp_path / "l.jsonl"
    hook = _stub(
        tmp_path,
        "broken-guard.sh",
        "#!/usr/bin/env bash\npython3 -c 'raise RuntimeError(\"boom\")'\n",
    )
    r = _run(hook, ledger)

    assert r.returncode not in (0, 2), "the broken stub must actually fail open"
    assert "Traceback (most recent call last)" in r.stderr, "child stderr is re-emitted"
    lines = _lines(str(ledger))
    assert len(lines) == 1
    assert lines[0]["hook"] == "broken-guard.sh"
    assert lines[0]["event"] == "fail-open"
    assert lines[0]["exit_code"] == r.returncode
    assert lines[0]["reason"] in ("nonzero-exit", "traceback")
    assert lines[0]["digest"].startswith("sha256:")


def test_wrapper_records_argv_so_the_registration_is_identifiable(tmp_path):
    ledger = tmp_path / "l.jsonl"
    hook = _stub(tmp_path, "broken.sh", "#!/usr/bin/env bash\nexit 3\n")
    _run(hook, ledger, args=("pre",))
    line = _lines(str(ledger))[0]
    assert line["argv"][-1] == "pre"
    assert line["argv"][0].endswith("broken.sh")


@pytest.mark.parametrize("code", [0, 2])
def test_wrapper_writes_no_line_for_a_verdict_exit(tmp_path, code):
    """0 = allow, 2 = block. Neither is a fail-open."""
    ledger = tmp_path / "l.jsonl"
    hook = _stub(tmp_path, "ok.sh", "#!/usr/bin/env bash\nexit %d\n" % code)
    r = _run(hook, ledger)
    assert r.returncode == code
    assert _lines(str(ledger)) == []


def test_wrapper_forwards_exit_code_stdout_stderr_and_stdin(tmp_path):
    """Verdict-neutrality: the wrapper is transparent to a healthy hook."""
    ledger = tmp_path / "l.jsonl"
    hook = _stub(
        tmp_path,
        "echo.sh",
        "#!/usr/bin/env bash\npayload=\"$(cat)\"\n"
        'printf "OUT:%s" "$payload"\nprintf "ERR:%s" "$1" >&2\nexit 2\n',
    )
    r = _run(hook, ledger, payload='{"tool_name":"Bash"}', args=("argone",))
    assert r.returncode == 2
    assert r.stdout == 'OUT:{"tool_name":"Bash"}'
    assert r.stderr == "ERR:argone"
    assert _lines(str(ledger)) == []


def test_wrapper_records_a_missing_hook_script(tmp_path):
    ledger = tmp_path / "l.jsonl"
    r = _run(str(tmp_path / "does-not-exist.sh"), ledger)
    assert r.returncode not in (0, 2)
    assert _lines(str(ledger))[0]["hook"] == "does-not-exist.sh"


def test_wrapper_records_a_traceback_even_when_the_hook_exits_zero(tmp_path):
    """A crashed subprocess inside an exit-0 hook is still a silent skip."""
    ledger = tmp_path / "l.jsonl"
    hook = _stub(
        tmp_path,
        "swallowing.sh",
        "#!/usr/bin/env bash\npython3 -c 'raise RuntimeError(\"boom\")' || true\nexit 0\n",
    )
    r = _run(hook, ledger)
    assert r.returncode == 0
    assert _lines(str(ledger))[0]["reason"] == "traceback"


def test_wrapper_survives_an_unwritable_ledger_without_changing_the_verdict(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    hook = _stub(tmp_path, "broken.sh", "#!/usr/bin/env bash\nexit 3\n")
    r = _run(hook, blocker / "sub" / "l.jsonl")
    assert r.returncode == 3


def test_wrapper_with_no_arguments_is_non_blocking():
    r = subprocess.run(["bash", WRAPPER], input="", capture_output=True, text=True)
    assert r.returncode == 0
