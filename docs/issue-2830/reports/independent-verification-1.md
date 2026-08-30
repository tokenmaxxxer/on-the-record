---
issue: 2830
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2830/reports/diagnose-first-7c274fa6.md  # untracked in this worktree; read via `gh pr diff 2833`, not a local checkout
    sha: 2292ed236b381e05f8accb637491163cbdc6666d
---

# issue-2830 — independent-verification-1 record

## What was done

Independently audited PR #2833 (branch `issue-2830/diagnose-first-7c274fa6`
→ main), the sole deliverable landed against this issue: a 345-line,
docs-only record reconstructing end-to-end pipeline latency for 5 named
issues from `gh` timestamps and session-log filesystem times.
canonical: `gh pr diff 2833` (full record body) and `gh pr view 2833
--json title,body,files,additions,deletions,commits` run in this session
— `files: [{"path":"docs/issue-2830/reports/diagnose-first-7c274fa6.md",
"additions":345,"deletions":0,"changeType":"ADDED"}]`.

Re-derived, from scratch and independently of the PR author's own
commands, every load-bearing number in that record:

- Re-ran `gh issue view <n> --json createdAt,closedAt` for all 5
  population issues (#2798, #2803, #2811, #2814, #2787) and `gh pr list
  --search "<n> in:body" --state all --json ...` for the same 5, plus
  #2749 and #2795 (used for the direct idle-gap measurement).
  derived: `gh issue view <n> --json createdAt,closedAt` run individually
  in this session for each of the 5, then `(closedAt - createdAt)` in
  minutes per issue:
  - #2798: 23:28:43 - 22:58:49 = 29.9
  - #2803: 00:28:08 - 23:32:43 = 55.4
  - #2811: 01:08:30 - 00:28:40 = 39.8
  - #2814: 01:19:43 - 00:38:00 = 41.7
  - #2787: 02:56:33(+1d) - 21:14:58 = 341.6
  All 5 match the record's per-issue table totals exactly.
- Confirmed the two edge cases the record calls out as non-routine both
  hold under independent recomputation: #2803's `E2` correctly uses the
  closing round's PR (#2808, createdAt 00:09:55Z), not the superseded
  #2804 (createdAt 23:43:17Z, from the same `gh pr list --search "2803
  in:body"` output) — using #2808 reproduces S1 = 00:09:55-23:32:43 =
  37.2 min; and #2814's `E4` (verify PR #2821, createdAt 01:30:56Z)
  lands after `E6` (issue #2814 closedAt 01:19:43Z), producing the
  reported negative `S3` (-11.2 min): S1+S2+S3 = 38.6+14.3+(-11.2) =
  41.7, matching the independently re-derived issue total above.
- Re-verified the "verification does not gate issue closure" finding by
  comparing each issue's `closedAt` against its implementation PR's
  `mergedAt` directly.
  derived: from the same `gh issue view`/`gh pr list` output above — all
  5 pairs within 1 second: #2798 closedAt 23:28:43Z vs #2799 mergedAt
  23:28:42Z (delta = 1s); #2803 closedAt 00:28:08Z vs #2808 mergedAt
  00:28:07Z (delta = 1s); #2811 closedAt 01:08:30Z vs #2816 mergedAt
  01:08:29Z (delta = 1s); #2814 closedAt 01:19:43Z vs #2820 mergedAt
  01:19:42Z (delta = 1s); #2787 closedAt 02:56:33Z vs #2826 mergedAt
  02:56:32Z (delta = 1s).
- Re-read the #2814 failed-spawn event trace the record cites.
  canonical:
  `on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.events.jsonl`
  under `$MUSTER_WORKSPACE_ROOT`, read in this session via a `python3`
  one-liner parsing `session-start`/`gate-refusal`/`session-end` events
  and converting each `ts` to KST — output: `09:40:15 session-start
  {pid: 3168489, ...}`, `09:53:29 gate-refusal {gate:
  pretooluse-dispatcher, ...}`, `09:53:36 session-end {outcome: refused,
  reason: "pull request create failed..."}` — verbatim match to the
  record's citation. The resulting gap to PR #2820's `createdAt`
  (01:16:36Z = 10:16:36 KST) also reproduces: 10:16:36 - 09:53:36 = 23
  min.
- Re-derived the n=2 idle-gap measurement (#2749, #2795) from `gh pr
  list` timestamps and `stat --format='%z'` / `ls --time-style=full-iso`
  on the surviving `task.txt`/`.session.*.log` files.
  derived: PR #2823 (issue #2749) createdAt=2026-08-30T02:49:36Z
  (11:49:36 KST); `on-the-record-issue-2749-adversarial-review-28904fd2.task.txt`
  stat mtime 11:57:03; session log filename timestamp
  `20260830T115728` (11:57:28) → idle gap = 11:57:28-11:49:36 = 7.87
  min. PR #2824 (issue #2795) createdAt=2026-08-30T02:49:52Z (11:49:52
  KST); `on-the-record-issue-2795-adversarial-review-a1341cc3.task.txt`
  stat mtime 11:57:51; session log filename timestamp `20260830T115831`
  (11:58:31) → idle gap = 11:58:31-11:49:52 = 8.65 min. Mean = (7.87 +
  8.65) / 2 = 8.26 min, matching the record's cited mean exactly.
- Confirmed the diff outside `docs/` is empty and the test-collection
  count is unchanged, per the record's must-not-compliance claim.
  canonical: `git diff origin/main origin/issue-2830/diagnose-first-7c274fa6
  -- . ':!docs' --stat` run in this session — no output (empty); full
  `--stat` shows exactly one file added
  (`docs/issue-2830/reports/diagnose-first-7c274fa6.md`, untracked in
  this worktree, 345 insertions).
  derived: `python3 -m pytest test/ -q --collect-only` run in this
  session, output = `443 tests collected in 0.26s` — this matches the
  record's cited count (derived: same `python3 -m pytest test/ -q
  --collect-only` command, 443 = 443).

One discrepancy found in a secondary corroboration figure; reported in
Open findings §1 below with its own `canonical:` citation. It does not
change the verdict — see Why.

## Why

Reproducing every `derived:`/`canonical:`-tagged number independently
(rather than reading the record and trusting its arithmetic) is the
standard this repo's own record-claim-guard gate and the acceptance
criteria's `provenance: executed-live` requirement set — and per the
issue body's own framing, #2135 is the cautionary example of a
measurement/attribution issue where insufficient rigor upstream cost a
full remeasurement cycle. Given #2830 is itself a measurement-only issue
whose entire value is the correctness of its numbers, a sample
spot-check was not enough: every segment total, both edge cases the
record called out as non-routine, and the two headline findings ("no
dominant segment in the routine case" and "verification does not gate
closure") were independently recomputed from raw `gh`/filesystem data in
"What was done" above, not re-read from the record's own prose.

All three acceptance checks are met by PR #2833:

- **Segment attribution closing on the total**: verified exactly for all
  5 issues (e.g. S1+S2+S3 = 41.7 for #2814 as shown above, and
  equivalently for the other 4), including the two irregular cases
  (#2803's send-back, #2814's negative `S3`, #2787's missing separate
  verification PR).
- **Dominant segment identified by number**: the record reports no
  single segment over its stated 30% threshold in the routine case once
  `S1` is decomposed into real session runtime vs. dispatch idle
  (session-log sub-split for #2798/#2811/#2814); this decomposition
  rests on the same `task.txt`/`.session.*` timestamps independently
  checked above, and the two outsized one-off events (#2814's 23-min
  retry gap, #2787's 336-min backlog wait, both reproduced above) are
  each independently confirmed from primary sources, not merely
  asserted.
- **Idle time separated from working time**: the specific PR-appears→
  verification-starts gap the issue names is measured directly (not
  inferred) for #2749/#2795 at n=2 (mean = (7.87+8.65)/2 = 8.26 min per
  "What was done" above), and every number in that measurement
  reproduced exactly except the one noted below.

## What did not work

None — the audit surfaced one data-citation inaccuracy (Open findings
§1) but no structural or methodological defect requiring rework.

## Upstream basis

`docs/issue-2830/reports/diagnose-first-7c274fa6.md` (untracked in this
worktree — this session's branch is `issue-2830/independent-verification-1`;
read via `gh pr diff 2833`, not a local checkout) at commit
`2292ed236b381e05f8accb637491163cbdc6666d` — PR #2833, branch
`issue-2830/diagnose-first-7c274fa6`, the only commit on that branch.
canonical: `gh pr view 2833 --json commits` — single commit entry with
that `oid`.

## Open findings

1. Minor citation inaccuracy in one secondary corroboration figure, not
   part of the core segment table. The record states the #2795
   verification session log ran "11:58:31→12:11:46 = 13.25 min."
   canonical: `stat --format='%z'
   on-the-record-issue-2795-adversarial-review-a1341cc3.session.20260830T115831.3978841.log`
   under `$MUSTER_WORKSPACE_ROOT`, run in this session — result:
   `2026-08-30 12:12:25.049985231 +0900`, not 12:11:46. Actual duration
   = 12:12:25 - 11:58:31 = 13.9 min, not the cited 13.25 min.
   derived: re-checked 3 seconds apart with `stat --format='%Y %s'` —
   both reads returned the same size (737352 bytes) and mtime, so the
   file was not still being appended at read time; the record's own PR
   commit timestamp (2026-08-30T03:19:49Z = 12:19:49 KST) postdates the
   observed 12:12:25 mtime, so the file was already static when the
   record was authored — the 12:11:46 figure was a citation error at
   capture time, not a since-changed value.
   Scope: this number is used only as a secondary corroboration against
   the issue body's separately-cited "verification session mean 12.9
   min, n=15" claim — itself already flagged in the record's own Open
   findings §5 as not independently re-derived at n=15 — and is not part
   of the S1/S2/S3 per-issue table or the idle-gap arithmetic
   (mean = (7.87+8.65)/2 = 8.26 min, independently reproduced in "What
   was done" above), both of which are correct.
   Resolution path: none needed under #2830 — cosmetic, does not change
   any reported segment share or the dominant-segment conclusion; worth
   a one-line correction if this record is ever revised, otherwise no
   action.

## Next steps

None. `loop_state: landed` — this independent-verification record is the
full deliverable for this role slot; #2830's second verification slot
(this subject needs 2 total) is a separate session's responsibility.

## Skill verdicts

- skill-verdict: work-in-english — applied: invoked; this record and all
  commands run during the audit are in English; the end-of-turn summary
  to the user is in Korean per the skill's routing rule.
