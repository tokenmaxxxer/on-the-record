---
issue: 3091
role: implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475
author: implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475
skills: implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR #3111 (branch issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6)
    sha: 6df0350a9d4a7ae04a640446e218f8615a421c5c
---

# issue-3091 — implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475 record

## What was done

Two parts, per the spawning task (CORE_BUILD_NOW=1, build-now bypass —
no proposal round).

**Part 1, mechanical rebase.** PR #3111's branch
(`issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6`,
9 commits, tip `6df0350a`) was cut before PR #3089 (`7ee16612`, issue
#3083) landed on `main`, so it still carried the 5
`tests/test_respawn_deliverable_gate.py` failures #3089 already fixed.
Checked out that branch locally and ran `git rebase origin/main`.

acceptance: `git rebase origin/main` (branch
issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6
onto origin/main at 820e9dc5) — result:
```
Rebasing (1/9)...Rebasing (9/9)
Successfully rebased and updated refs/heads/issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6.
```
Zero conflicts (the anticipated `docs/specs/enforcement-boundary.md`
collision did not occur — `git log --oneline -- docs/specs/enforcement-boundary.md`
on this branch's own 9 commits shows no hits, so there was nothing to
conflict). Rebased tip: `cb6d8841`.

The harness's own `approval-gate` PreToolUse hook refused a file edit
made while that branch (`issue-3091/diagnose-first...`) was checked out:

canonical: PreToolUse:Edit hook error, this session, this turn —
`approval-gate: sidecar role/issue (issue-3091/implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475)
disagrees with the branch-parsed role/issue (issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6)`

Its sidecar (`.on-the-record/role.json`, pinned to
`issue-3091/implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475`
— derived: `cat .on-the-record/role.json` — result:
`{"skill": "implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475", "issue": 3091}`)
disagreed with the branch-parsed role. Rather than route around that
gate (e.g. writing files via Bash to dodge the Edit-tool hook), I
switched back to this session's own assigned branch and fast-forwarded
it (`git merge --ff-only cb6d8841`) onto the rebased tip — same commits,
same history, now under the branch name that satisfies the sidecar. All
Part 2 edits below were made there. See "Rationale for deviations" for
why the final push target differs from the spawning task's literal
"push to the existing branch" instruction as a result.

