---
issue: 2719
role: adversarial-review-36975768
author: adversarial-review-36975768
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: d329e9b99b9e335644715046a05523f5611c315a
loop_state: landed
type: review
breaking: false
verdict: confirmed — PR #2721's three dispositions and its enumeration hold under independent re-derivation; one reproducibility defect found in a supporting "derived:" citation (does not change the substantive conclusion it supports)
upstream:
  - path: dfbfaaa7:docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md
    sha: dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69
---

# issue-2719 — adversarial-review-36975768 record

## What was done

Independently re-derived every claim in PR #2721 (branch
`issue-2719/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd`,
head `dfbfaaa7`, code commit `d329e9b9`) from the PR head and the live repo,
without restating the subject's own record's prose as evidence — canonical:
`gh pr view 2721 --json title,body,files,commits,headRefName,baseRefName,state`
and `gh pr diff 2721`, both read live this session. Two git worktrees were
used throughout: one at `d329e9b9^` (BEFORE, equal to `origin/main` at
session start) and one at `dfbfaaa7` (AFTER, the PR head) — derived:
`git rev-parse HEAD origin/main` on this branch printed
`ca6d6a9344867b8cf7b15c4b84aef773c1a4895a` for both.

### Site 1 — `upstream-defect-scope-guard.sh` `CHANNEL_SKILL`, kept

Read `in_scope()` directly at the PR head — canonical:
`dfbfaaa7:on-the-record/hooks/upstream-defect-scope-guard.sh` lines
215-234, 260-330, read via `git show dfbfaaa7:on-the-record/hooks/upstream-defect-scope-guard.sh`
this session — rather than trusting the operator ruling's prose. Condition
(a) is `channel_role_active` (the hardcoded-name check); condition (b)
requires a non-`None` `target_repo` extracted from the call shape, and
`in_scope` returns `target_repo.lower() != ORIGIN_REPO` only in that
branch. Two call shapes never produce an extractable target at all — the
GraphQL `createPullRequest` and `hub pull-request` branches both call
`in_scope(None)` directly (lines 283, 293 of that file) — and a
same-origin `--repo` value makes (b) evaluate to `False` even when a
target IS extracted. So with `channel_role_active` hypothetically removed,
`in_scope(None)` would always return `False`: a channel session's
own-origin or target-less PR-creation attempt is provably uncatchable by
(b) alone. This confirms the ruling's central premise is true as a
structural fact of the code, not merely as asserted prose.

Checked the ruling's three-part test against the code: (1) `CHANNEL_SKILL`
is the OR's first disjunct — `channel_role_active` returning `True` only
ever *adds* a `True` to `in_scope`'s result, never narrows it — an added
denial, not an exemption. (2) shown above: removing it strictly widens the
gate for two call shapes (GraphQL, `hub pull-request`) and one payload
class (same-origin `--repo`). (3) the constant is defined once, used once,
with no second name it dispatches among (`CHANNEL_SKILL =
"upstream-defect-report"`, one string, one use site) — contrast
`merge-allow-gate.sh`'s pre-change 2-name tuple dispatching into a 2-key
table (see Site 2 below). All three hold under direct code reading.

Verified the "comment-only diff" claim myself — derived:
```
$ git show d329e9b9 -- on-the-record/hooks/upstream-defect-scope-guard.sh | grep -E '^[+-]' | grep -v '^+++\|^---' | grep -vE '^\+#|^-#|^\+$'
$ echo "exit:$?"
exit:1
```
(no matching lines printed — every added line is a `#`-comment or blank).

### Site 2 — `merge-allow-gate.sh`, capability removed

Exercised the gate directly, before and after, using a throwaway fixture
git repo outside this checkout (`/tmp/mag-fixture-checkout`, untracked in
this repo — branch `issue-4242/secure-coding`, one commit touching
`auth/login.py`, a local `origin/main` ref so
`git diff --name-only origin/main...HEAD` resolves) and a stub
`gates/landing_readiness.py` (also untracked, `/tmp/mag-stub-checkout`)
that always reports `PR #42: READY`, run against both the BEFORE and AFTER
worktrees' actual `merge-allow-gate.sh` scripts — not against the PR
record's transcript of a run:

