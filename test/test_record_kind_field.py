"""issue #2241 stage 1: `gates/record_lint.py::record_kind_vocabulary_check`
is ADVISORY ONLY against the closed vocabulary
`docs/specs/record-kind-vocabulary.md` formalizes — a value outside it
produces an advisory, never a denial; a value inside it produces none."""
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import record_lint  # noqa: E402


class RecordKindVocabularyCheckTest(unittest.TestCase):
    def test_kind_outside_vocabulary_produces_one_advisory(self):
        text = "---\nissue: 2284\nkind: not-a-real-kind-xyz\n---\n\nbody\n"
        bad = record_lint.record_kind_vocabulary_check(ROOT, text)
        self.assertEqual(len(bad), 1)
        self.assertIn("not-a-real-kind-xyz", bad[0])

    def test_kind_inside_vocabulary_produces_no_advisory(self):
        text = "---\nissue: 2284\nkind: survey\n---\n\nbody\n"
        self.assertEqual(record_lint.record_kind_vocabulary_check(ROOT, text), [])

    def test_no_kind_line_is_additive_empty_state(self):
        text = "---\nissue: 2284\nrole: implementation\n---\n\nbody\n"
        self.assertEqual(record_lint.record_kind_vocabulary_check(ROOT, text), [])

    def test_kind_mentioned_only_in_prose_is_not_frontmatter(self):
        text = ("---\nissue: 2284\n---\n\n"
                "the section header says kind: not-a-real-kind-xyz here\n")
        self.assertEqual(record_lint.record_kind_vocabulary_check(ROOT, text), [])


class AdvisoryNeverBlocksAggregationTest(unittest.TestCase):
    def test_lint_record_source_never_calls_the_kind_check(self):
        """This repo's DEMOTE convention for a brand-new check (stage-1
        proposal Constraints): land it, prove it fires, and leave
        `lint_record()`'s blocking aggregation untouched until a later
        stage promotes it."""
        source = inspect.getsource(record_lint.lint_record)
        self.assertNotIn("record_kind_vocabulary_check", source)


if __name__ == "__main__":
    unittest.main()
