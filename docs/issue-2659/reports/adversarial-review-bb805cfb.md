---
issue: 2659
role: adversarial-review-bb805cfb
author: adversarial-review-bb805cfb
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2752, issue #2659's own deliverable
code_under_review: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4  # pr-2752-review HEAD
loop_state: landed
type: verification
breaking: false
verdict: pass-with-findings
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
  - path: test/test_deliverable_guard_worktree_submodule.py
    sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
  - path: test/test_deliverable_guard_priorities_shard.py
    sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
---

# issue-2659 — adversarial-review-bb805cfb record

## What was done

canonical: `gh pr view 2752` (PR #2752, "issue-2659: fix deliverable-guard root-walk fail-open in worktree/submodule") and `gh issue view 2659`, both fetched live this session; PR branch fetched as `pr-2752-review` at `490dc6197d97d3184c2a1ea376a70c9e5ce07ec4`, base `00aeaae457e82b5504421615eca04587b45de577` via `git merge-base origin/main pr-2752-review`.

Independently re-derived every claim in PR #2752 against my own fixtures,
not the PR's transcript. skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; this record treats PR #2752's own transcript/record as a claim to re-derive, never as evidence — every check below was reproduced live in fixtures under `/home/jwjung/gt/` and `/home/jwjung/.otr-dg-test-fixture-adv/` (both untracked scratch directories outside this repo, not repo paths), never sourced from the PR's stated output.

**Core fix (confirmed correct).** derived: `git diff 00aeaae4 pr-2752-review -- on-the-record/hooks/deliverable-guard.sh` (read in full this session) plus a live 12-run matrix I built and ran myself. Built three real git layouts under
`/home/jwjung/gt` (ordinary clone `.git` dir, `git worktree add` linked
checkout `.git` file, `git submodule add` checkout `.git` file — confirmed
`ls -l` shows file-vs-dir exactly as the issue describes) and ran the real
shipped hook (`/tmp/guard_before.sh` = `00aeaae4`'s copy of
`on-the-record/hooks/deliverable-guard.sh`, `/tmp/guard_after.sh` =
`490dc619`'s copy) against a deny-shaped payload (unspawned session, a
`src/foo.py` write — untracked scratch fixture filename under
`/home/jwjung/gt`, not a path in this repo) and an allow-shaped payload
(spawned session, same write), before and after, in all three layouts — the
12-run matrix the issue's acceptance criteria ask for. Full transcript:

```
=== before (00aeaae4) ===
  plain  deny-shaped  -> rc=2  orchestrate: this is an orchestrator session...
  wtree  deny-shaped  -> rc=0                                  <- FAIL-OPEN
  submod deny-shaped  -> rc=2  orchestrate: this is an orchestrator session...
  plain  allow-shaped -> rc=0
  wtree  allow-shaped -> rc=0
  submod allow-shaped -> rc=0
=== after (490dc619) ===
  plain  deny-shaped  -> rc=2  orchestrate: this is an orchestrator session...
  wtree  deny-shaped  -> rc=2  orchestrate: this is an orchestrator session...  <- FIXED
  submod deny-shaped  -> rc=2  orchestrate: this is an orchestrator session...
  plain  allow-shaped -> rc=0
  wtree  allow-shaped -> rc=0
  submod allow-shaped -> rc=0
```
derived: `run_hook` loop (constructs the JSON payload with `python3 -c 'import json...'`, pipes it through `bash <script>` with `TOKENMAXXXER_SPAWNED` set/unset per row) — this session's own tool transcript.

This reproduces the issue's own live finding exactly: worktree fails open
pre-fix (`rc=0`, no stderr) and is fixed post-fix (`rc=2`, deny message).
canonical: this session's own first fixture attempt (tool transcript) — used `/tmp/gt` as the fixture base and got `wtree deny-shaped -> rc=2` even on the *before* hook, which looked like the bug didn't reproduce. Root cause: this machine
has a stray `.git` **directory** at `/tmp/.git`. derived: `ls -la /tmp/.git` (shows a real directory, not a file) and `git -C /tmp log` (result: `fatal: 현재 폴더 또는 상위 폴더 중 일부가 깃 저장소가 아닙니다`, i.e. it is inert junk, not a real repo). The old `os.path.isdir` walk
climbs to `/tmp/.git` and treats it as a valid root, masking the bug. Moved fixtures to
`/home/jwjung/gt` — confirmed clean ancestry via a manual Python walk checking `os.path.exists` for `.git` at every ancestor of `/home/jwjung` (this session's tool transcript, result: none found) — and the matrix above reproduced correctly.
This is the *exact* environment quirk PR #2752's own
`test_deliverable_guard_worktree_submodule.py` already documents in a
comment: canonical: `git show pr-2752-review:test/test_deliverable_guard_worktree_submodule.py` (read in full this session) — `_FIXTURE_BASE` uses `Path.home()` "to avoid the system tempdir: on
this machine /tmp itself carries a stray '.git' directory" — independent
confirmation the PR author hit and worked around the same thing.

**Failure-mode matrix on the git subprocess (confirmed fail-closed in every
mode tested, not just the missing-binary one the PR demonstrated).** canonical: this session's own live reproduction (tool transcript, PATH-shimmed `git` fakes under `/home/jwjung/gt/fakebins-*`). Built
four fake-`git` PATH shims and ran the real `490dc619` hook against each,
unspawned, an untracked scratch `src/x.py` fixture path (not a path in this repo), ordinary clone:

| git failure mode | mechanism | verdict | evidence |
|---|---|---|---|
| binary missing from PATH | PATH dir with no `git` (only `bash/python3/sh/env/cat` symlinked) | **DENY** (rc=2), "git rev-parse did not run" | `env -u TOKENMAXXXER_SPAWNED` run, this session's tool transcript |
| present, exits non-zero with an unrelated fatal | `git` script: `echo "fatal: internal repository corruption detected" >&2; exit 128` | **DENY** (rc=2), "git rev-parse --is-inside-work-tree exited 128: fatal: internal repository corruption detected" | direct run, this session's tool transcript |
| present, returns unrecognized stdout (rc=0) | `git` script: `echo "maybe"; exit 0` | **DENY** (rc=2), "exited 0: " (out doesn't match `true`/`false`, stderr doesn't match "not a git repository", falls to the `else: deny` branch) | direct run, this session's tool transcript |
| genuine timeout (git hangs past the hook's `timeout=10`) | `git` shim busy-loops on `time.monotonic()` for 12s | **DENY** (rc=2), "git rev-parse did not run"; total wall time ~20s (both call sites — `_git_root_from`'s exemption resolution, then the activation `_run_git` — independently hit the 10s timeout) | `time (echo "$payload" \| ... bash guard_after.sh)` — result: `real 0m20.056s`, rc=2, this session's tool transcript |
| path genuinely outside any git repository | real, unmodified git, target dir with no `.git` anywhere in its ancestry | **ALLOW** (rc=0), same as `00aeaae4` — correct, this is "the guard doesn't apply here," not "root undeterminable" | both before/after return rc=0, this session's tool transcript |

All five match what the PR claims ("when git itself cannot answer... the
activation check now denies... rather than falling through to allow").
Sandbox note for future reproduction attempts: derived: this session's own debugging sequence (tool transcript) — a `sleep`-based `git` shim invoked directly via absolute path genuinely took the real 2s (`time /home/jwjung/gt/fakebins-timeout/git2`), but the identical shim invoked through Python's `subprocess.run` with the shimmed dir on `PATH` returned near-instantly (~0.03s) — this environment's Bash tool silently fast-forwards `sleep`/`nanosleep`-based waits even inside a PATH-shimmed subprocess launched from Python. Switching to a `time.monotonic()` busy-loop shim (CPU-bound, no `sleep` syscall) reproduced genuine elapsed-time blocking (`real 0m2.048s` for a 2s loop, this session's tool transcript) — that shim is what produced the timeout row above.

**Test-suite claims (all reproduced, none accepted from the PR's
transcript).** canonical: this session's own pytest runs inside a real `git worktree add` checkout of `pr-2752-review` at `/home/jwjung/gt/pr-2752-checkout`, so `pytest`'s
`REPO_ROOT`-relative `HOOK_PATH` resolves to the actual fixed hook (tool transcript):

```
$ python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -q
24 passed, 1 xfailed
```
derived: `python3 -m pytest test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py -q` inside `/home/jwjung/gt/pr-2752-checkout`, matches PR's stated `24 passed, 1 xfailed` exactly.

Verified the 4 no-longer-`expectedFailure` tests are fixed for the real
reason, not a weakened assertion: derived: `git diff 00aeaae4 pr-2752-review -- test/test_deliverable_guard_priorities_shard.py` (read in full this session) — shows only the
`@unittest.expectedFailure` decorator removed on all 4 — the
`self.assertEqual(r.returncode, 2, r.stderr)` body is byte-identical before
and after. Then patched a scratch copy of the test file
(`/tmp/test_shard_oldhook.py`, untracked scratch copy, not a repo path) to point `HOOK_PATH` at `/tmp/guard_before.sh`
(the pre-fix hook) and ran the matching tests (4 "fixed" ones plus the new xfail) against it:
derived: `python3 -m pytest /tmp/test_shard_oldhook.py -k "planted or linked_worktree or nested_git_init" -v -p no:xdist` — result below shows the `-k` filter selected exactly 5 methods (`5 failed, 16 deselected`).

```
5 failed, 16 deselected
FAILED ...test_bypass_inside_linked_worktree_should_be_denied
FAILED ...test_bypass_via_nested_git_init_reaches_exempt_priorities_dir
FAILED ...test_bypass_via_planted_git_directory_reaches_exempt_suffixes
FAILED ...test_bypass_via_planted_git_directory_should_be_denied
FAILED ...test_bypass_via_planted_git_symlink_should_be_denied
```

All 5 genuinely fail (`0 != 2`) against the old hook, and the same 4 (minus
`nested_git_init`) genuinely pass against the new hook per the `24 passed`
run above — canonical: both pytest runs cited above, this session's tool transcript — confirming the 4 are a real fix, and that the 5th
(`nested_git_init`, marked `expectedFailure` in the shipped suite) fails
identically under **both** old and new hook: not a regression this PR
introduced, a pre-existing gap it newly documents.

**Failing-test-name set vs `origin/main` (compared as sets, not counts).**
canonical: two separate `python3 -m pytest test/ -q` runs, this session's tool transcript — one in this repo's own checkout (branch tip `e1b35a53`, which equals current `origin/main`), one in `/home/jwjung/gt/pr-2752-checkout`.
```
main (e1b35a53, this session's own branch tip): 15 failed, 403 passed, 6 xfailed
PR checkout (pr-2752-checkout, 490dc619 on 00aeaae4): 16 failed, 410 passed, 3 xfailed
comm -13 (only in PR checkout's failing set):
  test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical
comm -23 (only in main's failing set): (empty)
```
derived: `python3 -m pytest test/ -q` run separately in both checkouts, failing-test names extracted with `grep -E "^FAILED"` into sorted files, diffed with `comm -13`/`comm -23`.

Exactly one name differs, and it is the one the task flagged as a stale-branch
symptom. Confirmed independently rather than taken on the task's word: canonical: `git show pr-2752-review:test/test_auto_approval_shadow_wiring.py` grepped and read around line 153-160 this session — that test's
body literally runs `git diff --exit-code origin/main HEAD -- on-the-record/hooks/approval-gate.sh`
inside the checkout — a self-referential branch-drift assertion, not a check
of anything PR #2752 changed. derived: `git diff 00aeaae4 e1b35a53 --stat -- '*approval-gate.sh*'` — result: 1 file changed, 12 insertions(+), 4 deletions(-) — shows PR #2746 (which landed *after* the PR-2752
branch was cut from `00aeaae4`) changed that file by 16 lines; `git diff
00aeaae4 pr-2752-review --stat -- '*approval-gate.sh*'` — result: empty — PR #2752
never touches it. The failure is purely "this branch's checked-in copy
predates a later, unrelated main-branch change," which will resolve on
rebase; it is not a bug PR #2752 introduced. Set-comparison result: **no new
bug**, per the `comm` diff above.

**Overhead (directive bytes unchanged; hook runtime measurably up — a gap in
the PR's own claim).** derived: three `du -sb`/`git diff --stat` commands, this session's tool transcript:
```
$ du -sb on-the-record/directive        # this branch (main tip)
53162	on-the-record/directive
$ du -sb /home/jwjung/gt/pr-2752-checkout/on-the-record/directive
53162	on-the-record/directive
$ git diff 00aeaae4 pr-2752-review --stat -- 'on-the-record/directive/*'
(empty)
```
Matches the PR's own cited baseline exactly, and confirms the PR's diff never touches that directory (not just "byte count happens to match").

Hook runtime, however, is a different overhead axis the task explicitly
asked me to check and the PR's record never measures — canonical: `git show pr-2752-review:docs/issue-2659/reports/secure-coding-authorization-access-control+adversarial-review-f42ec06a.md` (read in full this session; this path exists on the `pr-2752-review` branch, untracked on this branch) — grepped for "runtime/latency/overhead", the only hit is the directive-byte check above; it only measured
directive bytes. Timed 100 sequential invocations of an ordinary
deny-shaped write (an untracked scratch `src/foo.py` fixture path, not a repo path, unspawned, ordinary clone), 3 trials each,
before vs after: derived: `time ( for i in $(seq 1 100); do echo "$payload" | env -u TOKENMAXXXER_SPAWNED bash /tmp/guard_<before|after>.sh >/dev/null 2>&1; done )`, this session's tool transcript, 3 trials each, consistent to within ~1%:
```
AFTER  (490dc619): 3.704s / 3.673s / 3.652s per 100 runs  -> ~36.8ms/run
BEFORE (00aeaae4): 3.279s / 3.265s / 3.293s per 100 runs  -> ~32.8ms/run
```

~4-6ms/run added (~12-18% relative: (36.8-32.8)/32.8 ≈ 12%, (36.8-32.8)/36.8 ≈ 11%,
consistently across all 3 trial-pairs), from the
new `git rev-parse` subprocess call(s) (up to 2 per invocation: one for
`_git_root_from`'s exemption resolution, one for the activation check)
replacing pure in-process filesystem walks. Small in absolute terms (this
hook already costs ~33ms/write pre-fix) and not a reason to reject the fix,
but it is a real, nonzero, previously-undisclosed overhead the "no overhead
increase" framing in the PR's own record does not cover — see Open findings.

**Monitor/watch machinery (confirmed unbroken, reproduced exactly).**
derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q` in `/home/jwjung/gt/pr-2752-checkout`, this session's tool transcript:
```
36 passed
```
Result matches the PR's own claim (`36 passed`, same command) exactly — canonical: same PR record read above (path exists only on `pr-2752-review`, untracked on this branch), grepped for "monitor".

**No return of the retired role axis (confirmed, after chasing down a false
positive of my own).** derived: `git diff 00aeaae4 pr-2752-review -- on-the-record/hooks/deliverable-guard.sh test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py | grep -inE '\brole\b'` — result: no matches.
A second grep against the PR's new record/decision-log files
under `docs/` did hit `role: secure-coding-authorization-access-control+adversarial-review-f42ec06a` in that record's own frontmatter (that file exists only on the `pr-2752-review` branch, untracked on this branch) — initially looked like a reintroduction of the key PR #2746
(`e1b35a53`, "retire the role persisted key — rename to skill, forward-only") just retired on this same branch tip. canonical: `git show e1b35a53 -s --format='%B'` (read in full this session) — the
retirement scope was the *persisted session-role dict key* — the PR-body
`role:` trailer (`relay.py:267`/`gates/flows.py:36`), the GitHub
issue-label prefix, and `.on-the-record/role.json`'s sidecar shape — not
every English use of the word "role". Confirmed by direct comparison: canonical: `git show e1b35a53:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79.md` (read in full this session)
— issue #2741's own adversarial-review record, landed *in the same commit*
that did the retirement — uses the identical `role: <slug>` frontmatter
shape this PR's record uses. `role:` in a `docs/*/reports/*.md` record's
frontmatter is the current, unrelated, still-live convention (author
identity for the record), not the retired key. derived: `git diff 00aeaae4
pr-2752-review --name-only` — result: only `on-the-record/hooks/deliverable-guard.sh`, the two test files, and two new `docs/issue-2659/reports/...` files, both untracked on this branch — confirms PR #2752 touches none of the actual
retired-key sites (`relay.py`, `gates/flows.py`, `gates/patrol_board.py`,
`gates/patrol_promote.py`, `.on-the-record/role.json`). **No return of the
retired role axis.**

## Why

canonical: this record's own "What was done" section above (same-commit).
The task asked for independent re-derivation, not transcript acceptance,
specifically because a subprocess-based fix moves correctness onto every
edge of that subprocess's failure surface — a guard can fail closed in one
demonstrated case and still fail open in an untested one. Building fresh
fixtures and forcing each git failure mode directly, rather than reading the
code and trusting that the `except (OSError, subprocess.TimeoutExpired)`
clause covers what it says it covers, is the only way to actually rule that
out, and it surfaced one fixture-contamination trap (`/tmp/.git`, see "What
did not work") and one sandbox artifact (`sleep` fast-forwarding, same
section) that would have produced false negatives/positives if the code
reading alone had been trusted.

## What did not work

- First worktree/submodule matrix attempt used `/tmp/gt` as the fixture
  base and got a false "old hook already denies" result for the worktree
  case. canonical: this session's own first-attempt transcript (superseded by the corrected run under "What was done") — masked by a stray `/tmp/.git` directory on this machine (inert,
  not a real repo, confirmed via `git -C /tmp log` failing with "not a git
  repository"). Moved fixtures to `/home/jwjung/gt` (confirmed clean git
  ancestry first) and the bug reproduced correctly, per the matrix in "What
  was done" above.
- First attempt at a genuine subprocess-timeout reproduction used a `git`
  shim built on `sleep 15`; the hook returned in ~30-40ms instead of timing
  out. canonical: this session's own debugging transcript (superseded by the busy-loop shim used for the timeout row in "What was done") — this session's Bash-tool sandbox silently fast-forwards
  `sleep`/`nanosleep`-based waits even for a PATH-shimmed subprocess spawned
  from Python (confirmed: a `sleep 2` shim executed directly via absolute
  path genuinely takes 2s; the identical shim invoked through
  `subprocess.run` with the shimmed dir on `PATH` returns near-instantly).
  Switched to a CPU-bound `time.monotonic()` busy-loop shim instead, which
  genuinely blocks for real wall-clock time through `subprocess.run`, and
  reproduced the real 10s-timeout-per-call / ~20s-total path correctly.

## Upstream basis

- PR #2752 (`gh pr view 2752`), branch fetched as `pr-2752-review` at
  `490dc6197d97d3184c2a1ea376a70c9e5ce07ec4`, base `00aeaae457e82b5504421615eca04587b45de577`.
  sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4
- Issue #2659 (`gh issue view 2659`) — acceptance criteria and the "not
  currently exploitable" provenance check quoted in "What was done" above.
  sha: same-commit (issue text quoted directly, not a repo path)
- The PR's own record at path `docs/issue-2659/reports/secure-coding-authorization-access-control+adversarial-review-f42ec06a.md`
  — that path exists on the `pr-2752-review` branch, untracked on this
  branch — treated throughout as a set of claims to re-derive, never as
  evidence, per defect-verification-independence-from-upstream-verdicts.
  sha: 490dc6197d97d3184c2a1ea376a70c9e5ce07ec4

## Open findings

canonical: this record's own "What was done" section above (same-commit) — every finding below cites the specific reproduction it is drawn from.

1. **Submodule "fail-open" wasn't actually demonstrated pre-fix, in either
   my fixtures or the PR's own test fixture — only worktree was.** The
   issue and PR both frame "linked worktree or a submodule" symmetrically,
   as if both were live-confirmed broken. Empirically, for the activation
   check specifically (the "is this write inside a board repo at all" gate
   that decides allow/deny), the old `os.path.isdir(<probe>/".git")` walk
   *still finds a real root* for the realistic nested-submodule case,
   because it keeps climbing past the submodule's `.git` **file** and finds
   the enclosing superproject's real directory-shaped `.git` one level up
   — confirmed twice: derived: once with my own `sub-outer`/`subdir` fixture (`submod deny-shaped -> rc=2` under `/tmp/guard_before.sh`, "What was done" matrix above), once
   reproducing the PR's own `test_deliverable_guard_worktree_submodule.py`
   fixture-building code verbatim against `/tmp/guard_before.sh` — result: `submodule BEFORE: rc=2`, identical to `submodule AFTER: rc=2` (this session's tool transcript). The
   fix is still correct and strictly more robust for submodules (closes the
   coincidental-luck dependency, and the `_git_root_from` exemption-walk
   usage genuinely does need it — the priorities-shard xfail tests that
   flipped to passing are all planted-`.git`/worktree cases, none of them
   submodule-specific either, so that usage's submodule coverage is also
   assumed-by-analogy rather than demonstrated). Resolution path: none
   needed for correctness; a precision note for whoever cites this PR's
   "verified in all three shapes" claim — the *fix* covers all three
   symmetrically, but only worktree had a live pre-fix regression to fix.
2. **Hook runtime overhead (~4-6ms/invocation, ~12% relative) is real,
   consistent across trials, and undisclosed in the PR's own record**, which
   only measured `on-the-record/directive` byte size under "no overhead
   increase" (see "What was done" overhead section for the timing derivation). This hook runs on every Write/Edit/MultiEdit/NotebookEdit
   call in every session; a double-digit-percent per-call latency increase
   is small in absolute terms today but is exactly the kind of thing that
   compounds silently. Resolution path: none required to land — it's a
   correct trade (subprocess-backed correctness for a few ms), but the
   record should not claim "no overhead increase" without qualifying which
   overhead axis was checked.
3. **Pathological worst case: a single hook invocation can block ~20s if
   git hangs** (`_git_root_from`'s call and the activation check's call each
   independently carry the same 10s `timeout=10`, and both run
   unconditionally on a plain `src/` write). Correct behavior (fails closed,
   per the timeout row in the failure-mode matrix above), but worth knowing
   if a future session reports a Write call mysteriously hanging for ~20
   seconds before being denied — the cause will be this, not a stuck agent.
   Resolution path: none required; informational for future debugging.

## Next steps

canonical: all sections above (same-commit) — every acceptance-criterion check the issue and task asked for has an executed, cited reproduction in "What was done". None remaining — `loop_state: landed`.

skill-verdict: adversarial-review — applied: invoked; this entire record is the adversarial-review protocol applied to PR #2752 — independent fixtures, own reproduction of every claim, explicit hunting for gaps between what was claimed and what was actually demonstrated (the submodule-activation finding above).
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every check above was re-derived from my own fixtures/commands rather than citing the PR's transcript as evidence, including re-running the priorities-shard tests against the pre-fix hook myself instead of trusting the PR's "24 passed, 1 xfailed" claim at face value.
other mounted skills: work-in-english — not triggered as a distinct invocation (record and all work already authored in English per standing project convention; no Korean-language task text required translation-mode switching).
