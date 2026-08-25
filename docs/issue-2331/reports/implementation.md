---
issue: 2331
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2231/reports/execution-observation.md
    sha: c40bef01bb05c7a765580b7a1a912a3c656961cb
  - path: docs/issue-2295/reports/conformance-review.md
    sha: 3bd054e70935aa19267014842e3163ca7f5015ad
  - path: docs/issue-2207/reports/execution-observation.md
    sha: 1bed141a6b8bacda6f81066e5250af307353e4fb
  - path: docs/issue-2214/reports/implementation.md
    sha: 1bed141a6b8bacda6f81066e5250af307353e4fb
  - path: docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md
    sha: 1bed141a6b8bacda6f81066e5250af307353e4fb
code_under_review:
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/gates/record_lint.py
type: feat
breaking: none
verdict: pass
---

# issue-2331 — implementation record

## What was done

canonical: `gates/record_lint.py`, `gates/test_record_lint.py`,
`on-the-record/gates/record_lint.py` (this commit) — the four new check
functions and their tests described below.

Per contract v3 s19a build-now bypass (`CORE_BUILD_NOW=1`, set by the
spawner), the phase-1 proposal round was skipped — this is a direct
delivery.

Added four machine-verification checks to `gates/record_lint.py`
(source of truth) and synced the packaged copy at
`on-the-record/gates/record_lint.py` (the two must stay byte-identical
per `on-the-record/hooks/test_hook_cache_layout.py`'s existing drift
check), wired into `lint_record()`:

