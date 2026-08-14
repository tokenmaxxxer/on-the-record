# Conformance review — issue-459 PR-create/spec-index preflight hooks

## Upstream / basis

Requirement list: `docs/issue-459/proposals/2026-08-08-pr-and-spec-index-preflight-hooks.md`
(phase-1 proposal). Reviewed artifact: PR #461 / commit `9be65e8a`
(`on-the-record/hooks/pr-preflight.sh`,
`on-the-record/hooks/spec-index-preflight.sh`,
`on-the-record/hooks/test_pr_preflight.py`,
`on-the-record/hooks/test_spec_index_preflight.py`,
`on-the-record/hooks/hooks.json`, `docs/specs/enforcement-boundary.md`), as
those files stand on this branch today (both hook scripts have since grown
unrelated extensions from later issues — #707, #741, #866, #882, #1177,
#1310 — which this review does not evaluate; only the original #459 scope
is checked). Spec: issue #459 body's two named failure shapes
(premature/missing `Closes` trailer, unregenerated spec-index). Approved
via issue-level comment `APPROVE issue-459/conformance-review` by
JiwonJung94 (approvers.md, single-account mode).

## What was done

Artifact-only re-read of `pr-preflight.sh` and `spec-index-preflight.sh`
against the proposal's numbered build steps (items 1-6) and its "How
you'll know it worked" acceptance list. Ran both hooks' own test suites
and `gates/test_boundary.py` as evidence:

canonical: `python3 on-the-record/hooks/test_pr_preflight.py` (this turn)
```
$ python3 on-the-record/hooks/test_pr_preflight.py
PASS: phase2 Closes with incomplete non-final step -> denied
PASS: phase2 no closing keyword, plan None -> denied
PASS: phase1 plain #459 reference -> allowed
PASS: phase2 Closes #459, plan None -> allowed
PASS: phase2 Closes #459, plan all done -> allowed
PASS: phase2 Closes #459, only final step incomplete -> allowed
PASS: _plan_from_body parses steps
PASS: _plan_from_body returns None with no header
PASS: check_body(126, 'Closes #126', 'phase1') == [] (unchanged, gate lives outside check_body)
PASS: _phase1_closes_ref(126, 'Closes #126') finds it -> would deny
PASS: PR #763 shape: check_body('phase1') allows (plain ref present)
PASS: PR #763 shape: _phase1_closes_ref finds 'Closes #743' -> would deny
PASS: decoy shape: a naive .search() call would find the wrong issue (#999)
PASS: decoy shape: _phase1_closes_ref still finds the real 'Closes #743' via finditer
PASS: phase1 plain #459 reference only: check_body allows (existing case)
PASS: phase1 plain #459 reference only: _phase1_closes_ref finds nothing -> allowed
All checks passed
```

canonical: `python3 on-the-record/hooks/test_spec_index_preflight.py` (this turn)
```
$ python3 on-the-record/hooks/test_spec_index_preflight.py
PASS: red: tracked file staged content changed, index not staged -> mismatch
PASS: red: tracked file changed, index staged but still carries OLD hash
PASS: green: tracked file changed, staged index carries matching NEW hash
PASS: green: unrelated file staged, tracked file untouched -> no mismatch
PASS: green: tracked file staged but content unchanged -> no mismatch
PASS: skip: tracked file staged but git show failed (deletion) -> no mismatch
PASS: trigger: plain `git commit` is recognized
PASS: trigger: issue #866 regression — `git -c k=v commit` is recognized
PASS: trigger: `git log --grep=commit` is not a commit invocation
PASS: trigger: `git commit-tree` is not `git commit`
PASS: trigger: 'commit' only inside a quoted string is not a commit invocation
PASS: trigger: unparseable command (unbalanced quote) fails open -> False
PASS: trigger: issue #882 regression — `(git commit -m x)` subshell wrap is recognized
PASS: trigger: `cd /tmp && git commit -m x` chained invocation is recognized
all tests passed
```

canonical: `python3 gates/test_boundary.py` (this turn)
```
$ python3 gates/test_boundary.py
ok - t_a_new_unrecorded_module_is_caught
AssertionError: acceptance_authoring_rule.py, check_runner.py, merge_gate.py,
spawn_on_pr.py, tool_learnings_gate.py, tool_learnings_tracker.py 가
docs/specs/enforcement-boundary.md 에 판정이 기록된 행으로 없다 (#441)
```

