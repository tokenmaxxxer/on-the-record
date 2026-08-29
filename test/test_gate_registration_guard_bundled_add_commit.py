"""Regression test for issue #2705: `gate-registration-guard.sh` reads
`git diff --cached` in a PreToolUse hook, which fires BEFORE the guarded
Bash command's text runs. A bundled `git add <new gate> && git commit`
(this repo's own recommended landing shape, #2135) had nothing staged
at hook time, so the guard's target list was always empty and an
unregistered gate/hook module landed with no refusal, silently.

Runs the real shipped hook (`bash on-the-record/hooks/
gate-registration-guard.sh`) via a real PreToolUse JSON payload on
stdin, against a real local git checkout -- same harness shape as
test/test_upstream_defect_scope_guard_cross_repo_cwd.py.

Both directions matter (issue #2705 Acceptance): the bundled shape must
now refuse an unregistered new gate module, AND the pre-existing
stage-then-commit (two separate Bash calls) shape must keep behaving
exactly as before -- both refusing when unregistered and allowing when
registered.

An independent adversarial-review evaluator session (given only the
first cut of this fix's diff, no issue context) live-reproduced three
further bypasses of the bundled shape that the literal-path-only
`git add <path>` form above does not exercise:
`git add -A`/`--all` (BundledAddDashACommitTest -- the flag token was
being stripped by the generic `-`-prefix filter before the
whole-tree special case ever saw it, making that branch dead code),
`git -c k=v add`/`git -C dir add` (BundledGitGlobalOptionAddTest -- a
two-token global option between `git` and `add` broke the flag-skip
loop, the same bypass class issue #866/#876 already fixed for the
sibling `commit`-detection check but never hardened here), and
`git add .` scoped to the acting directory rather than the whole repo
(BundledAddDotScopingTest -- an unrelated untracked gate file elsewhere
in the tree must not false-close a docs-only commit run from a
subdirectory). `BundledAddDashUCommitTest` pins the correct negative:
`-u`/`--update` never stages a new untracked file, so it must not be
treated as "stage everything".

Two independent adversarial-review verification sessions of that first
cut (docs/issue-2705/reports/adversarial-review-249cc937.md and
adversarial-review-e4ba953e.md) then live-reproduced a further class of
bypass in the parser itself -- the very defect this issue exists to
fix, one layer down: `BundledCdBeforeAddTest` pins a `cd <subdir> &&
git add <relpath> && git commit` and its subshell form (an earlier
segment of the same command changes the effective directory the
`add`'s relative path resolves against, which the parser previously
never tracked), `BundledDirectoryAddTest` pins `git add gates/` /
`git add gates` (a directory argument stages every untracked file
beneath it, same as `.` already does, which the parser previously
treated as a single literal/glob token that matches nothing), and
`BundledExcludePathspecTest` pins the opposite-direction bug -- a false
REFUSAL, not a bypass -- where `git add . ':(exclude)<path>'` refused
on a path real git would not actually stage.

Run: python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "gate-registration-guard.sh"

_FIXTURE_BASE = Path.home() / ".otr-grg-bundled-test-fixture"


def _run_guard(command: str, cwd: str):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
        "session_id": "test-sess",
    })
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=cwd, env=env, timeout=30,
    )


class _GuardTestBase(unittest.TestCase):
    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        subprocess.run(["git", "clone", "-q", "--depth", "1",
                         f"file://{REPO_ROOT}", str(self.repo)],
                        check=True, timeout=60)

    def _write(self, rel_path: str, content: str):
        full = self.repo / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")


class BundledAddCommitRefusesUnregisteredGateTest(_GuardTestBase):
    """Acceptance check 1: `git add <new gates/*.py> && git commit` as a
    single Bash call must now show the refusal."""

    def test_bundled_shape_refuses_new_unregistered_gate(self):
        self._write("gates/new_gate_2705.py", "def check():\n    pass\n")
        r = _run_guard(
            "git add gates/new_gate_2705.py && git commit -m 'add gate'",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("no row in docs/specs/enforcement-boundary.md", r.stderr)


class BundledAddCommitAllowsRegisteredGateTest(_GuardTestBase):
    """The bundled shape must not become fail-closed for the ordinary
    case: a new gate that DOES carry its spec row in the same commit."""

    def test_bundled_shape_allows_registered_gate(self):
        self._write("gates/new_gate_2705b.py", "def check():\n    pass\n")
        self._write(
            "docs/specs/enforcement-boundary.md",
            "| mechanism | verdict |\n| --- | --- |\n"
            "| `new_gate_2705b.py` | registered, ok |\n")
        r = _run_guard(
            "git add gates/new_gate_2705b.py "
            "docs/specs/enforcement-boundary.md && git commit -m 'add gate'",
            str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)


class SeparateCommandsShapeUnchangedTest(_GuardTestBase):
    """Acceptance check 2: staging in one Bash call and committing in the
    next must keep behaving exactly as before this fix -- both the deny
    and the allow path."""

    def test_stage_then_commit_still_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705c.py", "def check():\n    pass\n")
        subprocess.run(["git", "add", "gates/new_gate_2705c.py"],
                        cwd=self.repo, check=True)
        r = _run_guard("git commit -m 'add gate'", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("no row in docs/specs/enforcement-boundary.md", r.stderr)

    def test_stage_then_commit_still_allows_registered_gate(self):
        self._write("gates/new_gate_2705d.py", "def check():\n    pass\n")
        self._write(
            "docs/specs/enforcement-boundary.md",
            "| mechanism | verdict |\n| --- | --- |\n"
            "| `new_gate_2705d.py` | registered, ok |\n")
        subprocess.run(
            ["git", "add", "gates/new_gate_2705d.py",
             "docs/specs/enforcement-boundary.md"],
            cwd=self.repo, check=True)
        r = _run_guard("git commit -m 'add gate'", str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)


class BundledAddDashACommitTest(_GuardTestBase):
    """`git add -A && git commit` must catch a new unregistered gate --
    the single most idiomatic "stage everything" bundled invocation."""

    def test_dash_a_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_a.py", "def check():\n    pass\n")
        r = _run_guard("git add -A && git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_dash_dash_all_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_all.py", "def check():\n    pass\n")
        r = _run_guard("git add --all && git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)


class BundledAddDashUCommitTest(_GuardTestBase):
    """`-u`/`--update` stages modifications to already-tracked files
    only -- it never stages a brand new untracked file, so a bundled
    `git add -u && git commit` must NOT be treated as "stage
    everything" and must not flag an untouched new gate file."""

    def test_dash_u_does_not_flag_unrelated_untracked_new_gate(self):
        self._write("gates/new_gate_2705_u.py", "def check():\n    pass\n")
        r = _run_guard("git add -u && git commit -m x --allow-empty",
                        str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)


