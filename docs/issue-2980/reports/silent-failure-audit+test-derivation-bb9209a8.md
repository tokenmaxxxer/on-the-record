---
issue: 2980
role: silent-failure-audit+test-derivation-bb9209a8
author: silent-failure-audit+test-derivation-bb9209a8
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 9738f59567d1548c2cfeacaa8bf89bccbfb88c22
type: implementation-record
breaking: false
verdict: requirement-drift-lookup-failures-now-print-under-their-own-tags-cached-retention-carries-an-observed-at-marker-and-actually-re-enters-the-verdict-uncached-failures-report-unknown-and-a-hunter-found-fixed-guard-regression-that-would-have-silenced-genuine-zero-failure-verdicts
loop_state: landed
upstream:
  - path: watchdog.py
    sha: 9738f59567d1548c2cfeacaa8bf89bccbfb88c22
  - path: tests/test_requirement_drift_third_state_2980.py
    sha: 9738f59567d1548c2cfeacaa8bf89bccbfb88c22
---

# issue-2980 — silent-failure-audit+test-derivation-bb9209a8 record

## What was done

Fixed `watchdog.requirement_drift()` (reached in production as
`spawn.requirement_drift`, since `spawn.py` imports `watchdog.py` and sets
`watchdog._sp = spawn`) so a failed `gh` lookup is never printed under the
same `[watchdog] requirement-drift:` tag a reached verdict line uses, and so
a lookup failure on a changed number is marked by which of two genuinely
different situations it is, rather than one message that both misnamed the
state and (for the cached case) didn't actually do what it claimed.

Three new print channels, all distinct from the verdict tag:

