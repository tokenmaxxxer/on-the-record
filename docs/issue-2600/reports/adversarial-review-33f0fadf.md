---
issue: 2600
role: adversarial-review-33f0fadf
author: adversarial-review-33f0fadf
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: committing
upstream:
  - path: PR #2731 (github.com/tokenmaxxxer/on-the-record/pull/2731), head commit
    sha: e16ddf98f6e848e58c7908697465e0b3e856ae58
---

# issue-2600 — adversarial-review-33f0fadf record

## What was done

Independent verification of PR #2731 (issue #2600 slice 4: rename every remaining `role`/`Role`/`ROLE`/`roles` Python and shell identifier in on-the-record to `skill`/`Skill`/`SKILL`/`skills`). Re-derived every negative claim in the PR body from the PR head myself, in a separate worktree, without trusting the builder's own record until after I had my own numbers.

checked: `gh pr view 2731 --json headRefName,baseRefName,headRefOid,baseRefOid,mergeable,commits` — result: `mergeable: MERGEABLE`, head `e16ddf98`, two commits (`20042be3` rename, `e16ddf98` deviation-log entry).

**1. Failing-test-set claim** — re-derived as sets of names, not counts.
derived: `git fetch origin pull/2731/head:pr-2731-review && git worktree add /tmp/pr2731-review pr-2731-review && git worktree add /tmp/main-review main`, then in each worktree `python3 -m pytest -m "not slow" -q` (executed this turn).
- main: `16 failed, 529 passed, 6 xfailed in 5.45s`
- PR head: `16 failed, 529 passed, 6 xfailed in 5.60s`
derived: `grep "^FAILED" <output> | sort` on both, then `diff main_failed_sorted.txt pr_failed_sorted.txt` — result: exactly one line differs:
```
15c15
< FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo
---
> FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
```
checked: `git diff main pr-2731-review -- test/test_spawn_skill_judge_haiku_timeout_overlap.py | grep -n role_source` — confirms the test method itself was renamed (`def test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo` → `..._skill_source_is_not_skill_repo`) along with its local variable `role_source`→`skill_source`; the test body logic is untouched. Claim **CONFIRMED exactly**: the failing-test-name-set differs by exactly one entry, and that entry is the legitimate rename the PR describes, nothing else.
derived: xfail-set comparison — `python3 -m pytest -m "not slow" -q -rX` on both worktrees, `grep "^XFAIL" | sort`, `diff` — result: identical, no XFAIL-set drift either.

**2. "Diff touched only identifiers" claim** — checked the other direction (did the AST walk rename a persisted key, CLI flag string, or prompt text?).
derived: `git diff main pr-2731-review -- '*.py' '*.sh'` (6485-line diff, saved and parsed programmatically) — wrote a small Python script pairing each removed/added line, extracting quoted-string contents, stripping `{...}` f-string placeholders, and flagging any remaining textual difference inside a string literal. Two categories of legitimate flag turned up, both re-verified by hand:
  - f-string placeholders (`{role}`→`{skill}`) inside otherwise-identical Korean/English prose — these are variable references, not literal-text changes; the surrounding prose is byte-identical (e.g. `bench/run.py`: `f"[{role}] 룰북에 bench/ 가 없다: {b}"` → `f"[{skill}] 룰북에 bench/ 가 없다: {b}"`).
  - a handful of string literals whose *content itself is a code identifier name* used reflectively, and that identifier really was renamed elsewhere in the same diff: `mock.patch.object(spawn, "_undispositioned_role_prs", ...)` → `"_undispositioned_skill_prs"` (3 occurrences, matches `relay.py`'s actual rename of that function), `body.count("_write_role_sidecar(")` → `"_write_skill_sidecar("` (matches the real rename), `"fetch_all_role_branches"` → `"fetch_all_skill_branches"` (matches the real rename), and one shell parameter expansion `"$role"`→`"$skill"` in `on-the-record/hooks/record-scaffold.sh` (matches that script's own variable rename on the line above it — checked: `git diff main pr-2731-review -- on-the-record/hooks/record-scaffold.sh`, full hunk read). None of these is a persisted key, CLI flag, or prompt text — each is a string that names a Python/shell identifier which the diff itself shows was actually renamed.
  derived: `grep -nE '^[-+].*["'"'"'](role|skill)["'"'"']' ` against the same diff — every `"role"` dict-key occurrence (`json.dumps({"role": skill, ...})`, `sidecar["role"]`, `ctx["role"]`, `entry.get("role")`, the `role.json` filename itself) keeps the **key string** `"role"` unchanged; only the **value-side local variable** was renamed to `skill`. Checked ~60 such sites in the diff; zero exceptions found.
  checked: `--role` CLI flag string — `grep -n -- '--role' <diff>` — 3 occurrences, all `_arg(rest, "--role")` / `_arg(argv, "--role")` / `["...", "--role", role]`; the flag string `"--role"` is unchanged in every case, only the destination variable was renamed.
  **Minor discrepancy found**: 7 comment lines across 6 files (`consult.py`, `gates/merge_gate.py`, `gates/spawn_on_pr.py`, `on-the-record/hooks/contract-guard.sh`, `on-the-record/monitors/poll_heartbeat_delta.py`, `pipeline.py` ×2) *were* touched — each is a comment that names a function by its exact (backtick-quoted) name, and that function really was renamed by this slice, e.g. `# \`_approved_roles_on_issue\`` → `` `_approved_skills_on_issue` ``. This directly contradicts the PR body's blanket claim "leaving comments, ... left untouched" — comments that name a renamed identifier verbatim *were* updated to keep them accurate. Functionally this is the right call (a stale comment naming a function that no longer exists would be worse), but the claim as written overstates the "comments untouched" boundary. Filed as a finding below, not a defect.

