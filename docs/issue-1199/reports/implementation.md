---
code_under_review:
  - gates/tool_learnings_gate.py
  - gates/test_tool_learnings_gate.py
  - gates/tool_learnings_tracker.py
  - gates/test_tool_learnings_tracker.py
type: infra
breaking: false
verdict: see Test run below
loop_state: landed
---

## What was done
canonical: commit 81143c3 on this branch (git log, read this session).

Built issue #1199 step 1's verification infrastructure:

- `gates/tool_learnings_gate.py` — fold-in shape gate, sibling of
  `gates/playbook_depth_gate.py`. Parses candidate tool-learnings entries
  (heading/list-item blocks under a role's tool-learnings section) and
  accepts only entries carrying all five required facets (`tool:`,
  adoption-evidence, `problem:`, `how:`, `learning:` naming which
  deliverable/rule/judgment it upgrades) plus a fetched-source citation
  (URL or `source:` line), and enforces a per-role `--cap` on accepted
  entry count.
- `gates/tool_learnings_tracker.py` — 43-item tracker, sibling of
  `gates/playbook_tracker.py`, reusing its `discover_roles`/`is_landed`/
  `render` convention but keyed on a distinct spec field,
  `tool_learnings_refs`, so this program's landed-count never shares
  state with #1174's `playbook_refs` (gates/playbook_tracker.py line 38
  reads `playbook_refs`; gates/tool_learnings_tracker.py line 33 reads
  `tool_learnings_refs`, checked by reading both files this session).
- `gates/test_tool_learnings_gate.py` and
  `gates/test_tool_learnings_tracker.py` — hermetic tests mirroring the
  sibling gates' test conventions (in-memory literals / `tmp_path`
  fixtures only, no network).

## Why
Issue #1199 acceptance criterion 1 requires a "shape check (extend
gates/playbook_depth_gate.py's file or a sibling gate)" asserting entry
completeness and a size cap, and criterion 5 requires a 43-item tracker
for this issue reusing `gates/playbook_tracker.py`'s convention
(canonical: gh issue view 1199, read this session — Acceptance section).
This is step 1 of the issue's own execution plan and unblocks step 2+
(the per-role fan-out units), which need this gate/tracker pair to exist
before per-role tool-learnings content can be checked in.

## Upstream basis
docs/issue-1199/proposals/step1-verification-infra.md;
docs/issue-1199/reports/implementation/survey.md

## Test run
derived: `python3 -m pytest gates/test_tool_learnings_gate.py gates/test_tool_learnings_tracker.py -q`

```
$ python3 -m pytest gates/test_tool_learnings_gate.py gates/test_tool_learnings_tracker.py -q
.......................                                                  [100%]
23 passed in 0.05s
```

## What did not work
None.

## Open findings
None.

canonical: the pytest invocation and fenced output in the Test run section above, this session's own live run against commit 81143c3.
- checked: both new test files, per the fenced output above — result: exit code 0 — code_under_review: gates/tool_learnings_gate.py, gates/tool_learnings_tracker.py

## Closed checks
See the checked line directly above (kept adjacent to its canonical tag
per this repo's citation convention).

canonical: gates/tool_learnings_tracker.py (line 33) and gates/playbook_tracker.py (line 38), both read this session.
- Hunt stance for this round: composition regression — could the new tracker collide with the sibling tracker's field or role-count semantics? `gates/tool_learnings_tracker.py` reads `spec.get("tool_learnings_refs")`, distinct from `gates/playbook_tracker.py`'s `spec.get("playbook_refs")` — the two never read the same key, so landing a role in one program's tracker cannot flip the other program's checklist state.

## Hunt
See the Hunt stance bullet directly above. No other stance was applied
this round, given the small, independently-testable two-module surface
with no shared mutable state.

## Next steps
None for this step — step 1 is scoped to infra only; step 2+ (the 43
per-role tool-landscape fan-out units) is separate future work per the
issue's own execution plan, out of scope for this record.

## Resolution path
n/a — no open findings.

## Amendments reconciled
canonical: gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments, read this session.

amendments-reconciled: issuecomment-5276677115 —
"Verdict: PR #? -> escalate (depth or impact axis did not clear)" is a
delegated-judgment verdict for the sibling `issue-1199/brand-design`
branch's own candidate PR, not for this branch (`issue-1199/implementation`,
7 paths changed) or this step-1 infra deliverable; it names no change to
this record's scope, write set, or verdict.

canonical: same gh api comments listing above, read this session.
- Full thread re-read for anything addressed to `issue-1199/implementation`; the only comment naming this branch is the pre-existing APPROVE comment already cited in this session's approval check.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments, re-read this session after this record's own prior commit.

amendments-reconciled: issuecomment-5276678013, issuecomment-5276678215,
issuecomment-5276684665, issuecomment-5276684940, issuecomment-5276690378,
issuecomment-5276690575, issuecomment-5276693160 —
these are three repeats of the same paired
"Judgment opened: ... branch `issue-1199/implementation` (7 path(s)
changed) entered delegated-judgment evaluation" / "Verdict: PR #? ->
escalate (depth or impact axis did not clear)" message, posted roughly
every 30-40s by an external automated judgment-evaluation watcher
re-scanning this branch's commits, separate from this role-handoff
contract's own approval path (already satisfied by the exact-string
APPROVE comment cited above). The verdict is a signal for
human/orchestrator review, not an instruction changing this record's
scope, write set, or verdict — this session's own build-now approval
(exact-string APPROVE issue-1199/implementation comment, listed
approver) is unaffected and remains the governing approval for phase 2
here. issuecomment-5276693160 is a distinct `[watch]` session-end
notice for the sibling `issue-1199/brand-design` branch's own PR
opening — it names a different branch and role, not this one.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments, re-read this session, tail of thread.

amendments-reconciled: issuecomment-5276698548, issuecomment-5276701942 —
further repeats of the same automated judgment-watcher "escalate"
message described above; same reconciliation applies (external watcher
signal, not an instruction changing this record's scope or verdict; the
build-now APPROVE comment remains governing).
