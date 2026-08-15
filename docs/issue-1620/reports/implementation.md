---
code_under_review:
  - gates/record_lint.py
  - gates/test_record_lint.py
type: fix
breaking: false
verdict: landed
loop_state: landed
---

## What was done

canonical: gh issue view 1620 (read this session)

Fixed the four second-wave misfire classes issue #1620 named for
`gates/record_lint.py`'s rule-330 (`orphaned_path_reference_check`) and
rule-333 (`bare_count_claim_check`) checkers:

1. **Path/function-locator suffixes** (`gates/record_lint.py:76-90`) —
   `_strip_line_suffix` now also strips a comma-separated line list and
   a `:name()`/`::name()` function/method locator suffix before the
   existence check, via a new `_FUNC_SUFFIX` regex applied ahead of the
   existing `_LINE_SUFFIX` one. Example shapes fixed (from the fixture
   tests added, `gates/test_record_lint.py`):
   ```
   gates/landing_readiness.py:60,137
   gates/claim_scan.py::scan_text()
   gates/ci.py:_phase2_record_evidence()
   ```
2. **Rename/deviation narration** (`gates/record_lint.py:453-479`) —
   `orphaned_path_reference_check` now skips a path reference when a
   3-line window around it contains a rename/move/deliberate-non-use
   narration marker (`_PATH_RENAME_NARRATION`).
