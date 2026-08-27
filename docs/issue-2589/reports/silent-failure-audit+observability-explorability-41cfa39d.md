---
issue: 2589
role: silent-failure-audit+observability-explorability-41cfa39d
author: silent-failure-audit+observability-explorability-41cfa39d
loop_state: landed
code_under_review: watchdog.py
type: bugfix
breaking: false
verdict: fixed
upstream:
  - path: watchdog.py
    sha: same-commit
---

# issue-2589 — silent-failure-audit+observability-explorability-41cfa39d record

## What was done

Split the single `print` in `watchdog.py::requirement_drift()`'s delta-mode
`failed_numbers` block (previously lines 736-741) into two, partitioned by
cache membership (`str(n) in cache`), preserving the sorted order already
established by the `for num in sorted(changed_numbers)` loop above:

- `cached_failed = [n for n in failed_numbers if str(n) in cache]` keeps the
  exact original wording unchanged:
  `[watchdog] requirement-drift: 조회 실패 {cached_failed} — 이전 캐시 판정 유지`
- `uncached_failed = [n for n in failed_numbers if str(n) not in cache]` gets
  a new line that does not claim a retained verdict:
  `[watchdog] requirement-drift: 조회 실패 {uncached_failed} — 캐시된 판정 없음, 이번 틱 미평가`

Each line only prints when its respective list is non-empty, so a tick with
only cached failures (or only uncached failures) prints exactly one line, and
a tick with both prints both — neither case is dropped or quieted.

canonical: watchdog.py:736-748 (post-fix, this commit) — the edited block
described above.

skill-verdict: silent-failure-audit — applied: invoked via the Skill tool to
review the two failure branches (cached-failure vs uncached-failure) in
watchdog.py's requirement_drift() and confirm neither is silently dropped or
misreported. Audit found 2 error-handling sites in scope, both classified
Handled — 0 Silently Absorbed, 0 Unreachable, 0 Unguarded: the `item is
None` origin site (watchdog.py:706-708, `failed_numbers.append(num)`) and
the post-fix two-way print split (watchdog.py:736-748, cited above).

skill-verdict: observability-explorability — not-applicable: this issue is
about correcting one existing log line's wording accuracy, not designing a
dashboard or ad-hoc investigation surface.

## Why

Before the fix, every number in `failed_numbers` — regardless of whether it
had ever been fetched successfully before — was reported with "이전 캐시
판정 유지" ("previous cached verdict retained"). `cache` is loaded once at
the top of the delta branch (`_sp._load_requirement_drift_cache(cache_path)`,
watchdog.py:700) and is keyed by `str(number)`; a number that fails fetch and
was never cached before (e.g. a brand-new issue/PR number that only appeared
in this tick's `changed_numbers` and whose very first fetch attempt failed)
has no entry in `cache` at all — so claiming its "previous verdict" was
retained is false: there is no previous verdict to retain, and the number
was silently excluded from this tick's requirement-drift evaluation without
a caller ever being told that. That's issue #2589: the observable behavior
(the log line) made a claim the underlying state didn't support, which is
exactly the kind of misreport that defeats a `print`-as-observability
contract — a human or downstream tooling reading the log has no way to
distinguish "stale but present verdict" from "no verdict, ever" for that
number. The fix must not reduce reporting in either case (per the issue's
explicit must-not clause): both partitions still print, each with accurate
wording for its own case.

canonical: watchdog.py:700 (`cache = _sp._load_requirement_drift_cache(cache_path)`)
and watchdog.py:704-708 (the `failed_numbers.append(num)` origin) — basis for
the "no entry in cache at all" claim above.

## What did not work

None.

## Upstream basis

- path: watchdog.py
  sha: same-commit

## Open findings

none

## Next steps

None — `loop_state` is terminal (`landed`) for this coding-record; the fix
is landed in this same commit as this record.

## Verification (executed evidence)

acceptance: `python3 /tmp/verify_2589.py` (throwaway script, not committed;
deleted immediately after this run) — result: a real call to
`watchdog.requirement_drift()` printed two distinct lines, one per
partition, and the in-script assertions on their exact content passed:

```
=== CAPTURED STDOUT ===
[watchdog] requirement-drift: 조회 실패 [100] — 이전 캐시 판정 유지
[watchdog] requirement-drift: 조회 실패 [200] — 캐시된 판정 없음, 이번 틱 미평가
[watchdog] requirement-drift: 요구 R1 — 다이제스트: "something" (source: #1) — 열린 이슈/PR 어디에도 인용되지 않는다. 후보(요구 인용이 전혀 없는 열린 이슈/PR): [300]
[watchdog] requirement-drift: 요구 ID 를 전혀 인용하지 않는 열린 이슈/PR [300]

=== CHECKS ===
ALL CHECKS PASSED
```

Test setup: a temp `root` with `docs/specs/requirement-digest.md` containing
`- R1: something [open] (source: #1)`; `watchdog._sp` set to `watchdog`
itself (the module's own patching-compat seam, since `_sp` is `None` outside
the real spawn.py import chain); `watchdog._requirement_drift_cache_path`
monkeypatched to a temp file pre-seeded via `_save_requirement_drift_cache`
with an entry for number `100` only (number `200` left absent — not
cached); `watchdog._fetch_issue_or_pr_via_cache` monkeypatched to return
`None` for `100` and `200` (forced lookup failure) and a valid open item for
`300` (so `any_fetch_ok` is `True` and the delta branch reaches the
`failed_numbers` print block instead of short-circuiting on the full
`gh 실패` early-return path); `watchdog._watchdog_note_gh_failure`
monkeypatched to `False` to avoid unrelated noise-state file I/O. Called
`watchdog.requirement_drift(Path(root), changed_numbers={100, 200, 300})`
with stdout captured via `contextlib.redirect_stdout`.

derived: the "ALL CHECKS PASSED" line in the fenced block above is the
in-script assertion result for: line containing `[100]` includes "이전 캐시
판정 유지"; line containing `[200]` does not include that phrase.
