---
issue: 2600
role: adversarial-review-219e8ec6
author: adversarial-review-219e8ec6
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2731's deliverable
loop_state: landed
code_under_review: e16ddf98f6e848e58c7908697465e0b3e856ae58
type: verification
breaking: false
verdict: CONFIRMED — the failing-test set is identical to origin/main modulo exactly the one claimed legitimate rename; the diff touches only Python/shell identifiers (persisted JSON keys, the CLI flag string, env var name, filenames, and the GH label prefix are all preserved literally); no cross-repo-shared identifier that tokenmaxxxer-core reads was renamed; docs/ is untouched relative to the PR's true merge-base; approval-gate.sh's exclusion is real, complete, and its stated reason holds; no compatibility alias was introduced. One immaterial deviation found: 7 comment lines were edited, each solely to keep a cross-reference in sync with a function that was genuinely renamed at its definition site (not prose rewriting).
upstream:
  - path: PR tokenmaxxxer/on-the-record#2731 (branch issue-2600/refactoring-legacy-seam-selection+refactoring-legacy-verification-cadence+adversarial-review-4c7357a0)
    sha: e16ddf98f6e848e58c7908697465e0b3e856ae58
---

# issue-2600 — adversarial-review-219e8ec6 record

## What was done

Independent re-derivation of every negative claim in PR #2731 (issue #2600
slice 4: rename every remaining `role`/`Role`/`ROLE`/`roles` **Python and
shell identifier** to `skill`/`Skill`/`SKILL`/`skills` in on-the-record,
1143 identifier-kind occurrences across 64 files). Two worktrees were built
from a fresh clone state — `/tmp/pr2731-verify` at the PR head
(`e16ddf98`) and `/tmp/main-baseline` at `origin/main`
(`8b2cab50`) — and every claim below was re-run against those trees rather
than read from the PR body.

skill-verdict: adversarial-review — applied: invoked; this whole task is the
adversarial-review shape (structurally independent evaluator re-deriving a
builder's claims from the PR head alone, incentivized to find what's wrong)
— every command in this record was run by me against the PR head/baseline,
not read off the PR description.
skill-verdict: work-in-english — applied: invoked; this record, all commit
messages and the PR body were written in English; only the final chat
summary to the user is in Korean.

### Check 1 — Failing-test set (PR head vs origin/main), as sets of names

```
cd /tmp/pr2731-verify && python3 -m pytest -m "not slow" -q 2>&1 | grep '^FAILED' | sort > /tmp/pr_failed.txt
cd /tmp/main-baseline  && python3 -m pytest -m "not slow" -q 2>&1 | grep '^FAILED' | sort > /tmp/main_failed.txt
diff /tmp/main_failed.txt /tmp/pr_failed.txt
wc -l /tmp/main_failed.txt /tmp/pr_failed.txt
```
derived: the two commands above, run directly against the two worktrees this turn.
canonical: pytest's own summary line, both runs read `16 failed, 529 passed, 6 xfailed`; `diff` output:
```
15c15
< FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo
---
> FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
```
Re-derived the claimed cause:
```
git diff origin/main pr2731-head -- test/test_spawn_skill_judge_haiku_timeout_overlap.py | sed -n '95,140p'
```
canonical: that hunk (read directly, `test/test_spawn_skill_judge_haiku_timeout_overlap.py:381-403` on the PR head) renames only the test's own method name
(`test_..._when_role_source_is_not_skill_repo` →
`test_..._when_skill_source_is_not_skill_repo`) and the local variable
`role_source`/`skill_source` used inside it and passed through
`mock.patch.object` calls — no assertion or mocked-return-value logic
changed.
Outcome: the failing-test set is unchanged except for that one legitimate
identifier rename; all 16 failures on both sides are pre-existing
sandbox-environment failures (`git fetch` against `origin` inside a
sandboxed temp repo has no such remote) unrelated to this diff.
acceptance: `diff /tmp/main_failed.txt /tmp/pr_failed.txt` — result: single-line diff shown above, both files 16 lines.

### Check 2 — diff touches only identifiers, checked in both directions

