---
code_under_review:
  - spawn.py
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - on-the-record/hooks/test_skill_verdict_guard.py
  - gates/test_record_lint.py
  - tests/test_spawn_directive_assembly.py
kind: conformance-review
loop_state: landed
---

# issue-2062: conformance review — invoke-before-apply obligation

kind: conformance-review
subject: issue-2062

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used this skill's rule 1 (split "and"/또한 bundled sentences) and rule 6 (dimension-tag) to decompose issue #2062's `## Acceptance` line into the 5 checkable requirements below (R1-R5), keeping the explicitly-deferred third clause as its own unverifiable-as-written item (R5) per rule 2 rather than guessing a substitute check.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used rule 4 (reuse an existing repo test rather than re-deriving a parallel manual check) for R1-R4 — each requirement already has an executable pytest case, so Test is the method, backed by this session's own re-run of those tests on a fresh worktree at the implementation branch's HEAD (see Evidence). Rule 1 (Inspection) applied to the byte-identity-of-guard-function check across gates/record_lint.py and on-the-record/gates/record_lint.py.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 3 (Unverifiable, name the missing evidence location, never a favorable/unfavorable guess) for R5. Rule 5 (name the failing clause, not a bare label) was not triggered — no Incorrect/Absent verdict was assigned in this review.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used rule 1 (file:line-range + commit sha, not a bare path) for every citation below, and rule 2 (one traceability link per contributing file) for R3, which cites both `gates/record_lint.py` and `on-the-record/gates/record_lint.py` as separate links since the same function block was patched in both tracked copies.
skill-verdict: conformance-review-finding-record — applied: invoked; used the field list (requirement, spec_ref, verdict, evidence, rationale) to shape each requirement block below, and the refusal rule (no Present/Absent/Incorrect with no evidence pointer) — every non-Unverifiable verdict below cites a file:line/test-run pointer.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the issue's own acceptance clauses and their landed code_under_review set (5 files, all touched by one small diff) was feasible in this session; no sampling was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope is ordinary fidelity-checking against issue #2062's stated acceptance, not an explicit extension into risk-weighting an already-recorded finding.

## What was done

canonical: `git log --oneline origin/main..origin/issue-2062/implementation`
(this session):
```
d0c85fec issue-2062: update record_lint fixture for invoked marker
0670f8f4 issue-2062: consult-trace (ok)
406a2486 issue-2062: invoke-before-apply obligation and skill-verdict marker check
d4b2cda5 issue-2062: consult-trace (ok)
```
Reviewed the two commits carrying code (`d0c85fec`, `406a2486`) against
issue #2062's own body and `## Acceptance` text — spawner-provided
basis for this board_condition (implementation commit landed, no
conformance-review record yet). canonical: `gh issue view 2062` (read
this session) — used as the spec text this review checks against.

derived: `git diff origin/main..origin/issue-2062/implementation --stat`
(this session, from a `git worktree add /tmp/wt-2062-impl
origin/issue-2062/implementation --detach` checkout at commit
d0c85fec):
```
docs/issue-2062/reports/consult-log.md          |  2 +
docs/issue-2062/reports/implementation.md       | 72 +++++++++++++++++++++++++
gates/record_lint.py                            | 25 ++++++++-
gates/test_record_lint.py                       |  2 +-
on-the-record/gates/record_lint.py              | 25 ++++++++-
on-the-record/hooks/test_skill_verdict_guard.py | 36 ++++++++++++-
spawn.py                                        | 12 ++++-
tests/test_spawn_directive_assembly.py          | 27 ++++++++++
8 files changed, 193 insertions(+), 8 deletions(-)
```
canonical: `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md`
(this session) — the implementer's own record, used below as the
implementer's account, cross-checked against the diff/test-run evidence
rather than taken at face value.

Requirement extraction (issue #2062 body, bundled sentence split per
requirement-extraction rule 1 — the body's two numbered clauses each
bundle an "and" of directive-text + guard-shape obligations):

- **R1** (functional behavior) — the spawn directive's mounted-skill
  block gains a sentence stating: a skill judged APPLICABLE must be
  invoked via the Skill tool (full SKILL.md loaded) before being
  applied; not-applicable skills are exempt.