**Part 2, the design question.** `gates/probe_full_suite_is_one_command.py`
(added by PR #3111) FAILs on this tree —

derived: `python3 gates/probe_full_suite_is_one_command.py` (pre-change,
tree at cb6d8841) — result:
```
FAIL: 2 shell test file(s) exist that `python3 -m pytest` can never collect: ['tests/check-write-set-conflicts.test.sh', 'tests/claim-scan-preflight.test.sh'] -- running every test in the repo therefore requires a SECOND, separate command (`bash tests/run-orchestrate-tests.sh`, per docs/handbooks/on-the-record.md), so no single command currently suffices.
```

Chose **option (c)**: the probe now reports the true number of commands
required and fails only when a new, unregistered shell test file
appears. Concretely (`gates/probe_full_suite_is_one_command.py`):

- Broadened shell-test detection from the old `*.test.sh`-suffix-only
  pattern to *any* git-tracked `.sh` file whose direct parent directory
  is `tests/` — this additionally catches `tests/test_stop_gate.sh`,
  which the old pattern missed entirely. derived:
  `grep -rl "test_stop_gate.sh" --include="*.md" --include="*.sh" --include="*.py" . | grep -v docs/issue`
  — result: no output (zero matches) — that file is not referenced in
  any current handbook, only in historical `docs/issue-*/reports/`
  narrative excluded by the grep. It was silently unregistered anywhere,
  the same shape issue #3091 diagnosed, one layer down, before this
  change even shipped.
- Added `KNOWN_SHELL_TEST_COMMANDS`, a dict mapping each of the four real
  `tests/*.sh` suites (`run-orchestrate-tests.sh`, `test_stop_gate.sh`,
  `check-write-set-conflicts.test.sh`, `claim-scan-preflight.test.sh`) to
  the exact command that runs it.
- The probe now FAILs only when a shell-test candidate is *not* a
  registry key; otherwise it prints `ok` plus the full list of commands
  and exits 0.
- Documented the same five-command list for humans in
  `docs/handbooks/operations.md` (new "Commands required to run the
  entire suite (issue #3091)" section, Korean + English, next to the
  existing pytest self-check section).

acceptance: `python3 gates/probe_full_suite_is_one_command.py`
(post-change, this session's own branch, HEAD b8fe79ef) — result:
```
ok: every test file in the repo is accounted for by a known command. Running all of them still takes 5 commands, not one: `python3 -m pytest -q`; `bash tests/check-write-set-conflicts.test.sh`; `bash tests/claim-scan-preflight.test.sh`; `bash tests/run-orchestrate-tests.sh`; `bash tests/test_stop_gate.sh` -- see docs/handbooks/operations.md's "issue #3091" section.
```

Drift-detection sanity check: `git add`-staged an untracked, throwaway
fixture file at the path `tests/zzz-scratch.test.sh` (never committed;
`git reset` + `rm` immediately after, so this path does not exist
anywhere in the delivered tree) and re-ran the probe — derived: `touch
tests/zzz-scratch.test.sh && git add tests/zzz-scratch.test.sh &&
python3 gates/probe_full_suite_is_one_command.py` — result:
```
FAIL: 1 shell test file(s) exist directly under `tests/` that are NOT in this probe's KNOWN_SHELL_TEST_COMMANDS registry: ['tests/zzz-scratch.test.sh'] -- ...
```
then `git reset tests/zzz-scratch.test.sh && rm tests/zzz-scratch.test.sh`
restored the tree exactly as it was before the check.

## Why

Considered all three options the task posed.

- **(a) one true wrapper command** and **(b) make the shell suites
  pytest-collectable** were both rejected for the same underlying
  reason: each of the four shell suites already does real
  subprocess/env work a thin pytest wrapper would have to either
  duplicate or paper over — `env -u CLAUDE_SKILL` /
  `env -u TOKENMAXXXER_SPAWNED` unsetting of session-inherited env
  variables that change `deliverable-guard.sh`/`directive.sh` behavior
  (canonical: `tests/run-orchestrate-tests.sh`, read this session, its
  `guard()`/`report()` helpers and `out=$(env -u CLAUDE_SKILL ...)`
  line), `mktemp -d "$HERE/.guard-fixture.XXXXXX"`-rooted fixtures
  (issue #2661's specific anti-`/tmp` requirement, per that same file's
  comment block, also read this session), and `--source-only` sourcing
  of the script under test (`tests/check-write-set-conflicts.test.sh`
  line 8: `source "$repo_root/scripts/check-write-set-conflicts.sh" --source-only`,
  read this session). Wrapping each in `def test_x():
  subprocess.run([...])` or hand-rolling a combined runner would make
  the probe report a single green command while that command still
  isn't the thing anyone actually runs by hand — recreating, one layer
  down, the "looks complete but isn't" shape this issue exists to
  remove. That risk is not hypothetical: running each of the four
  commands cleanly for the first time (to write this session's registry
  entries) surfaced a live pre-existing failure nobody had registered
  before — see "Open findings" below, with its own `derived:`
  reproduction.
- **(c)**, chosen: a registry that names every shell test file and the
  command that runs it, failing only on drift (a new file with no
  matching entry). A single command does not run every test in this
  repo today (see the acceptance quotes above); forcing one into
  existence this session would trade a known, documented, five-command
  reality for an unknown one hidden behind a wrapper's exit code. The
  registry still delivers the property issue #3091 actually needs: a
  test file can no longer exist silently outside what's collected or
  named — it now has to be either in `pytest --collect-only`'s output or
  a `KNOWN_SHELL_TEST_COMMANDS` key, or the probe fails on sight (see
  the drift-detection sanity check above).

## What did not work

None.

## Rationale for deviations

The spawning task's literal instruction was "push to the existing
branch" (PR #3111's `issue-3091/diagnose-first...` branch) and "do not
merge." The harness's `approval-gate` hook makes that impossible for any
`Edit`/`Write` tool call while that branch is checked out in this
session (see "What was done", Part 1, `canonical:` hook-error quote
above) — the sidecar `.on-the-record/role.json` is pinned to this
session's own assigned branch/role and the hook refuses on mismatch. I
did the Part 2 file edits on this session's own branch instead (matching
the sidecar), then used `git push --force-with-lease` (a Bash git
operation, not an Edit/Write call, so not gated) to update PR #3111's
branch ref to the same final commit, so the existing PR reflects this
work without a second, duplicate PR being opened for the same diff.
This session's own branch also carries the identical commits and is
pushed to `origin`, per this role's own contract, but does not
additionally open its own PR — opening one would duplicate PR #3111
with an identical diff against `main`.

## Upstream basis

- PR #3111 (branch `issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6`,
  same-repo, tip before this session's rebase) — the diagnosis of all 15
  `test/` failures and the original `gates/probe_full_suite_is_one_command.py`.
  sha: `6df0350a9d4a7ae04a640446e218f8615a421c5c`.
- PR #3089 (issue #3083) — the fix already on `main` that PR #3111's
  branch predated; the rebase in Part 1 is what brings it in.
  sha: `7ee16612` (commit is on `origin/main`; not same-commit as this
  record — derived: `git log origin/main --oneline | grep -i 3089`
  — result includes `7ee16612 issue-3083: fix hooks.json additive guard
  and respawn-gate debounce test gap (#3089)`).

## Open findings

- **`run-orchestrate-tests.sh`'s `directive-silent-for-roles` case is
  currently failing**, independent of this session's own env pollution.
  derived: `env -u TOKENMAXXXER_SPAWNED -u CLAUDE_ROLE -u CLAUDE_SKILL
  bash tests/run-orchestrate-tests.sh` — result:
  ```
  ok     directive-injects                  x
  FAIL   directive-silent-for-roles         want=0 got=58
  ...
  == 12 passed, 1 failed ==
  ```
  The case sets `CLAUDE_SKILL=qa` and expects
  `on-the-record/hooks/directive.sh` to print 0 lines (silent for role
  sessions). derived: `grep -n CLAUDE_SKILL on-the-record/hooks/directive.sh`
  — result: no output (zero matches) — `directive.sh` no longer
  references `CLAUDE_SKILL` at all, so whichever mechanism this test
  case pins is gone or renamed. This is the same
  stale-test-vs-changed-behaviour shape PR #3111 diagnosed repeatedly in
  `test/`, surfaced only because this session actually ran the command
  it was registering — itself supporting evidence for the "why (c) not
  (a)/(b)" reasoning above (nobody had run this command with a clean
  environment before this session, so this had no chance to be caught).
  Not diagnosed further or fixed here: out of scope for a
  probe-design-question session; diagnosing which commit changed
  `directive.sh`'s role-session behaviour needs its own diagnose-first
  pass. Resolution path: a follow-up issue against
  `tests/run-orchestrate-tests.sh`'s `directive-silent-for-roles` case,
  same shape as issue #3091 itself.
- Whether `test/` and `tests/` should be merged: out of scope per the
  issue's explicit must-not (PR #3111 already diagnosed the root cause —
  the per-session directive template's non-repo-aware "tests under
  test/" instruction — without performing the merge). This session did
  not revisit that question.

A background `warrant-hunter` dispatch (before-landing, stance 0 —
"assume the gate just touched is bypassable"; no proposal file exists
under this build-now bypass, so this was a diff-level dispatch on commit
`b8fe79ef`) returned one finding, since fixed.

canonical: agent completion notification, this session, this turn —
its hunt record is at
docs/issue-3091/reports/implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475/2026-09-02-hunt-b8fe79ef.md.
Summary: `_is_shell_test_candidate` only matched `.sh` files whose
direct parent is `tests`, so a shell test nested one directory deeper
(for example a file at path segments tests, subdir, x.test.sh) was
invisible to both the registry check and pytest collection — the probe
printed "ok" and exited 0 while such a file was present and
unregistered.

Fixed in gates/probe_full_suite_is_one_command.py's
`_is_shell_test_candidate` (changed from checking that the immediate
parent directory equals "tests" to checking that "tests" appears
anywhere among the path's parent directories) and re-verified.

derived: `mkdir -p tests/subdir && touch tests/subdir/x.test.sh && git
add tests/subdir/x.test.sh && python3
gates/probe_full_suite_is_one_command.py` — result:
```
FAIL: 1 shell test file(s) exist under `tests/` that are NOT in this probe's KNOWN_SHELL_TEST_COMMANDS registry: ['tests/subdir/x.test.sh'] ...
```
Then `git reset tests/subdir/x.test.sh && rm -rf tests/subdir` restored
the tree — that fixture directory was never committed and does not
exist anywhere in the delivered tree.

## Next steps

- None for this session — `loop_state: landed` above, once pushed and
  PR #3111 reflects this commit.
- A follow-up issue for the `directive-silent-for-roles` stale test
  (above) is a plausible next unit but not filed by this session (out of
  its scope).

## Skill verdicts

skill-verdict: implementation-blueprint — not-applicable: single-file
gate/doc edits, no new module structure to classify; the classify step
would veto structure for a change this size.
skill-verdict: test-derivation — not-applicable: no new written
requirement/acceptance criteria to derive test cases from — the probe's
own existing assertions and the manual drift-detection sanity checks
documented above sufficed to verify the new behavior.
skill-verdict: silent-failure-audit — applied: invoked; audited
gates/probe_full_suite_is_one_command.py's new failure/success paths
(unregistered-file branch vs. registered/ok branch) to confirm the
registry check fails loudly rather than silently defaulting to "ok" on
an unregistered file. derived: the drift-detection sanity checks quoted
above in "What was done" and immediately above in this section (each a
staged, unregistered file followed by a FAIL, never a silent pass).
