---
issue: 3129
role: silent-failure-audit+test-derivation+implementation-blueprint-ced67070
author: silent-failure-audit+test-derivation+implementation-blueprint-ced67070
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/amendment_channel.py, tests/test_amendment_channel.py (both untracked on THIS branch — they live only on PR #3137's branch, not merged; see note below)
loop_state: landed
type: bugfix
breaking: false
verdict: pass — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` (from `/tmp/pr3137-repair2`, PR #3137's branch) — result: 50 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 304 passed, 0 failed
upstream:
  - path: PR #3137 (branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019)
    sha: bedd1c72d506d83bceb1a038c741fc6371aa5d32
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md (PR #3159, merged 46998cf8)
    sha: 46998cf800aa9417da38c325b209dc285e30a5ae
---

# issue-3129 — silent-failure-audit+test-derivation+implementation-blueprint-ced67070 record

canonical: `gh pr view 3137 --json headRefName,state` output (state:
OPEN, headRefName:
`issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`)
— note on paths in this record: `on-the-record/hooks/amendment_channel.py`
(untracked on this branch) and `tests/test_amendment_channel.py`
(untracked on this branch) do not exist in THIS session's own branch
(`issue-3129/silent-failure-audit+test-derivation+implementation-blueprint-ced67070`,
based on `origin/main`), because PR #3137 (the branch that carries them)
is not merged to main yet.

derived: `git worktree add /tmp/pr3137-repair2 issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`
— result: `작업 트리 준비 중 ('issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019'
가져오는 중) / HEAD의 현재 위치는 bedd1c72입니다`. All code work described
below was done directly on PR #3137's branch, in that separate worktree,
per the spawning instructions ("push to the existing branch, do not
merge") — this session's own branch (current file's branch) never
touched those two files, which is why they read as untracked here.

## What was done

canonical: `gh pr view 3159 --json body` output, section "Writer-side
automaticity Present, but repo-keying at write time Incorrect" — this
session's assignment: repair round 2 on PR #3137, scoped to the single
new **Incorrect** finding PR #3159 reported after independently
re-verifying round 1's cross-repo fix.

derived: `git show 46998cf8:docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md`
(section "### 4. Writer-side automaticity and repo-keying at write time")
— `maybe_write_from_command()` derived the amendment marker's repo key
from the raw `PostToolUse` payload `cwd` (the orchestrator's own session
directory) instead of the repo the `gh issue edit` command it inspects
actually targets. PR #3159 reproduced the issue's own worked example
literally: an orchestrator whose session `cwd` is `on-the-record`,
running `cd .../study-companion && gh issue edit 42 --body ...`, wrote a
marker keyed to `tokenmaxxxer/on-the-record` rather than
`tokenmaxxxer/study-companion`. Per the spawning instructions, this is
exactly how the real orchestrator operates (it edits `study-companion`
issues from the `on-the-record` checkout), so the old cwd-keyed behavior
was wrong on every real use, not an edge case.

Fix, all on PR #3137's branch (worktree at `/tmp/pr3137-repair2` per the
note above, never merged; both paths below untracked on THIS record's
own branch):

- commit `7957bda7` — `on-the-record/hooks/amendment_channel.py`
  (untracked on this branch, see note above): added
  `_explicit_repo_flag(command, segment_start)` (an explicit
  `--repo`/`-R owner/repo` on the `gh issue edit` invocation's own
  segment — bounded by the next `;`/`&&`/`||`/`|` so a flag from an
  unrelated command in the same compound line is never picked up) and
  `target_repo_for_command(command, cwd, segment_start)`, which tries
  that flag first, then falls back to `hook_input.resolved_cwd(command,
  default=cwd)` — the shared, total, no-network leading-`cd <path> &&`
  parser `hook_input.py` already exports for exactly this class of
  defect ("each hook grew its own ad-hoc `cd <path> &&` extraction", per
  that module's own docstring) — before calling the existing
  `repo_slug_for_cwd()`. `maybe_write_from_command` now calls
  `target_repo_for_command()` instead of `repo_slug_for_cwd(cwd)`
  directly; the unresolvable-repo fallback (no marker written, one
  stderr line, never a shared bucket) is unchanged and reused as-is for
  both new "could not resolve" paths (bad/missing `--repo` value,
  unparseable `cd` target).
  - a segment-boundary bug caught before landing (this session's own
    manual check, not a citation): `_GH_ISSUE_EDIT_RE`'s match can start
    at a consumed leading separator (`; gh issue edit ...`), not at `gh`
    itself; using that raw `m.start()` as the flag-segment's left edge
    made the very next character (the separator) look like the
    segment's own right boundary, collapsing the scan to zero width.
    Fixed by offsetting past `m.group(0).find("gh")` before computing
    the segment.
- commit `bf28bf93` — `tests/test_amendment_channel.py` (untracked on
  this branch, see note above): new `WriterSideTargetsCommandNotSessionCwd`
  test class, driven through the real `run_hook` entrypoint (not the
  lower-level functions), per the spawning instructions' explicit ask:
  - `test_cd_into_another_checkout_keys_the_marker_to_that_checkout` —
    the worked example verbatim (session `cwd` = an `on-the-record`-
    origin checkout, command = `cd <study-companion-checkout> && gh
    issue edit 42 --body ...`); asserts the marker exists keyed to
    `tokenmaxxxer/study-companion` and does NOT exist keyed to
    `tokenmaxxxer/on-the-record`.
  - `test_explicit_repo_flag_overrides_cwd` — `--repo
    tokenmaxxxer/study-companion` with no `cd`, session `cwd` on a
    different repo; same two-sided assertion.
  - `test_no_cd_no_repo_flag_still_keys_to_session_cwd` — regression
    baseline: plain `gh issue edit ... --body ...` with neither `cd` nor
    `--repo` still keys off the session `cwd`, unchanged from before
    this repair round.

## Why

`hook_input.resolved_cwd()`/`cd_target()` already existed in this repo
specifically to close "ad-hoc `cd` extraction" as a recurring hook
defect class (its own docstring names this), and `amendment_channel.py`
already imports `hook_input` (for `tool_command()`) — reusing it here
instead of writing a second bespoke `cd`-parser keeps the fix inside a
boundary that already carries its own total-function contract (never
raises, `OpaqueCommand`/`NoCdTarget` handled) rather than adding a new
one this module would have to test from scratch. `--repo`/`-R` has no
equivalent shared helper in this repo, so it is a small local regex
(`_REPO_FLAG_RE`), scoped to the matched `gh issue edit` command's own
segment specifically so a `--repo` flag belonging to a different command
earlier or later in a compound Bash line is never mistaken for this
one's target — the same false-attribution shape the cwd bug itself was,
just at flag-parsing granularity instead of directory granularity. An
invalid or missing `--repo` value falls through to the `cd`/cwd
resolution rather than erroring, consistent with this module's house
style of "never raise, degrade to the next-best signal."

## Upstream basis

- PR #3137 (`bedd1c72`, branch
  `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`):
  the round-1 repair this round builds directly on top of (same branch,
  new commits on top).
- PR #3159's record (merged `46998cf8`): the independent verification
  that confirmed cross-repo isolation, unresolvable-slug isolation, and
  fire-once/stop-after-absorption all survived round 1 unweakened, and
  reported the one new **Incorrect** finding this round fixes.
  canonical: `git show 46998cf8:docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md`
  read in full this session.

## What was verified to survive (re-run this session, not re-cited from PR #3159)

acceptance: `python3 -m pytest tests/ -q` (from `/tmp/pr3137-repair2`,
after this session's fix, includes
`RunHookEndToEnd::test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo`,
`RunHookEndToEnd::test_two_repos_with_unresolvable_slugs_do_not_collide`,
and `GhCommandDetection::test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr`)
— result:
```
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 94%]
................                                                         [100%]
304 passed, 2 warnings in 10.55s
```
All three named tests are included in that passing run (no test was
skipped or deselected).

acceptance: `python3 gates/probe_running_session_sees_amendment.py`
(from `/tmp/pr3137-repair2`) — result:
```
ok
```

acceptance: `python3 gates/probe_amendment_notice_fires_once.py` (from
`/tmp/pr3137-repair2`) — result:
```
ok
```

## Acceptance checks (all four from the spawning issue, run from `/tmp/pr3137-repair2` at commit `bf28bf93`)

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` —
result:
```
...............................................                          [100%]
50 passed in 0.94s
```
(47 pre-existing + 3 new `WriterSideTargetsCommandNotSessionCwd` cases.)

