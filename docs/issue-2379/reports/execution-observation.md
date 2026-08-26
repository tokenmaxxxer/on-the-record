---
issue: 2379
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2379/reports/implementation.md
    sha: baef6d2dc3eaac385d24522831316129065f2d50
  - path: pipeline.py
    sha: baef6d2dc3eaac385d24522831316129065f2d50
  - path: spawn.py
    sha: baef6d2dc3eaac385d24522831316129065f2d50
  - path: tests/test_spawn_pipeline.py
    sha: baef6d2dc3eaac385d24522831316129065f2d50
subject: PR #2448 (issue-2379/implementation, head baef6d2dc3eaac385d24522831316129065f2d50, base main)
test: issue #2379 Acceptance section — 2 check bullets + 1 gate bullet
result: passed
assertedBy: execution-observation, independently re-run and independently re-fixtured this turn
---

# issue-2379 — execution-observation record

Path convention: every file cited below lives on `issue-2379/implementation`
at sha `baef6d2d` (checked out into an isolated worktree, `git worktree add
/tmp/otr-2379-eo baef6d2d`, removed after use), not on this record's own
branch (`issue-2379/execution-observation`, based on `origin/main` — this
branch carries no code changes, only this record). Scratch verification
scripts under `/tmp/otr-2379-eo-verify/` were authored fresh this turn,
distinct from the PR's own test fixtures, and removed after use.

## What was done

Independently re-derived both `check` bullets and the `gate` bullet of
issue #2379's Acceptance section against PR #2448, rather than citing the
implementation record's own claims.

