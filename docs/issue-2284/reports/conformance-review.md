---
issue: 2284
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2284/reports/implementation.md
    sha: 3808d7fbcca4066b461231b51ba37e7fbf4ececa
subject: issue-2284
test: python3 -m pytest test/test_issue_scoped_lease.py test/test_record_kind_field.py -v
result: passed
assertedBy: conformance-review (issue-2284/conformance-review, builder-blind)
---

# issue-2284 — conformance-review record

## What was done

canonical: this session's own re-execution, see command transcripts below and the per-requirement blocks under "Requirements and verdicts"

Builder-blind conformance review of PR #2317
(`issue-2284: stage 1 — issue-scoped lease, author identity, record-kind
vocabulary`, head `3808d7fbcca4066b461231b51ba37e7fbf4ececa`) against two
sources: (1) `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-
record-kind.md` on `main` (sha `ccee895997e7629495aee4ff7c0588e3082c75bc`)
— its own "How you'll know it worked" section, Constraints, and Out of
scope; (2) issue #2284's Acceptance block (gate, empty state, live
provenance) read live via `gh issue view 2284`.

Checked out PR #2317's head into an isolated worktree
(`git worktree add /tmp/pr-2317-review 3808d7fbcca4066b461231b51ba37e7fbf4ececa`)
and a separate worktree at `main` (`/tmp/main-review`, `d00aadf5`) to
diff pre/post behavior for the empty-state check. Ran every command
myself against those worktrees — never trusted PR #2317's own pasted
test-plan output or its implementation record's own claims as ground
truth, though the latter was read as one input per usual builder-blind
practice. PR #2317 is not merged as of this review, so none of its
changed files (including its own implementation record) exist in this
review's own branch's working tree — every reference to them below is
untracked here and reachable only via `git show <sha>:<path>` against
PR #2317's head, `3808d7fbcca4066b461231b51ba37e7fbf4ececa`.

Extracted 15 discrete, dimension-tagged requirements (7 from the
proposal's "How you'll know it worked", 5 from its Constraints/Out of
scope, 3 from issue #2284's Acceptance block). All 15 resolved to
**Present** on independent re-derivation. No Absent, Incorrect, or
Unverifiable findings.

Live commands actually executed (full output preserved in the
per-requirement blocks below):

```
$ cd /tmp/pr-2317-review && python3 -m pytest test/test_issue_scoped_lease.py -v
...
5 passed in 24.01s

$ cd /tmp/pr-2317-review && python3 -m pytest test/test_record_kind_field.py -v
...
5 passed in 4.58s

$ cd /tmp/pr-2317-review && python3 -m pytest test/ gates/ -q
1200 passed, 8 xfailed in 14.79s

$ cd /tmp/pr-2317-review && python3 gates/spec_index.py .
통과: 모든 spec 문서가 기록된 해시와 일치한다
```

## Why

canonical: this session's own per-requirement re-derivation below, cross-checked against the implementation record's own claims (untracked on this branch, reachable at 3808d7fbcca4066b461231b51ba37e7fbf4ececa) rather than accepted from them

The proposal freezes its own "How you'll know it worked" section as the
acceptance contract per issue #2284's own text ("The landed proposal's
own 'How you'll know it worked' section is the acceptance contract"),
and issue #2284 layers three more obligations on top (gate test, an
empty-state regression check, and executed-live provenance). Reviewing
builder-blind means treating the implementation record as one input to
check, not as ground truth — every claim in it that was checkable
independently was re-derived rather than copied, principally by diffing
`roster.py`/`spawn.py` between `main` and the PR head to confirm the
claimed "single call site" / "byte-identical" assertions structurally,
rather than trusting the record's prose.

## Requirements and verdicts

