import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "gates"))
import retirement_count  # noqa: E402


class TokenizeCoversTheDerivedPopulationTest(unittest.TestCase):
    """issue #2876: `\\brole\\b` misses every spelling where the character
    that continues "role" is itself a `\\w` character -- the plural
    suffix, an adjoining underscore, or a case change with no separator
    at all. `line_hits` must catch exactly those, and must not flag an
    unrelated word that merely contains the letters "role"."""

    def test_bare_word_still_matches(self):
        self.assertTrue(retirement_count.line_hits("the role is retired"))

    def test_plain_grep_word_boundary_already_missed_this(self):
        self.assertTrue(retirement_count.line_hits("the roles are retired"))

    def test_snake_case_prefix_and_suffix_both_match(self):
        self.assertTrue(retirement_count.line_hits("user_role = None"))
        self.assertTrue(retirement_count.line_hits("role_id = None"))

    def test_case_variants_match(self):
        self.assertTrue(retirement_count.line_hits('title = "Role"'))
        self.assertTrue(retirement_count.line_hits("ROLE_NAME = 1"))
        self.assertTrue(retirement_count.line_hits("class RoleModel: pass"))

    def test_hyphenated_compound_matches_like_old_check_already_did(self):
        self.assertTrue(retirement_count.line_hits("# role-handoff notes"))

    def test_singular_possessive_matches_like_old_check_already_did(self):
        self.assertTrue(retirement_count.line_hits("this role's scope"))

    def test_unrelated_word_containing_the_letters_is_not_flagged(self):
        self.assertFalse(retirement_count.line_hits("patrol the controller"))
        self.assertFalse(retirement_count.line_hits("cabriole step"))

    def test_empty_line_not_flagged(self):
        self.assertFalse(retirement_count.line_hits(""))


class EmptyStateExitsCleanNotErrorTest(unittest.TestCase):
    """A tree with zero occurrences must return 0 and exit clean -- the
    standing rule this issue's Acceptance names explicitly; a check that
    errors on the empty case is as unusable as one that always passes."""

    def test_zero_occurrences_returns_zero_and_prints_nothing_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, check=True)
            (Path(tmp) / "clean.py").write_text("x = 1\n")
            subprocess.run(["git", "add", "clean.py"], cwd=tmp, check=True)
            env = dict(os.environ)
            r = subprocess.run(
                [sys.executable, str(REPO_ROOT / "gates" / "retirement_count.py")],
                cwd=tmp, capture_output=True, text=True, env=env,
            )
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")

    def test_one_occurrence_fails_nonzero_and_lists_the_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, check=True)
            (Path(tmp) / "dirty.py").write_text('ACTIVE_KINDS = ["roles"]\n')
            subprocess.run(["git", "add", "dirty.py"], cwd=tmp, check=True)
            r = subprocess.run(
                [sys.executable, str(REPO_ROOT / "gates" / "retirement_count.py")],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("dirty.py:1:", r.stdout)


class ListFilesDerivesTheReaderCheckPopulationTest(unittest.TestCase):
    """issue #2876 round 2: pr-preflight.sh:417 kept the identical "roles"-
    key defect gates/flows.py was fixed for, invisible to a reader-check
    grep hand-typed with `--include=*.py` only. `--list-files` exposes this
    checker's own tracked population so a future reader search can pipe
    through it instead of restating (and potentially narrowing) the
    extension list by hand."""

    def test_list_files_includes_a_known_sh_and_py_site_excludes_docs_and_self(self):
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "gates" / "retirement_count.py"), "--list-files"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        files = set(r.stdout.splitlines())
        self.assertIn("on-the-record/hooks/pr-preflight.sh", files)
        self.assertIn("gates/flows.py", files)
        self.assertFalse(any(f.startswith("docs/") for f in files))
        self.assertNotIn("gates/retirement_count.py", files)


if __name__ == "__main__":
    unittest.main()