**3. No cross-repo-shared identifier renamed** — re-checked against an actual local `tokenmaxxxer-core` checkout (`/home/jwjung/tokenmaxxxer-core`, `git log -1` sha `60cbcb55a785e83edac637b4faea065cdf88f843`).
derived: grepped core's tracked `*.py`/`*.sh` files (its own rulebook-mirror and test-fixture subtrees that copy on-the-record's source verbatim for unrelated fixture purposes were excluded from this grep) for every on-the-record identifier this PR renamed that looked like a plausible cross-repo surface: `_approved_roles_on_issue`, `fetch_all_role_branches`, `resolve_role_family_source`, `role_settings`, `resolved_role_model`, `_undispositioned_role_prs`, `_role_from_pr`, `_ROLE_TRAILER_RE`, `found_role`, `role_entries`, `issue_role_key`, `EXPECTED_COMMIT_ROLES`, `rank_skills`, `_write_role_sidecar` — zero hits for any of them in core outside those mirror subtrees.
checked the one identifier that genuinely IS shared cross-repo: `core/hooks/board-gate.sh` reads `.on-the-record/role.json` and its JSON key `"role"` directly (`sed -n '850,890p' core/hooks/board-gate.sh`: `open(os.path.join(root, ".on-the-record", "role.json"), ...)`, `_sidecar.get("role")`, `_sidecar.get("issue")`, comparing against a branch-parsed `_cross_role`). This is exactly the hazard the task described: a gate in the other repo reads this sidecar file/key by name, and if on-the-record had renamed either the filename or the key, this gate would either always no-op (sidecar unreadable) or always fall through to the branch-string-only check — a silent enforcement loss, not a loud failure. checked: `grep -rn '"role\.json"\|d / "role.json"' <pr-head>` — the sidecar filename `role.json` and the JSON key `"role"` are both unchanged in every write site (`pipeline.py:932`, `test/test_approval_gate_carriers.py:70`, etc.) — only the local Python variable feeding the value (`role`→`skill`) changed. Claim **CONFIRMED**: no cross-repo-shared identifier or persisted interface was touched.