3. **Absence/negation statements** (`gates/record_lint.py:136-152`,
   `426-431`) — both `orphaned_path_reference_check` and
   `bare_count_claim_check` now skip a claim whose surrounding 3-line
   window matches `_ABSENCE_NEGATION` ("no ... needed/required", "not
   (yet) needed/required/applicable/measurable").
4. **Rule 333 self-evidencing tallies** (`gates/record_lint.py:432-448`)
   — `bare_count_claim_check` now also accepts, within a 6-line-above
   window: a `canonical:` tag, an inline-computed shape (`%` or `=`
   showing the arithmetic), or a fenced raw-output block anywhere
   earlier in the same record's prose.

Added fixture tests to `gates/test_record_lint.py`, each misfire class
covered both ways (fires on the genuine-violation shape, silent on the
misfire shape):

```
t_orphaned_path_reference_check_locator_suffix_resolved_issue_1620
t_orphaned_path_reference_check_double_colon_function_suffix
t_orphaned_path_reference_check_comma_separated_line_list
t_orphaned_path_reference_check_exempts_rename_narration
t_orphaned_path_reference_check_still_fires_on_genuinely_missing_rename
t_orphaned_path_reference_check_exempts_absence_negation
t_misfire_absence_negation_not_flagged_as_bare_count
t_misfire_inline_computed_percentage_not_flagged_as_bare_count
t_misfire_fenced_output_above_not_flagged_as_bare_count
t_misfire_canonical_tag_same_line_not_flagged_as_bare_count
t_bare_count_claim_check_still_fires_without_evidence
```

Also converted the pre-existing
`t_orphaned_path_reference_check_false_positives_documented_gap` xfail
(the locator-suffix half of a prior deferred gap) into a normal passing
regression test, per that test's own docstring instruction — its
`strict=True` marker would otherwise itself fail the moment the fix
landed.

## Why

canonical: gh issue view 1620 (read this session)

Issue #1620's own body quotes a 2026-08-16 HEAD 752965b6 measurement
placing rule 330 at 33.3% precision (4 TP / 12) and rule 333 at 0%
(0 TP / 5), both below the 70% per-rule kill bar. The issue names four
misfire classes with worked examples; this session fixed each class as
specified.

## Genuine citation breaks (Acceptance bullet 3) — scope note

canonical: PreToolUse hook output this session (board-gate.sh refusal,
quoted below)

Issue #1620 also asks for 4 genuine test-directory-rename citation
breaks to be fixed in their own issues' records. A `grep` naming
another issue's docs path as an argument was refused this session by
`core/hooks/board-gate.sh`:

```
board-gate: writing docs/issue-711/ requires branch issue-711/implementation (current: issue-1620/implementation).
```

That is a board-gate boundary on writes (and, as observed here, even
argument-mentions) touching another issue's tree. Per the
SCOPE-EXCEEDED rule this session finishes what its own write set
covers and stops rather than widening into those issues' branches —
filed as a deviation below.

## How this was verified (generation-time confirmation, not a review pass)

derived: `python3 -m pytest gates/test_record_lint.py -q`
```
..........................................................               [100%]
58 passed in 1.05s
```

derived: `python3 -m pytest gates/test_role_spec_shape.py gates/test_patrol_queue.py gates/test_precision_measure.py -q`
```
........................                                                 [100%]
24 passed in 0.91s
```

`role_spec_shape.py` calls `record_lint.orphaned_path_reference_check`
directly; `patrol_queue`/`precision_measure` both import `record_lint`
— targeted coverage for every module calling into the changed
functions.

## Acceptance bullet 2 — precision_measure re-run on live HEAD

derived: `python3 gates/precision_measure.py sample . --n 100 --seed 20260817 --out /tmp/samples_1620.json`
```
wrote 7 sample items (population 7) to /tmp/samples_1620.json
```

The live population went from 17 (issue's prior measurement) to 7 —
all 7 remaining are rule-330 findings; rule 333's population is 0
findings (empty state: precision undefined for rule 333, promotion not
applicable for it).

canonical: manual `ls`/`find` this session against each of the 7
sampled rule-330 findings' cited paths — all 7 confirmed absent from
the working tree, e.g.:
```
cited (absent):  gates/test_gates.py
actual location: tests/test_gates.py
cited (absent):  on-the-record/hooks/test_pr_base_guard.py
actual location: on-the-record/hooks/test_pr_base_guard_hook.py
```
so all 7 judged TP.

derived: `python3 gates/precision_measure.py report /tmp/samples_1620.json --judgments /tmp/judgments_1620.json`
```
population=7 sampled=7

| rule | sampled | TP | precision | wilson_lb_90 |
|---|---|---|---|---|
| issue-330 | 7 | 7 | 100.0% | 81.0% |
| overall | 7 | 7 | 100.0% | 81.0% |

pass rule: overall point>=90% AND wilson_lb_90>=85% AND no per-rule kill(<70%)
promote: NO
```

Per the #1614 promotion threshold (point>=90% AND Wilson LB>=85%, no
per-rule kill) applied to the numbers above, the result is NO — rule
330's point estimate is now 100% (no per-rule kill), but the shrunk
n=7 sample's one-sided Wilson lower bound (81%) sits below the 85%
floor. Evaluated as pre-registered, not relaxed for this run.

## PR #1622 review response (2026-08-16)

canonical: `gh pr view 1622 --json reviews,comments` this session (blocking
comment, quoted findings below)

Blocking findings 1 and 2 from the review comment:

canonical: `gates/record_lint.py:407-456` this session (diff applied in
this turn, quoted below)

1. Fence exemption was a blanket kill switch — `any(fence_flags[:i])`
   suppressed every count below the first fence anywhere in the file.
   Fixed: now tracks fence-close line indices and only exempts a count
   when a fence closed within `_FENCE_PROXIMITY_LINES` (5) lines above
   it.

canonical: `gates/record_lint.py:404-406,441` this session (diff applied
in this turn, quoted below)

2. `_INLINE_COMPUTED_LEADIN` over a 6-line window suppressed on any
   unrelated percent/equals sign (e.g. "set FOO=bar in config" above a
   bare tally). Fixed: the check now runs against the count's own line
   only, and the equals-sign half of the pattern requires a digit
   directly adjacent to it, not a bare equals sign.

4 new fixture tests added, each new misfire class covered both ways
(gates/test_record_lint.py):
- t_misfire_unrelated_fence_far_above_still_flagged_as_bare_count
- t_misfire_fence_close_within_proximity_not_flagged_as_bare_count
- t_misfire_unrelated_equals_above_still_flagged_as_bare_count
- t_misfire_digits_adjacent_equals_same_line_not_flagged_as_bare_count

canonical: this session's own pytest run, quoted immediately below
derived: `python3 -m pytest gates/test_record_lint.py -q`
```
..............................................................           [100%]
62 passed in 1.05s
```

derived: `python3 -m pytest gates/test_role_spec_shape.py gates/test_patrol_queue.py gates/test_precision_measure.py -q`
```
........................                                                 [100%]
24 passed in 0.98s
```

canonical: this session's own precision_measure sample/report run,
quoted below, plus manual read of the 2 rule-333 excerpts against
docs/issue-476/reports/execution-observation.md this session

Known precision cost of the tightened same-line requirement: the re-run
precision_measure sample surfaced 2 new rule-333 findings — a tally
whose equals-sign computation wraps across a markdown line break onto a
separate line reading:
```
0/3.
```
Both are judged FP under the Tricorder criterion (owner would take no
action) — a direct, expected consequence of restricting the signal to
the count's own line per finding 2 above. Not fixed here: doing so
would reopen the same blanket-suppression shape finding 2 refused.

canonical: PreToolUse hook output this session, board-gate refusal
quoted below

Finding 3 (acceptance bullet 3, genuine test/->tests/ citation breaks):
attempted the fix directly in this session — editing
docs/issue-711/reports/implementation.md and
docs/issue-476/reports/implementation.md was refused, same boundary as
the earlier round:
```
board-gate: writing docs/issue-711/ requires branch issue-711/implementation (current: issue-1620/implementation).
```

canonical: PreToolUse hook output this session, gh-guard refusal quoted
below

Attempted to file follow-up GitHub issues for those two records' own
roles to pick up, per the review's explicit fallback instruction; this
was refused:
```
gh-guard: refused for role session 'implementation': issues are the user's requirement backlog, user-authored only (contract v3 s9) — no role touches them.
```

A role session cannot author GitHub issues under this repo's own
contract. Re-scoping explicitly here per the review's instruction:
acceptance bullet 3 remains open on this PR. The 4 genuine
test-to-tests citation breaks (docs/issue-711/reports/implementation.md,
docs/issue-476/reports/implementation.md) need either (a) the user to
file a follow-up issue for issue-711's and issue-476's own roles to fix
from their own branches, or (b) the user's direct authorization for a
cross-issue write. This session cannot close that gap itself.

Finding 4 (acceptance bullet 2, post precision_measure to issue #1620):
posted as an issue comment this session — see below.

derived: `python3 gates/precision_measure.py sample . --n 100 --seed 20260817 --out /tmp/samples_1620b.json`
```
wrote 9 sample items (population 9) to /tmp/samples_1620b.json
```

derived: `python3 gates/precision_measure.py report /tmp/samples_1620b.json --judgments /tmp/judgments_1620b.json`
```
population=9 sampled=9

| rule | sampled | TP | precision | wilson_lb_90 |
|---|---|---|---|---|
| issue-330 | 7 | 7 | 100.0% | 81.0% |
| issue-333 | 2 | 0 | 0.0% | 0.0% (KILL <70%) |
| overall | 9 | 7 | 77.8% | 56.6% |

pass rule: overall point>=90% AND wilson_lb_90>=85% AND no per-rule kill(<70%)
promote: NO
```

## What did not work

- First `_ABSENCE_NEGATION` draft used a same-line `[^.?!]{0,40}` gap
  between "no" and "needed"; testing it against
  `docs/issue-791/reports/implementation.md`'s live "no new
  `docs/issue-791/decisions/` entry needed" phrasing surfaced two
  problems at once — the phrase wraps across a markdown line break, and
  the cited path's own `.md` extension trips the `[^.?!]` exclusion —
  expected: same-line match; actual: no match on either count. Fixed by
  widening to a 3-line window and dropping the punctuation exclusion.
derived: manual read against two live records this session
- First `bare_count_claim_check` inline-computed detector only matched
  a literal `%` character on the same line before the count; testing it
  against two more live records surfaced the gap — a multiplication
  written out with an `=` sign rather than a `%`, and a tally backed by
  a fenced raw-output block roughly 30 lines above it, outside the
  original 6-line lookback — expected: both self-evidencing counts
  skipped; actual: both still fired. Fixed by adding `=` as a
  computed-shape signal and by making the fenced-block check scan the
  whole record above the claim, not just the immediate 6-line window.

## Test-tier note

canonical: `ls .on-the-record/test-tiers.json` this session — file
absent, no per-repo test-tier config exists in this repo. Ran targeted
tests only, per the instruction given for this task; did not measure
the full suite's wall-clock cost — noting this as a known tiering gap
rather than silently absorbing the test-tier directive's observe-only
measurement ask.

`derived: pytest gates/test_record_lint.py -q and gates/precision_measure.py sample+report output, both quoted above under "How this was verified" and "Acceptance bullet 2"`
## Acceptance verification
- claim — checked: gates/test_record_lint.py::t_bare_count_claim_check_still_fires_without_evidence — result: pass
- claim — checked: gates/precision_measure.py:sample-report-on-live-HEAD — result: pass
- claim — checked: docs/issue-711/reports/implementation.md — result: unverifiable: out of this session's write set, core/hooks/board-gate.sh refuses a write touching another issue's docs/issue-<n>/ tree from this branch (see "Genuine citation breaks" section above); filed as a deviation for that issue's own role

## Open findings

- Acceptance bullet 3 (4 genuine test/->tests/ citation breaks in
  docs/issue-711/reports/implementation.md and
  docs/issue-476/reports/implementation.md) remains open on this PR —
  see "PR #1622 review response" above. Neither a direct write nor a
  follow-up GitHub issue could be created from this session
  (board-gate.sh and gh-guard.sh both refuse it).

## Resolution path

- Acceptance bullet 3: the user files a follow-up issue for
  issue-711's and issue-476's own implementation roles (or explicitly
  authorizes a cross-issue write), naming the test/->tests/ citation
  fix in docs/issue-711/reports/implementation.md and
  docs/issue-476/reports/implementation.md.

## Next steps

None — loop_state is landed.

## Rationale for deviations

canonical: PreToolUse hook output this session (board-gate.sh refusal,
quoted above under "Genuine citation breaks")

The write set stayed inside `gates/record_lint.py` and
`gates/test_record_lint.py` for all rule-fix work. Acceptance bullet 3
asks this session to also fix the 4 genuine citation breaks in their
own issues' records, but `core/hooks/board-gate.sh` refuses a write
touching another issue's `docs/issue-<n>/` tree from
`issue-1620/implementation`, as quoted above. Per the SCOPE-EXCEEDED
rule this session stops at the boundary of its own write set instead
of widening into those issues' branches.

canonical: PreToolUse hook output this session, gh-guard refusal quoted
above under "PR #1622 review response"

Per PR #1622's review, a second attempt was made this session to file
follow-up GitHub issues for issue-711's and issue-476's own roles to
pick the citation fix up — refused by gh-guard.sh (role sessions cannot
author issues, contract v3 s9).

canonical: this record's own "Open findings" and "Resolution path"
sections above

Bullet 3 stays open, not closed.