1. `requirement-drift-lookup-failed:` — total lookup failure (full-mode
   board unreadable, or delta-mode where zero of the changed numbers
   fetched). Still gated by the existing streak-based noise suppression
   (`_watchdog_note_gh_failure`, issue #2196) so a single transient blip
   stays silent and only a sustained streak reports.
2. `requirement-drift-cache-retained:` — a changed number whose fetch
   failed but has a genuine prior cache entry. The line now names when
   that prior was observed (`관측: <ISO-8601 UTC timestamp>`), taken from
   a new `cached_at` field written into `requirement_drift_cache.json`
   both on full-mode cache refresh and on each successful delta-mode
   per-number fetch.
3. `requirement-drift-unknown:` — a changed number whose fetch failed and
   has no prior cache entry at all (a newly filed subject). Never uses
   retention language, and is never added to the tick's verdict input.

canonical: `git show d0aca5a1 -- watchdog.py` (first commit this session):
```diff
-                print("[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)")
+                print("[watchdog] requirement-drift-lookup-failed: gh 실패 — "
+                      "조회 실패, 판정 없음 (advisory, 미집계)")
...
-            if cached_failed:
-                print(f"[watchdog] requirement-drift: 조회 실패 {cached_failed} — "
-                      "이전 캐시 판정 유지")
+            for n in cached_failed:
+                observed_at = cache.get(str(n), {}).get("cached_at", "unknown")
+                print(f"[watchdog] requirement-drift-cache-retained: 조회 실패 {n} — "
+                      f"이전 캐시 판정 유지 (관측: {observed_at})")
             if uncached_failed:
-                print(f"[watchdog] requirement-drift: 조회 실패 {uncached_failed} — "
-                      "캐시된 판정 없음, 이번 틱 미평가")
+                print(f"[watchdog] requirement-drift-unknown: 조회 실패 {uncached_failed} — "
+                      "이전 판정 없음, unknown")
```

A second, structural fix was required underneath the message change.
canonical: `watchdog.py` as it read pre-fix (before commit `d0aca5a1`) in
the delta-mode reuse pass — `if key_num in changed_numbers: continue`,
skipping every number in `changed_numbers` whether its fetch succeeded or
failed, so a `cached_failed` number's prior title/body was dropped from
`all_items` unconditionally and never actually re-entered the tick's
citation computation — the old "이전 캐시 판정 유지" ("retained the
previous cached verdict") message was never true. Fixed by tracking a
`fetched_numbers` set (numbers actually fetched this tick, success or
confirmed-closed) and having the reuse pass skip only those (`if key_num
in fetched_numbers: continue`), so a `cached_failed` number's prior data
now really does flow back into `all_items` and contribute to
`mentioned_reqs`.

Also fixed: the old code returned immediately whenever `any_fetch_ok` was
`False` (no changed number fetched live), which — for the case of exactly
one changed number failing — meant the per-number cached-retained/unknown
reporting code was unreachable, since that block sat after the early
`return`. The `gh`-connectivity streak signal
(`requirement-drift-lookup-failed`, still gated by the same streak logic)
is now independent of whether the tick continues to report per-number
retained/unknown state and compute a verdict from whatever data (fresh or
retained) is actually available. See "What did not work" for how this was
diagnosed.

A second commit (`9738f595`, "fix round") followed a before-landing
warrant-hunter finding against the first commit — see "Open findings"
below for the finding and its fix.

## Why

test-derivation (skill-repository, invoked via the Skill tool this
session): the issue's three acceptance checks are each one Given-When-Then
scenario already (Given a full/delta lookup that fails entirely / Given a
changed number with a cache entry that fails to refetch / Given a changed
number with no cache entry that fails to refetch — When `requirement_drift`
runs — Then it prints the corresponding distinct tag and never the verdict
tag). Routing: none of the three route to decision-table, state-transition,
pairwise, or MC/DC territory on their own terms — each is a single Boolean
condition (lookup succeeded or not, prior cache entry exists or not) — so
the primary route is equivalence partitioning over the lookup-outcome
space, at Medium depth (user/operator-facing advisory output, not
safety/regulatory, so no full itemized boundary enumeration is warranted).

derived: `grep -n "def test_" tests/test_requirement_drift_third_state_2980.py`
```
72:    def test_requirement_drift_lookup_failure_state(self, board_repo, capsys):
89:    def test_requirement_drift_lookup_failure_state_empty_when_no_failure(
104:    def test_requirement_drift_cached_verdict_marked(self, board_repo, capsys):
130:    def test_requirement_drift_cached_verdict_retention_not_dropped(
158:    def test_requirement_drift_no_prior_reports_unknown(self, board_repo, capsys):
176:    def test_requirement_drift_no_prior_reports_unknown_empty_when_all_succeed(
193:    def test_requirement_drift_no_failure_empty_items_still_flags_drift(
```
Five partitions total (fresh success — existing/untouched by this issue,
total failure, a cached-prior failure, a no-prior failure, and — added
after the hunter finding below — a zero-failure-but-empty-items tick),
each exercised by ≥1 of the 7 test cases listed above: total-failure by
lines 72 and 89, cached-prior failure by lines 104 and 130 (the second
constructs the genuine prior as an explicit two-tick sequence — a success
tick populates the cache, a later tick's fetch fails — since that is the
only way to construct a "genuine prior" at all; this rides along the EP
case rather than being separately routed to state-transition testing, as
there is no multi-state lifecycle here beyond "was this number ever
successfully cached before"), no-prior failure by lines 158 and 176, and
the zero-failure-empty-items partition (the fifth, added in response to
the hunter finding, not part of the issue's original three acceptance
checks but required to keep the fix from introducing a new silent-failure
class of its own) by line 193. Fresh success is exercised by every other
test in the suite that never mocks a fetch failure and is not re-derived
here.

silent-failure-audit (skill-repository, invoked via the Skill tool this
session): this issue is exactly the catalog's "log-and-continue with
misleading recovery" pattern, but in reverse-discovery order — the report
was already written in prose form by the issue text and the fix's job was
to trace forward from each `print()` site (Step 3 of the audit: site →
downstream consequence) to confirm what actually happens after the message
fires, not just to reword the message. canonical: that trace is what
surfaced the `fetched_numbers`/`all_items` structural bug documented above
under "What was done" — the cached-retained print site's downstream
consequence, before the first commit, was "the retained data is never
added to `all_items`," a Silently Absorbed pattern (default substitution —
silently dropping the failed number — without recording that the
substitution happened) hiding directly underneath a print statement that
claimed the opposite. The same audit lens caught a second instance of the
identical failure shape one layer deeper: the `if not all_items: return`
guard this session itself introduced to fix the first instance was, by the
letter of the audit's own Step 3 (trace every catch/guard site forward to
its downstream consequence), itself a new silent-absorption site — see
"Open findings" for the trace.

Considered and rejected: leaving the per-number cached/uncached reporting
gated behind the old `if not any_fetch_ok: ...; return` structure and only
adding the observed-at marker to the message text. Rejected because that
leaves the single-most-common real case — exactly one changed number, and
its fetch fails — printing nothing at all for the cached-retained/unknown
states. See "What did not work" for the live failing-test evidence that
led to rejecting it.

## What did not work

The first draft of `test_requirement_drift_cached_verdict_marked` (single
changed number, its own second-tick fetch failing) failed against a
message-only version of the fix (before the `fetched_numbers`/early-return
restructuring): the `if not any_fetch_ok: return` early exit swallowed the
whole failed_numbers reporting block whenever the only changed number in
the tick was the one that failed, since `any_fetch_ok` never became
`True`.

canonical: pytest failure output from that draft, captured live this
session before the restructuring:
```
>       assert "requirement-drift-cache-retained:" in out
E       AssertionError: assert 'requirement-drift-cache-retained:' in ''
```
Diagnosed from that empty output, then restructured the gh-connectivity
early return so it no longer aborts the per-number reporting or the
verdict computation over retained/reused data.

A second thing that did not work, caught by the dispatched before-landing
warrant-hunter rather than by this session's own tests: the first
commit's `if not all_items: return` guard (added to satisfy the
must-not on treating a failed lookup as a violation) was too broad — it
also fired, and silently suppressed a genuine verdict, on a fully
successful zero-failure tick whose only relevant cached item turned out
(via a successful live refetch) to be closed. See "Open findings" for the
finding and its fix.