**Full test-suite re-run, this turn, in the `baef6d2d` worktree:**

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -q` — result:
```
91 passed in 16.09s
```
Matches the record's own claimed 91 passed.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -k "corrupted_merge_base or bounded_diff_from_old_merge_base" -v` — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base PASSED
2 passed in 1.25s
```
Matches the record's own claimed 2 passed.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -m "not slow" -q` (this turn's own check, not cited by the record) — result:
```
72 passed in 1.25s
```
Confirms the two new regression tests are correctly tagged
`@pytest.mark.slow` (a pre-existing convention, 19 uses in this file) and
don't slow down the fast subset.

**Code-path confirmation, read directly (not test-mediated).**

canonical: baef6d2d:pipeline.py:1001-1067
```
def _checkout_named_branch(cwd: str, br: str) -> str:
    ...
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        r = _sp._recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _sp._base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    base = _sp._base(cwd)
    diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        git("remote", "set-head", "origin", "-a")
        git("fetch", "--prune", "-q", "origin")
        base = _sp._base(cwd)
        diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        sys.exit(f"브랜치 {br} 의 merge-base 가 base({base})와 크게 어긋나 ...")
    return br
```
Structurally: `_checkout_named_branch()` has exactly four exit paths into
`r =` (recut-absorbed, origin-tracking checkout, fresh `checkout -b …
base`, and the `checkout -b br` HEAD-fallback when `base` itself can't be
resolved) and the guard block sits after all four, before `return br` —
one choke point covers every branch-cut path, matching the record's "위
세 경로... 전부를 여기 한 곳에서 커버" claim (the record undercounts by
one — there are four branches into `r =`, not three — but the guard
still sits after all of them, so the claim's substance holds).

canonical: baef6d2d:spawn.py:2205,2274
```
def _recut_absorbed_branch(cwd: str, br: str):
    ...
    return git("checkout", br)
```
This is the final line of `_recut_absorbed_branch` (the "has commits
ahead of base, keep as-is" fallback issue #2379's own comment #2 names as
the recurrence vector — PR #2384 hit this exact line reusing PR #2372's
already-corrupted branch). It is unguarded inside `_recut_absorbed_branch`
itself, but its caller, `_checkout_named_branch` (quoted above), runs the
new guard immediately after it returns — so the fix does close that
specific fallback, even though the fallback function itself carries no
new check.

**Independent boundary-value fixtures (own git repos, own file/threshold
choices, distinct from the PR's 320-file two-lineage fixture and its
50-commit old-but-small-diff control) — calling `pipeline._verify_branch_base_sane()`
directly, not through `checkout_issue_branch`, via a scratch script
(`/tmp/otr-2379-eo-verify/boundary_check2.py`, removed after use):**

acceptance: `python3 /tmp/otr-2379-eo-verify/boundary_check2.py` — result:
```
300-own-files-vs-diverged-base(threshold=300) -> None
301-own-files-vs-diverged-base(threshold=300) -> 'merge-base 4df03fb2743d vs br: 301 files changed, 301 lines (한도 300파일/30000라인)'
env-override-max-files-2-vs-3-own-files -> 'merge-base 4df03fb2743d vs br: 3 files changed, 3 lines (한도 2파일/30000라인)'
0-own-files-diverged-base-no-diff -> None
```
This shows the `>` (not `>=`) boundary sits exactly where the code and
the "기본 상한 300파일" description say it does, that
`MUSTER_BRANCH_BASE_MAX_FILES` actually changes behavior at runtime, and
— independently, with a same-root-diverged-base fixture rather than the
PR's own — reconfirms the "old merge-base, small diff, still accepted"
design intent central to this issue's operator-frozen constraint (this
repo's own days-to-weeks approval waits must not false-positive).

**Fail-open edge case, not covered by either of the PR's two tests
(disclosed here as an open finding, not a blocking defect), via a second
scratch script (`/tmp/otr-2379-eo-verify/failopen_check.py`, removed
after use):**

acceptance: `python3 /tmp/otr-2379-eo-verify/failopen_check.py` — result:
```
no-common-ancestor (merge-base fails) -> None
```
An orphan/disjoint-history branch (`git checkout --orphan`, zero shared
commits with `main`, 500 unrelated files) is not caught — `git
merge-base` itself fails, and `_verify_branch_base_sane()` returns `None`
(fail-open) in that case, by explicit design:

canonical: baef6d2d:pipeline.py:958-965 (docstring excerpt)
```
    이상 없으면 None, 이상하면 사람이 읽을 진단 문자열(merge-base sha +
    파일/라인 수)을 반환한다 — merge-base 자체를 못 구하면(얕은 clone 등)
    검사 불가로 보고 기존과 동일하게 통과시킨다(fail-open, 계산 불가와
    이상 없음을 구분 못 하는 신호를 만들지 않기 위해)."""
```

**Diff-scope confirmation:**

acceptance: `git diff origin/main...HEAD --stat` (from the `baef6d2d`
worktree) — result:
```
pipeline.py                               |  93 +++++++++
spawn.py                                  |   1 +
tests/test_spawn_pipeline.py              |  97 +++++++++
docs/issue-2379/reports/implementation.md | 332 ++++++++++++++++++++++++++++++
4 files changed, 523 insertions(+)
```
Matches the PR's own file list, no unrelated changes.

## Why

derived: the full-suite pytest run, the targeted `-k` pytest run, and
both scratch-script fixture runs (boundary-value and fail-open), all
quoted in full under "What was done" above — every claim in this section
draws only on those already-cited transcripts and file:line reads, not
on new evidence.

The implementation record already asserts both `check` bullets and the
`gate` bullet are satisfied. Re-derived each independently this turn
rather than trusting the record's transcripts, using the full-suite run,
the targeted `-k` run, and both scratch-script fixtures quoted above.

Read the actual choke-point code directly (`pipeline.py:1001-1067`,
`spawn.py:2205-2274`, quoted above under "What was done") rather than
trusting only the record's own quoted excerpts, to check the "one choke
point covers every branch-cut path" claim structurally — the four-vs-
three exit-path discrepancy noted above was only visible by reading the
full function, not from the record's own three-path framing.

Authored fresh boundary-value and fail-open fixtures (both scratch
scripts quoted above, this turn) that call the guard function directly
with values and repo shapes the PR's own two named tests never exercise
(exact-threshold boundary, env-var override, orphan history), instead of
stopping after re-running just those two named tests: their fixed inputs
(321-vs-300 files, and a 50-commit-old 1-file branch) would not have
surfaced either the exact `>`-boundary check or the fail-open gap this
turn's own fixtures turned up (both quoted above under "What was done").

## Upstream basis

- `baef6d2d:docs/issue-2379/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `baef6d2d:pipeline.py`, `baef6d2d:spawn.py`,
  `baef6d2d:tests/test_spawn_pipeline.py` — the actual code and test
  changes, read and imported directly this turn via the
  `/tmp/otr-2379-eo` worktree.
- issue #2379's live body and comments (`gh issue view 2379`, fetched
  this turn) — the real Acceptance text and the operator-frozen
  constraint comment this record checks the delivery against.
- this branch's own unmodified `pipeline.py`/`spawn.py` (`origin/main`,
  no diff on this branch) — implicit "before" state for the diff-scope
  confirmation above.

## Open findings

derived: `/tmp/otr-2379-eo-verify/failopen_check.py`, run this turn
(quoted above under "What was done").

One residual gap, non-blocking against this issue's own Acceptance
criteria: `_verify_branch_base_sane()` fail-opens (returns `None`,
treated as sane) when `git merge-base br base` itself fails to resolve
any common ancestor at all — reproduced this turn with an orphan branch
carrying 500 files and zero shared history with `main` (result quoted
above: `no-common-ancestor (merge-base fails) -> None`).

The three real-world incidents this issue documents (#2372, #2384,
tokenmaxxxer-core #311) all involved a wrong-but-connected ancestor
(stale `origin/HEAD` pointing at a real, if old, point in the same
history — per the implementation record's own root-cause trace), so this
gap does not contradict the issue's own Acceptance bullets or its stated
reproduction. It is a real narrowing versus the operator-frozen
constraint's "must hold systemically... for any target repo" framing,
since a genuinely disjoint-history corruption (e.g. a workspace
accidentally re-initialized against the wrong remote) would slip through
by the same fail-open design that correctly protects legitimate shallow
clones. Not one of this issue's named Acceptance checks — no resolution
path opened here; noted for whoever next touches
`_verify_branch_base_sane()` if a disjoint-history corruption is ever
observed for real, per this repo's own precedent (#2278/#2313/#2233/#2463)
of fixing one observed case at a time rather than speculatively.

## What did not work

None — every independently-authored fixture behaved as its own hypothesis
predicted on the first run this turn; no wording or fixture-shape
correction was needed.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the three independently-executed Acceptance items
above — result:
```
check  "reproduce... or determine cannot be reproduced... guard added anyway": live concurrent-spawn repro not attempted (no outbound forge access from this sandbox either, consistent with the implementation record's own disclosure); state-level repro test result quoted above under "What was done" (2 passed); guard code confirmed present at the single choke point all four _checkout_named_branch exit paths return through (this turn, direct read, quoted above)
check  "spawn.py's branch-cut step verifies... recent... refuses/retries if not": _verify_branch_base_sane() + one-retry-then-refuse block confirmed at pipeline.py:1043-1067 (this turn, direct read, quoted above); boundary fixtures (300 accepted / 301 refused / env-override, this turn, quoted above) show the check fires exactly where the design claims
gate   "new regression test... mock a stale ref... assert refuses": test_checkout_refuses_branch_with_corrupted_merge_base result quoted above under "What was done"; independently-fixtured 301-file boundary case also refused (this turn, quoted above)
full suite: 91 passed (this turn, quoted above) — matches the record's own claimed count
```
