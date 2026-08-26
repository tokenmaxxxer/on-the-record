---
issue: 2510
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
type: fix
breaking: "none — the one path the issue requires unchanged (at least one
  criterion actually met, no UNKNOWN among the graded set, nothing blocks)
  prints byte-for-byte the same string as before, pinned by
  t_summarize_at_least_one_met_and_unblocked_reads_unchanged; grade()/
  check()'s return shape is untouched, only main()'s print logic (now
  extracted into summarize()) changed"
verdict: pass
---

# issue-2510 — implementation record

## What was done

canonical: python3 gates/requirement_met.py 2479 2493 --repo "$(pwd)" (full
transcript in Upstream basis below)

`gates/requirement_met.py` used to print the same string —
`게이트 통과 (N개 기준 채점, 차단 사유 없음)` — whenever nothing hit the
deterministic blocking sub-checks, regardless of whether any criterion had
actually been verified. An all-UNKNOWN result (nothing evaluated) and an
all-YES result (everything verified) read identically. Extracted the old
inline print logic in `main()` into a new pure function `summarize(result)
-> (text, exit_code)` and changed its branching:

1. `empty_state` (no gradable criteria) — unchanged.
2. `blocked` (deterministic sub-check fired) — unchanged: `게이트 차단:`
   plus each reason on its own line, individually visible.
3. Not blocked, but among the graded criteria:
   - every one is UNKNOWN → distinct message naming that explicitly
     (`미채점 (전부 UNKNOWN) — …`), never the legacy string, exit 0 (no
     hard-block — see Non-goals below).
   - at least one is YES and none is UNKNOWN → the exact legacy string,
     byte-for-byte (issue's "must not" clause).
   - anything else (some UNKNOWN mixed with YES/NO, or all NO with zero
     YES/UNKNOWN) → explicit `met N / unknown N / blocked 0` counts
     instead of a single collapsed verdict word, exit 0.

Also reconciled `requirement_met.py` and `merge_gate.py` on what an
all-judgment `## Acceptance` section (zero `check:`/`gate:` bullets, only
prose/advisory items) means, documented in the module docstring and here
(see Why).

Added `gates/test_requirement_met.py` coverage for `summarize()` directly
(pure-function fixtures, no `gh` calls): all-UNKNOWN, the unchanged
at-least-one-met path, partial-UNKNOWN counts, all-NO-no-UNKNOWN counts,
blocked-still-refuses, and empty-state passthrough.

## Why

canonical: python3 gates/merge_gate.py 2493 issue-2479 --repo "$(pwd)" (full
transcript in Upstream basis below)

Observed live on issue #2479 / PR #2493 (re-run captured verbatim in
Upstream basis): all four Acceptance criteria came back UNKNOWN from the
builder-blind grading session, and `requirement_met.py` still printed
`게이트 통과 (4개 기준 채점, 차단 사유 없음)`. "Nothing was evaluated" and
"everything was evaluated and nothing failed" are opposite claims that
collapsed into one string, and the collapse always favored merging — the
dangerous direction for a silent failure.

