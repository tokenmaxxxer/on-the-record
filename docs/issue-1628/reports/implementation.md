---
code_under_review:
  - gates/record_lint.py
  - gates/test_record_lint.py
type: fix
breaking: false
verdict: partial
loop_state: landed
---

# issue-1628 implementation record

## Skip record (scout-directive)
Scouting skipped: pure bugfix to an existing gate's regex
narration-exemption logic (rule #330 false-positive class), same shape
as the prior #1620/#1614 misfire fixes already present in this
function — no product-shaped design decision is open.

## What was done
1. `gates/record_lint.py`'s `orphaned_path_reference_check` (rule #330)
   gained a fourth narration exemption function,
   `_is_untracked_out_of_scope_narration`, matching the words
   untracked / out-of-scope / not-in-repo in the 3-line window around a
   cited path — mirroring the two exemptions already in the same
   function (rename narration, absence negation). This closes the FP
   the issue names, at issue-645's implementation record line 126,
   where a path is narrated as one of three untracked files left
   deliberately unedited — not a live reachability claim.
2. `gates/test_record_lint.py` gained both-ways fixtures:
   `t_orphaned_path_reference_check_exempts_untracked_out_of_scope_narration`
   (must not fire) and
   `t_orphaned_path_reference_check_still_fires_on_genuinely_missing_no_narration`
   (a missing path with no such narration still fires).

canonical: `gates/test_record_lint.py` (both new fixtures read back after write)
derived: `python3 -m pytest gates/test_record_lint.py -q`
```
64 passed
```

## Requirement 2 — could not be completed as scoped; denial recorded
The issue's Context section states the 2 unevidenced rule-333 tallies
are in the same record as the rule-330 FP (issue-645's implementation
record). That premise does not match the live tree.

canonical: `git log --all -p -- docs/issue-645/reports/implementation.md`
derived: `git log --all -p -- docs/issue-645/reports/implementation.md | grep -cE "[0-9]/[0-9]"`
```
0
```

That record has never carried a bare digit-slash-digit fraction, in any
commit on any branch.

canonical: `python3 gates/precision_measure.py sample . --out /tmp/samples_final.json` — result: PASS, run this turn — a live population scan shows the real two rule-333 findings live in a different issue's execution-observation record, not issue-645's implementation record:

derived: `python3 -m json.tool /tmp/samples_final.json`
```
{
    "population_size": 2,
    "sample": [
        {"id": "s0000", "rule": "333",
         "path": "docs/issue-476/reports/execution-observation.md"},
        {"id": "s0001", "rule": "333",
         "path": "docs/issue-476/reports/execution-observation.md"}
    ]
}
```

canonical: `python3 -m json.tool /tmp/samples_final.json` — result: PASS, the sample output directly above from this turn's own run — the two findings are absent from issue-645's implementation record entirely; they live in issue-476's execution-observation record instead.

The issue's `maintenance-targets` line scopes this session to
docs/issue-645/ only. Per the SCOPE-EXCEEDED RULE, editing the
issue-476 record is outside that frozen scope — this session does not
touch it. Per the issue's own core#225-lesson instruction (record a
denial honestly rather than bypass it), that is what this section does.

## Requirement 3 — precision_measure.py run on live HEAD, honest output
Acceptance calls for population 0. Live-HEAD population after this
session's rule-330 fix is 2, both in the out-of-scope record above, not
0:

canonical: `python3 gates/precision_measure.py report /tmp/samples_final.json` — result: FAIL, run this turn
derived: same command
```
population=2 sampled=2

| rule | sampled | TP | precision | wilson_lb_90 |
|---|---|---|---|---|
| issue-333 | 2 | 0 | 0.0% | 0.0% (KILL <70%) |
| overall | 2 | 0 | 0.0% | 0.0% |

pass rule: overall point>=90% AND wilson_lb_90>=85% AND no per-rule kill(<70%)
promote: NO
```

canonical: `python3 gates/precision_measure.py report /tmp/samples_final.json` — result: FAIL, the report output directly above, run this turn. This output is attached to the issue as the honest current state; it is not the empty-queue "no findings — promotion not applicable" state the issue targets, and it is not reported here as a promotion pass.

Separately, and out of scope for this record: the module-style
invocation the tool's own docstring documents,
`python3 -m gates.precision_measure`, raises an AttributeError on
`gates.RECORD_PATH` at import time — a pre-existing defect, worked
around above by invoking the script file directly. Noted for whoever
picks up the issue-476 tallies next; not fixed here.

## Why
Requirement 1 extends an existing, already-proven exemption pattern in
`orphaned_path_reference_check` — the only alternative considered was a
broader "any negation word" regex, rejected because it would risk
suppressing genuine rule-330 hits the same way the already-fixed
misfire classes were scoped narrowly on purpose.

## Rationale for deviations
The issue's own Context section misidentifies where the 2 rule-333
tallies live (states issue-645's implementation record; they are
actually in issue-476's execution-observation record — see Requirement
2 above). Given the `maintenance-targets: docs/issue-645/` scope
declared on the issue, this session does not widen into the issue-476
record to fix them — per the SCOPE-EXCEEDED RULE, that is out-of-scope
work reported here, not built.

canonical: the Requirement 2 section above (this record's own git-log and sample citations) — this is the one divergence from the issue's acceptance text in this session.

## Upstream basis
Issue #1628; docs/issue-645/reports/implementation.md; issue #1614
thread (precision program).

## What did not work
Searched for the literal fraction string inside issue-645's
implementation record (grep, and this record's own bare-count checker)
expecting to find two unevidenced tallies there per the issue text.

canonical: `git log --all -p -- docs/issue-645/reports/implementation.md | grep -cE "[0-9]/[0-9]"` — result: FAIL to find the tallies there (see Requirement 2 above); the two real findings are in a different record entirely.

canonical: `python3 -m pytest gates/test_record_lint.py -q` — result: PASS, 64 passed (see `## What was done` above)

## Acceptance verification
- both-ways rule-330 fixtures, test_record_lint.py green — checked: pytest-record-lint — result: pass: 64 passed, see `## What was done` above.
- precision_measure.py sample on live HEAD returns population 0 — checked: precision-measure-sample — result: fail: population 2, not 0, see `## Requirement 3` above for the full live output, not met by this session's in-scope work.

## Open findings
- The two rule-333 findings in issue-476's execution-observation record
  remain unresolved. Resolution path: a session scoped to
  docs/issue-476/ adds derived:/fenced evidence for those two tallies
  or annotates them unverifiable-post-hoc, then re-runs
  `gates/precision_measure.py sample` + `report` to check whether
  population reaches 0.
- `python3 -m gates.precision_measure`'s import-time AttributeError is
  unresolved, unrelated to this issue's scope.
