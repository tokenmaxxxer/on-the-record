---
issue: 2720
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
loop_state: landed
type: verification
breaking: false
verdict: pass
code_under_review: PR #2722 (issue-2720/technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3), commit c3e1afc7
upstream:
  - path: consult.py
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: directive_assembly.py
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: spawn.py
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: gates/record_lint.py
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
  - path: on-the-record/gates/record_lint.py
    sha: c3e1afc77b4709942a87cf1281effb73fae82b3c
---

# issue-2720 — independent-verification-2 record

## What was done

Independently audited PR #2722 (branch
`issue-2720/technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3`,
commit `c3e1afc7`), which claims to resolve issue #2720 (runtime `.py` prompt
strings carrying the retired 역할/role vocabulary, missed by #2600 slice 3's
`.md`-glob sweep in PR #2714). Re-derived the population from scratch in a
separate git worktree checked out at the PR's head commit rather than
trusting the PR's own record, then spot-checked the kind-filtering
(prompt-text vs CLI/log/gate-diagnostic vs docstring) and the coupled-line
disposition table against the actual source.

canonical: `gh pr view 2722 --json title,body,state,mergeable,commits,files,baseRefName,headRefName` — state OPEN, base `main`, head
`issue-2720/technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3`,
body contains `Closes #2720`, 3 commits, 5 source files touched
(`consult.py`, `directive_assembly.py`, `spawn.py`, `gates/record_lint.py`,
`on-the-record/gates/record_lint.py`) plus the PR author's own record and
deviation-log file (untracked in this branch — those two files live only on
PR #2722's branch, per the same `gh pr view --json files` output; this
branch does not carry them).

**1. Population re-derivation (acceptance check 1).** derived: reproduced
the PR record's exact AST+`tokenize` scanner script against a worktree at
`c3e1afc7` and ran `python3 /tmp/scan_verify.py > /tmp/verify_out_post.txt &&
grep -vc docstring /tmp/verify_out_post.txt && grep -c docstring
/tmp/verify_out_post.txt` — result:
```
285
186
```
This matches the PR record's claimed 285/186 exactly — an independent
re-run of the same derivation, not a re-paste of the PR's own numbers.

**2. Cross-check against a naive `grep`.** derived: `grep -rn "역할"
--include="*.py" . | grep -v '^\./docs/' | grep -v '^\./runs/'` found 110
distinct `path:line` locations vs. the scanner's 53 역할-only hits (after
normalizing a `./` path-prefix mismatch between the two tools' outputs,
found via `comm -23`). derived: read every one of the resulting 67
candidate lines (`comm -23 /tmp/raw_lines_norm.txt
/tmp/scanner_lines_norm.txt`) in source with `sed -n` around each — every
one was either (a) inside a `#`-comment, correctly excluded by
`tokenize.COMMENT`, or (b) a continuation line of a multi-line docstring
the scanner had already attributed to its opening line under the
`docstring` kind. None was a missed runtime string-literal. This
independently confirms the scanner does not silently drop genuine
prompt-text hits.

**3. Kind-filter spot-check** (which of the 285 string-literal hits are
"prompt text" reaching a model automatically vs. CLI/log/gate-diagnostic
text). derived: read the actual sink for `pipeline.py:449`,
`skills.py:497`, `spawn.py:3075`, `events.py:508,557`,
`watchdog.py:1040-1041`, `gates/ci.py:601-614`, `board.py:840,842,911,1277,1285`
with `sed -n` around each — all are `sys.exit(...)`, `print(...)`, or
appended to a `bad`/`mismatch` list a CI gate prints/comments; none is
passed as `input=` to a `subprocess.run(...)` model call. Consistent with
the PR record's disposition.
canonical: `consult.py:1577` (`_append_judge_trace(trace_path, ts, role,
merge_sha, outcome)` in the `finally:` block of `judge_cmd`) — confirms the
`outcome` string built at `consult.py:1490` (deferred by the PR as a
"log-line", not prompt-text) is only ever written to a trace file, never to
a model prompt; the deferral is correct.
canonical: `directive_assembly.py:612` builds the record filename as
`f"{role}.md"`, and the `_RECORD_SKELETON` template at `directive_assembly.py:509`
has a literal `role: {role}` frontmatter line — both confirm that the
`<role>`/`role:` prose at `directive_assembly.py:176,509` and
`gates/record_lint.py:1457` (deferred to slice 4/5) documents the current
Python identifier/frontmatter key, so a reasonable deferral rather than
scope avoidance.

**4. Fixed-lines vs. final diff.** derived: `gh pr diff 2722` — confirmed
all 15 intended line changes named in the PR record are present in the
actual diff: `consult.py` (5 edits across `consult_cmd`,
`_judge_prefilter`, `_judge_validate`, `judge_cmd`, `_run_panel_session`),
`directive_assembly.py` (4 edits — including the two the PR's own "What did
not work" section says were initially missed and caught by its own
adversarial-review pass, all four now present), `gates/record_lint.py` +
its `on-the-record/` twin (1 edit each, "role output"→"skill output"),
`spawn.py` (1 edit, "고정 role->skill 표"→"고정 스킬 매핑 표"). No Python
identifier (`role`, `peer_role`) was renamed anywhere in the diff — the
must-not "do not rename the interpolated role variable" was honored.

