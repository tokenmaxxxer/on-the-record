---
issue: 2288
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
subject: PR #2480 (https://github.com/tokenmaxxxer/on-the-record/pull/2480), commit 38b0c272 (code) / 10510bec (implementation record, PR head)
test: docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md#how-youll-know-it-worked
result: passed
assertedBy: conformance-review (issue-2288/conformance-review session)
---

# issue-2288 — conformance-review record

## What was done

Builder-blind conformance review of PR #2480 ("rewrite observer-pair
matching onto record-kind (role retirement stage 5)") against the
acceptance the stage-5 proposal itself states
(`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`)
and issue #2288's own Acceptance section (gate, empty-state, and
executed-live provenance requirements). Extracted 17 discrete, checkable
requirements from the proposal's `## What will be done`, `## Constraints`,
`## Out of scope`, `## How you'll know it worked`, and `## Rollback`
sections plus issue #2288's `## Acceptance` section — the diff is 573
insertions / 39 deletions across 7 files (canonical:
`git diff --stat $(git merge-base origin/main pr-2480-review) pr-2480-review`,
worktree `/tmp/pr2480-worktree` @ 10510bec), small enough for full
enumeration — no separate sampling scope was derived.

`docs/handbooks/observer-verification.md` (untracked on this branch),
`docs/issue-2288/reports/implementation.md` (untracked on this branch),
and `test/test_merge_gate_record_kind.py` (untracked on this branch) are
new in PR #2480 and exist only on the reviewed PR branch; every citation
below to any of the three was read from
`git fetch origin pull/2480/head:pr-2480-review`, checked out in a
disposable worktree at `/tmp/pr2480-worktree`. Every acceptance command
below was re-run there by this review, not copied from the PR body or
from `docs/issue-2288/reports/implementation.md` (untracked on this
branch).

acceptance: `python3 -m pytest gates/test_merge_gate.py tests/test_spawn_on_pr.py test/test_merge_gate_record_kind.py test/test_record_kind_field.py gates/test_record_lint.py -q` (worktree `/tmp/pr2480-worktree` @ 38b0c272) — result:
```
........................................................................ [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
147 passed in 1.52s
```

acceptance: `grep -rln "PR_TRIGGERED_ROLES\|applicable_roles\b\|_exempt_own_role\b" --include="*.py" .` (worktree `/tmp/pr2480-worktree` @ 38b0c272) — result: no output (no remaining references).

acceptance: live parity check against this repo's actual current board (proposal's third "How you'll know it worked" bullet), re-run independently rather than trusting the pasted PR/implementation-record output — result:
```
subjects checked: 591
mismatches: 0
```

derived: same 591/0 result independently obtained by this review's own
re-run of the parity script above, matching the claim pasted in
`docs/issue-2288/reports/implementation.md` (untracked on this branch)
"Acceptance" section.

acceptance: `python3 -m pytest test/ gates/ -q -m "not slow"` (worktree `/tmp/pr2480-worktree` @ 38b0c272) — result:
```
3 failed, 1270 passed, 8 xfailed in 20.59s
```
derived: the 3 failures — `test/test_local_dependency_env.py`
(`CallSiteWiringTest.test_origin_captured_before_workspace_reassignment`),
`test/test_spawn_artifact_skill_pairing.py`
(`SpawnOneArtifactSkillPairingTest.test_no_declaration_line_byte_identical_to_baseline`),
`test/test_spawn_cross_family_skill_selection.py`
(`SpawnOneCrossFamilyAcceptanceTest.test_non_matching_task_mounts_and_directive_byte_identical_to_baseline`)
— were confirmed pre-existing and unrelated to this PR by re-running the
same three node IDs against `origin/main` in the same worktree
(`git checkout origin/main -- .` then re-run): identical 3 failures
reproduced, none of the three files touching `gates/merge_gate.py`,
`gates/spawn_on_pr.py`, or any other file in this PR's diff.

Requirement-by-requirement verdicts:

