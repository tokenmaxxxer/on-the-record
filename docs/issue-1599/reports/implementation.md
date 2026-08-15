---
code_under_review:
  - gates/record_lint.py
  - on-the-record/gates/record_lint.py
  - gates/test_record_lint.py
type: bugfix
breaking: false
verdict: landed
loop_state: landed
---

# issue #1599 — record_lint precision fixes

## What was done

canonical: gates/record_lint.py, as committed on this branch this
session, read directly.

Four fixes to `gates/record_lint.py` (and its deployed mirror
`on-the-record/gates/record_lint.py`, kept identical — the module's own
docstring at `gates/record_lint.py:33` states they are meant to be the
same source), each with a fixture regression test in
`gates/test_record_lint.py`:

1. **`_PATH_REF` line-suffix bug** (`gates/record_lint.py:68-77`): added
   `_LINE_SUFFIX`/`_strip_line_suffix` and applied it in
   `orphaned_path_reference_check` and `git_tracked_path_reference_check`
   before the existence/git-log check, so `` `docs/specs/approvers.md:2` ``
   resolves to the real file instead of being reported broken.
2. **Pre-rule cutoff for sweep mode**: added `SWEEP_CUTOFF_DATE =
   "2026-08-09"` (the linter's own first commit —
   derived: `git log --diff-filter=A --format='%H %ci' -- gates/record_lint.py | tail -1`
   → `0dea23a5 2026-08-09 01:11:43 +0900`) and `_last_authored_date`.
   `find_records(root, sweep_cutoff=True)` (default on) now skips a
   record whose most recent commit predates that date — a single
   linter-wide cutoff, not a per-rule birth date (rationale at
   `gates/record_lint.py:518-525`: the checks have each grown since
   0dea23a5, and a per-rule date would need per-check tracking for a
   precision problem one conservative cutoff already fixes). Single-record
   `lint_record(path)` (the write-time `record-claim-guard.sh` path) is
   not touched — the cutoff only applies to the whole-repo/sweep walk.
3. **Six misfire-class exclusions**, one fixture test each: (a)
   YAML-frontmatter metadata lines (a `loop_state:` field set to a
   terminal value) — added `_structural_skip_mask` (frontmatter block,
   `#` heading, `>` blockquote) and wired it into
   `outcome_claim_citation_check`, `canonical_source_claim_check`,
   `bare_count_claim_check`, `defect_claim_grounding_check`; (b) section
   headings — extended the heading-skip already present in the
   outcome/defect checks to `canonical_source_claim_check`, which lacked
   it; (c) blockquoted claims from other documents — same
   `_structural_skip_mask`; (d) hyphenated names read as ratios
   ("layer-2/3") — `_COUNT_RATIO` gained a `(?<!-)` lookbehind so a digit
   immediately preceded by a hyphen never starts a ratio match; (e) the
   CLI-flag verb (`--pass-through`-style flag names) — `_OUTCOME_CLAIM_MARKER`
   and `_STATE_CLAIM_MARKER` gained `(?<![-\w])`/`(?![-\w])` lookarounds so
   a marker word glued to a hyphen (part of a flag or compound token)
   doesn't match; (f) counterfactual sentences ("had this round found...")
   — added `_COUNTERFACTUAL_LEADIN` and skip lines matching it in
   `outcome_claim_citation_check`, `canonical_source_claim_check`,
   `defect_claim_grounding_check`.
4. **Commit-pinned citation recognition**: added `_COMMIT_PINNED_CITE`
   (`<7-40 hex sha>:<path>:<line>`) and accept it as evidence — alongside
   the existing `canonical:`/`derived:` tag paths — in
   `outcome_claim_citation_check` and `canonical_source_claim_check`.

## Why

canonical: gh issue view 1599, read this session.

Issue #1599's own measurement: a 40-entry hand-graded sample from the
#1582 sweep queue scored TP 6 / FP 34 (15% precision), against the 90%
admission bar in `docs/reports/product/priorities.md`. Each fix targets
a root cause the issue text lists in its "Root causes to fix" section;
scope stayed to those four items only.

## Upstream basis

`0dea23a5` (`gates/record_lint.py`'s first commit, 2026-08-09) for the
sweep-cutoff date; issue #1599's body for the four fix areas and the
misfire-class list.

## Acceptance verification

canonical: acceptance: `python3 -m pytest gates/test_record_lint.py -q` — result: PASS

- checked: `python3 -m pytest gates/test_record_lint.py -q` — result: pass
```
...........................................x.........                 [100%]
35 passed, 1 xfailed in 0.94s
```
(the 1 xfail, `t_orphaned_path_reference_check_false_positives_documented_gap`,
predates this change — issue #744's own deferred-scope note, unrelated
to #1599's four fix areas — and is unrelated to it.)

canonical: acceptance: `python3 gates/patrol_queue.py scan . --lane sweep` (run twice, before/after this fix, on this session's own working tree) — result: PASS

- checked: whole-repo sweep re-run, before vs. after this fix — result: pass

  derived: `git stash && python3 gates/patrol_queue.py scan . --lane sweep`
  (before, this fix stashed out):
  ```
  {
    "lane": "sweep", "scanner": "record_lint",
    "raw_findings": 3023, "verified": 2929, "verify_dropped": 94,
    "enqueued": 200, "budget_truncated_scanners": 1, "queue_size": 183
  }
  ```
  derived: `git stash pop && rm -rf .on-the-record && python3 gates/patrol_queue.py scan . --lane sweep`
  (after, this fix restored):
  ```
  {
    "lane": "sweep", "scanner": "record_lint",
    "raw_findings": 548, "verified": 523, "verify_dropped": 25,
    "enqueued": 200, "budget_truncated_scanners": 1, "queue_size": 199
  }
  ```

  `raw_findings`/`verified` are the honest before/after delta —
  3023→548 raw (an 82% drop, derived from the two fenced command outputs
  above), 2929→523 verified (also an 82% drop, same source). `queue_size`
  is not treated as the delta signal here: both runs hit the scanner's
  200-item per-scan enqueue cap (`budget_truncated_scanners: 1`), and
  this comparison used two independent fresh queues — no prior
  `.on-the-record/findings/queue.jsonl` existed anywhere in this
  worktree or its git history before this session ran the scan, so the
  issue's stated "183 open findings" baseline could only be re-derived
  from a fresh scan (the "before" run above), not read back as an
  accumulated, previously-dismissed queue.

  unverifiable: the issue's originally-graded 183-entry queue file
  itself is not present in this worktree or its git history — it must
  have lived only in the scanning environment that produced it, so the
  40-entry hand-graded precision sample from the issue body cannot be
  re-graded against these exact same findings; the raw/verified count
  drop derived above is the reproducible substitute measured this
  session.

## What did not work

- First attempt at `python3 gates/patrol_queue.py scan . --lane sweep`
  (no prior queue file, 2-minute default timeout) timed out — the
  `git_tracked_path_reference_check` git-log subprocess call, run once
  per unique path reference across 622 record files, is expensive at
  this scale. Re-ran with a 10-minute timeout, which finished both the
  before (2m43s) and after (1m50s) scans.

## Rationale for deviations

None — implementation matched the issue body's four fix areas and
acceptance criteria; no scope-exceeded stop, no proposal-stated
alternative swap. This session treated the issue's four numbered,
CONFIRMED-or-enumerated root causes as leaving no open design decision
(the scout-directive's pure-bugfix skip condition) and went straight to
implementation without a phase-1 proposal round.

## Open findings

None.
