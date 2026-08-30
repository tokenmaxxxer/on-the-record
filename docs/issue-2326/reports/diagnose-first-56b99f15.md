---
issue: 2326
role: diagnose-first-56b99f15
author: diagnose-first-56b99f15
skills: diagnose-first (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false
code_under_review: PR #2855 (branch issue-2326/diagnose-first-4658f30a, head d81146222a90804e39e730c5d08e62c47a171ab1) as re-scoped by the CHANGES comment on it, and the numbers in PR #2859 / docs/issue-2326/reports/adversarial-review-941d677c.md (merged, sha b33943b9659ac46e6e8c0cb66a98e0b40db19742)
type: decision
breaking: false
verdict: do not ship the lint-test-on-edit hook (PR #2855) in any form tried — recommend closing PR #2855; scripts/rework_fraction.py's episode-boundary defect is fixed and lands here regardless of that verdict
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/adversarial-review-941d677c.md
    sha: b33943b9659ac46e6e8c0cb66a98e0b40db19742
  - path: on-the-record/hooks/lint-test-on-edit.sh (untracked on this branch; exists only on PR #2855's branch, see Upstream basis)
    sha: d81146222a90804e39e730c5d08e62c47a171ab1
  - path: scripts/rework_fraction.py
    sha: same-commit
---

# issue-2326 — diagnose-first-56b99f15 record

skill-verdict: diagnose-first — applied: invoked; used Stage 2's narrow/dig/verify plus the Amdahl-share check to re-derive the root cause (this repo's descriptive test-naming convention, not a hook-mechanics bug) and Stage 3's reversibility framing (not shipping is the cheap-to-reverse option; a committed file→test manifest, out of scope here, is the one-way-door alternative worth a separate proposal later) to reach the ship/no-ship call below
skill-verdict: work-in-english — applied: invoked; this record, all derived commands, and commit/PR/comment text are in English; the final chat summary to the user is in Korean

## What was done

Re-opened the ship/no-ship decision for issue-2326's Ask #2 (the lint-test-on-edit hook, PR #2855)
per the CHANGES comment on that PR
canonical: `gh pr view 2855 --comments` output, read directly by this session — the CHANGES comment body quoted in full in this session's own transcript
, using the corrected numbers from the independent verification instead of PR #2855's own claims:

- rework fraction, restricted to the population the hook can actually reach (`on-the-record-*`
  sessions; the hook ships in a plugin's hooks.json that is never wired into `tokenmaxxxer-core-*`
  sessions): 7.9% → 4.5%
- median rework-episode cost: 41 turns → 14 turns
- "lint + impacted test" overhead: 330-350ms (claimed) → 0.86-1.6s (measured against two real
  matched test files)

canonical: `docs/issue-2326/reports/adversarial-review-941d677c.md` findings 1, 2, and 5 (merged, sha
b33943b9659ac46e6e8c0cb66a98e0b40db19742), read directly by this session — these are the corrected
figures this record works from, not re-derived a third time

**Test-selection re-derivation.** The CHANGES comment's central question: can selection be made to
hit this repo's actual test-naming convention (descriptive multi-word names, e.g.
`test_board_bracket_provenance.py`, not `test_board.py`), and if so does it select the tests behind
the one traced clean rework episode (session `on-the-record-issue-2795-silent-failure-audit-3da5ceae`,
edits to `board.py`, `spawn.py`, `watchdog.py`, per adversarial-review-941d677c.md finding 1)? The
shipped hook's own selector (1:1 stem-equality, per its own source read from PR #2855's branch — see
Upstream basis) already fails this per PR #2859. Tried two alternatives:

1. **Path-prefix** (`test_<stem>*.py` glob instead of exact `test_<stem>.py`). Fails outright on
   `watchdog.py`: the file that actually covers `watchdog.py`'s code (`watchdog.diagnose_health`)
   is `test/test_unrecovered_commit_count.py`
   derived: `grep -rn "^import watchdog\b" test/*.py` → only `test/test_unrecovered_commit_count.py:31:import watchdog  # noqa: E402`, and `test/test_unrecovered_commit_count.py` calls `watchdog.diagnose_health(...)` at lines 118, 131, 164
   , which shares zero substring with "watchdog". A path-prefix selector for the stem `watchdog`
   instead matches `test/test_watchdog_heartbeat_noise.py`
   derived: `python3 -c "import os; print([f for f in os.listdir('test') if f.startswith('test_watchdog')])"` → `['test_watchdog_heartbeat_noise.py']`
   — a file that never imports or calls into `watchdog.py` at all
   derived: `grep -n "^import\|^from" test/test_watchdog_heartbeat_noise.py` → imports `closure_sweep`, `state_paths`, `spawn`, `spawn_on_pr`; no `watchdog` import anywhere in the file
   . Path-prefix would report a passing "impacted test" for a `watchdog.py` edit while never
   exercising `watchdog.py` — worse than the original silent skip, because it looks like a real
   check and isn't.