- **R2** (functional behavior) — the skill-verdict obligation text
  (issue #2039 block) gains a companion sentence: an `applied:` line's
  free text must start with `invoked;` as proof the Skill tool was
  called; `not-applicable:` lines need no marker.
- **R3** (functional behavior) — `skill_verdict_reason_check` in
  `gates/record_lint.py` (and its tracked mirror
  `on-the-record/gates/record_lint.py`) rejects an `applied:` line
  lacking the `invoked;` marker and accepts one carrying it, shape-only
  (never judging whether the marker's claim is true).
- **R4** (edge-case / scope-boundary) — `not-applicable:` lines and
  zero-mounted-skill sessions stay byte-unaffected by R1-R3.
- **R5** (scope-boundary, flagged unverifiable-as-written per
  requirement-extraction rule 2) — a live consumer spawn after landing
  produces a record whose `applied:` lines carry the marker and the
  harness log shows the corresponding Skill tool calls;
  `provenance: executed-live` per the issue's own Acceptance text —
  the issue itself states this can only be observed on a future spawn,
  not from within a review session.

### Verdicts

**R1 — Present.**
spec_ref: issue #2062 body, clause "the spawn directive's mounted-skill
obligation gains one sentence — a skill you judge APPLICABLE must be
invoked via the Skill tool ... BEFORE applying it".
canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py -q -k InvokeBeforeApply`
— result:
```
$ python3 -m pytest tests/test_spawn_directive_assembly.py -q -k InvokeBeforeApply
.....                                                                    [100%]
5 passed in 1.12s
```
(this session, worktree checkout of commit d0c85fec)
evidence: `spawn.py:8455-8465` (implementation branch, commit
d0c85fec) — the `스킬 점검(이슈 #1960)` block, inside the existing
`if skill_sources or role_source["skills"]:` guard, now reads
"...호출하고, 없으면 검토했다는 사실만 유념하고 넘어가라.
invoke-before-apply(이슈 #2062): APPLICABLE 로 판단한 스킬은 적용하기
전에 반드시 Skill 도구로 그 스킬의 전체 SKILL.md 를 로드해야 한다 —
not-applicable 로 판단한 스킬은 이 의무에서 면제된다(강제 로드도,
토큰 낭비도 없다)." — this session's own task prompt carries the
identical `invoke-before-apply(이슈 #2062)` sentence, delivered by
`spawn.py` at this very session's own spawn, direct observation.
rationale: the pytest run above (`test_mounted_skill_directive_states_invoke_before_apply`)
runs and checks that `"invoke-before-apply(이슈 #2062)"` and `"invoked;"`
both appear in the directive text `spawn.py` delivers when a skill is
mounted — the directive text sits next to the mounted-skill list,
inside the same conditional guard the test exercises.

**R2 — Present.**
spec_ref: issue #2062 body, "its skill-verdict line must state that it
was invoked".
canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py -q -k InvokeBeforeApply`
— result: same run pasted under R1 above (this session, commit
d0c85fec).
evidence: `spawn.py:8466-8474` (implementation branch, commit
d0c85fec) — the 이슈 #2039 block gains "applied: 줄은 위
invoke-before-apply 의무에 따라 실제로 Skill 도구를 호출했다는 증거로
`invoked;` 를 자유 텍스트 맨 앞에 붙여야 한다(이슈 #2062) —
not-applicable: 줄은 이 마커가 필요 없다." — this session's own task
prompt carries this exact sentence, direct observation.
rationale: same directive-assembly point as R1, checked by the same
test cited above (`InvokeBeforeApplyObligation` checks for both the
obligation text and the `invoked;` requirement in one delivered
string).

**R3 — Present.**
spec_ref: issue #2062 body, "(2) skill-verdict-guard extends its shape
check: an 'applied:' verdict line must contain an invocation marker
(e.g. 'invoked;' prefix in the free text) — still shape-only, never
interpreting skill content."
canonical: `python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py -q`
— result:
```
$ python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py -q
80 passed in 1.81s
```
(this session, worktree checkout of commit d0c85fec) — this run
includes `t_applied_line_without_invocation_marker_is_blocked` (a bare
`applied: used it.` line is rejected) and `t_satisfied_skill_verdicts_pass`
(`applied: invoked; used it at spawn.py:8181.` is accepted), direct
evidence that the guard rejects an `applied:` line lacking the
`invoked;` marker and accepts one carrying it, shape-only.
evidence: `gates/record_lint.py:385-433` and
`on-the-record/gates/record_lint.py:244-292` (implementation branch,
commit d0c85fec) — both carry the identical new
`_SKILL_VERDICT_APPLIED`/`_SKILL_VERDICT_INVOKED_MARKER` regex pair and
the new branch inside `skill_verdict_reason_check`: when `content`
matches `applied:` and the text after that label does not start with
`invoked;`, a new violation string is appended; the check only reads
the marker's presence, never the truth of what follows it.
canonical: `diff gates/record_lint.py on-the-record/gates/record_lint.py`
restricted to the `_SKILL_VERDICT_LINE`..`skill_verdict_reason_check`
block — result: zero-line diff over that block (this session, worktree
checkout of d0c85fec), confirming both tracked copies carry the
identical new branch. Two separate traceability links recorded per
traceability-and-evidence rule 2, since the function is duplicated in
both tracked files.
rationale: canonical: `python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py -q`
— result: the 80-line run pasted at the top of this R3 block, this
session, executed against the implementation branch's actual HEAD
(d0c85fec), not merely read from the implementer's account, covers
both the reject case and the accept case above.

**R4 — Present.**
spec_ref: issue #2062 body, "NA lines and zero-skill sessions byte-unaffected".
canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py -q -k InvokeBeforeApply`
and `python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py gates/test_record_lint.py -q`
— result: the two runs pasted under R1 and R3 above, both executed this
session against commit d0c85fec.
evidence: `tests/test_spawn_directive_assembly.py:219-224`
(`test_zero_mounted_skills_directive_omits_invoke_before_apply`) and
`on-the-record/hooks/test_skill_verdict_guard.py:203-217`
(`t_not_applicable_line_needs_no_invocation_marker`), implementation
branch commit d0c85fec — both included in the two runs cited
immediately above, whose test bodies assert `r.stdout == ""` and
`assertNotIn("invoke-before-apply", delivered)` directly.
rationale: the two edge cases named in the requirement (NA lines,
zero-mounted-skill sessions) each have their own dedicated test
asserting byte/behavioral non-effect, not an inferred absence of
change.

**R5 — Unverifiable.**
spec_ref: issue #2062 `## Acceptance`, third clause: "a live consumer
spawn after landing produces a record whose applied lines carry the
marker and the harness log shows the corresponding Skill tool calls."
canonical: `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md`
— result: this session's read of the implementer's own "Open findings"
section, which states the same self-assessment ("provenance:
executed-live and can only be observed on a future spawn after this PR
merges — it is not verifiable from within this session").
evidence: none available to this session — the required evidence is a
future post-landing spawn's own record plus its harness log entry,
neither of which exists yet as of this review (this session's own
current spawn is the conformance-review session itself, not a
"consumer spawn after landing" in the sense the clause names, and this
role does not write to any consumer's implementation record).
rationale: per verdict-assignment rule 3, an unlocatable-evidence case
is Unverifiable, never a favorable or unfavorable guess. This review
independently re-derives that same conclusion from the requirement's
own wording (a future-tense, post-merge-only observation) rather than
deferring to the implementer's matching self-assessment cited above.

## Why

Basis: `gh issue view 2062` (read this session, used as the spec text)
and `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md`
(read this session, used as the implementer's account, cross-checked
against the diff/test evidence above rather than trusted directly).
Reviewed per this role's mandate (marketplace `conformance-review` role
spec, `roles/conformance-review.json`): an implementation commit landed
on `issue-2062/implementation` and no conformance-review record existed
yet for it — spawned automatically on PR creation per `spawn_on_pr.py`,
per this session's own task prompt. Phase-2 write approved via `APPROVE
issue-2062/conformance-review` (this session, posted from account
`JiwonJung94`, listed in `docs/specs/approvers.md`): canonical:
https://github.com/tokenmaxxxer/on-the-record/issues/2062#issuecomment-5381562272

## Open findings

None. R1-R4 each carry an executable-test citation re-run by this
session against the implementation branch's actual HEAD (d0c85fec, not
merely the implementer's account). R5 is Unverifiable by the issue's
own design — not a defect, a scope boundary the issue itself names as
checkable only after this PR lands and a future consumer spawn occurs.

## Amendments reconciled

amendments-reconciled: issuecomment-5381558954 (JiwonJung94,
2026-08-22T17:00:35Z) — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5381558954`
(this session). The comment states the change landed via PR #2063
(+fixture finalization d0c85fec, the same commit this review's R1-R4
evidence was gathered against) and reports a fetched-worktree fast-tier
run as fully green; it adds no new requirement beyond issue #2062's own
body/Acceptance text already extracted as R1-R5 above, so no additional
requirement item is opened. Its fast-tier count claim (2588, all green)
is the commenter's own account from a separate session, not re-verified
by this review — this review's own R1-R4 evidence above is this
session's independent re-run against the same commit, not a citation of
that account.

## Next steps

None from this review. R5 will need its own check once a real
post-landing consumer spawn produces a record and a harness log entry —
that check belongs to a future session (or a follow-up issue), not this
one, since the evidence does not exist yet. `loop_state` is `landed`
(terminal for `kind: conformance-review`) because every requirement
checkable from the current landed state has a verdict.
