---
proposal: (none — CORE_BUILD_NOW bypass, uncommitted working-tree diff)
---

# Hunt record — skill-selection-followups

## before-landing — stance 0: assume the gate/filter just touched is bypassable — find the bypass

Verdict: FINDING — `_skill_declared_phrases()` (pipeline.py) reads the raw, unstripped frontmatter description and feeds consult.py's exact-phrase fast-path, so a quoted phrase living *inside* a skill's own "Do NOT use ..." clause is still returned as a positive declared trigger phrase and can silently auto-pick that skill (no judge review) for a task that merely echoes the phrase the author explicitly excluded — the very leak `_strip_negative_scope()` was added in this same diff to close for the BM25 index is left open on this sibling reader of the same field.
Kind: composition
Seed: uncommitted diff of pipeline.py/skills.py/spawn.py (`git diff -- pipeline.py skills.py spawn.py`) — adds `_strip_negative_scope()`/`_NEGATIVE_SCOPE_RE` and `_STATIC_POLICY_SKILLS`
cap_seconds: 120
tier: default
diff_stat_lines: 3 files changed (pipeline.py +26/-8, skills.py +28/-1, spawn.py +1)
started_at: 2026-08-24T00:00:00Z
ended_at: 2026-08-24T00:45:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2208-implementation
python3 - <<'EOF'
import sys, tempfile, shutil
sys.path.insert(0, '.')
from pathlib import Path
from unittest import mock
import consult, spawn, pipeline

tmp = Path(tempfile.mkdtemp())
skill_dir = tmp / "some-other-family-skill"
skill_dir.mkdir()
(skill_dir / "SKILL.md").write_text('''---
name: some-other-family-skill
description: >-
  Use when doing normal work for this family. Trigger on requests like
  "normal family trigger phrase". Do NOT use for "quick style tweaks only"
  (use ux-engineering-color-visibility instead).
---

# body
''', encoding="utf-8")

# 1) the guard this diff added strips the negative clause from the BM25 doc:
print("BM25 doc (stripped, correct):", pipeline._skill_bm25_document("some-other-family-skill", skill_dir))
# 2) but the declared-phrase extractor used by the exact-phrase fast path does NOT:
print("declared phrases (raw, leaks the negative clause):", pipeline._skill_declared_phrases(skill_dir))

task = "Please just do some quick style tweaks only on the button, nothing else needed here at all today"
with mock.patch.object(spawn, "_bm25_cross_family_scores",
                        return_value=[(1.0, "some-other-family-skill", skill_dir, "skill-repo")]):
    picked_dirs, outcome = consult._cross_family_skill_matches_with_consult(
        task, "some-role", None, issue=None, cwd=None, k=2)
print("picked_dirs:", picked_dirs)
print("outcome:", outcome)
shutil.rmtree(tmp)
EOF
```

This uses the exact "Do NOT use for \"...\" (use other-skill)" convention already present verbatim in the real skill-repository corpus (`skills/release-engineering-error-budget-policy/SKILL.md`: `Do NOT use to define what "healthy" means from scratch`), just with a quoted phrase long enough to clear `_skill_declared_phrases()`'s `>=8 chars or contains a space` filter (the real corpus's one instance, `"healthy"`, happens to be exactly 7 chars with no space, so it is coincidentally filtered out today — nothing in the code enforces that).

### Observed
```
BM25 doc (stripped, correct): some other family skill Use when doing normal work for this family. Trigger on requests like "normal family trigger phrase".
declared phrases (raw, leaks the negative clause): ['normal family trigger phrase', 'quick style tweaks only']
picked_dirs: [PosixPath('/tmp/.../some-other-family-skill')]
outcome: fast-path:some-other-family-skill
```
`_skill_declared_phrases()` returns `'quick style tweaks only'` — a phrase that only exists in the skill's own "Do NOT use" clause — as a legitimate declared trigger. `_cross_family_skill_matches_with_consult()` then auto-picks (`outcome == "fast-path:..."`) this skill for a task whose only overlap with the skill is that excluded phrase, with **no** `skill_judge` consult and no fail-open review — the exact bypass mode (BM25/declared-phrase self-inflation from the skill's own negative-scope text) issue #2208's own `_strip_negative_scope()` docstring says it exists to prevent, just via the sibling function that reads the same raw description field.

### Expected
`_skill_declared_phrases()` should extract quoted phrases from the same negative-scope-stripped text `_skill_bm25_document()` uses (i.e. call `_strip_negative_scope()` on the description before scanning for quoted phrases, or scan only the text before the "Do NOT use" clause), so a phrase that exists solely inside a skill's own "Do NOT use for X" exclusion can never become that skill's own fast-path auto-pick trigger.

### Fixed
canonical: pipeline.py `_skill_declared_phrases()`, added `desc = _strip_negative_scope(desc)` before the phrase scan. Repro script above re-run verbatim after the edit:
```
declared phrases (after fix): ['normal family trigger phrase']
outcome: fail-open
```
canonical: `python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=` re-run after the edit:
```
============================== 9 passed in 14.12s ==============================
```
