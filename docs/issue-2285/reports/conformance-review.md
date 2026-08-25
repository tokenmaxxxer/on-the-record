---
issue: 2285
role: conformance-review
author: conformance-review
loop_state: closed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
  - path: consult.py
    sha: 0baac6010bb12baf3adb42d025f51885e8433892
  - path: docs/specs/consult-guidance-source.md
    sha: 0baac6010bb12baf3adb42d025f51885e8433892
  - path: test/test_consult_no_rulebook_identity_regression.py
    sha: 0baac6010bb12baf3adb42d025f51885e8433892
  - path: docs/issue-2285/reports/implementation.md
    sha: 579fa7027836ff78e4909cbf4b2309cbae2d1f8d
subject: PR #2344 ("issue-2241 stage 2: confirm consult.py's guidance source, role identity stays exposed"), branch issue-2285/implementation, commit f50e689f2a1509cedc1192cdf755b9ddc513887e
test: docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md ("Constraints", "What will be done", "Out of scope", "How you'll know it worked", "Rollback") and issue #2285 ("## Acceptance" plus the operator-frozen-constraint comment, 2026-08-25T01:27:57Z)
result: failed
assertedBy: conformance-review, issue-2285/conformance-review session, 2026-08-25
---

# issue-2285 — conformance-review record

## What was done

