---
issue: 3182
role: implementation-blueprint+test-derivation+conformance-review-traceability-and-evidence-b553be9c
author: implementation-blueprint+test-derivation+conformance-review-traceability-and-evidence-b553be9c
skills: implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), conformance-review-traceability-and-evidence (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 8550d99697a55f4d8799507f08f54f4f37fea5d5
type: repair-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: scripts/preflight/consumer_preconditions.py
    sha: same-commit
  - path: tests/test_issue_3182_citation_line_accuracy.py
    sha: 8550d99697a55f4d8799507f08f54f4f37fea5d5
---

# issue-3182 — implementation-blueprint+test-derivation+conformance-review-traceability-and-evidence-b553be9c record

## What was done

PR #3087 shifted line numbers inside `spawn.py` (unrelated change:
canonical: `git log --oneline --all --grep '#3087'` output —
`b6f5eb05 issue-3061: standing delegation as machine-visible state (#3087)`),
which drifted 6 of 16 `line_anchors` tuples in
`scripts/preflight/consumer_preconditions.py`. This broke two tests on
`main`.

acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` (before repair) — result:
```
2 failed, 8 passed
posix_fork_support: spawn.py:4639 does not contain 'os.fork()' as real code -- actual line: comment (이슈 #2382 ...)
posix_fork_support: spawn.py:2668 does not contain 'os.fork()' as real code -- actual line: print("(부분적으로 확인된 위반)")
workspace_disk_headroom: spawn.py:729 does not contain 'def _spawn_capacity_check' as real code -- actual line: MIN_FREE_BYTES_DEFAULT = ...
workspace_disk_headroom: spawn.py:740 does not contain 'shutil.disk_usage' as real code -- actual line: probe = Path(path)
workspace_disk_headroom: spawn.py:745 does not contain 'sys.exit(' as real code -- actual line: except OSError:
workspace_disk_headroom: spawn.py:3229 does not contain '_spawn_capacity_check(work)' as real code -- actual line: unrelated comment
```
That second failing test's assertion enumerates every failing anchor in
one run (not just the first), which is how the complete 6-anchor list
above was obtained in a single pass rather than iteratively.

canonical: `grep -n "os.fork()" spawn.py` output — `2702:            child_pid = os.fork()` and `4704:            child_pid = os.fork()`
(also confirmed by reading surrounding context: `_spawn_one()`'s real
spawn path starts at `def _spawn_one` spawn.py:3856, containing the
os.fork() at 4704; the background validity-consult mirror contains the
os.fork() at 2702). Same method (`grep -n` for the exact expected
substring, then `Read` the surrounding function to disambiguate) located
the other 4 drifted anchors. Corrected all 6 `line_anchors` tuples in
`scripts/preflight/consumer_preconditions.py`, plus the matching line
numbers in the human-readable `source` prose strings (not mechanically
tested, but left accurate rather than stale):

| check | anchor | old line | new line |
|---|---|---|---|
| posix_fork_support | `os.fork()` (real spawn path, inside `_spawn_one`) | 4639 | 4704 |
| posix_fork_support | `os.fork()` (background consult mirror) | 2668 | 2702 |
| workspace_disk_headroom | `def _spawn_capacity_check` | 729 | 733 |
| workspace_disk_headroom | `shutil.disk_usage` | 740 | 744 |
| workspace_disk_headroom | `sys.exit(` | 745 | 749 |
| workspace_disk_headroom | `_spawn_capacity_check(work)` call site | 3229 | 3294 |

`scripts/preflight/consumer_preconditions.py`'s behavior (the `fn`
callables, remedy text content, check ordering) is unchanged — only the
numeric anchors and their prose line references moved
(derived: `git diff 8550d99697a5^..8550d99697a5 -- scripts/preflight/consumer_preconditions.py` shows only `source`/`line_anchors` value changes, no `fn`/`remedy`/ordering lines touched).

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` — result: 12 passed
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` — result: 4 passed
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` — result: 4 passed
acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` (after repair) — result: 10 passed (all 16 anchors verified live via `test_every_cited_line_contains_the_call_it_claims`, discrimination property re-verified via `test_all_sixteen_real_anchors_still_pass` plus the 4 synthetic comment/docstring/string-literal fixture tests, all passing)
acceptance: `python3 -m pytest tests/ -q` — result: 512 passed, 2 warnings (matches the pre-break baseline of 512 passed stated in the task; the 2 warnings are a pre-existing, unrelated `pinned-fixture-divergence` UserWarning from `test_skill_candidates_floor.py`, not a failure)

## Why

The task framed this correctly: the citation test caught real drift and
did its job, so the fix is to correct the anchors, not to touch the test
or the checked script's behavior. Reading each drifted line's context
(not just grepping for the target string) mattered because `os.fork()`
appears twice in `spawn.py` for two different features — a blind
first-match grep could have re-anchored both `posix_fork_support` entries
onto the same call site, silently collapsing a citation that is
deliberately pointing at two distinct code paths.

## What did not work

None.

## Rationale for deviations

None — the delivered work matches the round's scope exactly (repair the
6 drifted anchors, verify all sixteen and the discrimination property,
answer the line-pinning-shape question, restore green; no replacement
mechanism implemented, per instruction).

## Upstream basis

- `scripts/preflight/consumer_preconditions.py` — the file carrying the
  repaired `line_anchors` (this commit).
- `tests/test_issue_3182_citation_line_accuracy.py` (already on `main`,
  unmodified this round) — the mechanical check that caught the drift and
  proves the discrimination property (comment/docstring/string-literal
  rejection) still holds after the repair.
- PR #3087 (already merged to `main`) — the unrelated `spawn.py` change
  that caused the drift; not modified or re-reviewed here.
  canonical: `git log --oneline --all --grep '#3087'` output —
  `b6f5eb05 issue-3061: standing delegation as machine-visible state (#3087)`.

## Open findings

1. During this round's `Read` calls on `spawn.py`, a `lint-test-on-edit`
   hook note (canonical: this session's own `PostToolUse:Read` hook
   output attached to a `Read spawn.py` tool call this turn) reported
   `test/test_bootstrap_signal_guard.py:382`
   (`BootstrapSignalGuardReviewGapsTest::test_signal_after_session_log_before_disarm_does_not_delete_workspace`)
   as already-confirmed-failing during its background scan. Re-run in
   isolation this round to check:
   acceptance: `python3 -m pytest test/test_bootstrap_signal_guard.py::BootstrapSignalGuardReviewGapsTest::test_signal_after_session_log_before_disarm_does_not_delete_workspace -q` — result:
   ```
   1 passed in 30.86s
   ```
   It did not reproduce, is unrelated to
   `line_anchors`/`consumer_preconditions.py`, and lives under `test/`
   (not `tests/`, the suite this round's acceptance criteria and the
   512-baseline scope). No action taken; noted in case the hook's
   background scan signal recurs elsewhere.
2. The line-pinning-shape question the incident raises: see below.

### The line-pinning-shape question

Anchors drift whenever code above them moves, and this repo lands many
PRs a day — this round's incident alone broke 6 of the 16 anchors
(derived: the anchor-repair table above) from a single unrelated PR
touching `spawn.py` for a different feature entirely. That is a high
drift rate for a mechanism whose entire job is precision.

**Is line-number pinning the right shape?** Only partially. Its strength
is exactly what let this round finish fast: a line number is cheap to
check (read line N, test a substring) and cheap to repair once located,
with no ambiguity about what passed or failed. But it ties the citation
to *absolute position in the file*, a property that has no relationship
to the thing actually being cited (which call resolves inside which
function) and shifts on every unrelated edit above it. The cost is not
borne once at write time — it recurs every time upstream code moves,
indefinitely, proportional to the file's churn rate rather than to
whether the citation is still true.

**Alternatives considered:**

- **Bounded-window search** (search a fixed number of lines around the
  last-known line instead of requiring an exact hit): cheapest possible
  change to the existing mechanism, but it is a band-aid, not a fix. The
  drift measured this round reached 65 lines (see the anchor-repair
  table above: 3229 to 3294, and 4639 to 4704) — any window wide enough
  to absorb that is wide enough to risk matching a comment, docstring,
  or copy-pasted mention elsewhere in the file, which is precisely the
  false-positive class the discrimination tests in
  `tests/test_issue_3182_citation_line_accuracy.py` (`CitationCommentAndStringDiscriminationTest`)
  were built to eliminate (canonical: this test file's own module
  docstring, lines 1-46, which narrates that exact history). Widening
  the window to make drift-tolerance easier would quietly reopen that
  hole. Rejected.

- **Content hash of the enclosing function**: store a hash of the cited
  function's body (or of the exact cited line's text) and flag drift
  when it no longer matches. This has the strongest detection power — it
  would catch a semantic change even if the line number happened to stay
  correct by coincidence. But it does not reduce the maintenance burden;
  it very likely increases it, since the hash breaks on any edit to the
  function (a rename of an unrelated local variable, a reformatted line,
  an added comment inside the body) even when the citation is still
  correct in spirit. It also loses the property that made this round's
  repair fast: a human or agent cannot look at a mismatched hash and know
  what to fix without extra tooling to regenerate and diff it. Higher
  engineering cost, and it trades one drift-annoyance for a worse one.
  Rejected as the primary mechanism.

- **Stable symbol name** (cite `(file, enclosing_qualified_name,
  expected_substring)`, resolve the named function/class's current line
  range via `ast` at check time, then search — with the same
  tokenize-based comment/docstring masking this suite already has —
  *within that bounded region* rather than the whole file): survives
  everything that does not rename or restructure the enclosing symbol,
  which covers the actual incident here — `_spawn_one`,
  `_spawn_capacity_check`, and the consult branch's containing function
  all kept their names across the drift-causing PR; only their line
  offsets moved (canonical: `grep -n "^def _spawn_one\|^def _spawn_capacity_check" spawn.py`
  output — `733:def _spawn_capacity_check`, `3856:def _spawn_one`, both
  names present and unchanged). It also naturally disambiguates the two
  `os.fork()` call sites this round had to reason about by hand:
  `_spawn_one` vs. the consult function *are* the two labels, so the
  citation stays precise without a human re-deriving which line is which
  after every drift. Cost is a one-time `ast`-based "resolve enclosing
  def/class by qualified name to a line range" helper, shared across all
  `CHECKS` entries; ongoing cost drops close to zero, since function
  renames are far rarer than line-shifting edits. Its failure mode — a
  rename or split of the enclosing symbol — is also the failure mode a
  human citation-reviewer would most want flagged anyway, unlike an
  unrelated line shift.

**Recommendation:** stable symbol name, not line number, as the
authoritative anchor going forward, with a human-facing line number kept
in the `source` prose as a *cache* regenerated by tooling (not
hand-maintained) rather than the asserted fact. This keeps the search
bounded to the enclosing function's body — preserving the precision this
suite's comment/docstring discrimination logic already fought for —
while eliminating the recurring, churn-proportional repair cost that
this round exists to pay off. Not implemented in this round per
instruction; this round's deliverable is the repair plus this
recommendation, not the replacement mechanism.

## Next steps

None required for this round: acceptance: all three of this round's
required checks and the full `tests/` suite pass (see `## What was done`
above). A follow-up issue could pick up the stable-symbol-anchor
mechanism recommended above, scoped to
`scripts/preflight/consumer_preconditions.py` and
`tests/test_issue_3182_citation_line_accuracy.py`.

skill-verdict: implementation-blueprint — not-applicable: pure line-number repair to an existing single-file data structure, not new multi-module code needing structural/architectural decisions.
skill-verdict: test-derivation — not-applicable: no new requirements/acceptance criteria to derive test cases from this round; the existing citation-accuracy test suite (already deriving from this issue's prior-round requirements) was reused as-is to verify the repair.
skill-verdict: conformance-review-traceability-and-evidence — invoked; applied: loaded to shape this record's evidence citations (the `acceptance:`/`canonical:`/`derived:`-tagged results above, and the upstream/anchor traceability table linking each of the 6 repaired anchors to its old and new line).
other mounted skills: not triggered
