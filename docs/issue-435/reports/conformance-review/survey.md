# Conformance-review survey — issue #435's implementation

kind: record
loop_state: surveyed
upstream: docs/issue-435/reports/implementation.md
code_under_review:
- gates/test_closes_gate_ci.py
- tests/shape_contracts.py
- docs/handbooks/operations.md
- docs/issue-435/reports/implementation.md

## What was done

canonical: docs/issue-435/reports/implementation.md, read this session
— re-checked every falsifiable claim in the implementation record
against the current working tree (commit 336a7e3d, HEAD) by re-running
its cited commands live and reading the named code, rather than
trusting the record's own narration.

## Why

Issue #435 (this review's subject issue) is itself a landed
implementation with no conformance-review record yet, spawned via
`spawn_on_pr.py`'s PR-trigger path (issue #1360's scope: only
subjects whose issue is still OPEN). Requirement basis is the
implementation record's own "How you'll know it worked" bar carried
over from the proposal: 13 named stub fixes, a new
`assert_stub_return_shape` check, and a doc default change, each
independently verifiable in the current tree.

## Per-claim verdicts

### Claim 1 — 13 `spawn._issue_comments` stubs fixed to `(list, bool)` shape — Present

derived: `grep -n "lambda repo, n:" gates/test_closes_gate_ci.py | grep -v ", True)" | grep -v "\[\], True"`, run this session:
```
816:    old_shape_stub = lambda repo, n: [{"login": "x", "body": "y"}]
```
canonical: same grep command, run this session — result: the sole
remaining bare-list stub is the deliberate old-shape fixture inside
the new demonstration test at gates/test_closes_gate_ci.py lines
808-825 (`t_issue_comments_stub_shape_contract_catches_old_pre_287_shape`),
not a leftover unfixed stub; every other `_issue_comments` stub in the
file returns the `(list, bool)` tuple shape.

### Claim 2 — masked second stub gap (`_issue_view_body` missing `## Acceptance`) fixed — Present

canonical: gates/test_closes_gate_ci.py lines 708-709, read this
session — `pr_reference._issue_view_body`'s stub in the
`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
test function returns a string containing "no plan checklist here"
followed by a "## Acceptance" heading and a check line naming this
same test file, matching the record's claim of an added Acceptance
section.

### Claim 3 — `assert_stub_return_shape` added, with one-level recursion into tuple/list elements — Present

canonical: tests/shape_contracts.py lines 42-83, read this session —
`_check_shape()` checks the outer container then recurses into
`tuple`/`list`/`set`/`frozenset` element types one level deep, and
`assert_stub_return_shape()` resolves `real`'s return annotation via
`inspect.signature(real, eval_str=True)`, matching the record's
description of both the base check and the resolved warrant-hunter
finding (recursion into element types) verbatim.

### Claim 4 — `docs/handbooks/operations.md` no-`--ignore=gates` default, both languages — Present

derived: `grep -n "ignore=gates\|pytest -q" docs/handbooks/operations.md`, run this session:
```
1060:전체 스위트를 돌릴 때는 `--ignore=gates` 를 붙이지 않는다(issue #435):
1066:python3 -m pytest -q
1086:Do not run the full suite with `--ignore=gates` (issue #435): that flag
1089:breaks again. Run `python3 -m pytest -q` with no ignore flag.
```
canonical: same grep command, run this session — result: both the
Korean and English self-check sections instruct `pytest -q` with no
`--ignore=gates`, matching the record's claim.

### Claim 5 — targeted test file, verified isolated — Present

canonical: `python3 -m pytest gates/test_closes_gate_ci.py -q`, run
this session — result:
```
54 passed in 0.89s
```
This tally covers the 13 fixed stubs and the two new/fixed tests named
in the record, with zero failures reported in this run.

### Claim 6 — full-suite `495 passed` acceptance figure — Unverifiable

canonical: `python3 -m pytest -q`, attempted three times this session
(background and foreground) — result: none of the three attempts
returned a tally within available turn time.

canonical: `ps aux`, run this session — result: 10+ concurrent
`pytest -q` / `pytest -q --ignore=gates` invocations from other
sessions on the same host were running at the same time as this
session's attempts, consistent with resource-contention timeouts
rather than a code defect in the reviewed files — Claim 5's narrower
run above, against the actual code_under_review, returned in under one
second with zero failures reported. canonical: this session's own
three attempts cited above — this session obtained neither a matching
nor a contradicting tally for the record's full-suite figure, so it is
carried here as unverified-neither-way.

### Claim 7 — closure_sweep test failure encountered mid-session — Out of scope, pre-existing

canonical: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_merge_gate.py gates/test_closure_sweep.py -q`,
run this session while investigating an unrelated subject before
recognizing the correct target for this review (see "What did not
work" below) — result:
```
FAILED gates/test_closure_sweep.py::MainExitCode::test_exit_code_is_2_and_prints_could_not_check
1 failed, 36 passed in 1.13s
```
canonical: same command, re-run this session against commit af3dd121
(pre-dating both issue #435 and issue #1360, via `git checkout
af3dd121 -- gates/closure_sweep.py gates/test_closure_sweep.py`) —
result: the identical failure reproduces there too, showing a
pre-existing gap where closure_sweep.py's main() has an unmocked
rate-limit pre-check that leaks through when the host's live gh API
rate limit is exhausted (this session's own `gh issue view 435` call
failed earlier in the turn with "API rate limit already exceeded").
Not caused by, and not in the code_under_review scope of, either issue
#435 or issue #1360's changes.

## Summary table

canonical: the per-claim verdicts above, this session — condensed
below; see each claim's own canonical/derived citations for the
executed-live evidence behind each verdict.

| Claim | Record's claim | Verdict |
|---|---|---|
| 1 | 13 stubs fixed to tuple shape | Present |
| 2 | masked `_issue_view_body` gap fixed | Present |
| 3 | `assert_stub_return_shape` + recursion fix | Present |
| 4 | operations.md no-ignore default, both languages | Present |
| 5 | reviewed file's own tests, isolated run | Present |
| 6 | full-suite 495-tally figure | Unverifiable (host contention) |
| 7 | (encountered, off-topic) closure_sweep test failure | Out of scope, pre-existing |

## What did not work

This session's task briefing quoted a spawn-template task string
identical in shape to issue #1360's own spawn template. canonical:
the task prompt at this turn's start, read this session — it named
issue #435 and `issue-435/implementation` literally, but this session
initially investigated issue #1360's `spawn_on_pr.py` changes as the
review subject before re-reading the literal issue number and running
`git branch`. Caught before any conformance-review content was written
for the wrong subject; the issue-1360 investigation (spawn_on_pr.py /
`_board_wide_sweep` review) was discarded, not reused here, since it
belongs to a different issue's own review.

## Open findings

canonical: the per-claim verdicts section above, this session (Claims
1-7 and their own citations) — no open findings; every claim in scope
for issue #435's code_under_review set reproduces against the current
tree per its own citation. Claim 6 is carried as Unverifiable per its
own section's reasoning above, not as an Incorrect finding.

## Resolution path

Not applicable — no open findings requiring a fix. Claim 6 can be
re-verified by any future session with an uncontended host running
`python3 -m pytest -q` directly.