**4. docs/ untouched claim** — checked: `git diff --name-status main pr-2731-review -- docs/` (executed this turn, against current `origin/main` tip) — result:
```
A	docs/issue-2600/reports/refactoring-legacy-seam-selection+refactoring-legacy-verification-cadence+adversarial-review-4c7357a0.md
A	docs/issue-2600/reports/refactoring-legacy-seam-selection+refactoring-legacy-verification-cadence+adversarial-review-4c7357a0/deviation-log/20260829T141525473187-89030bf9b0d7f247.md
D	docs/issue-2719/reports/adversarial-review-5d983b72/deviation-log/20260829T125242042429-471f5a6ea403e1ed.md
```
No `M` (modified) status anywhere under `docs/` — no historical record was renamed or rewritten. The two `A` entries are this PR's own required record + deviation-log entry (new files, not edits to existing docs; not present in this reviewing session's own working tree — they live only on PR #2731's branch). derived: `git merge-base main pr-2731-review` → `01ffdde1d801a2cfc1241eb7168f252bfb14b137`; checked: `git show 01ffdde1:<the D path>` and `git show pr-2731-review:<the D path>` both fail with "exists on disk, but not in" — the file is absent at the merge-base AND absent on the PR head; it was added to `main` by a later, unrelated commit (`8b2cab50`, issue-2719) after PR #2731's branch diverged. This is pure base-branch drift from a direct two-ref diff, not something PR #2731 deleted; a real three-way merge would keep it (nobody on the PR side touched it). **Discrepancy found**: the PR body's own claim "`git diff --stat origin/main -- docs/`: empty — history untouched" is not literally true against current `origin/main` (2 new files exist in the diff) — but the substance of the acceptance bar (no existing docs content renamed/rewritten) does hold. Filed as a finding below.

**5. `approval-gate.sh` exclusion — real and complete, not partial.**
checked: `git diff --stat main pr-2731-review -- on-the-record/hooks/approval-gate.sh` — empty (zero diff). checked: `grep -Io -iE '\brole\b' <pr-head>/on-the-record/hooks/approval-gate.sh | wc -l` — `45`, matching the PR's own count, none renamed. checked: `grep -n "assertIn\|assertEqual" <pr-head>/test/test_convention_equivalence.py` filtered to role/branch_role/cross_role — confirms `ApprovalGateEquivalenceTest` does `self.assertIn("if role != branch_role:", text)`, `self.assertIn('needle = "APPROVE issue-%d/%s" % (issue, role)', text)`, `self.assertIn("if isinstance(record, dict) and role in record:", text)`, `self.assertIn("if cross_issue != issue or cross_role != branch_role:", text)` against `approval-gate.sh`'s live source text — renaming those identifiers would flip these assertions from passing to failing with no behavior change, exactly the stated reason. Claim **CONFIRMED**.