Full non-docs diff pulled once:
```
git diff origin/main pr2731-head -- . ':!docs' > /tmp/full_pr_diff.txt
git diff --stat origin/main pr2731-head -- . ':!docs' | tail -1
```
derived: above command — result: `64 files changed, 1006 insertions(+), 1006 deletions(-)` (2140 changed `[+-]` lines by `grep -c`), file count matches the PR's claim of 64.

- Persisted dict/JSON keys: `derived: grep -nE '^[+-].*"(role|Role|ROLE|roles)"\s*:' /tmp/full_pr_diff.txt | grep -v '"role":'` — result: only two `"roles":` key lines, both with the key itself unchanged (`{"step": step_n, "roles": roles, "done": done}` → `{"step": step_n, "roles": skills, "done": done}` at `board.py`), only the value variable renamed. No dict/JSON key was ever renamed.
- CLI flag string: `derived: grep -nE '^\+.*--(role|skill)\b|^-.*--(role|skill)\b' /tmp/full_pr_diff.txt` — result: 3 hits, all `_arg(rest, "--role")` / `"--role", role` sites (`board.py`, `spawn.py`); the literal `"--role"` text is byte-identical on both sides of every hunk, only the variable it's assigned to (`role`→`skill`) changed.
- Env var name: `derived: grep -inE '^[+-].*(os\.environ|getenv)' /tmp/full_pr_diff.txt | grep -iE 'role|skill'` — result: 7 hits, all `os.environ["CLAUDE_SKILL"]`/`os.environ.get("CLAUDE_SKILL")`; `CLAUDE_SKILL` was already the env var name pre-PR. `derived: grep -rn "CLAUDE_ROLE" /tmp/pr2731-verify --include="*.py" --include="*.sh"` — result: zero hits.
- Persisted filenames: read directly in the diff context lines — `spawn.py`'s renamed constant `SKILL_MODEL_CONFIG = ROOT / "role_model.txt"` (identifier renamed, string value untouched) and `spawn.py`'s `os.path.join(..., ".on-the-record", "role.json")` (unchanged on both sides, confirmed by `derived: grep -n 'role_model\|role.json' /tmp/full_pr_diff.txt` showing these only on unchanged/context lines).
- GH label / approval-needle formats: `f"role:{role}"` → `f"role:{skill}"` in `gates/patrol_board.py` and `gates/patrol_promote.py` (label prefix literal `"role:"` unchanged, only the interpolated variable renamed); the approval needle format lives only in `approval-gate.sh`, which is untouched (see Check 5).
- Compatibility-alias check (reverse direction): `derived: grep -nE '^\+\s*(role|Role|ROLE)\s*=\s*(skill|Skill|SKILL)\b' /tmp/full_pr_diff.txt` and the reverse pattern, plus `grep -nE '^\+.*def (role|get_role|role_)\(' /tmp/full_pr_diff.txt` — result: zero hits in all three.
- **Exception found and traced**: `derived: grep -nE '^-\s*#.*\brole\b' /tmp/full_pr_diff.txt -i` and `grep -nE '^\+#|^\+\s+#' /tmp/full_pr_diff.txt | grep -iE 'role|skill'` — result: together surface 8 comment-line edits (1 in `on-the-record/hooks/contract-guard.sh`, 7 in `.py` files). Checked each named symbol against its actual definition site, read live on the PR head:
  - `_approved_roles_on_issue`→`_approved_skills_on_issue`, defined at `gates/ci.py:226`
  - `fetch_all_role_branches`→`fetch_all_skill_branches`, defined at `gates/check_runner.py:464`
  - `skill_settings`, defined at `pipeline.py:211`
  - `_undispositioned_skill_prs`, defined at `relay.py:57`
  canonical: the four `grep -n "def <name>" <file>` lookups above, run directly against `/tmp/pr2731-verify`. All four are real renames at their definition sites; the comment edits do nothing but keep a same-file/cross-file textual reference to the symbol's name in sync with it. This is a real, if immaterial, deviation from the PR body's literal claim "leaving comments ... untouched": 8 of 2140 changed lines were comment edits, and every one tracks an actual rename rather than editing unrelated prose. Not a functional defect.

### Check 3 — no cross-repo-shared identifier renamed