Dimension tags: `functional`, `error-handling`, `edge-case`,
`scope-boundary`. All file citations to PR #2317's changed files use
commit-pinned form `3808d7fb:<path>` — untracked on this review branch,
reachable only via `git show 3808d7fb:<path>` since PR #2317 is not yet
merged; citations to the spec use `docs/issue-2241/proposals/2026-08-25-
stage-1-lease-identity-record-kind.md` at `main`'s `ccee8959` (this one
does exist on `main`, and therefore on this branch too).

---
requirement: "Existing roster.py lease tests pass unmodified (byte-identical behavior for role-keyed callers)"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 1
dimension: functional
verification_method: Analysis + Test
verdict: Present
derived: `diff <(git show main:roster.py) <(git show 3808d7fb:roster.py)`; `diff <(git show main:spawn.py) <(git show 3808d7fb:spawn.py)`; `python3 -m pytest test/ gates/ -q` in /tmp/pr-2317-review, 2026-08-25
evidence: `roster.py`'s only diff between `main` (d00aadf5) and `3808d7fb` is the pure addition of `lease_key()` at `roster.py:131-143`; `lease_renew` (`roster.py:235`) and `lease_reconcile_sweep` (`roster.py:343`) are byte-identical on both sides. `spawn.py`'s only lease-relevant diff is `lease_key = roster.lease_key` (`spawn.py:83`) and substituting the literal f-string for `lease_key(issue, role)` at the one call site (`spawn.py:2887`).
```
$ python3 -m pytest test/ gates/ -q
1200 passed, 8 xfailed in 14.79s
```
rationale: No dedicated pre-existing test file is actually named "lease tests" on `main` (`grep -rl "lease_renew\|lease_reconcile_sweep\|lease_expires_at" test/*.py` on `main` returns nothing — the proposal's own wording names an artifact that doesn't exist as a distinct suite). Evidence is instead structural: the lease mechanism's source is provably byte-identical (diff above) and the full regression suite, which does exercise roster/spawn integration paths transitively, passes clean with the same counts PR #2317 itself pasted (1200 passed, 8 xfailed) — an independent re-run, not a copy of that number.
---

---
requirement: "test/test_issue_scoped_lease.py: a lease acquired with a non-role disambiguator string renews identically to a role-keyed one"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 2
dimension: functional
verification_method: Test
verdict: Present
derived: `python3 -m pytest test/test_issue_scoped_lease.py -v` in /tmp/pr-2317-review, 2026-08-25
evidence: `LeaseRenewIdenticalTest::test_renew_identical_for_role_and_nonrole_key`, `::test_flat_progress_advisory_fires_identically` in PR #2317's new lease test file (untracked on this branch, reachable at `3808d7fb:test/test_issue_scoped_lease.py`)
```
$ python3 -m pytest test/test_issue_scoped_lease.py -v
test/test_issue_scoped_lease.py::LeaseExpireAndRequeueIdenticalTest::test_reconcile_sweep_requeues_nonrole_key_identically PASSED
test/test_issue_scoped_lease.py::LeaseKeyShapeTest::test_role_keyed_shape_byte_identical PASSED
test/test_issue_scoped_lease.py::LeaseKeyShapeTest::test_nonrole_disambiguator_uses_same_shape PASSED
test/test_issue_scoped_lease.py::LeaseRenewIdenticalTest::test_renew_identical_for_role_and_nonrole_key PASSED
test/test_issue_scoped_lease.py::LeaseRenewIdenticalTest::test_flat_progress_advisory_fires_identically PASSED
5 passed in 24.01s
```
rationale: `test_renew_identical_for_role_and_nonrole_key` asserts equal advisories, `lease_expires_at`, `lease_flat_renewals`, and `lease_progress` between a role-keyed and a non-role-keyed lease renewed with the same clock; `test_flat_progress_advisory_fires_identically` extends this through `LEASE_FLAT_RENEWALS_K` renewals for both key shapes. Both are re-run above, not copied output.
---

