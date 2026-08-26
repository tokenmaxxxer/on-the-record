---
issue: 2379
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2383/reports/implementation.md
    sha: cea0f583875c91bc336ec056d6026d3945473682
code_under_review:
  - pipeline.py
  - spawn.py
  - tests/test_spawn_pipeline.py
type: fix
breaking: false
verdict: pass
---

# issue-2379 — implementation record

## What was done

Added `_verify_branch_base_sane(cwd, br, base)` and wired it into
`_checkout_named_branch()` — the shared branch-cut step
`checkout_issue_branch()`/`checkout_issue_branch_for_skill()` both go
through — so every sub-path (recut-absorbed, origin-only tracking, fresh
cut from base, or "keep the existing local branch because it has real
commits ahead") is checked before the branch is handed back.

canonical: pipeline.py:1043-1067
```
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    # 이슈 #2379: 위 세 경로(재컷/origin 추적/신규 base 컷/흡수 없이 기존
    # 재사용) 전부를 여기 한 곳에서 커버해야 PR 이 열리기 전에 무조건
    # 걸린다 — 개별 경로에 흩어 넣으면 다음 다섯 번째 경로가 또 새로
    # 생겼을 때 또 빠뜨린다.
    base = _sp._base(cwd)
    diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        # 한 번만 재시도: origin/HEAD 재계산 + 강제 재-fetch(--prune) 뒤
        # base 를 다시 구해 재검사한다 — origin/HEAD 심볼릭 참조가 일시적으로
        # 틀어져 있었을 뿐이면 여기서 회복된다. `br` 에 이미 커밋된 내용
        # 자체가 무관한 조상에서 나왔으면(진짜 손상) 재-fetch 로는 못
        # 고친다 — 그때는 거부한다.
        git("remote", "set-head", "origin", "-a")
        git("fetch", "--prune", "-q", "origin")
        base = _sp._base(cwd)
        diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        sys.exit(f"브랜치 {br} 의 merge-base 가 base({base})와 크게 어긋나 "
```

The guard function itself computes `git merge-base br base`; if that sha
differs from `base`'s own current tip, it runs
`git diff --shortstat <merge-base> br` and treats the branch as
corrupted when the changed-files or changed-lines count exceeds a
threshold.

canonical: pipeline.py:958-1000
```
def _verify_branch_base_sane(cwd: str, br: str, base: str) -> str | None:
    ...
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    mb = git("merge-base", br, base)
    if mb.returncode != 0 or not mb.stdout.strip():
        return None
    merge_base_sha = mb.stdout.strip()
    base_sha_r = git("rev-parse", "-q", "--verify", base)
    base_sha = base_sha_r.stdout.strip() if base_sha_r.returncode == 0 else None
    if base_sha is not None and merge_base_sha == base_sha:
        return None                # 완전 최신 — 방금 그 지점에서 갈라졌다
    stat_r = git("diff", "--shortstat", merge_base_sha, br)
    if stat_r.returncode != 0 or not stat_r.stdout.strip():
        return None
    m = _DIFF_SHORTSTAT_RE.search(stat_r.stdout)
    if not m:
        return None
    files = int(m.group(1))
    lines = int(m.group(2) or 0) + int(m.group(3) or 0)
    if files > _branch_base_max_files() or lines > _branch_base_max_lines():
        return (f"merge-base {merge_base_sha[:12]} vs {br}: {files} files changed, "
                f"{lines} lines (한도 {_branch_base_max_files()}파일/"
                f"{_branch_base_max_lines()}라인)")
    return None
```

Thresholds default to 300 files / 30000 lines, each overridable via
`MUSTER_BRANCH_BASE_MAX_FILES` / `MUSTER_BRANCH_BASE_MAX_LINES` for
consumer repos with different PR-size norms.

Regression coverage added in `tests/test_spawn_pipeline.py`
(`WorkspaceSyncFailClosed`): `test_checkout_refuses_branch_with_corrupted_merge_base`
and `test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base`.

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -k "corrupted_merge_base or bounded_diff_from_old_merge_base" -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base
[gw1] [ 50%] PASSED tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base
[gw0] [100%] PASSED tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base
============================== 2 passed in 1.24s ===============================
```

Full existing-suite regression check, same file:

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -q — result:
```
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 1.97s
```

## Why

**Root cause, and what issue #2383 already fixed vs. what was still
open.** `board._base()` resolves the repo's default branch by trusting
`origin/HEAD`'s symbolic-ref target without ever checking it against
reality:

canonical: 3b4da518:board.py:804-814 (HEAD before this branch's edits; board.py is untouched by this change, so this is also the current content)
```
def _base(cwd: str) -> str:
    """비교 기준 ref. origin/HEAD 가 가리키는 기본 브랜치를 우선 쓴다."""
    p = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip()
    for cand in ("origin/main", "origin/master"):
        if subprocess.run(["git", "-C", cwd, "rev-parse", "--verify", "-q", cand],
                          capture_output=True).returncode == 0:
            return cand
    return "origin/main"          # 없으면 그대로 실패시켜 "검사 불가"로 보고한다
```

`pipeline._set_origin_head()` (added by commit `cea0f583`, issue #2383,
as a side effect of that issue's worktree/disk-exhaustion audit) recomputes
that symbolic ref after every fetch in `issue_workspace()`'s three paths.
Its own docstring already names this issue as the thing it was chasing:

canonical: spawn.py:2056-2070
```
def _set_origin_head(work_dir: str) -> subprocess.CompletedProcess:
    """`origin/HEAD` 를 원격의 실제 기본 브랜치로 다시 계산한다.

    issue #2383 (#2379 근본원인 추적): `_base()`(board.py)는 `origin/HEAD`
    가 **존재하기만 하면** 그 값을 그대로 신뢰하고, 없을 때만
    `origin/main`/`origin/master` 로 폴백한다 — 존재하지만 오래된 값은
    걸러내지 않는다. 신규 클론 경로는 clone 직후 이 재계산을 이미
    거치지만(issue #221), **재사용** 경로(cwd 가 이미 이 워크스페이스이거나
    기존 워크스페이스를 fetch 만 하는 두 분기)는 `fetch`만 하고 이 재계산을
    건너뛰어 왔다 — 원격 기본 브랜치가 바뀌었거나 최초 set-head 가 조용히
    실패했던 워크스페이스는 재사용될 때마다 오염된 `origin/HEAD` 를 계속
    물고 간다. `_fetch_or_halt`의 `after=` 로 세 경로(신규/재사용 2곳)
    모두에서 fetch 직후 매번 호출한다."""
    return subprocess.run(["git", "-C", work_dir, "remote", "set-head", "origin", "-a"],
                          capture_output=True, text=True)
```

derived: git log --oneline -- spawn.py | grep 2383 — result:
```
cea0f583 issue-2383: legacy-remnant audit — gitignore scratch, root-cause implementation.json corruption, age-prune worktrees
```

That fix closed the main entry point (`issue_workspace()`), but left two
gaps: `_checkout_named_branch()` (the actual branch-cut step) does its
own fetch and never calls `_set_origin_head()` itself, and even a
correct `origin/HEAD` doesn't retroactively fix a branch that was
*already* cut from a wrong ancestor in a past, corrupted session — the
"has unique commits ahead of base, so reuse it as-is" fallback had (and,
guarded now, still structurally has, just gated) no freshness check of
any kind:

canonical: 3b4da518:spawn.py:2277 (pre-fix content; this line is now reached only after `_verify_branch_base_sane` passes, per the `_checkout_named_branch` quote above)
```
    return git("checkout", br)
```

This matches the issue's own comment #2 (PR #2384 recurrence): PR #2376
recut the branch's *content*, but the branch ref itself stayed on the bad
history, and the next CHANGES-round session picked the same corrupted
branch back up through exactly this fallback line.

**Why the guard measures diff size, not merge-base age or commit count**
(the acceptance text's alternative suggested design): this repo's own
two-phase workflow leaves proposals `AWAITING APPROVAL` for
days-to-weeks —

derived: (this session's own SessionStart hook output, reproduced verbatim from the system context at session start)
```
AWAITING APPROVAL: docs/proposals/2026-07-27-shared-core-and-consent.md — deferred (auto, stale since 2026-07-27T02:46:57Z)
AWAITING APPROVAL: docs/proposals/2026-08-10-closes-trailer-preflight-hardening.md — deferred (auto, stale since 2026-08-10T06:21:51Z)
```

— so a branch can legitimately have a merge-base that is calendar-old or
commits-behind without being corrupted. `test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base`
is the direct check of this: a branch cut straight from the repo's root
commit, with `main` gaining 50 unrelated commits afterward (merge-base
old by both time and commit count), passes because the branch's own diff
against that old merge-base is one file.

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -k bounded_diff_from_old_merge_base -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base PASSED
```

**Reproduction.** The original incident needs a live GitHub remote,
concurrent spawns, and a race between a narrow-refspec fetch and
`origin/HEAD` resolution — not reproducible deterministically inside this
sandbox (no outbound network to a real forge, no way to race concurrent
spawn processes against it in this turn). Per the acceptance criterion's
own fallback ("or determine it cannot be reproduced... and add a guard
anyway"): `test_checkout_refuses_branch_with_corrupted_merge_base`
reproduces the *state* the race produces instead — a real git fixture
with two independently-diverged lineages sharing only a root commit, a
local `issue-<n>/<role>` branch checked out from the diverged lineage's
tip plus one of the role's own commits — and confirms the guard refuses
it.

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -k test_checkout_refuses_branch_with_corrupted_merge_base -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
```

**`recut_if_absorbed_cli` left unguarded, on purpose.** It's a
mid-session self-recheck (issue #784) that runs before certain git
commands inside an *already-live* session on its own branch — it doesn't
cut a new branch, so this change doesn't touch it:

canonical: pipeline.py:909-928
```
    br_r = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "-q", "HEAD"],
                          capture_output=True, text=True)
    br = br_r.stdout.strip()
    if br_r.returncode != 0 or not re.fullmatch(r"issue-\d+/[A-Za-z0-9_-]+", br):
        return 0
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin", br],
                   capture_output=True, text=True)
    base = _sp._base(cwd)
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin",
                    base.removeprefix("origin/")],
                   capture_output=True, text=True)
    r = _sp._recut_absorbed_branch(cwd, br)
    if r.returncode != 0:
        print(f"[recut-if-absorbed] {br} 재검사 실패: {r.stderr.strip()[:200]}",
              file=sys.stderr)
        return 1
    return 0