Checked against a local `tokenmaxxxer-core` checkout at `/home/jwjung/tokenmaxxxer-core`, fetched live this turn:
```
cd /home/jwjung/tokenmaxxxer-core && git fetch origin main && git log -1 --oneline origin/main
```
derived: above — result: `60cbcb5 issue-2670: rename CLAUDE_ROLE to CLAUDE_SKILL (core read side) (#348)` — the same repo/issue that already made `CLAUDE_SKILL` the correct env var name before this PR.
canonical: `core/hooks/board-gate.sh:862` (read directly): `with open(os.path.join(root, ".on-the-record", "role.json"), ...)`, followed by parsing the JSON key `"role"` from that file. Both the filename `.on-the-record/role.json` and the JSON key `"role"` are the concrete shared surface, and both are confirmed literally unchanged on the on-the-record side (Check 2, persisted filenames/keys). The env var (`CLAUDE_SKILL`) and CLI flag (`--role`) surfaces are likewise unchanged (Check 2).
One stale reference was found and traced to be a non-issue: `core/hooks/board-gate.sh:89` comments "spawn.py's ROLES tuple". `derived: grep -n "^ROLES\|^SKILLS\b" /tmp/main-baseline/spawn.py /tmp/pr2731-verify/spawn.py` — result: no match on either side; no such tuple exists in `spawn.py` before or after this PR, so this is pre-existing dead prose in core, not a live coupling this PR could break.
Outcome: no cross-repo-shared identifier was renamed by this PR.

### Check 4 — docs/ untouched

`git diff --stat origin/main pr2731-head -- docs/` initially showed 3 files
changed (2 additions under the PR's own new record path, plus what looked
like a 1-line deletion in an existing file,
`docs/issue-2719/reports/adversarial-review-5d983b72/deviation-log/20260829T125242042429-471f5a6ea403e1ed.md`,
present on `origin/main` — `canonical: git cat-file -e
origin/main:docs/issue-2719/reports/adversarial-review-5d983b72/deviation-log/20260829T125242042429-471f5a6ea403e1ed.md`,
run live, exits 0).
Traced the deletion:
```
git merge-base origin/main pr2731-head
git log --oneline pr2731-head..origin/main
```
derived: above — result: merge-base is `01ffdde1d801a2cfc1241eb7168f252bfb14b137`, and exactly one commit exists on `origin/main` that isn't on the PR branch — `8b2cab50 issue-2719: land deviation-log entry from #2728 (#2730)` — which *added* that file to `origin/main` after PR #2731's branch point. Re-running the diff against the true merge-base:
```
git diff --stat 01ffdde1 pr2731-head -- docs/
```
canonical: result — `2 files changed, 107 insertions(+)`, both new files
(untracked on this branch — they live on PR #2731's branch at commit
`e16ddf98`; canonical: `git diff --name-status 01ffdde1 pr2731-head --
docs/`, read live against the `pr2731-head` worktree, both lines `A`): the
PR's own record file and its `deviation-log/` entry under
`docs/issue-2600/reports/`, zero deletions.
Outcome: no existing `docs/` file was touched by this PR; the earlier
3-file/1-deletion appearance was branch staleness (one intervening
unrelated main commit), not something the PR did — consistent with why the
PR's own verification note ("`git diff --stat origin/main -- docs/`:
empty") was accurate at the time it was written.

### Check 5 — approval-gate.sh exclusion is real and complete, stated reason holds

```
diff /tmp/main-baseline/on-the-record/hooks/approval-gate.sh /tmp/pr2731-verify/on-the-record/hooks/approval-gate.sh && echo IDENTICAL
grep -oiE '\brole\b' /tmp/pr2731-verify/on-the-record/hooks/approval-gate.sh | wc -l
```
derived: above two commands — result: `IDENTICAL` (empty diff) and `45`, matching the PR's claim exactly.
canonical: `test/test_convention_equivalence.py:201-234` (read directly on the PR head), `ApprovalGateEquivalenceTest`: `self.assertIn("if role != branch_role:", text)` and `self.assertIn('needle = "APPROVE issue-%d/%s" % (issue, role)', text)`, both asserted directly against `approval-gate.sh`'s own source text — a real, literal pin on those identifier names as source text, not a paraphrase.
`test_hook_file_exists_and_has_expected_shape` (the first assertion in that class) is present in **both** failing-test lists from Check 1 — i.e. a pre-existing failure on `origin/main` too, unrelated to and unaffected by this PR either way. This is orthogonal to the correctness of leaving the file alone, but confirms the exclusion isn't papering over a regression this PR introduced.
Outcome: the exclusion is real (file untouched), complete (all 45 occurrences remain), and the stated reason (literal source-text pinning by `ApprovalGateEquivalenceTest`) holds under direct reading of the test.

