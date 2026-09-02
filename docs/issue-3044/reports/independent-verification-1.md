---
issue: 3044
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3068's own deliverable, checked out and re-derived against a fresh worktree
loop_state: landed
code_under_review: PR #3068 (issue-3044/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3, still OPEN, not yet merged), commit bc557df536ea5a44ab2059a002644bb2fbdf8946
type: verification
breaking: false
verdict: All 3 literal acceptance checks pass, independently re-run in a
  fresh worktree. All 4 must-not clauses hold on independent code reading
  and the PR's own subprocess tests. One non-blocking documentation defect
  found (see Open findings): the PR's new block message points to
  docs/handbooks/skill-verdict-obligation.md, but that handbook (untouched
  by this PR) still states its checks are advisory-only, which is now false
  for the invoked-mismatch case this PR adds.
upstream:
  - path: PR 3068, branch issue-3044/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3
    sha: bc557df536ea5a44ab2059a002644bb2fbdf8946
  - path: bc557df5:docs/issue-3044/reports/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3.md
    sha: bc557df536ea5a44ab2059a002644bb2fbdf8946
---

# issue-3044 — independent-verification-1 record

## What was done

An independent verification of PR #3068 (the deliverable for issue #3044),
spawned per the standing `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` mechanism
(`docs/handbooks/observer-verification.md`).

derived: `python3 gates/merge_gate.py 3068 issue-3044`, run this session:
```
거절: PR #3068 (issue-3044)
  - check-runner 코멘트를 찾을 수 없다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
```
0 of 2 qualifying records existed before this session's own record (the
pasted `0/2` above, from that same command run this session).

canonical: `gh issue view 3044`, run this session -- read the issue body's
three literal `check:` commands and the "must not" clause.

canonical: `gh pr view 3068 --json title,body,mergeable,additions,deletions,files,commits`,
run this session -- read the PR's own description and file list before
touching any code.

Checked out the PR into a fresh worktree: `git fetch origin
pull/3068/head:pr-3068-review && git worktree add /tmp/pr3068-review
pr-3068-review`, run this session -- and re-ran every check independently
in that worktree rather than trusting the PR body's pasted output.

### Re-derivation of the three literal acceptance checks

1. `python3 -m pytest on-the-record/hooks/ -q -k invoked`. derived: ran this
   session in `/tmp/pr3068-review` -- result:
   ```
   9 passed in 0.90s
   ```
   **Verdict: Present.**
2. `grep -rn 'invoked' gates/record_lint.py | head -1`. derived: ran this
   session in `/tmp/pr3068-review` -- result:
   ```
   gates/record_lint.py:545:_SKILL_VERDICT_INVOKED_MARKER = re.compile(r"(?i)^invoked\s*;")
   ```
   non-empty. The issue's second check is a literal existence probe
   standing in for a substantive question ("the obligation is re-derived
   somewhere a merge cannot bypass, or the Stop hook blocks -- the PR
   states which"); canonical: PR #3068 body, read this session -- states
   the Stop-hook choice and why CI was left alone (CI has no durable
   transcript to re-derive the invoked set from). Independently confirmed
   by reading the code (see "Independent code reading" below), not just
   trusting the PR's own prose. **Verdict: Present.**
3. `python3 -m pytest on-the-record/hooks/ -q`. derived: ran this session in
   `/tmp/pr3068-review` -- result:
   ```
   FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_every_hooks_json_registration_has_a_classification_entry
   FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_registration_count_matches_the_issues_own_count
   2 failed, 40 passed in 1.10s
   ```
   derived: ran `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q`
   this session against an unmodified `origin/main` worktree
   (`git worktree add /tmp/main-check origin/main`, commit 24bc12b4) -- result:
   ```
   FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_registration_count_matches_the_issues_own_count
   FAILED on-the-record/hooks/test_hook_classification.py::HookClassificationTest::test_every_hooks_json_registration_has_a_classification_entry
   2 failed, 4 passed in 0.84s
   ```
   the same 2 tests fail on unmodified `main` too, confirming the PR body's
   claim that these failures pre-exist and are unrelated to this change
   (they check `gate-registration-post-guard.sh` registrations against
   `hook_classification.json`, neither file touched by this PR). **Verdict:
   Present**, pre-existing failures excluded per the issue's own framing
   ("truthful case is unaffected").

### Independent code reading beyond the literal checks

canonical: `gates/record_lint.py`'s `skill_verdict_reason_check` function,
read this session in the PR worktree (`/tmp/pr3068-review`). Confirmed the
`mounted` parameter is, by issue #2153's prior design (unchanged docstring,
still accurate), already the session's *invoked*-skill set, not every
mounted name -- `skill-verdict-guard.sh` passes `invoked` (the
transcript-derived list) as this argument. This makes the PR's new converse
loop (`for name, content in found.items(): if name in mounted_set: continue
...`) semantically correct: any `applied: invoked; ...` line whose name is
absent from the transcript-derived invoked set is exactly a claim the
transcript disproves, regardless of whether that name was mounted,
mounted-but-uninvoked, or a typo/hallucination -- the loop iterates over
every `skill-verdict:` line found in the record text, not just names drawn
from `mounted`.

