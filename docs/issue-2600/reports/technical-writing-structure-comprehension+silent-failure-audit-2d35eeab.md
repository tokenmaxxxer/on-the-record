---
issue: 2600
role: technical-writing-structure-comprehension+silent-failure-audit-2d35eeab
author: technical-writing-structure-comprehension+silent-failure-audit-2d35eeab
skills: technical-writing-structure-comprehension (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: on-the-record (53 files — see "What was done" for the list; full diff in this PR)
    sha: same-commit
  - path: tokenmaxxxer-core (audited, zero in-scope edits found)
    sha: 764aebc19c7e01fedd0078805c75740ac777b9a6
type: audit-and-fix
breaking: false
verdict: comment/docstring slice of #2600 delivered for on-the-record (53 files, acceptance-regex count 2377 -> 2226, diff verified comment/docstring-only, full test suite identical before/after); tokenmaxxxer-core audited with the same rule and found zero in-scope occurrences (934 -> 934, no commit needed) — a real negative result, not a shortfall.
loop_state: landed
upstream:
  - path: same-commit
    sha: same-commit
---

# issue-2600 — technical-writing-structure-comprehension+silent-failure-audit-2d35eeab record

## What was done

Second slice of #2600 ("retire the word itself"), scoped to the **comment/docstring kind** in both enforcement repos, per the partition in the issue's own comment thread and the per-kind occurrence map carried on PR #2668's branch.
canonical: `git show origin/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md` (that path is not checked out on this branch/worktree; it exists only on `origin/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`, read live this session via `git show <branch>:<path>`) — comment-docstring kind = 912 occurrences (on-the-record) / 642 (tokenmaxxxer-core), both outside `docs/`.

**on-the-record (this repo): 53 files edited, comment/docstring text only.**

Files (grouped by area): `board.py`, `checkpoint.py`, `consult.py`, `directive_assembly.py`, `harness/driver.py`, `ledger/decisions.py`, `pipeline.py`, `plumbing.py`, `relay.py`, `skills.py`, `spawn.py`, `trajectory_analyzer.py`, `watchdog.py`; `gates/ci.py`, `gates/finding_shape.py`, `gates/findings_due.py`, `gates/gates.py` (+ mirror `on-the-record/gates/gates.py`), `gates/gh_cache.py`, `gates/issue_bundling.py`, `gates/merge_gate.py`, `gates/quality_bar.py`, `gates/record_lint.py` (+ mirror `on-the-record/gates/record_lint.py`), `gates/repo_scope.py`, `gates/skip_eligibility.py`, `gates/skip_gate.py`, `gates/spawn_on_approve.py`, `gates/spawn_on_pr.py`, `gates/state_paths.py`; 23 `on-the-record/hooks/*.sh` files (`approach-cap-warning.sh`, `approval-gate.sh`, `decision-queue-stopgate.sh`, `delegated-judgment-gate.sh`, `delegation-post-gate.sh`, `deliverable-guard.sh`, `deviation-log-guard.sh`, `directive.sh`, `gh-write-allow-gate.sh`, `git-push-guard.sh`, `heredoc-command-refusal-gate.sh`, `merge-allow-gate.sh`, `pr-base-guard.sh`, `product-capture-stopgate.sh`, `record-claim-guard.sh`, `record-claim-shape-directive.sh`, `report-framing-check.sh`, `retry-loop-bound.sh`, `role-deviation-directive.sh`, `spawn-allow-gate.sh`, `stop-poll-rearm.sh`, `upstream-defect-scope-guard.sh`); `test/test_spawn_skills_mount.py`.
derived: `git diff --stat origin/main -- . ':!docs'` — result: `53 files changed, 193 insertions(+), 175 deletions(-)`, file list matches the above exactly.

Every occurrence of "role"/"역할" sitting in a `#` comment or a `"""..."""`/`'''...'''` docstring was triaged individually against one rule: **rewrite if it teaches CURRENT behavior using the retired closed-tuple identity concept as if still live; leave unchanged if it narrates HISTORY** (an incident, a removed mechanism, a past decision, correctly using the vocabulary as it stood then). Ambiguous cases were left unchanged and logged rather than guessed. Rewrites replaced "role" with whatever the surrounding prose already established as the current term for the same referent — almost always "session"/"spawned session" (a generic spawned identity) or "skill" (the still-live mounting axis) — inventing no new claims.

**tokenmaxxxer-core: audited under the same rule, branch `issue-2600/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab` created from `origin/main`, zero commits.**
derived: `git -C /home/jwjung/tokenmaxxxer-core rev-parse origin/main` — result: `764aebc19c7e01fedd0078805c75740ac777b9a6`
acceptance: `git -C /home/jwjung/tokenmaxxxer-core status --short` (after the audit) — result:
```
(no modified/staged files — only pre-existing untracked leftovers from other sessions: .landing-obligations/, .on-the-record/, docs/issue-335/, docs/issue-341/, none of which this session touched)
```
Every comment/docstring occurrence resolved to one of: (a) accurate current documentation of the still-live `CLAUDE_ROLE` session-identity variable (explicitly out of scope for renaming per this issue, and not the retired closed-tuple concept the operator's ruling targets), (b) correctly-framed historical narration, (c) text inside a `python3 <<'PY' ... PY` / `cat <<EOF ... EOF` heredoc a shell script actually feeds to an interpreter (skipped wholesale per the task's own heredoc-caution instruction), or (d) inside a load-bearing directive/contract/agent-persona file. No occurrence needed a rewrite — a genuine negative result, checked (not merely asserted) by the before/after acceptance-regex count in Verification below, which is identical (934 -> 934) and confirmed by a clean `git status`.

**Load-bearing files excluded from this slice entirely** (prompt/directive/command/contract text a session reads as instruction, not a comment — belongs to the prompt-text slice, not this one):
- on-the-record: `protocol.md`, `protocol.ko.md`, `on-the-record/directive/*.md`, `on-the-record/commands/*.md` (Claude Code slash-command definitions), `.on-the-record/directive/*.md`.
- core: `core/contract/role-handoff-contract.md`, `core/directive/session-protocol.md`, `scout/directive/scout-protocol.md`, `freelunch/directive/freelunch-protocol.md`, `warrant/directive/warrant-protocol.md`, `warrant/agents/warrant-hunter.md` (subagent persona).
derived: `grep -n "design-rationale" on-the-record/commands/run.md` — result: `design-rationale: 조율 세션의 대화형 절차를 그대로 프롬프트 텍스트로 남긴다 — ...` (the file's own frontmatter states it is deliberately kept as prompt text, not a script — confirming the exclusion for this whole directory).

**Left unedited, flagged ambiguous rather than guessed:** `README.md`, `README.ko.md`, `on-the-record/UNENFORCED-CLAUSES.md` (on-the-record).
derived: `grep -n "APPROVE issue-<n>/<role>" gates/spawn_on_pr.py board.py pipeline.py gates/delegation_metrics.py` — all four still emit this literal template today, confirming the dual-scheme (old role-axis / new skill-axis, issue #2432 stage 4) is still live in current code, not purely historical.
Whether README's prose describing that shape is "stale" or "accurately naming the still-live template placeholder" depends on a fact (does `spawn.py` ever produce a fresh `issue-<n>/<role>` branch today, or is that purely legacy-read) that needs the identifier/prompt-text slice's own investigation, not a terminology-only pass. Rewriting on a guess risked exactly the "turn history into fiction" failure mode this slice was warned against.

**Docstrings checked for tool-parsing (none rewritten):** `scripts/behavior_metrics.py`, `scripts/cache_coverage.py`, `scripts/session_waste_metrics.py`, `scripts/related_files.py` all wire their module docstring into `argparse(description=__doc__)`, shown verbatim in `--help`.
derived: `grep -n "description=__doc__\|__doc__" scripts/behavior_metrics.py scripts/cache_coverage.py scripts/session_waste_metrics.py scripts/related_files.py` — result: all four wire `description=__doc__` into their `argparse.ArgumentParser(...)` call. `grep -rn "__doc__" --include=*.py .` outside these four returns no other hit in either repo's changed-file set — left untouched, flagged as load-bearing (belongs to the identifier/prompt-text slice if it ever needs to change).

**Heredoc-executed text noticed and left alone, on both sides.** Both repos' `*-gate.sh` hooks embed their real enforcement logic (including many `#` comments matching "role") inside `python3 <<'PY' ... PY` or `cat <<EOF ... EOF` blocks a shell actually feeds to an interpreter or emits verbatim to a consumer. These were excluded wholesale rather than edited line-by-line, since editing text inside them changes what a hook emits/executes, not just what a human reading the source sees. On-the-record: roughly 55 such lines across `approach-cap-warning.sh`, `approval-gate.sh`, `absorbed-branch-recut-guard.sh`, `call-shape-guard.sh`, `contract-guard.sh`, `decision-queue-stopgate.sh`, `delegated-judgment-gate.sh`, `deviation-log-guard.sh`, `gh-write-allow-gate.sh`, `git-push-guard.sh`, `merge-allow-gate.sh`, `plan-order-guard.sh`, `post-landing-obligation-gate.sh`, `pr-preflight.sh` (its entire body), `quality-bar-gate.sh`, `retry-loop-bound.sh`, `role-deviation-directive.sh`, `skill-verdict-guard.sh`, `spawn-allow-gate.sh`, `upstream-defect-scope-guard.sh`. Core: roughly 250 such lines across `approval-gate.sh`, `board-gate.sh`, `record-fields-gate.sh`, `gh-guard.sh`, `ordering-gate.sh`, `trailer-gate.sh`, `survey-order-gate.sh`, `handbook-trigger-gate.sh`, `facet-keyword-gate.sh`, `citation-gate.sh`, `record-shape-gate.sh`, `warrant/hooks/state.sh`, `directive.sh`, `lib/role-directive.sh`, and several `hooks/tests/run-*.sh` fixture heredocs.

## Why

The operator's own framing for #2600 is that nothing in the *working system* should teach the retired concept as its own current vocabulary — not that the word must vanish from every sentence. The rule applied above operationalizes exactly that split: current-teaching prose is rewritten, historical narration is left (rewriting "issue-295 carved out an exemption for two named roles" to say "skills" would make a true sentence false), and anything whose editing risk (tool-parsed docstrings, heredoc-embedded text, directive/prompt files read as instruction) exceeds a vocabulary swap's benefit is left to a different, already-scoped slice instead of being forced in here.

Given the volume (912 on-the-record / 642 core comment-docstring occurrences per PR #2668's map) and that judgment is required per occurrence — not a mechanical find-and-replace — the work was fanned out by repo, then by file group within on-the-record (each group's own file-ownership frozen up front, no two workers ever assigned the same file), consuming this session's `CORE_BUILD_NOW=1` delivery mandate together with the standing freelunch delegation directive. Each worker was handed the identical frozen rule verbatim (historical-vs-current test, the load-bearing exclusion list, the CLAUDE_ROLE/identifier/persisted-key/docs exclusions, the heredoc caution) so that 11 independent workers' outputs are comparable rather than each reinventing the judgment call differently.

## Upstream basis

Same commit (this record lands with the code it describes). Reads from, but does not modify, `origin/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md` (PR #2668, open, unmerged as of this session — its own env-var renames are not yet on `main`, so this slice's baseline is `main`, independent of that PR's still-pending changes) for the per-kind occurrence map and methodology notes.
canonical: `gh pr view 2668 --json state` — result: `state: OPEN`.

## Verification

Per the task's own framing, verification for this slice is mostly negative — showing nothing executable changed — so each check below is derived by command, not asserted.

**Diff is comment/docstring-only (on-the-record).** A tokenize-based checker (`comment_or_string_lines` from Python's `tokenize` module for `.py` files; "every changed line must start with `#`" for `.sh` files) was run over every changed line in `git diff origin/main -- . ':!docs'`.
derived: `python3 /tmp/verify_comment_only.py` (per-hunk line check against tokenize COMMENT/STRING spans, or `#`-prefix for `.sh`) — result:
```
ALL CHANGED LINES ARE COMMENTS/DOCSTRINGS
```
acceptance: `git diff --stat origin/main -- docs/` — result: empty (no historical record touched).
acceptance: `git diff --name-only origin/main -- runs/` — result: empty (no persisted-data file touched).

**No `CLAUDE_ROLE` mention was altered.**
derived: `git diff origin/main -- . ':!docs' | grep -n CLAUDE_ROLE` — result: every changed hunk containing `CLAUDE_ROLE` keeps that exact token on both the `-` and `+` sides; only surrounding prose changed (e.g. "a role session is defined by..." -> "a spawned session is defined by...").

**Syntax-clean.**
acceptance: `for f in $(git diff --name-only origin/main -- . ':!docs' | grep '\.py$'); do python3 -m py_compile "$f"; done` — result: no output, no failure.
acceptance: `for f in $(git diff --name-only origin/main -- . ':!docs' | grep '\.sh$'); do bash -n "$f"; done` — result: no output, no failure.

**Acceptance-regex count, on-the-record.**
acceptance: `grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' .` — result:
```
before (origin/main, via git stash): 2377
after  (working tree):               2226
```
canonical: `git show origin/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`, Deliverable 1's methodology notes — states this same 2377 figure for `origin/main`, confirming the same baseline. The 151-occurrence drop is smaller than the raw "N rewritten" tallies summed loosely across workers' reports (~150-155) because this regex only counts "role"/"역할" as a bare word — it does not match inside identifiers (`_role_family`, `resolve_role_family_source`), which this slice explicitly never touches — so the delta is a clean measure of comment/docstring prose rewrites specifically, consistent with (not double-counting) the identifier-kind slice's own future scope.

**Acceptance-regex count, tokenmaxxxer-core.**
acceptance: `cd /home/jwjung/tokenmaxxxer-core && grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l` — result:
```
before (origin/main, fresh checkout): 934
after  (post-audit, same checkout):   934
```
This differs from PR #2668's own core-repo acceptance-regex baseline of 933 by exactly 1 — a one-line drift explained by unrelated landings on `main` between that map's derivation and this session (not investigated further, since both this session's before and after counts come from the same fresh checkout, so the slice's own before/after comparison is unaffected regardless of the cause).

**Test suites, on-the-record — identical before and after** (`git stash` / `git stash pop` around the same runs, both against the real working tree, not a description of a prior run).
acceptance: `python3 -m pytest test/test_spawn_model_override.py test/test_convention_equivalence.py test/test_spawn_skills_mount.py -q` — result:
```
before: 2 failed, 80 passed
after:  2 failed, 80 passed   (byte-identical failing-test names: ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape, BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim — both pre-existing per PR #2668's own record, unrelated to this change)
```
acceptance: `python3 -m pytest test/ -q` — result:
```
before: 15 failed, 358 passed, 3 xfailed
after:  15 failed, 358 passed, 3 xfailed   (identical set of 15 failing test names both times; all are network-dependent or unrelated pre-existing failures — e.g. "리모트 저장소에서 읽을 수 없습니다" in test_local_dependency_env.py — not caused by this change)
```

**Reconciliation against PR #2668's per-kind map.**
canonical: `git show origin/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`, Deliverable 1 table — on-the-record comment-docstring bucket = 912 (substring-inclusive, e.g. counts "role" inside `_role_family`); core's = 642. Those totals are not directly comparable to this record's before/after deltas, which use the acceptance-check's whole-word regex (per that same source's own methodology note: `\b` does not break on `_`, so the map's totals are always larger than acceptance-regex counts for the same scope). No disagreement was found between what this session measured (above, by command) and what that map predicted for the acceptance-regex baseline — the one discrepancy found (933 vs. 934 for core) is explained above rather than silently adopted.

## Open findings

1. **README.md, README.ko.md, on-the-record/UNENFORCED-CLAUSES.md left unedited, ambiguity unresolved.** See "What was done" above. Resolution path: whichever session next works the identifier/prompt-text slice should first determine whether `spawn.py` today can still produce a fresh `issue-<n>/<role>` branch (vs. that shape being purely a legacy-read compatibility path), then this slice's rewrite-or-leave call for these three files follows directly from that answer.
2. **`gates/gates.py` (`PROTECTED_ROOT_DIRS`) and `gates/ci.py` (L69-73) reference a `roles/` directory and a `gates.BRANCH_ROLE` identifier that a sub-audit could not confirm still exist** in current `gates.py`.
   derived: `grep -n "BRANCH_ROLE" gates/gates.py` — result: no match (identifier not found in current `gates.py`); `ls roles/` — result: `ls: cannot access 'roles/': No such file or directory` (consistent with the #2539/#2610 catalog-deletion narration already in the file's own history comments). Left unchanged rather than asserting a dead-code claim beyond a vocabulary swap. Resolution path: whoever next touches `gates/gates.py`'s identifiers should confirm live/dead status and, if dead, both fix the comment and consider whether `PROTECTED_ROOT_DIRS` itself needs updating (identifier-kind slice, not this one).
3. **A handful of individually-flagged ambiguous lines were left unresolved by design** (full list and reasoning in each contributing worker's report, summarized in "What was done"): `lifecycle.py:93,119`, `scripts/behavior_metrics.py:31-32`, `bench/run.py:2,36,108`, `gates/model_routing.py`'s "unknown role" fail-open clause, `gates/claims.py`'s "role JSON" example, `gates/frozen_decisions.py`'s "role manifest" sample, `gates/check_runner.py`'s "just-pushed" branch framing, `delegated-judgment-gate.sh:8,11`, `upstream-defect-scope-guard.sh:32-34` (core), `role-deviation-directive.sh:15`. Each is a case where confirming the rewrite would require asserting a new factual claim about current dead/live code status beyond a vocabulary swap, which the frozen rule explicitly disallows inventing. None affect correctness of what *was* changed; each is a candidate the identifier/prompt-text slice can resolve once it has reason to touch the underlying code anyway.
4. **The tokenmaxxxer-core branch was created and left with zero commits**, since the audit found nothing in-scope to change.
   derived: `git -C /home/jwjung/tokenmaxxxer-core log origin/main..HEAD --oneline` — result: (empty — no commits ahead of `origin/main`). No PR is needed for a no-op branch; noted here so a future slice doesn't rediscover the same zero result from scratch — the per-category disposition above is the citable answer to "was core's comment-docstring kind checked."

## Next steps

- Remaining slices per the issue's partition: prompt-text kind, identifier kind (hooks vs non-hooks split), each scoped from PR #2668's map counts, each inheriting this record's three open findings above as pointers into code they will touch anyway.
- `CLAUDE_ROLE`'s replacement name remains its own decision (PR #2668's Open finding #1) before any slice touches it.

## What did not work

- Initial per-repo delegation (one worker per repo) proved too coarse for on-the-record given the volume (2377 baseline occurrences, spread across ~50 files needing individual judgment): the first on-the-record worker hit its own turn budget mid-task and further split its assignment into file-group workers rather than completing inline. This was allowed to proceed (rather than recalled) since the resulting groups were still non-overlapping by file ownership; before integrating, this session independently re-verified the resulting diff was comment-only and re-ran the full test suite itself rather than trusting the delegation chain's own narration, per the risk that concurrent, uncoordinated edits to a shared working tree could otherwise have silently conflicted (see Verification above for the actual re-derived checks, not a restatement of the workers' own claims).
- No deviation from the approved scope occurred otherwise — the load-bearing/heredoc/ambiguous-case exclusions above are the frozen rule working as intended, not departures from it.

skill-verdict: silent-failure-audit — not-applicable: invoked (Skill tool call this session, full procedure read) and found its procedure targets try/catch-style fallible operations in an implementation under review; this session's work is a text/comment-only vocabulary sweep with no new error-handling code, so the skill's own "does this need the procedure?" gate says skip.
derived: `python3 /tmp/verify_comment_only.py` (this session, see Verification above) — result: `ALL CHANGED LINES ARE COMMENTS/DOCSTRINGS` — the analogous risk this task actually carries (an edit silently changing what a hook emits/executes rather than just what a human reads) was handled directly via the heredoc-exclusion rule and this same tokenize-based check, in place of the skill's catch/error-path procedure.
skill-verdict: technical-writing-structure-comprehension — not-applicable: this task is a targeted terminology substitution (retire one word, per an operator ruling) inside existing comments, not a sentence/paragraph/section restructuring pass for reader comprehension.
canonical: this record's own "What was done" section above, listing every rewrite as a like-for-like word substitution ("role" -> "session"/"skill") — none of the recorded edits split a sentence, reordered a paragraph, or regrouped a procedure, confirming no sentence/paragraph-structure judgment was exercised.
