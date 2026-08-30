---
issue: 2811
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # this record independently verifies PR #2816, the deliverable for this subject
loop_state: landed
upstream:
  - path: spawn.py
    sha: c4f762a9ced3a97d04b8ae957edf8b526cbaa108
---

# issue-2811 — independent-verification-2 record

## What was done

Independently audited PR #2816 (`issue-2811/technical-writing-style-guide-compliance-ea5a2771`, still OPEN, not yet merged to `main`), which fixes the `role`/`role family` retired-noun vocabulary in `spawn.py:1399-1438`'s `_skill_family()`/`_attempt_superseded()` docstrings. Re-derived every load-bearing claim from local fetched refs of both the PR head and its merge-base, not from reading the PR's own record.

canonical: `gh pr view 2816` — state OPEN, base `3a9b424739cf32aed02180fbe6c5a4534f50e9d2` (this branch's own current HEAD), head commit `c4f762a9ced3a97d04b8ae957edf8b526cbaa108`.

**Check 1 — retired-noun grep over the changed range, before and after (issue's stated check):**
```
derived: git fetch origin pull/2816/head:pr-2816-check && git fetch origin main:refs-main-check
         git merge-base refs-main-check pr-2816-check
3a9b424739cf32aed02180fbe6c5a4534f50e9d2   (= this branch's own base, confirmed same commit)

derived: git show 3a9b4247:spawn.py | sed -n '1399,1438p' | grep -oinE '\brole\b' | wc -l
7

derived: git show pr-2816-check:spawn.py | sed -n '1399,1438p' | grep -inE '\brole\b'
(no output, exit 1 — zero matches)
```
Matches the PR's claim exactly: 7 occurrences before, 0 after.

**Check 2 — diff shape (must-not: no identifier renamed, no executable line touched):**
```
derived: git diff 3a9b4247 pr-2816-check -- spawn.py
1 file changed, 5 insertions(+), 5 deletions(-)
```
Read the full diff: all 10 changed lines sit inside the three `"""..."""` docstring blocks of `_skill_family()` and `_attempt_superseded()`; no `def`/`return`/`if` line, no identifier, appears in the diff. `git diff --stat 3a9b4247 pr-2816-check` shows only `spawn.py` changed by the code commit itself.

**Check 3 — full test suite before/after, compared as SETS OF TEST NAMES (issue's stated check):**
```
derived: git worktree add /tmp/wt-before 3a9b4247 && git worktree add /tmp/wt-after pr-2816-check
         (cd /tmp/wt-before && python3 -m pytest test/ --collect-only -q) | grep '::' | sort > before_names.txt
         (cd /tmp/wt-after  && python3 -m pytest test/ --collect-only -q) | grep '::' | sort > after_names.txt
         wc -l before_names.txt after_names.txt
443 before_names.txt
443 after_names.txt
         diff before_names.txt after_names.txt
(no output — identical sets)
```
443 collected both before and after; `diff` between the two sorted name lists is empty — identical sets, confirming the rename is inert.

**Check 4 — cross-repo sweep for the retired noun in prose describing a skill-named identifier (issue's stated check, "state the population and show the command"):**

on-the-record repo, re-run against the PR head:
```
derived: git ls-files '*.py' | grep -v -E '^(test|tests|spec)/' | grep -v -E '(^|/)test_[^/]*\.py$' | wc -l
127
derived: ...| xargs grep -lE '_skill_family|_attempt_superseded'
consult.py roster.py skills.py spawn.py
derived: ...| xargs grep -inE '\brole[ _-]family\b'
roster.py:595
spawn.py:1363
spawn.py:1372
```
Matches the PR's stated population (127) and both stated results exactly: the mechanism appears in 4 files, and `consult.py`/`skills.py`'s only hits are `resolve_skill_family_source` (the different, already-routed-to-#2561 mechanism per this issue's non-goals) — confirmed by `grep -nE '_skill_family|_attempt_superseded' consult.py skills.py`, both hits are `resolve_skill_family_source`. The 3 remaining `role[ _-]family` sites (`roster.py:595`, `spawn.py:1363`, `spawn.py:1372`) are outside the issue's stated `1399-1438` range and were correctly left unfixed and reported as open findings by the PR, not silently dropped.

tokenmaxxxer-core repo — **discrepancy found**:
```
derived: git -C "$CLAUDE_PLUGIN_ROOT_CORE" rev-parse --show-toplevel
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core
derived: cd <that toplevel> && git ls-files '*.py' | grep -v -E '^(test|tests|spec)/' | grep -v '/test_\|^test_'
core/hooks/lib/gate-lib.py
core/hooks/pretooluse_dispatcher.py
core/hooks/tests/gate-prose-coverage-check.py
scripts/extract-record-shape-config.py
warrant/hooks/lib/scope-gate.py
         (same command) | wc -l
5
```
canonical: `gh pr diff 2816` (read this session, output pasted in full at the top of "Upstream basis" below) — the PR's own record states this population as `3` files (`hooks/lib/gate-lib.py`, `hooks/pretooluse_dispatcher.py`, `hooks/tests/gate-prose-coverage-check.py`), labeled "tokenmaxxxer-core repo". Running the PR's own cited command from the actual git toplevel of that repo (confirmed via `git rev-parse --show-toplevel`, not `$CLAUDE_PLUGIN_ROOT_CORE`, which is only the `core/` subdirectory within it) returns `5` files, not `3` — the two extra files (`scripts/extract-record-shape-config.py`, `warrant/hooks/lib/scope-gate.py`) sit outside `core/` and were dropped because the command was evidently run scoped to `$CLAUDE_PLUGIN_ROOT_CORE` rather than the repo root the record names.

Checked whether this changes the sweep's substantive conclusion:
```
derived: grep -inE '_skill_family|_attempt_superseded' scripts/extract-record-shape-config.py warrant/hooks/lib/scope-gate.py
(no output, exit 1)
derived: grep -inE '\brole[ _-]family\b' scripts/extract-record-shape-config.py warrant/hooks/lib/scope-gate.py
(no output, exit 1)
derived: grep -inE '\brole\b' scripts/extract-record-shape-config.py warrant/hooks/lib/scope-gate.py
warrant/hooks/lib/scope-gate.py:122:    re.compile(r"^bash\s+\S+/(run-gate-lib-tests|run-role-gates-tests)\.sh" + SAFE_ARG + r"\s*$"),
```
Neither missing file contains the mechanism or `role family`; the one bare `role` hit is inside a shell-command regex literal (`run-role-gates-tests`), not prose describing a skill-named identifier, so it is not itself a finding under this issue's acceptance criterion. The sweep's zero-findings conclusion for tokenmaxxxer-core still holds under the corrected 5-file population — but the record's stated population count does not match what its own cited command actually returns from the repo it names, which is precisely the citation-accuracy failure mode this issue cluster (#2729, the 49-vs-34 population, the #2808 miscitation this issue itself fixes) is about, now recurring inside the very delivery meant to close it. Filed as an open finding below; does not change the verdict on the shipped `spawn.py` diff.

## Why

Independent verification means re-deriving each acceptance check from a fresh reference rather than trusting the PR's own quoted output — this is exactly what caught the tokenmaxxxer-core population discrepancy: the PR's own command, when actually re-run against the repo root it names (not the subdirectory the delivering session evidently ran it from), returns a different file count than stated. The underlying sweep conclusion (zero role/skill-family findings outside the fixed range, in that repo) is still correct, but the record's own citation does not support the number it states, which matters given this issue exists specifically because of prior citation failures in this cluster.

## What did not work

None.

## Upstream basis

- canonical: `gh pr view 2816` (read this session) — PR https://github.com/tokenmaxxxer/on-the-record/pull/2816, state OPEN, base `3a9b424739cf32aed02180fbe6c5a4534f50e9d2`, head `c4f762a9ced3a97d04b8ae957edf8b526cbaa108`, branch `issue-2811/technical-writing-style-guide-compliance-ea5a2771`.
- canonical: `gh pr diff 2816` (read this session) — the PR's own record, at path `docs/issue-2811/reports/technical-writing-style-guide-compliance-ea5a2771.md` (untracked in this branch's working tree — that path exists only on the unmerged PR #2816 branch at commit `c4f762a9ced3a97d04b8ae957edf8b526cbaa108`, same commit as the code); read here via `gh pr diff`, not a local path.
- canonical: `gh issue view 2811` (read this session) — issue tokenmaxxxer/on-the-record#2811, naming `spawn.py:1399-1438`, the 7-occurrence count, and the three acceptance checks re-run above verbatim.

## Open findings

- The PR's own record's tokenmaxxxer-core sweep-population citation (`3` files) does not match what its own cited command returns when run from the git toplevel of the repo it names (`5` files) — the command was evidently run scoped to `$CLAUDE_PLUGIN_ROOT_CORE` (the `core/` subdirectory) rather than the full `tokenmaxxxer-core` repo root.
  derived: `git -C "$CLAUDE_PLUGIN_ROOT_CORE" rev-parse --show-toplevel` then re-running the PR's exact cited command (`git ls-files '*.py' | grep -v -E '^(test|tests|spec)/' | grep -v '/test_\|^test_'`) from that toplevel — full commands and output above under "What was done" → Check 4. The two omitted files (`scripts/extract-record-shape-config.py`, `warrant/hooks/lib/scope-gate.py`) contain neither the mechanism nor `role family` nor any prose-context `role`, so the sweep's zero-findings conclusion is unaffected in substance — this is a citation-accuracy defect, not a missed finding. Does not block the PR's core deliverable (the `spawn.py` prose fix), which is independently verified correct above. Resolution path: the PR's author (or a follow-up) corrects the population count and file list in that record's cross-repo sweep section before/if this delivery lands, or files a note acknowledging the discrepancy.

## Next steps

None — `loop_state: landed`.

derived: this record's own "What was done" section, Checks 1-4 (re-run this session against `spawn.py` at commits `3a9b424739cf32aed02180fbe6c5a4534f50e9d2` and `c4f762a9ced3a97d04b8ae957edf8b526cbaa108`, and against both repos' `git ls-files` sweeps) — result: 7→0 `role` occurrences in the `1399-1438` range, identical 443-name `pytest --collect-only` sets before/after, on-the-record sweep population 127 files with 4 mechanism files and 3 correctly-deferred `role family` sites outside range — all match the PR's claims exactly. The PR's own record additionally claims a 3-file population for the tokenmaxxxer-core sweep; derived: re-running its exact cited command from that repo's actual git toplevel (Check 4 above) — result: 5 files, not 3 (see Open findings), a citation-accuracy defect that does not change the sweep's substantive zero-findings result. `verifies_subject: true` because this record independently re-derived and confirms the PR's core deliverable (the `spawn.py` docstring fix and its stated test/range acceptance checks) is correct.

## Skill verdicts

- skill-verdict: work-in-english — applied: invoked; used for the duration of this session — all repository-bound artifacts (this record, prior tool commands, eventual commit/PR text) authored in English per the skill's scope, final user-facing summary in Korean.