canonical: `on-the-record/hooks/skill-verdict-guard.sh`, read this session
in `/tmp/pr3068-review`. Traced the paths a false `invoked;` claim could
still slip through:
- Transcript missing/unreadable (`transcript_path` absent, not a string,
  or not `os.path.isfile`): `sys.exit(0)` at lines 91-94, before
  `skill_verdict_reason_check` is ever reached -- structurally cannot
  block. Matches the must-not clause ("must not block a session whose
  transcript is unreadable or absent").
- Transcript readable but `invoked_skill_names()` raises `OSError`
  mid-read (`except OSError: return []`): `invoked` becomes `[]`, which
  routes to the `zero_invocation_notice` branch, never reaching the
  hard-block path either.
- Zero skills mounted (`if not mounted: finish(reminder)`): early exit
  before any transcript scan.
- The one path that does reach the hard check requires a non-empty
  `invoked` list derived from an actually-parsed transcript -- real
  evidence must exist before a block can fire. `hard = [v for v in
  violations if v.startswith("invoked-mismatch")]` / `soft = [...]`
  correctly separates the new hard violations from the four pre-existing
  shape-only ones (missing line, empty content, missing `invoked;` marker,
  zero-invocation summary), which stay in the `soft` (advisory-only,
  `additionalContext`) path exactly as before -- confirms "must not weaken
  the existing detection of a missing verdict line."
- `not-applicable:` lines never match `_SKILL_VERDICT_APPLIED` (`^applied
  \s*:\s*(.*)$`), so a skill legitimately judged not-applicable can never
  trigger `invoked-mismatch` -- confirms the fourth must-not clause.

derived: `diff gates/record_lint.py on-the-record/gates/record_lint.py`,
run this session in `/tmp/pr3068-review` -- result: empty (`IDENTICAL`
printed by the follow-on echo), the two mirror files stay byte-identical
as the PR body claims.

canonical: `bc557df5:on-the-record/hooks/test_skill_verdict_reason_check.py`
(new file this PR adds, read this session from the checked-out worktree
`/tmp/pr3068-review/on-the-record/hooks/test_skill_verdict_reason_check.py`
-- not present on this record's own branch since PR #3068 has not landed
yet). 6 pure-unit tests equivalence-partition the new logic by (line type:
`applied: invoked;` vs `not-applicable:`) x (name membership: invoked vs
not), plus regression tests for the pre-existing #2039/#2062 shape checks
and the empty-mounted no-op. 3 subprocess tests run the real shipped
`skill-verdict-guard.sh` end-to-end via a fabricated transcript and
Stop-event payload, asserting: the hook emits `decision: "block"` on a
mismatched claim, stays advisory (`decision` key absent) when all claims
are truthful, and stays advisory (no crash, no block) when the transcript
path does not exist on disk. All three of these assertions were
independently re-run as part of the full-suite check above (item 3, the
`40 passed` count includes these 3), not just read as source.

### One defect found: stale handbook the new block message points to

`skill-verdict-guard.sh`'s new block message ends with `"자세한 형태는
docs/handbooks/skill-verdict-obligation.md 참고"`. canonical:
`docs/handbooks/skill-verdict-obligation.md` (this repo's own tree, on this
record's own branch -- unaffected by PR #3068, confirmed by the
`gh pr view --json files` list captured above having no such path), read
this session:
```
39: `not-triggered` content is actually correct -- that judgment
40: stays entirely the session's own, per the frozen skills-guidance-only
41: principle (guidance only; enforcement is core hooks only). Every check
42: here is advisory (`additionalContext`), never `decision: "block"`.
```
(line numbers from `grep -n` run this session against the file at its
current path in this working tree). This line is now false for the
`invoked-mismatch` case PR #3068 adds: the Stop hook does now emit
`decision: "block"` for that specific violation (confirmed live above,
`test_hook_blocks_on_invoked_mismatch_record`). A session that hits the
block and follows the message's own pointer to "자세한 형태" reads a
handbook that flatly contradicts what just happened to it. This is a real,
PR-introduced inconsistency: the PR adds the first blocking path this
handbook's text explicitly denies exists, without updating the handbook it
references. It is a documentation consistency gap, not a functional
defect -- none of the three literal acceptance checks or four must-not
clauses depend on this handbook's wording, and the block itself fires and
reports correctly per the independent re-derivation above.

## Why

canonical: `docs/handbooks/observer-verification.md`, read this session --
`verifies_subject: true` is self-declared per record; a subject with
`REQUIRED_INDEPENDENT_VERIFICATIONS = 2` needs two qualifying records with
`author:` different from the subject's own deliverable author before it can
merge. This record's `author:` is `independent-verification-1`, distinct
from PR #3068's own deliverable record author
(`silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3`,
canonical: `gh pr view 3068 --json commits`, read this session, single
commit authored by the PR's own branch), so this record qualifies once
`verifies_subject: true` is set.

Re-running every check in a fresh worktree rather than trusting the PR
body's pasted output was chosen over reading the PR body alone because an
independent pass that only re-typed the same numbers would add nothing --
derived: the full-suite pytest run above (item 3) was executed twice, once
against the PR worktree and once against unmodified `origin/main`, which is
the concrete step that distinguishes "pre-existing failure" from
"regression this PR introduced," a distinction the PR body asserts but
does not itself demonstrate against an unmodified tree.

## What did not work

None.

## Upstream basis

- canonical: `gh pr view 3068 --json title,body,mergeable,additions,deletions,files,commits`,
  run this session -- PR #3068, branch
  issue-3044/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3,
  commit bc557df536ea5a44ab2059a002644bb2fbdf8946, state OPEN, mergeable.
- `bc557df5:docs/issue-3044/reports/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3.md`
  (PR #3068's own deliverable record, only present on that commit -- not
  landed on this record's own branch) -- read this session for context via
  `git show bc557df5:docs/issue-3044/reports/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3.md`;
  every claim re-derived independently above against the checked-out
  branch, not inherited from its prose.
- Issue #3044 body -- `gh issue view 3044`, run this session.
- `gates/record_lint.py`, `on-the-record/hooks/skill-verdict-guard.sh`,
  `bc557df5:on-the-record/hooks/test_skill_verdict_reason_check.py` -- read
  and executed directly from `/tmp/pr3068-review` (worktree of
  `pull/3068/head`, commit bc557df5), all checks in this record ran
  against this checkout.
- `/tmp/main-check` (worktree of `origin/main`, commit 24bc12b4) -- used
  only to confirm the 2 pre-existing `test_hook_classification.py`
  failures reproduce identically without this PR's change (result quoted
  under acceptance-check item 3 above).
- derived: `python3 gates/merge_gate.py 3068 issue-3044`, run this session
  -- full pasted output at the top of this record's "What was done"
  section.

## Open findings

- `docs/handbooks/skill-verdict-obligation.md`'s current text ("Every check
  here is advisory ... never `decision: "block"`", quoted in full under
  "One defect found" above, `grep -n` output from this session) is now
  false for the `invoked-mismatch` case PR #3068 adds, and the PR's own new
  block message points a blocked session at exactly this file. Resolution
  path: a small follow-up PR updating that line to carve out
  `invoked-mismatch` as the one hard-blocking exception, referencing issue
  #3044. Not blocking for PR #3068 itself -- none of the three literal
  acceptance checks or four must-not clauses depend on this handbook's
  wording, and the block behavior itself is correct and covered by the
  PR's own subprocess tests (re-run live above).
- `gates/record_lint.py`'s `record_skill_verdicts_in` docstring claims it
  is used by both `gates/ci.py` and `on-the-record/hooks/skill-verdict-guard.sh`.
  derived: `grep -rn "record_skill_verdicts_in" --include="*.py" --include="*.sh" .`,
  run this session in `/tmp/pr3068-review` -- only the definition itself
  and a comment mention in the hook's header, zero actual call sites
  anywhere in the tree; the hook calls `skill_verdict_reason_check`
  directly, not this wrapper. derived: same grep run against
  `/tmp/main-check` (`origin/main`, commit 24bc12b4) -- identical result,
  confirming this docstring is unchanged by PR #3068 and was already
  inaccurate before it. Not in scope for #3044's acceptance criteria
  (which only ask that the PR state its CI-vs-Stop-hook choice, which it
  does per acceptance-check item 2 above) -- noted here so a future session
  fixing the stale docstring or wiring `gates/ci.py` doesn't have to
  rediscover it.

## Next steps

`loop_state` is terminal (`landed`) for this record: the three literal
acceptance checks and four must-not clauses were independently re-run and
re-read against a fresh checkout of PR #3068 in `/tmp/pr3068-review`, not
inherited from the PR's own body. derived: this session made no `git
push`, `gh pr merge`, or `gh pr edit` call against PR #3068 or any other
PR -- verification only. The Open findings above name follow-up work
without starting it.

## Skill verdicts

- skill-verdict: work-in-english — applied: invoked; used to route this
  record's exhaust (this record's body, upstream citations, worktree
  commands) to English while keeping the end-of-turn summary to the user
  in Korean, per the spawning prompt's Korean task text.
- other mounted skills: not triggered.
