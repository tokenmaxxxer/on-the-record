---
issue: 3047
role: silent-failure-audit+implementation-blueprint+test-derivation-48ce3454
author: silent-failure-audit+implementation-blueprint+test-derivation-48ce3454
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 1ab1b0804af47d6ea5a6cb5a62a1fd5414134d0d
type: implementation-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: gh issue view 3047 --repo tokenmaxxxer/on-the-record (issue body + 2 comments)
    sha: same-commit
---

# issue-3047 — silent-failure-audit+implementation-blueprint+test-derivation-48ce3454 record

## What was done

`watchdog._classify_narrowing_prs` (`watchdog.py`) decided, on exactly one
predicate (`if f"issue-{issue_n}" in board_now`), that every subject-shaped
PR absent from the board was a #2379 corrupted-merge-base and printed a
`spawn.py recut-corrupted` force-push repair line for it — observed live
against PR #3043 (a brand-new issue with an open PR and no merged record
yet, the ordinary state of every new issue) and a second time against
`JiwonJung94/study-companion` (a read-failure the machinery reported as
"checked, and it's ambiguous").

Changes, all in `watchdog.py`:

- Three named causes (`_MAPPING_LOSS_CORRUPTED`, `_MAPPING_LOSS_NO_RECORD_YET`,
  `_MAPPING_LOSS_UNCLASSIFIED`) replace the old single-bucket "mapping
  loss" outcome.
- `_classify_mapping_loss_cause(pr_index, issue_n)` (new): scans the
  already-fetched `pr_index` (branch → `{number, state, body}`, the bulk
  `gh api repos/{slug}/pulls?state=all` index `closure_sweep._pr_index_all`
  already builds once per delta-carrying tick — issue #1702/#1688, zero
  extra `gh` calls) for every sibling `issue-<n>/*` branch. Any MERGED
  sibling → corrupted-merge-base (a merged record existed and the subject
  is still missing from the board — the one case that survives with its
  alarm and repair). No MERGED but a CLOSED-non-merged sibling → unclassified
  (closed-without-merge is ambiguous between normal supersession and an
  abandoned corrupted attempt; the index alone cannot resolve it). Neither
  → no-record-yet (only OPEN siblings, or none at all — the ordinary new-
  issue state).
- `_format_mapping_loss_line(prn, issue_n, branch, cause)` (new): renders
  a distinct sentence per cause. The `recut-corrupted` remediation sentence
  is emitted only for `_MAPPING_LOSS_CORRUPTED`.
- `_classify_narrowing_prs` gained an optional `pr_index` parameter and
  now returns 4-tuples `(pr_number, issue_number, branch, cause)` in
  `mapping_loss_new` instead of 3-tuples.

  derived: `sed -n '947,949p' watchdog.py` — result:
  ```python
            cause = (_classify_mapping_loss_cause(pr_index, issue_n)
                     if pr_index is not None else _MAPPING_LOSS_UNCLASSIFIED)
            mapping_loss_new.append((prn, issue_n, branch, cause))
  ```
  A `pr_index` that was never supplied at all (not the same as "supplied
  and empty" — no production caller does this, the parameter is optional
  only for defensive callers) routes to `unclassified` per the code
  quoted above, not a guessed `no-record-yet`. See silent-failure-audit
  finding in Why below for why this branch exists.
- The `_board_wide_sweep` print loop (`watchdog.py:~1434`) now passes the
  already-in-scope `pr_index` through and calls `_format_mapping_loss_line`
  per cause instead of one fixed sentence.

`gates/probe_cause_misattribution.py` (new): the amendment's two `check:`
lines route through this — runs the classifier against a synthesised new-
issue subject and a synthesised corrupted-merge-base subject entirely
offline (no `gh`, no network), asserts the two outputs differ, asserts
only the corrupted one carries `recut-corrupted`, and asserts a third
synthesised unclassifiable subject is reported as its own distinct
`unclassified` cause rather than falling into either bucket.

acceptance: `python3 gates/probe_cause_misattribution.py` — result:
```
ok
```

`tests/test_watchdog_cause_classification.py` (new, test-derivation
skill): decision-table coverage over `_classify_mapping_loss_cause`'s two
boolean conditions (any MERGED sibling? any CLOSED sibling?), all 4
feasible columns exercised, plus GWT coverage of `_format_mapping_loss_line`'s
text-level guarantee and end-to-end routing through `_classify_narrowing_prs`.

