---
issue: 3281
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: scripts/issue-3041/run_pair.sh, on-the-record/hooks/amendment_channel.py, on-the-record/checks/macos_bash32_compat.py, docs/handbooks/operations.md (PR #3282, head b5a83907cdcb3000d472f3ed6e269b2d85ce44b9)
loop_state: terminal
type: verification
breaking: false
verdict: PR #3282's three claimed fixes hold up under independent re-derivation (bash guard preserves quoting on multi-word non-empty arrays, not just the report's single-word case; the /proc runtime notice genuinely fires and fails closed) and both acceptance checks reproduce exactly, including that the one remaining pytest failure is confirmed pre-existing on main by this session's own worktree run, not cited from the PR's claim. One correction to a prior verification record surfaced (PR #3286 / commit 7e63ebbba58a3e0cae0f0feddb05368a53c0d2c1 misattributes the check's `os.path.isdir("/proc")` regex-blind-spot line to :482, which pre-dates this PR; the actual new line is :913-914 -- the underlying blind-spot finding itself is independently confirmed real and still applies to the new line).
upstream:
  - path: PR #3282 (branch issue-3281/silent-failure-audit+test-derivation-e073366a)
    sha: b5a83907cdcb3000d472f3ed6e269b2d85ce44b9
---

# issue-3281 — independent-verification-1 record

## What was done

Independent, structurally separate re-derivation of PR #3282's claims against
the actual code, run from throwaway `git worktree` checkouts rather than by
citing the PR's own comment or either of the two prior independent
verifications already merged for this issue.

canonical: `gh pr list --search "3281 in:title" --state all --json number,title,headRefName,state,mergedAt` (this session's own fetch) — shows PR #3284 (merged) and PR #3286 (merged) already recorded independent verifications of PR #3282 under the `adversarial-review`/`silent-failure-audit` role names, distinct from this record's `independent-verification` role; PR #3282 itself is still OPEN.

**1. Re-derived both acceptance checks from a clean worktree at the PR's own
head**, not from the PR's self-reported comment:

canonical: `git worktree add /tmp/pr3282-verify origin/issue-3281/silent-failure-audit+test-derivation-e073366a --detach`, then in that worktree:

derived: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -q` — result:
```
4 passed in 0.84s
```

derived: `python3 -m pytest -q` — result:
```
1 failed, 1652 passed, 3 xfailed, 2 warnings in 46.01s
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
```

**2. Independently re-derived the "no new failures relative to main" claim**
from a second clean worktree at `origin/main`, rather than accepting the PR's
own `git stash`-based claim:

derived: `git worktree add /tmp/main-verify origin/main --detach`, then:
```
python3 -m pytest harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace -q
1 failed in 0.85s   (same assertion, same stdout: '')
```

derived: `python3 -m pytest -q` on `origin/main` — result:
```
2 failed, 1650 passed, 3 xfailed, 2 warnings in 54.35s
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
```
This confirms both halves of the acceptance claim in one independently-run
pair: main fails 2 (the pre-existing harness flake, plus the compat check
itself — this is literally the issue's own opening complaint, reproduced
live); the PR head fails only the pre-existing harness flake. Total
non-xfailed count also reconciles: 1650+2=1652 main, 1652+1=1653 PR-head —
the +1 is the one new test PR #3282 added
(`test_no_proc_on_platform_is_fail_closed_with_a_distinct_notice`).

**3. Re-derived the three site fixes from the diff and `git blame`, not from
the PR's or a prior verification's prose:**

- Site 1 (`scripts/issue-3041/run_pair.sh:96,109`): confirmed via
  `git diff origin/main...origin/issue-3281/silent-failure-audit+test-derivation-e073366a -- scripts/issue-3041/run_pair.sh`
  that both `env "${UNSET_ARGS[@]}"` sites became
  `env ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"}`. The PR's own report tested this
  guard only with a single-word array element (`-u FOO`). I ran an
  independent edge case the prior reports did not cover — a multi-word
  element, to check for word-splitting/quoting loss:

  derived:
  ```
  $ bash -c '
  set -euo pipefail
  UNSET_ARGS=(-u "VAR WITH SPACE" -u "OTHER")
  i=0
  for a in ${UNSET_ARGS[@]+"${UNSET_ARGS[@]}"}; do
    i=$((i+1)); echo "arg$i=[$a]"
  done
  echo "count=$i"
  '
  arg1=[-u]
  arg2=[VAR WITH SPACE]
  arg3=[-u]
  arg4=[OTHER]
  count=4
  ```
  Quoting is preserved (4 args, not 5 from word-splitting `VAR WITH SPACE`) —
  the guard does not corrupt a non-trivial non-empty array, closing a gap
  the PR's own single-word test left open. No bash 3.2 binary was available
  in this environment either (`bash --version` — GNU bash 5.1.16 only, no
  `bash-3.2`/`bash3.2` on `$PATH`, confirmed via `which`), so, like the PR's
  own report, this cannot independently reproduce the bash-3.2
  unbound-variable abort itself; PR #3284's record already did that against
  a real `bash:3.2` Docker image, which this record does not re-attempt.

- Site 2 (`on-the-record/hooks/amendment_channel.py`): confirmed via
  `git blame` — not the diff alone — exactly which lines are new. The
  caller-side check `record_amendment_from_response()`'s
  `if not os.path.isdir("/proc"): return NoProcOnPlatform()` is new, at
  lines 913-914, committed in `f5c4f6384` (this PR's first commit). The
  callee `registered_repo_for_pid()`'s own `if not os.path.isdir("/proc"):
  return None` at line 482 is **not** new — `git blame -L 480,484` on the
  PR-head worktree attributes it to `638620e4f`, dated before this PR's
  commits, i.e. it already existed on `main`. This matters because a prior
  verification record (PR #3286, see Open findings below) cites line 482 as
  the PR's own new code; it is not.

  Confirmed the new `NoProcOnPlatform` path fails closed: `main()`'s
  nonzero-exit tuple was extended to include it (verified by reading the
  diff hunk directly, not paraphrasing it), and `_report_write_result()`'s
  new branch writes a stderr line containing both "no /proc" and "macOS" —
  independently re-ran the PR's own new test in the PR-head worktree
  (not cited from its "84 passed" summary alone):

  derived: `python3 -m pytest tests/test_amendment_channel.py -q` — result:
  ```
  84 passed in 1.00s
  ```

- Site 3 (`on-the-record/checks/macos_bash32_compat.py`): confirmed
  `KNOWN_PROC_SITES` gained `"amendment_channel.py"`
  (`grep -n KNOWN_PROC_SITES` on the PR-head worktree). Read `check_py_file()`
  directly (lines 151-179) to confirm, independent of any report's
  characterization, what "passing" actually proves: it is a file-level
  allowlist membership check plus a regex hit-count — it does not itself
  verify that a runtime-visible notice exists in the code. The "must have a
  runtime notice, not just a docstring" requirement is enforced by human
  review at PR time, not mechanically by this check. I verified the notice
  exists as actual code (not just as the allowlist-comment's claim) by
  reading `_report_write_result()`'s new `NoProcOnPlatform` branch directly,
  per the confirmation in Site 2 above.

**4. Checked the two must-nots** stated in the issue:
  - Linux `/proc` reads unchanged: the pre-existing `NoRegisteredRepo`-path
    tests in `tests/test_amendment_channel.py` (none of which mock
    `os.path.isdir`) ran unmodified and passed in the same 84-test run
    above, exercising the real, un-mocked `/proc` on this Linux worktree.
  - Non-empty-array behavior unchanged: covered by the multi-word edge case
    in Site 1 above, which is a stronger check than the PR's own
    single-word test.

## Why

Per this task's framing, the risk this record is specifically guarding
against is citation drift: treating a green PR comment, or a prior
verification's prose, as itself the evidence. Every claim above was
re-derived from a fresh `git worktree` at the actual commit sha, from
`git blame` rather than the diff's framing, or from a fresh edge case the
existing records had not run — not copied from PR #3282's comment or from
PR #3284/#3286's records.

canonical: `gh pr list --search "3281 in:title" --state all --json number,title,headRefName,state,mergedAt` (this session's own fetch, cited in full in "What was done" above) — confirms PR #3284/#3286 already exist as merged verification records, which this record deliberately re-derives past rather than cites.

## What did not work

None.

## Upstream basis

canonical: `git worktree add /tmp/pr3282-verify origin/issue-3281/silent-failure-audit+test-derivation-e073366a --detach` (this session's own checkout at sha `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9`) and `git worktree add /tmp/main-verify origin/main --detach` (at sha `7e63ebbba58a3e0cae0f0feddb05368a53c0d2c1`). Both worktrees were removed (`git worktree remove --force`) before this record was written.

canonical: `gh issue view 3281` (this session's own fetch) — body names the three sites and the two must-nots checked above.

canonical: `gh pr view 3282 --json body,commits` (this session's own fetch) — confirms the PR's own claimed test-plan numbers, independently re-derived rather than trusted, in "What was done" above.

## Open findings

- **A prior independent verification record cites the wrong line number for
  a real finding.** PR #3286 (merged as commit
  `7e63ebbba58a3e0cae0f0feddb05368a53c0d2c1`,
  `docs/issue-3281/reports/silent-failure-audit+test-depth-audit-4856384e.md`)
  states: "PR #3282 adds exactly this line,
  `if not os.path.isdir("/proc"): return NoProcOnPlatform()`, at
  `on-the-record/hooks/amendment_channel.py:482`". Line 482 is
  `registered_repo_for_pid()`'s pre-existing `if not os.path.isdir("/proc"):
  return None` (see Site 2 above, `git blame` confirms it predates this
  PR's commits by attribution to `638620e4f`). The genuinely new line with
  the identical `os.path.isdir("/proc")` shape is at 913-914
  (`f5c4f6384`), inside `record_amendment_from_response()`, not
  `registered_repo_for_pid()`.

  The underlying technical finding in that record — `_PROC_RE = re.compile(
  r'["\']/proc/')` requires a trailing slash and therefore does not match
  `os.path.isdir("/proc")` — is independently confirmed real by this
  session:

  derived: `python3 -c "import re; r=re.compile(r'[\"\x27]/proc/'); print(bool(r.search('if not os.path.isdir(\"/proc\"):')))"` — result: `False`

  and it does still apply to the actual new line (913-914), just not to the
  line the prior record named. This does not change PR #3282's compliance
  with issue #3281's stated acceptance criteria (the check's own coverage
  gap is a property of `macos_bash32_compat.py` predating this PR, not
  something the issue asked this PR to fix), but the citation itself should
  not be relied on for its stated line number without re-checking.
  Resolution path: informational only — no action needed against PR #3282;
  a future editor of PR #3286's record or of `macos_bash32_compat.py`
  should use line 913-914, not 482, if citing where this PR's code falls
  into the blind spot.

- **The pre-existing harness failure is confirmed pre-existing, not
  PR-introduced**, independently (see "What was done" §2) — not a new
  finding, but explicitly re-confirmed rather than cited from the PR's own
  `git stash` claim, per this task's independence requirement.

- No other open findings against PR #3282's own fix. The check's coverage
  gaps documented in PR #3286's record (uncaught `timeout` sites,
  file-level allowlist granularity) are real per that record and this
  session did not re-run them, since they are about the check's own scope
  rather than about re-deriving PR #3282's specific three-site fix, which
  is this record's target.

## Next steps

None — terminal.

## Skill verdicts

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: attempted invocation via the Skill tool, which returned "Unknown skill" (not mounted for invocation in this session despite the amendment notification naming it as matched); read its `SKILL.md` directly instead and applied its rules — re-derived all three site fixes and both acceptance numbers from fresh worktrees/blame rather than citing PR #3282's comment or PR #3284/#3286's prior verdicts (rule 3), ran a genuinely new edge case (multi-word array element, rule 2) instead of only re-running the PR's own happy-path test, and treated the two already-merged verification records as claims to re-check rather than settled fact — which surfaced the line-482-vs-913 citation error in PR #3286's record (rules 1, 4, 6).

skill-verdict: adversarial-review — applied: attempted invocation via the Skill tool, which returned "Unknown skill"; read its `SKILL.md` directly instead. Full blind two-session evaluator spawning was not used (this task is a single-session PR audit against a stated acceptance criterion, which the skill's own "First: does this even need the procedure?" section identifies as the "known, objective standard" case the full protocol is not for) — applied the underlying mechanism it teaches instead: treated PR #3282's own comment and PR #3284/#3286's prior verdicts as claims to independently re-derive rather than facts to cite, which is the core anti-self-review-bias mechanism the skill describes.

other mounted skills: not triggered.
