---
kind: current-state-survey
subject: issue-452
code_under_review:
- on-the-record/UNENFORCED-CLAUSES.md
- on-the-record/commands/run.md
- gates/test_boundary.py
- docs/specs/enforcement-boundary.md
---

# Current-state survey — conformance review of issue #452's landed delivery

## Background

canonical: docs/issue-452/proposals/2026-08-08-ship-unenforced-clause-list.md,
read this session — approved phase-1 proposal pinning the delivery shape:
`on-the-record/UNENFORCED-CLAUSES.md` (new, derived extract), a reference
line in `on-the-record/commands/run.md`, two new `gates/test_boundary.py`
cases (exact-set match, reference-line presence), and a short note in
`docs/specs/enforcement-boundary.md`.

canonical: docs/issue-452/reports/implementation.md, read this session —
phase-2 record claims all four items delivered via commit `78a4295b`
(`feat(issue-452): ship unenforced-clause list in plugin payload`),
merged to main through PR #455 (merge commit `0195b2c6`).

This survey re-runs the proposal's own "How you'll know it worked"
acceptance commands against current repo state.

## Method

Ran each of the three acceptance checks named in the proposal's "How
you'll know it worked" section directly against the working tree.

## Findings

### File exists inside the plugin-deployed tree

acceptance: `ls on-the-record/UNENFORCED-CLAUSES.md` — result:
```
on-the-record/UNENFORCED-CLAUSES.md
```
file present at the required plugin-payload path.

### `run.md` reference line

acceptance: `grep -n "UNENFORCED-CLAUSES" on-the-record/commands/run.md` — result:
```
15:어떤 계약 절이 기계적으로 강제되지 않는지는 `${CLAUDE_PLUGIN_ROOT}/UNENFORCED-CLAUSES.md`
```
reference line present.

### Spec note

acceptance: `grep -n "UNENFORCED-CLAUSES" docs/specs/enforcement-boundary.md` — result:
```
169:`on-the-record/UNENFORCED-CLAUSES.md` (issue #452) is the derived,
```
sync note present.

### The two new `gates/test_boundary.py` cases, run individually

acceptance: `python3 -c "..."` invoking `t_unenforced_clauses_file_matches_spec_exactly`
and `t_run_md_references_unenforced_clauses` directly from
`gates/test_boundary.py` — result: both functions returned with no
exception raised (their own internal assertions did not fire):
```
t_unenforced_clauses_file_matches_spec_exactly PASS
t_run_md_references_unenforced_clauses PASS
```

### Full `gates/test_boundary.py` suite — fails, on an unrelated case

acceptance: `python3 gates/test_boundary.py` — result:
```
ok - t_a_new_unrecorded_module_is_caught
Traceback (most recent call last):
  ...
  File "gates/test_boundary.py", line 77, in t_all_gates_modules_recorded
    assert not bad, "\n".join(bad)
AssertionError: acceptance_authoring_rule.py 가 docs/specs/enforcement-boundary.md 에 판정(verdict)이 기록된 행으로 없다 — 기록되지 않은 게이트가 조용히 존재한다(#441).
check_runner.py 가 ...
merge_gate.py 가 ...
spawn_on_pr.py 가 ...
tool_learnings_gate.py 가 ...
tool_learnings_tracker.py 가 ...
```
the failing case, `t_all_gates_modules_recorded`, is #441's own
pre-existing catch-all check that every `gates/*.py` module has a
recorded verdict row; it is unrelated to the two cases issue #452's
proposal added.

acceptance: `git log -1 --format=%ci -- gates/spawn_on_pr.py` and
`git log -1 --format=%ci e00d1653` (issue-452's last landed commit,
"regenerate spec index hash baseline") — result:
```
2026-08-14 12:35:15 +0900
2026-08-08 17:33:27 +0900
```
`gates/spawn_on_pr.py` (one of the six unrecorded modules in the
failure above) was last touched six days after issue-452's delivery
landed; the six modules the failure lists are new/unrecorded gates
added after issue-452's commits, not anything issue-452's own change
introduced or broke.

## Summary table

| Acceptance item (proposal) | Re-run result |
|---|---|
| `on-the-record/UNENFORCED-CLAUSES.md` exists | present, per the `ls` acceptance run above |
| Content matches spec's `contract, CI-supplement` / `out of scope — operator decision` rows exactly | present, per the standalone `t_unenforced_clauses_file_matches_spec_exactly` acceptance run above |
| `run.md` reference line present | present, per the `grep` acceptance run above |
| `docs/specs/enforcement-boundary.md` sync note present | present, per the `grep` acceptance run above |
| Full `gates/test_boundary.py` suite green | fails, per the full-suite acceptance run above — on `t_all_gates_modules_recorded`, a pre-existing #441 catch-all unrelated to issue-452, tripped by six gates modules added 2026-08-14, after issue-452's own commits |

## What did not work

None.