## Upstream basis

`watchdog.py` (function `requirement_drift`) and
`tests/test_requirement_drift_third_state_2980.py`, both committed at
`9738f59567d1548c2cfeacaa8bf89bccbfb88c22` (second commit; first commit
`d0aca5a160c0de9204c0a8efc736527ec82f73f8`).

## Acceptance (executed evidence)

acceptance: `python3 -m pytest tests/ -k requirement_drift_lookup_failure_state -q` — result:
```
2 passed
```

acceptance: `python3 -m pytest tests/ -k requirement_drift_cached_verdict_marked -q` — result:
```
1 passed
```

acceptance: `python3 -m pytest tests/ -k requirement_drift_no_prior_reports_unknown -q` — result:
```
2 passed
```

acceptance: `python3 -m pytest tests/test_requirement_drift_third_state_2980.py -v` — result: all 7 cases pass —
```
tests/test_requirement_drift_third_state_2980.py::TestLookupFailureState::test_requirement_drift_lookup_failure_state PASSED
tests/test_requirement_drift_third_state_2980.py::TestLookupFailureState::test_requirement_drift_lookup_failure_state_empty_when_no_failure PASSED
tests/test_requirement_drift_third_state_2980.py::TestCachedVerdictMarked::test_requirement_drift_cached_verdict_marked PASSED
tests/test_requirement_drift_third_state_2980.py::TestCachedVerdictMarked::test_requirement_drift_cached_verdict_retention_not_dropped PASSED
tests/test_requirement_drift_third_state_2980.py::TestNoPriorReportsUnknown::test_requirement_drift_no_prior_reports_unknown PASSED
tests/test_requirement_drift_third_state_2980.py::TestNoPriorReportsUnknown::test_requirement_drift_no_prior_reports_unknown_empty_when_all_succeed PASSED
tests/test_requirement_drift_third_state_2980.py::TestNoFailureStillComputesVerdict::test_requirement_drift_no_failure_empty_items_still_flags_drift PASSED
============================== 7 passed in 0.80s ===============================
```

