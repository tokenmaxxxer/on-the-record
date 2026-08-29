---
issue: 2709
role: test-authoring-isolation-and-fixture-strategy+adversarial-review-5556333f
author: test-authoring-isolation-and-fixture-strategy+adversarial-review-5556333f
skills: test-authoring-isolation-and-fixture-strategy (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: test
breaking: false
verdict: pass — pushd, subshell-cd, and chained-`cd A && cd B` are each now pinned by a real, discriminating test against the shipped hook; all three currently deny (the safe direction), confirmed by construction, not assumed
upstream:
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: e1f390ab6c01018ce805b00114232adfe86ab749
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: same-commit
---

# issue-2709 — test-authoring-isolation-and-fixture-strategy+adversarial-review-5556333f record

## What was done

Added three test methods to the existing
`CrossRepoCwdDisagreementTest` class in
`test/test_upstream_defect_scope_guard_cross_repo_cwd.py` (the same file
#2669/#2706 already used to pin the guard's `cd`-following resolution
and its residual spoofed-origin gap), reusing that class's `setUp`
fixture (`self.repo_a`, `self.repo_b` — real local git checkouts with
configured `origin` remotes, one per test via `tempfile.TemporaryDirectory`):

- `test_pushd_not_followed_still_denied`
- `test_subshell_cd_not_followed_still_denied`
- `test_chained_cd_uses_first_target_not_final_still_denied`

canonical: `sed -n '175,235p' test/test_upstream_defect_scope_guard_cross_repo_cwd.py` (same-commit) — the three methods and their docstrings

Each constructs the shape named in issue #2709's Acceptance
(`pushd <dir> && ...`, `(cd <dir> && ...)`, `cd A && cd B && ...`) and
runs it through the real shipped hook via a real PreToolUse JSON
payload on stdin — same harness shape as the file's pre-existing tests.
No production code changed; `on-the-record/hooks/upstream-defect-scope-guard.sh`
is untouched — checked: `git diff origin/main -- on-the-record/hooks/upstream-defect-scope-guard.sh` — result: empty (no output).

acceptance: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result:
```
10 passed, 2 xfailed in 0.93s
```
(unchanged xfail count — the two pre-existing spoofed-origin/origin-removed pins; all three new tests among the 10 passed.)

## Why

Each shape is denied for the same structural reason: `operative_cwd()`
(`on-the-record/hooks/upstream-defect-scope-guard.sh:184-193`) matches
only a literal, anchored leading `cd <dir> &&`/`cd <dir>;` token, and
only the FIRST such match:
```
def operative_cwd(payload_cwd):
    m = re.match(r'^\s*cd\s+("[^"]+"|\'[^\']+\'|\S+)\s*(?:&&|;)', cmd)
    if not m:
        return payload_cwd, False
```
derived: `sed -n '184,193p' on-the-record/hooks/upstream-defect-scope-guard.sh` (sha e1f390ab6c01018ce805b00114232adfe86ab749)

- `pushd` isn't `cd`, so the regex never matches — origin resolves from
  the payload cwd, not the `pushd` target.
- `(cd <dir> && ...)` starts with `(`, not `cd` — same non-match.
- `cd A && cd B && ...` matches only the first `cd A`, never advancing
  to `cd B`, even though the command's real final directory is B.

Per the issue's `must not`, this drive does not implement following for
any of the three shapes — #2669/#2637's own conclusion recorded in the
guard's own comment block (`on-the-record/hooks/upstream-defect-scope-guard.sh:65-79`,
citing `docs/issue-2637/reports/silent-failure-audit+architecture-interface-contract-shape-149dabd2.md`)
is that widening the follower widens the attack surface the PR #2706
fail-open fix closed. The job here is only to make the boundary
observable.

### Discrimination check (mutant, not committed)

A test that passes before and after a change pins nothing. Built a
throwaway mutant of `operative_cwd()` (`/tmp/otr_mutant_guard.sh`,
never committed to this repo) that (a) also recognizes `pushd`, (b)
strips a leading `(`, and (c) follows the LAST chained `cd` instead of
the first, then ran each new test's exact constructed payload against
combinations of the shipped hook and single-feature variants of that
mutant, each variant applying exactly one of (a)/(b)/(c) with the other
two held at shipped behavior:

derived: `python3 /tmp/otr_probe.py` (control run against the shipped hook, `on-the-record/hooks/upstream-defect-scope-guard.sh` sha e1f390ab6c01018ce805b00114232adfe86ab749) then three re-runs of the same probe pointed at single-feature mutant copies of the hook — result:
```
                  shipped   +pushd-only   +paren-only   +last-cd-only
pushd rc:            2           0             2              2
subshell cd rc:      2           2             0              2
chained cd A&&B rc:  2           2             2              0
```

Each test flips to allow (0) *only* under the mutant matching its own
claimed gap, and stays deny (2) under the other two mutations — each
test is discriminating for the specific shape it names, not a
tautology that would pass regardless of hook behavior.

### Independent adversarial review (adversarial-review skill)

Spawned an independent `general-purpose` subagent (fresh context — no
issue text, no acceptance criteria, no builder rationale; given only
the test file and the hook script) per the skill's two-party
blind-evaluator protocol.

canonical: subagent report, this session's transcript (agentId af4ef4ccbf38b73e9) — the subagent independently ran `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` (result: 10 passed, 2 xfailed) and independently built its own single-feature-mutant discrimination table, reproducing the same result shape as the "Discrimination check" above from its own fresh run.

The subagent confirmed all three tests are real and discriminating, but
found one real gap: each test asserted only `returncode == 2`. The
hook's own `trap` (`on-the-record/hooks/upstream-defect-scope-guard.sh:99`,
`trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`)
remaps ANY unexpected nonzero exit — including an unrelated Python
crash inside `operative_cwd`/`origin_repo` — to exit code 2 as well, so
a future regression that crashed the hook on these inputs would make
these three tests pass for the wrong reason (crashed-and-fail-closed,
not "correctly denied per the documented gap").