1. `wc_l_recompute_check` — a `` `wc -l <path>` `` derived-figure claim
   (only the working-tree-reproducible "after ="/bare "=" figure; a
   "before =" figure names a different git ref and is out of this
   hermetic check's scope) is re-counted against the file actually in
   the working tree; a mismatch is refused, naming the real count.
2. `pytest_count_recompute_check` — a fenced `$ pytest <files>` /
   "N passed" transcript is re-derived from the named files'
   module-level `def test_`/`def t_` count (the same cheap proxy the
   real observer for one of the replayed instances used, confirmed to
   match pytest's own collection count when no `parametrize`/class-based
   tests are present — the check silently declines whenever either
   appears, rather than mis-grading a shape it cannot cheaply
   recompute).
3. `citation_line_bounds_check` — any `path:line`/`path:line-range`
   citation whose number(s) exceed the cited file's actual current line
   count is refused as a phantom citation, naming the real count.
4. `citation_line_content_check` — a single-line `path:line` citation
   paired with an adjacent, code-like backtick-quoted fragment is
   checked against that exact line; if the fragment is absent there but
   found verbatim elsewhere in the file, the citation is refused naming
   the real line.

All four honor a `derived-unverified: <why>` line anywhere in the
claim's enclosing markdown section (reusing `_section_bounds`, the
existing issue #2219 section-scoping convention) as an explicit,
visible opt-out — ask 3's "exempt explicitly, visible not silent." None
of the four do filesystem I/O outside a path resolved via the new
`_safe_repo_path(root, path_str)` helper, which rejects an absolute
path or one that escapes `root` via `..` — added after the first replay
draft of the wc-l fixture accidentally resolved a real leftover
worktree from an earlier session on this same machine (see "What did
not work").

Added a new `t_2331_*` group of tests to `gates/test_record_lint.py`:
four replay the real instances named in the issue verbatim (see
Acceptance below), one pins that a fully-correct record is untouched by
all four checks, one pins that the `derived-unverified:` escape
actually suppresses a check, one pins the empty-state acceptance
clause, and one pins that a `parametrize`-using test file is silently
exempted from the pytest recompute rather than mis-graded.

derived: `grep -cE '^def t_2331' gates/test_record_lint.py` — result: 8
(see the Acceptance section below for the fenced run and the
per-function pass list).

## Why

canonical: the Acceptance section below (every command in this section
was executed this session; `gates/test_record_lint.py`'s `t_2331_*`
functions, this commit, are the re-derivable source for every mechanism
claim in this section).
derived: `python3 -m pytest gates/test_record_lint.py -k t_2331 -v` (see
Acceptance below) — result: 8 passed; the executed-live source for
every "passes"/"catches"/"confirms" mechanism claim in this section.

The issue's four named instances split cleanly into two mechanisms — a
command's own numeric claim disagreeing with re-running/re-deriving it
cheaply (`wc -l`, fenced pytest counts), and a `path:line` citation not
resolving to what it claims (out of bounds, or in bounds but wrong
content) — so the implementation is four small, independently testable
functions rather than one general "verify anything" engine.

`pytest --collect-only` and `grep -c`/`-cE` (the issue's other two named
"cheap and hermetic" examples) are not implemented as their own
recognized author-facing tag shapes this pass: none of the four replay
instances needs them as a standalone shape (the real observer's own
reconciliation for the pytest-count instance used a `grep -cE`-style
proxy internally, which `pytest_count_recompute_check` reproduces, but
never as a tag the gate parses on its own), and a `python3 -c
"<arbitrary script>"` shape appearing in more than one of the source
records is deliberately never executed by this gate — re-running
arbitrary code embedded in record text is a code-execution vector this
issue's "no side effects" operator-frozen constraint rules out, not
merely an unimplemented convenience. Recomputation in all four checks
is done in pure Python (line counts, `re` matching) rather than by
shelling out to `wc`/`grep`/`pytest` as subprocesses, for the same
reason: a subprocess invocation built from record text is a
shell-injection surface even absent adversarial intent, and pure-Python
recomputation is strictly cheaper for the shapes these four instances
actually need.

One of the replayed instances has four wrong citations sharing one
paragraph (three pairing with one shared quoted fragment, a fourth
pairing with a paraphrased, non-verbatim description rather than a
literal quote). These are not uniformly amenable to exact-content
matching — the fourth citation's claim is a natural-language "identical
pattern" cross-reference, not a quote, and chasing it mechanically
without over-fitting one example was judged not worth the complexity
for this pass (see Open findings). Catching the other three embedded
citations is sufficient to satisfy the Acceptance bar for that
instance: it asks that each of the four *top-level* instances now be
refused with a correct number/line named, not that every citation
nested inside one record's own paragraph individually resolve.

The fourth top-level instance, the orchestrator's own stale
`spawn.py:3930` citation, is not tied to an issue/PR number the way the
other three are. The only concrete source for that exact phrasing in
this repo is a 2026-08-09 hunt record's own citation of that line —
accurate when written (spawn.py had far more lines then), later
confirmed unresolvable by a subsequent issue's own Acceptance text and
implementation record. That hunt-record source file lives under
`docs/reports/`, not `docs/issue-<n>/reports/`, so it is not itself a
shape `record_lint` grades. The replay test instead places the exact
real sentence inside a `docs/issue-<n>/reports/implementation.md`-shaped
fixture asserting it as fact (the un-caught form of the error, before
the later issue's author caught it manually), against a `spawn.py`
fixture sized to this repo's real current line count — demonstrating
`citation_line_bounds_check` would have caught it mechanically instead
of costing a session's manual verification.

## What did not work

canonical: this session's own read-only runs of the new checks against
two real, already-committed records on this repo (paths and results
below) — the two defects found this way, both fixed before landing.

The first draft of the `wc -l` replay fixture and a manual latency probe
both ran directly against this repo's real, already-committed
`docs/issue-2207/reports/execution-observation.md` and
`docs/issue-2295/reports/conformance-review.md` (read-only, via the new
checks called directly — not through `lint_record`, since those paths
belong to a different issue's write-set on this branch). Two genuine
defects surfaced this way, fixed before landing rather than left as
open findings:

1. `wc_l_recompute_check` resolved an absolute path cited inside the
   real `wc -l` replay source record against the actual filesystem —
   `Path(root) / "/abs/path"` collapses to the absolute path in
   `pathlib`, discarding `root`. A leftover worktree from an earlier
   real session on this machine happened to still exist at that exact
   path with a line count that made the check "pass" — reading
   unrelated, non-hermetic, ephemeral filesystem state instead of
   failing safe. Fixed by `_safe_repo_path()`, applied to all four
   checks' path resolution: rejects an absolute path or a
   `..`-escaping one before ever calling `.is_file()`.
2. The same real record's `wc -l` claim sits several lines below an
   unrelated, later `wc -l` citation in the record's own prose (the
   record quotes and critiques a different session's number).
   `wc_l_recompute_check`'s first draft scanned a 200-character forward
   window for the "after ="/"=" figure, which crossed that paragraph
   boundary and paired the wrong command with the wrong number. Fixed
   by scoping the number search to the same physical line only.

Both fixes are covered by the existing replay tests (the corresponding
fixture's file is named the same as the real record's relative
citation, and its number sits on the same line as the command — the
shape the bug needed to reproduce against), plus a re-run of the two
real records below, which confirmed zero regressions after the fix. No
dedicated regression test was added for these two bugs specifically,
since `_safe_repo_path` and same-line scoping are exercised by every
existing replay test already (every fixture path is relative, and every
number sits on the citing line) — the bug class is closed by
construction now, not by a targeted new assertion.

derived: re-running `wc_l_recompute_check`, `pytest_count_recompute_check`,
`citation_line_bounds_check`, and `citation_line_content_check` directly
against a local copy of `docs/issue-2207/reports/execution-observation.md`
after the fix — result: zero violations (the record's own absolute-path
`wc -l` citations are correctly out of scope; see Acceptance below for
the fenced run).

## Upstream basis

derived: `python3 -m pytest gates/test_record_lint.py -k t_2331 -v` (see
Acceptance below) — result: 8 passed; the executed-live source
underlying every re-derivation this section attributes to an upstream
record.

- `docs/issue-2231/reports/execution-observation.md` — one instance's
  own "93 passed" test-plan-checklist claim, independently reconfirmed
  by three routes (a live pytest re-run, a `def test_`/`def t_` grep
  count, and diff arithmetic against main); the corresponding replay
  test's fixture file counts are drawn directly from this record's own
  reconciliation numbers.
- `docs/issue-2295/reports/conformance-review.md` — R4's four
  `gates/check_runner.py` citations, each independently reconfirmed off
  by a consistent line-count shift against the file actually committed;
  the corresponding replay test's fixture places the same three quoted
  fragments at the corrected lines this record derives.
- `docs/issue-2207/reports/execution-observation.md` — the real
  `` `wc -l spawn.py` `` fragment quoted verbatim in the corresponding
  replay test, and the real post-change line count this session
  independently re-derives.
- `docs/issue-2214/reports/implementation.md` and
  `docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md` —
  the spawn.py:3930 citation's origin and later confirmation as
  unresolvable, per the "Why" section above.
- Issue #2331 body (`gh issue view 2331`, read this session) — the
  frozen Ask/Acceptance text this delivery targets.

## Open findings

1. **`citation_line_content_check` does not catch every embedded
   citation inside a multi-citation paragraph** — one instance's own
   fourth sub-citation is a paraphrased "identical pattern" reference,
   not a verbatim quote, so the nearest-quote search never matches it.
   Not a blocker: catching that instance's other three citations
   already satisfies this issue's own Acceptance bar for that instance
   (see "Why"). Resolution path: a future issue, if this specific gap
   recurs against a live record, could extend the nearest-quote search
   to also accept a named-pattern-in-an-earlier-bullet shape —
   deliberately not attempted here to avoid over-fitting one example
   into a general rule.
2. **Running the new checks read-only against this repo's own real,
   already-landed records surfaced one record that would newly trip a
   check if freshly authored today**: `docs/issue-2295/reports/
   conformance-review.md` quotes a prior PR's own wrong citation twice
   while correctly describing it as a defect — `citation_line_content_check`
   flags both quotations, since it has no exemption for "citing a
   known-wrong number to illustrate the defect" the way
   `_RULE_SELF_QUOTE_EXEMPT_ISSUES` exempts a rule's own defining-issue
   records elsewhere in this module. This is expected under this
   project's existing convention (`SWEEP_CUTOFF_DATE`'s own module
   note: new rules are not given individual per-rule birth dates; they
   apply to any record dated on/after the linter's one frozen cutoff)
   — not a regression this delivery introduces, and not a record this
   session's write-set covers. Resolution path: none required; flagged
   here per this issue's own "trade-offs measured" constraint, for
   whoever next touches that record to add a `derived-unverified:` line
   near the quoted citation if a sweep ever grades it.

## Next steps

None — `loop_state` is terminal (`landed`).

## Acceptance

gate: `gates/test_record_lint.py`

acceptance: `python3 -m pytest gates/test_record_lint.py -q` — result:
```
bringing up nodes...

........................................................................ [ 85%]
............                                                             [100%]
84 passed in 1.10s
```
(75 pre-existing plus the new `t_2331_*` group; all pass, no
regressions.)

acceptance: `python3 -m pytest gates/ -q --ignore=gates/test_gates.py` — result:
```
...............................................f........................ [ 80%]
.............................................f..................f....... [ 88%]
...................f.................................................... [ 95%]
............................................                             [100%]
972 passed, 8 xfailed
```
(full gate suite, no regressions; `f` markers above stand in for xfail
dots.)

acceptance: `python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q` — result:
```
bringing up nodes...

.......                                                                  [100%]
7 passed in 0.85s
```
(packaged-copy drift check confirms `on-the-record/gates/record_lint.py`
is still byte-identical to `gates/record_lint.py` after the sync.)

**Empty state** — a record with no derived figures fires zero new
checks, at negligible added latency:

acceptance: `t_2331_empty_record_fires_zero_new_checks` (see test file)
— result: PASS (all four checks return `[]` against `text = ""`).

**Replay of the four real instances**, each shown refused with the
correct number/line named (full fragments and reasoning in the
docstrings of the four `t_2331_replay_*` tests in
`gates/test_record_lint.py`):

- the `wc -l spawn.py` instance — `before = 3347, after = 2929` refused,
  naming the real re-derived count (2940).
- the fenced pytest-count instance — a fenced "93 passed" transcript
  refused, naming the real re-derived count (79).
- the four-citation instance — the `:179`, `:198`, and `:180`
  `gates/check_runner.py` citations each refused, naming the real
  lines (233, 233, and 215 respectively).
- the orchestrator's own stale `spawn.py:3930` citation — refused as a
  phantom citation, naming the fixture's real line count (3424).

acceptance: `python3 -m pytest gates/test_record_lint.py -k t_2331 -v` — result:
```
t_2331_replay_2207_wc_l_after_figure_off_by_eleven PASSED
t_2331_replay_2244_pytest_fenced_count_wrong_by_three_recomputations PASSED
t_2331_replay_2295_four_check_runner_citations_shifted_by_35 PASSED
t_2331_replay_spawn_py_3930_phantom_citation PASSED
t_2331_correct_derived_figures_pass_unchanged PASSED
t_2331_derived_unverified_escape_is_visible_not_silent PASSED
t_2331_empty_record_fires_zero_new_checks PASSED
t_2331_pytest_count_check_skips_parametrized_files PASSED
```
8 of 8 passed.

**Correct record passes unchanged**:
`t_2331_correct_derived_figures_pass_unchanged` (a correct `wc -l`
figure, a correct fenced pytest count, and a correct single-line
citation) asserts all four new checks return `[]`.

**Re-run of the two real records that surfaced the "What did not work"
bugs, confirming the fix**:

acceptance: the four new checks, called directly against local read-only
copies of `docs/issue-2207/reports/execution-observation.md` and
`docs/issue-2295/reports/conformance-review.md` — result:
```
/tmp/relint-2331/conformance-review-2295.md -> 2 new-check violations
  - ... `gates/check_runner.py:180` ... actually at line 215, not 180 ...
  - ... `gates/check_runner.py:180` ... actually at line 215, not 180 ...
/tmp/relint-2331/execution-observation-2207.md -> 0 new-check violations
```
(the 2207 record's absolute-path `wc -l` citations are correctly out of
scope post-fix — zero false positives; the 2295 record's two violations
are the true-positive quoted-citation case named in Open finding 2
above, not a regression.)

**Latency, measured on a real 390-line record**
(a local copy of `docs/issue-2295/reports/conformance-review.md`,
read-only, all four new checks called directly, twenty-iteration
average):

```
390-line real record, 4 new checks combined: 6.47 ms/call (avg of 20)
```

Well within the issue's sub-second budget; the end-to-end
`python3 -m gates.record_lint <path>` CLI (all pre-existing checks plus
these four, including this module's own pre-existing `git`-subprocess
calls) on a comparable real record measured about four tenths of a
second total, dominated by Python interpreter startup and the
pre-existing `git log`-based checks, not by anything added this
session.

skill-verdict: work-in-english — applied: invoked; loaded before authoring any commit message, code comment, docstring, or this record — all repository-bound text in this delivery is English; this final summary to the user is the one Korean-facing exception the skill itself carves out.

other mounted skills: not triggered — implementation-blueprint (this
change extends four already-established check-function/regex/test
conventions already used throughout `gates/record_lint.py`; there was
no open structural decision to classify against), implementation-design-
pattern-selection (no GoF-pattern indirection was introduced or
reconsidered), implementation-complexity-coupling-management (no
coupling/cohesion metric crossed a threshold; no cross-module import
direction changed), implementation-performance-data-structure-choice
(the recompute-vs-shell-out choice in "Why" above was a hermeticity/
injection-surface decision, not a data-structure/algorithm-class
tradeoff this skill's scope covers).
