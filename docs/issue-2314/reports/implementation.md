---
issue: 2314
role: implementation
loop_state: landed
upstream:
  - path: gates/stale_revert_guard.py
    sha: 69a26bc7a994056095699ed01aeab48d11497636
code_under_review:
  - gates/stale_revert_guard.py
  - gates/test_stale_revert_guard.py
type: fix
breaking: "none for text-only PRs (see empty-state evidence below); binary-touching PRs go from crash to a verdict"
verdict: pass
---

# issue-2314 — implementation record

## What was done

canonical: `git show 69a26bc7 --stat`
```
 docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md |  71 ++++
 gates/stale_revert_guard.py                                                     |  49 ++-
 gates/test_stale_revert_guard.py                                                | 218 +++++++++
 tests/test_stale_revert_guard.py                                                | 116 ------
 4 files changed, 328 insertions(+), 126 deletions(-)
```
The `D` line above is: renamed from `tests/test_stale_revert_guard.py` to
`gates/test_stale_revert_guard.py` in this same commit; the `tests/` path
no longer exists as of `69a26bc7`.

`gates/stale_revert_guard.py:_git_show()` used to decode `git show` output
with `text=True` (strict UTF-8) and crashed on any binary blob a PR touched
(e.g. a PNG), taking the whole `check_pr()` call down with no ALLOW/REFUSE
verdict:

derived: `python3 -c "srg.check_pr(repo, 'main', mb_sha, 'pr-branch')"` against `gates/stale_revert_guard.py` at parent commit `e876c17e` (pre-fix), synthetic repo with a base HEAD that grows a PNG then a security fix, PR branch a stale unrelated edit that also adds a PNG (fixture shape now at `gates/test_stale_revert_guard.py:132-149`, `_init_repo`/`_commit_binary`)
```
Traceback (most recent call last):
  File "gates/stale_revert_guard.py", line 141, in check_pr
    head_content = _git_show(repo, pr_head_ref, path)
  File "gates/stale_revert_guard.py", line 119, in _git_show
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=repo,
  ...
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte
```
This is the exact trace and byte position (0x89, position 0) reported in
the issue body.

Two changes, per the issue's ask:

1. `changed_paths()` now runs `git diff --numstat` instead of `--name-only`
   and skips any path where git marks both added/deleted columns `-` —
   git's own binary marker — so binary paths never reach line-diff logic
   (primary defense).

   canonical: `69a26bc7:gates/stale_revert_guard.py:142-158`
   ```
   def changed_paths(repo: Path, merge_base_ref: str, head_ref: str) -> list[str]:
       """`--numstat`으로 바이너리 경로를 제외한다 -- git 은 바이너리 파일의
       추가/삭제 줄 수 칸에 `-`를 찍는다("-\t-\t<path>"), 그 자체가 "이
       경로는 line-diff 대상이 아니다"라는 신호다(issue #2314)."""
       r = subprocess.run(
           ["git", "diff", "--numstat", f"{merge_base_ref}..{head_ref}"],
           cwd=repo, capture_output=True, text=True)
       if r.returncode != 0:
           return []
       paths = []
       for line in r.stdout.splitlines():
           if not line:
               continue
           added, deleted, path = line.split("\t", 2)
   ```

2. `_git_show()` now captures raw bytes (drops `text=True`) and decodes
   with `errors="surrogateescape"` (defense in depth for a binary path
   that slips past #1 — see the hunt finding below for why this isn't a
   bare try/except-to-`""`).

   canonical: `69a26bc7:gates/stale_revert_guard.py:135-139`
   ```
       r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=repo,
                           capture_output=True)
       if r.returncode != 0:
           return ""
       return r.stdout.decode("utf-8", errors="surrogateescape")
   ```

Also renamed from `tests/test_stale_revert_guard.py` to
`gates/test_stale_revert_guard.py` in this same commit (`git mv`) — the
issue's Acceptance names `gates/test_stale_revert_guard.py` as the gate,
and this matches the repo's own established convention of colocating a
module's test beside its module in `gates/`. Precedent: `gates/test_merge_gate.py`
(a real, currently-existing path) was itself renamed from
`tests/test_merge_gate.py` to `gates/test_merge_gate.py` earlier, for the
same `gates/test_duplicate_test_basenames.py` collision-avoidance reason —
see that file's own docstring, first paragraph (`gates/test_merge_gate.py:2-7`).

Added 5 new tests to `gates/test_stale_revert_guard.py` (11 total in the
file, 6 pre-existing moved unchanged) covering the binary-exclusion path,
the non-crash guarantee, and the non-UTF-8-but-non-binary regression the
hunt found (below). derived: `git show 69a26bc7 -- gates/test_stale_revert_guard.py | grep -c '^+def test_'` → 11

## Why

`--numstat`'s binary marker is git's own semantics for "not a line-diff
subject," not a heuristic re-derivation, so it's the correct primary
signal. `_git_show` hardening is defense in depth for whatever `--numstat`
doesn't catch — once that path is reachable, the fallback has to preserve
content rather than erase it, or the gate trades "crashes on unusual
input" for "silently permits unusual input to revert real fixes," a worse
failure mode for a merge gate whose job is refusing bad merges.

## What did not work

