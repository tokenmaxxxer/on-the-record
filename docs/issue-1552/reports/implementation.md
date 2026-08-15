---
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
type: bugfix
breaking: false
canonical: pytest run pasted verbatim in this file's "## Test run" section, executed this turn
acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result: pass, 16 passed, 0 skipped
verdict: pass
loop_state: landed
---

Subject: issue-1552

## Test run

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q
................                                                         [100%]
16 passed in 2.27s
```

## What was done

Extended `_MACHINE_BODY_RE` in `on-the-record/hooks/pr-preflight.sh`
(:269-275) with one more alternative, `APPROVE issue-\S+/\S+\s*$`, so a
bare single-account approval comment classifies as a machine/
reconciliation-exempt comment for the reconciliation-cursor block. The
watchdog `Judgment opened: `/`Verdict: PR ` shapes were already covered
(canonical: on-the-record/hooks/pr-preflight.sh:269-274, read directly,
during survey — docs/issue-1552/reports/implementation/survey.md).

Added `test_machine_body_re_classifies_three_observed_shapes` to
`on-the-record/hooks/test_pr_preflight.py`, which reads
`_MACHINE_BODY_RE`'s source straight out of `pr-preflight.sh` (rather
than duplicating the pattern) and asserts all three observed shapes —
`Judgment opened: ...`, `Verdict: PR #? -> escalate ...`, `APPROVE
issue-N/role` — classify as machine, and one non-templated human comment
("looks good, approving informally, ship it") still requires
reconciliation.

## Why

Issue #1552: on high-traffic issues, watchdog comments and the bare
approval token were landing during a role session's `gh pr create`
retries and re-triggering the reconciliation-gate check on every attempt
because `_MACHINE_BODY_RE` did not yet treat the approval-token shape as
exempt (the watchdog shapes were already exempt from a prior fix).

## Upstream basis

docs/issue-1552/reports/implementation/survey.md,
docs/issue-1552/proposals/machine-comment-approve-shape.md

## Doc-placement ladder

- No new env var, config key, dependency, or migration introduced —
  nothing owed to a handbook.
- No new library-or-format choice or changed public signature/wire
  format beyond this issue's own regex extension, already recorded in
  docs/issue-1552/proposals/machine-comment-approve-shape.md's Rationale
  — no separate docs/issue-1552/decisions/ entry needed.
- No benchmark/investigation numbers produced.

## Test-tier note (issue #1518)

derived: ls .on-the-record/test-tiers.json
```
$ ls .on-the-record/test-tiers.json
ls: cannot access '.on-the-record/test-tiers.json': No such file or directory
```
No tier config present in this repo — ran the targeted suite directly
(see "## Test run" above).

## What did not work

None.

## Open findings

None.

## Warrant hunt

Not dispatched: contract v3 s22 (headless single-shot session) forbids
ending a turn having delegated work not consumed within the same turn,
and this turn's remaining budget did not allow waiting on a hunter
dispatch before commit/push. Recorded here per the hunt-cadence
requirement rather than silently omitted.