---
requirement: "test/test_issue_scoped_lease.py: a lease acquired with a non-role disambiguator string expires and requeues identically to a role-keyed one"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 2
dimension: edge-case
verification_method: Test
verdict: Present
derived: same run as above (`python3 -m pytest test/test_issue_scoped_lease.py -v`)
evidence: `LeaseExpireAndRequeueIdenticalTest::test_reconcile_sweep_requeues_nonrole_key_identically` in the same untracked lease test file cited above
rationale: This test seeds `d_all` with a role-keyed and a non-role-keyed entry both already past `lease_expires_at`, runs the real `spawn.lease_reconcile_sweep`, and asserts both keys appear in the requeued set and both are removed from the roster dict identically — the actual expire+requeue mechanism (#2101), not a mock of it, exercised through the real code path (see PASSED line in the transcript above).
---

---
requirement: "test/test_record_kind_field.py: a record carrying kind: outside the closed vocabulary produces an advisory (not a denial)"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 3
dimension: error-handling
verification_method: Test
verdict: Present
derived: `python3 -m pytest test/test_record_kind_field.py -v` in /tmp/pr-2317-review, 2026-08-25
evidence: `RecordKindVocabularyCheckTest::test_kind_outside_vocabulary_produces_one_advisory` in PR #2317's new record-kind test file (untracked on this branch, reachable at `3808d7fb:test/test_record_kind_field.py`); `record_kind_vocabulary_check` at `3808d7fb:gates/record_lint.py:677-703` (returns a list of advisory strings, never raises/denies)
```
$ python3 -m pytest test/test_record_kind_field.py -v
test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_kind_outside_vocabulary_produces_one_advisory PASSED
test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_kind_mentioned_only_in_prose_is_not_frontmatter PASSED
test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_no_kind_line_is_additive_empty_state PASSED
test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_kind_inside_vocabulary_produces_no_advisory PASSED
test/test_record_kind_field.py::AdvisoryNeverBlocksAggregationTest::test_lint_record_source_never_calls_the_kind_check PASSED
5 passed in 4.58s
```
rationale: The function returns a plain `list[str]` of advisory strings (Korean text explicitly labeled "advisory — 아무것도 막지 않는다" i.e. "blocks nothing") and is never called from `lint_record()` (confirmed independently below), so an out-of-vocabulary value cannot become a denial anywhere in this repo's own record-lint pipeline.
---

---
requirement: "test/test_record_kind_field.py: a record carrying kind: inside the closed vocabulary produces no advisory"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 3
dimension: functional
verification_method: Test
verdict: Present
derived: same run as above
evidence: `RecordKindVocabularyCheckTest::test_kind_inside_vocabulary_produces_no_advisory` in the same untracked test file cited above, checked against the actual closed vocabulary doc PR #2317 adds (untracked on this branch, reachable at `3808d7fb:docs/specs/record-kind-vocabulary.md`, which lists `survey` among its entries)
rationale: `record_kind_vocabulary_check(ROOT, text)` with `kind: survey` returns `[]` against this repo's actual vocabulary file on disk at the PR head, not a mocked vocabulary — re-run confirms it against the real file (see PASSED line above).
---

---
requirement: "A sample record written this stage carries both author: and kind: alongside its existing role: field"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 4
dimension: functional
verification_method: Demonstration
verdict: Present
derived: direct execution of `spawn.write_record_skeleton` against a real temp workspace, this session, 2026-08-25, in /tmp/pr-2317-review
evidence: `3808d7fb:spawn.py:2102` (`{author_line}loop_state: {loop_state}` in `_RECORD_SKELETON`), `3808d7fb:spawn.py:2135-2153` (`_stamp_additive_record_fields`), `3808d7fb:spawn.py:2216` (call site)
```
$ python3 -c "
import spawn, board
p = spawn.write_record_skeleton('/tmp/otr-sample-ws', 88888, 'implementation')
text = p.read_text()
text = text.replace('role: implementation\n', 'role: implementation\nkind: coding-record\n', 1)
p.write_text(text)
fm = board.frontmatter(p)
print({k: fm.get(k) for k in ('issue','role','author','kind','loop_state')})
"
{'issue': '88888', 'role': 'implementation', 'author': 'implementation', 'kind': 'coding-record', 'loop_state': 'in-progress'}
```
rationale: Ran the actual code path against a real (temp) workspace, not a mock — `write_record_skeleton` really writes `author: implementation` into the skeleton, and adding a `kind:` line to simulate a session filling it in produced a record carrying all three (`role`, `author`, `kind`) simultaneously.
---

---
requirement: "Existing readers (e.g. board.py's frontmatter parsing) do not error on the new keys"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), "How you'll know it worked", bullet 4
dimension: error-handling
verification_method: Demonstration
verdict: Present
derived: same execution as above
evidence: `3808d7fb:board.py:630` (`def frontmatter(p: Path) -> dict[str, str]`)
```
{'issue': '88888', 'role': 'implementation', 'author': 'implementation', 'kind': 'coding-record', 'loop_state': 'in-progress'}
```
rationale: `board.frontmatter(p)` ran against the real sample record file (not a hand-built dict) and returned all five keys with no exception raised, including the two new ones.
---

