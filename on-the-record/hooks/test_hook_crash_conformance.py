#!/usr/bin/env python3
"""issue #2093 — crash conformance over every registered hook.

Acceptance check 1: every hook in `hooks.json` survives the edge-input corpus
with no Traceback on stderr.

The unit under test is the **hooks.json entry**, not the script file: the same
script appears under different argv, and argv selects the parse path, so the
matrix keys on the registration.

What "survives" means, and why it is not "exits 0": the platform's exit-code
table is fixed -- 0 = allow, 2 = block, anything else = non-blocking.  A guard
that crashes exits 1 and is therefore *skipped silently* while spraying a
traceback into the consuming session.  So the conformance property is:

    exit code in {0, 2}  AND  no traceback on stderr

Exit 2 is a legitimate outcome here, not an exemption: `deliverable-guard.sh`
deliberately fails **closed** on unverifiable stdin (docs/handbooks/
on-the-record.md), and that is encoded below as a declared expectation rather
than skipped.

Isolation: every invocation runs in a throwaway HOME and a throwaway cwd, with
`gh`/`curl` shadowed by stubs on PATH, so a conformance run neither touches the
network nor mutates the developer's real state.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = HOOKS_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parent
HOOKS_JSON = HOOKS_DIR / "hooks.json"

PER_HOOK_TIMEOUT = 60
TRACEBACK_MARKER = "Traceback (most recent call last)"

# Hooks whose declared behaviour on an unverifiable input is to fail CLOSED.
# Listed so the expectation is visible, not so the check is skipped.
FAIL_CLOSED_HOOKS = {"deliverable-guard.sh"}

# The five sites migrated onto hook_input in this issue.  The fast-tier smoke
# below covers exactly these, so the default suite is not blind to the class
# while the full 58-entry matrix stays slow-marked.
MIGRATED_HOOKS = (
    "contract-guard.sh",
    "merge-allow-gate.sh",
    "post-landing-obligation-gate.sh",
    "quality-bar-gate.sh",
    "absorbed-branch-recut-guard.sh",
)


# --- the edge-input corpus -------------------------------------------------

def _payload(command, tool="Bash", **extra):
    body = {"session_id": "conformance", "tool_name": tool,
            "tool_input": {"command": command}}
    body.update(extra)
    return json.dumps(body)


CORPUS = [
    ("unexpanded-tilde-cd", _payload("cd ~/work/repo && git commit -m x")),
    ("unexpanded-tilde-cd-merge", _payload("cd ~/work/repo && gh pr merge 1 --squash")),
    ("heredoc-body", _payload("cat <<'EOF'\ncd /elsewhere && gh pr merge 9\nEOF")),
    ("nested-quotes", _payload("""git commit -m "a 'b' \\"c\\" d" """)),
    ("unbalanced-quotes", _payload("cd /tmp && echo 'unterminated")),
    ("unicode", _payload("git commit -m '日本語 🎉 커밋'")),
    ("empty-command", _payload("")),
    ("huge-command", _payload("cd /tmp && echo " + "z" * 100_000)),
    ("missing-tool-input", '{"session_id": "conformance", "tool_name": "Bash"}'),
    ("non-dict-payload", "[1, 2, 3]"),
    ("malformed-json", "{not json"),
    ("empty-stdin", ""),
]


# --- the registry ----------------------------------------------------------

def _registered_entries():
    """Every hooks.json registration, as (id, event, matcher, argv)."""
    raw = HOOKS_JSON.read_text().replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))
    hooks = json.loads(raw).get("hooks", {})
    out = []
    for event, groups in sorted(hooks.items()):
        for group in groups:
            matcher = group.get("matcher", "")
            for h in group.get("hooks", []):
                command = h.get("command", "")
                if not command:
                    continue
                argv = command.split()
                # A wrapped registration's subject is the hook it wraps.
                subject = argv[1] if Path(argv[0]).name == "fail-open-wrapper.sh" \
                    and len(argv) > 1 else argv[0]
                ident = "%s:%s:%s" % (event, Path(subject).name,
                                      "+".join(argv[1:]) or "-")
                out.append((ident, event, matcher, argv))
    return out


ENTRIES = _registered_entries()
ENTRY_IDS = [e[0] for e in ENTRIES]


def test_the_registry_is_non_empty_and_every_script_exists():
    """A matrix built from an empty or broken registry proves nothing."""
    # issue #2138 gate retirement: 58 registrations -> 28 (KEEP set,
    # pinned exactly by test_gate_registry.py).
    assert len(ENTRIES) >= 25, "hooks.json parsed to %d entries" % len(ENTRIES)
    for ident, _event, _matcher, argv in ENTRIES:
        subject = argv[1] if Path(argv[0]).name == "fail-open-wrapper.sh" \
            and len(argv) > 1 else argv[0]
        assert Path(subject).is_file(), "%s: %s missing" % (ident, subject)


# --- the sandbox -----------------------------------------------------------

@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    """A throwaway HOME + cwd + stub PATH shared by the whole matrix."""
    base = tmp_path_factory.mktemp("hook-conformance")
    home = base / "home"
    (home / ".claude" / "on-the-record").mkdir(parents=True)
    cwd = base / "project"
    cwd.mkdir()
    subprocess.run(["git", "init", "-q", str(cwd)], capture_output=True)
    subprocess.run(["git", "-C", str(cwd), "config", "user.email", "t@t.t"],
                   capture_output=True)
    subprocess.run(["git", "-C", str(cwd), "config", "user.name", "t"],
                   capture_output=True)

    stubs = base / "bin"
    stubs.mkdir()
    for name in ("gh", "curl", "wget"):
        p = stubs / name
        p.write_text("#!/usr/bin/env bash\nexit 1\n")
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "PATH": str(stubs) + os.pathsep + env.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
        "CLAUDE_PROJECT_DIR": str(cwd),
        "OTR_FAIL_OPEN_LEDGER": str(base / "fail-open.jsonl"),
        "TOKENMAXXXER_CHECKOUT": str(REPO_ROOT),
    })
    env.pop("ORCHESTRATE_OFF", None)  # an off switch would vacuously pass the matrix
    return {"env": env, "cwd": str(cwd), "base": base}


def _run_entry(argv, payload, sandbox):
    return subprocess.run(
        ["bash", *argv],
        input=payload,
        capture_output=True,
        text=True,
        env=sandbox["env"],
        cwd=sandbox["cwd"],
        timeout=PER_HOOK_TIMEOUT,
    )


def _assert_survives(ident, argv, case, payload, sandbox):
    subject = Path(argv[1] if Path(argv[0]).name == "fail-open-wrapper.sh"
                   and len(argv) > 1 else argv[0]).name
    try:
        r = _run_entry(argv, payload, sandbox)
    except subprocess.TimeoutExpired:
        pytest.fail("%s hung past %ds on the %s case" % (ident, PER_HOOK_TIMEOUT, case))

    assert TRACEBACK_MARKER not in r.stderr, (
        "%s sprayed a traceback on the %s case:\n%s" % (ident, case, r.stderr[-2000:])
    )
    assert r.returncode in (0, 2), (
        "%s exited %d on the %s case — neither allow (0) nor block (2), so the "
        "platform skips it silently.\nstderr:\n%s"
        % (ident, r.returncode, case, r.stderr[-2000:])
    )
    if subject in FAIL_CLOSED_HOOKS and case in ("malformed-json", "empty-stdin"):
        assert r.returncode == 2, (
            "%s is declared fail-closed on unverifiable stdin; it exited %d"
            % (subject, r.returncode)
        )
    return r


# --- fast tier: the migrated sites ----------------------------------------

@pytest.mark.parametrize("case,payload", CORPUS, ids=[c[0] for c in CORPUS])
@pytest.mark.parametrize("hook", MIGRATED_HOOKS)
def test_migrated_hooks_survive_the_corpus(hook, case, payload, sandbox):
    """Fast-tier smoke: the sites this issue actually rewrote."""
    _assert_survives(hook, [str(HOOKS_DIR / hook)], case, payload, sandbox)


def test_a_deliberately_broken_hook_fails_this_conformance_check(sandbox, tmp_path):
    """Negative control: the check can actually go red."""
    broken = tmp_path / "broken-guard.sh"
    broken.write_text("#!/usr/bin/env bash\npython3 -c 'raise RuntimeError(\"boom\")'\n")
    broken.chmod(broken.stat().st_mode | stat.S_IXUSR)
    with pytest.raises(Exception):
        _assert_survives("broken", [str(broken)], "malformed-json", "{not json", sandbox)


def test_tilde_expansion_is_what_makes_the_tilde_case_pass(sandbox):
    """Negative control for the fix itself, not just for the harness.

    Reverting `expanduser` in `cd_target` is what this asserts against: with a
    real `~`-prefixed cd, the resolved target must be an absolute path.
    """
    extract = str(HOOKS_DIR / "absorbed-branch-recut-guard.sh")
    r = _run_entry([extract], _payload("cd ~/work/repo && git commit -m x"), sandbox)
    assert TRACEBACK_MARKER not in r.stderr
    assert r.returncode in (0, 2)

    import sys as _sys
    _sys.path.insert(0, str(HOOKS_DIR))
    from hook_input import CdTarget, cd_target
    resolved = cd_target("cd ~/work/repo && git commit -m x")
    assert isinstance(resolved, CdTarget)
    assert resolved.path.startswith(os.path.expanduser("~"))
    assert "~" not in resolved.path


# --- slow tier: the full registry x corpus matrix -------------------------

@pytest.mark.slow
@pytest.mark.parametrize("case,payload", CORPUS, ids=[c[0] for c in CORPUS])
@pytest.mark.parametrize("ident,event,matcher,argv", ENTRIES, ids=ENTRY_IDS)
def test_every_registered_hook_survives_the_corpus(
    ident, event, matcher, argv, case, payload, sandbox
):
    _assert_survives(ident, argv, case, payload, sandbox)


@pytest.mark.slow
def test_no_registered_hook_is_missing_from_the_matrix():
    """The matrix is derived from hooks.json, so drift cannot silently shrink it."""
    on_disk = {p.name for p in HOOKS_DIR.glob("*.sh")}
    registered = set()
    for _ident, _event, _matcher, argv in ENTRIES:
        for token in argv:
            if token.endswith(".sh"):
                registered.add(Path(token).name)
    assert registered <= on_disk | {"fail-open-wrapper.sh"}
    assert shutil.which("bash"), "the matrix needs a real bash"