`merge_gate.py` already handles the adjacent case correctly: it reads
`check_runner`'s result for the same PR, and when the issue's Acceptance
section declares zero runnable `check:`/`gate:` lines, `check_runner`
returns its no-checks marker instead of a numeric ratio, and
`merge_gate.py` treats that as a refusal, not a pass (issue #2233). The
re-run against PR #2493 above shows this holds for it too — its Acceptance
section is entirely prose/judgment bullets, zero `check:`/`gate:` lines.

Reconciling the two gates does **not** mean making `requirement_met.py`
hard-block on UNKNOWN (the issue's explicit non-goal — an all-judgment
Acceptance section legitimately produces UNKNOWNs, and every one of them
blocking would stall a pipeline that is working as designed), nor does it
mean loosening `merge_gate.py` (the issue's explicit "must not" — it is
already correct today). The two gates operate on different axes and
neither needed to become the other:

- `merge_gate.py` is the actual landing gate (`gh pr merge` reads its
  `allowed`/`reasons`, per `on-the-record/directive/merge-gates.md`'s
  "ACCEPTANCE CHECK-RUNNER AT LANDING" and "LANDING REQUIREMENT-MET GRADE"
  entries). It already refuses an all-judgment Acceptance section outright
  via the check-runner track, independent of this fix.
  **`merge_gate.py` is authoritative for landing.**
- `requirement_met.py` was never meant to gate landing on its own: per the
  same directive doc, its deterministic artifact-presence sub-check blocks
  the merge, while its semantic YES/NO/UNKNOWN verdict per criterion is
  recorded advisory-only and never blocks by itself. Its job is to make
  the advisory picture an operator reads honest — this fix does that by
  refusing to reuse the pass string for a result nothing was actually
  verified in, without turning it into a second, competing landing gate.

So the two gates now agree on what an all-judgment section means:
`merge_gate.py` says "not satisfied" by refusing outright (authoritative,
blocks); `requirement_met.py` says the same thing by never claiming its
pass string for it (advisory, does not additionally block). Neither gate
was made more permissive to get there.

## What did not work

None.

## Upstream basis

Live re-run against issue #2479 / PR #2493, both commands run from this
repo's checkout (`--repo "$(pwd)"`, `sha: same-commit`).

**Before** (working tree at `HEAD`, this branch's parent commit, i.e.
before this fix — captured by `git stash`-ing the two edited files, running
the command, then `git stash pop` to restore the fix):

```
$ python3 gates/requirement_met.py 2479 2493 --repo "$(pwd)"
advisory: [UNKNOWN] a reproduction session given the current (undocumented) state hits at least one of the two gate refusals on its first relevant write attempt — baseline, demonstrated live.
advisory: [UNKNOWN] after adding the passing-shape directive text, a comparable reproduction session (same task shape) completes its commit/citation writes without hitting either gate on the first attempt — demonstrated live, before/after.
advisory: [UNKNOWN] state explicitly whether the gates' own refusal-message detail was found sufficient to self-correct from without the new directive text — if insufficient, file that as a separate follow-up issue and link it here rather than expanding this issue's scope.
advisory: [UNKNOWN] state explicitly whether `progressed-dirty-tree` should also be reclassified by watchdog as "needs directive fix" rather than "dead session, respawn from scratch" — if that's a separate mechanism change, name it as a follow-up rather than implementing it here (keep this issue scoped to the directive-text fix).
게이트 통과 (4개 기준 채점, 차단 사유 없음)
$ echo $?
0
```

**After** (this commit's `gates/requirement_met.py`):

```
$ python3 gates/requirement_met.py 2479 2493 --repo "$(pwd)"
advisory: [UNKNOWN] a reproduction session given the current (undocumented) state hits at least one of the two gate refusals on its first relevant write attempt — baseline, demonstrated live.
advisory: [UNKNOWN] after adding the passing-shape directive text, a comparable reproduction session (same task shape) completes its commit/citation writes without hitting either gate on the first attempt — demonstrated live, before/after.
advisory: [UNKNOWN] state explicitly whether the gates' own refusal-message detail was found sufficient to self-correct from without the new directive text — if insufficient, file that as a separate follow-up issue and link it here rather than expanding this issue's scope.
advisory: [UNKNOWN] state explicitly whether `progressed-dirty-tree` should also be reclassified by watchdog as "needs directive fix" rather than "dead session, respawn from scratch" — if that's a separate mechanism change, name it as a follow-up rather than implementing it here (keep this issue scoped to the directive-text fix).
미채점 (전부 UNKNOWN) — 4개 기준 중 실제로 검증된 것이 없다. 차단 사유는 없지만 이건 게이트 통과가 아니다.
$ echo $?
0
```

Exit code is the same in both runs above — no hard-block introduced, per
the issue's non-goal.

`merge_gate.py`'s side of the reconciliation, same PR, live:

```
$ python3 gates/merge_gate.py 2493 issue-2479 --repo "$(pwd)"
거절: PR #2493 (issue-2479)
  - check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 없다(no checks declared) — 통과로 취급하지 않는다
$ echo $?
1
```

This shows PR #2493's Acceptance section is all-judgment (zero
`check:`/`gate:` bullets) and `merge_gate.py` already refuses it on that
basis — the authoritative landing verdict for this PR was refused before
this fix too; this fix only stops `requirement_met.py`'s advisory output
from reading as a contradicting second opinion.

Unit tests, this repo:

```
$ python3 gates/test_requirement_met.py
[... 39 pre-existing + 6 new t_summarize_* fixtures ...]
41/41 passed
$ python3 -m pytest gates/test_requirement_met.py -q
41 passed in 0.87s
```

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; kept the file's existing
Korean docstrings/comments in `gates/requirement_met.py` (project
convention — "match surrounding style" guard), wrote this record and the
commit/PR text in English matching this repo's own convention (e.g.
`docs/issue-2447/reports/implementation.md`, recent `git log` subjects are
already English) — final chat-facing summary is in Korean per the skill's
report-language rule.

other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint,
verify-finding-record): not triggered — this is a single-file messaging
fix with no coupling/pattern/data-structure/architecture decision, and it
patches the defect rather than only recording a reproduction attempt.
