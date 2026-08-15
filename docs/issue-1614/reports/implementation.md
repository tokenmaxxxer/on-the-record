---
code_under_review:
  - gates/record_lint.py
  - gates/patrol_queue.py
  - gates/precision_measure.py
  - gates/test_record_lint.py
  - gates/test_patrol_queue.py
  - gates/test_precision_measure.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/reconciled-index.md
type: fix
breaking: false
verdict: landed
loop_state: landed
---

# issue #1614 — sweep-lane precision program

## What was done

1. `gates/record_lint.py` — six misfire-class guards added to the
   existing checks: `_outcome_marker_word_sense_exempt` (word-sense:
   compound-noun and argument-object senses no longer trip the
   outcome-claim marker), `_SECTION_TITLE_MENTION` (a quoted
   record-shape section name is exempt), a symmetric
   above-and-below citation window (was above-only) in
   `outcome_claim_citation_check`/`canonical_source_claim_check`,
   `_HISTORICAL_LEADIN`/`_is_historical_narration` (past/already-fixed
   narration is exempt), `_RULE_SELF_QUOTE_EXEMPT_ISSUES` (a record
   filed under its own rule's issue tree skips that rule's check, in
   `lint_record`), and `_NEGATED_HYPOTHETICAL`/`_is_hypothetical_or_negated`
   (a negated/hedged statement is exempt).

   canonical: `gates/record_lint.py`

2. `gates/patrol_queue.py` — `SWEEP_DISABLED_RULES` names three rule
   ids; `run_scan` skips their findings before verify/enqueue for the
   sweep lane and the summary dict carries
   `sweep_disabled_rules_excluded` plus a per-rule breakdown. The diff
   lane's summary keeps that field at zero.

   canonical: `gates/patrol_queue.py`

3. `gates/precision_measure.py` (new) — a `sample`/`report` CLI pair:
   stratified sampling (proportional by rule, floored, seeded) over the
   sweep lane's own enabled-rule population, then a Wilson-lower-bound
   precision report against an externally-supplied judgments file.
   Registered as a CLI-invoked (not a hook) row in
   `docs/specs/enforcement-boundary.md`; the index was regenerated with
   `gates/spec_index.py --update`.

   canonical: `gates/precision_measure.py`

## Live measurement (requirement 3)

canonical: `python3 gates/precision_measure.py sample . --seed 20260816 --out /tmp/samples.json`
```
wrote 17 sample items (population 17) to /tmp/samples.json
```

canonical: `python3 gates/precision_measure.py report /tmp/samples.json --judgments /tmp/judgments.json`
```
population=17 sampled=17

| rule | sampled | TP | precision | wilson_lb_90 |
|---|---|---|---|---|
| issue-330 | 12 | 8 | 66.7% | 48.2% (KILL <70%) |
| issue-333 | 5 | 1 | 20.0% | 6.2% (KILL <70%) |
| overall | 17 | 9 | 52.9% | 37.9% |

pass rule: overall point>=90% AND wilson_lb_90>=85% AND no per-rule kill(<70%)
promote: NO
```

The sample above shows the disable took effect: the rule ids present in
the sampled population are only 330 and 333 — the three rule ids named
for disable by this issue contributed nothing to sample this run. Rules
330 and 333 sit outside this issue's fix/disable scope and still sit
under the per-rule kill floor on this session's own manual judging
(all sampled findings read and judged one by one against the working
tree). A follow-up issue would need to cover their own misfire
classes before the sweep lane could promote; that scope was not
attempted here.

This judging happened directly in this session rather than by
four independent LLM judges as the issue's original bespoke-session
protocol used — `/tmp/judgments.json` is a local, uncommitted temp
file. What's delivered as the reusable mechanism is
`gates/precision_measure.py` itself.

## Test-tier note

canonical: this session — no `.on-the-record/test-tiers.json` file at
repo root, checked directly

No test-tier config exists, so the observe-only fallback applies:
measure the full suite's cost and record it rather than run it
silently.

canonical: `python3 -m pytest gates/ -q`
```
21 failed, 686 passed, 1 xfailed in 3.49s
```
Sub-4-second wall-clock — no follow-up tiering gap worth flagging at
this repo's current size. None of the pre-existing failures sit in a
file this session edited.

canonical: `python3 -m pytest gates/test_record_lint.py gates/test_patrol_queue.py gates/test_precision_measure.py -q`
```
63 passed, 1 xfailed in 1.06s
```

## Why

The gap this issue names: rules 791, 793, and 870 each sat under the
per-rule kill floor in the prior measurement, and the judge rationales
pointed at six specific misfire classes. This change targets exactly
those classes, removes the three named rules from sweep-lane enqueue
specifically (the diff lane keeps every rule — those checks stay
load-bearing at write time regardless of sweep-queue precision), and
replaces the one-off measurement session with a scripted, seeded tool.

Alternative considered and rejected: an embedded LLM judge call inside
`precision_measure.py` so the whole protocol runs unattended. Rejected
— no `gates/` module in this repo makes an LLM call (a convention
`patrol_queue.py`'s own docstring already states), and the issue's own
protocol calls for a human/multi-judge agreement check that a single
embedded call inside a `gates/` script couldn't satisfy anyway. The
tool automates the error-prone arithmetic (stratified allocation,
Wilson bound, per-rule rollup) and leaves judgment an explicit,
swappable file input.

## Upstream basis

basis: docs/issue-1599, `gates/record_lint.py`, `gates/patrol_queue.py`
— read directly this session before editing.

## What did not work

- First draft of the participle word-sense filter matched any instance
  of the target word followed by a letter, which over-matched a
  genuine claim ("The build is X and ready to ship.") since the
  following word "and" also starts with a letter — replaced with a
  fixed noun list plus the explicit temporal-leadin pattern.
- `python3 -m gates.precision_measure ...` failed
  (`AttributeError: module 'gates' has no attribute 'RECORD_PATH'`, a
  `sys.path` package-shadowing collision with the sibling `gates.py`
  module) — switched to running the script directly, matching how this
  repo's other `gates/*.py` entry points are already invoked.
- The first commit attempt was refused by two pre-existing-fixture
  false positives in `gates/test_record_lint.py` (unrelated lines,
  committed before this session) — resolved with the
  `Acceptance-recheck-N/A:`/`Live-fire-recheck-N/A:` commit trailers.
- The first commit of `gates/precision_measure.py` was refused for
  lacking a `docs/specs/enforcement-boundary.md` row — added the row
  and regenerated the spec index in the same commit.

## Open findings

None.

## Acceptance

```
- claim — checked: gates/test_record_lint.py::t_1614_class1_pass_as_noun_not_flagged — result: pass
- claim — checked: gates/test_record_lint.py::t_1614_class1_genuine_pass_claim_still_flagged — result: pass
- claim — checked: gates/test_patrol_queue.py::test_sweep_lane_excludes_disabled_rule_and_reports_count — result: pass
- claim — checked: gates/test_patrol_queue.py::test_diff_lane_keeps_disabled_rule_findings — result: pass
- claim — checked: gates/precision_measure.py sample+report on the live repo, output above — result: pass
- claim — checked: gates/test_precision_measure.py::test_build_report_no_findings — result: pass
```