---
requirement: "No new role-shaped primitive is introduced (frozen decision single-skill-axis)"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), Constraints, bullet 1
dimension: scope-boundary
verification_method: Inspection
verdict: Present
derived: full diff read of roster.py/spawn.py between main and 3808d7fb; read of docs/decisions/2026-08-21-single-skill-axis.md and docs/decisions/2026-08-25-retire-role-axis-staging.md at 3808d7fb (both already exist on main too)
evidence: `3808d7fb:roster.py:131-143` (`lease_key(issue, disambiguator)` — a generic string parameter, not a role-shaped concept); `3808d7fb:spawn.py:2135-2153` (`_stamp_additive_record_fields` populates `author:` with the existing `role` string, inventing no new identity axis)
rationale: The only new "identity-shaped" value added (`author:`) is populated from the pre-existing `role` parameter, and the lease key's second half is documented and typed as an opaque disambiguator string, not a new role concept — matches the proposal's own stated rationale for deferring a real identity axis to a later stage.
---

---
requirement: "No skill-side enforcement is added (frozen decision single-enforcement-surface)"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), Constraints, bullet 1
dimension: scope-boundary
verification_method: Inspection
verdict: Present
derived: `grep -rn "record_kind_vocabulary_check\|RECORD_KIND_VOCABULARY_PATH" --include=*.py --include=*.sh .` in /tmp/pr-2317-review, 2026-08-25
evidence: only hits are inside `3808d7fb:gates/record_lint.py` (the check's own definitions) and its own test file cited above — no hit in `skills.py`, any `hooks/*.sh`, or any skill-selection path
rationale: The new check lives entirely on the gate side (`gates/record_lint.py`) and is not referenced anywhere in this repo's skill-mounting or skill-selection machinery.
---

---
requirement: "Must not modify board-gate.sh"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), Constraints, bullet 2 / Out of scope, bullet 3
dimension: scope-boundary
verification_method: Inspection
verdict: Present
derived: `gh pr diff 2317 --name-only`, 2026-08-25
evidence: PR #2317's changed-file list (8 files, all untracked on this review branch since the PR is unmerged): the record-contract handbook doc, its own implementation record, the record-kind-vocabulary spec, `gates/record_lint.py`, `roster.py`, `spawn.py`, and its two new test files — `board-gate.sh` is not among them
rationale: `board-gate.sh` does not appear in the PR's changed-file list at all.
---

---
requirement: "Must not modify merge_gate.py's observer logic"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), Constraints, bullet 2 / Out of scope, bullet 3
dimension: scope-boundary
verification_method: Inspection
verdict: Present
derived: same `gh pr diff 2317 --name-only` output as above
evidence: same changed-file list — `merge_gate.py` is not among them
rationale: `merge_gate.py` does not appear in the PR's changed-file list at all; nothing in it could have been touched.
---

