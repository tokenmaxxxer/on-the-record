---
proposal: build-now delivery, no proposal file (contract v3 s19a build-now bypass) — see docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea.md
---

# Hunt record — delivery

## before-landing — stance 0: assume the gate/guard logic just touched is bypassable — find the bypass

Verdict: FINDING — `_classify_narrowing_prs` conflates "PR number has no
entry in `number_to_branch`" with "PR's branch was never subject-shaped",
so a genuine subject-mapping-loss PR can be silently folded into the
never-printed non-subject count instead of getting its individual line +
recut-corrupted remediation.
Kind: silent-failure
Seed: watchdog.py `_classify_narrowing_prs` (~line 835) and its caller in
`_board_wide_sweep` (~line 1358); `closure_sweep._pr_index_all`
(gates/closure_sweep.py:175)
cap_seconds: 180
tier: full
diff_stat_lines: 460 (139+50+199+139 across 4 files per `git diff --stat`)
started_at: 2026-09-01T00:00:00Z
ended_at: 2026-09-01T00:20:00Z
canonical: watchdog.py:857-869 (`_classify_narrowing_prs`, `branch =
number_to_branch.get(prn)` then `m = _HEAD_REF_SUBJECT_RE.match(branch) if
branch else None` — `None` from either cause takes the same non-subject
branch); gates/closure_sweep.py:233 (`if branch and branch not in index:`
— first-wins dedup by branch string in `_pr_index_all`); watchdog.py:1360
(`number_to_branch = {v.get("number"): k for k, v in pr_index.items()}` —
inversion that drops any PR number whose branch was dedup-collapsed away)
(all read this turn)

### Reproduce
canonical: gates/closure_sweep.py:233 and watchdog.py:857-869,1360 (read
this turn) — mechanism cited above.

`closure_sweep._pr_index_all()` builds its branch->PR index with an
explicit first-wins dedup keyed by branch string (gates/closure_sweep.py:233).
When two PR numbers share the same head ref string, only one PR's number
survives as a value in that index. `_board_wide_sweep` inverts it
(watchdog.py:1360): `number_to_branch = {v.get("number"): k for k, v in
pr_index.items()}`, so the PR number that lost the dedup has no entry at
all — `number_to_branch.get(prn)` is `None` for it, indistinguishable in
`_classify_narrowing_prs` (watchdog.py:857-869) from "branch was never
subject-shaped."

```
python3 /tmp/repro_2979.py
```
`/tmp/repro_2979.py` calls `wd._classify_narrowing_prs(root, {100, 200},
{200: "issue-42/architecture-abc"}, board_now={})` directly, i.e. it feeds
`_classify_narrowing_prs` the exact `number_to_branch` shape
`_pr_index_all`'s dedup produces when two PR numbers share one branch
string: PR #100 has no entry (simulating dedup collision), PR #200 (same
branch) does. `issue-42` is absent from `board_now`.

### Observed
```
number_to_branch: {200: 'issue-42/architecture-abc'}
changed_numbers: set()
non_subject_count: 1
mapping_loss_new: [(200, 42, 'issue-42/architecture-abc')]
mapping_loss_already_reported: 0
```
PR #100 is counted only inside the aggregate `non_subject_count` line
("board 와 무관, 집계만") — it never gets an individual line, never calls
`_watchdog_note_unmappable_pr`, and never surfaces the recut-corrupted
remediation advice, even though its branch shape is identical to PR
#200's, which *does* get flagged as subject-mapping-loss.

### Expected
A PR number whose branch cannot be resolved because of an index dedup
collision (branch reused by another PR, e.g. a `recut-corrupted` retry
that reopens a new PR from the same subject branch name — the exact
remediation this code path itself recommends, per watchdog.py's printed
`spawn.py recut-corrupted --issue <n> --session <session>` line) is not
evidence the branch was ever non-subject-shaped. `_classify_narrowing_prs`
should not place it in the silently-aggregated bucket on that basis alone.
