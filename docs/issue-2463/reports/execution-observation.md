---
issue: 2463
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2463/reports/implementation.md
    sha: 11603890e96d3a4c5edc728f5ff8e31bfe095c00
  - path: gates/check_runner.py
    sha: 11603890e96d3a4c5edc728f5ff8e31bfe095c00
  - path: gates/test_check_runner.py
    sha: 11603890e96d3a4c5edc728f5ff8e31bfe095c00
subject: PR #2464 (issue-2463/implementation, head 11603890e96d3a4c5edc728f5ff8e31bfe095c00, base main)
test: issue #2463 Acceptance section — 4 check bullets
result: passed
assertedBy: execution-observation, independently re-run this turn
---

# issue-2463 — execution-observation record

Path convention: every file cited below with an explicit `<sha>:<path>`
prefix lives on `issue-2463/implementation` at sha `11603890`, not on this
record's own branch (`issue-2463/execution-observation`, based on
`origin/main`). Bare paths refer to this branch or to `/tmp` scratch
scripts (all removed after use, called out explicitly where cited).

## What was done

Independently re-derived all four of issue #2463's acceptance checks
against PR #2464, rather than citing its own record's claims, in an
isolated worktree (`git worktree add /tmp/otr-2463-eo
origin/issue-2463/implementation`, sha `11603890`, removed with `git
worktree remove --force` after use).

**Full test-suite re-run, this turn, in the `11603890` worktree:**

acceptance: `python3 gates/test_check_runner.py` — result:
```
31/31 passed
```
Matches the record's own claimed 31/31 (includes the 3 new tests this fix
adds).

acceptance: `python3 -m pytest gates/test_check_runner.py -q` — result:
```
38 passed in 1.78s
```
Matches the record's own claimed 38 passed (derived: hand count "38" above
equals pytest's own "38 passed" summary line).

acceptance: `python3 -m pytest gates/ -q` (full gate suite) — result:
```
1006 passed, 8 xfailed in 10.16s
```
Matches the record's own claimed "1006 passed, 8 xfailed" — same counts,
this turn's own run, confirming no regression across the full gate suite.