**5. Coupled-line disposition (acceptance check 2).** derived: read the PR
record's disposition table (each line named with an explicit fixed/deferred
call and reason) against `gh pr diff 2722` and the source reads in item 3
above — every named line's actual state in the diff matches its claimed
disposition; no line was silently split. Spot-checked the fixed case the
issue itself names as the hard example, `consult.py:1414`: confirmed in the
diff as `역할 '{role}' 의 관할(role jurisdiction)` → `스킬 '{role}' 의
관할(skill jurisdiction)`, `{role}` interpolation left untouched.

**6. Regression check (test suite).** derived: checked out the PR's base
commit (`39890acf`, pre-PR) into a separate worktree and ran `python3 -m
pytest -q -k "consult or directive"` on both the base and the PR-head
worktrees — result: identical on both:
```
4 failed, 15 passed in ~2.3s
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
```
Same 4 failing tests, same two pre-existing root causes (a lambda signature
mismatch and a sandboxed-workdir `fatal: 'origin' does not appear to be a
git repository` network failure) on both commits — neither related to the
vocabulary edits. This is a subset reproduction of the PR record's
full-suite claim (`15 failed, 389 passed, 6 xfailed`, identical set
stashed/unstashed); consistent, no new regression from this diff.

**7. Consult-call demonstration (acceptance check 3, "3b").** acceptance:
independently re-ran `python3 spawn.py consult general-purpose "2+2는
얼마인가? 숫자만 답하라."` against the PR-head worktree (not copied from the
PR record) — result:
```
{
  "answer": "4",
  "confidence": "high",
  "caveats": []
}
```
Byte-identical to the PR record's own run. Verified via the actual
subprocess trace: `spawn.py consult-log` in that worktree showed a new
`verb=consult | question='2+2는 얼마인가? 숫자만 답하라.' | outcome='ok: 4 |
...'` entry timestamped at this session's run, confirming this exercised a
real `claude -p` call through the edited `base_prompt` in `consult_cmd`,
not a cached or stubbed result.

**8. "3a" (a session spawned after the change reaches a PR).** The PR
record discloses this as `unverifiable` with a stated reason: a real nested
spawn would open a genuine branch/PR under the operator's account as a side
effect of verifying a single vocabulary fix, which is disproportionate and
which the PR author correctly judged itself unauthorized to trigger. It
substitutes `py_compile` on the edited `spawn.py` path plus the fact that
its own delivery is such a session reaching a PR. I did not additionally
attempt a real nested spawn for the same reason — this verification
session's own PR (opened as part of this record's delivery) is itself a
second, independent instance of exactly that demonstration. Accepted the
PR's disclosed-unverifiable disposition as reasonable rather than treating
it as a gap.

canonical: items 1–8 above, each backed by a command this session executed
directly (the `derived:`/`acceptance:` tags and their outputs) — the PR's
claims reproduce independently: no missed prompt-text lines, no incorrect
kind classification, no silently split coupled lines, no regression, and
the one demonstrated runtime behavior (the consult call) reproduces
byte-for-byte.

## Why

canonical: this session's spawning task prompt ("이 subject 에 필요한 총
개수: 2, 이 세션의 슬롯: independent-verification-2") — this subject
requires 2 independent verification records before its deliverable is
treated as confirmed landed, and this record is slot 2. The audit method
chosen — re-derive the population and re-run the acceptance commands in a
fresh worktree rather than re-reading the PR's own record as ground truth —
is what makes this verification independent rather than a restatement of
the builder's claims.

## What did not work

A naive `grep "역할"` initially appeared to find 57 more hits than the
scanner (item 2 above), which looked like a possible undercount in the PR's
derivation script. Normalizing a `./` path-prefix mismatch between the two
tools' outputs resolved the apparent discrepancy to 0 real gaps after
manual line-by-line review of all 67 candidates; recorded here per the
deviation-logging convention as a real moment where the expected match
did not hold on the first comparison.

## Upstream basis

- `consult.py`, `directive_assembly.py`, `spawn.py`, `gates/record_lint.py`,
  `on-the-record/gates/record_lint.py` at PR head `c3e1afc7` — the 5 files
  PR #2722 modifies, all audited above (see frontmatter `upstream:`).
- PR #2722's own delivery record and deviation-log entry — untracked in
  this branch (they live only on PR #2722's branch); read via `gh pr diff
  2722`, not via a local file path in this checkout.
- Issue #2720 (`gh issue view 2720`) — acceptance-criteria basis for this
  audit.

## Open findings

None beyond what PR #2722 itself already discloses as open. canonical: PR
#2722's own record "Open findings" section (read via `gh pr diff 2722`) —
slice 4 (identifier rename) and slice 5 (persisted-key rename) remain open
under #2600, both explicitly out of this issue's scope per its own
Non-goals, and both already named as open by the PR itself, not newly
surfaced by this audit.

## Next steps

None. canonical: items 1–8 in "What was done" above, each executed this
session with its own `derived:`/`acceptance:` command and output —
loop_state set to landed on that basis, and PR #2722 recommended to proceed
to merge from a verification standpoint.

### Skill verdicts

skill-verdict: work-in-english — applied: invoked; wrote this record, the
commit message, and the PR body in English per the skill (the spawning task
was communicated in Korean), with the final user-facing summary in Korean.
other mounted skills: not triggered.