---
requirement: `gates/spawn_on_pr.py`'s `PR_TRIGGERED_ROLES` becomes `PR_TRIGGERED_RECORD_KINDS` (same two values); `applicable_roles()` becomes `applicable_record_kinds()`, scanning board entries' `kind:` field instead of filename
spec_ref: proposal `## What will be done`, bullet 1
verdict: Present
evidence: canonical: 38b0c272:gates/spawn_on_pr.py:39 (`PR_TRIGGERED_RECORD_KINDS = ("execution-observation", "conformance-review")`); canonical: 38b0c272:gates/spawn_on_pr.py:70-102 (`applicable_record_kinds()`, `kind_field = fm.get("kind")` checked first)
rationale: both renames exist at the cited lines with the same two values, and the function body matches on the `kind:` field (with a documented OR-fallback to filename, see the next requirement) rather than presence-only filename matching.
---
requirement: `applicable_roles()`'s filename-based fallback is preserved as an OR condition (not a narrower absent-only fallback), so pre-vocabulary ad hoc `kind:` values don't spuriously regress a subject's missing-verification status
spec_ref: proposal Rationale ("checks for the presence of two record-kind values... cross-referenced against author"); implementation record's "What did not work" section
verdict: Present
evidence: canonical: 38b0c272:gates/spawn_on_pr.py:96-98 (`matched = kind_field if kind_field in kinds else (name if name in kinds else None)` — filename checked independently of what, if anything, `kind_field` holds, not only when it's `None`)
rationale: the live parity re-run (591 subjects, 0 mismatches, reproduced independently above) is exactly the regression this fallback exists to prevent, and it passes; `test_kind_field_wins_over_filename` and `test_legacy_record_without_kind_field_falls_back_to_filename` in `test/test_merge_gate_record_kind.py` (untracked on this branch) and `tests/test_spawn_on_pr.py` cover both directions of the OR and are part of the 147-passed run above.
---
requirement: `gates/merge_gate.py required_verification_missing()` delegates to the renamed `applicable_record_kinds()`
spec_ref: proposal `## What will be done`, bullet 2 (first clause)
verdict: Present
evidence: canonical: 38b0c272:gates/merge_gate.py:143-160 (`required_verification_missing()` calls `spawn_on_pr.applicable_record_kinds(subject_board, subject_author=subject_author)`)
rationale: the call site is present at the cited lines and is covered by `RequiredVerificationMissingIntegrationTest.test_reads_subject_author_from_the_implementation_record`, part of the 147-passed run above.
---
requirement: `_exempt_own_role`'s circularity-breaking logic is preserved, re-keyed on `author:` matching the subject's own author instead of branch-name matching
spec_ref: proposal `## What will be done`, bullet 2 (second clause)
verdict: Surface
evidence: canonical: 38b0c272:gates/merge_gate.py:116-138 (`_exempt_own_record_kind()`) — the function's only comparison is still `own_kind = own_branch[len(subject) + 1:]; return [k for k in missing if k != own_kind]`; no `author:` field is read anywhere in this function, before or after the rename
rationale: the circularity-breaking logic is genuinely preserved (matches the first clause), and the rename happened, but the specific condition this clause names — the *exemption* itself re-keyed from branch-name matching to `author:` matching — does not fire; the function is unchanged branch-suffix matching under a new name. The overall self-verification requirement this bullet's neighboring bullet describes (a `kind:` match whose `author:` equals the subject's own does not count) is independently satisfied by `applicable_record_kinds()`'s `subject_author` parameter, checked separately below — so the *safety property* the Constraints section cares about holds, but this specific bullet's literal mechanism does not. See "Why" and "Open findings" below for why this is not treated as blocking.
---
requirement: Self-verification guard — a record-kind match whose `author:` equals the subject artifact's own `author:` does not count toward satisfying `required_verification_missing()`
spec_ref: proposal `## What will be done`, bullet 3; `## Constraints`, bullet 2
verdict: Present
evidence: canonical: 38b0c272:gates/spawn_on_pr.py:99-101 (`if subject_author is not None and fm.get("author") == subject_author: continue`); canonical: 38b0c272:gates/merge_gate.py:157-158 (`subject_author` read from the subject's own `implementation` record's `author:` field and threaded through)
rationale: the guard is implemented exactly as the Constraints section requires (kind-presence alone is insufficient, author-identity must also differ), and `test_self_verification_guard_blocks_same_author_as_subject` / `test_no_subject_author_skips_the_guard` in `test/test_merge_gate_record_kind.py` (untracked on this branch) plus `test_applicable_record_kinds_self_authored_does_not_satisfy` in `tests/test_spawn_on_pr.py` cover both the guard firing and the no-subject-author skip path, all part of the 147-passed run above.
---
requirement: `docs/handbooks/observer-verification.md` (untracked on this branch) documents the rewritten check and the self-verification guard explicitly
spec_ref: proposal `## What will be done`, bullet 4
verdict: Present
evidence: canonical: 38b0c272:docs/handbooks/observer-verification.md (untracked on this branch; new file, sections "What changed", "Kind-field matching, with a filename fallback", "Self-verification guard", "What did not change", "Rollback")
rationale: the file exists with the required content — the rewritten check's mechanism, the OR-fallback rule, and a dedicated section explaining the self-verification guard mechanically and by reference to issue #2241's non-goal.
---
requirement: no change to which two record-kinds are required, or to widening/narrowing the observer pair
spec_ref: proposal `## Out of scope`, bullet 1
verdict: Present
evidence: canonical: `git diff` `PR_TRIGGERED_RECORD_KINDS` value (see first requirement row) — still exactly `("execution-observation", "conformance-review")`
rationale: the tuple's two values are unchanged from the pre-PR `PR_TRIGGERED_ROLES`; only the name and matching mechanism changed.
---
requirement: no change to branch naming (stage 4) or write-scope (stage 3)
spec_ref: proposal `## Out of scope`, bullet 2
verdict: Present
evidence: canonical: `git diff --stat $(git merge-base origin/main pr-2480-review) pr-2480-review` (worktree `/tmp/pr2480-worktree`) — full file list: `docs/handbooks/observer-verification.md` (untracked on this branch), `docs/issue-2288/reports/implementation.md` (untracked on this branch), `gates/merge_gate.py`, `gates/spawn_on_pr.py`, `gates/test_merge_gate.py`, `test/test_merge_gate_record_kind.py` (untracked on this branch), `tests/test_spawn_on_pr.py` — 0 matches for `pipeline.py`, `roster.py`, `board.py`, `board-gate.sh`
rationale: the constraint is a negative (must-not-touch); the complete, directly-observed file list contains none of the stage-3/stage-4 write-set files.
---
requirement: single-enforcement-surface stays in `gates/` (core), never moves to a skill-side check
spec_ref: proposal `## Constraints`, bullet 3
verdict: Present
evidence: same file-list evidence as the row above — every code file touched (`gates/merge_gate.py`, `gates/spawn_on_pr.py`) is under `gates/`; no path under `skills/` appears in the diff
rationale: the complete file list contains no skill-side path, and both rewritten functions remain in their pre-existing `gates/` modules.
---
requirement: this stage lands only after stages 1 (record-kind exists), 3 (write-scope no longer role-gated), and 4 (naming stabilized) are landed and stable
spec_ref: proposal `## Constraints`, bullet 1
verdict: Present
evidence: canonical: `git log --oneline origin/main` — `debe31c8` (issue-2284, stage 1, #2317), `a34a3aa5` (issue-2286, stage 3, #2387/core PR #312), `2cc6d108` (issue-2432, stage 4) all present on `origin/main` at or before this PR's merge-base (`fcf0b5b9`)
rationale: all three prerequisite stages are on `main` and precede this PR's branch point; the sequencing constraint the proposal's Rationale calls "the risk mitigation itself" is satisfied.
---
requirement: subject board with both required `kind:` values present (different authors) reports no missing verification; missing one reports it by record-kind name, not role name
spec_ref: proposal `## How you'll know it worked`, bullet 1
verdict: Present
evidence: canonical: 38b0c272:test/test_merge_gate_record_kind.py:16-31 (untracked on this branch; `test_both_present_different_authors_reports_none_missing`, `test_one_missing_reported_by_record_kind_name`)
rationale: both cases are exercised by name-matching tests, part of the 147-passed run above; the two record-kind values are the same literal strings the old role check used, so "record-kind name" and "role name" coincide as values — the distinction the proposal draws is about matching mechanism (kind: field vs. filename), which the tests exercise via the `test_kind_field_wins_over_filename` case reviewed two rows up.
---
requirement: a `kind:` match whose `author:` equals the subject's own author does not satisfy the requirement (self-verification guard proven)
spec_ref: proposal `## How you'll know it worked`, bullet 1 (third clause)
verdict: Present
evidence: canonical: 38b0c272:test/test_merge_gate_record_kind.py:34-39 (untracked on this branch; `test_self_verification_guard_blocks_same_author_as_subject`)
rationale: same test file, part of the 147-passed run above; duplicate coverage of the guard-firing requirement already verified two rows up (self-verification guard), collapsed here as the proposal's acceptance-list phrasing of the same property.
---
requirement: `_exempt_own_role`'s (renamed) circularity-breaking path still prevents an observer's own PR from blocking on its own missing record, re-verified under the new author-keyed logic
spec_ref: proposal `## How you'll know it worked`, bullet 2
verdict: Present
evidence: canonical: 38b0c272:test/test_merge_gate_record_kind.py:60-71 (untracked on this branch; `ExemptOwnRecordKindTest.test_drops_only_the_supplying_prs_own_kind`, `test_other_subjects_pr_is_a_no_op`, `test_no_pr_context_is_a_no_op`) and `RequiredVerificationMissingIntegrationTest.test_reads_subject_author_from_the_implementation_record` (lines 79-96)
rationale: read narrowly (does the exemption still functionally work, in the context of the new author-keyed `applicable_record_kinds()` pipeline) rather than as a second demand that `_exempt_own_record_kind` itself read `author:`, this bullet is satisfied — the integration test exercises exactly the combination (a self-authored kind blocked by the guard, then the branch-derived exemption applied on top) and passes. The stricter reading of this bullet is the same mechanism flagged Surface three rows up; this row verifies the acceptance test as stated, not the stricter reading.
---
requirement: a live re-run of `required_verification_missing()` against this repo's current board produces the same missing-set as today's role-keyed version, for every subject where record-kind data already exists from stage 1 onward
spec_ref: proposal `## How you'll know it worked`, bullet 3
verdict: Present
evidence: acceptance block above ("live parity check"), re-run independently by this review — 591 subjects checked, 0 mismatches
rationale: re-run directly by this review against a freshly checked-out copy of the PR branch, not copied from the implementation record's pasted output — matches the claimed result exactly, and (per the same note the implementation record makes) holds for all 591 subjects on the live board today, not only the stage-1-onward subset the bullet scopes itself to.
---
requirement: rollback (revert `gates/merge_gate.py`/`gates/spawn_on_pr.py` to the role-matching version) does not strand any subject's verification state, since every stage-1-onward record carries both `role:`/filename and `kind:`
spec_ref: proposal `## Rollback`
verdict: Present
evidence: canonical: 38b0c272:docs/handbooks/observer-verification.md (untracked on this branch), "Rollback" section; supporting: the live parity result above (new kind-based matching agrees with presence-only role-style matching on the current board)
rationale: this claim concerns behavior under a reversion this review did not execute (rebuilding and running the reverted gate is out of this review's scope), so it is checked by Analysis rather than Test: the parity result shows the two matching schemes agree on every current subject, which is the condition under which a revert would not change any subject's evaluated state — a direct trace of the code (additive-only field, OR-matching that always includes the filename check) supports the same conclusion.
---
requirement: gate `gates/test_merge_gate.py` passes
spec_ref: issue #2288 `## Acceptance`, "gate"
verdict: Present
evidence: acceptance block above ("147 passed in 1.52s"), re-run independently, includes `gates/test_merge_gate.py`
rationale: re-run directly by this review; matches the implementation record's own claimed count and shows 0 failures.
---
requirement: empty state — with the stage unused/rolled back, prior-stage behavior is byte-identical (issue's own Acceptance section, distinct from the proposal's Rollback section it points to)
spec_ref: issue #2288 `## Acceptance`, "empty state"
verdict: Present
evidence: same as the Rollback requirement above — this issue-level Acceptance bullet is the same claim, checked the same way (Analysis via the parity result and the additive-field code trace)
rationale: identical basis to the Rollback requirement two rows up; recorded as its own line because it is a separate named bullet in the issue body, not because it needed separate evidence.
---
requirement: provenance is executed-live — the proposal's acceptance commands run against a real spawn/workspace with output pasted in the record
spec_ref: issue #2288 `## Acceptance`, "provenance"
verdict: Present
evidence: `docs/issue-2288/reports/implementation.md` (untracked on this branch) "Acceptance" section pastes command + output for all three checks (grep, pytest, live parity); this review independently re-ran all three in a freshly fetched worktree (see acceptance blocks above) and obtained matching results
rationale: this row checks the implementation record's own compliance with the issue's provenance requirement, distinct from this conformance-review's own re-run (which this record's own frontmatter/body separately documents) — both the builder's pasted evidence and this review's independent re-run agree.
---

## Why

Verification method per requirement followed the structural/dynamic
split: Inspection for static diff-shape properties (file scope,
`PR_TRIGGERED_RECORD_KINDS` value unchanged, no `skills/` path touched),
Test for behavioral claims covered by an executable test — reused via a
fresh re-run on a freshly fetched copy of the PR branch rather than
trusting the PR body's or implementation record's pasted output (per
this session's verify-at-landing obligation and the finding-record
skill's evidence-must-be-a-pointer-into-the-artifact rule), and Analysis
for the two claims this review cannot directly exercise without actually
performing a revert (Rollback / empty-state byte-identical behavior) —
traced from the code's additive-only field shape and the parity result
instead.

Full enumeration (17 requirements, all checked) rather than sampling:
the diff is small (573 insertions, 39 deletions, 7 files — canonical:
`git diff --stat` citation in "What was done" above) and the proposal's
own `## How you'll know it worked` plus issue #2288's `## Acceptance`
sections already name a short, closed acceptance list — deriving a
separate sampling scope on top of that would have re-derived a scope the
spec already stated.

One requirement (`_exempt_own_role`'s circularity-breaking logic ...
re-keyed on author: matching ... instead of branch-name matching",
proposal `## What will be done` bullet 2's second clause) is marked
Surface rather than Present: the literal wording names a change to the
*exemption function's own matching key* that the code does not make —
`_exempt_own_record_kind()` (`gates/merge_gate.py:116-138`) still
compares branch suffixes, not `author:` values, before and after the
rename. This is distinguished from the neighboring, separately-stated
self-verification-guard bullet (proposal `## What will be done` bullet
3), which *is* author-keyed and is independently Present. Read as two
requirements per the requirement-extraction skill's bundling rule
(splitting a sentence that bundles "logic preserved" with "re-keyed on
author" into two obligations) rather than one, the first clause is
squarely Present and the second is Surface. This is not treated as
blocking: canonical: 10510bec:docs/issue-2288/reports/implementation.md
(untracked on this branch) "Why" section discloses this exact deviation
and argues for it directly (the board `_exempt_own_record_kind()` reads
is the local working tree, not the PR-under-evaluation's branch, so
reading `author:` there would add an I/O round trip and break the
function's documented pure-function property; the branch suffix is a
valid proxy for that PR's own eventual `author:` value for these two
specific record-kinds, argued from `checkout_issue_branch`'s
branch-naming behavior being unaffected by stage 4 for this pair) —
this is a disclosed, reasoned judgment call against an arguably
underspecified spec sentence, not a silent divergence, and the safety
property the Constraints section actually cares about (self-verification
cannot be satisfied by kind-presence alone) is independently proven
Present via the neighboring guard. See "Open findings" below.

Verdict tally derived from the 17 requirement blocks above (count of
`verdict:` lines): 16 Present, 1 Surface, 0 Absent/Incorrect/Unverifiable.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the proposal's `## What will be done` bullet 2 (which bundles "circularity-breaking logic preserved" with "re-keyed on author: matching instead of branch-name matching") into two separate requirement rows per rule 1, dimension-tagged the full 17-item list (functional / edge-case / scope-boundary), and did not re-derive a sampling scope since the spec's own acceptance list was used verbatim per rule 4.
skill-verdict: conformance-review-sampling-derivation — not-applicable: the diff (573 insertions, 39 deletions, 7 files) was small enough for full enumeration, so no sampling scope was needed.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; routed static/structural properties (file scope, tuple values, `skills/` absence) to Inspection, reused the PR's own executable tests as Test-method evidence via a fresh re-run on a freshly fetched branch copy rather than re-deriving parallel manual checks, and routed the two revert/empty-state claims (which this review cannot exercise without performing an actual revert) to Analysis rather than asserting Present from an untested happy path.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; per the tally above, 16 of the 17 requirements reached Present only after locating reachable, active evidence; the remaining one (`_exempt_own_role` re-keyed on author) is Surface per rule 1 — matching code (the renamed function) exists but the specific condition the requirement clause names (author-keyed matching in that function) does not fire, verified by reading the function's full body rather than guessing from its name or docstring; re-checked once against the current artifact state (rule 6) before finalizing, since a rename-only diff is exactly the kind of near-miss this rule warns about.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation above pins file:line-range plus the commit sha actually read (38b0c272 for the code commit, 10510bec for the implementation-record/PR-head commit); the proposal's own version is pinned via its landing sha (135712e8e4c56195aa0dedab6060db1610f3dc13) in the frontmatter `upstream:` block; two requirement rows (self-verification guard proven, and the Rollback/empty-state pair) explicitly note they trace to the same underlying evidence as a neighboring row rather than filing silently-duplicated citations.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block above carries requirement/spec_ref/verdict/evidence/rationale, and the one Surface verdict names the specific clause ("re-keyed on author... instead of branch-name matching") the evidence fails to satisfy rather than a bare verdict label.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting; the one non-Present finding is recorded with its resolution path (non-blocking, disclosed and reasoned by the builder, safety property independently satisfied elsewhere) under finding-record's own procedure rather than banded.

## Upstream basis

canonical: 135712e8e4c56195aa0dedab6060db1610f3dc13:docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
— the stage-5 proposal this review checked PR #2480 against, verbatim
per issue #2288's own "Spec" pointer. Also read issue #2288's own body
(`## Acceptance` section: gate/empty-state/provenance) for the
acceptance requirements layered on top of the proposal's own "How
you'll know it worked", and canonical:
10510bec:docs/issue-2288/reports/implementation.md (untracked on this
branch) for the builder's claimed evidence, independently re-executed
by this review rather than trusted (see the `acceptance:` blocks above
this record's requirement list). Also read (not modified) canonical:
docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-
cutover.md `files:` frontmatter and canonical:
38b0c272:pipeline.py:1122-1146
(`checkout_issue_branch`/`checkout_issue_branch_for_skill` docstrings)
to independently verify the implementation record's own branch-naming
rationale for the Surface finding below, rather than taking that
rationale at face value.

## Open findings

None blocking. One disclosed, reasoned deviation, recorded above as
Surface rather than a defect:

canonical: 38b0c272:gates/merge_gate.py:116-138 — `_exempt_own_record_kind()`
still matches on branch-name suffix, not on an `author:` field read,
despite proposal `## What will be done` bullet 2's literal wording
asking for the exemption to be "re-keyed on `author:` matching...
instead of branch-name matching." canonical:
10510bec:docs/issue-2288/reports/implementation.md (untracked on this
branch) "Why" section discloses and argues for this directly (I/O-purity
and a from-first-principles argument that the branch suffix is a valid
proxy for this pair's eventual `author:` value, since `spawn_on_pr.py`
is outside stage 4's write set). This review finds that argument sound
as far as it goes: canonical: 38b0c272:spawn.py:2747 confirms
`checkout_issue_branch(cwd, issue, role)` is still what `_spawn_one()`
calls for these two kinds, and canonical:
docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-
cutover.md `files:` frontmatter confirms `spawn_on_pr.py` is not in
stage 4's write set — but it is a mechanism substitution for a spec
sentence specific enough to name the "instead of branch-name matching"
replacement, not a case where the spec was silent. Resolution path: no
code change requested by this review — the safety property in question
(self-verification cannot be satisfied by kind-presence alone) is
independently Present via `applicable_record_kinds()`'s
`subject_author` guard, so nothing is unenforced. Worth a plain word
for whoever writes stage 6 (role enum deletion, issue #2241's own next
step): if a future stage does move these two kinds onto skill-axis
branch naming (per `_exempt_own_record_kind`'s own docstring, which
already flags this), `_exempt_own_record_kind`'s branch-suffix proxy
stops being valid and would need the fuller `author:`-reading rewrite
this bullet's literal text already anticipated.

## Next steps

None — `loop_state: reported` is terminal for a `conformance-review`
record. This record checked PR #2480 (stage 5, last of the five staged
rewrites) only; stage 6 (role enum deletion) is issue #2241's own next
step, tracked separately.
