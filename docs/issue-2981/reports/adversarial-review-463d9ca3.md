---
issue: 2981
role: adversarial-review-463d9ca3
author: adversarial-review-463d9ca3
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true
code_under_review: b2ec4e1dd93a18b7062768bf9ceca218decf1d21
loop_state: landed
type: review
breaking: false
verdict: changes-recommended -- the three named acceptance checks and a full regression sweep reproduce independently at the same pass/fail counts PR #3002 reports, and the merged/landed-state record-only exclusion is name-agnostic. But the new gate reaches only one of the two call sites that share `_respawn_or_cap()`: `_self_trigger_respawn()` calls it with no deliverable-existence check at all, live-reproduced below. A second, narrower gap: the still-open-PR record-only exclusion is a name match against one literal slug and does not generalize to this repo's other record-only branch-naming conventions, also live-reproduced below.
upstream:
  - path: b2ec4e1d:gates/spawn_on_pr.py, lifecycle.py, spawn.py, tests/test_respawn_deliverable_gate.py
    sha: b2ec4e1dd93a18b7062768bf9ceca218decf1d21
  - path: b2ec4e1d:docs/issue-2981/reports/merge-gates+test-derivation-2f452df8.md
    sha: b2ec4e1dd93a18b7062768bf9ceca218decf1d21
---

# issue-2981 -- adversarial-review-463d9ca3 record

## What was done

Independently re-derived PR #3002's acceptance/must-not claims for issue
#2981 against a fetched copy of its own head, rather than trusting the
PR's test-plan checkmarks or its own record's narrative.

