---
issue: 2139
role: refactoring-legacy-seam-selection+adversarial-review-1f7845d2
author: refactoring-legacy-seam-selection+adversarial-review-1f7845d2
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR #2883 (branch issue-2139/adversarial-review-64149232, commits d0682205, 7e21537d)
    sha: d06822058b0425bcf638c8c92bf1c3ab87de95de
---

# issue-2139 — refactoring-legacy-seam-selection+adversarial-review-1f7845d2 record

## What was done

Rebased PR #2883's substantive code changes onto current `origin/main` and delivered them on this branch instead. PR #2883 (67h old, three-way conflict on `roster.py`/`skills.py`/`watchdog.py` when merged directly) carries two commits: a mechanical `role`→`skill` wording/dead-name-reference cleanup batch across 12 files, plus a deviation-log-only commit with no code content.

Extracted PR #2883's real diff by diffing its head against its own merge-base with `main` (`git merge-base main pr2883-head` = `6003d3d4`), not against current `main` directly — a direct `main`..PR diff is dominated by ~43,700 lines of unrelated deletions/re-additions from `main` having advanced 67h past the branch point (hundreds of `docs/issue-*/reports/*` files, retired hooks, retired gates — none of it PR #2883's own content). The real diff is 41 changed lines across 12 files: `board.py`, `consult.py`, `events.py`, `gates/ci.py`, `gates/patrol_wiring.py` (untracked — deleted from `main`, see below), `on-the-record/directive/delegation-loops.md`, `pipeline.py`, `relay.py`, `roster.py`, `skills.py`, `spawn.py`, `watchdog.py`.

canonical: a Python script diffed each of PR #2883's 41 removed (old-wording) lines against (a) `git show HEAD:<file>` (current `main`, before this session's edit) and (b) the working tree after this session's edit, per file — this session's own executed output:
```
('board.py', 4, True, 1, True, 0)
('consult.py', 10, True, 0, True, 0)
('events.py', 2, True, 0, True, 0)
('gates/ci.py', 4, True, 0, True, 0)
('gates/patrol_wiring.py', 1, False, 0, False, 0)
('on-the-record/directive/delegation-loops.md', 3, True, 0, True, 0)
('pipeline.py', 2, True, 0, True, 0)
('relay.py', 4, True, 0, True, 0)
('roster.py', 1, True, 0, True, 0)
('skills.py', 2, True, 0, True, 0)
('spawn.py', 5, True, 0, True, 0)
('watchdog.py', 3, True, 0, True, 0)
TOTAL before: 1  after: 0
```
(tuple = filename, hunk-line-count, exists-in-HEAD, before-hits, exists-in-worktree, after-hits)