acceptance: `python3 gates/probe_running_session_sees_amendment.py` —
result: `ok` (same run cited above).

acceptance: `python3 gates/probe_amendment_notice_fires_once.py` —
result: `ok` (same run cited above).

acceptance: `python3 -m pytest tests/ -q` — result: `304 passed, 0
failed` (same run cited above; 301 PR #3159 confirmed + 3 new).

derived: `python3 -m pytest test/ -q` (from `/tmp/pr3137-repair2`, not
in the acceptance list but re-checked per the spawning instructions'
pre-existing-failure note) — result:
```
15 failed, 548 passed, 3 xfailed in 32.37s
```
Same 15 failing test IDs (`ApprovalGateEquivalenceTest`,
`BranchRoleFieldDualReadEquivalenceTest`,
`CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
`Bm25CrossFamilySkillMatchesTest`, `ConsultJudgeStageTest` (x2),
`FourSurfaceCandidateCorpusTest`,
`SpawnOneCrossFamilyAcceptanceTest` (x2),
`SkillJudgeOverlapOrderingTest`,
`SpawnOneArtifactSkillPairingTest` (x2),
`SkillJudgeLedgerFieldTest` (x3)) PR #3147/#3159 already confirmed owned
by #3091 — no new failures introduced by this change.

derived: verified each of the two new behavior-changing tests fails
against the pre-fix commit — `git stash && git checkout bedd1c72 --
on-the-record/hooks/amendment_channel.py && git stash pop` (keeps the
new test file, restores the pre-fix module), then `python3 -m pytest
tests/test_amendment_channel.py -q -k WriterSideTargetsCommandNotSessionCwd`
— result:
```
FAILED tests/test_amendment_channel.py::WriterSideTargetsCommandNotSessionCwd::test_explicit_repo_flag_overrides_cwd
FAILED tests/test_amendment_channel.py::WriterSideTargetsCommandNotSessionCwd::test_cd_into_another_checkout_keys_the_marker_to_that_checkout
2 failed, 1 passed in 0.87s
```
`test_no_cd_no_repo_flag_still_keys_to_session_cwd` is the one that
passed — expected, since it is a regression baseline (same cwd-keying
behavior before and after this fix), not a reproduction of the defect.
`git restore --staged --worktree on-the-record/hooks/amendment_channel.py`
(untracked on this branch, same worktree path as above) restored the
post-fix module afterward; re-ran the full suite (cited above under
"What was verified to survive") to confirm the restore landed cleanly.

## Open findings

None from this round's scope. Two minor findings PR #3147/#3159 carried
forward unchanged (truncation marker on long notes, `main()`'s
stdin/stdout `OSError` stderr trace) remain out of this repair round's
stated scope and were not re-litigated.

## What did not work

None.

## Next steps

derived: `git push origin issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`
(from `/tmp/pr3137-repair2`, run after each commit) — result (final
push shown): `7957bda7..bf28bf93
issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019
-> issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`
— both commits landed on `origin`. Nothing further from this session:
code changes are committed and pushed to PR #3137's branch, not merged,
per the spawning instructions. PR #3137 remains open with `Closes #3129`
on its own body (unedited by this session); this record documents the
repair, and this session's own branch carries only this record.