derived: `git fetch origin pull/3002/head:pr-3002-review && git worktree add /tmp/pr-3002-review pr-3002-review` — result:
```
HEAD is now at b2ec4e1d issue-2981: log skipped warrant-hunter dispatch under build-now bypass
```
derived: `git merge-base origin/main pr-3002-review && git diff f737b6c8..pr-3002-review --stat` (in the worktree) — result:
```
 .../merge-gates+test-derivation-2f452df8.md        | 202 ++++++++++++++++++
 .../20260901T043756092451-348bc818fb9470d3.md      |   3 +
 gates/spawn_on_pr.py                               |  62 ++++++
 lifecycle.py                                       |  49 +++++
 spawn.py                                           |   1 +
 tests/test_respawn_deliverable_gate.py             | 237 +++++++++++++++++++++
 6 files changed, 554 insertions(+)
```
This matches PR #3002's own claimed `additions: 554, deletions: 0` exactly
(the wider diff against `origin/main` directly is noise from unrelated
commits main gained after this branch's fork point).

derived: `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` (isolated worktree) -- result:
```
....                                                                     [100%]
4 passed in 0.93s
```
derived: `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` -- result:
```
......                                                                   [100%]
6 passed in 0.91s
```
derived: `python3 -m pytest tests/ -k respawn_skip_is_reported -q` -- result:
```
..                                                                       [100%]
2 passed in 0.89s
```
All three named acceptance counts match PR #3002's own test-plan exactly.

derived: `python3 -m pytest test/ tests/ gates/ -q` (full repo sweep, same worktree) -- result:
```
16 failed, 681 passed, 3 xfailed in 31.71s
```
PR #3002's own record cites `17 failed, 680 passed, 3 xfailed` for the
identical command; the one-test difference is consistent with the
`pytest-xdist` ordering flake its own record already names for one of the
17 (`test_worktree_for_ref_success_path_is_gc_sweepable_end_to_end`). None
of the 16 failures observed here name `lifecycle.py`, `spawn.py`, or
`gates/spawn_on_pr.py`, and none match `test_respawn_deliverable_gate`:
```
test/test_convention_equivalence.py (2 tests)
test/test_local_dependency_env.py (1 test)
test/test_spawn_cross_family_skill_selection.py (7 tests)
test/test_spawn_artifact_skill_pairing.py (2 tests)
test/test_spawn_skill_judge_haiku_timeout_overlap.py (3 tests)
tests/test_spawn_gate_wiring.py (1 test)
```

**Must-not audit, checked against the diff and by direct reproduction:**

1. Does not disable automatic respawn -- derived: the
   `test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash`
   fixture (part of the second `pytest -k` rerun above) uses a real dead
   `wrapper_pid` so `session_end_verdict()` itself computes `crashed`
   un-mocked, mocks only `_subject_has_deliverable` to `None`, and asserts
   `_respawn_or_cap` is actually invoked with the right `(issue, skill)`
   args -- this partition genuinely exercises the fail-open direction, not
   just an execution-only pass.
2. Record-only PR must not suppress a respawn -- holds for the merged
   state, does not hold for the still-open state. See the dedicated
   section below.
3. No existing PR closed/altered/force-pushed -- derived: `git diff f737b6c8..pr-3002-review -- gates/spawn_on_pr.py lifecycle.py spawn.py | grep -iE "pr close|pr edit|force"` -- result: no output (no match).
4. Does not touch verdict-reliability code (issue #2969's separate scope)
   -- derived: `git diff f737b6c8..pr-3002-review --stat` lists no
   `watchdog.py` entry, and the new gate block in `_auto_respawn_check()`
   sits strictly after the existing, unmodified `if verdict != "crashed":
   return` line.

## Why

Per `defect-verification-independence-from-upstream-verdicts`: every claim
above was re-run against the fetched PR head in an isolated worktree
rather than cited from the PR's own test-plan or record text, and the
probing below deliberately targets the two edges the PR's own test suite
never exercises (a second call site, and non-matching branch names) rather
than stopping once the three named acceptance checks came back matching.

## Site 1 -- `_self_trigger_respawn()` never consults the new gate

`_respawn_or_cap()` has exactly two callers in the whole tree --
derived: `grep -rn "_respawn_or_cap(" --include="*.py" . | grep -v "^\./tests/\|^\./test/"` (isolated worktree) -- result:
```
lifecycle.py:359:def _respawn_or_cap(key: str, work: str, issue: int, skill: str, log: str,
lifecycle.py:580:    _sp._respawn_or_cap(key, work, issue, skill, entry.get("log", ""), start_ts, state,
lifecycle.py:615:    _sp._respawn_or_cap(roster_key, work, issue, skill, log, session_start_ts, state,
```
Line 580 sits inside `_auto_respawn_check()`, immediately after this PR's
new gate block. Line 615 sits inside `_self_trigger_respawn()`, which has
no gate block before it at all.

derived: script run against the real `lifecycle.py`/`spawn.py` in the isolated worktree --
```python
import sys
from unittest import mock
sys.path.insert(0, "/tmp/pr-3002-review")
sys.path.insert(0, "/tmp/pr-3002-review/gates")
import spawn, lifecycle
lifecycle._sp = spawn

found = {"number": 4242, "branch": "issue-9002/implementation", "state": "OPEN"}
with mock.patch.object(spawn, "_subject_has_deliverable", return_value=found), \
     mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
    lifecycle._self_trigger_respawn("uncommitted-work", "issue-9002/demo",
                                     "/tmp/fake-work", 9002, "demo", "log", 12345,
                                     single_phase=True)
print("respawn_or_cap called despite existing deliverable:", respawn_or_cap.called)
```
result:
```
respawn_or_cap called despite existing deliverable: True
```
Even with `subject_has_deliverable()` itself correctly resolving a real
open deliverable PR, `_self_trigger_respawn()` reaches `_respawn_or_cap()`
regardless -- the exact duplicate-PR shape the issue reports (a subject
that already has a covering PR gets a second one) is reachable through
this path with the PR applied. `b2ec4e1d:tests/test_respawn_deliverable_gate.py`
has no test naming `_self_trigger_respawn` -- derived: `grep -n
"_self_trigger_respawn" tests/test_respawn_deliverable_gate.py` (isolated
worktree) -- result: no output (no match) -- so this reproduces cleanly
against the shipped acceptance suite, which does not cover it. This is the
same sink two independent verifiers of issue #2969's PR already flagged
for the verdict-reliability question; here it is unguarded for the
deliverable-existence question instead.

## Site 2 -- the still-open record-only exclusion is one hardcoded name, not a content check

`gates/spawn_on_pr.py`'s `_VERIFICATION_SLOT_RE` pattern is
`^independent-verification-\d+$` -- derived: `grep -n "_VERIFICATION_SLOT_RE = " gates/spawn_on_pr.py` (isolated worktree) -- result:
```
_VERIFICATION_SLOT_RE = re.compile(r"^independent-verification-\d+$")
```
`subject_deliverable_branch()` treats any open-PR branch slug that does
NOT match this one pattern as a deliverable candidate. This repo's actual
record-only branches are not named that way -- this very review session's
own branch is `issue-2981/adversarial-review-463d9ca3`, and other
record-only skill names visible in this same worktree's history include
`test-derivation-*` and `merge-gates+test-derivation-*`.

derived: regex check --
```python
import re
pat = re.compile(r'^independent-verification-\d+$')
for s in ['independent-verification-1', 'adversarial-review-2acc75af',
          'merge-gates+test-derivation-98d98713', 'test-derivation-8718eaa7']:
    print(s, '->', bool(pat.match(s)))
```
result:
```
independent-verification-1 -> True
adversarial-review-2acc75af -> False
merge-gates+test-derivation-98d98713 -> False
test-derivation-8718eaa7 -> False
```

derived: script run against the real `subject_has_deliverable()` in the isolated worktree --
```python
import sys, tempfile
from pathlib import Path
from unittest import mock
sys.path.insert(0, "/tmp/pr-3002-review")
sys.path.insert(0, "/tmp/pr-3002-review/gates")
import spawn_on_pr, closure_sweep

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pr_index = {"issue-9001/adversarial-review-463d9ca3":
                {"number": 55, "state": "OPEN", "body": ""}}
    with mock.patch.object(closure_sweep, "_pr_index_all", return_value=(pr_index, True)):
        result = spawn_on_pr.subject_has_deliverable(root, "issue-9001")
    print("result:", result)
```
result:
```
result: {'number': 55, 'branch': 'issue-9001/adversarial-review-463d9ca3', 'state': 'OPEN'}
```
An open, record-only PR under any of this repo's actual non-
`independent-verification-N` review/verification branch names resolves as
a genuine deliverable through this path.

The merged partition does not share this gap -- derived: script run in the same worktree --
```python
import sys, tempfile
from pathlib import Path
from unittest import mock
sys.path.insert(0, "/tmp/pr-3002-review")
sys.path.insert(0, "/tmp/pr-3002-review/gates")
import spawn_on_pr, closure_sweep

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    rep = root / "docs" / "issue-9001" / "reports"
    rep.mkdir(parents=True)
    (rep / "adversarial-review-abc123.md").write_text(
        "---\nloop_state: landed\nauthor: someone\nverifies_subject: true\n---\n\nbody\n")
    with mock.patch.object(closure_sweep, "_pr_index_all", return_value=({}, True)):
        result = spawn_on_pr.subject_has_deliverable(root, "issue-9001")
    print("result:", result)
```
result:
```
result: None
```
`subject_deliverable_record()` excludes by the `verifies_subject: true`
frontmatter field, which does not depend on the branch/file name -- only
the still-open path is narrow.

PR #3002's own record (`b2ec4e1d:docs/issue-2981/reports/merge-gates+test-derivation-2f452df8.md:128`)
argues the name-based filter was chosen over
`merge_gate.py::_own_pr_supplies_verification()`'s content check because
that function returns `False` on any `git show` read failure -- backwards
for this call site. That argument covers only the unreadable-branch
failure mode; it does not address a branch that IS readable and simply
carries a different, equally real record-only name, which is the gap
reproduced above.

## Acceptance verification

- b2ec4e1d:tests/test_respawn_deliverable_gate.py:117 — checked: respawn_skips_existing_deliverable — result: pass
- b2ec4e1d:tests/test_respawn_deliverable_gate.py:90 — checked: respawn_proceeds_without_deliverable — result: pass
- b2ec4e1d:tests/test_respawn_deliverable_gate.py:206 — checked: respawn_skip_is_reported — result: pass

## What did not work

None.

## Upstream basis

`code_under_review` is PR #3002's own head commit, fetched live via `git
fetch origin pull/3002/head:pr-3002-review` and cross-checked with `git
rev-parse HEAD` in the isolated worktree. `b2ec4e1d:docs/issue-2981/reports/merge-gates+test-derivation-2f452df8.md`
is that same PR's own record, read directly rather than trusted, and
cited above by section.

## Open findings

1. (high) `_self_trigger_respawn()` (`lifecycle.py`, PR head `b2ec4e1d`,
   line 615 -- not this checkout's own pre-PR copy of the file) reaches
   `_respawn_or_cap()` with zero `subject_has_deliverable()` consultation
   -- Site 1 above. Resolution path: extend the same check into
   `_self_trigger_respawn()`, or move it into `_respawn_or_cap()` itself
   where both callers already converge.
2. (medium) `subject_deliverable_branch()`'s still-open-PR record-only
   exclusion matches only the literal `independent-verification-<N>` slug
   -- Site 2 above. Resolution path: generalize the still-open check to a
   content marker (e.g. a PR-body field analogous to `verifies_subject:
   true`) rather than a name pattern, or explicitly document the residual
   scope narrowing in the issue/PR.

## Next steps

Findings 1 and 2 above are handed back to coding/qa for issue #2981 --
loop_state is terminal for this review session; no further action is
pending on this record's own side.

skill-verdict: adversarial-review -- applied: invoked; used to approach
PR #3002 as an artifact to find problems in per the task's explicit
instruction not to trust its claimed results
skill-verdict: defect-verification-independence-from-upstream-verdicts -- applied: invoked; used to re-derive every acceptance/must-not claim from the isolated worktree rather than citing the PR's test-plan or record output, and to probe the two edges its own tests never cover
other mounted skills: not triggered