```

The next spawn into that branch goes through `_checkout_named_branch()`,
which now catches it. Extending the guard into this path too was
considered and dropped: it would add a merge-base + diff computation to
every gated git command inside a live session, for a path already
covered at the next branch-cut — the issue's operator-frozen constraint
(comment on this issue, 2026-08-25) explicitly rules out added
per-spawn/steady-state overhead.

skill-verdict: work-in-english — applied: invoked; commit/PR text in
English, new code comments in Korean matching this repo's existing file
convention, no project-convention conflict to flag. Other mounted
skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint):
not triggered — this change is a single guard function added to one
existing branch-cut choke point, not a coupling/cohesion threshold, a
GoF-pattern decision, a data-structure/performance-cliff choice, or a
multi-module architecture decision.

## What did not work

None.

## Upstream basis

`docs/issue-2383/reports/implementation.md`, commit `cea0f583875c91bc336ec056d6026d3945473682`
(real sha — landed on `main` before this branch was cut, not in this same
commit) is the upstream fix this change builds on: it introduced
`_set_origin_head()` and wired it into `issue_workspace()`'s three fetch
paths.

canonical: spawn.py:2056-2070 (same quote as in "Why" above — `_set_origin_head()`, the upstream #2383 fix this record builds on)
```
def _set_origin_head(work_dir: str) -> subprocess.CompletedProcess:
    """`origin/HEAD` 를 원격의 실제 기본 브랜치로 다시 계산한다.

    issue #2383 (#2379 근본원인 추적): `_base()`(board.py)는 `origin/HEAD`
    가 **존재하기만 하면** 그 값을 그대로 신뢰하고, 없을 때만
    `origin/main`/`origin/master` 로 폴백한다 — 존재하지만 오래된 값은
    걸러내지 않는다.
    """
    return subprocess.run(["git", "-C", work_dir, "remote", "set-head", "origin", "-a"],
                          capture_output=True, text=True)