Builder-blind conformance review of PR #2344 against the stage-2
proposal (`docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
on `main`, `ccee895`) and issue #2285. Fetched the PR's branch
(`origin/issue-2285/implementation`, tip `f50e689f`) into a separate
git worktree (`/tmp/review-2344`) and independently re-derived every
checkable clause there — re-grepped `consult.py`/`skills.py` line
numbers myself, reran every acceptance command myself — rather than
re-reading `579fa702:docs/issue-2285/reports/implementation.md`'s
claims and trusting them.

Two of the three deliverable paths are new files this stage creates
and are untracked on this `issue-2285/conformance-review` branch's own
working tree (this stage's actual deliverable landed on the separate
`issue-2285/implementation` branch): `0baac601:docs/specs/consult-guidance-source.md`,
hereafter "the spec doc", and `0baac601:test/test_consult_no_rulebook_identity_regression.py`,
hereafter "the regression test". Both names below refer to these same
two `0baac601`-pinned files; `consult.py` itself already exists on
every branch since it predates this stage.

canonical: requirement-block count in this record
```
grep -c '^requirement:' docs/issue-2285/reports/conformance-review.md
```
derived: this command, run in this session against this file after
writing it, counts eleven `requirement:` lines (`R1` through `R11`
below); verdict tally by grep over the same blocks:
```
grep -c '^verdict: Present' docs/issue-2285/reports/conformance-review.md
grep -c '^verdict: Incorrect' docs/issue-2285/reports/conformance-review.md
```
derived: ten `Present`, one `Incorrect` (`R5`).

## Why

Full enumeration (not sampling), per conformance-review-sampling-derivation:
the stage's actual code+doc+test surface is three files (`consult.py`,
the spec doc, the regression test) — small enough that every clause in
the proposal's Constraints/What-will-be-done/Out-of-scope/How-you'll-
know-it-worked sections, plus issue #2285's own Acceptance and
operator-frozen-constraint comment, could be checked directly with no
efficiency gain from spot-checking.

Independent re-derivation, not citation-checking the implementation
record, because "builder-blind" is this session's own mandate: every
line-number claim in the spec doc was re-grepped against the actual
post-commit `consult.py`, not accepted from the spec doc's or the
implementation record's prose — this is what surfaced R5 below:
`579fa702:docs/issue-2285/reports/implementation.md`'s Deviations
section claims it corrected the proposal's stale citations, but the
"corrected" numbers are themselves stale against the very commit that
introduces them (see R5's acceptance block).

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
  on `main`, `ccee895997e7629495aee4ff7c0588e3082c75bc` — the
  authoritative spec; its `files:`, Constraints, Out of scope, and
  Rollback apply verbatim per issue #2285's own text.
- `0baac6010bb12baf3adb42d025f51885e8433892` — the delivery commit
  (`consult.py`, the spec doc, the regression test), read directly in
  a separate worktree (`/tmp/review-2344`), not via the PR diff view
  alone.
- `579fa702:docs/issue-2285/reports/implementation.md` — read for its
  claims, not trusted as evidence; every claim this review's verdicts
  rely on was independently re-run or re-grepped (see requirement
  blocks).
- Issue #2285 body and its operator-frozen-constraint comment
  (2026-08-25T01:27:57Z) — backward-traced before checking
  implementation evidence against them.

## Open findings

---
requirement: "frozen write set matches the proposal's `files:` list exactly (`consult.py`, the spec doc, the regression test)"
spec_ref: "proposal frontmatter, `files:`"
verdict: Present
evidence: "`0baac6010bb12baf3adb42d025f51885e8433892` diff --stat touches exactly those three paths, no others"
rationale: "Exact match against the frozen list. The two later commits on the PR branch (`579fa702`, `f50e689f`) add only this issue's own record docs (`579fa702:docs/issue-2285/reports/implementation.md`, its `deviation-log.md`) and an append to `docs/reports/product/priorities.md` — record/log paths outside the stage's `files:` list but within the contract's separate per-role record-writing allowance, not a deliverable-scope addition."
acceptance: `git show --stat 0baac6010bb12baf3adb42d025f51885e8433892` (this session, worktree /tmp/review-2344) — result:
```
consult.py                                            |  6 ++++++
docs/specs/consult-guidance-source.md                 | 59 ++++++++++++++++++
test/test_consult_no_rulebook_identity_regression.py  | 77 +++++++++++++++++
3 files changed, 142 insertions(+)
```
---
requirement: "Constraints: no new role-shaped lookup structure introduced (`single-skill-axis`); `_ROLE_SKILLS` and the `roles/<role>.json` existence-check are not touched (collapses Constraints bullets 1-2 and Out-of-scope bullets 1-2, same evidence, per traceability rule 4)"
spec_ref: "proposal '## Constraints' (both bullets); '## Out of scope' (bullets 1-2)"
verdict: Present
evidence: "`skills.py` carries zero diff lines in commit `0baac601` (`git show 0baac601 -- skills.py` empty); `0baac601:consult.py`'s only change at all five `roles/<role>.json` existence-check call sites is a 6-line Korean comment inserted before the first one"
rationale: "Inspection (structural/static property, rule 1) confirms both constraints hold literally — a comment is not a structural lookup change."
acceptance: `git show 0baac6010bb12baf3adb42d025f51885e8433892 -- skills.py | wc -l` (this session) — result:
```
0
```
full review of `git show 0baac6010bb12baf3adb42d025f51885e8433892 -- consult.py` — single hunk, all added lines inside a `#`-comment block, zero removed/non-comment lines.
---
requirement: "Out of scope: no change to `board-gate.sh` or `merge_gate.py`"
spec_ref: "proposal '## Out of scope', bullet 3"
verdict: Present
evidence: "same `0baac601` diff --stat as R1 above — neither path appears"
rationale: "Inspection; disjoint from the three-file diff cited under R1's acceptance block."
---
requirement: "the spec doc exists, documents unconditional skill-repo resolution via `resolve_role_source()` for every role, and states `role` staying exposed as a lookup key is deferred to later stages of the issue #2241 program (not this one)"
spec_ref: "proposal '## What will be done', bullet 1"
verdict: Present
evidence: "the spec doc's '## Claim' section states the unconditional-resolution claim; its '## What stays exposed, on purpose' section names `_ROLE_SKILLS` and the existence-check and attributes their migration/removal to later stages of the issue #2241 program"
rationale: "Content matches the proposal's stated intent exactly."
---
requirement: "the spec doc's citations resolve against the current `consult.py`/`skills.py` line ranges"
spec_ref: "proposal '## How you'll know it worked', bullet 2"
verdict: Incorrect
spec_vs_built: "Spec requires: the spec doc's citations resolve against the current consult.py/skills.py line ranges. Built: every consult.py citation in the spec doc points six lines above its actual target statement in the same commit's consult.py — e.g. the citation for consult_cmd()'s resolve_role_source() call lands inside an unrelated docstring about cache-flag measurements, not the call itself. The two skills.py citations are accurate — skills.py has zero diff in this commit (see R2's acceptance block)."
evidence: "the spec doc's citation list; independently re-derived actual line numbers via `git show 0baac601:consult.py | grep -n` in this session (worktree /tmp/review-2344)"
rationale: "Incorrect, not Surface, per verdict-assignment rule 2 — the citations don't merely fail to fire, they actively name the wrong statement in the same file/commit they claim to describe. Re-checked twice before finalizing (rule 6): (a) grep -n for the exact call-site line numbers in the post-commit tree, (b) an awk excerpt of the actual content sitting at each cited line number, confirming the citation for _readonly_plugin_dirs()'s call lands inside its docstring rather than the call line. The offset across every consult.py citation (and only consult.py citations) matches the length of the six-line Korean comment this same commit inserts at the first existence-check call site — the citations were computed against a pre-comment version of the file and never recomputed after the comment was added. 579fa702:docs/issue-2285/reports/implementation.md's Deviations section claims the opposite (that it corrected the proposal's stale citations to 'the actual current locations'), but the 'corrected' numbers are themselves stale against the very commit that introduces them."
acceptance: `git show 0baac6010bb12baf3adb42d025f51885e8433892:consult.py | grep -n '_sp.resolve_role_source(role\|f = _sp.ROOT / "roles"'` (this session, worktree /tmp/review-2344) — result:
```
355:        f = _sp.ROOT / "roles" / f"{role}.json"
642:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
690:        f = _sp.ROOT / "roles" / f"{role}.json"
816:        f = _sp.ROOT / "roles" / f"{role}.json"
916:    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
1155:        f = _sp.ROOT / "roles" / f"{role}.json"
1304:    f = _sp.ROOT / "roles" / f"{role}.json"
1309:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
```
derived: none of the spec doc's eight consult.py line citations match a line shown above; every one of them equals the true line above minus the six-line comment block's own length.
---
requirement: "the regression test exists and asserts no code path in `consult.py` reads a rulebook/plugin-repo identity for guidance content"
spec_ref: "proposal '## What will be done', bullet 2"
verdict: Present
evidence: "the regression test — NoRulebookIdentityInSource (static scan for retired identifiers) + ReadonlyPluginDirsUnconditionalSkillRepo (behavioral check that _readonly_plugin_dirs() reaches resolve_role_source() identically for a mapped and an unmapped role)"
rationale: "Test method reused (rule 4 of verification-method-selection) since the test already exists in the repo; rerun independently rather than trusting the pasted implementation-record output."
acceptance: `python3 -m pytest -v` on the regression test (this session, worktree /tmp/review-2344, HEAD f50e689f, run against the file cited above) — result:
```
NoRulebookIdentityInSource::test_consult_py_carries_no_forbidden_rulebook_identifiers PASSED
ReadonlyPluginDirsUnconditionalSkillRepo::test_unmapped_role_still_resolves_through_resolve_role_source PASSED
ReadonlyPluginDirsUnconditionalSkillRepo::test_mapped_role_takes_the_same_single_path PASSED
3 passed in 2.46s
```
---
requirement: "`consult.py` carries an inline comment at the first existence-check call site pointing at the proposal and naming later stages of the issue #2241 program as owning `_ROLE_SKILLS`/the existence-check"
spec_ref: "proposal '## What will be done', bullet 3"
verdict: Present
evidence: "0baac601:consult.py, the six-line Korean comment immediately preceding the first `roles/<role>.json` existence-check call site — cites the spec doc, names later stages for the key-shape migration and the existence-check removal, and cites skills.py's _ROLE_SKILLS"
rationale: "Matches the proposal's literal instruction."
---
requirement: "Rollback: reverting the spec doc + the regression test leaves `consult.py`'s actual code change as comment-only, no runtime effect (also satisfies issue #2285's Acceptance 'empty state:' clause — same evidence, collapsed per traceability rule 4)"
spec_ref: "proposal '## Rollback'; issue #2285 '## Acceptance', 'empty state:' line"
verdict: Present
evidence: "git show 0baac6010bb12baf3adb42d025f51885e8433892 -- consult.py (this session) — single hunk, all added lines inside a #-prefixed comment block, zero removed or non-comment lines (same diff cited under R2's acceptance block)"
rationale: "Inspection is sufficient here (rule 1: structural/static property) — a comment-only diff cannot change runtime output, so 'byte-identical' behavior on rollback follows directly without a live rollback-and-diff run."
---
requirement: "No behavior change to `consult.py`'s output for any existing caller; existing consult tests pass unmodified (also satisfies issue #2285's Acceptance 'gate:' line — same evidence, collapsed per traceability rule 4)"
spec_ref: "proposal '## How you'll know it worked', bullet 3; issue #2285 '## Acceptance', 'gate:' line"
verdict: Present
evidence: "reran independently in worktree /tmp/review-2344, HEAD f50e689f"
rationale: "Test method reused; results match 579fa702:docs/issue-2285/reports/implementation.md's pasted output exactly (identical pass counts), corroborating the record's 'executed-live' provenance claim (issue #2285 Acceptance, 'provenance:' line) as genuine rather than fabricated."
acceptance:
```
$ python3 -m pytest tests/test_spawn_consult_panel.py -q
58 passed, 1 xfailed in 1.67s
$ python3 -m pytest test/test_spawn_role_skill_resolution.py -q
9 passed in 3.32s
$ python3 gates/spec_index.py
통과: 모든 spec 문서가 기록된 해시와 일치한다
```
---
requirement: "operator-frozen constraint holds: systemic for every consumer session/repo, no added per-spawn/steady-state overhead, no new conflict surfaces, no stall/deadlock mode, no consumer-tree pollution"
spec_ref: "issue #2285 comment by JiwonJung94, 2026-08-25T01:27:57Z"
verdict: Present
evidence: "0baac601's only consult.py change is the comment covered under R2/R8's acceptance blocks; the spec doc and the regression test add no production code path"
rationale: "Analysis, per verification-method-selection rule 2 — a systemic no-overhead claim across every consumer session/repo isn't reproducible as one local run. A comment carries zero runtime cost, the spec doc is never read at runtime, and the regression test only runs under pytest's own collection — there is no new code path any consumer session executes, so there is no mechanism for added overhead, a new contention point, or consumer-tree residue."
---
requirement: "phase-2 delivery PR carries `Closes #2285`"
spec_ref: "role-handoff contract v3, PR trailer phase split"
verdict: Present
evidence: "PR #2344 body carries the literal trailer `Closes #2285`"
rationale: "Matches the contract's phase-2 requirement exactly."
acceptance: `gh pr view 2344` (this session) — result: PR body's last line before the test plan reads `Closes #2285`.
---

## Next steps

canonical: verdict tally cited under "What was done" above (`grep -c '^verdict: '`, this session)

`R5` is a real, reproducible defect against an explicit acceptance
clause, not a false positive (re-checked twice, see R5's rationale)
and not a design deviation graded correct elsewhere in this record.

acceptance: `git show 0baac6010bb12baf3adb42d025f51885e8433892:consult.py | grep -n '_sp.resolve_role_source(role\|f = _sp.ROOT / "roles"'` (this session, rerun of R5's acceptance block) — result:
```
355, 642, 690, 816, 916, 1155, 1304, 1309
```
Flagged for whoever owns the next pass on the spec doc: recompute
every consult.py citation against the eight post-comment lines shown
above (the exact statement each belongs to is spelled out in R5's own
acceptance block); also re-run `python3 gates/spec_index.py --update`
if that gate is ever extended to auto-register new `docs/specs/*.md`
files (today it only rewrites hashes for a curated row list already
present in `docs/specs/reconciled-index.md` and does not add new rows
— confirmed by reading `gates/spec_index.py`'s `update()` function
directly, not assumed).

This is a documentation citation-drift defect, not a functional
regression: every Constraints/Out-of-scope boundary, the regression
test, the existing-test gate, the rollback/empty-state claim, and the
operator-frozen constraint are all `Present`, independently
re-derived above. `loop_state: closed` — nothing here blocks the
stage; the citation fix is a follow-up for the spec doc alone.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the proposal's bundled Constraints/Out-of-scope bullets and issue #2285's Acceptance clauses into discrete line items, then collapsed same-evidence duplicates (R2, R8, R9) back down per traceability rule 4 rather than double-counting them as separate findings.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Inspection for R1/R2/R3/R4/R7/R8 (structural/static properties), Test (reused + independently rerun) for R6/R9, Analysis for R10 (systemic no-overhead claim not reproducible as one run).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Incorrect (not Surface or Absent) to R5 since the citations actively name the wrong statement rather than merely omitting or failing to fire on one; re-checked R5's evidence twice before finalizing per rule 6; named the failing clause via spec_vs_built.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation carries a file:line or sha:path pointer to the exact commit read, backward-traced the proposal and issue #2285's Acceptance/operator-constraint text before checking implementation evidence, collapsed R2/R8/R9's duplicate-evidence sub-clauses into single entries with the duplication noted inline.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote one `---`-delimited requirement block per extracted requirement below the header block, each carrying requirement/spec_ref/verdict/evidence/rationale (plus spec_vs_built on the one Incorrect verdict), refusing none for missing evidence since all eleven were checkable from the artifact.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the stage's three-file change surface was feasible; no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; its outputs are conformance verdicts (Present/Incorrect), not severity-banded defects.
skill-verdict: implementation-audit — not-applicable: this session already operates under the native role-handoff contract's builder-blind conformance-review protocol (this task's own governing process, structurally equivalent to the marketplace skill's two-session audit shape); invoking the marketplace skill's own procedure would duplicate rather than add distinct verification.