### Supporting spot-checks (not part of the 5 assigned checks, corroborating)

```
cd /tmp/pr2731-verify && xargs -a /tmp/changed_py.txt ruff check --select F821,F841
cd /tmp/main-baseline && ruff check --select F821,F841 watchdog.py
```
derived: above — result: identical single `F841` at `watchdog.py:784` (`Local variable 'found' is assigned to but never used`) on both `origin/main` and the PR head.
canonical: `consult.py:749` (read directly on the PR head) — `def rank_skills(task_text: str, skill: str = "candidates", ...)` vs `origin/main`'s `role: str = "candidates"` — confirms the PR body's claimed fix for the leftover inconsistent parameter.
`derived: git diff origin/main pr2731-head -- . ':!docs' | grep -oiE '\brole\b' | wc -l` — result: 1145 (both directions symmetric), consistent with the claimed 1143 AST-identified identifier occurrences; small variance expected between a whole-word regex count over diff text and an AST-node walk over source.

## Why

The task specifically named this program's own failure pattern — 8 false
negative claims across 4 prior deliverables, 3 of them exactly "the
failing-test set is unchanged" — asserted without execution. Every claim
above was therefore re-run from the PR head and `origin/main` directly
rather than parsed out of the PR body, using two disposable worktrees so
neither run could contaminate this session's own branch state.

## What did not work

None.

## Upstream basis

- PR tokenmaxxxer/on-the-record#2731, head commit `e16ddf98f6e848e58c7908697465e0b3e856ae58`, base `origin/main` at PR creation (`git merge-base origin/main pr2731-head` = `01ffdde1d801a2cfc1241eb7168f252bfb14b137`; sha: same-commit does not apply — this cites the PR head directly, not a docs/issue-2600 path landing in this commit).
- `origin/main` current tip at verification time: `8b2cab5050a041ca939dc80cc0a2afb0c4029260`.
- `tokenmaxxxer-core` local checkout (`/home/jwjung/tokenmaxxxer-core`), fetched to `origin/main` `60cbcb5` (issue #2670, "rename CLAUDE_ROLE to CLAUDE_SKILL (core read side)"), used only to check the cross-repo-shared-identifier claim (Check 3).

## Open findings

1. (Immaterial) 8 comment lines were edited across the diff — all tracking
   an actually-renamed symbol's cross-reference; derived/canonical:
   Check 2's exception paragraph above (the four `grep -n "def <name>"`
   lookups against `/tmp/pr2731-verify`), not prose rewriting. A literal
   reading of the PR body's "leaving comments ... untouched" is therefore
   not 100% true, though nothing functional or scope-wise is wrong.
   Resolution: none needed, noted for the record only.
2. `on-the-record/hooks/approval-gate.sh` (45 `role` occurrences) remains
   deliberately unrenamed, tracked by PR #2731 itself as its own "Open
   finding 1" for a follow-up that edits it together with
   `test/test_convention_equivalence.py`. canonical: Check 5's `diff`/`grep`
   output above (file `IDENTICAL`, `45` occurrences) — confirmed real and
   correctly scoped out of this slice; no action needed from this record.
3. The semantic collision between the renamed vocabulary and this
   codebase's pre-existing "skill" (Claude Skills) concept, tracked by
   PR #2731 as its own "Open finding 2" (canonical: `gh pr view 2731`
   body, read live this session), was not independently re-litigated
   here — the PR frames it as a consequence of an earlier, already-merged
   slice's word choice, out of scope for a slice-4 identifier-rename
   verification.

## Next steps

None. acceptance: Checks 1-5 in `## What was done` above, each with its own
`derived:`/`canonical:` tag and command output — result: CONFIRMED for
every check; `loop_state: landed`.