Of PR #2883's 41 target old-wording lines, only 1 was still literally present on current `main`: `board.py`'s `roster_ps()` docstring, `"돌고 있는 역할 세션 없음"과 구분 없이 찍혔다` (describing legacy pre-#2203 print behavior). Applied that one wording fix (`역할`→`스킬`) — `board.py:1454`. The other 40 target lines were already gone from `main` before this session started, independently of PR #2883, for two distinct reasons (both verified per-line, not assumed):
- 39 lines: already fixed by earlier `role`→`skill` wording/comment/docstring-vocabulary passes that landed on `main` after PR #2883's branch point. derived: `git log --oneline -i --all --grep="role.*skill" -- consult.py spawn.py relay.py skills.py roster.py pipeline.py board.py watchdog.py gates/ci.py events.py` — shows `0fd0c914`/`ee7c8c92` "issue-2600: retire teaching-current-model 'role'/역할 wording from comments and docstrings" and `ec629890` (#2816) "issue-2811: fix retired-noun docstring vocabulary in spawn.py" among the commits touching these exact files with role→skill wording intent, landed after PR #2883's merge-base `6003d3d4`.
- 1 line (`gates/patrol_wiring.py`'s stale-constant-name comment): the entire file is untracked on current `main` — deleted by commit `bd8d5f4d` (#2954, "rebase patrol-program removal onto main"). derived: `git log -3 --stat -- gates/patrol_wiring.py` — top entry `bd8d5f4d4cb9d81845b21336eb9f2a35683a4b5d`, `gates/patrol_wiring.py | 142 -------------------------------------------------`, `1 file changed, 142 deletions(-)`; `git ls-files gates/patrol_wiring.py` on current tree returns nothing. The patrol program itself was retired, so the comment PR #2883 wanted to reword no longer exists anywhere to reword.

## Why

Per the task: keep `main`'s current content as the base, and re-apply only the wording changes still needed, dropping any hunk whose target string is already fixed or gone rather than force-applying PR #2883's stale diff (which is what produced the three-way conflict on `roster.py`/`skills.py`/`watchdog.py` in the first place — those files' surrounding lines had all shifted). A mechanical `git apply` of the extracted 12-file/41-line patch was tried first and failed on every file (context-line drift from the 67h of intervening commits), confirming a hunk-by-hunk manual re-check against current file content was necessary rather than a blind patch/merge.

## What did not work

- `git apply --check` of the extracted PR #2883 diff (base `6003d3d4`..`pr2883-head`, scoped to the 12 target files) failed on all 12 files with context-mismatch errors — every file had shifted enough since the branch point that none of the original hunks could locate their anchor lines, even for hunks whose target string was still literally present (`board.py`). derived: `git apply --check --verbose /tmp/pr2883.patch` — result: `error: 패치 실패: board.py:898` / `error: board.py: 패치를 적용하지 않습니다` and equivalent failures for all 12 files (`consult.py:24`, `events.py:505`, `gates/ci.py:498`, `on-the-record/directive/delegation-loops.md:11`, `pipeline.py:269`, `relay.py:61`, `roster.py:183`, plus `gates/patrol_wiring.py` reporting the file itself untracked). Confirms the task's premise that a raw merge/cherry-pick would conflict broadly, not just on the three files reproduced in the merge attempt (`roster.py`/`skills.py`/`watchdog.py`) — used the mechanical line-presence check above instead.

## Upstream basis

- PR #2883, commit `d06822058b0425bcf638c8c92bf1c3ab87de95de` ("issue-2139: relic-sweep cleanup batch — role->skill wording fixes + fix-issue recommendations") — source of the 41-line/12-file wording diff this session re-derived and selectively re-applied. Real 40-char sha (not same-commit): this PR's branch (`issue-2139/adversarial-review-64149232`) is a different, still-open session's work, fetched read-only via `git fetch origin pull/2883/head`.
- Issue #2139 comment (2026-08-30, "Round 2 landed — cleanup PR + fix-issue recommendations"), read via `gh issue view 2139 --comments` this session — names PR #2883 and its two recommended-not-filed follow-ups, both out of scope for this rebase (see Open findings).

## Open findings

- `on-the-record/directive/delegation-loops.md`'s "the matching skill's rulebook loaded" phrase — PR #2883 wanted `rulebook`→`guidance`. On current `main` this line already reads "the matching skill's skill loaded" (a different, independent rewrite landed after PR #2883 branched), which is grammatically awkward (repeats "skill") but is not the string PR #2883 targeted. derived: `grep -n "rulebook\|guidance loaded" on-the-record/directive/delegation-loops.md` — result: no match (both terms absent); `sed -n '14p' on-the-record/directive/delegation-loops.md` — result: `` `<n>]` — the matching skill's skill loaded, judgment rendered, answer returned as ``. PR #2883's specific replacement was dropped as moot rather than force-applied over the newer wording. Not fixed here — copyediting a wording nobody flagged as retired-vocabulary is outside this rebase's scope (re-applying PR #2883's own changes, not a fresh sweep). Resolution path: a future pass can reword it directly (e.g. "the matching skill's own skill-specific guidance loaded") if picked up.
- The two follow-ups PR #2883's body recommended but did not file (`spawn.py:4006`'s `role-skill-triggers` directive-diet label; `directive_assembly.py`'s `_RECORD_SKELETON` `role:` frontmatter key) are not code diffs — they were prose recommendations in the PR description, not part of the 41-line patch, so nothing to rebase. Still open; resolution path is the operator filing them as separate issues per PR #2883's own recommendation.
- `board.py:1449`, same function's docstring, still reads `` `ROSTER`(`issue-<n>/<role>` 키) `` — same retired `<role>` vocabulary as the line just fixed, but not a line PR #2883's diff touched. Left as-is: this delivery's scope is re-applying PR #2883's own changes, not a fresh sweep of the file (issue #2139's broader sweep already covers this class of finding through its own evidence-comment process).

## Next steps

None for this delivery. loop_state: landed.

## Acceptance verification

acceptance: `python3 -m pytest gates/ -q` — result:
```
46 passed
```
acceptance: `python3 -m py_compile board.py` — result: clean, exit 0
canonical: retired-vocabulary sweep count (PR #2883's own 41 target lines, 12 files), this session's own executed script output quoted verbatim in "What was done" above — before this session: 1 line still present (`board.py`); after: 0.

### Skill verdicts

skill-verdict: refactoring-legacy-seam-selection — not-applicable: this delivery is a mechanical wording/vocabulary rebase (re-applying an existing PR's comment/docstring/string-literal fixes onto a moved `main`) with no new behavior introduced into legacy code and no seam/Sprout-vs-Wrap decision to make.
skill-verdict: adversarial-review — not-applicable: no AI-made artifact needed a structurally-independent fresh-context evaluation here; the task's own verification (mechanical old-line-presence diff against `main`, plus `pytest gates/`) is a direct, checkable derivation, not a self-report needing a second opinion.
other mounted skills: not triggered