class BundledGitGlobalOptionAddTest(_GuardTestBase):
    """A two-token git global option (`-c <key>=<val>`, `-C <dir>`)
    between `git` and `add` must not defeat detection -- the same
    bypass class issue #866/#876 already fixed for this file's
    `commit`-detection check."""

    def test_dash_c_kv_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_c.py", "def check():\n    pass\n")
        r = _run_guard(
            "git -c user.email=a@b.com add gates/new_gate_2705_c.py "
            "&& git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_dash_cap_c_dir_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_cap_c.py", "def check():\n    pass\n")
        r = _run_guard(
            f"git -C {self.repo} add gates/new_gate_2705_cap_c.py "
            "&& git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)


class BundledAddDotScopingTest(_GuardTestBase):
    """`git add .` stages only the acting directory's subtree in real
    git -- an untracked, unregistered gate file elsewhere in the repo
    must not false-close a `git add . && git commit` run from an
    unrelated subdirectory, while the same command from the repo root
    (where `.` really does cover the gate file) must still refuse."""

    def test_dot_from_unrelated_subdir_does_not_flag_stray_gate_elsewhere(self):
        self._write("gates/stray_unrelated_2705.py", "def check():\n    pass\n")
        self._write("docs/note_2705.md", "hello\n")
        r = _run_guard("git add . && git commit -m 'docs update'",
                        str(self.repo / "docs"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_dot_from_repo_root_still_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_dot.py", "def check():\n    pass\n")
        r = _run_guard("git add . && git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)


class BundledCdBeforeAddTest(_GuardTestBase):
    """A `cd` (or subshell `cd`) segment before the `git add` segment
    of the same bundled command shifts the effective directory the
    add's relative path resolves against -- the payload's static
    top-level `cwd` (the repo root here) is only the STARTING
    directory, not necessarily the one in force when `add` runs. Both
    independent adversarial-review verifications of the first cut of
    this fix live-reproduced this as a silent bypass (rc=0) on the
    identical unregistered-module fixture the literal-path case above
    correctly refuses."""

    def test_plain_cd_before_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_cd.py", "def check():\n    pass\n")
        r = _run_guard(
            "cd gates && git add new_gate_2705_cd.py && git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_subshell_cd_before_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_sub.py", "def check():\n    pass\n")
        r = _run_guard(
            "(cd gates && git add new_gate_2705_sub.py && git commit -m x)",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_cd_then_dotdot_relative_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_dotdot.py", "def check():\n    pass\n")
        self._write("sub/.keep", "")
        r = _run_guard(
            "cd sub && git add ../gates/new_gate_2705_dotdot.py "
            "&& git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_subshell_cd_does_not_leak_to_a_later_top_level_segment(self):
        """A subshell's own `cd` must not affect a LATER top-level
        segment's cwd once the subshell closes -- bash itself does not
        leak a `(...)`'s directory change to its parent shell, so the
        outer `git add gates/new_gate_2705_noleak.py` below must still
        resolve against the repo root, not the subshell's `other/`."""
        self._write("gates/new_gate_2705_noleak.py", "def check():\n    pass\n")
        self._write("other/.keep", "")
        r = _run_guard(
            "(cd other) && git add gates/new_gate_2705_noleak.py "
            "&& git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)


class BundledDirectoryAddTest(_GuardTestBase):
    """`git add gates/` / `git add gates` (no trailing slash) stage
    every untracked file beneath that directory in real git -- the
    same sweep `git add .` already gets, just spelled with a directory
    name instead of the cwd shorthand. The pre-fix parser treated a
    directory argument as an ordinary literal/glob token, which
    matches neither the exact untracked path nor its fnmatch fallback
    (no wildcard character in a bare directory name), so it silently
    contributed zero targets."""

    def test_trailing_slash_directory_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_dir1.py", "def check():\n    pass\n")
        r = _run_guard("git add gates/ && git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_no_trailing_slash_directory_add_refuses_unregistered_gate(self):
        self._write("gates/new_gate_2705_dir2.py", "def check():\n    pass\n")
        r = _run_guard("git add gates && git commit -m x", str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)


class BundledExcludePathspecTest(_GuardTestBase):
    """`git add . ':(exclude)<path>'` (pathspec magic) stages
    everything under `.` except the excluded path in real git -- the
    pre-fix parser had no concept of pathspec magic, so the `.`
    argument's unconditional cwd-relative sweep flagged the excluded,
    unregistered file anyway: a false REFUSAL on a path real git would
    never actually stage, the over-refusal direction issue #2705's
    must-not explicitly warns against. A second case pins that an
    exclude pathspec for an UNRELATED path must not swallow a real,
    still-staged unregistered gate -- the fix must not just make the
    whole segment go quiet whenever any exclude token appears."""

    def test_exclude_pathspec_does_not_falsely_refuse_excluded_gate(self):
        self._write("gates/excluded_2705.py", "def check():\n    pass\n")
        self._write("unrelated_2705.md", "hello\n")
        r = _run_guard(
            "git add . ':(exclude)gates/excluded_2705.py' && git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_exclude_pathspec_for_unrelated_path_still_refuses_real_gate(self):
        self._write("gates/new_gate_2705_excl.py", "def check():\n    pass\n")
        self._write("excluded_unrelated_2705.md", "hello\n")
        r = _run_guard(
            "git add . ':(exclude)excluded_unrelated_2705.md' "
            "&& git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_bang_shorthand_exclude_pathspec_does_not_falsely_refuse(self):
        self._write("gates/excluded_2705_bang.py", "def check():\n    pass\n")
        r = _run_guard(
            "git add . ':!gates/excluded_2705_bang.py' && git commit -m x",
            str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