No regressions — derived: ran the full suite (`python3 -m pytest test/
tests/ -q`) after the second (fix-round) commit:
```
20 failed, 690 passed, 3 xfailed
```
The same 20 pre-existing failures as measured before this session's
changes (verified earlier the same session via `git stash`/`git stash
pop` around the first commit: `20 failed, 114 passed` over the affected
subset with changes stashed out, identical failing test IDs, none in
`watchdog.py`'s `requirement_drift` or the new test file) — one more test
passes now (690 vs. 689) because of the added
`test_requirement_drift_no_failure_empty_items_still_flags_drift`
regression case; zero new failures.

Diff scope — derived: `git show --stat d0aca5a1` and `git show --stat 9738f595`:
```
d0aca5a1: watchdog.py | 72 ++-, tests/test_requirement_drift_third_state_2980.py | 182 ++ (new file) -- 2 files changed, 237 insertions(+), 17 deletions(-)
9738f595: watchdog.py | 19 ++, tests/test_requirement_drift_third_state_2980.py | 36 ++, docs/issue-2980/reports/.../2026-09-01-hunt-requirement-drift-third-state.md (new file) -- 3 files changed, 154 insertions(+), 5 deletions(-)
```
No `gates/`, `hooks/`, or `docs/specs/` path touched by either commit, so
no `spec_index.py --update` regeneration applies.

## Open findings

One finding, fixed within this session (not open). Before-landing
warrant-hunter (background, stance 0 — "assume the third-state distinction
is bypassable," tier `size:>200-lines`, 180s cap), dispatched against the
first commit (`d0aca5a1`), reported: the `if not all_items: return` guard
also suppressed a genuinely successful, zero-failure delta tick (the only
cached item confirmed closed via a successful live refetch, nothing else
cached) — full silence, none of the three new tags or the original verdict
tag fired, where the equivalent full-mode empty-board state correctly
prints a `requirement-drift:` violation line.

canonical: `docs/issue-2980/reports/silent-failure-audit+test-derivation-bb9209a8/2026-09-01-hunt-requirement-drift-third-state.md`
(full finding, reproduction script, and resolution, committed at
`9738f595`).

Fixed in the second commit (`9738f595`) by narrowing the guard to
`if failed_numbers and not all_items: return`, and covered going forward
by `test_requirement_drift_no_failure_empty_items_still_flags_drift`.

## Next steps

None — `loop_state: landed`.

skill-verdict: silent-failure-audit — applied: invoked; traced each of the
`requirement_drift()` print/guard sites forward (Step 3 of the audit) to
their actual downstream consequence, which is what surfaced both the
`fetched_numbers`/`all_items` structural defect and (via the dispatched
hunter applying the same trace-forward lens one layer deeper) the
`if not all_items: return` over-broad guard — see "Why" and "Open
findings" above.
skill-verdict: test-derivation — applied: invoked; routed the three
acceptance checks (plus a fourth partition added in response to the hunter
finding) to equivalence partitioning over the lookup-outcome space,
classified Medium depth, and derived
`tests/test_requirement_drift_third_state_2980.py`'s test cases from that
partition list plus one two-tick genuine-prior construction for the
cached-prior partition — see "Why" above.
skill-verdict: work-in-english — invoked; applied: wrote code comments,
commit messages, and this record in English; the final user-facing reply
is in Korean.
other mounted skills: not triggered
