---
proposal: (no docs/issue-2803/proposals/ entry found; probing the follow-up rename commit directly on issue #2803)
---

# Hunt record — role-to-skill-rename-comment-only

## after-proposal — stance 1: comment/docstring-only "role"→"skill" rename in test/test_spawn_attempt_staleness.py could plausibly break a docstring/comment-introspecting or grep-based consumer elsewhere

Verdict: NO FINDING
Seed: `git diff test/test_spawn_attempt_staleness.py` — 6 comment/docstring occurrences of "role family"/"role-family"/"role" changed to "skill family"/"skill-family"/"skill"; no assertions, test names, or code logic touched.
cap_seconds: unspecified (no dispatcher-provided cap in this prompt)
tier: default
diff_stat_lines: 1 file changed, 6 insertions(+), 6 deletions(-)
started_at: 2026-08-30T00:00:00Z
ended_at: 2026-08-30T00:15:00Z

### Reproduce

acceptance: `grep -rn "role" test/test_spawn_attempt_staleness.py` — result:
```
(no output)
```

acceptance: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result:
```
.........................................                                [100%]
41 passed in 0.85s
```

acceptance: `grep -rln "test_spawn_attempt_staleness\|SkillFamilyTest" test/*.py . --include=*.py 2>/dev/null | grep -v test_spawn_attempt_staleness.py` — result:
```
(no output)
```

acceptance: `grep -n "test_spawn_attempt_staleness\|_skill_family\|SkillFamilyTest" test/test_board_front_skill.py test/test_record_kind_field.py` — result:
```
(no output)
```
(these two files were the only repo-wide hits for `getdoc\|__doc__\|inspect.getsource` in `test/*.py`, via `grep -rln "getdoc\|__doc__\|inspect.getsource" test/*.py`)

acceptance: `grep -rln "doctest" --include=*.py . | xargs grep -l "test_spawn_attempt_staleness" 2>/dev/null` — result:
```
(no output)
```

canonical: `gates/record_lint.py:1457` — `"docs/issue-<n>/reports/<role>.md 형태여야 한다."` — the repo's only nearby "role" occurrence in lint tooling refers to the `<role>` filename slot in report paths, unrelated to this test file's prose.

### Observed

acceptance: (summary of the five commands above, this turn) — result:
```
target file: 0 remaining "role" occurrences
test/test_spawn_attempt_staleness.py: 41/41 tests green
repo-wide grep for the module name / SkillFamilyTest / doctest / docstring-introspection idioms against this file: 0 hits
```

### Expected
N/A — no finding.