canonical: read `on-the-record/hooks/hooks.json` and
`docs/specs/enforcement-boundary.md` directly (this turn) for the two new
wiring entries/rows. One verdict rendered per requirement below.

## Verdicts

**R1 — `pr-preflight.sh` intercepts `gh pr create`/`gh pr edit`, zero-install
(no `gates/` import), extracts body from the command line itself: Present.**
canonical: `on-the-record/hooks/pr-preflight.sh` (read this turn). Line 48
filters on `\bgh\s+pr\s+(create|edit)\b`; the entire `check_body`/
`_plan_from_body` logic is ported inline in the script's embedded Python
(lines 318-431), no `import gates.*`; body extraction reads
`--body`/`--body-file` off `cmd` itself (lines 71-92), never `gh pr view`
(no PR exists yet at `create` time).

**R2 — Phase/issue resolution from branch name + `APPROVE issue-<n>/<role>`
comment: Present.** canonical: `on-the-record/hooks/pr-preflight.sh` (read
this turn), lines 98-142. Derives `issue`/`role` from
`^issue-(\d+)/([\w-]+)$` against `git rev-parse --abbrev-ref HEAD`, then
sets `phase2` by scanning `gh issue view --json comments` for an exact
`APPROVE issue-<n>/<role>` body from an `approvers.md`-listed login — the
same rule the proposal cites from `gates/ci.py`'s approved-roles check.

**R3 — `check_body` rule ported exactly (phase-1 plain `#n` required/Closes
forbidden; phase-2 incomplete non-final plan forbids Closes; phase-2
otherwise requires Closes): Present.** canonical:
`on-the-record/hooks/pr-preflight.sh` lines 368-393 (read this turn),
cross-checked against the `test_pr_preflight.py` run above. `check_body`
matches the proposal's build-step-1 wording for all three branches; the
red/green cases `phase2 Closes with incomplete non-final step -> denied`
and `phase1 plain #459 reference -> allowed` in the run above exercise
exactly those branches.

**R4 — Deny (exit 2) names the exact expected trailer; fail-open on any
lookup/parse gap: Present.** canonical:
`on-the-record/hooks/pr-preflight.sh` lines 32-46, 95, 102-108, 127
(read this turn). `deny()` (line 32) always emits both the violation and
an `expected:` hint line built from `hint` (lines 397-400); every early-exit
path (missing `gh`/`python3`, unmatched command, unparseable body,
non-issue branch, failed `gh` lookup, unreadable body-file) resolves to
`sys.exit(0)`/shell `exit 0`, never a silent deny or a silent
approve-without-checking on a positive violation.

