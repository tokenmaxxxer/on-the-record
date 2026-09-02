---
issue: 3127
role: adversarial-review+silent-failure-audit+experiment-trust-5431c323
author: adversarial-review+silent-failure-audit+experiment-trust-5431c323
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true
code_under_review: 824bbf8fc57b96783c5e83ae818a87bff4325b1d
loop_state: done
type: verification
breaking: false
verdict: sound
upstream:
  - path: docs/issue-3127/reports/implementation-blueprint+silent-failure-audit-b4641815.md
    sha: 125cef425783a024dcd8f7d44bc21a25af1424d3
  - path: docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md
    sha: 6d1a233b74f0f19cc7ef5b7fdb26e9c7cf6a3d2b
---

# issue-3127 — adversarial-review+silent-failure-audit+experiment-trust-5431c323 record

## What was done

Round-4 verification of PR #3169's fix (commit `824bbf8f`, merge of round-4's own fix `86cad057` with `origin/main`) to `scripts/issue-3127/verify_preregistration.py`, per the task's four-item instructions. canonical: `gh pr view 3169 --json commits` and `git show 6d1a233b:docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md` and `git show 125cef42:docs/issue-3127/reports/implementation-blueprint+silent-failure-audit-b4641815.md` — read first, per the task instructions, before attacking PR #3169's branch. Per round 3's own already-graded-Present findings (merge-commit bind, `--follow`/rename removal, failure-vs-empty distinction), these were not re-derived.

Set up a detached worktree at `824bbf8f` (`/tmp/pr3169review`) for all attacks and checks below, so nothing touched PR #3169's own branch. Note: `tests/test_issue_3127_verify_preregistration.py` (untracked / out-of-scope on this session's own branch — the file exists only on PR #3169's branch, which has not merged to main; commands against it below ran inside the `824bbf8f` worktree, not this session's own working tree) is cited below by its PR-#3169-branch path, following round 3's own precedent (`docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md:19`, `PR-3169-branch:tests/test_issue_3127_verify_preregistration.py`).