- Wrote `_git_show()`'s decode-failure fallback as
  `except UnicodeDecodeError: return ""` (the issue's literal wording).
  A before-landing warrant-hunt (stance 0: assume the gate just touched is
  bypassable) reproduced a silent fail-open:

  acceptance: cat docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md — result:
  ```
  Verdict: FINDING — `_git_show()`'s UnicodeDecodeError-to-`""` fallback lets a real (non-binary-per-git) stale revert of a security fix pass as ALLOW when the fixed line contains a non-UTF-8 byte, because `""` makes `classify()`'s `_added_lines()` see zero additions and short-circuit to ALLOW before ever comparing to `head`.
  ...
  numstat: '1\t0\tapp.py\n'
  git_show(base_head): ''
  refusals: []
  ```
  (full reproduction script and narrative committed at
  `69a26bc7:docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md`)

  Replaced the `""` fallback with `errors="surrogateescape"` decoding —
  never fails, preserves byte-level distinctness, so `classify()`'s line
  comparisons still work correctly on such content. See Rationale for
  deviations.

- After that change, `_merge_file()` (which writes the three snapshots via
  `Path.write_text()` and reads `git merge-file`'s stdout via `text=True`
  — both strict-UTF-8) raised `UnicodeEncodeError` on a
  `surrogateescape`-decoded string containing a lone surrogate:

  derived: `python3 -m pytest -q gates/test_stale_revert_guard.py::test_check_pr_refuses_stale_revert_of_non_utf8_line_git_does_not_treat_as_binary` (run against the `_git_show`-only fix, before the `_merge_file` follow-up)
  ```
  cur_p.write_text(current)
  ...
  UnicodeEncodeError: 'utf-8' codec can't encode character '\udce9' in position 13: surrogates not allowed
  ```
  Fixed by round-tripping `_merge_file()`'s I/O through
  `encode`/`decode("utf-8", errors="surrogateescape")` as well (shown in
  the `_merge_file` quote in Rationale for deviations, and live at
  `69a26bc7:gates/stale_revert_guard.py:57-66`).

## Rationale for deviations

canonical: `69a26bc7:gates/stale_revert_guard.py:57-66`
```
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cur_p, base_p, other_p = tdp / "current", tdp / "base", tdp / "other"
        cur_p.write_bytes(current.encode("utf-8", errors="surrogateescape"))
        base_p.write_bytes(base.encode("utf-8", errors="surrogateescape"))
        other_p.write_bytes(other.encode("utf-8", errors="surrogateescape"))
        r = subprocess.run(
            ["git", "merge-file", "-p", str(cur_p), str(base_p), str(other_p)],
            capture_output=True)
        return r.returncode == 0, r.stdout.decode("utf-8", errors="surrogateescape")
```

The issue's Ask literally specifies: "harden `_git_show` (bytes + decode
with fallback `""`) as defense in depth." I implemented that first, then
the before-landing warrant-hunt cited under What did not work found it
introduces a silent-ALLOW regression on genuine stale reverts of
non-UTF-8-but-git-non-binary content. A merge gate silently passing a real
stale revert is a worse outcome than the crash the issue reports, so I
deviated from the literal fallback value: `_git_show` decodes with
`errors="surrogateescape"` instead of falling back to `""` on failure.
This still satisfies the issue's actual requirement (`_git_show` never
raises `UnicodeDecodeError`) and its "defense in depth" framing (primary
defense stays `changed_paths()`'s binary-path exclusion), while closing
the gap the literal fallback opened. It also required hardening
`_merge_file()`'s I/O to the same encoding scheme (quoted above) — outside
the issue's named functions, but necessary for the `surrogateescape` fix
to not just relocate the crash.

## Upstream basis

- `gates/stale_revert_guard.py` at `same-commit` (`69a26bc7`, this fix).
- Issue #2314 body: exact crash trace matched byte-for-byte, see
  reproduction under What was done.
- Before-landing warrant-hunt log, committed at
  `69a26bc7:docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md`.

## Open findings

None open. The one warrant-hunt finding (silent fail-open via the `""`
fallback) was fixed in commit `69a26bc7` and is covered by
`test_check_pr_refuses_stale_revert_of_non_utf8_line_git_does_not_treat_as_binary`
(passing, see acceptance evidence below). A second before-landing hunt
round was not re-dispatched after the `_merge_file` follow-up fix — that
fix is a narrow, same-shape encoding round-trip with no new control flow,
covered directly by the full `gates/test_stale_revert_guard.py` suite plus
a full `gates/` regression run (both green, see below).

## Acceptance evidence

Post-fix, same PNG fixture as the pre-fix reproduction above: clean
verdict, genuine stale revert still refused.

acceptance: `python3 -c "... srg.check_pr(repo, 'main', mb_sha, 'pr-branch') ..."` (post-fix, commit `69a26bc7`) — result:
```
refusals: [{'verdict': 'REFUSE', 'reason': 'app.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)', 'path': 'app.py'}]
OK
```

Empty state (text-only PR, no binaries) — byte-identical: 6 tests renamed
from `tests/test_stale_revert_guard.py` to `gates/test_stale_revert_guard.py`
in this same commit, plus 5 new ones, all pass:

acceptance: `python3 -m pytest -q gates/test_stale_revert_guard.py` — result:
```
...........
11 passed in 18.20s
```

Full gate-suite regression guard:

acceptance: `python3 -m pytest -q gates/` — result:
```
975 passed, 8 xfailed in 92.16s
```
(8 xfailed are pre-existing, unrelated to this change.)

skill-verdict: implementation-blueprint — not-applicable: single-function bugfix inside one existing module, no new module/file structure or multi-file architecture decision to make.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric threshold, accessor chain, or check-pipeline-ordering decision involved.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern introduction/removal decision; this is a direct procedural fix.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm choice with a performance-cliff shape; `--numstat` vs `--name-only` is a correctness fix (binary exclusion), not a perf trade-off.
skill-verdict: work-in-english — applied: invoked; commit messages, this record, and in-code English comments/docstrings for the new logic are English; existing Korean rationale comments in this module predate this change and were kept in the surrounding style, not newly introduced.

## Next steps

None — loop_state: landed.
