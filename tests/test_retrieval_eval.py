"""Issue #2124 part 4: offline retrieval eval for the cross-family skill
recommender — pure python, no network, no model calls.

Gold set: tests/data/retrieval_gold.jsonl (frozen; each case documents the
judgment behind its expected set). Two measured stages:

- BM25 stage: `spawn._bm25_cross_family_scores` top-8 (the candidate slate the
  judge sees) — Recall@8 and MRR per case. Recall@8 must be 1.0 for every
  case with a non-empty expected set (the dicequest #72 live case regressed
  to 0 under the old single-trigger-sentence documents).
- Final-pick stage: `_cross_family_skill_matches_with_consult` with the judge
  mocked as an oracle (picks expected∩candidates) — exercises the
  exact-phrase fast path + cap plumbing; precision/recall over final picks.

Runs against the real skill-repository checkout (`spawn._skill_repo_root()`);
skipped when no checkout is installed (keeps CI hermetic). The installed-
plugin tier is patched out so the corpus is exactly the skill repo —
deterministic regardless of what plugins this machine has."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

GOLD_PATH = Path(__file__).parent / "data" / "retrieval_gold.jsonl"
TOPN = 8
K = 2


def _load_gold():
    return [json.loads(line)
            for line in GOLD_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class RetrievalEvalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = spawn._skill_repo_root()
        if cls.repo_root is None or not cls.repo_root.is_dir():
            raise unittest.SkipTest("no skill-repository checkout installed")
        cls.gold = _load_gold()
        # Every expected skill must exist in the corpus — a frozen gold set
        # naming a renamed/removed skill should fail loudly, not eval to 0.
        for case in cls.gold:
            for name in case["expected"]:
                if not (cls.repo_root / name / "SKILL.md").is_file():
                    raise unittest.SkipTest(
                        f"gold skill {name} missing from checkout")

    def _patched(self):
        # Corpus = skill-repo tier only (deterministic on any machine).
        return mock.patch.object(spawn, "_installed_plugin_skill_dirs",
                                 lambda: {})

    def test_gold_set_frozen_shape(self):
        self.assertGreaterEqual(len(self.gold), 10)
        for case in self.gold:
            self.assertIn("id", case)
            self.assertIn("role", case)
            self.assertIn("task", case)
            self.assertIsInstance(case["expected"], list)
            self.assertTrue(case["note"])

    def test_bm25_recall_at_8_and_final_pick_metrics(self):
        rows = []
        recall_sum = prec_sum = mrr_sum = 0.0
        nonempty = 0
        with self._patched():
            for case in self.gold:
                expected = set(case["expected"])
                scored = spawn._bm25_cross_family_scores(
                    case["task"], case["role"], self.repo_root)
                top = [name for _s, name, _d, _src in scored[:TOPN]]
                ranks = [i + 1 for i, n in enumerate(
                    name for _s, name, _d, _src in scored) if n in expected]
                mrr = 1.0 / ranks[0] if ranks else 0.0
                recall8 = (len(expected & set(top)) / len(expected)
                           if expected else None)

                # Final-pick stage: oracle judge = expected ∩ candidates.
                def oracle(task_text, role, candidates, issue, cwd,
                           model=None, max_picks=K, _exp=expected):
                    picked = [d for n, d, _src in candidates
                              if n in _exp][:max_picks]
                    return picked, {"picked": [d.name for d in picked],
                                    "rejected": [], "reasons": {}}
                with mock.patch.object(spawn, "_skill_judge_consult", oracle):
                    picked_dirs, outcome = (
                        spawn._cross_family_skill_matches_with_consult(
                            case["task"], case["role"], self.repo_root,
                            None, None, k=K))
                picked = {d.name for d in picked_dirs}
                tp = len(picked & expected)
                precision = tp / len(picked) if picked else (
                    1.0 if not expected else 0.0)
                recall_final = tp / len(expected) if expected else 1.0
                rows.append((case["id"], recall8, mrr, precision,
                             recall_final, outcome))
                if expected:
                    nonempty += 1
                    recall_sum += recall8
                    mrr_sum += mrr
                prec_sum += precision

        hdr = (f"{'case':38} {'R@8':>5} {'MRR':>5} {'P':>5} {'R':>5}  outcome")
        print("\n" + hdr)
        for cid, r8, mrr, p, r, outcome in rows:
            print(f"{cid:38} {('-' if r8 is None else f'{r8:.2f}'):>5} "
                  f"{mrr:.2f} {p:5.2f} {r:5.2f}  {outcome}")
        print(f"macro (non-empty n={nonempty}): "
              f"Recall@8={recall_sum / nonempty:.3f} "
              f"MRR={mrr_sum / nonempty:.3f} | "
              f"final-pick precision (all n={len(rows)})="
              f"{prec_sum / len(rows):.3f}")

        # Frozen assertions: every non-empty gold case is fully recalled in
        # the judge's top-8 slate, and the oracle-judged final picks recall
        # every expected skill (cap K=2 >= max expected-set size).
        for cid, r8, _mrr, _p, r, _o in rows:
            if r8 is not None:
                self.assertEqual(r8, 1.0, f"Recall@8 < 1.0 for {cid}")
                self.assertEqual(r, 1.0, f"final-pick recall < 1.0 for {cid}")

    def test_fast_path_verbatim_phrase_autopicks_without_judge(self):
        """Acceptance (b): a task text carrying a skill's declared quoted
        phrase verbatim injects that skill even when the judge is disabled
        (mocked to raise, i.e. the fail-open path)."""
        case = next(c for c in self.gold
                    if c["id"] == "dicequest-72-monster-scaling")

        def broken_judge(*a, **kw):
            raise RuntimeError("skill_judge disabled")
        with self._patched(), \
                mock.patch.object(spawn, "_skill_judge_consult", broken_judge):
            picked_dirs, outcome = (
                spawn._cross_family_skill_matches_with_consult(
                    case["task"], case["role"], self.repo_root,
                    None, None, k=K))
        names = [d.name for d in picked_dirs]
        # "per-stage monster damage/HP scaling" is a declared phrase of
        # game-growth-system-design and appears verbatim in the task text.
        self.assertIn("game-growth-system-design", names)
        self.assertTrue(outcome.startswith("fast-path:"), outcome)
        self.assertIn("game-growth-system-design", outcome)
        self.assertLessEqual(len(names), K)


class HermeticEnrichmentAndFastPathTest(unittest.TestCase):
    """Fixture-skill tests that need no skill-repository checkout — the
    document-enrichment extractors (part 1) and the exact-phrase fast path
    (part 2) stay covered in a hermetic CI."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self._plug = mock.patch.object(spawn, "_installed_plugin_skill_dirs",
                                       lambda: {})
        self._plug.start()
        self.addCleanup(self._plug.stop)

    def _skill(self, name, description, axis=None):
        d = self.root / name
        d.mkdir(parents=True)
        meta = f"metadata:\n  axis: {axis}\n" if axis else ""
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: >-\n  {description}\n{meta}---\n",
            encoding="utf-8")
        return d

    def test_bm25_document_carries_description_name_and_axis(self):
        d = self._skill("game-growth-system-design",
                        "Use when scaling monster HP across stages. Trigger "
                        'on requests like "per-stage monster damage/HP '
                        'scaling". Do NOT use for reward loops.',
                        axis="growth-system-design")
        doc = spawn._skill_bm25_document("game-growth-system-design", d)
        for tok in ("game", "growth", "system", "design", "monster",
                    "scaling", "stages"):
            self.assertIn(tok, spawn._tokenize(doc))

    def test_document_falls_back_to_name_tokens_without_description(self):
        d = self.root / "bare-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: bare-skill\n---\n",
                                    encoding="utf-8")
        self.assertEqual(spawn._skill_bm25_document("bare-skill", d),
                         "bare skill")

    def test_declared_phrases_are_quoted_and_short_words_dropped(self):
        d = self._skill("s", 'Trigger on "upgrade cost curve", "band", '
                             '"balance derivation".')
        self.assertEqual(spawn._skill_declared_phrases(d),
                         ["upgrade cost curve", "balance derivation"])

    def test_fast_path_autopicks_on_verbatim_phrase_judge_never_called(self):
        self._skill("game-growth-system-design",
                    'Use when scaling monsters. Trigger on "per-stage '
                    'monster damage/HP scaling".')
        self._skill("other-skill",
                    'Use when scaling widgets. Trigger on "widget scaling".')
        calls = []

        def judge(task_text, role, candidates, issue, cwd, model=None,
                  max_picks=2):
            calls.append([n for n, _d, _s in candidates])
            return [], {"picked": [], "rejected": [], "reasons": {}}
        with mock.patch.object(spawn, "_skill_judge_consult", judge):
            picked, outcome = spawn._cross_family_skill_matches_with_consult(
                "Implement Per-Stage Monster Damage/HP Scaling for stage 6.",
                "implementation", self.root, None, None, k=2)
        self.assertEqual([d.name for d in picked],
                         ["game-growth-system-design"])
        self.assertEqual(outcome,
                         "fast-path:game-growth-system-design+completed")
        # Judge consulted only for the remaining slot, without the fast pick.
        self.assertEqual(calls, [["other-skill"]])

    def test_fast_path_filling_cap_skips_judge_entirely(self):
        self._skill("skill-a", 'Trigger on "alpha beta gamma".')
        self._skill("skill-b", 'Trigger on "delta epsilon zeta".')

        def judge(*a, **kw):
            raise AssertionError("judge must not be consulted")
        with mock.patch.object(spawn, "_skill_judge_consult", judge):
            picked, outcome = spawn._cross_family_skill_matches_with_consult(
                "alpha beta gamma then delta epsilon zeta please",
                "implementation", self.root, None, None, k=2)
        self.assertEqual([d.name for d in picked], ["skill-a", "skill-b"])
        self.assertEqual(outcome, "fast-path:skill-a,skill-b")


if __name__ == "__main__":
    unittest.main()