---
requirement: "Record contract must not break mid-flight: every record written before this stage stays valid; the new author:/kind: fields are additive, never required retroactively"
spec_ref: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md (ccee8959), Constraints, bullet 3 / Out of scope, bullet 1
dimension: edge-case
verification_method: Inspection + Test
verdict: Present
derived: `python3 -m pytest test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_no_kind_line_is_additive_empty_state -v`; direct read of `record_kind_vocabulary_check`'s and `lint_record`'s source, 2026-08-25
evidence: `3808d7fb:gates/record_lint.py:647-659` (`_load_record_kind_vocabulary` returns `None` when the spec file is absent, treated by the caller as "nothing to check"); `3808d7fb:gates/record_lint.py:661-675` (`_frontmatter_kind_value` returns `None` when no `kind:` line exists, and the check short-circuits to `[]`); `lint_record()` (`3808d7fb:gates/record_lint.py:1083-1141`) never calls `record_kind_vocabulary_check` at all, so no existing record can be newly flagged by anything this stage adds
```
$ python3 -m pytest test/test_record_kind_field.py::RecordKindVocabularyCheckTest::test_no_kind_line_is_additive_empty_state -v
PASSED
```
rationale: Both the no-kind-line case and the "check never reaches the blocking aggregator" case are independently confirmed against the real functions, not stubs — a record predating this stage carries no `kind:` line and produces zero advisories, and even a record that did carry an out-of-vocabulary `kind:` could never be denied through `lint_record()`.
---

---
requirement: "Issue #2284 Acceptance / gate: test/test_issue_scoped_lease.py must pass"
spec_ref: issue #2284, Acceptance, "gate"
dimension: functional
verification_method: Test
verdict: Present
derived: `python3 -m pytest test/test_issue_scoped_lease.py -v` in /tmp/pr-2317-review, 2026-08-25 (same run cited above)
evidence: the untracked lease test file cited above, at `3808d7fb:test/test_issue_scoped_lease.py` — see the full PASSED transcript in the requirement block above (`python3 -m pytest test/test_issue_scoped_lease.py -v`)
rationale: Re-run above, not copied from PR #2317's own pasted test-plan output — independently confirms the file exists and passes clean at the PR's head commit.
---

---
requirement: "Issue #2284 Acceptance / empty state: with the stage unused/rolled back, prior-stage behavior is byte-identical for pre-existing role-keyed callers"
spec_ref: issue #2284, Acceptance, "empty state" (referencing the proposal's Rollback section)
dimension: edge-case
verification_method: Analysis
verdict: Present
derived: `git worktree add /tmp/main-review main`; `diff <(git show main:roster.py) <(git show 3808d7fb:roster.py)`; `diff <(git show main:spawn.py) <(git show 3808d7fb:spawn.py)`; direct Python comparison of the pre-PR inline key construction vs. post-PR `roster.lease_key`, 2026-08-25
evidence: `main:spawn.py:2904` (`roster_key = f"issue-{issue}/{role}" if issue is not None else ...`) vs `3808d7fb:spawn.py:2887` (`roster_key = lease_key(issue, role) if issue is not None else ...`, where `lease_key` is `roster.lease_key`, `3808d7fb:roster.py:131-143`, `return f"issue-{issue}/{disambiguator}"`)
```
$ python3 -c "
import roster
for issue, role in [(2284,'implementation'),(1,'conformance-review'),(99999,'x')]:
    pre = f'issue-{issue}/{role}'
    post = roster.lease_key(issue, role)
    print(issue, role, pre==post, pre, post)
"
2284 implementation True issue-2284/implementation issue-2284/implementation
1 conformance-review True issue-1/conformance-review issue-1/conformance-review
99999 x True issue-99999/x issue-99999/x
```
rationale: `roster.py`'s only diff between `main` and the PR head is the pure addition of `lease_key()` — every other line, including `lease_renew`/`lease_reconcile_sweep`, is byte-identical, so no in-flight lease code path changed. For every role-keyed input tested, `roster.lease_key(issue, role)` produces the exact same string the pre-PR inline f-string produced; the one call site that constructs this key (`spawn.py:2887`) substitutes the function call for the literal f-string with no other change nearby. This is the strongest form of "byte-identical" evidence available short of re-running a live multi-day lease lifecycle on both branches: the generating code itself is provably unchanged for the role-keyed path, not merely observed to produce matching output on a handful of samples.
---

