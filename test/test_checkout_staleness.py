"""Tests for issue #2506: a gate invoked from a stale checkout must refuse
to produce a verdict, naming the staleness, instead of silently evaluating
old code.

`spawn.checkout_staleness(root)` is the pure-ish detector (fetch + compare,
never mutates the working tree). `merge_gate.evaluate()` wires it in as the
first check, ahead of any check-runner/verification-record logic, so a
stale checkout short-circuits to a refusal that names the staleness.

Run: python3 -m pytest test/test_checkout_staleness.py -q
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import merge_gate  # noqa: E402
import spawn  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


class CheckoutStalenessTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.bare = base / "origin.git"
        self.a = base / "checkout-a"  # will be pointed at a deliberately-stale HEAD
        self.b = base / "checkout-b"  # advances origin
        _git(base, "init", "-q", "--initial-branch=main", str(self.bare), "--bare")
        for clone in (self.a, self.b):
            subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)],
                           capture_output=True, text=True, check=True)
            _git(clone, "config", "user.email", "a@b.c")
            _git(clone, "config", "user.name", "test")
        (self.a / "README.md").write_text("hello\n")
        _git(self.a, "add", "README.md")
        _git(self.a, "commit", "-q", "-m", "init")
        subprocess.run(["git", "-C", str(self.a), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)
        # A clone made from an empty bare repo (as `b` was, above) never
        # gets `origin/HEAD` set automatically -- only a clone of a
        # non-empty repo does. Both checkouts need it for the ancestry
        # comparison `checkout_staleness()` relies on.
        _git(self.a, "remote", "set-head", "origin", "-a")
        _git(self.b, "pull", "-q", "origin", "main")
        _git(self.b, "remote", "set-head", "origin", "-a")

    def _advance_origin_from_b(self):
        (self.b / "NEWS.md").write_text("gate landed\n")
        _git(self.b, "add", "NEWS.md")
        _git(self.b, "commit", "-q", "-m", "advance")
        subprocess.run(["git", "-C", str(self.b), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)

    def test_current_checkout_is_not_stale(self):
        result = spawn.checkout_staleness(root=self.a)
        self.assertTrue(result["checked"])
        self.assertFalse(result["stale"])
        self.assertEqual(result["behind"], 0)

    def test_deliberately_stale_checkout_is_flagged_with_count(self):
        self._advance_origin_from_b()
        # checkout-a never fetched/pulled the new commit -- deliberately stale.
        result = spawn.checkout_staleness(root=self.a)
        self.assertTrue(result["checked"])
        self.assertTrue(result["stale"])
        self.assertEqual(result["behind"], 1)
        self.assertIn("1개 커밋 뒤처졌다", result["detail"])

    def test_staleness_check_never_mutates_the_working_tree(self):
        self._advance_origin_from_b()
        before = _git(self.a, "rev-parse", "HEAD").stdout.strip()
        status_before = _git(self.a, "status", "--porcelain").stdout
        spawn.checkout_staleness(root=self.a)
        after = _git(self.a, "rev-parse", "HEAD").stdout.strip()
        status_after = _git(self.a, "status", "--porcelain").stdout
        self.assertEqual(before, after, "fetch+compare must not move HEAD")
        self.assertEqual(status_before, status_after)

    def test_merge_base_error_is_not_silently_read_as_fresh(self):
        # silent-failure-audit finding (issue #2506): `merge-base
        # --is-ancestor` returns 0=yes/1=no, but other exit codes mean git
        # itself failed (e.g. a corrupt object) -- that must surface as
        # `checked: False`, not fall through and get counted as "0 commits
        # behind" the way a bare `returncode == 0` check would.
        self._advance_origin_from_b()
        real_run = subprocess.run

        def fake_run(cmd, *a, **kw):
            if "merge-base" in cmd and "--is-ancestor" in cmd:
                return subprocess.CompletedProcess(cmd, 128, "", "fatal: bad object\n")
            return real_run(cmd, *a, **kw)

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = spawn.checkout_staleness(root=self.a)
        self.assertFalse(result["checked"])
        self.assertFalse(result["stale"])
        self.assertIn("판정 실패", result["detail"])

    def test_no_origin_remote_is_a_checked_false_no_op(self):
        # issue's declared empty state: a fresh checkout with no remote --
        # must not be mistaken for stale.
        solo = Path(self._tmp.name) / "solo"
        subprocess.run(["git", "init", "-q", "--initial-branch=main", str(solo)],
                       capture_output=True, text=True, check=True)
        _git(solo, "config", "user.email", "a@b.c")
        _git(solo, "config", "user.name", "test")
        (solo / "f.txt").write_text("x\n")
        _git(solo, "add", "f.txt")
        _git(solo, "commit", "-q", "-m", "init")
        result = spawn.checkout_staleness(root=solo)
        self.assertFalse(result["checked"])
        self.assertFalse(result["stale"])


class MergeGateRefusesOnStaleCheckoutTest(unittest.TestCase):
    """`gates/merge_gate.py::evaluate()` must refuse before computing any
    check-runner/verification-record logic when its own checkout is stale
    — the exact shape of the 2026-08-26 incident (a stale `_exempt_own_role`
    producing a confident wrong refusal)."""

    def test_stale_checkout_short_circuits_to_a_named_refusal(self):
        stale = {"checked": True, "stale": True, "behind": 9, "fetch_ok": True,
                 "detail": "체크아웃(/fake)이 origin 대비 9개 커밋 뒤처졌다 (로컬=aaa origin=bbb)"}
        with mock.patch.object(spawn, "checkout_staleness", return_value=stale):
            with mock.patch.object(merge_gate, "latest_check_runner_comment") as m:
                result = merge_gate.evaluate(Path("/fake"), Path("/fake"), 1, "subject")
                m.assert_not_called()  # never reaches the old-code-dependent checks
        self.assertFalse(result["allowed"])
        self.assertEqual(len(result["reasons"]), 1)
        self.assertIn("checkout-stale", result["reasons"][0])
        self.assertIn("9개 커밋 뒤처졌다", result["reasons"][0])
        self.assertEqual(result["checkout_staleness"], stale)

    def test_legitimately_current_checkout_is_not_blocked(self):
        fresh = {"checked": True, "stale": False, "behind": 0, "fetch_ok": True, "detail": ""}
        with mock.patch.object(spawn, "checkout_staleness", return_value=fresh):
            with mock.patch.object(merge_gate, "latest_check_runner_comment",
                                   return_value=None):
                with mock.patch.object(merge_gate.check_runner,
                                       "fetch_all_skill_branches"):
                    with mock.patch.object(merge_gate, "required_verification_missing",
                                           return_value=[]):
                        with mock.patch.object(merge_gate, "pr_refs", return_value=None):
                            with mock.patch.object(merge_gate, "stale_revert_reasons",
                                                   return_value=[]):
                                with mock.patch.object(merge_gate, "staleness_for_pr",
                                                       return_value=None):
                                    result = merge_gate.evaluate(
                                        Path("/fake"), Path("/fake"), 1, "subject")
        # not blocked by the checkout-staleness guard specifically (it may
        # still be refused for the missing check-runner comment, which is
        # the real, unrelated reason here).
        self.assertNotIn("checkout_staleness", result)
        self.assertEqual(result["reasons"], ["check-runner 코멘트를 찾을 수 없다"])


if __name__ == "__main__":
    unittest.main()
