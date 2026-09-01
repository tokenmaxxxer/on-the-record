---
issue: 2978
role: silent-failure-audit-b2c2405e
author: silent-failure-audit-b2c2405e
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: gates/spawn_on_pr.py, watchdog.py, spawn.py, tests/test_watchdog_normal_state_not_violation_2978.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-2978/reports/adversarial-review-1df63424.md
    sha: f981ec4e02c4599e06710edb160dc42da6fe371a
  - path: gates/spawn_on_pr.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7  # PR #3012's original fix commit, before this session's follow-up
---

# issue-2978 — silent-failure-audit-b2c2405e record

## What was done

This session's own assigned branch is `issue-2978/silent-failure-audit-b2c2405e`,
but the work item it was given was a follow-up fix for a real defect
independent verification found in PR #3012 (branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`) — canonical:
`gh pr view 3021 --json title,state,headRefName` this session — result:
`{"headRefName":"issue-2978/adversarial-review-1df63424","state":"MERGED",
"title":"issue-2978: independent verification of PR #3012 (watchdog
false-positive fix) — spawn-on-pr defect found"}`; its record now lives at
`docs/issue-2978/reports/adversarial-review-1df63424.md` (merged to main in
commit `f981ec4e02c4599e06710edb160dc42da6fe371a`, present in this session's
own working tree after this session's `git reset --hard origin/main`).

Per the follow-up instruction ("Issue #2978 follow-up on the SAME branch
issue-2978/observability-signal-golden+test-derivation-5c7f5864 (PR #3012)"),
and per this repo's established precedent for this exact shape
(`docs/issue-2969/reports/silent-failure-audit-daadb0ad.md`, PR #3005 against
PR #2990 — read in full this session via `git show 98104361:docs/issue-2969/
reports/silent-failure-audit-daadb0ad.md`): the code fix was committed on
this session's own branch (temporarily fast-forwarded to PR #3012's actual
head via `git reset --hard origin/issue-2978/observability-signal-golden
+test-derivation-5c7f5864` so the fix applied against PR #3012's real code,
then this session switched back to fresh `origin/main` to write this record)
and pushed directly to PR #3012's own branch rather than opened as a separate
PR carrying the code — canonical: `git push origin HEAD:issue-2978/
observability-signal-golden+test-derivation-5c7f5864` this session — result:
`34b95473..d9a6845f  HEAD -> issue-2978/observability-signal-golden
+test-derivation-5c7f5864`. `board-gate.sh` R5 (report ownership) means this
session's role cannot edit PR #3012's own record file, so this record
documents the fix here instead.

**The defect (PR #3021's finding, reproduced against PR #3012's own code
before fixing it).** `gates/spawn_on_pr.py`'s `missing_verification()` used
`subject_deliverable_record(subject_board)`'s collapsed `_slug is None` as
its sole discriminator for "no PR yet, nothing to report" when a subject's
deliverable branch was also missing from `pr_index`.
`subject_deliverable_record()` itself already documents (pre-existing
docstring, `f0d8c2eb8fdf2b685203ab39b9921708ae86bab7:gates/spawn_on_pr.py`
lines 183-221) that it returns `(None, {})` for two different candidate
counts: 0 non-verifying board records (no deliverable ever landed -- the
ordinary, just-filed-issue case #2978 exists to stop reporting) and 2+
non-verifying records with no `verifies_subject` marker to disambiguate them
(#2593's own documented refuse-to-guess ambiguity -- a deliverable
demonstrably DID land here, since that is why more than one non-verifying
candidate record exists). `_slug is None` could not tell these two counts
apart, so PR #3012's fix silently suppressed the report for the 2+ case too.
Reproduced this session, directly against PR #3012's pre-fix code (checked
out at commit `34b95473`, before this session's own fix commit): `board =
{"issue-50001": {"implementation": {"author": "alice"}, "conformance-review":
{"author": "bob"}}}`, neither record `verifies_subject: true` ->
`subject_deliverable_record(board["issue-50001"])` returns `(None, {})`,
`verification_deficit(...)` still `> 0` -> `missing_verification()` reached
the branch-resolution check, found no branch in an empty `pr_index`, and
silently `continue`d instead of printing or one-shot-marking -- derived:
`python3 -c` snippet run this session against that checkout, same shape as
`docs/issue-2978/reports/adversarial-review-1df63424.md`'s own "Open
findings" item 1 reproduction — result: `missing_verification(root,
issue_states={50001: "OPEN"}, pr_index={}) == {}`, zero print calls, zero
marker calls. That review record also reports the precondition live on 146
of 700 currently-tracked board subjects — canonical:
`docs/issue-2978/reports/adversarial-review-1df63424.md`, "Open findings"
item 1, the `len(board), len(ambiguous)` derivation and its `(700, 146)`
result, read in full this session; not independently re-run here since PR
#3021 already ran it against the identical unfixed code this session started
from and the fix below does not change board contents, only how
`missing_verification()` reports on them.

**The fix (commit `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`, pushed to PR
#3012's branch).**

- Added `_deliverable_candidate_count(subject_board)` to
  `gates/spawn_on_pr.py` -- the same non-verifying-record count
  `subject_deliverable_record()` already computes internally, exposed as its
  own pure function so `missing_verification()` can tell 0 apart from 2+
  instead of only seeing the collapsed `None`.
- In `missing_verification()`'s branch-not-found handling: when `_slug is
  None`, the count is now checked. 0 candidates -> unchanged behavior,
  silently `continue` (the ordinary no-PR-yet case). 2+ candidates -> no
  longer silently suppressed -- reported under its own message
  (`"deliverable record 모호함 (N건, verifies_subject 미표시로 특정 불가) —
  브랜치도 pr_index 에서 찾지 못함"`) and its own one-shot marker
  (`_watchdog_note_ambiguous_deliverable_record`, added to `watchdog.py` and
  exposed via `spawn.py`, mirroring the pre-existing
  `_watchdog_note_unmappable_subject_branch` sibling's one-shot contract but
  in a separate state bucket -- `"ambiguous_deliverable_record_reported"`
  rather than `"unmappable_subject_branch_reported"` -- since "record set is
  ambiguous" and "branch confirmed missing" are different findings that must
  not collapse into the same reported-once key or the same printed line).
  This follows the issue's own follow-up guidance: the ambiguity itself is
  worth surfacing rather than resolved by guessing either direction (silent
  suppression) -- this repo's `DEAD-REMOTE-STATE-UNKNOWN` (#2795) and
  `HEALTHY-CONFIRMED`/`HEALTHY-UNCONFIRMED` split (#2969) are the precedent
  this follow-up named for a third state over a forced binary — canonical:
  `grep -n "DEAD-REMOTE-STATE-UNKNOWN\|HEALTHY-CONFIRMED\|HEALTHY-UNCONFIRMED"
  watchdog.py` run this session — result: hits at `watchdog.py:410,526` (the
  `DEAD-REMOTE-STATE-UNKNOWN` literal) and `watchdog.py:595,598` (the
  `HEALTHY-CONFIRMED`/`HEALTHY-UNCONFIRMED` literals).
- The confirmed-single-deliverable case (`_slug is not None`) is completely
  unchanged -- same code path, same message, same marker as PR #3012 left it.
- Added a summary line at the end of `missing_verification()`
  (`"N건 이전에 보고된 모호한 deliverable record subject — 계속 무시"`),
  mirroring the pre-existing `unmappable_branch_already_reported` summary --
  the already-reported count for this new bucket folds the same way instead
  of reprinting every tick.
- Added regression test `SpawnOnPrAmbiguousRecordSetIsStillReported` /
  `test_spawn_on_pr_ambiguous_record_set_still_reported` to
  `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5:tests/
  test_watchdog_normal_state_not_violation_2978.py` (this file is untracked
  on this session's own branch -- it lives only on PR #3012's branch, not yet
  merged to main), constructing the exact 2-non-verifying-record board shape
  PR #3012's own acceptance test 2 (`SpawnOnPrGenuinelyMissingBranchIsStillReported`)
  did not cover (that test only exercises the single-record case) -- asserts
  the new marker fires, the old `_watchdog_note_unmappable_subject_branch`
  marker does NOT fire (the two findings stay on separate one-shot keys), and
  the printed line names the record set as ambiguous rather than "not found".
- `gates/closure_sweep.py` is untouched -- `docs/issue-2978/reports/
  adversarial-review-1df63424.md`'s "Open findings" item 2 found that half
  sound (reuses issue #2974's own diff-content record-only signal verbatim,
  independently re-derived with a fresh non-PR-authored fixture) and this
  follow-up's own instruction says not to touch it.

## Why

Followed `silent-failure-audit` (skill invoked this session, see
skill-verdict below): the defect is exactly this skill's signature shape --
a code path (`missing_verification()`'s branch-not-found handling) that
looks like it handles both `_slug` outcomes but actually treats one
silently-absorbed outcome (the 2+-candidate case) as though it were the
other, correctly-handled one (the 0-candidate case), because both share the
same `None` return value one layer down. The fix does not change what
`subject_deliverable_record()` returns (still `(None, {})` for both counts,
by design -- `verifying_record_count()` and the rest of this module's
self-verification-guard logic still only need "is there a unique
deliverable," not which ambiguity shape produced `None`) -- it adds a
second, narrower query (`_deliverable_candidate_count()`) at the one call
site that actually needs the distinction, rather than changing
`subject_deliverable_record()`'s own contract and risking silently changing
behavior at its other call sites in this file.

Kept the ambiguous case as a genuinely separate one-shot marker/message
instead of reusing `_watchdog_note_unmappable_subject_branch` for both,
because the issue's own follow-up text names a third state, not a forced
binary — canonical: the same `DEAD-REMOTE-STATE-UNKNOWN`/`HEALTHY-CONFIRMED`
grep cited in "## What was done" above, re-cited here since this rationale
restates that precedent: a distinct signal name lets an operator (or a
future automation reading these lines) tell "the branch is confirmed gone"
apart from "the record set itself does not resolve to one deliverable,"
which are different repairs (branch-mapping vs. board hygiene / applying a
`verifies_subject` marker retroactively).

## Upstream basis

- `gates/spawn_on_pr.py` at commit `f0d8c2eb8fdf2b685203ab39b9921708ae86bab7`
  (PR #3012's original fix, `subject_deliverable_record()` and the
  `_slug is None` discriminator this session extended).
- `docs/issue-2978/reports/adversarial-review-1df63424.md` at commit
  `f981ec4e02c4599e06710edb160dc42da6fe371a` (merged to main, present in this
  session's own working tree) — the source of the defect finding, its
  reproduction, and the board-prevalence count, all read in full this
  session (`canonical` citations in "## What was done" above).
- This session's own fix commit: `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`,
  pushed to `issue-2978/observability-signal-golden+test-derivation-5c7f5864`
  (PR #3012), one commit ahead of that branch's prior head `34b95473` —
  canonical: `git log --oneline -1 origin/issue-2978/observability-signal-golden+test-derivation-5c7f5864`
  this session, after the push above — result: `d9a6845f issue-2978:
  distinguish ambiguous deliverable record set from no-PR-yet in
  spawn-on-pr`.

## Open findings

None. PR #3021's finding is fixed by the commit documented above; the
closure-sweep half PR #3021 also audited had no open finding to begin with.

## Next steps

`loop_state: landed`.

- acceptance: `git log --oneline -1 origin/issue-2978/observability-signal-golden+test-derivation-5c7f5864` — result:
  ```
  d9a6845f issue-2978: distinguish ambiguous deliverable record set from no-PR-yet in spawn-on-pr
  ```
  (confirms this session's fix commit is live on PR #3012's remote branch;
  the "## Acceptance re-run" section below re-derives all five pytest checks
  against that exact commit).

What remains is external to this record: PR #3012 (now carrying commit
`d9a6845f`) needs a human/verifier to re-review before merge -- not
something this session can do for its own upstream PR.

## Acceptance re-run

Re-ran all four of issue #2978's original acceptance checks, plus the new
regression test and a broader regression sweep, against the fixed tree on
`issue-2978/observability-signal-golden+test-derivation-5c7f5864` at commit
`d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`, before switching back to this
session's own branch to write this record:

- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
  ```
  1 passed in 0.90s
  ```
- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
  ```
  1 passed in 0.85s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
  ```
  1 passed in 0.90s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
  ```
  1 passed in 0.96s
  ```
- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_ambiguous_record_set -q` (new
  regression case added this session, `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5:
  tests/test_watchdog_normal_state_not_violation_2978.py`) — result:
  ```
  1 passed in 0.88s
  ```
- acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py tests/test_watchdog_normal_state_not_violation_2978.py -q` — result:
  ```
  38 passed in 0.85s
  ```

Broader regression sweep (not claimed by PR #3012 or #3021, run to check for
collateral damage from this session's own edit) — derived:
`python3 -m pytest tests/ test/ gates/ -q` — result:
```
16 failed, 721 passed, 3 xfailed in 31.62s
```
canonical: `docs/issue-2978/reports/adversarial-review-1df63424.md`'s own
"What was done" section states its identical sweep against PR #3012's
pre-follow-up head as `16 failed, 720 passed, 3 xfailed` (matching test
names: `test_convention_equivalence.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_local_dependency_env.py` -- hook-wiring and skill-selection tests
untouched by this diff) -- the `+1 passed` measured this session is this
session's own new regression test. Zero new failures from this session's
edit.

skill-verdict: silent-failure-audit — applied: invoked; used its
Handled/Silently-Absorbed/Unreachable classification to locate the exact
defect shape -- `missing_verification()`'s branch-not-found handling looked
like it fully handled both `_slug` outcomes but silently absorbed the
2+-candidate ambiguity into the 0-candidate "nothing to report" path because
both collapse to the same `None` one layer below in
`subject_deliverable_record()`
skill-verdict: work-in-english — applied: invoked; wrote this record, the
fix commit message, and all in-session commands/comments in English per the
policy
other mounted skills: not triggered