**Acceptance bullet 1 — synthetic fixture reproducing the 9-case pattern,
independently authored (not the PR's own test text), before/after against
`11603890:gates/check_runner.py` (after) and this branch's unmodified
`gates/check_runner.py` (before, `origin/main`, no diff on this branch):**
built via a small scratch script (`/tmp/otr-2463-eo-verify.py`, removed
after use) that imports both module versions directly and calls
`parse_checks()` on four independently-worded fixture lines — result:
```
BEFORE=['file-existence'] AFTER=['judgment']  <- results are written under `issue-<n>/<role>` per the naming convention
BEFORE=['test']           AFTER=['test']      <- this mirrors the layout described in `docs/issue-<n>/reports/<role>.md`
BEFORE=['judgment']       AFTER=['judgment']  <- branch names follow the `<n>-<role>` shape used elsewhere
BEFORE=['file-existence'] AFTER=['judgment']  <- see `<role>/notes` for the convention this replaces
```
Two of my four independent fixtures reproduce the exact `file-existence`
→ `judgment` shift the issue describes, on wording distinct from the PR's
own test file. The third (`branch names follow...`) was already
`judgment` pre-fix (no `/` in that backtick) — not part of this defect
class, included as a negative control. The second fixture surfaces a
residual gap, disclosed below under "Open findings" — it is not one of
the acceptance bullets and does not block this delivery.

**Acceptance bullet 2 — regression fixture, genuinely nonexistent literal
path, independently worded:** first attempt
(`` `build/output/really-missing-manifest.json` ``) turned out to
classify as `test`, not `file-existence`, on both before and after — an
artifact of the pre-existing (`/` + `.` in the same token →
`looks_like_command`) rule from issue #2313, unrelated to this fix; a
wording mistake in my own fixture, not a finding. Corrected to an
extension-less path (matching the shape the PR's own regression test
uses) — result:
```
BEFORE=['file-existence'] AFTER=['file-existence']
run_checks status (post-fix, empty tempdir): fail
```
`reports/summary-that-truly-does-not-exist` (my own wording, distinct
from the PR's `reports/genuinely-missing-report`) still classifies
`file-existence` and still genuinely `fail`s against an empty tempdir on
both before and after — confirms the placeholder exclusion did not
blanket-disable the check.

**Acceptance bullet 3 — live re-classification of issue #2402's actual
Acceptance section:** fetched independently this turn
(`gh issue view 2402 --json body -q .body`, not copied from either the
implementation or conformance-review record), classified through both
module versions via `_acceptance_section()` + `parse_checks()` — result:
```
BEFORE fix:
file-existence  | there is a supported way to recut a corrupted branch's content that remains mapped to its `issue-<n>/<role>` subject...
judgment        | `board-sweep`'s subject-mapping recognizes branches produced by that path...
judgment        | a role whose delivery landed via a recut branch is NOT re-spawned...
judgment        | if the chosen approach leaves any unmapped-branch case...

AFTER fix:
judgment        | there is a supported way to recut a corrupted branch's content that remains mapped to its `issue-<n>/<role>` subject...
judgment        | `board-sweep`'s subject-mapping recognizes branches produced by that path...
judgment        | a role whose delivery landed via a recut branch is NOT re-spawned...
judgment        | if the chosen approach leaves any unmapped-branch case...
```
Identical to the implementation record's own before/after claim,
independently re-derived. Confirmed (per `check_runner.py`'s own module
docstring and the implementation record's disclosure) that classification
runs at issue-body granularity, not per-PR — this is the same text that
actually ran against PRs #2446, #2456, and #2461, since none of those
PRs carries a per-PR variant of issue #2402's Acceptance section.

**Acceptance bullet 4 — WARN-tier statement:** `11603890:gates/check_runner.py`
and `11603890:gates/merge_gate.py` read directly this turn; `grep -ni
warn` against both returns no match — confirms no third check-result
status was introduced. The implementation record explicitly states the
WARN tier (consult recommendation 3) is deferred, not implemented,
reasoning that the 9 observed cases were all unambiguous placeholder
mentions (not the genuinely-ambiguous middle case WARN targets) and that
introducing a third status would reach into `run_checks()`,
`format_comment()`, and `merge_gate.py` — a materially larger change
outside this issue's `design-research-skip: mechanical` scope. Diff scope
confirmed independently: `git diff origin/main...HEAD --stat` from the
`11603890` worktree shows only `gates/check_runner.py` (+13),
`gates/test_check_runner.py` (+39), the implementation record itself, and
two unrelated consult-log files — no `gates/merge_gate.py` change and no
change to any `run_checks()` caller, corroborating the "single narrow
exclusion, no new vocabulary" characterization.

## Why

The implementation record already asserts all four of issue #2463's
acceptance checks are satisfied. Re-derived each from scratch in a fresh
worktree rather than treating the record's transcripts as sufficient: ran
the full test suite myself, authored my own fixture wording distinct from
the PR's own test file for both the placeholder and regression cases, and
independently fetched and classified issue #2402's actual Acceptance
text through both module versions. canonical: the "What was done" section
above holds every executed transcript this paragraph summarizes — this
turn's own runs, not the implementation record's numbers.

Considered and rejected: stopping after re-running the PR's own test
suite (bullets already pinned by its 3 new tests) instead of also
authoring independent fixture wording — rejected, since re-running the
same test file only confirms internal consistency, not that the fix
generalizes past the exact strings the implementation session chose;
independently-worded fixtures are what actually exercise the regex rather
than the test author's own phrasing.

## Upstream basis

- `11603890:docs/issue-2463/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `11603890:gates/check_runner.py`, `11603890:gates/test_check_runner.py`
  — the actual code and test changes, read and imported directly this
  turn via the `/tmp/otr-2463-eo` worktree.
- issue #2402's live body (`gh issue view 2402 --json body`, fetched this
  turn) — the real historical Acceptance text acceptance bullet 3 targets.
- this branch's own unmodified `gates/check_runner.py` (`origin/main`) —
  used as the "before" module for every before/after comparison above.

## Open findings

One residual gap, non-blocking against this issue's own Acceptance
criteria: a backticked placeholder token that *also* has a `/`-plus-known-
extension shape (e.g. `` `docs/issue-<n>/reports/<role>.md` ``) is caught
by the pre-existing `looks_like_command` branch (issue #2313's compound-
command rule: token contains `/` and at least one `.`) *before*
`_looks_like_path()`/`_ANGLE_PLACEHOLDER` is ever reached, so it
classifies as `test` rather than `judgment` and still mechanically FAILs
(reproduced this turn: `run_checks` on this exact string against an empty
tempdir raised `[Errno 2] No such file or directory:
'docs/issue-<n>/reports/<role>.md'`, status `fail`, on both before and
after this fix). Same defect family (a descriptive mention misclassified
as mechanically checkable) surviving in a sibling code path. Not one of
the issue's 9 observed cases and not named in its Acceptance bullets — no
resolution path opened here; noted for whoever files the next classifier-
hardening issue in this series if it's hit for real, per this repo's own
#2278/#2313/#2233/#2463 precedent of fixing one observed case at a time
rather than speculatively.

## What did not work

The first regression-fixture wording attempted for acceptance bullet 2
(`` `build/output/really-missing-manifest.json` ``) did not classify as
`file-existence` on either the before or after module — it hit the
pre-existing `/`+`.` → `looks_like_command` rule instead, an artifact of
my own fixture's shape (a real-looking script/artifact path, not a bare
non-executable path) rather than a finding about the fix. Corrected to an
extension-less path matching the shape the PR's own regression test uses;
documented under "What was done" rather than silently redone.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the four independently-executed checks above —
result:
```
bullet 1 (synthetic fixture, before/after): file-existence -> judgment on 2 independently-worded placeholder fixtures (this turn)
bullet 2 (regression, no placeholder): file-existence -> file-existence, still fails, on 1 independently-worded fixture (this turn)
bullet 3 (issue #2402 real Acceptance text, live re-classification): file-existence -> judgment, identical to the record's own claim (this turn)
bullet 4 (WARN-tier statement): confirmed explicitly deferred, no "warn" string anywhere in check_runner.py/merge_gate.py (this turn, direct grep)
full suite: 31/31, 38 passed, 1006 passed + 8 xfailed — all match the record's own claimed counts (this turn)
```