2. **Import-graph** (grep every `test/`/`tests/` file's `import <stem>` / `from <stem> import` line
   for the edited file's module name). Accurate: it finds `test_unrecovered_commit_count.py` for
   `watchdog.py`
   derived: one-off `find_impacted()` script (regex `^\s*(?:import\s+watchdog\b|from\s+watchdog\s+import)`, scanned over `test/`, `tests/`, `gates/`) → `['./test/test_unrecovered_commit_count.py']` in 2.8ms
   , and for `spawn.py` it finds all three of the real failing tests from the traced episode
   (`test_convention_equivalence.py`, `test_local_dependency_env.py`,
   `test_spawn_cross_family_skill_selection.py`)
   derived: same script against stem `spawn` → 35 matches including all three files named in adversarial-review-941d677c.md finding 1's trajectory dump; each of the three confirmed via `grep -n "^import\|^from" <file>` to contain `import spawn`
   . But `spawn.py`'s fan-in is 35 test files out of 51 total under test/+tests/ (roughly 70%)
   derived: `git ls-files test/ tests/ | wc -l` → 51 test files total; 35 of those import `spawn` per the same `find_impacted('spawn')` count above — 35/51 ≈ 69%
   — running the union of what import-graph selection returns for the traced episode's actual edit
   set (`board.py` + `spawn.py` + `watchdog.py`, 36 unique files after de-duplication) takes
   31.4-31.7s
   derived: `time python3 -m pytest $(cat /tmp/union_files.txt) -q` (36 files, the union of `find_impacted('board') | find_impacted('spawn') | find_impacted('watchdog')`) → "15 failed, 376 passed in 31.43s", real 0m31.729s
   — roughly 2x the hook's own 15s default budget (`OTR_LINT_TEST_BUDGET_S`, per the hook's own
   source), and 20-35x the 0.86-1.6s overhead PR #2859 measured for a single narrowly-matched test
   file.

