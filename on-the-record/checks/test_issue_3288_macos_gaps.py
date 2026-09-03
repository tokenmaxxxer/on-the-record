"""Three gaps the macOS check could not see (issue #3288).

PR #3282 fixed everything this check reported, and its independent
verification then found the same files still break on a Mac -- for
reasons the check had no rule for. A gate that passes a file which fails
on the platform it is named after is worse than no gate: it is a claim.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import macos_bash32_compat as m  # noqa: E402


class GnuOnlyBinariesAreFlaggedTest(unittest.TestCase):
    def test_an_unguarded_timeout_is_a_violation(self):
        v = m.check_sh_gnu_only("x.sh", "#!/bin/bash\ntimeout 600 claude -p hi\n")
        self.assertEqual(len(v), 1, v)
        self.assertIn("gtimeout", v[0])

    def test_a_guarded_timeout_is_not(self):
        text = ("if command -v timeout >/dev/null 2>&1; then\n"
                "  timeout 600 claude -p hi\n"
                "else\n  claude -p hi\nfi\n")
        self.assertEqual(m.check_sh_gnu_only("x.sh", text), [])

    def test_a_python_keyword_argument_is_not_the_binary(self):
        # First run of this rule flagged `timeout=30` inside a heredoc'd
        # Python block in amends-landing-apply.sh.
        text = "python3 - <<'PY'\nsubprocess.run(c, timeout=30)\nPY\n"
        self.assertEqual(m.check_sh_gnu_only("x.sh", text), [])

    def test_a_comment_is_not_an_invocation(self):
        self.assertEqual(
            m.check_sh_gnu_only("x.sh", "# timeout 600 was here once\n"), [])


class TheProcRegexSeesTheBarePathTest(unittest.TestCase):
    def test_isdir_proc_is_matched(self):
        # The guard PR #3282 itself introduced; the old regex required a
        # trailing slash and missed it.
        self.assertTrue(m._PROC_RE.search('if not os.path.isdir("/proc"):'))

    def test_a_proc_path_is_still_matched(self):
        self.assertTrue(m._PROC_RE.search('open("/proc/%d/stat" % pid)'))

    def test_an_unrelated_word_is_not(self):
        self.assertIsNone(m._PROC_RE.search('note = "process the queue"'))


class TheAllowlistCountsDependenciesTest(unittest.TestCase):
    def test_every_reviewed_file_carries_a_count(self):
        self.assertTrue(all(isinstance(v, int)
                            for v in m.KNOWN_PROC_SITES.values()),
                        "a bare filename allowlists the FILE, so a second "
                        "dependency added to it is invisible")

    def test_the_counts_match_the_tree_today(self):
        # If this fails, either a /proc dependency was added (review it,
        # then update the number) or one was removed (the reviewed number
        # no longer describes the file).
        import subprocess  # noqa: PLC0415
        root = HERE.parent.parent
        files = subprocess.run(["git", "-C", str(root), "ls-files", "*.py"],
                               capture_output=True, text=True).stdout.split()
        seen = {}
        for rel in files:
            if rel.startswith("docs/") or "/test" in rel or rel.startswith("test"):
                continue
            try:
                text = (root / rel).read_text(encoding="utf-8")
            except OSError:
                continue
            n = sum(1 for line in text.splitlines()
                    if m._PROC_RE.search(line) and not line.strip().startswith("#"))
            if n:
                seen[Path(rel).name] = n
        self.assertEqual(seen, m.KNOWN_PROC_SITES)


if __name__ == "__main__":
    unittest.main()