- `MUSTER_SKILLS=secure-coding`, record absent — derived: BEFORE:
  `rc=0`, no output (withheld). AFTER: `rc=0`, allow JSON
  (`"permissionDecision": "allow"`, reason cites `landing_readiness=READY`).
- Same payload, record present — a file at the untracked, `/tmp`-only
  fixture-repo path `docs/issue-4242/reports/secure-coding.md` (untracked
  in this repo; it exists solely inside `/tmp/mag-fixture-checkout`,
  added and committed there via this session's own Write+git-add+git-commit
  calls) — derived: BEFORE and AFTER both produce the identical allow JSON
  (the routing-fix only ever withheld on record-absence, so a present
  record is unaffected either way, matching the PR record's claim).
- Same payload, `MUSTER_SKILLS` unset — derived: BEFORE and AFTER both
  produce the identical allow JSON (unaffected, matching the PR record's
  claim).

This reproduces the PR record's Site 2 table exactly: the only observable
behavior change across all three payload shapes is the first case (skill
mounted, sensitive path touched, record absent), which is exactly the
capability the PR's own removal comment names as removed.

### Site 3 — `board.py` `ownership_report`, path-only signal

Ran the PR's new test file at the PR head — canonical:
`dfbfaaa7:test/test_board_ownership_report.py`, read via
`git show dfbfaaa7:test/test_board_ownership_report.py` this session —
against both worktrees. Derived: AFTER,
`python3 -m pytest test/test_board_ownership_report.py -q` → `6 passed in
0.79s`. Copied the same test file onto the BEFORE worktree and re-ran it
there — derived: `5 passed, 1 failed` — the sole failure is
`test_other_role_writing_alt_subdir_now_unflagged_disclosed_widening`,
i.e. exactly the disclosed-widening case (a `coding`-role write to
`spikes/` is flagged before the change, silently unflagged after). This is
a stronger independent check than reading the diff: it proves the test
actually pins new behavior rather than passing vacuously against the old
code too.

Verified the "zero prior writes to these subdirs" claim directly — derived:
```
$ git log --all --diff-filter=A --oneline -- 'docs/issue-*/reports/spikes/*' 'docs/issue-*/reports/postmortems/*' | wc -l
0
$ git log --all --oneline -- 'docs/issue-*/reports/spikes/*' 'docs/issue-*/reports/postmortems/*' | wc -l
0
```
Confirms the disclosed widening reclassified no real historical write.

### Enumeration (acceptance bullet 3)

Re-ran the PR record's grep command myself, independently, against the PR
head worktree and a fresh shallow clone of tokenmaxxxer-core — not copied
from the record's pasted output — derived:
```
$ grep -rnE '\brole\s*==\s*"|\brole\s+in\s*\(|\bskill\s*==\s*"|\bskill\s+in\s*\(|MUSTER_SKILLS.*in\s*\(|in\s*\("[a-z-]+",\s*"[a-z-]+"\)|ROLES\s*=|_ROLES\s*=' \
    --include='*.py' --include='*.sh' . 2>/dev/null | grep -v -E '/(test|tests)/|docs/|\.md:'
```
on-the-record head, non-noise hits: `board.py:587` (`_front_role`'s
`("product-discovery", "technical-feasibility")` tie-break — canonical:
`dfbfaaa7:board.py` line 587, read via `sed -n '580,595p' board.py` this
session on the PR worktree), `board.py:892` (prose comment above
`ALT_RECORD_SUBDIRS`, matches as text not code), `scripts/behavior_metrics.py:35`
(`EXPECTED_COMMIT_ROLES = {"implementation", "coding"}`, a metrics
threshold, not an enforcement decision). Also present in the raw output
but correctly out-of-population and *not* individually named by the PR
record's own curation text: `harness/fixture-multirole/fixture_multirole/cli.py:21`
(`args.command in ("save", "load")`, CLI-subcommand dispatch, same shape
as the `spawn.py`/gates hits the record does exclude by name) and
`on-the-record/monitors/test_poll_heartbeat.py:118` (a `test_`-prefixed
file defining fixture string data, not live gate logic). Neither changes
the population count; both are test/CLI-dispatch noise by the record's own
stated criterion, just not individually listed. Also read
`on-the-record/hooks/quality-bar-gate.sh` lines 232-243 directly on the PR
worktree — derived: `sed -n '225,243p' on-the-record/hooks/quality-bar-gate.sh`
— confirmed the 7-key `_TRIGGER_PATH_PATTERNS` dict exists exactly as the
PR record quotes it.

tokenmaxxxer-core, fresh clone — derived:
```
$ git clone -q --depth 1 https://github.com/tokenmaxxxer/tokenmaxxxer-core.git /tmp/core-audit-verify
$ grep -rnE '\brole\s*==\s*"|\brole\s+in\s*\(|\bskill\s*==\s*"|\bskill\s+in\s*\(|MUSTER_SKILLS.*in\s*\(|in\s*\("[a-z-]+",\s*"[a-z-]+"\)|_ROLES\s*=|OBSERVER_ROLES' \
    --include='*.py' --include='*.sh' . 2>/dev/null | grep -v -E '/(test|tests)/|docs/|\.md:'
```
→ only CLI-flag-tuple noise (`trailer-gate.sh`, `board-gate.sh`,
`state.sh`, `gate-lib.py`) and two `#`-comment mentions inside
`approval-gate.sh`'s own CAPABILITY-REMOVED block (core#343, merged).
Zero live hits — matches the PR record's claim.

**Population re-derived independently: four live sites in on-the-record
(the three named plus `board.py:587`), one borderline dict
(`quality-bar-gate.sh`), zero in tokenmaxxxer-core — same count the PR
record reports.**

### Full test suite, failing-set byte-identity

Ran the full suite myself on both worktrees rather than trusting the PR
record's pasted summary line — derived:
```
BEFORE (d329e9b9^, = origin/main): 16 failed, 525 passed, 6 xfailed in 5.82s
AFTER  (dfbfaaa7):                 16 failed, 531 passed, 6 xfailed in 5.45s
$ grep '^FAILED' before.log | sort > before_failed.txt
$ grep '^FAILED' after.log  | sort > after_failed.txt
$ diff before_failed.txt after_failed.txt && echo "IDENTICAL FAILING SET"
IDENTICAL FAILING SET
```
16 pre-existing failures, same 16 test names, in both worktrees; the +6
passing tests are exactly the new `test_board_ownership_report.py` file.
Matches the PR record's claim exactly.

## Why

I was asked to test hardest whether condition (b) of `in_scope` really
cannot cover a channel session's own-origin or target-less PR-creation
attempt, since the whole site-1 ruling depends on that being true —
canonical: `in_scope()`'s body, `dfbfaaa7:on-the-record/hooks/upstream-defect-scope-guard.sh`
lines 215-234 (quoted and traced through in "What was done" above). I read
the function and its call sites directly rather than the ruling's prose
description of them, and confirmed the premise holds structurally:
`in_scope(None)` can only ever return `True` via `channel_role_active`,
and a same-origin `--repo` value makes the `target_repo is not None`
branch return `False` too. There is no path through the function where (b)
alone denies either shape. The ruling's premise is true, so its conclusion
(site 1 stays kept) is not built on a false foundation, and I found no
basis in this review to send the PR back on that ground.

For the two edited sites, I did not trust the PR record's transcript of
its own gate exercises — I rebuilt the fixtures and ran the actual scripts
at both commits myself (see "What was done", Site 2 and Site 3), and
separately ran the actual pytest files at both commits. Every number
reported above is from a command executed in this session against the PR
head or the parent commit, not a quotation of the subject's record.

### One reproducibility defect found

The PR record's Site 2 "byte-identical" claim for the removed
`secure-coding` trigger-pattern list and `quality-bar-gate.sh`'s own copy
cites this exact command as producing no output:
```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)
```
Running it myself does NOT reproduce "no output" — derived:
```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)
1,3c1,3
<         "secure-coding": ["**/auth/**", "**/*credential*", "**/*permission*",
<                            "**/*secret*", "**/*password*", "**/*login*",
<                            "**/*input*", "**/*sanitiz*", "**/*validat*"],
---
>     "secure-coding": ["**/auth/**", "**/*credential*", "**/*permission*",
>                        "**/*secret*", "**/*password*", "**/*login*",
>                        "**/*input*", "**/*sanitiz*", "**/*validat*"],
```
The two lists differ only in leading indentation (the removed code was
nested one function-level deeper than the module-level dict in
`quality-bar-gate.sh`) — stripping leading whitespace from both sides
before diffing produces no output (derived:
`diff <(...| sed 's/^[[:space:]]*//') <(...| sed 's/^[[:space:]]*//')` →
no output), so the actual glob-pattern content is identical and the
substantive backstop argument (the same 9 patterns exist in both files)
still holds. But the PR record's own "derived:" citation, as literally
written, is not reproducible — it asserts a specific command produces no
output, and it does not. Logged as an open finding below rather than
grounds to send the PR back, since the conclusion the citation supports is
independently true.

## What did not work

None.

## Upstream basis

- `dfbfaaa7:docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md` — PR #2721's own record (on the PR's branch, not this branch; not `same-commit`). Read directly via `git show dfbfaaa7:docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md` this session — none of its prose is restated here as evidence; every claim above is re-derived from the code and from commands run in this session.
- `gh issue view 2719 --json comments` (read live this session, canonical) — the operator's site-1 ruling comment, dated 2026-08-27, quoted and tested against the code in "What was done" above.
- `gh pr view 2721 --json title,body,files,commits,headRefName,baseRefName,state` and `gh pr diff 2721` (read live this session, canonical) — the PR's actual head commit, files, and full diff.

## Open findings

1. PR #2721's record contains one unreproducible `derived:` citation
   (Site 2's `diff <(...) <(...)` claiming "no output — identical" for the
   `secure-coding` trigger-pattern lists) — the command as literally
   written produces a 6-line indentation-only diff, not no output —
   canonical: this record's "Why" section, "One reproducibility defect
   found," which shows both the failing command and its passing
   whitespace-normalized variant, run this session. The substantive
   conclusion it supports (the two files carry the same 9 glob patterns)
   is independently true once whitespace is normalized, so this does not
   change this review's verdict, but the citation itself should be
   corrected (e.g. `diff <(... | sed 's/^[[:space:]]*//') <(...)`) if PR
   #2721 is amended for any other reason. Resolution path: leave to the PR
   author to fix on next touch; not severe enough to independently request
   a revision for.
2. The PR record's enumeration curation names three non-noise hits by path
   but the raw grep also surfaces two more lines
   (`harness/fixture-multirole/fixture_multirole/cli.py:21`,
   `on-the-record/monitors/test_poll_heartbeat.py:118`) that are correctly
   out-of-population (CLI dispatch and test-fixture string data,
   respectively) but weren't individually named in the record's curation
   text — canonical: this record's "Enumeration" section above, same grep
   command re-run this session. Population count is unaffected. Resolution
   path: none needed — noted for completeness only.

## Next steps

None. `loop_state` is `landed` — every claim in PR #2721 this review was
asked to check has an executed command and its output in "What was done"
above: the site-1 ruling's premise (traced through `in_scope()`'s own
code), both edited gates' before/after behavior (fixture runs against both
worktrees), the enumeration (independent grep re-run against both repos),
and the failing-test-set byte-identity (`diff before_failed.txt
after_failed.txt` → `IDENTICAL FAILING SET`, shown in "What was done"
above) — with one reproducibility defect in a supporting citation logged
in "Open findings" rather than left undiscovered.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; used the skill's
  structural-independence stance to re-derive every claim in PR #2721 from
  the PR head and live repo state (worktrees, fresh fixtures, a fresh
  `tokenmaxxxer-core` clone, direct reads of `in_scope()`) rather than
  restating or trusting the subject's own record's prose, and it is what
  surfaced the one derived-command citation that does not reproduce as
  written (Site 2's whitespace-sensitive `diff`).
- other mounted skills: not triggered.