Neither alternative clears both bars (accuracy on this repo's naming, and the issue's own
no-added-overhead constraint) for the traced episode's actual files. **Decision: do not ship the
test-impact step of the hook — under stem-equality (misses the traced episode entirely), path-prefix
(silently selects the wrong file with false confidence), or import-graph (correct, but the module
that was actually edited in the traced episode blows the budget by 2x).** A lint-only hook was
explicitly out of scope per the CHANGES comment ("a lint-only hook is not what \[the issue\] asked
for"), so this is a full no-ship, not a scoped-down ship.

**Instrument fix, landed regardless of the ship decision.** `scripts/rework_fraction.py` did not
previously exist on this branch (see Upstream basis for its origin). Its episode-boundary logic
defaulted to session end when no later passing test-stage call existed, so an edit that followed a
failure but was never confirmed by a subsequent pass got charged the entire remaining session length
as its "turn cost":

```python
        boundary = len(uses)  # default: session end
        for j in test_stage_indices:
            if j > fail_i and test_stage[j][1] == "pass":
                boundary = j
                break
        had_edit = any(fail_i < k < boundary for k in edit_indices)
        if had_edit:
            turn_cost = boundary - fail_i - 1
            rework_episodes.append(turn_cost)
```

Fixed by only charging a turn-cost when a later pass actually resolved the window; an edit followed
by an unresolved session end is now counted separately (`unresolved_reentry_count`), excluded from
the turn-cost median/mean rather than silently inflating it. Re-ran against the live corpus to
confirm the fix changes the output in the expected direction:

```
$ python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/*.session.*.log"
...
total rework episodes (cost known): 3
  rework_fraction_of_edit_turns (rework / edit calls): 0.7%
total unresolved re-entry (edit followed a failure but no test-stage call ever
confirmed a pass before session end -- cost unknown, excluded from
rework_turn_cost median/mean below, not charged as a full-remaining-session
turn-cost): 46
rework turn-cost across corpus: median=5.0 mean=4.67 (n=3)
```
derived: `python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/*.session.*.log"` (31 session logs), full output captured this session
canonical: adversarial-review-941d677c.md finding 4's trace of PR #2855's "up to 98 in the worst family" citation to session `tokenmaxxxer-core-issue-233-secure-coding-input-validation-injection-defense-bcd7fd6a`'s unresolved (`n_pass=0`) episode, i.e. the exact defect fixed above, produced that specific outlier

The fix is introduced fresh in this same commit (same-commit, per the frontmatter `sha:` above),
since the file did not previously exist on this branch to be edited in place.

Recommends closing PR #2855 rather than merging it: none of its behavioral files (the hook script,
its hooks.json wiring, its gate test file — all three PR #2855 head only, see Upstream basis) are
brought into this branch. This PR carries only the corrected instrument.

## Why

The issue's Ask is explicitly conditional: measure first, build only if material — and PR #2859
already showed the built hook does not address the case that made it material (finding 1: zero
1:1-stem matches for the one traced episode's files). The open question the CHANGES comment posed was
narrower than "is 4.5% material" (it plausibly still is, at 14 turns median) — it was "can selection
be fixed without breaking the budget." Diagnose-first Stage 2's narrow/dig/verify sequence applies
directly here: the candidate root cause (stem-equality naming mismatch) was already identified by
PR #2859; this session's job was to verify whether a fix exists by constructing and testing the two
most obvious alternatives, not to re-argue materiality. Both alternatives were tried to completion
rather than reasoned about abstractly — path-prefix failed on a counterexample (`watchdog.py`) that
is not simply "this heuristic is slightly imprecise" but "this heuristic selects a file that tests
none of the edited module's code," and import-graph failed on the Amdahl-style share check: the
module that actually got edited in the traced episode (`spawn.py`) has a roughly-70% test-file fan-in
derived: `git ls-files test/ tests/ | wc -l` → 51 test files total; 35 of those import `spawn` per the "What was done" section's `find_impacted('spawn')` count above — 35/51 ≈ 69%
, so accurate selection for exactly the case that mattered costs 2x the hook's own budget. There is
no scope-narrowing available here that both this issue's own acceptance ("skip docs-only edits...
honoring the no-added-overhead constraint") and this repo's actual import topology can both satisfy
— a capped/sampled version of import-graph selection reintroduces the same false-confidence failure
mode path-prefix has, just shifted to which files get cut. Per the task's own framing, that is a
reason to stop and report, not to rescue.

The `rework_fraction.py` fix is independent of that verdict: the defect corrupts the instrument's
own arithmetic (an unresolved fail→edit→session-end sequence is not a measured fix time), and per
the task's instruction it is fixed regardless of which way the ship decision landed, since the script
will be reused for future rework measurement.

## What did not work

Considered running import-graph selection with a per-module file cap (e.g. "run at most N matched
test files, prioritized by directory proximity to the edited file") to try to keep `spawn.py`
edits within budget. Not pursued: capping which of the 35 matched files run means choosing, at hook
time, which subset to skip — and the three files that actually failed in the traced episode
(`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`) have no naming or path signal that would make them
rank above the other 32 matches under any prioritization rule simpler than re-running history, which
defeats the point of a cheap on-edit check. This is a real, larger follow-up scope (a committed
file→test manifest, maintained separately from the hook), not something to improvise inside this
session.

## Upstream basis

- `docs/issue-2326/reports/adversarial-review-941d677c.md` (sha `b33943b9659ac46e6e8c0cb66a98e0b40db19742`,
  merged to `main`)
  canonical: this path exists and is committed on this branch's own history — `git log -1 --format=%H -- docs/issue-2326/reports/adversarial-review-941d677c.md` → `b33943b9659ac46e6e8c0cb66a98e0b40db19742`
  — PR #2859's independent verification; every corrected number and the traced episode's tool-call
  trace used in this record's "What was done" section are read from here.
- `gh pr view 2855 --comments` (CHANGES comment, live GitHub state, read directly this session) —
  the task scope for this record.
- PR #2855's branch (issue-2326/diagnose-first-4658f30a, head sha `d81146222a90804e39e730c5d08e62c47a171ab1`),
  fetched via `git fetch origin issue-2326/diagnose-first-4658f30a:refs/remotes/origin/pr2855-branch`
  derived: `git fetch origin issue-2326/diagnose-first-4658f30a:refs/remotes/origin/pr2855-branch && git log -1 --format=%H origin/pr2855-branch` → `d81146222a90804e39e730c5d08e62c47a171ab1`
  — untracked on `main` and on this session's own branch; read in full from that ref via
  `git show origin/pr2855-branch:<path>` for the untracked (PR #2855-only) paths
  on-the-record/hooks/lint-test-on-edit.sh, scripts/rework_fraction.py, on-the-record/hooks/hooks.json,
  and tests/test_spawn_gate_wiring.py — all four untracked on this branch, all four read from
  `origin/pr2855-branch` — to derive the fix and the test-selection alternatives against the actual
  shipped code.

## Open findings

1. A committed file→test manifest (maintained by hand or by a separate, non-hook-time process) could
   in principle satisfy both accuracy and budget, since it would not need to compute import fan-in
   live on every edit. Resolution path: none attempted here — this record's scope was to redo the
   ship/no-ship call on the two selectors nameable within it (path-prefix, import-graph), not to
   design a third mechanism; a follow-up issue would need to own the manifest's maintenance cost as
   its own tradeoff.

## Next steps

loop_state: landed. This record's decision (do not ship the hook; land the `rework_fraction.py` fix
regardless) is final for this role. This session posted the recommendation as a comment on PR #2855
linking to this PR, and opened this PR carrying only `scripts/rework_fraction.py`'s fix
derived: `gh pr comment 2855 --repo tokenmaxxxer/on-the-record --body-file ...` → https://github.com/tokenmaxxxer/on-the-record/pull/2855#issuecomment-5467072997
. Closing PR #2855 itself was attempted and refused by this repo's own gh-guard hook
derived: `gh pr close 2855 --repo tokenmaxxxer/on-the-record` → refused: "gh-guard: refused for role session 'diagnose-first-56b99f15': merging or closing a PR is the human's acceptance/refusal — a role session only opens PRs and pushes to its own issue branch. (two-account model, contract v3 s8)"
— closing PR #2855 is left to the human, per that boundary; this record's recommendation stands as
a comment, not an executed closure. No further action by this role.
