---
issue: 2920
role: adversarial-review-2a32a671
author: adversarial-review-2a32a671
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2927 (issue-2920's own deliverable)
code_under_review: consult.py, skills.py, spawn.py
type: verification
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: PR #2927 (github.com/tokenmaxxxer/on-the-record/pull/2927)
    sha: d3d49cbd9ce44e6b0dda854103bcaa078267911a
  - path: docs/issue-2920/reports/adversarial-review-e466be2e.md
    sha: 16e6bc5616ab98da3aed1b6eb36bd6c25629fb31
  - path: d3d49cbd9ce44e6b0dda854103bcaa078267911a:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-641ebdab.md
    sha: d3d49cbd9ce44e6b0dda854103bcaa078267911a
---

# issue-2920 — adversarial-review-2a32a671 record

skill-verdict: work-in-english — applied: invoked; loaded via Skill tool this session, followed for this record and commit language; final chat summary in Korean.

other mounted skills: not triggered. `adversarial-review` (the name this
task's own role names) was not mounted this session — canonical: this
session's own `docs/issue-2920/reports/consult-log/20260831T052702177588-1680005.md`,
`verb=skill_judge`, `outcome='ok: picked=[]...'`. That is a `spawn.py`
session-mount matching outcome for this session's own task text, a
different subsystem from consult's own selector resolution that this
issue's acceptance criteria target (verified below) — not a defect this
record's checks cover.

## What was done

Second independent adversarial review of PR #2927 (branch
`issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4`).
canonical: `gh pr view 2927 --json state,commits` — head commit
`d3d49cbd9ce44e6b0dda854103bcaa078267911a`, state OPEN. This PR already
carries one prior independent review — canonical:
`docs/issue-2920/reports/adversarial-review-e466be2e.md`, merged as
`16e6bc56` — whose two open findings were addressed by a later commit on
this same branch: canonical:
`d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-641ebdab.md`.
This round re-derives the PR's acceptance-relevant claims independently
(live code execution against the real on-disk skill-repository, not the
PR's own record read first) rather than re-trusting the chain.

Checked out the PR branch's changed source files
(`git checkout origin/issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4 -- consult.py skills.py spawn.py test/`)
on top of current `main` (`46779718`) in this workspace and ran every
check below live from there.

## Acceptance 1 — consult / `--skills` parity

checked: `python3 -c` importing `spawn`+`skills`,
`skills.resolve_consult_skill_source(n, repo)` vs
`skills.resolve_skill_source(n, repo)` for real skill names — result:
```
adversarial-review consult skills: ['adversarial-review', 'work-in-english'] unresolved: []
code-architecture  consult skills: ['code-architecture', 'work-in-english'] unresolved: []
adversarial-review --skills: ['adversarial-review']
code-architecture  --skills: ['code-architecture']
```
Both real skill names mount themselves under consult exactly as
`--skills` mounts them; consult additionally carries the always-on
`work-in-english` POLICY baseline (add-only, not a disagreement per the
issue's "must not treat work-in-english as fatal" clause).

Multi-skill consult (comma form, `--skills`'s own syntax) — derived:
`skills.resolve_consult_skill_source('adversarial-review,code-architecture', repo)['skills']`
— result: `['adversarial-review', 'code-architecture', 'work-in-english']`.

Empty/unresolved-selector visibility — derived:
`skills.resolve_consult_skill_source(n, repo)` for `'conformance-review'`
and `'totally-bogus-xyz'` — result:
```
conformance-review  consult skills: ['work-in-english'] unresolved: ['conformance-review']
totally-bogus-xyz   consult skills: ['work-in-english'] unresolved: ['totally-bogus-xyz']
```
Neither call raised `SystemExit` (consult's argument stays free-form,
issue #2569).

`--skills` validation unweakened — derived:
`skills.resolve_skill_source('conformance-review', repo)` — result:
`SystemExit("모르는 스킬 conformance-review — 쓸 수 있는 이름: ...adversarial-review...work-in-english")`
(truncated; full name list included, `--skills` still fails closed on
the same name consult reports as `unresolved` rather than raising).

All four checks above reproduce the same shape as PR #2927's own record
and the prior independent review — canonical:
`d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md`,
section "Acceptance demonstration (executed-live)".

## Acceptance 2 — retirement-count on the resolution-path files

derived: `python3 gates/retirement_count.py` (run in this workspace,
PR-head files checked out) — result: `retirement_count: 1100
occurrence(s) of the retired role/roles axis in py/sh sources (docs/
excluded)`. This matches round-2's own corrected number — canonical:
`d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-641ebdab.md`,
"1101 → 1100 after the round-2 rename" — re-derived here on the actual
checkout rather than re-trusted from that record.

`gates/retirement_count.py` takes no file-list argument — checked:
reading `gates/retirement_count.py`'s `main()` (only accepts
`--list-files`) — so the identifier check below is bounded to the three
resolution-path files this issue's population names (`consult.py`,
`skills.py`, `spawn.py`), applied by hand via `grep`:

derived: `git diff main <PR-head> -- consult.py skills.py spawn.py |
grep '^+' | grep -iE '\brole' | wc -l` — result: 11 lines. All 11 read as
Korean docstring/comment prose citing "the retired role axis /
role->skill table / retired role name" in past tense — checked: reading
every one of the 11 matched lines directly — result: each line is
comment/docstring text (no `def`, parameter, dict key, or variable name
among them).

derived: `grep -nE "def [a-zA-Z_]*role[a-zA-Z_]*\(" consult.py skills.py
spawn.py` — result: empty (no `role`-named function).
derived: `grep -nE "def [a-zA-Z_]+\([^)]*\brole\b" consult.py skills.py
spawn.py` — result: empty (no `role`-named parameter). The one remaining
identifier round-2's own record explicitly disposes of, `a.role`
(spawn.py's argparse dispatch attribute — which command form was typed,
not a skill selector), pre-dates this issue and is untouched by this
diff — checked: `git diff main <PR-head> -- spawn.py` shows only a
single changed line, a re-export/docstring line, not `a.role`'s
declaration.

## Acceptance 3 — empty-mount corpus prevalence

derived: `find docs -iname "consult-log.md" | wc -l` — result: 33.
derived: `find docs -iname "consult-log.md" -exec cat {} \; | wc -l` —
result: 153.
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -c "^- "`
— result: 147.
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -oE
"verb=[a-zA-Z_]+" | sort | uniq -c` — result: 53 `verb=consult`, 80
`verb=skill_judge`.
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -c
"mounted="` — result: 0 (the field this PR adds; the historical corpus
predates it).
derived: `ls runs/consult-logs` — result: no such directory (gitignored,
ephemeral).

All five numbers above reproduce exactly against PR #2927's own record
— canonical:
`d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4.md`,
section "Evidence — corpus bound for acceptance #3" — re-run
independently rather than re-trusted.

Selector-kind breakdown of the 53 `verb=consult` entries — derived:
`find docs -iname "consult-log.md" -exec cat {} \; | grep "verb=consult"
| grep -oE "role=[^ ]+" | sort | uniq -c | sort -rn` — result:
```
26 implementation
20 requirements-engineering
 2 architecture
 1 product-management
 1 product-discovery
 1 legal-compliance
 1 defect-verification
 1 conformance-review
```
(historical trace lines carry the field literally spelled `role=` — the
trace format's field label changed to `skill=` in the current code, but
already-committed historical lines are not rewritten retroactively).
26+20+2+1+1+1+1+1 = 53, matching the count above. This reproduces the
same 8-bucket table as PR #2927's own record; 52/53 of these entries are
selector strings that are directory-name prefixes but not exact
skill-repository directory matches — checked: `skills.resolve_skill_source(n, repo)`
for each of the 7 non-`product-management` names above, run
individually — result: all 7 raise `SystemExit` (no exact directory
match), the remaining 1 (`product-management`) also matches no
skill-repository directory. All 80 `verb=skill_judge` lines and all 153
total lines carry 0 `mounted=` occurrences (derived above), so the full
historical corpus is undeterminable for "mounted only work-in-english" —
reported here as its own bucket, not folded into either side, per the
acceptance check's population clause.

## Regression check — full test suite before/after

derived: `python3 -m pytest test/ -q` on the PR-head checkout (this
workspace, files checked out from the PR branch) — result: 528 passed,
3 xfailed, 15 failed.
derived: `python3 -m pytest test/ -q` on unmodified `main` (`46779718`,
`git stash` / `git stash pop` around the same checkout) — result: 513
passed, 3 xfailed, 15 failed.
528 - 513 = 15, matching derived: `python3 -m pytest
test/test_consult_skill_resolution_2920.py -q` — result: 15 passed (the
new test file in full).
checked: diffing the two runs' `FAILED` line lists — result: the 15
failing test names are identical between the PR-head and `main` runs.
checked: reading one representative failure's traceback from the
pytest output — result: `fatal: 'origin' does not appear to be a git
repository` (a `git fetch` against a sandboxed/absent `origin` remote),
unrelated to this change.

## Why

This round's aim was not to re-litigate whether the fix is correct.
canonical: `d3d49cbd:skills.py`'s `resolve_consult_skill_source()`
(the `unresolved` list-comprehension excluding `_STATIC_POLICY_SKILLS`
members) and `d3d49cbd:test/test_consult_skill_resolution_2920.py`
(both read directly in this session's checkout) — the two fixes the
prior review (`adversarial-review-e466be2e`) asked for are present at
PR head `d3d49cbd`: the POLICY-skill-exclusion fix, and the renamed
test function
(`test_retired_family_prefix_no_longer_pulls_in_family_members`,
checked: `grep -n "def test_retired" test/test_consult_skill_resolution_2920.py`
— result: only that name present, the old
`test_retired_role_name_no_longer_pulls_in_family_members` absent).

This round's aim was to check whether a chain of two prior records (the
PR's own, and the review that corrected part of it) still holds against
the current PR head — worth doing because round-2's own record
documents PR #2927's *first* record containing an incorrect
self-reported number. canonical:
`d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-641ebdab.md`,
section "Re-derivation of Finding 1's numbers" (quoted verbatim from
that record): "This matches the adversarial review's re-derivation...
not PR #2927's own claimed 1135 → 1098" and "17, not the claimed 14" —
derived there via `python3 gates/retirement_count.py` at merge-base
`85d9f61d` (1135) and at PR commit `61990112` (1101), both re-run by
that record, not retyped here. Every number in this record's Acceptance
sections above was reproduced independently in this workspace before
reading round-2's derivation section in detail, and every one of them
agrees with round-2's corrected values.

## What did not work

None.

## Upstream basis

- PR #2927, branch
  `issue-2920/refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4`,
  head `d3d49cbd9ce44e6b0dda854103bcaa078267911a` — canonical: `gh pr
  view 2927 --json state,commits,files` (checked above) — the
  deliverable under review, checked out and executed live in this
  workspace.
- `docs/issue-2920/reports/adversarial-review-e466be2e.md`
  (sha `16e6bc5616ab98da3aed1b6eb36bd6c25629fb31`) — the prior
  independent review.
- `d3d49cbd:docs/issue-2920/reports/refactoring-legacy-seam-selection+silent-failure-audit-641ebdab.md` —
  the round-2 fix record responding to that prior review's findings.

## Open findings

**judge_cmd family-coverage loss for legacy plain-role-named merge
records — informational, not a defect in this PR's diff.** derived:
`patrol_wiring._merge_skills()` called live with two synthetic
record-path strings, one with an old plain role slug and one with a
compound skill-plus-suffix slug — result: `['adversarial-review-abc123',
'implementation']` — confirming this function extracts a bare `<name>`
straight from a merge's own touched `docs/issue-<n>/reports/<name>.md`
record filenames and hands it unmodified to `judge_cmd()`. canonical:
`d3d49cbd:consult.py`'s `_readonly_plugin_dirs()` docstring (rewired in
this PR to `resolve_consult_skill_source()`'s exact-name resolution,
read directly) — for a name like `implementation` with no matching
skill-repository directory (confirmed unresolved in Acceptance 3
above), a judge session for that merge now mounts only the POLICY
baseline instead of the family a retired role name used to expand to.
`_readonly_plugin_dirs()`'s own docstring in this PR already names this
exact loss and states it is deliberate and out of this issue's scope
(consult's empty-mount visibility, not judge-trace expansion) — this
finding is filed only as a pointer for a future session auditing
`patrol_wiring`'s judged-merge coverage; no action requested against
this PR.

**Secondary (issue body) truncated-refusal-message item — unaddressed,
correctly out of scope.** checked: `skills.py:140`,
`f"쓸 수 있는 이름: {', '.join(available)}"` — unchanged by
`git diff main <PR-head> -- skills.py` around that line. The issue's
own "Secondary" section marks this item as secondary and it is not one
of the three acceptance checks; no action requested against this PR. A
candidate for its own follow-up issue if the orchestrator wants one
filed.

## Next steps

None.
