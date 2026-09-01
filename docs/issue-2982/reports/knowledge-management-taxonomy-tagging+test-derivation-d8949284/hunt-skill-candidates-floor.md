---
proposal: docs/issue-2982/proposals/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md
---

# Hunt record — skill-candidates-floor

## before-landing — stance 0: assume the gate/check just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: git diff main...HEAD (consult.py rank_skills(), spawn.py _SKILL_CANDIDATES_RELEVANCE_FLOOR re-export, test/test_skill_candidates_ranking.py, tests/test_skill_candidates_floor.py)
cap_seconds: 180
tier: size:large
diff_stat_lines: ~248 non-docs lines across 4 files
started_at: 2026-09-01T00:00:00Z
ended_at: 2026-09-01T00:20:00Z

Checked for a code path where use_judge=False (the --skill-candidates default) still returns outcome="bm25-only" with a populated ranked list even though the top BM25 score is under the calibrated floor (16.0):
- Confirmed `scored.sort(key=lambda t: (-t[0], t[1]))` in directive_assembly._bm25_cross_family_scores(), so `scored[0][0]` really is the max score fed to the floor check — no ordering bug to exploit.
- Ran the actual CLI (`python3 spawn.py --skill-candidates "<task>"`) against the live ~270-skill corpus for: pure gibberish, and both regression tasks quoted in tests/test_skill_candidates_floor.py (workspace-preservation predicate rewrite; 200-turn-cap removal). All three correctly returned `{"ranked": [], "outcome": "no-candidates", "picked": []}` — floor holds in the real CLI path, not just in the mocked unit tests.
- Tried an adversarial long jargon-soup query (many distinct generic engineering terms) to see if summed per-token idf could push an irrelevant top-1 over 16.0; still filtered to no-candidates. `_tokenize()` (pipeline.py) returns a `set`, so repeating one token in the query cannot inflate its BM25 contribution (no query-term-frequency amplification to exploit).
- Verified `consult.rank_skills()` reads the floor via `_sp._SKILL_CANDIDATES_RELEVANCE_FLOOR` (spawn.py`s copy, bound at spawn import time), not the local `consult._SKILL_CANDIDATES_RELEVANCE_FLOOR`. This looks like a two-copies-of-one-constant trap at first read, but it is the exact same shape already used by three pre-existing sibling constants in this file (`_LEDGER_TAIL_READ_BYTES`, `_MIN_PLAUSIBLE_JUDGE_WALL_S`, `_SKILL_JUDGE_PERF_MIN_EVENTS` — each defined once in consult.py, re-exported by assignment in spawn.py, referenced at runtime via `_sp.<name>`), and the file`s own top-of-module docstring names this as the deliberate patching-compat convention (`mock.patch.object(spawn, "<name>")` is the intended seam). Patching `consult._SKILL_CANDIDATES_RELEVANCE_FLOOR` directly is a no-op for rank_skills() at runtime, exactly as it is for the three sibling constants — confirmed by direct repro (patching `consult._SKILL_CANDIDATES_RELEVANCE_FLOOR = 0.0` left `spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR` and rank_skills() behavior unchanged). Since this is the established, consistently-applied convention rather than something unique to this diff, it is not reported as a finding.
- The documented non-goal (use_judge=True / `--with-judge` bypasses the floor entirely, and spawn`s own internal cross-family mount via `_cross_family_skill_matches_with_consult()` never passes through rank_skills() at all) is explicit in both the code comment and the docstring added by this diff, not a silent/hidden bypass — did not chase it further as a "finding" since it is disclosed, not invisible.

No reproducible bypass found: could not get a low-confidence/irrelevant BM25 top-1 to surface as outcome="bm25-only" with a populated ranked list through any use_judge=False path, real CLI invocation, or corpus-shape variation tried within the cap.