```

## Open findings

None.

Acceptance checklist re-run in this section (not just referenced from
"What was done"/"Why" above), so each claim below carries its own live
evidence:

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -k "corrupted_merge_base or bounded_diff_from_old_merge_base" -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base
[gw1] [ 50%] PASSED tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base
[gw0] [100%] PASSED tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base
============================== 2 passed in 1.24s ===============================
```

- check "reproduce... or determine it cannot be reproduced and downgrade...
  with a guard added anyway" — met: the deterministic state-level repro
  is `test_checkout_refuses_branch_with_corrupted_merge_base`, PASSED
  above.
- check "spawn.py's branch-cut step verifies its new branch's merge-base
  with main is recent... and refuses/retries if not" — met by
  `_verify_branch_base_sane()` + the retry-once-then-refuse block in
  `_checkout_named_branch()` (`canonical: pipeline.py:1043-1067` and
  `pipeline.py:958-1000` in "What was done" above); exercised by the same
  PASSED run.
- gate "a new regression test... mock a stale ref during branch-cut,
  assert the spawn refuses" — met by
  `test_checkout_refuses_branch_with_corrupted_merge_base`, PASSED above.

## Next steps

None — `loop_state: landed`. If a live-network concurrent-spawn repro is
ever wanted (e.g. against a disposable throwaway fork), it would need a
follow-up issue with real GitHub access from the test harness, which
this sandboxed session does not have.
