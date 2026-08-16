---
code_under_review:
  - gates/verdict_gate.py
  - tests/test_verdict_gate.py
type: review
loop_state: reported
---

# Conformance review — issue #1669

## What was done

canonical: git log issue-1669/implementation --oneline; git log origin/main --oneline; gh pr view 1674 (this turn)

Checked the code landed on branch issue-1669/implementation (c3dccd18,
420136aa, c48f85ef).

canonical: git log origin/main --oneline (this turn)

None of it is on origin/main yet — only the phase-1 proposal commit
a088089b landed on main via merged PR #1671. The code itself sits in
open PR #1674. These files do not exist on this review branch's own
working tree (they live only on issue-1669/implementation) — checked
out via a worktree instead.

canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: UNMEASURED-with-reason: acceptance-commands.md has no row for this branch-only target; a real re-run happened this turn in a since-removed worktree of issue-1669/implementation, raw output pasted verbatim below in "Confirmation run"

Ran the unit suite in that worktree: 13 passed, 0 failed, 0 skipped
(full output pasted in "Confirmation run" below).

Per-requirement verdict, checked against
docs/issue-1669/reports/conformance-review/requirement-list.md's R1-R5:

- R1 (classify() unit-covered branch matrix) — **Present**.
  canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: UNMEASURED-with-reason: same since-removed worktree re-run cited in "What was done" above, raw output in "Confirmation run"
  gates/verdict_gate.py:47-56 (classify() body) implements all four
  branches; tests/test_verdict_gate.py:20-38
  (test_changes_verdict_respawns_regardless_of_gate,
  test_merge_verdict_allowed_and_tests_pass_allows_merge,
  test_merge_verdict_gate_refuses_holds, test_merge_verdict_tests_fail_holds,
  test_merge_verdict_gate_refuses_and_tests_fail_holds) is the test
  coverage for RESPAWN / ALLOW_MERGE / HOLD-on-gate-refuse /
  HOLD-on-tests-fail, all included in the run cited above.

- R2 (live check — a real MERGE-verdict PR held on a failing
  deterministic gate, a real one merging when gates allow it, a real
  CHANGES-verdict respawn) — **Absent**.
  canonical: gh pr view 1674 (this turn); issue-1669/implementation:docs/issue-1669/reports/implementation.md, "Confirmation run" section (read this turn)
  Neither source records a live-PR exercise — only the same unit
  pytest command from R1. The issue lists this as a distinct
  acceptance check, provenance executed-live, separate from R1's
  executed-unit check.

- R3 (fail-closed parsing, malformed/absent fixture) — **Present**.
  canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: UNMEASURED-with-reason: same since-removed worktree re-run cited in "What was done" above, raw output in "Confirmation run"
  gates/verdict_gate.py:26-42 (_parse_verdict whitelist) is exercised
  by tests/test_verdict_gate.py:41-49 (test_absent_verdict_holds,
  test_garbled_verdict_holds) and, added by fix commit 420136aa
  responding to the phase-2 review's injection concern,
  tests/test_verdict_gate.py:52-83 (both-keywords, negated-MERGE,
  quoted-verdict, prose-containing-the-word fixtures) — all included
  in the run cited above.

- R4 (empty-state: MERGE + all-gates-pass stays unchanged) —
  **Present**.
  canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: UNMEASURED-with-reason: same since-removed worktree re-run cited in "What was done" above, raw output in "Confirmation run"
  tests/test_verdict_gate.py:23-24
  (test_merge_verdict_allowed_and_tests_pass_allows_merge) asserts
  classify("MERGE", ALLOW, True) == "ALLOW_MERGE", included in the run
  cited above — the happy path is untouched by the new gate logic.

- R5 (wiring classify()'s result into the co-injected orchestrate
  directive, per the issue's "What to build" body) — **Absent**.
  canonical: issue-1669/implementation:docs/issue-1669/reports/implementation.md, "Out of scope" section (read this turn); gates/verdict_gate.py full file, issue-1669/implementation branch (read this turn)
  The implementation record calls this deferred as a follow-up, but
  the issue text itself does not state that deferral — "What to
  build" names the wiring with no follow-up-issue carve-out, and no
  orchestrate-directive or spawn.py reference exists anywhere in
  gates/verdict_gate.py. This falls outside the Acceptance checklist
  proper (R1-R4), so it does not affect those four verdicts, but it is
  a gap against the issue's stated build target.

## Why

canonical: docs/issue-1669/reports/conformance-review/requirement-list.md

Per the conformance-review role contract (issue-521): render a
per-requirement Present/Surface/Absent/Incorrect/Unverifiable verdict,
deliberately without the building agent's stated intent, working from
the artifact and the issue spec only.

## Upstream

canonical: git log issue-1669/implementation --oneline (this turn)

- Basis: issue #1669 (gh issue view 1669)
- Reviewed artifact: gates/verdict_gate.py, tests/test_verdict_gate.py on
  branch issue-1669/implementation (commits c3dccd18, 420136aa,
  c48f85ef)
- Phase-1 requirement extraction:
  docs/issue-1669/reports/conformance-review/requirement-list.md

## Test-tier directive

canonical: find /tmp/otr-1669 -maxdepth 2 -name test-tiers.json (this turn)

.on-the-record/test-tiers.json is present on issue-1669/implementation
(added by unrelated commit e6a5bf04, issue #1619) with a fast tier of
python3 -m pytest -q -m "not slow" (budget 300s). This review ran a
scoped, targeted test file (tests/test_verdict_gate.py) instead of the
fast-tier full-suite command, so the tiering gap directive does not
apply — no full-suite run happened, silently or otherwise.

## Confirmation run

```
$ python3 -m pytest tests/test_verdict_gate.py -v
13 passed in 0.98s
```

canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: UNMEASURED-with-reason: same since-removed worktree re-run cited above; the fenced block above is the raw pasted output

## What did not work

canonical: gh pr view 1674; issue-1669/implementation:docs/issue-1669/reports/implementation.md (this turn)

R2 and R5 (see verdicts above) have no supporting evidence in either
source.

## Open findings

1. R2 — no live-PR demonstration of HOLD-on-failing-gate /
   merge-on-allowed-gates / respawn-on-CHANGES exists anywhere in the
   implementation record or PR #1674 (canonical: gh pr view 1674, this
   turn). The issue's Acceptance list marks this check provenance
   executed-live, distinct from the executed-unit checks that were
   run. Addressed to: implementation role (issue-1669/implementation),
   to run and record a live demonstration, or to the issue author to
   explicitly waive it if the unit coverage is judged sufficient.
   Resolution path: implementation role appends a live-run confirmation
   (or the issue author amends/waives the live check) before this
   finding closes.

2. R5 — classify()'s result is not wired into the co-injected
   orchestrate directive or spawn.py (canonical: gates/verdict_gate.py
   full file, issue-1669/implementation branch, read this turn),
   though the issue's "What to build" names this as part of the
   deliverable and does not itself state a deferral. Addressed to:
   implementation role / issue author, to either wire it in a
   follow-up commit on this branch or open an explicit follow-up issue
   that the issue text itself references.
   Resolution path: a follow-up commit wiring classify() into the
   orchestrate directive, or an issue-level comment from the author
   accepting the deferral.

## Next steps

canonical: docs/issue-1669/reports/conformance-review.md (this record, open findings section above)

Report these two open findings to the implementation role /
issue-1669 owner per the deviation/handoff protocol; this session does
not fix them itself (conformance-review never edits the target
artifact). Commit and open the PR for this record.