**6. No compatibility alias introduced.**
checked: grepped PR head for dual-read/alias patterns (`getattr`/`hasattr` role-or-skill fallbacks, "backward compat" markers) — every role/skill dual-mention hit is either help text ("role-or-skill" wording, a pre-existing pattern from earlier already-merged slices per #2572's precedent) or a comment, not a new runtime fallback. checked: `spawn.py`'s retired `--role` flag hard-error (`tok == "--role"`) is unchanged (string-literal comparison, not turned into an accepted second spelling). Claim **CONFIRMED**.

**7. Static-analysis / behavior-preservation claims**, spot-re-run independently (not explicitly required by the task's checklist but load-bearing for the "behavior unchanged" umbrella claim):
derived: `ruff check --select F821,F841 <every changed .py file>` on PR head — result: `watchdog.py:784:9: F841 Local variable 'found' is assigned to but never used`, one error, nothing else. checked: same command against the identical file on `main` — same single F841 at the same line. Confirms it's pre-existing and unrelated to this diff, matching the PR's claim.
derived: `git diff --stat main pr-2731-review -- '*.py' '*.sh'`:
```
64 files changed, 1006 insertions(+), 1006 deletions(-)
```
matches the PR's claimed 64-file, balanced 1006/1006 diff exactly.
derived: `grep -rIo --exclude-dir=.git --exclude-dir=docs -i 'role' --include=*.py --include=*.sh` on main vs PR head — result: `2649` → `1506`, delta `1143` (2649 − 1506 = 1143) — matches the PR's claimed "1143 identifier-kind occurrences renamed" exactly.

## Why

The task named this exact failure class — plausible-sounding negative claims ("behavior unchanged", "failing-test set identical", "nothing outside the identifier kind was touched") produced without actually running the check — as something this program has already shipped four times uncaught. The only way to close that gap is to not read the PR body as evidence: re-derive each negative claim from the PR head with fresh commands, in a worktree separate from the builder's own working directory, and only then cross-check against the builder's own record to see whether the same numbers came out. Every command in "What was done" above was run by this session against a `git worktree` checkout of the PR head and of `main`, not copied from the PR body.

skill-verdict: adversarial-review — applied: invoked; this whole record follows the skill's blind-evaluator posture — every command was re-run independently against the PR head before I read the builder's own record file in detail, and the record above documents disagreements with the PR body's stated claims (comment-touch scope, docs/ "empty" claim) rather than restating them.
skill-verdict: work-in-english — applied: invoked; this record, its commit message, and the PR title/body were all written in English per the skill's routing rule, with only the final end-of-turn summary to the user written in Korean.

## What did not work

None. canonical: this record's own "What was done" section, items 1-7 above, read in-session — every claim re-derived either matched the PR body exactly (items 1, 3, 5, 6, 7) or is documented as a discrepancy (items 2 and 4, both claim-precision issues rather than functional defects, carried forward into Open findings below).

## Upstream basis

- PR #2731 (`e16ddf98f6e848e58c7908697465e0b3e856ae58`, on `issue-2600/refactoring-legacy-seam-selection+refactoring-legacy-verification-cadence+adversarial-review-4c7357a0`, not present in this reviewing session's own working tree — checked out separately via `git fetch origin pull/2731/head:pr-2731-review`) — the subject under review; every command above ran against a `git worktree` of this commit and of `origin/main` at `8b2cab5050a041ca939dc80cc0a2afb0c4029260`.
- The builder's own record for PR #2731, at path `docs/issue-2600/reports/refactoring-legacy-seam-selection+refactoring-legacy-verification-cadence+adversarial-review-4c7357a0.md` on PR #2731's branch (sha `20042be3dff85484ce2bd55abb43bc3cbdd46438`; untracked/absent in this session's own working tree, since it was never merged to this branch) — read only after independently re-deriving the numbers above, to check for agreement.
- `/home/jwjung/tokenmaxxxer-core` local checkout (sha `60cbcb55a785e83edac637b4faea065cdf88f843`) — used to verify the cross-repo-shared-identifier claim directly against the other repo's actual source.

## Open findings

1. **Comment-touch scope claim is imprecise.** The PR body states "leaving comments, docstrings, string literals/prompt text, ... left untouched," but 7 comment lines across 6 files were in fact edited, each updating a backtick-quoted reference to a function name that this slice itself renamed (e.g. `` `_approved_roles_on_issue` `` → `` `_approved_skills_on_issue` `` in `gates/spawn_on_pr.py` and `pipeline.py`). This keeps the comments accurate rather than stale, which is the right outcome, but the claim as written should have said "comments were left untouched except where they named a renamed identifier verbatim." Resolution path: none needed — no code change, only a wording precision note for future slice records making the same "comments untouched" claim.
2. **`docs/` "empty diff" claim is imprecise against current `origin/main`.** `git diff --name-status origin/main -- docs/` shows 2 new files (this PR's own required record + deviation-log entry) and 1 apparent deletion that is pure base-branch drift (a file added to `main` by an unrelated, later-landed issue-2719 commit after this PR's branch diverged — confirmed absent at the merge-base and absent on the PR head, so a real merge would not remove it). No existing docs content was renamed or rewritten (zero `M` status), so the acceptance intent ("historical records are untouched") holds; only the literal "empty" wording in the PR body does not. Resolution path: none needed for this PR to land — a real merge will keep the issue-2719 file; the wording nuance is worth carrying into the issue's final overall acceptance check, which should diff against docs/ state right before merge, not treat "any diff under docs/" as failure when new same-issue records are expected.
3. Everything else re-derived (failing-test-set identity, xfail-set identity, persisted-key/CLI-flag/prompt-text preservation, cross-repo-shared identifier preservation, `approval-gate.sh` exclusion completeness, no-compat-alias, ruff cleanliness, file/line-count balance) matched the PR's own claims exactly — no further open findings.

## Next steps

None outstanding for this verification. canonical: Open findings 1-3 above (read in-session) — both discrepancies found are claim-wording issues with no required code change; `loop_state` moves to `landed` once this record's own PR is confirmed merged, outside this session's turn.