**R5 — `test_pr_preflight.py` covers the four named acceptance shapes
(#447/#458 premature-Closes, #448 missing-Closes, phase-1 plain-`#n`):
Present.** canonical: `python3 on-the-record/hooks/test_pr_preflight.py`
run above (this turn) — cases `phase2 Closes with incomplete non-final
step -> denied`, `phase2 no closing keyword, plan None -> denied`, and
`phase1 plain #459 reference -> allowed` map directly to the three named
shapes; file exists at the exact acceptance-named path
`on-the-record/hooks/test_pr_preflight.py`.

**R6 — `spec-index-preflight.sh` intercepts `git commit`, ports
`parse_index` inline, hashes staged content via `git show :<path>`:
Present.** canonical: `on-the-record/hooks/spec-index-preflight.sh`
(read this turn), lines 66-73, 76, 108-115. Tokenizes `cmd` and checks for
`git`+`commit` tokens; `_ROW_RE` reproduces the index's row format
inline, no `gates/` import; `git_show_bytes` reads the staged blob via
`git show :<path>`, not the working-tree file, matching the proposal's
explicit "about-to-be-committed blob" requirement.

**R7 — Deny only when a tracked staged file's hash differs AND the index
itself isn't staged with a matching updated hash; regen command named:
Present.** canonical: `on-the-record/hooks/spec-index-preflight.sh`
(read this turn), lines 117-142. `rows` is swapped to the staged index's
own parsed rows when `reconciled-index.md` is itself staged (lines
118-124), so same-commit regen is checked against, not around; mismatches
are collected only for files both staged and tracked (lines 127-135); the
deny message (lines 138-142) names every mismatched file and the exact
regen command `python3 gates/spec_index.py --update`.

**R8 — Fail-open when the index doesn't exist/isn't readable or `git diff
--cached` fails: Present.** canonical:
`on-the-record/hooks/spec-index-preflight.sh` (read this turn), lines
80-81, 97-105 — index-missing/unreadable and `git diff --cached`
raising/nonzero both resolve to `sys.exit(0)`, the exact fail-open
triggers the proposal names.

**R9 — `test_spec_index_preflight.py` covers the named red/green pair:
Present.** canonical: `python3 on-the-record/hooks/test_spec_index_preflight.py`
run above (this turn) — `red: tracked file staged content changed, index
not staged -> mismatch` and `green: tracked file changed, staged index
carries matching NEW hash` map directly to the two acceptance-named cases;
file exists at the exact acceptance-named path
`on-the-record/hooks/test_spec_index_preflight.py`.

**R10 — `hooks.json` wires both scripts as `command` entries inside the
existing `PreToolUse`/`Bash` matcher block, `contract-guard.sh` preserved
first: Present.** canonical: `on-the-record/hooks/hooks.json` (read this
turn), lines 38-44 — `pr-preflight.sh` is the entry immediately after
`contract-guard.sh` in the same `"matcher": "Bash"` block,
`spec-index-preflight.sh` is a later entry in the same block;
`contract-guard.sh` remains the earliest of the three, matching the
proposal's stated ordering.

**R11 — `enforcement-boundary.md` records a row for each new `.sh` file:
Present.** canonical: `docs/specs/enforcement-boundary.md` (read this
turn), lines 89 and 91 — a `pr-preflight.sh` row (`contract`) and a
`spec-index-preflight.sh` row (`contract`) both exist with the `new
(#459): ...` provenance note the proposal's build-step-6 calls for.

**R12 — acceptance criterion "`gates/test_boundary.py` runs clean with
both new `.sh` files recorded": Incorrect as a literal top-to-bottom run
today, but not a regression of #459's own delivery.** canonical:
`python3 gates/test_boundary.py` run above (this turn) — fails
`t_all_gates_modules_recorded`, but every failing row names a different
module (`acceptance_authoring_rule.py`, `check_runner.py`,
`merge_gate.py`, `spawn_on_pr.py`, `tool_learnings_gate.py`,
`tool_learnings_tracker.py`) — none of them `pr-preflight.sh` or
`spec-index-preflight.sh`, both of which are correctly recorded per R11.
This is drift introduced by later, unrelated issues that shipped `.py`
gates without a matching boundary row; #459's own two files still satisfy
the check unmodified.

unverifiable: whether `gates/test_boundary.py` was fully green at PR
#461's own landing time — no CI log or transcript from that merge was
read this turn; `docs/issue-459/reports/implementation.md`'s own text
asserts a clean run but that assertion predates this review and is not
independently re-derivable from current branch state, since six unrelated
modules have since been added without boundary rows.

## Why

Per-requirement fidelity verdicts, artifact-only, per the conformance-review
role's rulebook (never a holistic quality read, never a fix).

## What did not work

None — the requirement list was already scoped by the phase-1 proposal; no
method changes needed.

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

- **R12 — `gates/test_boundary.py` fails today, but for reasons outside
  #459's write scope.** Six unrelated `.py` gate modules
  (`acceptance_authoring_rule.py`, `check_runner.py`, `merge_gate.py`,
  `spawn_on_pr.py`, `tool_learnings_gate.py`, `tool_learnings_tracker.py`)
  lack a recorded row in `docs/specs/enforcement-boundary.md`. Addressed
  to: whichever role(s) shipped those modules — not #459's implementation,
  which correctly recorded both of its own new files (R11).

## Next steps

No finding routes back to #459's own delivery — all 11 requirements
extracted from the phase-1 proposal (R1-R11) render Present against the
artifact as it stands, evidenced by the `test_pr_preflight.py` and
`test_spec_index_preflight.py` runs above plus direct reads of both hook
scripts, `hooks.json`, and `enforcement-boundary.md`. The one Incorrect
verdict (R12) is a `test_boundary.py` failure caused by modules unrelated
to #459's two files and is flagged for the modules that actually lack a
row, not for re-work here. Overall: issue #459 conforms to its phase-1
proposal.

## Resolution path

R12: route to whichever role(s) shipped `acceptance_authoring_rule.py`,
`check_runner.py`, `merge_gate.py`, `spawn_on_pr.py`,
`tool_learnings_gate.py`, `tool_learnings_tracker.py` to add their missing
`docs/specs/enforcement-boundary.md` rows — out of #459's frozen write set,
no action needed from this issue.
