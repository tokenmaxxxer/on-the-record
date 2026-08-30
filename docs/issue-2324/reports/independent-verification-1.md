---
issue: 2324
role: independent-verification-1
author: independent-verification-1
skills: work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2852's own deliverable
code_under_review: docs/issue-2324/_assets/measure_batching_headroom.py (untracked on this branch; exists only on PR #2852 branch issue-2324/diagnose-first-3c31bf9d, tip 321af046, not yet merged), tests/test_directive_diet_2135.py (same, untracked here), docs/issue-2324/reports/diagnose-first-3c31bf9d.md (same, untracked here)
type: verification
breaking: false
verdict: pass-with-disclosed-discrepancy — every reproducible acceptance claim in PR #2852 independently reproduces (gate test, PR-scoped diff, directive-file-untouched, monitor/watchdog tests, full-suite pass/fail counts, table sum-arithmetic, cited upstream shas); 1 of the PR's 10 headroom-table rows does not reproduce against its own cited, unchanged transcript file — but the corrected aggregate (derived below) still clears the same pre-declared threshold, so the PR's STOP-AND-REPORT conclusion (no directive-file edit) survives the correction.
loop_state: complete
upstream:
  - path: docs/issue-2324/reports/diagnose-first-3c31bf9d.md
    sha: 321af046e8193ebe44d8d71bad4f50dfea741fb5
  - path: docs/issue-2324/_assets/measure_batching_headroom.py
    sha: 321af046e8193ebe44d8d71bad4f50dfea741fb5
  - path: tests/test_directive_diet_2135.py
    sha: 321af046e8193ebe44d8d71bad4f50dfea741fb5
---

# issue-2324 — independent-verification-1 record

## What was done

Independently verified PR #2852 (`issue-2324/diagnose-first-3c31bf9d`,
tip `321af046`) — canonical: `gh pr view 2852` output (state: OPEN,
mergeable: MERGEABLE), read this session. The PR's own record and code
artifacts — `docs/issue-2324/reports/diagnose-first-3c31bf9d.md`
(untracked on this branch), `docs/issue-2324/_assets/measure_batching_headroom.py`
(untracked on this branch), `tests/test_directive_diet_2135.py`
(untracked on this branch) — exist only on PR #2852's own branch (not
yet merged). Checked out that branch into an isolated `git worktree`
(`git worktree add /tmp/pr2852-verify origin/issue-2324/diagnose-first-3c31bf9d`)
and re-derived every checkable claim from scratch there, rather than
trusting the PR's own pasted output. Below, "the PR's record" always
means that same untracked-here file read from the worktree.

- acceptance: `python3 -m pytest tests/test_directive_diet_2135.py -v` — result:
```
7 passed in 0.90s
```
  matches the PR's claim.

- acceptance: `grep -n -iE "\brole\b" docs/issue-2324/_assets/measure_batching_headroom.py tests/test_directive_diet_2135.py`
  — result: no match (exit 1) — matches the PR's retired-role-axis
  claim (issue #2741).

- The two-dot `git diff origin/main --stat` initially showed 18 changed
  files including large deletions; this was a verification-methodology
  mistake, corrected before being reported — see "What did not work".
  The PR-scoped (merge-base) comparison: acceptance: `git diff
  origin/main...HEAD --stat` — result:
```
 .../_assets/measure_batching_headroom.py           | 157 +++++++
 docs/issue-2324/reports/diagnose-first-3c31bf9d.md | 465 +++++++++++++++++++++
 .../20260830T052046092073-0e7be548a00e8a5a.md      |  25 ++
 tests/test_directive_diet_2135.py                  | 212 ++++++++++
 4 files changed, 859 insertions(+)
```
  matches the PR's own `gh pr view 2852` file list (4 files, all
  ADDED, additions 157+465+25+212=859, deletions 0) and its "only new
  files" claim.

- acceptance: `git diff origin/main --stat -- directive_assembly.py .on-the-record/directive/ on-the-record/directive/`
  — result: empty (0 lines) — matches the PR's "no overhead increase"
  claim.

- acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q`
  — result:
```
36 passed in 2.43s
```
  matches the PR's monitor/watch-machinery claim.

- acceptance: `python3 -m pytest test/ tests/ -q` — result:
```
15 failed, 462 passed, 3 xfailed in 31.45s
```
  and the 15 failing test names printed by this run are byte-identical
  to the 15 names the PR's record pastes in its own acceptance section
  (checked by eye, name for name) — matches the PR's "no new bug"
  claim in full, not just the headline counts.

- derived: re-summed the PR record's own 10 per-row tuples independently
  in a fresh process —
```
python3 -c "
rows=[(18,2,10,5),(67,0,16,3),(50,15,15,4),(36,1,8,2),(53,5,14,5),
      (77,6,19,7),(123,0,34,7),(70,0,20,4),(101,3,25,5),(118,5,51,15)]
total=sum(r[0] for r in rows); multi=sum(r[1] for r in rows)
single=sum(r[2] for r in rows); pairs=sum(r[3] for r in rows)
print(total, multi, single, pairs, f'{100*multi/total:.2f}%', f'{100*single/total:.2f}%', f'{100*pairs/total:.2f}%')
"
```
  result: `713 37 212 57 5.19% 29.73% 7.99%` — matches the PR record's
  stated sum row exactly; the PR's arithmetic on its own inputs is
  correct.

- derived: `git cat-file -e` on all three shas the PR cites as upstream
  (`90d1c5a7c7dc3197cb2b43e9baa2b1c53a2e7238`,
  `81a628df4bdcb8b00524c418f17c4f6063654c65`,
  `a7a7417aeadaa9e37fcc3d509834f1e37a840dd0`) — all three exit 0
  (resolve to real objects); none are dangling references.

- Re-ran the PR's own committed measurement script against every one of
  its 10 cited transcripts still present under `$MUSTER_WORKSPACE_ROOT`
  in this environment: derived: `ls
  "$MUSTER_WORKSPACE_ROOT"/*.session.*.log | wc -l` — result: `36` files
  present, of which 7 of the PR's 10 cited names matched (the other 3,
  `2827-diagnose-first-6c16a19d`, `2749-adversarial-review-71d5dd92`,
  and `2749-silent-failure-audit-e9b54ddf`, are absent — their subject
  sessions had already landed/merged by the time this verification ran
  — canonical: this branch's own `git log --oneline -5` (read this
  session) shows commits `0b4bd643` and `76e3b216` already referencing
  those same two subjects, consistent with normal post-merge workspace
  cleanup rather than a PR fault). derived:
```
python3 docs/issue-2324/_assets/measure_batching_headroom.py \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2749-adversarial-review-28904fd2.session.20260830T115728.3966889.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2798-adversarial-review-99b10ef0.session.20260830T080603.2662095.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771.session.20260830T093054.3136489.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.session.20260830T094015.3166892.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2830-diagnose-first-7c274fa6.session.20260830T120848.4170669.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2847-diagnose-first-50e013fd.session.20260830T134944.497939.log"
```
  result:
```
transcript	total_turns	multi_tool_turns	single_small_call_turns	batchable_adjacent_pairs
2135-diagnose-first+minimalism-scoping	101	3	25	5
2749-adversarial-review-28904fd2	67	0	16	3
2798-adversarial-review-99b10ef0	70	0	20	4
2811-technical-writing-style-guide	123	0	34	7
2814-test-authoring-...	53	5	14	5
2830-diagnose-first-7c274fa6	36	1	8	2
2847-diagnose-first-50e013fd	80	15	28	8
```
  6 of these 7 rows are byte-identical to the PR record's own table —
  derived: comparing the block above against the PR record's table rows
  1-of-`2135`, 2-of-`2749-28904fd2`, 4-of-`2830`, 5-of-`2814`,
  7-of-`2811`, 8-of-`2798` (row numbers per the PR record's own
  numbering) line by line, all 6 match exactly. The 7th,
  `2847-diagnose-first-50e013fd` (the PR record's row 3), does **not**
  reproduce: the PR record's row 3 reads `50 | 15 | 15 | 4`, but the
  re-run above gives `80 | 15 | 28 | 8` (derived above) — 3 of the 4
  columns differ (`total_turns`, `single_small_call_turns`,
  `batchable_adjacent_pairs`; `multi_tool_turns` matches at `15`). See
  "Open findings" #1.

## Why

Chose worktree-based, from-scratch re-derivation over reading the PR's
pasted command output at face value, because this role's purpose is
independent verification: a pasted `derived:`/`acceptance:` line is
only as good as its last re-run, and the delivering PR's own record
already documents one self-caught measurement bug (line-per-turn vs
`message.id`-per-turn parsing), which is itself evidence that
first-pass output in this exact tool is not always trustworthy.
Re-running every reproducible table row (not only the script's already-
summed total) is what surfaced the one row that does not reproduce.

Investigated the `2847` mismatch rather than assuming environment
drift (the underlying session could plausibly have kept running after
being measured, which would explain a larger current transcript):
derived:
```
stat -c '%y %n' "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2847-diagnose-first-50e013fd.session.20260830T134944.497939.log"
```
result: mtime `2026-08-30 14:09:59 +0900` = `05:09:59Z` — earlier than
both of the PR's own commits (`b5ad704a` at `05:19:15Z`, `321af046` at
`05:21:07Z` — canonical: `gh pr view 2852 --json commits` output, read
this session) and this check itself (`date -u` at `05:24:04Z`), with no
later write to the file in between (single mtime, unchanged across two
separate re-runs of the script in this session). This rules out
"the session kept running after being measured" as the explanation:
the file's content was already in its post-measurement state before
the PR was committed. Cross-checked independently with `jq` (not the
PR's own script, to avoid trusting the same code twice) counting
distinct `message.id` values under `type=="assistant"`: derived: `jq
-r 'select(.type=="assistant") | .message.id' <file> | sort -u | wc -l`
— result: `82` — consistent with the script's own `80` (a small number
of assistant messages carry no countable content block) and
inconsistent with the PR record's claimed `50`.

## What did not work

The first `git diff origin/main --stat` run inside the PR worktree
showed 18 changed files including large deletions (`spawn.py`,
`roster.py`, `on-the-record/hooks/self-update.sh`, several
`docs/issue-2749`/`docs/issue-2827` report files), which would have
contradicted the PR's own "only new files" claim if reported as-is.
Investigated before reporting: derived: `git rev-list --left-right
--count origin/main...HEAD` — result: `3	2` — the PR branch is 3
commits behind current `origin/main` (unrelated commits landed on
`main` after the PR's branch point) and 2 ahead. Two-dot `git diff A
--stat` diffs tip-to-tip, so it necessarily includes every unrelated
change `main` picked up in between; `git diff origin/main...HEAD`
(triple-dot, merge-base-relative — the same comparison GitHub computes
for a PR's own diff view) gives the PR-scoped result reported above (4
files, matching the PR's claim). No finding was filed on this — it was
a verification-methodology mistake on this session's own part,
corrected before being written down, not a defect in the PR.

## Upstream basis

- derived: `git show origin/issue-2324/diagnose-first-3c31bf9d:docs/issue-2324/reports/diagnose-first-3c31bf9d.md`
  (sha `321af046`, PR #2852 branch tip, not yet merged; untracked on
  this branch) — the record under verification, read in full this
  session.
- derived: `git show origin/issue-2324/diagnose-first-3c31bf9d:docs/issue-2324/_assets/measure_batching_headroom.py`
  (same sha, same branch, untracked here) — the measurement instrument
  re-run independently above.
- derived: `git show origin/issue-2324/diagnose-first-3c31bf9d:tests/test_directive_diet_2135.py`
  (same sha, same branch, untracked here) — the gate test re-run
  independently above.

## Open findings

1. **Headroom-table row 3 (`2847-diagnose-first-50e013fd`) does not
   reproduce against its own cited transcript file** (derived above:
   PR record's row reads `50 | 15 | 15 | 4`, this session's re-run of
   the PR's own committed script against the unchanged transcript gives
   `80 | 15 | 28 | 8`). Effect on the PR's conclusion: derived:
```
python3 -c "
rows=[(18,2,10,5),(67,0,16,3),(80,15,28,8),(36,1,8,2),(53,5,14,5),
      (77,6,19,7),(123,0,34,7),(70,0,20,4),(101,3,25,5),(118,5,51,15)]
total=sum(r[0] for r in rows); pairs=sum(r[3] for r in rows)
print(f'{pairs}/{total} = {100*pairs/total:.2f}%')
"
```
   result: `61/743 = 8.21%` — still below the PR record's own
   pre-declared 10-15% action threshold — canonical: the PR record's
   own "Why" section, which states the threshold was chosen "before
   measuring" (read this session, PR #2852 branch) — so the PR's
   STOP-AND-REPORT decision (no directive-file edit) is unchanged by
   this correction. This is a data-accuracy defect in one evidence row,
   not a defect in the PR's decision logic. Resolution path: a human
   maintainer or a follow-up PR should correct that one row (or
   re-run the full table fresh) in the PR's own record — untracked on
   this branch, `docs/issue-2324/reports/diagnose-first-3c31bf9d.md` on
   PR #2852's branch — before treating its exact 7.99% figure as
   authoritative; this record's own corrected figure (`8.21%`, derived
   above) should be cited instead until that correction lands.
2. 3 of the PR's 10 cited transcripts are no longer present in this
   environment (see "What was done"), so their rows could not be
   independently re-derived by this verification — only cross-checked
   for internal arithmetic consistency against the PR's own sum, which
   passed (derived above: `713 37 212 57 5.19% 29.73% 7.99%`). Not
   attributed to the PR as a fault: normal post-merge workspace cleanup
   is a plausible, unforced explanation, and 6 of the 7 still-available
   rows reproduced exactly. Resolution path: none needed unless a
   future audit has specific reason to distrust these 3 rows too.
3. The PR record's own disclosed Open findings 1 and 3 — no
   MultiEdit-over-serial-Edit sentence added to `_TURN_BUDGET_PROSE`,
   and the token-overlap dependency heuristic not validated against
   hand-labeled data — canonical: the PR's own record (untracked on
   this branch, PR #2852 branch), "Open findings" section 1 and 3, read
   this session — are pre-existing, disclosed limitations, not
   independently re-derived further here; both are already correctly
   scoped in the record under review.

## Next steps

None — this record is terminal. `loop_state: complete` reflects that
every acceptance/derived check above was executed this session
(canonical: this record's own "What was done" section, whose
`acceptance:`/`derived:` lines are this session's own freshly-run
`pytest`/`git`/`jq`/`python3` output, not a re-paste of the PR's
claims) and no further check remains queued. A human maintainer should
read Open finding #1 before deciding whether to merge PR #2852 as-is
(the threshold-crossing conclusion is unaffected by the one-row
discrepancy) or request the one-row correction first.

skill-verdict: work-in-english — applied: invoked; this record, its
commit, and its PR are written in English throughout (the spawning
instructions and issue body were partly in Korean).
skill-verdict: observability-phase-trace — not-applicable: this record
verifies a measurement-only diagnostic PR, not a phase-2 implementation
record's signal set against a named methodology phase-1.
skill-verdict: defect-verification-severity-band-assignment —
not-applicable: this session's own Open finding #1 is a data-accuracy
defect in one evidence row of a diagnostic record, not a reproduced
code defect being routed through the docs/issue-<n>/reports/
defect-verification workflow this skill's halting/degrading/cosmetic
band table targets.
skill-verdict: issue-retrospective-timeline-comprehensibility-and-subtraction-rules —
not-applicable: this is a single-subject independent-verification
record, not a cross-skill retrospective Timeline/Contributing-factors/
Action-items composition.
skill-verdict: verify-finding-record — not-applicable: this record's
path is docs/issue-2324/reports/independent-verification-1.md, not
docs/issue-<n>/reports/defect-verification.md, and its content is a PR
audit rather than a reproduction-attempt outcome in that workflow's
three-value schema.
skill-verdict: market-analysis-mece-proposal — not-applicable: no
phase-1 proposal is being authored or reviewed in this session; PR
#2852 is a phase-2/diagnostic delivery.