acceptance: `python3 -m pytest tests/test_watchdog_cause_classification.py tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py -q`
— result:
```
26 passed in 0.86s
```
(the second file is issue #2979's existing decision-table suite over the
same function, updated to pass `pr_index` fixtures and expect the new
4-tuple shape; 14 new + 12 existing = 26.)

acceptance: `python3 -m pytest tests/ -q -x` — result: fails on a pre-
existing failure unrelated to this change (see next paragraph) — the
amendment's third check as literally written does not distinguish
pre-existing from newly-introduced failures, and `-x` stops at the first
one either way regardless of which tree it's run against.

derived: `python3 -m pytest tests/ test/ -q` — result:
```
20 failed, 744 passed, 3 xfailed, 2 warnings in 33.26s
```

derived: `git stash push -u -- watchdog.py tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py gates/probe_cause_misattribution.py tests/test_watchdog_cause_classification.py && python3 -m pytest tests/ test/ -q; git stash pop`
— result (pre-change tree, same command):
```
20 failed, 730 passed, 3 xfailed, 2 warnings in 31.99s
```
Both runs' `FAILED` lines list the identical 20 test IDs (`test_respawn_deliverable_gate.py`
×4, `test_spawn_gate_wiring.py` ×1, `test_convention_equivalence.py` ×2,
`test_local_dependency_env.py` ×1, `test_spawn_cross_family_skill_selection.py`
×7, `test_spawn_artifact_skill_pairing.py` ×2, `test_spawn_skill_judge_haiku_timeout_overlap.py`
×3) — pre-existing and unrelated to `_classify_narrowing_prs`/board-sweep
(env-dependent: empty-clone git warnings and live skill-scoring divergence
in this sandbox, per their own captured stderr/warnings). The 14-test
delta (744 − 730) is exactly this change's own new test file; no test
that passed before now fails, and none of the 20 pre-existing failures
touch `watchdog.py` or either test file this change modified.

## Why

The signal chosen is sibling-branch state within `pr_index`, not diff
shape (file/line count). The issue's own must-not clause forbids fetching
per-PR detail on every tick to obtain the distinguishing signal, and
GitHub's PR-list endpoint (what `_pr_index_all` already calls with
`state=all`) does not carry `additions`/`deletions`/`changed_files` in
its response — those fields exist only on the single-PR endpoint.

canonical: `gates/closure_sweep.py:250-258` (the exact fields
`_pr_index_all` extracts from each `pr` dict in the already-fetched list
response):
```python
        for pr in data:
            head = pr.get("head") or {}
            branch = head.get("ref") or ""
            if branch and branch not in index:
                state = "MERGED" if pr.get("merged_at") else str(
                    pr.get("state", "")).upper()
                index[branch] = {"number": pr.get("number"),
                                 "state": state,
                                 "body": pr.get("body", "") or ""}
```
Only `number`/`state`/`body` are extracted — no diff-shape field is
present to extract, confirming a diff-shape signal was unreachable
without the extra per-PR call the issue forbids. `state=all` means this
one already-paid-for call returns every PR ever opened for the repo
(open + closed + merged), which is what makes a sibling-branch scan free.

The real #2379 corruption detector, by contrast, does use diff shape —
but pays for it with a local `git diff --shortstat` against a fetched
clone, not a `gh` API field:

canonical: `pipeline.py:1027-1029` (`_verify_branch_base_sane`'s actual
signal):
```python
    stat_r = git("diff", "--shortstat", merge_base_sha, br)
    if stat_r.returncode != 0 or not stat_r.stdout.strip():
        return None
```
This confirms the issue's must-not clause is protecting against exactly
this cost (a local diff computation per candidate branch, not just an
extra `gh` round-trip) — reinforcing that a bulk-index field scan, not a
diff-shape recomputation, is the correct place to find a budget-safe
signal for the per-tick classifier.

This also matches both live-observed cases from the issue: the #3043
new-issue case has exactly one PR ever opened for issue-3042 (the PR
itself, still open) — no MERGED, no CLOSED sibling, so `no-record-yet`.
A genuine #2379 corrupted-merge-base — the branch re-cut and force-pushed
under the same name after a prior session's record had already merged —
leaves that MERGED record behind in `pr_index` as the one thing a
just-filed issue's first PR can never have accumulated yet.