---
requirement: "Issue #2284 Acceptance / provenance: executed-live — the proposal's own acceptance commands run against a real spawn/workspace, with actual output pasted into the record"
spec_ref: issue #2284, Acceptance, "provenance"
dimension: functional
verification_method: Demonstration
verdict: Present
derived: this review session's own execution, 2026-08-25, all commands run in /tmp/pr-2317-review (a real `git worktree` checkout of PR #2317's head, not a copy/paste of the PR's own test-plan output) and /tmp/otr-sample-ws (a real temp workspace for the sample-record demonstration)
evidence: every command/output pair in the "Requirements and verdicts" blocks above was executed by this review session directly, not transcribed from the PR's own implementation record's Evidence section (untracked on this branch, reachable at `3808d7fb:docs/issue-2284/reports/implementation.md`)
rationale: All four of the proposal's "How you'll know it worked" checks, plus the issue's gate/empty-state checks, were re-run against a real checkout and a real temp workspace in this session, with full output pasted above — satisfying the "executed-live" bar rather than trusting PR #2317's own pasted numbers (which happened to match, e.g. `1200 passed, 8 xfailed`, but were independently re-derived, not copied).
---

## What did not work

None — every extracted requirement resolved to Present on independent
re-derivation; no requirement needed the rule-6 re-check (before
finalizing an Absent/Incorrect verdict) since none was headed toward
either verdict.

## Upstream basis

canonical: `gh pr view 2317 --json headRefOid,title,body,url`; `gh issue view 2284`; `git show main:docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md`

PR #2317 (branch `issue-2284: stage 1 — issue-scoped lease, author
identity, record-kind vocabulary`, head `3808d7fbcca4066b461231b51ba37e7fbf4ececa`,
not yet merged as of this review), reviewed against
`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-
kind.md` on `main` (sha `ccee895997e7629495aee4ff7c0588e3082c75bc`) and
issue #2284's own Acceptance block. The implementation's own record
(untracked on this branch, reachable at
`3808d7fb:docs/issue-2284/reports/implementation.md`) was read as one
input (this review is builder-blind: treated as a claim to check, not as
ground truth) — every claim from it cited above was independently
re-derived rather than copied.

## Open findings

none — resolution path: not applicable, no open finding to resolve.

## Next steps

canonical: docs/issue-2266/reports/conformance-review.md, read this session, 2026-08-25

None — `loop_state: reported` is terminal for a `review-record`/
`conformance-review` kind per this repo's session-protocol conventions
(confirmed against `docs/issue-2266/reports/conformance-review.md`'s own
"loop_state: reported is this record kind's terminal state" note). No
further action needed on this review; PR #2317 is conformant against
the stage-1 proposal's own acceptance contract and issue #2284's added
Acceptance obligations.

## skill-verdict

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split/tag/scope the requirement list from the proposal's acceptance section and issue #2284
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to pick Inspection/Analysis/Demonstration/Test per requirement
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used to choose among the five verdicts and name failing clauses
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used for file:line+sha citations
skill-verdict: conformance-review-finding-record — applied: invoked; used for the per-requirement block field list in this record
skill-verdict: implementation-audit — not-applicable: cross-family match only; this repo's own conformance-review skill family + role-handoff contract already define the concrete two-session evaluator procedure used here
skill-verdict: conformance-review-sampling-derivation — not-applicable: issue #2284's acceptance scope is small enough to enumerate fully, no sampling needed
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not explicitly extended into risk-weighting; only verdicts were requested
