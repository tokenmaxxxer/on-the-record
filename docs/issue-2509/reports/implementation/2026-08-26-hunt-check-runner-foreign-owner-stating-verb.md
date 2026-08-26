---
proposal: docs/issue-2509/reports/implementation.md
---

# Hunt record — check-runner-foreign-owner-stating-verb

## before-landing — stance 1: silent misclassification of genuinely-local paths as foreign-owned judgment

Verdict: FINDING — `_FOREIGN_OWNER` matches generic English possessives ("the other tool's", "another module's") that do not imply the path lives outside this repo, silently downgrading a genuinely-missing in-repo `gates/...` path assertion from `file-existence` (mechanical FAIL) to `judgment` (out of scope, never checked)
Kind: silent-failure
Seed: git diff HEAD -- gates/check_runner.py gates/test_check_runner.py (uncommitted, ~90 lines touched: new `_FOREIGN_OWNER`/`_STATING_VERB_PREFIX` regexes + `len(tokens) == 1` file-existence guard in parse_checks(), plus 6 new tests in gates/test_check_runner.py)
cap_seconds: n/a (not provided by dispatcher)
tier: n/a (not provided by dispatcher)
diff_stat_lines: 2 files changed, ~104 insertions(+), 2 deletions(-) (git diff --stat)
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T00:30:00Z

### Reproduce
```
python3 -m pytest gates/test_check_runner.py -q   # 44 passed, confirms baseline is green
python3 -c "
import sys; sys.path.insert(0,'gates')
import check_runner

section_a = '''
- check: the \`gates/definitely_missing_dir_xyz\` layout is unchanged
'''
section_b = '''
- check: the other tool's \`gates/definitely_missing_dir_xyz\` layout is unchanged
'''
print('without foreign-owner phrase:', check_runner.parse_checks(section_a))
print('with foreign-owner phrase:   ', check_runner.parse_checks(section_b))
"
```

### Observed
```
without foreign-owner phrase: [{'type': 'file-existence', 'raw': 'the `gates/definitely_missing_dir_xyz` layout is unchanged', 'path': 'gates/definitely_missing_dir_xyz'}]
with foreign-owner phrase:    [{'type': 'judgment', 'raw': "the other tool's `gates/definitely_missing_dir_xyz` layout is unchanged"}]
```
Adding the phrase "the other tool's" immediately before the backtick — ordinary English that, in this bullet, refers to nothing outside this repository (the path is `gates/...`, a real top-level directory of this very repo) — flips the classification from `file-existence` (which would mechanically FAIL because the directory genuinely does not exist) to `judgment`, which `parse_checks`'s own docstring says is "이 러너의 범위 밖" (out of this runner's scope) and is never mechanically executed. The same happens for "another module's", "another project's", "another package's", all of which the `_FOREIGN_OWNER` alternation admits, and all of which are ordinary phrasings for something else *inside the same repository*, not necessarily an installed plugin or a different consuming/target repo.

### Expected
`_FOREIGN_OWNER` is meant to catch bullets describing a path that lives in a genuinely different repository/plugin/target checkout (the issue #2488 live cases: "installed plugin's `skills/`", "target repo's `.claude/skills`"). It should not fire on generic same-repo possessives ("another module's", "the other tool's") that happen to precede a path that is unambiguously local to this repo (e.g. starts with a real top-level directory name like `gates/`). As written, a genuinely-missing in-repo path can be silently exempted from the mechanical file-existence check merely by phrasing the bullet with "another X's" — the check_runner then never verifies (or fails) it, and the PR comment gives no indication this happened; the check bullet still shows the raw text with the backticked path unchanged.