Fixed in this same commit by adding a shared assertion helper,
`_assert_denied_for_documented_reason()`
(`test/test_upstream_defect_scope_guard_cross_repo_cwd.py`, same-commit), which
additionally requires the real policy-denial message substring
(`"issue #1131 req#4"`) on stderr and rejects a `Traceback`, called
from all three new tests after the `returncode == 2` assertion.

derived: constructed a throwaway copy of the hook (`/tmp/otr_crash_guard.sh`, not committed) with `raise RuntimeError('boom-unrelated-crash')` injected at the top of `operative_cwd`, then ran the pushd-shape payload against it — result:
```
rc: 2
stderr contains 'issue #1131 req#4': False
stderr contains Traceback: True
```
`_assert_denied_for_documented_reason` would fail against this crash (rc==2 alone would not have caught it) and passes cleanly against the real shipped hook — checked: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q` (post-fix) — result: `10 passed, 2 xfailed in 0.93s`.

## Standing invariants

**1. Role axis must not come back.**
derived: `git grep -wIn "role" -- . ':!docs/'` (this branch, HEAD e1f390ab6c01018ce805b00114232adfe86ab749) — result: `1230`
derived: `git grep -wIn "role" origin/main -- . ':!docs/'` — result: `1230`
Identical count before/after. checked: `git diff origin/main -- .` piped through `grep -iw role` — result: no matches (empty output, `head` made the pipeline's own exit code 0). This change adds zero "role" occurrences. (The 1390 baseline figure named in the drive brief does not match the exact `git grep -w` invocation used here — the load-bearing check is identity before/after this change on the same command, which holds: 1230==1230.)

**2. No new bug — failing-test set as names, not counts.**
acceptance: `python3 -m pytest test/ -q` (this branch) — result: `15 failed, 406 passed, 6 xfailed in 2.83s` (timing varies run to run, see invariant 3)
acceptance: `python3 -m pytest test/ -q` run inside `git worktree add /tmp/otr-clean-0pz8 origin/main` (confirmed via `git log --oneline -1` in that worktree: `00aeaae4 issue-2741: ...` — same commit as this branch's own merge-base, confirmed via `git merge-base HEAD origin/main` returning `00aeaae4` and `git log --oneline origin/main..HEAD` returning empty, i.e. zero commits ahead) — result: `15 failed, 403 passed, 6 xfailed in 3.15s`
The 15 failing test names are byte-identical between the two runs (both lists captured in this session's tool output; compared by eye — same 15 fully-qualified test IDs on both sides, e.g. `test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`, `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo`, etc.) — all pre-existing, unrelated to this change (env/network-dependent: origin-remote fetch failures, BM25 candidate-corpus tests, skill-judge ledger tests). The +3 passed delta (406 vs 403) is exactly the three new tests added here.

**3. No overhead increase.**
Full suite: `3.15s` (origin/main worktree, above) vs. `2.83s`-`3.16s` (this branch, two separate runs in this session) — within normal pytest-xdist run-to-run variance, no material increase.
derived: `time python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q` before this change (`git stash` applied) — result: `7 passed, 2 xfailed in 0.89s`
derived: same command after this change (`git stash pop`) — result: `10 passed, 2 xfailed in 0.92s`, and after the crash-blindness fix — result: `10 passed, 2 xfailed in 0.93s`
Three additional real-subprocess tests (each spins two `git init` + one `bash` hook invocation) cost ~0.03-0.04s total. No production code touched, so no runtime-path overhead anywhere else.

**4. Monitor/watch machinery unaffected.**
checked: `python3 -m pytest test/ -q` output above — `monitors/test_poll_heartbeat.py` is included in the full-suite run and is not in either run's 15-name failing set (passes both before and after). No watch-class check was disabled, skipped, or weakened; `git diff origin/main --stat -- .` (shown under "What was done") shows only the one test file changed — nothing under `monitors/` or `gates/` was touched.

## Skill application

- skill-verdict: test-authoring-isolation-and-fixture-strategy — applied: invoked; the three new tests reuse the existing `CrossRepoCwdDisagreementTest.setUp` fixture (real git checkouts, fresh `tempfile.TemporaryDirectory` per test — Fresh Fixture per rule 1.4, real dependency per rule 5.18 since local git+subprocess is fast and side-effect-free) rather than duplicating setup, consistent with rule 1.1 (reuse a Creation Method once several tests need the same construction — this file already had several tests using it before this change, per `sed -n '95,115p' test/test_upstream_defect_scope_guard_cross_repo_cwd.py`).
- skill-verdict: adversarial-review — applied: invoked; spawned an independent `general-purpose` subagent with only the test file and hook script (no issue text, no acceptance criteria, no builder rationale), per the skill's two-party blind-evaluator protocol. It ran the tests itself, built its own mutant-discrimination table, and surfaced the returncode-only/crash-blindness gap described above, which was then fixed in this same commit (see "Independent adversarial review" above; canonical source: subagent report in this session's transcript, agentId af4ef4ccbf38b73e9).

## Open findings

None outstanding. The adversarial-review finding (rc==2 blind to crash-vs-deny) was fixed in this same commit, not deferred.

## What did not work

None — no reverted approach, no scope-exceeded stop, no dropped shape. All three named shapes (`pushd`, subshell `cd`, chained `cd A && cd B`) were pinned as asked.

## Next steps

None — `loop_state: landed`. This is a self-contained test-pinning change with no follow-on work implied (the issue's own `must not` forecloses implementing the following behavior as part of this).