**1. Timeout (PR #3223 open finding 1, fixed in `824bbf8f`).** Confirmed with a real (not mocked) hung subprocess: put a fake `git` script (`#!/bin/sh\nsleep 60`) first on `PATH` and called `vp._run_git(Path("."), "log", ...)` directly.
```
elapsed: 10.011371374130249
returncode: 124
stderr: timed out after 10s waiting for `git log --diff-filter=A --format=%H --reverse -- docs/issue-3127/decisions/pre-registration.md`
```
Same for `_default_gh_runner` with a fake hung `gh`:
```
elapsed: 30.022595405578613
returncode: 124
stderr: timed out after 30s waiting for `gh pr view 1 --json mergeCommit`
```
Both fail closed at the stated limit rather than blocking, and the failure names the command and reads as a timeout (`exit 124`, `timed out after Ns waiting for ...`), not a clean negative. End-to-end with the real hung `git` on `PATH`, calling `vp.verify(Path("."))` directly (not the module's own mocked `SubprocessTimeoutTest`, which patches `subprocess.run` rather than exercising a real process):
```
elapsed: 10.011459350585938
ok: False
msg: could not determine commit history -- `git log ...` failed (exit 124): timed out after 10s waiting for `git log ...` -- neither a failed git command nor output that doesn't look like a commit sha is evidence the path has no commits yet, so this cannot be read as a pass (fail closed)
```
Reports the failure as a `GitCommandError` flowing through the same fail-closed branch round 3 verified, not as a silent pass — matches the file's own `TimeoutExpired` → synthetic non-zero `CompletedProcess` conversion at `scripts/issue-3127/verify_preregistration.py:115-136` (cited from the `824bbf8f` worktree; this file is untracked / out-of-scope on this session's own branch).

Attacked the values themselves: derived: `time git log --diff-filter=A --format=%H --reverse -- docs/issue-3127/decisions/pre-registration.md` on this repo's real history (`git rev-list --count HEAD` = 4000 commits, in the `824bbf8f` worktree) — result: `real 0m0.070s`, repeated 3x with the same result (`0.070s`, `0.070s`, `0.071s`). `GIT_TIMEOUT=10` is ~140x this repo's real measured time, not merely asserted headroom — the code's own comment ("10s is generous headroom ... not a tight margin") is confirmed by measurement, not just reasoning. `GH_TIMEOUT=30` is not independently measured against a real slow-network condition in this session (no safe way to induce one); it is justified by citing this repo's other `gh` call-site precedent (10-30s range), which the round-4 fix record itself cites (`gates/gh_budget.py:37`, `harness/driver.py:165`, `gates/probe_cwd_shapes.py:66`). What happens to a legitimate slow call that exceeds either timeout: it is reported as a failure (`ok=False`), the same as a real failure — a false negative, not a false positive. That is the safe direction for a check whose job is refusing an unproven ordering claim; an over-eager timeout costs a spurious re-run, not a bypass.

**2. SHA shape check (PR #3223 open finding 2, fixed in `824bbf8f`).** Fed `_first_commit_for_path` nine constructed `git log` outputs via a monkeypatched `_run_git` returning `returncode=0` with each stdout:
```
short_sha ('abc1234'): REJECTED (GitOutputError)
40char_nonhex ('gggg...' x40): REJECTED (GitOutputError)
trailing_whitespace ('aaa...a' + '   '): REJECTED (GitOutputError)
trailing_whitespace_tab ('aaa...a' + '\t'): REJECTED (GitOutputError)
sha_plus_text ('aaa...a (some note)'): REJECTED (GitOutputError)
empty_line_then_valid ('\n' + 'bbb...b'): ACCEPTED -> 'bbb...b' (leading blank line correctly skipped, first non-blank line used)
uppercase_hex_40 ('AAA...A' x40): REJECTED (GitOutputError)
valid_lowercase_hex_40 ('ccc...c' x40): ACCEPTED -> 'ccc...c'
cr_lf_valid ('ddd...d' + '\r\n'): ACCEPTED -> 'ddd...d' (str.splitlines() strips \r\n before the regex sees it, so no false rejection)
```
Every malformed shape either fails closed (`GitOutputError`) or is correctly accepted; none is silently taken as a valid commit. Which of these git can actually produce: `git log --format=%H` only ever emits a full 40-character lowercase-hex sha per matching commit, one per line, with nothing else on the line — none of the six rejected shapes (short sha, non-hex, trailing whitespace/tab, trailing text, uppercase) is real output `git log --format=%H` can produce; the check is preventive tightening against a corrupted/spoofed/unexpected exit-0 payload, not a strictness gap against real git output. The two accepted shapes (plain 40-lowercase-hex, and the same with a trailing `\r\n` a Windows-checkout `core.autocrlf` setting could introduce) are exactly the real output shapes. Not too strict for real output, not too loose for corrupted output.

**3. Merge claim (`824bbf8f` = merge of `86cad057` with `origin/main`).** Independently re-derived rather than accepting round 4's stated reasoning. First check (a red herring worth naming): `git diff 86cad057:scripts/issue-3127/verify_preregistration.py origin/main:scripts/issue-3127/verify_preregistration.py` shows a large diff -- but that's comparing the branch's fully-redesigned file against main's pre-redesign version (main only ever received PR #3131's original file, before any of rounds 1-4's fixes), not evidence of a conflicting change. The actual claim requires two other checks (all run in the `824bbf8f` worktree):
```
git log --oneline origin/main -- scripts/issue-3127/verify_preregistration.py
  -> fb0bb0d3 issue-3127: pre-register + build consumer-path harness ... (#3131)   [only commit]
git merge-base --is-ancestor fb0bb0d3 86cad057 && echo "already ancestor"
  -> already ancestor of pre-merge branch tip
git diff 86cad057 824bbf8f -- scripts/issue-3127/verify_preregistration.py
  -> (empty, exit 0)
```
`origin/main` has exactly one commit touching this file (`fb0bb0d3`), and that commit was already an ancestor of the branch's pre-merge tip (`86cad057`) before this round's merge ran -- main introduced zero *new* commits to the file since the branch's fork point, and the file is byte-identical immediately before and after the merge commit. Round 4's claim holds under independent re-derivation, not just its own stated reasoning.

Test suite: derived: `python3 -m pytest tests/ -q` on `824bbf8f` (in the worktree) — result: `535 passed, 2 warnings in 21.63s`, matching round 4's own claimed count exactly. The 2 warnings are the same pre-existing `SkillCandidatesPinnedFixtureDivergenceTest` notice round 4's record already caveated, unrelated to this file. Spot-checked the specific test round 3 recorded as failing, in `tests/test_spawn_gate_wiring.py` (path confirmed tracked via `git ls-files | grep test_spawn_gate_wiring.py`), class `HooksJsonWiringIsAdditive`, method `test_pre_existing_post_tool_use_commands_are_all_still_present` — derived: `python3 -m pytest tests/ -q -k test_pre_existing_post_tool_use_commands_are_all_still_present` on `824bbf8f` — result:
```
1 passed in 0.84s
```
confirming it is the merge (not incidental) that resolved it.

**4. Soundness.** No route to defeat the ordering property was found across the timeout attacks, the nine sha-shape attacks, or a search for gaps the merge could have introduced. The timeout paths can only produce false negatives (fail closed on a legitimate slow call), never a false positive -- an attacker cannot use a timeout to make a bad ordering read as good. The sha-shape check closes an exit-0-with-corrupted-output gap that round 3's own forward-trace had already found no live exploit for; round 4 tightened it preventively, consistent with round 3's own conclusion. Round 4 did not touch `_resolve_via_pr_history`, the merge-commit bind, or the failure-vs-empty distinction, and this round's own re-derivation of the merge (item 3 above) confirms `origin/main` carried no commit that could have altered any of that logic. canonical: `docs/issue-3127/decisions/pre-registration.md` (in the `824bbf8f` worktree), section "Limitation of the mechanical ordering check": the script proves *construction* order, not *decision* order -- a determined actor who commits in the right order on purpose after already knowing the answer defeats no mechanism here, because there is none aimed at that threat. That limitation still accurately bounds what the check proves: round 4 only closed *observability* gaps (a hang, a corrupted-but-clean-exit payload), which is orthogonal to the construction-vs-decision-order boundary the limitation describes. That boundary is unchanged and still accurate.

## Why

Per the task, each attack targeted exactly the two claims round 4 introduced (timeout, sha-shape) plus independent re-derivation of the one claim round 4 asserted without full derivation in its own record (the merge not touching this file) — round 3's already-Present findings (merge-commit bind, `--follow` removal, failure-vs-empty distinction) were read as settled and not re-attacked, per the task's explicit instruction.

Used live subprocesses (a real hung `git`/`gh` script on `PATH`) for the timeout attacks rather than only trusting the module's own `SubprocessTimeoutTest`, which mocks `subprocess.run` directly — a mock proves the exception-handling code path exists, not that `timeout=` is actually being honored by a real process; the live version is strictly stronger evidence.

## What did not work

None.

## Upstream basis

`docs/issue-3127/reports/implementation-blueprint+silent-failure-audit-b4641815.md` (round-4 fix record, commit `125cef42`) and `docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md` (round-3 verification record, commit `6d1a233b`, PR #3223) — both read first per the task instructions; their Present grades on the merge-commit bind, `--follow`/rename handling, and failure-vs-empty distinction are relied on, not re-derived.

## Open findings

Two minor, non-blocking observations, neither a defect in the shipped code:

1. `GH_TIMEOUT=30`'s justification (this repo's other `gh` call-site precedent) is not independently verified against a real slow-network condition in this session -- no safe way to induce one. Not a blocker: a legitimate slow call that exceeds it fails closed (a false negative costing a re-run), never a false positive, so the residual risk is availability, not correctness. Resolution path: none needed unless a future round observes a real false-negative timeout in practice; if so, raise `GH_TIMEOUT` rather than remove it.
2. canonical: `scripts/issue-3127/verify_preregistration.py` test coverage in the `824bbf8f` worktree, class `FirstCommitForPathTest`, method `test_raises_git_output_error_on_malformed_shape_at_exit_0` — covers only one malformed-sha shape (a plain non-hex string). This round's own attack (item 2 above) covered eight more (short sha, trailing whitespace/tab, trailing text, uppercase hex, leading blank line, valid+CRLF) and found the actual code correct on all of them -- the code is not under-tested in behavior, only in the checked-in regression suite's shape coverage. Resolution path: whoever next touches this test file could add the remaining shapes as parametrized cases; not blocking because this round already exercised and confirmed them directly against the shipped code.

## Next steps

None queued by this record. canonical: `gh pr view 3169 --json state -q .state` — result: `OPEN` (not merged, not edited, per the task's instruction). This is likely the last verification round on this check per the task framing; no further attack vector against `verify_preregistration.py`'s current logic was found.

## Acceptance checks and full test suite

acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run` — checked on PR #3169's branch at `824bbf8f` (worktree) — result: exit=0 (dry-run plan printed, nothing executed)
acceptance: `test -f docs/issue-3127/_assets/consumer-path-results.json` — result: exit=0
acceptance: `python3 scripts/issue-3127/verify_preregistration.py` — result:
```
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
```
exit=0

derived: `python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q` on `824bbf8f` (worktree) — result: `23 passed in 0.90s`, matching round 4's claimed count.
derived: `python3 -m pytest tests/ -q` on `824bbf8f` (worktree) — result: `535 passed, 2 warnings in 21.63s`, matching round 4's claimed count exactly; the branch-staleness failure round 3 recorded is gone.

## Grading (Present / Surface / Absent / Incorrect / Unverifiable)

- **Timeout on every subprocess call**: Present. derived: live hung-subprocess attacks above (item 1) — confirmed both `_run_git` and `_default_gh_runner` fail closed at their stated limits (10s/30s), report a named-command timeout distinguishable from a real git/gh failure (`exit 124`), and flow through the same fail-closed branches round 3 already verified end-to-end (`verify()` returns `ok=False`). Values: `GIT_TIMEOUT=10` independently confirmed generous (~140x this repo's measured real `git log` time of 0.070s); `GH_TIMEOUT=30` is precedent-justified, not independently measured this session, but the failure direction on an over-tight value is safe (false negative, not false positive) — see Open findings 1.
- **SHA shape check**: Present. derived: nine-case constructed-input attack above (item 2) — all classified correctly; none of the rejected shapes is real `git log --format=%H` output, so the check is neither too strict for real output nor too loose for corrupted output.
- **Merge claim**: Present. derived: `git log --oneline origin/main -- <file>`, `git merge-base --is-ancestor`, and `git diff` across the merge commit above (item 3) — independently re-derived (not merely accepted); confirms `origin/main` carried zero new commits to `verify_preregistration.py` since the branch's fork point and the file is byte-identical before/after the merge. Full test suite (535 passed) and the specific previously-failing staleness test (1 passed) both confirm the merge resolved round 3's residual failure.
- **Soundness (this round is likely the last)**: Present. Per item 4 above: no route to defeat the ordering property was found across all attacks in this round or round 3's seven; the recorded construction-order-vs-decision-order limitation in `docs/issue-3127/decisions/pre-registration.md` still accurately bounds what the check proves, unaffected by round 4's purely-observability-focused changes.

skill-verdict: adversarial-review — applied: invoked; ran as the structurally independent evaluator session (this session did not build round 4) attacking round 4's two new mechanisms (timeout, sha-shape) plus independently re-deriving the merge claim rather than accepting PR #3169's own stated reasoning, per Steps 1-4.
skill-verdict: silent-failure-audit — applied: invoked; classified both new `except subprocess.TimeoutExpired` blocks (`_run_git`, `_default_gh_runner`) as Handled, not Silently Absorbed — traced forward with a real hung subprocess (not the module's own mock) to confirm the synthetic non-zero `CompletedProcess` each produces reaches the same already-verified fail-closed branches (`GitCommandError` → `verify()`'s `except`, or the generic `None`-on-nonzero pattern in the `gh`-runner helpers) that round 3's own sweep confirmed for every other failure mode in this file — see item 1 above.
skill-verdict: experiment-trust — not-applicable: this round audits a mechanical ordering-verification script (`verify_preregistration.py`), not an A/B experiment result or variant comparison; no SRM/A-A/pre-registration-interpretation question is in scope here (the pre-registration this check enforces was already audited by earlier rounds under this same skill).