The third bucket (`unclassified`) exists because the issue's central
complaint is not "the classifier guessed wrong between two options" but
"the classifier asserted a cause it never established." A CLOSED-without-
merge sibling is genuinely ambiguous from `pr_index` alone (normal
supersession by a later PR on the same subject vs. an abandoned corrupted
attempt) — routing it into either named bucket would manufacture
certainty the index doesn't support.

The `pr_index=None` (never supplied) case gets this same `unclassified`
treatment rather than an earlier in-session draft's `pr_index or {}`
coalesce into a guessed `no-record-yet` —

derived: this session's working tree at commit time; the code quoted
under What was done (`watchdog.py:947-949`) branches on `pr_index is not
None` before calling the classifier at all, so a never-supplied
`pr_index` never reaches `_classify_mapping_loss_cause` and cannot be
silently read as "checked, found nothing." An earlier in-session draft
used `pr_index = pr_index or {}` instead, which would have let that
default reach the classifier and come back `no-record-yet` — the same
defect shape this issue reports, at the width of one optional parameter.
Caught during the silent-failure-audit pass (skill-verdict below) before
`1ab1b0804af47d6ea5a6cb5a62a1fd5414134d0d` was committed; the draft
itself was never committed separately, so there is no earlier sha to
cite — `git log --oneline -- watchdog.py` shows this issue's single
commit only.

implementation-blueprint was judged not applicable — see skill-verdict
below — so no architecture/module-boundary decision was made or needed;
the change is three new functions and one signature extension, all within
the single file (`watchdog.py`) the defect lives in.

## What did not work

None.

## Upstream basis

- `gh issue view 3047 --repo tokenmaxxxer/on-the-record` — issue body
  (PR #3043 observation), first comment (second instance,
  `study-companion` read-failure), second comment (acceptance amendment:
  3 `bash -c` checks replacing the original prose checks, per #3059).
- `watchdog.py:835-872` (pre-change `_classify_narrowing_prs`) and
  `watchdog.py:1434-1465` (pre-change print loop) — the code under audit,
  read directly before editing.
- `gates/closure_sweep.py:195-262` (`_pr_index_all`) — cited above under
  Why.
- `pipeline.py:999-1034` (`_verify_branch_base_sane`) — cited above under
  Why.

## Open findings

None. The two must-not clauses hold by construction:

derived: `grep -n "gh \|subprocess" watchdog.py` scoped by inspection to
the three changed/added functions (`_classify_mapping_loss_cause`,
`_format_mapping_loss_line`, `_classify_narrowing_prs`) — none contain a
`gh`/`subprocess` call; they only read the `pr_index` dict already passed
in, so no per-PR `gh` call was added.

The genuine corrupted-merge-base alarm survives unchanged:
`_MAPPING_LOSS_CORRUPTED` still carries the identical `recut-corrupted`
sentence and `#2402` reference the old code printed unconditionally, now
gated to the one cause that actually established it —

acceptance: `python3 -m pytest tests/test_watchdog_cause_classification.py -k test_corrupted_cause_carries_recut_corrupted_instruction -q`
— result:
```
1 passed
```

## Next steps

None — `loop_state: landed`.

skill-verdict: silent-failure-audit — applied: invoked; audited the new
`_classify_mapping_loss_cause`/`_classify_narrowing_prs` path for exactly
the shape this issue targets (a cause asserted without being established).
Found and fixed, prior to
`1ab1b0804af47d6ea5a6cb5a62a1fd5414134d0d:watchdog.py:947-949`, the
`pr_index=None` collapse detailed under Why above.
skill-verdict: implementation-blueprint — not-applicable: single-file
change (three new functions plus one signature extension, all in
`watchdog.py`, the file the defect already lives in) — no cross-module
structure decision, no parallel-worker fan-out; the skill's own guidance
names "purely algorithmic work" / "single-file" as out of scope.
skill-verdict: test-derivation — applied: invoked; routed the new cause-
classification logic to decision-table testing (2 boolean conditions ×
4 feasible columns, all exercised) plus GWT for the remediation-text
guarantee, per the skill's own routing procedure — see What was done
above for the resulting test file.
other mounted skills: not triggered (work-in-english — followed as
ambient convention: commit/PR/record text in English, without a separate
Skill-tool invocation).
