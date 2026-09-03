"""The control arm has to mirror a multi-file skill (issue #3245).

`code-architecture` and `experiment-trust` carry a `references/`
directory. The decoy built only SKILL.md, so the arms mounted 4 files
against 2 and 3 against 2, and the trust root refused both pairs --
correctly: a scored difference could then be attributed to the file count
rather than to the guidance.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "consumer-path"))

import prepare_arms  # noqa: E402


class TheDecoyMirrorsTheFileSetTest(unittest.TestCase):
    def setUp(self):
        self.real_root = Path(tempfile.mkdtemp()) / "skills" / "demo-skill"
        (self.real_root / "references").mkdir(parents=True)
        (self.real_root / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: real\n---\n\nreal body\n",
            encoding="utf-8")
        (self.real_root / "references" / "rules.md").write_text(
            "rule one\n", encoding="utf-8")

    def _decoy(self):
        root = prepare_arms.build_decoy_skill_root(
            "demo-skill", self.real_root / "SKILL.md")
        return root / "demo-skill"

    def _rel(self, base):
        return sorted(str(p.relative_to(base)) for p in base.rglob("*")
                      if p.is_file())

    def test_the_decoy_has_the_same_file_set(self):
        self.assertEqual(self._rel(self._decoy()), self._rel(self.real_root))

    def test_a_companion_file_carries_no_guidance(self):
        text = (self._decoy() / "references" / "rules.md").read_text(
            encoding="utf-8")
        self.assertNotIn("rule one", text)
        self.assertIn("placeholder", text)

    def test_the_skill_body_is_still_the_manipulated_variable(self):
        decoy = (self._decoy() / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("real body", decoy)
        self.assertIn("demo-skill", decoy, "the name must still resolve")

    def test_a_single_file_skill_is_unchanged_by_this(self):
        (self.real_root / "references" / "rules.md").unlink()
        (self.real_root / "references").rmdir()
        self.assertEqual(self._rel(self._decoy()), ["SKILL.md"])

    def test_nested_companion_directories_are_mirrored(self):
        deep = self.real_root / "references" / "deep" / "more.md"
        deep.parent.mkdir()
        deep.write_text("more\n", encoding="utf-8")
        self.assertIn("references/deep/more.md", self._rel(self._decoy()))


if __name__ == "__main__":
    unittest.main()
